from collections.abc import Sequence
from enum import Enum
from math import ceil

ADDRESS_BITS = 18
COMMAND_BITS = 4
FRAME_BITS = ADDRESS_BITS + COMMAND_BITS
MAX_ADDRESS = (1 << ADDRESS_BITS) - 1

REPEAT_CADENCE_MS = 43
MIN_REPETITIONS = 1
MAX_REPETITIONS = 255


class Command(str, Enum):
    ON = "on"
    OFF = "off"
    FLAME_UP = "flame_up"
    FLAME_DOWN = "flame_down"


COMMAND_MASKS: dict[Command, tuple[int, int, int, int]] = {
    Command.ON: (1, 0, 0, 1),
    Command.OFF: (1, 0, 1, 1),
    Command.FLAME_UP: (1, 1, 0, 1),
    Command.FLAME_DOWN: (1, 1, 1, 0),
}
COMMANDS_BY_MASK = {mask: command for command, mask in COMMAND_MASKS.items()}


def address_bits(address: int) -> list[int]:
    if not isinstance(address, int) or isinstance(address, bool):
        raise TypeError("address must be an integer")
    if not 0 <= address <= MAX_ADDRESS:
        raise ValueError(f"address must fit in {ADDRESS_BITS} bits")

    return [
        (address >> bit_index) & 1
        for bit_index in range(ADDRESS_BITS - 1, -1, -1)
    ]


def build_frame(address: int, command: Command) -> list[int]:
    try:
        command_bits = COMMAND_MASKS[command]
    except KeyError as error:
        raise ValueError(f"unsupported command: {command}") from error

    frame = address_bits(address) + list(command_bits)
    if len(frame) != FRAME_BITS:
        raise AssertionError(f"expected a {FRAME_BITS}-bit frame")
    return frame


def parse_frame(frame: Sequence[int]) -> tuple[int, Command]:
    if len(frame) != FRAME_BITS:
        raise ValueError(f"frame must contain exactly {FRAME_BITS} bits")
    if any(bit not in (0, 1) for bit in frame):
        raise ValueError("frame must contain only binary bits")

    address = 0
    for bit in frame[:ADDRESS_BITS]:
        address = (address << 1) | bit

    command_mask = tuple(frame[ADDRESS_BITS:])
    try:
        command = COMMANDS_BY_MASK[command_mask]
    except KeyError as error:
        raise ValueError(f"unknown command mask: {command_mask}") from error

    return address, command


def frame_as_binary(address: int, command: Command) -> str:
    return "".join(str(bit) for bit in build_frame(address, command))


def repetitions_for_duration(
    duration_ms: int | None,
    *,
    default_repetitions: int = 10,
) -> int:
    if duration_ms is None:
        return _clamp_repetitions(default_repetitions)
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, int | float):
        raise TypeError("duration_ms must be numeric or None")
    if duration_ms <= 0:
        return MIN_REPETITIONS

    return _clamp_repetitions(ceil(duration_ms / REPEAT_CADENCE_MS))


def _clamp_repetitions(repetitions: int) -> int:
    return max(MIN_REPETITIONS, min(MAX_REPETITIONS, repetitions))
