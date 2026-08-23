from __future__ import annotations

import ctypes
import ctypes.util
import os
from pathlib import Path


class NativeError(RuntimeError):
    pass


class NativeEvent(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint32), ("phase", ctypes.c_int),
                ("dx", ctypes.c_double), ("dy", ctypes.c_double),
                ("fingers", ctypes.c_uint32), ("timestamp_us", ctypes.c_uint64)]


def load_native(path: Path | None = None) -> ctypes.CDLL:
    candidate = str(path) if path else os.environ.get("FINGERSWIPE_LIBRARY")
    candidate = candidate or ctypes.util.find_library("fingerswipe")
    if not candidate:
        raise NativeError("libfingerswipe.so.1 was not found")
    try:
        library = ctypes.CDLL(candidate)
    except OSError as error:
        raise NativeError(f"cannot load native library: {error}") from error
    library.fs_abi_version.restype = ctypes.c_uint32
    if library.fs_abi_version() != 1:
        raise NativeError("unsupported FingerSwipe native ABI")
    library.fs_error_string.argtypes = [ctypes.c_int]
    library.fs_error_string.restype = ctypes.c_char_p
    if hasattr(library, "fs_uinput_trigger_super_key"):
        library.fs_uinput_trigger_super_key.argtypes = []
        library.fs_uinput_trigger_super_key.restype = ctypes.c_int
    return library


def check(library: ctypes.CDLL, result: int) -> None:
    if result:
        message = library.fs_error_string(result)
        raise NativeError(message.decode("utf-8", "replace") if message else f"native error {result}")
