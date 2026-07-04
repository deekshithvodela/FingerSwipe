from __future__ import annotations

import ctypes
from fingerswipe.backends.base import AudioBackend
from fingerswipe.native import check


class PipeWireBackend(AudioBackend):
    def __init__(self, library: ctypes.CDLL) -> None:
        self._library = library
        self._handle = ctypes.c_void_p()
        library.fs_audio_create.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        library.fs_audio_create.restype = ctypes.c_int
        library.fs_audio_destroy.argtypes = [ctypes.c_void_p]
        for name in ("fs_audio_get_volume", "fs_audio_set_volume",
                     "fs_audio_get_muted", "fs_audio_set_muted"):
            getattr(library, name).restype = ctypes.c_int
        library.fs_audio_get_volume.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
        library.fs_audio_set_volume.argtypes = [ctypes.c_void_p, ctypes.c_double]
        library.fs_audio_get_muted.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_bool)]
        library.fs_audio_set_muted.argtypes = [ctypes.c_void_p, ctypes.c_bool]

    def connect(self) -> None:
        if not self._handle:
            check(self._library, self._library.fs_audio_create(ctypes.byref(self._handle)))

    def disconnect(self) -> None:
        if self._handle:
            self._library.fs_audio_destroy(self._handle)
            self._handle = ctypes.c_void_p()

    def get_volume(self) -> float:
        value = ctypes.c_double()
        check(self._library, self._library.fs_audio_get_volume(self._handle, ctypes.byref(value)))
        return value.value

    def set_volume(self, volume: float) -> None:
        check(self._library, self._library.fs_audio_set_volume(self._handle, volume))

    def is_muted(self) -> bool:
        value = ctypes.c_bool()
        check(self._library, self._library.fs_audio_get_muted(self._handle, ctypes.byref(value)))
        return value.value

    def set_muted(self, muted: bool) -> None:
        check(self._library, self._library.fs_audio_set_muted(self._handle, muted))

    def __enter__(self) -> PipeWireBackend:
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.disconnect()
