#pragma once
#include "../source/common.h"

extern float host_slider_value;
/* 0 = top left eye, 1 = top right eye, 2 = bottom */
const u8 *host_surface(int which, int *w, int *h);
