#pragma once
#include "common.h"

enum {
    KEY_A_ = 1 << 0,
    KEY_B_ = 1 << 1,
    KEY_X_ = 1 << 2,
    KEY_Y_ = 1 << 3,
    KEY_L_ = 1 << 4,
    KEY_R_ = 1 << 5,
    KEY_START_ = 1 << 6,
    KEY_SELECT_ = 1 << 7,
    KEY_UP_ = 1 << 8,
    KEY_DOWN_ = 1 << 9,
    KEY_LEFT_ = 1 << 10,
    KEY_RIGHT_ = 1 << 11,
    KEY_TOUCH_ = 1 << 12,
    KEY_ZL_ = 1 << 13,
    KEY_ZR_ = 1 << 14,
};

typedef struct {
    u32 down, held, up;
    int tx, ty; /* touch position on the bottom screen while touching */
    float cx;   /* circle pad horizontal, -1..1 (right positive) */
    float cy;   /* circle pad vertical, -1..1 (up positive) */
} Input;

/* Root folder that holds games/, saves/ and settings.cfg. */
const char *platform_root(void);
/* The SD card's root ("sdmc:" on the 3DS), for paths outside the root
 * (link.c: vn3ds and standalone apps finding each other). */
const char *platform_sdmc(void);
/* This program's own .3dsx (argv[0]), "" when not known. */
const char *platform_self_path(void);
/* Starts another .3dsx with argv[0..argc) (argv[0] its path) once this one
 * exits; false when this setup can't (see link.h). */
bool platform_launch(int argc, const char **argv);
bool platform_mkdir(const char *path);
/* Calls cb for each sub-folder name of `path`. */
void platform_list_dirs(const char *path, void (*cb)(const char *name, void *ud), void *ud);
u32 platform_time(void); /* seconds since 1970 */
u64 platform_ms(void);   /* a millisecond clock (for timing) */
/* Writes buffered PERF lines to the log (the background thread calls it). */
void platform_perf_flush(void);
/* Long transfers: keep the console awake (even with the lid closed) and
 * switch the screens' backlights off and on. No-ops on the desktop. */
void platform_keep_awake(bool on);
void platform_screens(bool on);
