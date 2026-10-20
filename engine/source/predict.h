#pragma once
/* Script lookahead for preloading (predict.c). */
#include "stage.h"
#include "vm.h"
#include "audio.h"

#define PREDICT_MAX_IMAGES 32

typedef struct {
    s32 images[PREDICT_MAX_IMAGES];   /* ImageDef indices, nearest first */
    u8 image_dist[PREDICT_MAX_IMAGES];/* lines of dialogue before each */
    int nimages;
    s32 music_res;                    /* the next music PLAY, or -1 */
    u8 music_flags;
    int music_dist;                   /* lines of dialogue before it */
} Prediction;

/* Looks ahead from where `vm` stopped, at most `max_dist` lines of dialogue
 * (or menus) along every path. `st` is the stage as it is now. */
void predict_scan(const VM *vm, const Stage *st, int max_dist, Prediction *out);
