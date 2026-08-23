#include "fingerswipe/api.h"

#include <pthread.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <ctype.h>
#include <dirent.h>

static bool is_valid_device_name(const char *name) {
    if (!name || *name == '\0') return false;
    for (const char *p = name; *p != '\0'; ++p) {
        if (!isalnum((unsigned char)*p) && *p != '_' && *p != '-') {
            return false;
        }
    }
    return true;
}

struct FSBrightness {
    pthread_t thread;
    pthread_mutex_t mutex;
    pthread_cond_t cond;

    double current_brightness;
    double target_brightness;
    bool has_target;
    bool stop;

    char sysfs_path[512];
    char device_name[256];
    long max_brightness;
    bool use_sysfs;
    int last_applied_kde_val;
};

static bool find_backlight_device(char *out_path, size_t path_size, char *out_device, size_t device_size, long *out_max) {
    const char *base_dir = "/sys/class/backlight";
    DIR *dir = opendir(base_dir);
    if (!dir) return false;

    struct dirent *entry;
    bool found = false;

    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_name[0] == '.') continue;
        if (!is_valid_device_name(entry->d_name)) continue;

        char path[512];
        int len = snprintf(path, sizeof(path), "%s/%s/max_brightness", base_dir, entry->d_name);
        if (len < 0 || (size_t)len >= sizeof(path)) continue;

        FILE *fp = fopen(path, "r");
        if (fp) {
            long max_val = 0;
            if (fscanf(fp, "%ld", &max_val) == 1 && max_val > 0) {
                int out_len = snprintf(out_path, path_size, "%s/%s/brightness", base_dir, entry->d_name);
                if (out_len > 0 && (size_t)out_len < path_size) {
                    snprintf(out_device, device_size, "%s", entry->d_name);
                    *out_max = max_val;
                    found = true;
                    fclose(fp);
                    break;
                }
            }
            fclose(fp);
        }
    }
    closedir(dir);
    return found;
}

static double read_current_brightness(FSBrightness *b) {
    if (b->use_sysfs) {
        FILE *fp = fopen(b->sysfs_path, "r");
        if (fp) {
            long val = 0;
            if (fscanf(fp, "%ld", &val) == 1 && b->max_brightness > 0) {
                fclose(fp);
                return (double)val / (double)b->max_brightness;
            }
            fclose(fp);
        }
    }

    FILE *fp = popen("brightnessctl g 2>/dev/null", "r");
    if (fp) {
        long val = 0;
        if (fscanf(fp, "%ld", &val) == 1) {
            pclose(fp);
            FILE *fp_m = popen("brightnessctl m 2>/dev/null", "r");
            if (fp_m) {
                long max_v = 0;
                if (fscanf(fp_m, "%ld", &max_v) == 1 && max_v > 0) {
                    pclose(fp_m);
                    return (double)val / (double)max_v;
                }
                pclose(fp_m);
            }
        } else {
            pclose(fp);
        }
    }

    return 0.5;
}

