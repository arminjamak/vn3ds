/* citro2d implementation of gfx.h.
 *
 * Stereo: the top screen runs in 3D mode with separate left/right render
 * targets; the portable renderer draws the scene once per eye with per-layer
 * horizontal offsets. When the slider is at 0 only the left eye is drawn,
 * as in the libctru stereoscopic example. */

#include <3ds.h>
#include <citro2d.h>
#include <citro3d.h>
#include <zlib.h>

#include "../gfx.h"

#define DRAW_DEPTH 0.5f

struct GfxTex {
    C3D_Tex tex;
    Tex3DS_SubTexture sub;
};

static C3D_RenderTarget *top_t[2], *bottom_t, *cap_t[2];
static C3D_Tex cap_tex[2];
static bool cap_ok[2];
static Tex3DS_SubTexture cap_sub;
static C2D_TextBuf textbuf, measurebuf;
static GfxTex **pending;
static int npending, cap_pending;

static inline u32 col(u32 rgba)
{
    return C2D_Color32((u8)(rgba >> 24), (u8)(rgba >> 16), (u8)(rgba >> 8), (u8)rgba);
}

bool gfx_init(void)
{
    gfxInitDefault();
    gfxSet3D(true);
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS * 2);
    C2D_Prepare();
    fontEnsureMapped();
    top_t[0] = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);
    top_t[1] = C2D_CreateScreenTarget(GFX_TOP, GFX_RIGHT);
    bottom_t = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);
    for (int i = 0; i < 2; i++) {
        cap_ok[i] = C3D_TexInitVRAM(&cap_tex[i], 512, 256, GPU_RGBA8);
        if (cap_ok[i]) {
            C3D_TexSetFilter(&cap_tex[i], GPU_LINEAR, GPU_LINEAR);
            cap_t[i] = C3D_RenderTargetCreateFromTex(&cap_tex[i], GPU_TEXFACE_2D, 0, GPU_RB_DEPTH16);
            cap_ok[i] = cap_t[i] != NULL;
        }
    }
    cap_sub.width = TOP_W;
    cap_sub.height = TOP_H;
    cap_sub.left = 0.0f;
    cap_sub.right = TOP_W / 512.0f;
    /* A texture target uses Mtx_Ortho with scene y = 0 at the first memory
     * row, which is v = 1.0: the capture reads back upright. (top < bottom
     * would mean "rotated" to citro2d, so never swap them.) */
    cap_sub.top = 1.0f;
    cap_sub.bottom = 1.0f - TOP_H / 256.0f;
    textbuf = C2D_TextBufNew(8192);
    measurebuf = C2D_TextBufNew(1024);
    return true;
}

void gfx_exit(void)
{
    for (int i = 0; i < npending; i++) {
        C3D_TexDelete(&pending[i]->tex);
        free(pending[i]);
    }
    free(pending);
    pending = NULL;
    npending = cap_pending = 0;
    C2D_TextBufDelete(textbuf);
    C2D_TextBufDelete(measurebuf);
    for (int i = 0; i < 2; i++) {
        if (cap_t[i])
            C3D_RenderTargetDelete(cap_t[i]);
        if (cap_ok[i])
            C3D_TexDelete(&cap_tex[i]);
    }
    C2D_Fini();
    C3D_Fini();
    gfxExit();
}

/* ---- textures ---------------------------------------------------------- */

GfxTex *gfx_tex_load(const char *path, u32 *bytes)
{
    FILE *f = fopen(path, "rb");
    if (!f)
        return NULL;
    u8 hdr[36];
    if (fread(hdr, 1, 36, f) != 36 || memcmp(hdr, "CTEX", 4) != 0) {
        fclose(f);
        return NULL;
    }
    int fmt = rd_u16(hdr + 6), tw = rd_u16(hdr + 8), th = rd_u16(hdr + 10);
    int iw = rd_u16(hdr + 12), ih = rd_u16(hdr + 14);
    u32 flags = rd_u32(hdr + 24), raw = rd_u32(hdr + 28), stored = rd_u32(hdr + 32);
    GPU_TEXCOLOR gfmt = fmt == 0 ? GPU_RGBA8 : fmt == 1 ? GPU_RGB8 : GPU_RGB565;

    GfxTex *t = calloc(1, sizeof(GfxTex));
    if (!t || !C3D_TexInit(&t->tex, (u16)tw, (u16)th, gfmt)) {
        free(t);
        fclose(f);
        return NULL;
    }
    bool ok = t->tex.size == raw;
    if (ok && (flags & 1)) {
        u8 *packed = malloc(stored);
        ok = packed && fread(packed, 1, stored, f) == stored;
        if (ok) {
            uLongf n = raw;
            ok = uncompress(t->tex.data, &n, packed, stored) == Z_OK && n == raw;
        }
        free(packed);
    } else if (ok) {
        ok = fread(t->tex.data, 1, raw, f) == raw;
    }
    fclose(f);
    if (!ok) {
        C3D_TexDelete(&t->tex);
        free(t);
        return NULL;
    }
    C3D_TexFlush(&t->tex);
    C3D_TexSetFilter(&t->tex, GPU_LINEAR, GPU_LINEAR);
    C3D_TexSetWrap(&t->tex, GPU_CLAMP_TO_EDGE, GPU_CLAMP_TO_EDGE);
    t->sub.width = (u16)iw;
    t->sub.height = (u16)ih;
    t->sub.left = 0.0f;
    t->sub.top = 1.0f;
    t->sub.right = (float)iw / (float)tw;
    t->sub.bottom = 1.0f - (float)ih / (float)th;
    *bytes = raw;
    return t;
}

