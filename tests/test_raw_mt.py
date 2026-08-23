from __future__ import annotations

from unittest.mock import MagicMock
from fingerswipe.providers.raw_mt import Raw4FingerTapDetector


def test_raw_4_finger_tap_detector_initialization() -> None:
    callback = MagicMock()
    detector = Raw4FingerTapDetector(on_tap_callback=callback, max_duration_ms=1000, device_path="/dev/null")
    assert detector._max_duration_ms == 1000
    assert detector._device_path == "/dev/null"