static void apply_brightness(FSBrightness *b, double val) {
    if (val < 0.0) val = 0.0;
    if (val > 1.0) val = 1.0;

    // 1. Try KDE Plasma D-Bus (triggers native desktop OSD overlay + updates system tray brightness widget)
    int kde_val = (int)round(val * 10000.0);
    char cmd[512];

    if (b->last_applied_kde_val == kde_val) {
        // Value unchanged (e.g. swiping at 100% max or 0% min limit). Issue 1-unit pulse to force KDE OSD overlay popup
        int pulse_val = (kde_val >= 10000) ? 9999 : (kde_val <= 0 ? 1 : (kde_val - 1));
        snprintf(cmd, sizeof(cmd),
            "busctl --user call org.kde.ScreenBrightness /org/kde/Solid/PowerManagement/Actions/BrightnessControl org.kde.Solid.PowerManagement.Actions.BrightnessControl setBrightness i %d >/dev/null 2>&1",
            pulse_val);
        int res = system(cmd);
        (void)res;
    }

    snprintf(cmd, sizeof(cmd),
        "busctl --user call org.kde.ScreenBrightness /org/kde/Solid/PowerManagement/Actions/BrightnessControl org.kde.Solid.PowerManagement.Actions.BrightnessControl setBrightness i %d >/dev/null 2>&1",
        kde_val);
    if (system(cmd) == 0) {
        b->last_applied_kde_val = kde_val;
        return;
    }

    // 2. Try sysfs write directly (works if udev rule / permissions permit)
    if (b->use_sysfs) {
        FILE *fp = fopen(b->sysfs_path, "w");
        if (fp) {
            long target_val = (long)round(val * b->max_brightness);
            fprintf(fp, "%ld\n", target_val);
            fclose(fp);
            return;
        }
    }

    // 3. Try systemd-logind D-Bus method
    if (b->device_name[0] != '\0' && b->max_brightness > 0) {
        long target_val = (long)round(val * b->max_brightness);
        snprintf(cmd, sizeof(cmd),
            "busctl call org.freedesktop.login1 /org/freedesktop/login1/session/auto org.freedesktop.login1.Session SetBrightness ssu \"backlight\" \"%s\" %ld >/dev/null 2>&1",
            b->device_name, target_val);
        if (system(cmd) == 0) {
            return;
        }
    }

    // 4. Fallback to brightnessctl if installed
    snprintf(cmd, sizeof(cmd), "brightnessctl s %.1f%% >/dev/null 2>&1", val * 100.0);
    int res = system(cmd);
    (void)res;
}

static void *brightness_worker_thread(void *arg) {
    FSBrightness *b = (FSBrightness *)arg;

    while (1) {
        pthread_mutex_lock(&b->mutex);
        while (!b->stop && !b->has_target) {
            pthread_cond_wait(&b->cond, &b->mutex);
        }

        if (b->stop) {
            pthread_mutex_unlock(&b->mutex);
            break;
        }

        double val = b->target_brightness;
        b->has_target = false;
        pthread_mutex_unlock(&b->mutex);

        apply_brightness(b, val);
    }

    return NULL;
}

FSError fs_brightness_create(FSBrightness **output) {
    if (!output) return FS_ERROR_INVALID_ARGUMENT;

    FSBrightness *b = calloc(1, sizeof(*b));
    if (!b) return FS_ERROR_OUT_OF_MEMORY;

    pthread_mutex_init(&b->mutex, NULL);
    pthread_cond_init(&b->cond, NULL);

    b->last_applied_kde_val = -1;
    b->use_sysfs = find_backlight_device(b->sysfs_path, sizeof(b->sysfs_path), b->device_name, sizeof(b->device_name), &b->max_brightness);
    b->current_brightness = read_current_brightness(b);

    if (pthread_create(&b->thread, NULL, brightness_worker_thread, b) != 0) {
        pthread_mutex_destroy(&b->mutex);
        pthread_cond_destroy(&b->cond);
        free(b);
        return FS_ERROR_BRIGHTNESS;
    }

    *output = b;
    return FS_OK;
}

void fs_brightness_destroy(FSBrightness *b) {
    if (b) {
        pthread_mutex_lock(&b->mutex);
        b->stop = true;
        pthread_cond_signal(&b->cond);
        pthread_mutex_unlock(&b->mutex);

        pthread_join(b->thread, NULL);

        pthread_mutex_destroy(&b->mutex);
        pthread_cond_destroy(&b->cond);
        free(b);
    }
}

FSError fs_brightness_get(FSBrightness *b, double *value) {
    if (!b || !value) return FS_ERROR_INVALID_ARGUMENT;

    double cur = read_current_brightness(b);

    pthread_mutex_lock(&b->mutex);
    b->current_brightness = cur;
    *value = b->current_brightness;
    pthread_mutex_unlock(&b->mutex);

    return FS_OK;
}

FSError fs_brightness_set(FSBrightness *b, double value) {
    if (!b) return FS_ERROR_INVALID_ARGUMENT;
    if (!isfinite(value) || value < 0.0 || value > 1.0) return FS_ERROR_INVALID_ARGUMENT;

    pthread_mutex_lock(&b->mutex);
    b->current_brightness = value;
    b->target_brightness = value;
    b->has_target = true;
    pthread_cond_signal(&b->cond);
    pthread_mutex_unlock(&b->mutex);

    return FS_OK;
}
