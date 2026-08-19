#include "fingerswipe/api.h"

#include <pthread.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>

struct FSAudio {
    pthread_t thread;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    
    double current_volume;
    bool current_muted;
    
    double target_volume;
    bool has_volume_target;
    
    bool target_muted;
    bool has_mute_target;
    
    bool stop;
};

static void *audio_worker_thread(void *arg) {
    FSAudio *audio = (FSAudio *)arg;
    
    while (1) {
        pthread_mutex_lock(&audio->mutex);
        while (!audio->stop && !audio->has_volume_target && !audio->has_mute_target) {
            pthread_cond_wait(&audio->cond, &audio->mutex);
        }
        
        if (audio->stop) {
            pthread_mutex_unlock(&audio->mutex);
            break;
        }
        
        double vol = 0.0;
        bool do_vol = false;
        if (audio->has_volume_target) {
            vol = audio->target_volume;
            audio->has_volume_target = false;
            do_vol = true;
        }
        
        bool mute = false;
        bool do_mute = false;
        if (audio->has_mute_target) {
            mute = audio->target_muted;
            audio->has_mute_target = false;
            do_mute = true;
        }
        
        pthread_mutex_unlock(&audio->mutex);
        
        if (do_vol) {
            char cmd[128];
            snprintf(cmd, sizeof(cmd), "wpctl set-volume @DEFAULT_AUDIO_SINK@ %.4f 2>/dev/null", vol);
            int res = system(cmd);
            (void)res;
        }
        if (do_mute) {
            char cmd[128];
            snprintf(cmd, sizeof(cmd), "wpctl set-mute @DEFAULT_AUDIO_SINK@ %d 2>/dev/null", mute ? 1 : 0);
            int res = system(cmd);
            (void)res;
        }
    }
    
    return NULL;
}

static void sync_initial_state(FSAudio *audio) {
    FILE *fp = popen("wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null", "r");
    double val = 0.5;
    bool is_muted = false;
    if (fp) {
        char buf[128];
        if (fgets(buf, sizeof(buf), fp) != NULL) {
            if (sscanf(buf, "Volume: %lf", &val) != 1) {
                val = 0.5;
            }
            if (strstr(buf, "[MUTED]") != NULL) {
                is_muted = true;
            }
        }
        pclose(fp);
    }
    pthread_mutex_lock(&audio->mutex);
    audio->current_volume = val;
    audio->current_muted = is_muted;
    pthread_mutex_unlock(&audio->mutex);
}

FSError fs_audio_create(FSAudio **output) {
    if (!output) return FS_ERROR_INVALID_ARGUMENT;
    
    FSAudio *audio = calloc(1, sizeof(*audio));
    if (!audio) return FS_ERROR_OUT_OF_MEMORY;
    
    pthread_mutex_init(&audio->mutex, NULL);
    pthread_cond_init(&audio->cond, NULL);
    
    sync_initial_state(audio);
    
    if (pthread_create(&audio->thread, NULL, audio_worker_thread, audio) != 0) {
        pthread_mutex_destroy(&audio->mutex);
        pthread_cond_destroy(&audio->cond);
        free(audio);
        return FS_ERROR_PIPEWIRE;
    }
    
    *output = audio;
    return FS_OK;
}

void fs_audio_destroy(FSAudio *audio) {
    if (audio) {
        pthread_mutex_lock(&audio->mutex);
        audio->stop = true;
        pthread_cond_signal(&audio->cond);
        pthread_mutex_unlock(&audio->mutex);
        
        pthread_join(audio->thread, NULL);
        
        pthread_mutex_destroy(&audio->mutex);
        pthread_cond_destroy(&audio->cond);
        free(audio);
    }
}

FSError fs_audio_get_volume(FSAudio *audio, double *volume) {
    if (!audio || !volume) return FS_ERROR_INVALID_ARGUMENT;
    
    sync_initial_state(audio);
    
    pthread_mutex_lock(&audio->mutex);
    *volume = audio->current_volume;
    pthread_mutex_unlock(&audio->mutex);
    
    return FS_OK;
}

FSError fs_audio_set_volume(FSAudio *audio, double volume) {
    if (!audio) return FS_ERROR_INVALID_ARGUMENT;
    if (!isfinite(volume) || volume < 0.0 || volume > 1.0) return FS_ERROR_INVALID_ARGUMENT;
    
    pthread_mutex_lock(&audio->mutex);
    audio->current_volume = volume;
    audio->target_volume = volume;
    audio->has_volume_target = true;
    pthread_cond_signal(&audio->cond);
    pthread_mutex_unlock(&audio->mutex);
    
    return FS_OK;
}

FSError fs_audio_get_muted(FSAudio *audio, bool *muted) {
    if (!audio || !muted) return FS_ERROR_INVALID_ARGUMENT;
    
    sync_initial_state(audio);
    
    pthread_mutex_lock(&audio->mutex);
    *muted = audio->current_muted;
    pthread_mutex_unlock(&audio->mutex);
    
    return FS_OK;
}

FSError fs_audio_set_muted(FSAudio *audio, bool muted) {
    if (!audio) return FS_ERROR_INVALID_ARGUMENT;
    
    pthread_mutex_lock(&audio->mutex);
    audio->current_muted = muted;
    audio->target_muted = muted;
    audio->has_mute_target = true;
    pthread_cond_signal(&audio->cond);
    pthread_mutex_unlock(&audio->mutex);
    
    return FS_OK;
}
