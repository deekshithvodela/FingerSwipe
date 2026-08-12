#include "fingerswipe/api.h"

uint32_t fs_abi_version(void) { return FS_ABI_VERSION; }

const char *fs_error_string(FSError error) {
    switch (error) {
    case FS_OK: return "success";
    case FS_ERROR_UNKNOWN: return "unknown error";
    case FS_ERROR_INVALID_ARGUMENT: return "invalid argument";
    case FS_ERROR_OUT_OF_MEMORY: return "out of memory";
    case FS_ERROR_NOT_INITIALIZED: return "not initialized";
    case FS_ERROR_IO: return "I/O error";
    case FS_ERROR_PERMISSION: return "permission denied";
    case FS_ERROR_TIMEOUT: return "operation timed out";
    case FS_ERROR_LIBINPUT: return "libinput error";
    case FS_ERROR_PIPEWIRE: return "PipeWire error";
    case FS_ERROR_AUDIO_TARGET: return "default audio sink unavailable";
    case FS_ERROR_BRIGHTNESS: return "brightness error";
    default: return "unrecognized error";
    }
}
