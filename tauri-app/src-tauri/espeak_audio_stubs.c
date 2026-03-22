// Stub implementations for espeak-ng audio output functions.
// Piper only uses espeak for phonemization, not audio playback.

#include <stddef.h>

typedef struct { char _unused; } audio_object;

void* create_audio_device_object(const char* device, const char* app, const char* desc) {
    (void)device; (void)app; (void)desc;
    return NULL;
}

int audio_object_open(void* obj, int format, int rate, int channels) {
    (void)obj; (void)format; (void)rate; (void)channels;
    return 0;
}

int audio_object_close(void* obj) {
    (void)obj;
    return 0;
}

int audio_object_write(void* obj, const void* data, size_t len) {
    (void)obj; (void)data; (void)len;
    return 0;
}

int audio_object_flush(void* obj) {
    (void)obj;
    return 0;
}

int audio_object_drain(void* obj) {
    (void)obj;
    return 0;
}

const char* audio_object_strerror(void* obj, int err) {
    (void)obj; (void)err;
    return "audio disabled";
}
