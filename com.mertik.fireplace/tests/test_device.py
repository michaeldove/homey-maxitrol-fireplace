import asyncio
from types import SimpleNamespace
import unittest

from mertik_protocol import Command, build_frame

from homey_test_support import load_app_module


class FakeSignal:
    def __init__(self) -> None:
        self.tx_calls: list[dict[str, object]] = []

    async def tx(
        self,
        payload: list[int],
        *,
        repetitions: int,
        device: object,
    ) -> None:
        self.tx_calls.append(
            {
                "payload": payload,
                "repetitions": repetitions,
                "device": device,
            }
        )


class ConcurrentSignal(FakeSignal):
    def __init__(self) -> None:
        super().__init__()
        self.active = 0
        self.maximum_active = 0

    async def tx(
        self,
        payload: list[int],
        *,
        repetitions: int,
        device: object,
    ) -> None:
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        await asyncio.sleep(0.01)
        await super().tx(
            payload,
            repetitions=repetitions,
            device=device,
        )
        self.active -= 1


class FakeRF:
    def __init__(self, signal: FakeSignal) -> None:
        self.signal = signal
        self.requested_signal_ids: list[str] = []

    def get_signal_433(self, signal_id: str) -> FakeSignal:
        self.requested_signal_ids.append(signal_id)
        return self.signal


class DeviceTests(unittest.IsolatedAsyncioTestCase):
    async def make_device(
        self,
        address: int,
        signal: FakeSignal | None = None,
    ) -> tuple[object, FakeSignal, object]:
        module = load_app_module(
            "drivers/fireplace/device.py",
            "drivers.fireplace.device",
        )
        selected_signal = signal or FakeSignal()
        rf = FakeRF(selected_signal)
        device = module.MertikFireplaceDevice()
        device.data = {"address": address}
        device.homey = SimpleNamespace(rf=rf)

        await device.on_init()
        return device, selected_signal, module

    async def test_initialization_uses_persisted_address_and_registers_capabilities(
        self,
    ) -> None:
        address = 0x2A5A5
        device, _, _ = await self.make_device(address)

        self.assertEqual(device.handset_address, address)
        self.assertEqual(
            set(device.capability_listeners),
            {"onoff", "button.flame_up", "button.flame_down"},
        )
        self.assertIn(f"0x{address:05X}", device.logs[-1])

    async def test_all_capabilities_transmit_the_learned_address(self) -> None:
        address = 0x2A5A5
        device, signal, _ = await self.make_device(address)

        await device.capability_listeners["onoff"](True)
        await device.capability_listeners["onoff"](False)
        await device.capability_listeners["button.flame_up"](True)
        await device.capability_listeners["button.flame_down"](True)

        expected_commands = [
            Command.ON,
            Command.OFF,
            Command.FLAME_UP,
            Command.FLAME_DOWN,
        ]
        self.assertEqual(len(signal.tx_calls), len(expected_commands))
        for call, command in zip(signal.tx_calls, expected_commands, strict=True):
            with self.subTest(command=command):
                self.assertEqual(
                    call["payload"],
                    build_frame(address, command),
                )
                self.assertEqual(call["repetitions"], 10)
                self.assertIs(call["device"], device)

    async def test_duration_controls_repetition_count(self) -> None:
        device, signal, _ = await self.make_device(0x12345)

        await device.increase_flame(duration_ms=86)
        await device.decrease_flame(duration_ms=44)

        self.assertEqual(
            [call["repetitions"] for call in signal.tx_calls],
            [2, 2],
        )

    async def test_transmissions_are_serialized(self) -> None:
        signal = ConcurrentSignal()
        device, _, module = await self.make_device(0x12345, signal)

        await asyncio.gather(
            device._transmit(module.Command.ON),
            device._transmit(module.Command.OFF),
        )

        self.assertEqual(signal.maximum_active, 1)
        self.assertEqual(len(signal.tx_calls), 2)
