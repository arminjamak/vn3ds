#pragma once
#include "gfx.h"

/* The current frame of a video resource (opens it on first use). */
GfxTex *video_tex(s32 res);
/* Advance every open video; closes ones that left the screen. */
void video_update(float dt);
void video_close_all(void);
