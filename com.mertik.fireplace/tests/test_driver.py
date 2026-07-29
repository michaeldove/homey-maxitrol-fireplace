import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from mertik_protocol import Command, build_frame

from homey_test_support import load_app_module


class FakeFlowCard:
    def __init__(self) -> None:
        self.listener = None

    def register_run_listener(self, listener: object) -> None:
        self.listener = listener


class FakeFlow:
    def __init__(self) -> None:
        self.cards = {
            "flame_up": FakeFlowCard(),
            "flame_down": FakeFlowCard(),
        }

    def get_action_card(self, card_id: str) -> FakeFlowCard:
        return self.cards[card_id]


class FakeSignal:
    def __init__(self, *, disable_error: Exception | None = None) -> None:
        self.payload_listener = None
        self.enable_count = 0
        self.disable_count = 0
        self.removed_listeners: list[tuple[str, object]] = []
        self.disable_error = disable_error

    def on_payload(self, listener: object) -> None:
        self.payload_listener = listener

    def remove_listener(self, event: str, listener: object) -> None:
        self.removed_listeners.append((event, listener))
        if self.payload_listener is listener:
            self.payload_listener = None

    async def enable_rx(self) -> None:
        self.enable_count += 1

    async def disable_rx(self) -> None:
        self.disable_count += 1
        if self.disable_error is not None:
            raise self.disable_error

    def emit(self, payload: list[int], first: bool = False) -> None:
        if self.payload_listener is not None:
            self.payload_listener(tuple(payload), first)


class FakeRF:
    def __init__(self, signal: FakeSignal) -> None:
        self.signal = signal

    def get_signal_433(self, signal_id: str) -> FakeSignal:
        self.signal_id = signal_id
        return self.signal


class FakePairSession:
    def __init__(self) -> None:
        self.handlers: dict[str, object] = {}

    def set_handler(self, name: str, handler: object) -> None:
        self.handlers[name] = handler


class DriverTests(unittest.IsolatedAsyncioTestCase):
    async def make_pairing(
        self,
        *,
        signal: FakeSignal | None = None,
    ) -> tuple[object, FakeSignal, FakePairSession, object]:
        module = load_app_module(
            "drivers/fireplace/driver.py",
            "drivers.fireplace.driver",
        )
        selected_signal = signal or FakeSignal()
        driver = module.MertikFireplaceDriver()
        driver.homey = SimpleNamespace(rf=FakeRF(selected_signal))
        session = FakePairSession()

        await driver.on_pair(session)
        return driver, selected_signal, session, module

    async def test_flow_actions_forward_optional_duration(self) -> None:
        module = load_app_module(
            "drivers/fireplace/driver.py",
            "drivers.fireplace.driver",
        )
        flow = FakeFlow()
        driver = module.MertikFireplaceDriver()
        driver.homey = SimpleNamespace(flow=flow)

        await driver.on_init()

        device = SimpleNamespace(
            increase_flame=AsyncMock(),
            decrease_flame=AsyncMock(),
        )
        await flow.cards["flame_up"].listener(
            {"device": device, "duration": 172}
        )
        await flow.cards["flame_down"].listener({"device": device})

        device.increase_flame.assert_awaited_once_with(duration_ms=172)
        device.decrease_flame.assert_awaited_once_with(duration_ms=None)

    async def test_pairing_requires_three_matching_addresses(self) -> None:
        _, signal, session, _ = await self.make_pairing()
        learn_remote = session.handlers["learn_remote"]

        task = asyncio.create_task(learn_remote({"source": "pair-view"}))
        await asyncio.sleep(0)

        address_a = 0x12345
        address_b = 0x2A5A5
        signal.emit([0] * 21)
        for _ in range(2):
            signal.emit(build_frame(address_a, Command.FLAME_DOWN))
            signal.emit(build_frame(address_b, Command.FLAME_DOWN))
        self.assertFalse(task.done())

        signal.emit(build_frame(address_b, Command.FLAME_DOWN))
        result = await asyncio.wait_for(task, timeout=1)

        self.assertEqual(
            result,
            {
                "name": "Mertik Fireplace (0x2A5A5)",
                "data": {
                    "id": "g6r-h4t5-2a5a5",
                    "address": address_b,
                },
            },
        )
        self.assertEqual(signal.enable_count, 1)
        self.assertEqual(signal.disable_count, 1)

    async def test_pairing_timeout_disables_receiver(self) -> None:
        _, signal, session, module = await self.make_pairing()

        with patch.object(module, "LEARN_TIMEOUT_SECONDS", 0.001):
            with self.assertRaisesRegex(
                RuntimeError,
                "No compatible remote was detected",
            ):
                await session.handlers["learn_remote"]()

        self.assertEqual(signal.enable_count, 1)
        self.assertEqual(signal.disable_count, 1)

    async def test_disconnect_cancels_learning_and_removes_listener(self) -> None:
        _, signal, session, _ = await self.make_pairing()

        task = asyncio.create_task(session.handlers["learn_remote"]())
        await asyncio.sleep(0)
        await session.handlers["disconnect"]()

        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertIsNone(signal.payload_listener)
        self.assertEqual(signal.removed_listeners[0][0], "payload")

    async def test_receiver_disable_error_is_logged_without_losing_result(
        self,
    ) -> None:
        signal = FakeSignal(disable_error=RuntimeError("radio busy"))
        driver, _, session, _ = await self.make_pairing(signal=signal)

        task = asyncio.create_task(session.handlers["learn_remote"]())
        await asyncio.sleep(0)
        for _ in range(3):
            signal.emit(build_frame(0x12345, Command.FLAME_DOWN))
        result = await task

        self.assertEqual(result["data"]["address"], 0x12345)
        self.assertEqual(len(driver.errors), 1)
        self.assertEqual(driver.errors[0][0], "Could not disable the 433 MHz receiver")
