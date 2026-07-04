#ifndef FINGERSWIPE_EXPORT_H
#define FINGERSWIPE_EXPORT_H

#if defined(_WIN32) || defined(__CYGWIN__)
    #ifdef FINGERSWIPE_BUILD
        #define FS_API __declspec(dllexport)
    #else
        #define FS_API __declspec(dllimport)
    #endif
#else
    #define FS_API __attribute__((visibility("default")))
#endif

#endif