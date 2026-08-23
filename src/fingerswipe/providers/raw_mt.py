from __future__ import annotations

import logging
import os
import struct
import threading
import time
from pathlib import Path
from typing import Callable

# Linux input event constants
EV_ABS = 0x03
ABS_MT_SLOT = 0x2f
ABS_MT_TRACKING_ID = 0x39

EVENT_FORMAT = "llHHi"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)


def find_touchpad_device_node() -> str:
    proc_devices = Path("/proc/bus/input/devices")
    if proc_devices.exists():
        content = proc_devices.read_text()
        current_device: dict[str, str] = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                name = current_device.get("N", "").lower()
                handlers = current_device.get("H", "")
                if "touchpad" in name or ("elan" in name and "mouse" not in name) or ("synaptics" in name and "mouse" not in name):
                    for h in handlers.split():
                        if h.startswith("event"):
                            return f"/dev/input/{h}"
                current_device = {}
                continue
            if ":" in line:
                prefix, val = line.split(":", 1)
                if prefix.strip() == "N":
                    current_device["N"] = val.replace("Name=", "").strip('"')
                elif prefix.strip() == "H":
                    current_device["H"] = val.replace("Handlers=", "")

    return "/dev/input/event4"


class Raw4FingerTapDetector:
    """Dedicated background raw kernel Multi-Touch event listener for 4-finger taps."""

    def __init__(
        self,
        on_tap_callback: Callable[[], None],
        max_duration_ms: int = 1000,
        device_path: str | None = None,
    ) -> None:
        self._callback = on_tap_callback
        self._max_duration_ms = max_duration_ms
        self._device_path = device_path or find_touchpad_device_node()
        self._running = False
        self._thread: threading.Thread | None = None
        self._logger = logging.getLogger("fingerswipe.raw_mt")

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="RawMTTapDetector")
        self._thread.start()
        self._logger.info("Raw 4-finger MT tap detector started on %s", self._device_path)

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _run_loop(self) -> None:
        try:
            fd = os.open(self._device_path, os.O_RDONLY | os.O_NONBLOCK)
        except Exception as err:
            self._logger.warning("Cannot open raw MT device %s: %err", self._device_path, err)
            return

        active_slots: dict[int, int] = {}
        current_slot = 0
        start_time: float | None = None
        peak_slots = 0

        try:
            while self._running:
                try:
                    data = os.read(fd, EVENT_SIZE)
                except BlockingIOError:
                    time.sleep(0.005)
                    continue
                except Exception:
                    break

                if not data or len(data) < EVENT_SIZE:
                    continue

                _sec, _usec, ev_type, code, value = struct.unpack(EVENT_FORMAT, data)

                if ev_type == EV_ABS:
                    if code == ABS_MT_SLOT:
                        current_slot = value
                    elif code == ABS_MT_TRACKING_ID:
                        if value != -1:
                            active_slots[current_slot] = value
                            if len(active_slots) > peak_slots:
                                peak_slots = len(active_slots)
                            if start_time is None:
                                start_time = time.monotonic()
                        else:
                            active_slots.pop(current_slot, None)
                            if not active_slots and start_time is not None:
                                duration_ms = (time.monotonic() - start_time) * 1000.0
                                if peak_slots == 4 and duration_ms <= self._max_duration_ms:
                                    self._logger.info("🎉 Raw MT 4-finger tap detected! (Duration: %.1f ms)", duration_ms)
                                    try:
                                        self._callback()
                                    except Exception as cb_err:
                                        self._logger.error("Tap callback failed: %s", cb_err)
                                start_time = None
                                peak_slots = 0

        finally:
            os.close(fd)
