from __future__ import annotations

import ctypes
from fingerswipe.backends.base import BrightnessBackend
from fingerswipe.native import check


class NativeBrightnessBackend(BrightnessBackend):
    def __init__(self, library: ctypes.CDLL) -> None:
        self._library = library
        self._handle = ctypes.c_void_p()
        library.fs_brightness_create.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        library.fs_brightness_create.restype = ctypes.c_int
        library.fs_brightness_destroy.argtypes = [ctypes.c_void_p]
        for name in ("fs_brightness_get", "fs_brightness_set"):
            getattr(library, name).restype = ctypes.c_int
        library.fs_brightness_get.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
        library.fs_brightness_set.argtypes = [ctypes.c_void_p, ctypes.c_double]

    def connect(self) -> None:
        if not self._handle:
            check(self._library, self._library.fs_brightness_create(ctypes.byref(self._handle)))

    def disconnect(self) -> None:
        if self._handle:
            self._library.fs_brightness_destroy(self._handle)
            self._handle = ctypes.c_void_p()

    def get_brightness(self) -> float:
        value = ctypes.c_double()
        check(self._library, self._library.fs_brightness_get(self._handle, ctypes.byref(value)))
        return value.value

    def set_brightness(self, value: float) -> None:
        check(self._library, self._library.fs_brightness_set(self._handle, value))

    def __enter__(self) -> NativeBrightnessBackend:
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()
