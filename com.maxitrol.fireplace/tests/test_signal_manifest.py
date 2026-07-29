import json
from pathlib import Path
import unittest

from maxitrol_g6r_h4t_protocol import Command, build_frame

APP_ROOT = Path(__file__).resolve().parents[1]
SIGNAL_PATH = (
    APP_ROOT
    / ".homeycompose"
    / "signals"
    / "433"
    / "maxitrol_g6r_h4t_433.json"
)


class SignalManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.signal = json.loads(SIGNAL_PATH.read_text(encoding="utf-8"))

    def test_rf_parameters_match_verified_handset_capture(self) -> None:
        self.assertEqual(self.signal["carrier"], 433_920_000)
        self.assertEqual(self.signal["words"], [[308, 624], [609, 323]])
        self.assertEqual(self.signal["eof"], [609, 21_860])
        self.assertEqual(self.signal["interval"], 21_860)
        self.assertEqual(self.signal["repetitions"], 10)
        self.assertEqual(self.signal["minimalLength"], 22)
        self.assertEqual(self.signal["maximalLength"], 22)
        self.assertEqual(self.signal["sensitivity"], 0.4)

    def test_flame_down_frame_has_verified_duration_and_cadence(self) -> None:
        frame = build_frame(0x15C03, Command.FLAME_DOWN)
        words = self.signal["words"]
        eof = self.signal["eof"]

        payload_duration_us = sum(sum(words[bit]) for bit in frame)
        on_air_frame_us = payload_duration_us + eof[0]
        start_to_start_us = payload_duration_us + sum(eof)

        self.assertEqual(payload_duration_us, 20_504)
        self.assertEqual(on_air_frame_us, 21_113)
        self.assertEqual(start_to_start_us, 42_973)

    def test_generated_manifest_contains_the_same_signal(self) -> None:
        generated_manifest = json.loads(
            (APP_ROOT / "app.json").read_text(encoding="utf-8")
        )
        packaged_signal = generated_manifest["signals"]["433"][
            "maxitrol_g6r_h4t_433"
        ]
        self.assertEqual(packaged_signal, self.signal)