GfxTex *gfx_tex_create(int tw, int th, int fmt, int iw, int ih)
{
    GPU_TEXCOLOR gfmt = fmt == 0 ? GPU_RGBA8 : fmt == 1 ? GPU_RGB8 : GPU_RGB565;
    GfxTex *t = calloc(1, sizeof(GfxTex));
    if (!t || !C3D_TexInit(&t->tex, (u16)tw, (u16)th, gfmt)) {
        free(t);
        return NULL;
    }
    memset(t->tex.data, 0, t->tex.size);
    C3D_TexSetFilter(&t->tex, GPU_LINEAR, GPU_LINEAR);
    C3D_TexSetWrap(&t->tex, GPU_CLAMP_TO_EDGE, GPU_CLAMP_TO_EDGE);
    t->sub.width = (u16)iw;
    t->sub.height = (u16)ih;
    t->sub.left = 0.0f;
    t->sub.top = 1.0f;
    t->sub.right = (float)iw / (float)tw;
    t->sub.bottom = 1.0f - (float)ih / (float)th;
    return t;
}

void *gfx_tex_data(GfxTex *t) { return t->tex.data; }

void gfx_tex_commit(GfxTex *t) { C3D_TexFlush(&t->tex); }

void gfx_tex_free(GfxTex *t)
{
    if (!t)
        return;
    /* The GPU may still be reading it; free after the next frame sync. */
    if (npending == cap_pending) {
        int cap = cap_pending ? cap_pending * 2 : 64;
        GfxTex **grown = realloc(pending, sizeof(*pending) * (size_t)cap);
        if (!grown)
            return; /* leak rather than free a texture the GPU may be using */
        pending = grown;
        cap_pending = cap;
    }
    pending[npending++] = t;
}

/* ---- frame / targets --------------------------------------------------- */

void gfx_frame_begin(void)
{
    C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
    for (int i = 0; i < npending; i++) {
        C3D_TexDelete(&pending[i]->tex);
        free(pending[i]);
    }
    npending = 0;
    C2D_TextBufClear(textbuf);
}

void gfx_frame_end(void)
{
    C3D_FrameEnd(0);
}

void gfx_target_top(int eye, u32 clear)
{
    C2D_TargetClear(top_t[eye], col(clear));
    C2D_SceneBegin(top_t[eye]);
}

void gfx_target_bottom(u32 clear)
{
    C2D_TargetClear(bottom_t, col(clear));
    C2D_SceneBegin(bottom_t);
}

void gfx_target_capture(int eye, u32 clear)
{
    if (!cap_ok[eye])
        return;
    C2D_TargetClear(cap_t[eye], col(clear));
    C2D_SceneBegin(cap_t[eye]);
}

void gfx_draw_capture(int eye, float alpha)
{
    if (!cap_ok[eye] || alpha <= 0)
        return;
    C2D_Image img = {&cap_tex[eye], &cap_sub};
    C2D_ImageTint tint;
    C2D_PlainImageTint(&tint, C2D_Color32f(1, 1, 1, alpha), 0.0f);
    C2D_DrawImageAt(img, 0, 0, DRAW_DEPTH, &tint, 1.0f, 1.0f);
}

/* ---- primitives -------------------------------------------------------- */

