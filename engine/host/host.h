#pragma once
#include "../source/common.h"

extern float host_slider_value;
/* 0 = top left eye, 1 = top right eye, 2 = bottom */
const u8 *host_surface(int which, int *w, int *h);
/* --decode-audio IN [OUT.wav] [--loops N]: decode through the 3DS's
 * streaming path (audio_dec.c) and time it. */
int host_decode_audio(const char *in, const char *out, int loops);
