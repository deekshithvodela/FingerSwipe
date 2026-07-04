#include "fingerswipe/api.h"

#include <errno.h>
#include <fcntl.h>
#include <libinput.h>
#include <poll.h>
#include <stdlib.h>
#include <unistd.h>
#include <libudev.h>

struct FSInput { struct udev *udev; struct libinput *li; };

static int open_restricted(const char *path, int flags, void *data) {
    (void)data;
    return open(path, flags | O_CLOEXEC);
}
static void close_restricted(int fd, void *data) { (void)data; close(fd); }
static const struct libinput_interface interface = { open_restricted, close_restricted };

FSError fs_input_create(FSInput **output) {
    if (!output) return FS_ERROR_INVALID_ARGUMENT;
    *output = NULL;
    FSInput *input = calloc(1, sizeof(*input));
    if (!input) return FS_ERROR_OUT_OF_MEMORY;
    input->udev = udev_new();
    if (!input->udev) { free(input); return FS_ERROR_LIBINPUT; }
    input->li = libinput_udev_create_context(&interface, NULL, input->udev);
    if (!input->li || libinput_udev_assign_seat(input->li, "seat0") != 0) {
        fs_input_destroy(input); return errno == EACCES ? FS_ERROR_PERMISSION : FS_ERROR_LIBINPUT;
    }
    *output = input;
    return FS_OK;
}

void fs_input_destroy(FSInput *input) {
    if (!input) return;
    if (input->li) libinput_unref(input->li);
    if (input->udev) udev_unref(input->udev);
    free(input);
}

static bool process_next_event(struct libinput *li, FSGestureEvent *out) {
    struct libinput_event *event;
    while ((event = libinput_get_event(li)) != NULL) {
        enum libinput_event_type type = libinput_event_get_type(event);
        if (type >= LIBINPUT_EVENT_GESTURE_SWIPE_BEGIN && type <= LIBINPUT_EVENT_GESTURE_SWIPE_END) {
            struct libinput_event_gesture *gesture = libinput_event_get_gesture_event(event);
            *out = (FSGestureEvent){
                .size = sizeof(*out),
                .fingers = libinput_event_gesture_get_finger_count(gesture),
                .timestamp_us = libinput_event_gesture_get_time_usec(gesture)
            };
            if (type == LIBINPUT_EVENT_GESTURE_SWIPE_BEGIN) {
                out->phase = FS_GESTURE_SWIPE_BEGIN;
            } else if (type == LIBINPUT_EVENT_GESTURE_SWIPE_UPDATE) {
                out->phase = FS_GESTURE_SWIPE_UPDATE;
                out->dx = libinput_event_gesture_get_dx(gesture);
                out->dy = libinput_event_gesture_get_dy(gesture);
            } else {
                out->phase = libinput_event_gesture_get_cancelled(gesture) ? FS_GESTURE_SWIPE_CANCEL : FS_GESTURE_SWIPE_END;
            }
            libinput_event_destroy(event);
            return true;
        }
        libinput_event_destroy(event);
    }
    return false;
}

FSError fs_input_poll(FSInput *input, int timeout_ms, FSGestureEvent *out, bool *available) {
    if (!input || !out || !available || timeout_ms < 0) return FS_ERROR_INVALID_ARGUMENT;
    *available = false;

    if (libinput_dispatch(input->li) != 0) return FS_ERROR_LIBINPUT;

    if (process_next_event(input->li, out)) {
        *available = true;
        return FS_OK;
    }

    struct pollfd pfd = { .fd = libinput_get_fd(input->li), .events = POLLIN };
    int result;
    do { result = poll(&pfd, 1, timeout_ms); } while (result < 0 && errno == EINTR);
    if (result < 0) return FS_ERROR_IO;
    if (result == 0) return FS_OK;

    if (libinput_dispatch(input->li) != 0) return FS_ERROR_LIBINPUT;

    if (process_next_event(input->li, out)) {
        *available = true;
    }
    return FS_OK;
}
