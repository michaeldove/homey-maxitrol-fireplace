import unittest

from maxitrol_g6r_h4t_protocol import (
    ADDRESS_BITS,
    FRAME_BITS,
    MAX_ADDRESS,
    Command,
    address_bits,
    build_frame,
    frame_as_binary,
    parse_frame,
    repetitions_for_duration,
)

HANDSET_ADDRESS = 0x15C03


class FrameTests(unittest.TestCase):
    def test_address_is_18_bits(self) -> None:
        bits = address_bits(HANDSET_ADDRESS)
        self.assertEqual(len(bits), ADDRESS_BITS)
        self.assertEqual("".join(map(str, bits)), "010101110000000011")

    def test_captured_frames(self) -> None:
        expected = {
            Command.ON: "0101011100000000111001",
            Command.OFF: "0101011100000000111011",
            Command.FLAME_UP: "0101011100000000111101",
            Command.FLAME_DOWN: "0101011100000000111110",
        }

        for command, binary in expected.items():
            with self.subTest(command=command):
                self.assertEqual(frame_as_binary(HANDSET_ADDRESS, command), binary)
                self.assertEqual(
                    len(build_frame(HANDSET_ADDRESS, command)),
                    FRAME_BITS,
                )

    def test_address_bounds(self) -> None:
        self.assertEqual(len(address_bits(0)), ADDRESS_BITS)
        self.assertEqual(len(address_bits(MAX_ADDRESS)), ADDRESS_BITS)

        for invalid_address in (-1, MAX_ADDRESS + 1):
            with self.subTest(address=invalid_address):
                with self.assertRaises(ValueError):
                    address_bits(invalid_address)

    def test_address_rejects_non_integer(self) -> None:
        for invalid_address in (True, "0x15C03", 1.5):
            with self.subTest(address=invalid_address):
                with self.assertRaises(TypeError):
                    address_bits(invalid_address)  # type: ignore[arg-type]

    def test_parse_captured_frames(self) -> None:
        expected = {
            Command.ON: "0101011100000000111001",
            Command.OFF: "0101011100000000111011",
            Command.FLAME_UP: "0101011100000000111101",
            Command.FLAME_DOWN: "0101011100000000111110",
        }

        for command, binary in expected.items():
            with self.subTest(command=command):
                address, parsed_command = parse_frame(
                    tuple(int(bit) for bit in binary)
                )
                self.assertEqual(address, HANDSET_ADDRESS)
                self.assertEqual(parsed_command, command)

    def test_parse_round_trip_with_another_handset(self) -> None:
        address = 0x2A5A5
        for command in Command:
            with self.subTest(command=command):
                self.assertEqual(
                    parse_frame(build_frame(address, command)),
                    (address, command),
                )

    def test_parse_rejects_invalid_frames(self) -> None:
        with self.assertRaises(ValueError):
            parse_frame([0] * 21)
        with self.assertRaises(ValueError):
            parse_frame([0] * 21 + [2])
        with self.assertRaises(ValueError):
            parse_frame([0] * 18 + [1, 1, 1, 1])

    def test_build_rejects_unsupported_command(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported command"):
            build_frame(HANDSET_ADDRESS, "invalid")  # type: ignore[arg-type]


class RepetitionTests(unittest.TestCase):
    def test_default_repetitions(self) -> None:
        self.assertEqual(repetitions_for_duration(None), 10)

    def test_duration_uses_43_ms_cadence(self) -> None:
        self.assertEqual(repetitions_for_duration(1), 1)
        self.assertEqual(repetitions_for_duration(43), 1)
        self.assertEqual(repetitions_for_duration(44), 2)
        self.assertEqual(repetitions_for_duration(430), 10)

    def test_repetitions_are_clamped(self) -> None:
        self.assertEqual(repetitions_for_duration(-1), 1)
        self.assertEqual(repetitions_for_duration(0), 1)
        self.assertEqual(repetitions_for_duration(100_000), 255)
        self.assertEqual(
            repetitions_for_duration(None, default_repetitions=0),
            1,
        )
        self.assertEqual(
            repetitions_for_duration(None, default_repetitions=999),
            255,
        )

    def test_duration_rejects_non_numeric_values(self) -> None:
        for invalid_duration in (True, "43"):
            with self.subTest(duration=invalid_duration):
                with self.assertRaises(TypeError):
                    repetitions_for_duration(invalid_duration)  # type: ignore[arg-type]

    def test_fractional_duration_rounds_up(self) -> None:
        self.assertEqual(repetitions_for_duration(43.1), 2)


if __name__ == "__main__":
    unittest.main()
