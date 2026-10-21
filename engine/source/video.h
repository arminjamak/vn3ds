#pragma once
#include "gfx.h"

/* The current frame of a video resource (opens it on first use). */
GfxTex *video_tex(s32 res);
/* A stereo clip (.cvh flag 2) that is playing: the texture showing `eye`'s
 * view, and *mid, the clip's median disparity as a fraction of the picture's
 * width (positive: behind the screen). NULL otherwise (then draw video_tex
 * as a flat picture: the left view, or the poster). */
GfxTex *video_tex_stereo(s32 res, int eye, float *mid);
/* Advance every open video; closes ones that left the screen. */
void video_update(float dt);
void video_close_all(void);