void gfx_image(GfxTex *t, float x, float y, float w, float h, float angle, float alpha)
{
    if (!t || alpha <= 0)
        return;
    /* Negative sizes mirror: C2D_DrawImage swaps the UVs and C2Di_CalcQuad
     * uses fabs() for the extent, so the pivot stays at the box centre.
     * (Swapping sub.top/bottom instead would mean "rotated" to citro2d.) */
    float aw = fabsf(w), ah = fabsf(h);
    C2D_Image img = {&t->tex, &t->sub};
    C2D_DrawParams p;
    p.pos.x = x + aw / 2;
    p.pos.y = y + ah / 2;
    p.pos.w = w;
    p.pos.h = h;
    p.center.x = aw / 2;
    p.center.y = ah / 2;
    p.depth = DRAW_DEPTH;
    p.angle = angle;
    C2D_ImageTint tint;
    C2D_PlainImageTint(&tint, C2D_Color32f(1, 1, 1, alpha), 0.0f);
    C2D_DrawImage(img, &p, alpha < 1.0f ? &tint : NULL);
}

void gfx_rect(float x, float y, float w, float h, u32 rgba)
{
    if ((rgba & 0xFF) == 0)
        return;
    C2D_DrawRectSolid(x, y, DRAW_DEPTH, w, h, col(rgba));
}

void gfx_gradient(float x, float y, float w, float h, u32 top, u32 bottom)
{
    C2D_DrawRectangle(x, y, DRAW_DEPTH, w, h, col(top), col(top), col(bottom), col(bottom));
}

void gfx_triangle(float x0, float y0, float x1, float y1, float x2, float y2, u32 rgba)
{
    if ((rgba & 0xFF) == 0)
        return;
    u32 c = col(rgba);
    C2D_DrawTriangle(x0, y0, c, x1, y1, c, x2, y2, c, DRAW_DEPTH);
}

void gfx_circle(float x, float y, float r, u32 rgba)
{
    if ((rgba & 0xFF) == 0 || r <= 0)
        return;
    C2D_DrawCircleSolid(x, y, DRAW_DEPTH, r, col(rgba));
}

void gfx_line(float x0, float y0, float x1, float y1, float thick, u32 rgba)
{
    if ((rgba & 0xFF) == 0)
        return;
    u32 c = col(rgba);
    C2D_DrawLine(x0, y0, c, x1, y1, c, thick, DRAW_DEPTH);
}

void gfx_draw_capture_part(int eye, float sx, float sy, float sw, float sh,
                           float dx, float dy, float dw, float dh, float alpha)
{
    if (!cap_ok[eye] || alpha <= 0 || sw <= 0 || sh <= 0)
        return;
    Tex3DS_SubTexture sub;
    sub.width = (u16)sw;
    sub.height = (u16)sh;
    sub.left = sx / 512.0f;
    sub.right = (sx + sw) / 512.0f;
    sub.top = 1.0f - sy / 256.0f;
    sub.bottom = 1.0f - (sy + sh) / 256.0f;
    C2D_Image img = {&cap_tex[eye], &sub};
    C2D_ImageTint tint;
    C2D_PlainImageTint(&tint, C2D_Color32f(1, 1, 1, alpha), 0.0f);
    C2D_DrawImageAt(img, dx, dy, DRAW_DEPTH, alpha < 1.0f ? &tint : NULL, dw / sw, dh / sh);
}

/* ---- text (system font) ------------------------------------------------ */

void gfx_text(const char *s, float x, float y, float scale, u32 rgba)
{
    if (!s || !*s || (rgba & 0xFF) == 0)
        return;
    C2D_Text text;
    C2D_TextParse(&text, textbuf, s);
    C2D_TextOptimize(&text);
    C2D_DrawText(&text, C2D_WithColor, x, y, DRAW_DEPTH, scale, scale, col(rgba));
}

float gfx_text_width(const char *s, float scale)
{
    if (!s || !*s)
        return 0;
    C2D_TextBufClear(measurebuf);
    C2D_Text text;
    C2D_TextParse(&text, measurebuf, s);
    float w = 0, h = 0;
    C2D_TextGetDimensions(&text, scale, scale, &w, &h);
    return w;
}

/* citro2d draws the system font at 30 / cellHeight of its native size and
 * spaces lines by ceil(scale * that * lineFeed); match it so wrapping agrees
 * with what C2D_DrawText produces. */
static float font_scale(void)
{
    return 30.0f / (float)fontGetGlyphInfo(fontGetSystemFont())->cellHeight;
}

float gfx_glyph_advance(u32 cp, float scale)
{
    CFNT_s *font = fontGetSystemFont();
    int idx = fontGlyphIndexFromCodePoint(font, cp);
    charWidthInfo_s *cw = fontGetCharWidthInfo(font, idx);
    return cw ? cw->charWidth * scale * font_scale() : 0;
}

float gfx_line_height(float scale)
{
    return ceilf(scale * font_scale() * fontGetInfo(fontGetSystemFont())->lineFeed);
}

float gfx_slider(void)
{
    return osGet3DSliderState();
}
