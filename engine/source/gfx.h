#pragma once
#include "common.h"

/* Rendering backend. The 3DS build implements this with citro2d
 * (gfx_3ds.c); the desktop test build with a software rasteriser. */

typedef struct GfxTex GfxTex;

enum { EYE_LEFT = 0, EYE_RIGHT = 1 };

bool gfx_init(void);
void gfx_exit(void);

/* Loads a .ctex file; *bytes receives the memory it occupies. */
GfxTex *gfx_tex_load(const char *path, u32 *bytes);
void gfx_tex_free(GfxTex *t);
/* Dynamic texture (video): the caller fills the native tiled pixel buffer
 * (tw*th*bpp bytes, format as in .ctex) and commits it. */
GfxTex *gfx_tex_create(int tw, int th, int fmt, int iw, int ih);
void *gfx_tex_data(GfxTex *t);
void gfx_tex_commit(GfxTex *t);
/* Draw only the window (x, y, w, h) of the image (in its pixels, top-left
 * origin) from now on, e.g. one eye's half of a side-by-side stereo video
 * frame. Draws use the window as it is when they are made. */
void gfx_tex_window(GfxTex *t, int x, int y, int w, int h);
/* Like gfx_tex_create without clearing the pixels (the caller writes all
 * of them). Background loading (texcache.c): the main thread allocates and
 * commits, the background thread decodes into gfx_tex_data() in between. */
GfxTex *gfx_tex_alloc(int tw, int th, int fmt, int iw, int ih);

void gfx_frame_begin(void);
void gfx_frame_end(void);
/* Select a render target. Each call clears it to `clear` (0xRRGGBBAA). */
void gfx_target_top(int eye, u32 clear);
void gfx_target_bottom(u32 clear);
/* Off-screen copy of the top screen, used for cross-fades. */
void gfx_target_capture(int eye, u32 clear);
void gfx_draw_capture(int eye, float alpha);

/* Save snapshots: render the top screen into an off-screen picture, then
 * (on a later frame, once the GPU is done) read it back shrunk to w x h as
 * RGB565, top row first. */
void gfx_target_snapshot(u32 clear);
bool gfx_snapshot_read(u16 *out, int w, int h);
/* Make a texture from RGB565 pixels (top row first), e.g. a save snapshot. */
GfxTex *gfx_tex_from_rgb565(const u16 *px, int w, int h);

/* Draw a texture into the box (x, y, |w|, |h|); negative w/h mirror it.
 * `angle` (radians) rotates about the box centre. */
void gfx_image(GfxTex *t, float x, float y, float w, float h, float angle, float alpha);
void gfx_rect(float x, float y, float w, float h, u32 rgba);
/* Vertical two-colour gradient. */
void gfx_gradient(float x, float y, float w, float h, u32 top, u32 bottom);
/* Filled triangle, filled circle and a thick line (minigames, effects). */
void gfx_triangle(float x0, float y0, float x1, float y1, float x2, float y2, u32 rgba);
void gfx_circle(float x, float y, float r, u32 rgba);
void gfx_line(float x0, float y0, float x1, float y1, float thick, u32 rgba);
/* Draw the part (sx, sy, sw, sh) of an eye's capture into (dx, dy, dw, dh):
 * render something into the capture first, then cut it up or distort it. */
void gfx_draw_capture_part(int eye, float sx, float sy, float sw, float sh,
                           float dx, float dy, float dw, float dh, float alpha);

/* System-font text. `s` may contain '\n'. */
void gfx_text(const char *s, float x, float y, float scale, u32 rgba);
float gfx_text_width(const char *s, float scale);
float gfx_glyph_advance(u32 codepoint, float scale);
float gfx_line_height(float scale);

/* 0..1 position of the 3D slider (0 when 3D is off). */
float gfx_slider(void);
