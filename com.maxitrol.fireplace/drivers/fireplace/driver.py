import asyncio
from typing import Any

from homey.driver import Driver as HomeyDriver
from homey.pair_session import PairSession

from ...maxitrol_g6r_h4t_protocol import parse_frame

SIGNAL_ID = "maxitrol_g6r_h4t_433"
LEARN_TIMEOUT_SECONDS = 30
LEARN_MATCHING_FRAMES = 3


class MaxitrolFireplaceDriver(HomeyDriver):
    async def on_init(self) -> None:
        await super().on_init()

        flame_up_card = self.homey.flow.get_action_card("flame_up")

        async def on_flame_up(
            card_arguments: dict[str, Any], **trigger_kwargs: Any
        ) -> None:
            device = card_arguments["device"]
            duration = card_arguments.get("duration")
            await device.increase_flame(duration_ms=duration)

        flame_up_card.register_run_listener(on_flame_up)

        flame_down_card = self.homey.flow.get_action_card("flame_down")

        async def on_flame_down(
            card_arguments: dict[str, Any], **trigger_kwargs: Any
        ) -> None:
            device = card_arguments["device"]
            duration = card_arguments.get("duration")
            await device.decrease_flame(duration_ms=duration)

        flame_down_card.register_run_listener(on_flame_down)
        self.log("Maxitrol G6R driver initialized")

    async def on_pair(self, session: PairSession) -> None:
        signal = self.homey.rf.get_signal_433(SIGNAL_ID)
        learning_lock = asyncio.Lock()
        learned_address: asyncio.Future[int] | None = None
        candidate_counts: dict[int, int] = {}

        def on_payload(payload: tuple[int, ...], first: bool) -> None:
            nonlocal learned_address

            if learned_address is None or learned_address.done():
                return

            payload_bits = "".join(str(bit) for bit in payload)
            try:
                address, command = parse_frame(payload)
            except ValueError as error:
                self.log(
                    f"Ignored RF payload {payload_bits} "
                    f"(first={first}): {error}"
                )
                return

            candidate_counts[address] = candidate_counts.get(address, 0) + 1
            count = candidate_counts[address]
            self.log(
                f"Detected G6R candidate 0x{address:05X} from "
                f"{command.value} frame ({count}/{LEARN_MATCHING_FRAMES}, "
                f"first={first}, payload={payload_bits})"
            )
            if count >= LEARN_MATCHING_FRAMES:
                self.log(f"Learned G6R handset 0x{address:05X}")
                learned_address.set_result(address)

        signal.on_payload(on_payload)

        async def disable_receiver() -> None:
            try:
                await signal.disable_rx()
            except Exception as error:
                self.error("Could not disable the 433 MHz receiver", error)

        async def on_learn_remote(_data: Any = None) -> dict[str, Any]:
            nonlocal learned_address

            async with learning_lock:
                loop = asyncio.get_running_loop()
                candidate_counts.clear()
                learned_address = loop.create_future()
                await signal.enable_rx()
                self.log("Listening for a compatible G6R H4T handset frame")

                try:
                    address = await asyncio.wait_for(
                        learned_address,
                        timeout=LEARN_TIMEOUT_SECONDS,
                    )
                except TimeoutError as error:
                    raise RuntimeError(
                        "No compatible remote was detected. "
                        "Try again and hold Flame Down for two seconds."
                    ) from error
                finally:
                    learned_address = None
                    await disable_receiver()

                address_hex = f"0x{address:05X}"
                return {
                    "name": f"Maxitrol G6R Fireplace ({address_hex})",
                    "data": {
                        "id": f"g6r-h4t-433-{address:05x}",
                        "address": address,
                    },
                }

        async def on_disconnect(_data: Any = None) -> None:
            nonlocal learned_address

            if learned_address is not None and not learned_address.done():
                learned_address.cancel()
            learned_address = None
            await disable_receiver()
            signal.remove_listener("payload", on_payload)

        session.set_handler("learn_remote", on_learn_remote)
        session.set_handler("disconnect", on_disconnect)


homey_export = MaxitrolFireplaceDriver
