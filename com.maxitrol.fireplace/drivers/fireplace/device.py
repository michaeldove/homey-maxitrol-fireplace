import asyncio
from typing import Any

from homey.device import Device as HomeyDevice

from ...maxitrol_g6r_h4t_protocol import (
    Command,
    build_frame,
    repetitions_for_duration,
)

SIGNAL_ID = "maxitrol_g6r_h4t_433"
DEFAULT_REPETITIONS = 10


class MaxitrolFireplaceDevice(HomeyDevice):
    handset_address: int
    _transmit_lock: asyncio.Lock

    async def on_init(self) -> None:
        await super().on_init()

        data = self.get_data()
        self.handset_address = int(data["address"])
        self._transmit_lock = asyncio.Lock()
        self._signal = self.homey.rf.get_signal_433(SIGNAL_ID)

        self.register_capability_listener("onoff", self._on_onoff)
        self.register_capability_listener("button.flame_up", self._on_flame_up)
        self.register_capability_listener("button.flame_down", self._on_flame_down)

        self.log(
            f"Initialized G6R H4T 433 MHz fireplace at address "
            f"0x{self.handset_address:05X}"
        )

    async def _on_onoff(self, value: bool, **kwargs: Any) -> None:
        await self._transmit(Command.ON if value else Command.OFF)

    async def _on_flame_up(self, value: bool, **kwargs: Any) -> None:
        await self.increase_flame()

    async def _on_flame_down(self, value: bool, **kwargs: Any) -> None:
        await self.decrease_flame()

    async def increase_flame(self, duration_ms: int | None = None) -> None:
        await self._transmit(Command.FLAME_UP, duration_ms=duration_ms)

    async def decrease_flame(self, duration_ms: int | None = None) -> None:
        await self._transmit(Command.FLAME_DOWN, duration_ms=duration_ms)

    async def _transmit(
        self,
        command: Command,
        *,
        duration_ms: int | None = None,
    ) -> None:
        repetitions = repetitions_for_duration(
            duration_ms,
            default_repetitions=DEFAULT_REPETITIONS,
        )
        frame = build_frame(self.handset_address, command)

        async with self._transmit_lock:
            self.log(
                f"Transmitting {command.value} to 0x{self.handset_address:05X} "
                f"({repetitions} repetitions)"
            )
            await self._signal.tx(
                frame,
                repetitions=repetitions,
                device=self,
            )


homey_export = MaxitrolFireplaceDevice
