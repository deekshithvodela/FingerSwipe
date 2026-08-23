#ifndef FINGERSWIPE_API_H
#define FINGERSWIPE_API_H

#include <stdbool.h>
#include <stdint.h>
#include "export.h"

#ifdef __cplusplus
extern "C" {
#endif

#define FS_ABI_VERSION 1U

typedef struct FSInput FSInput;
typedef struct FSAudio FSAudio;
typedef struct FSBrightness FSBrightness;

typedef enum FSError {
    FS_OK = 0,
    FS_ERROR_UNKNOWN = -1,
    FS_ERROR_INVALID_ARGUMENT = -2,
    FS_ERROR_OUT_OF_MEMORY = -3,
    FS_ERROR_NOT_INITIALIZED = -4,
    FS_ERROR_IO = -5,
    FS_ERROR_PERMISSION = -6,
    FS_ERROR_TIMEOUT = -7,
    FS_ERROR_LIBINPUT = -100,
    FS_ERROR_PIPEWIRE = -200,
    FS_ERROR_AUDIO_TARGET = -201,
    FS_ERROR_BRIGHTNESS = -300
} FSError;

typedef enum FSGesturePhase {
    FS_GESTURE_NONE = 0,
    FS_GESTURE_SWIPE_BEGIN = 1,
    FS_GESTURE_SWIPE_UPDATE = 2,
    FS_GESTURE_SWIPE_END = 3,
    FS_GESTURE_SWIPE_CANCEL = 4
} FSGesturePhase;

typedef struct FSGestureEvent {
    uint32_t size;
    FSGesturePhase phase;
    double dx;
    double dy;
    uint32_t fingers;
    uint64_t timestamp_us;
} FSGestureEvent;

FS_API uint32_t fs_abi_version(void);
FS_API const char *fs_error_string(FSError error);
FS_API FSError fs_input_create(FSInput **output);
FS_API void fs_input_destroy(FSInput *input);
FS_API FSError fs_input_poll(FSInput *input, int timeout_ms,
                             FSGestureEvent *event, bool *available);
FS_API FSError fs_audio_create(FSAudio **output);
FS_API void fs_audio_destroy(FSAudio *audio);
FS_API FSError fs_audio_get_volume(FSAudio *audio, double *volume);
FS_API FSError fs_audio_set_volume(FSAudio *audio, double volume);
FS_API FSError fs_audio_get_muted(FSAudio *audio, bool *muted);
FS_API FSError fs_audio_set_muted(FSAudio *audio, bool muted);

FS_API FSError fs_brightness_create(FSBrightness **output);
FS_API void fs_brightness_destroy(FSBrightness *brightness);
FS_API FSError fs_brightness_get(FSBrightness *brightness, double *value);
FS_API FSError fs_brightness_set(FSBrightness *brightness, double value);

FS_API FSError fs_uinput_init(void);
FS_API FSError fs_uinput_trigger_super_key(void);
FS_API void fs_uinput_cleanup(void);

#ifdef __cplusplus
}
#endif
#endif
