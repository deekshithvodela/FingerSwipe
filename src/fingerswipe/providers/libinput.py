from __future__ import annotations

import ctypes
from collections.abc import Iterator

from fingerswipe.interactions.event import GestureEvent
from fingerswipe.interactions.phase import GesturePhase
from fingerswipe.native import NativeEvent, check
from fingerswipe.providers.base import Provider


class LibinputProvider(Provider):
    _phases = {1: GesturePhase.BEGIN, 2: GesturePhase.UPDATE,
               3: GesturePhase.END, 4: GesturePhase.CANCEL}

    def __init__(self, library: ctypes.CDLL, poll_ms: int = 250) -> None:
        self._library = library
        self._poll_ms = poll_ms
        self._handle = ctypes.c_void_p()
        library.fs_input_create.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        library.fs_input_create.restype = ctypes.c_int
        library.fs_input_destroy.argtypes = [ctypes.c_void_p]
        library.fs_input_poll.argtypes = [ctypes.c_void_p, ctypes.c_int,
            ctypes.POINTER(NativeEvent), ctypes.POINTER(ctypes.c_bool)]
        library.fs_input_poll.restype = ctypes.c_int
        check(library, library.fs_input_create(ctypes.byref(self._handle)))
        self._running = True

    def stop(self) -> None:
        self._running = False

    def close(self) -> None:
        self.stop()
        if self._handle:
            self._library.fs_input_destroy(self._handle)
            self._handle = ctypes.c_void_p()

    def events(self) -> Iterator[GestureEvent]:
        while self._running:
            raw, available = NativeEvent(), ctypes.c_bool()
            raw.size = ctypes.sizeof(raw)
            check(self._library, self._library.fs_input_poll(
                self._handle, self._poll_ms, ctypes.byref(raw), ctypes.byref(available)))
            if available.value and raw.fingers in (3, 4):
                yield GestureEvent(self._phases[raw.phase], raw.dx, raw.dy, raw.timestamp_us / 1_000_000, fingers=raw.fingers)

    def __enter__(self) -> LibinputProvider:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
