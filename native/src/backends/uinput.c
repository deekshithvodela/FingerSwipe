#include "fingerswipe/api.h"

#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>

static int g_uinput_fd = -1;

static void emit(int fd, uint16_t type, uint16_t code, int32_t val) {
    struct input_event ie;
    memset(&ie, 0, sizeof(ie));
    ie.type = type;
    ie.code = code;
    ie.value = val;
    ssize_t ret = write(fd, &ie, sizeof(ie));
    (void)ret;
}

FSError fs_uinput_init(void) {
    if (g_uinput_fd >= 0) {
        return FS_OK;
    }

    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (fd < 0) {
        if (errno == EACCES || errno == EPERM) {
            return FS_ERROR_PERMISSION;
        }
        return FS_ERROR_IO;
    }

    if (ioctl(fd, UI_SET_EVBIT, EV_KEY) < 0) {
        close(fd);
        return FS_ERROR_IO;
    }

    // Register full keyboard keybits so libinput / KWin classifies device as a full seat keyboard
    for (int key = KEY_ESC; key <= KEY_COMPOSE; key++) {
        ioctl(fd, UI_SET_KEYBIT, key);
    }

    struct uinput_setup usetup;
    memset(&usetup, 0, sizeof(usetup));
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1234;
    usetup.id.product = 0x5678;
    strcpy(usetup.name, "FingerSwipe Virtual Keyboard");

    if (ioctl(fd, UI_DEV_SETUP, &usetup) < 0 ||
        ioctl(fd, UI_DEV_CREATE, 0) < 0) {
        close(fd);
        return FS_ERROR_IO;
    }

    g_uinput_fd = fd;
    usleep(50000); // 50ms for compositor virtual device seat registration
    return FS_OK;
}

void fs_uinput_cleanup(void) {
    if (g_uinput_fd >= 0) {
        ioctl(g_uinput_fd, UI_DEV_DESTROY);
        close(g_uinput_fd);
        g_uinput_fd = -1;
    }
}

FSError fs_uinput_trigger_super_key(void) {
    if (g_uinput_fd < 0) {
        FSError err = fs_uinput_init();
        if (err != FS_OK) {
            return err;
        }
    }

    // Emitting KEY_LEFTMETA (Super key) on persistent virtual device
    emit(g_uinput_fd, EV_KEY, KEY_LEFTMETA, 1);
    emit(g_uinput_fd, EV_SYN, SYN_REPORT, 0);

    usleep(40000); // 40ms key hold duration

    emit(g_uinput_fd, EV_KEY, KEY_LEFTMETA, 0);
    emit(g_uinput_fd, EV_SYN, SYN_REPORT, 0);

    return FS_OK;
}
