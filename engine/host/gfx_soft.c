/* Software implementation of gfx.h for the desktop test build. It decodes the
 * same .ctex files the 3DS loads (un-tiling them), so the packager's texture
 * layout is exercised too. */

#include "../source/gfx.h"
#include "font_data.h"
#include "host.h"

#include <zlib.h>

typedef struct {
    int w, h;
    u8 *px; /* RGBA */
} Surf;

struct GfxTex {
    int w, h;
    u8 *px; /* RGBA, top row first */
    /* dynamic textures keep their native tiled buffer too */
    u8 *native;
    int tw, th, fmt;
};

static Surf top_s[2], bot_s, cap_s[2], snap_s;
static Surf *cur;
float host_slider_value = 1.0f;

static void surf_init(Surf *s, int w, int h)
{
    s->w = w;
    s->h = h;
    s->px = calloc((size_t)(w * h), 4);
}

bool gfx_init(void)
{
    surf_init(&top_s[0], TOP_W, TOP_H);
    surf_init(&top_s[1], TOP_W, TOP_H);
    surf_init(&cap_s[0], TOP_W, TOP_H);
    surf_init(&cap_s[1], TOP_W, TOP_H);
    surf_init(&bot_s, BOT_W, BOT_H);
    surf_init(&snap_s, TOP_W, TOP_H);
    cur = &top_s[0];
    return true;
}

void gfx_exit(void) {}

const u8 *host_surface(int which, int *w, int *h)
{
    const Surf *s = which == 0 ? &top_s[0] : which == 1 ? &top_s[1] : &bot_s;
    *w = s->w;
    *h = s->h;
    return s->px;
}

/* ---- textures ---------------------------------------------------------- */

static int morton(int x, int y)
{
    return (x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) |
           ((y & 4) << 3);
}

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
    u8 *data = malloc(stored);
    if (fread(data, 1, stored, f) != stored) {
        free(data);
        fclose(f);
        return NULL;
    }
    fclose(f);
    u8 *pix = data;
    if (flags & 1) {
        pix = malloc(raw);
        uLongf n = raw;
        if (uncompress(pix, &n, data, stored) != Z_OK || n != raw) {
            free(pix);
            free(data);
            return NULL;
        }
        free(data);
    }
    int bpp = fmt == 0 ? 4 : fmt == 1 ? 3 : 2;
    if ((u32)(tw * th * bpp) != raw) {
        free(pix);
        return NULL;
    }
    GfxTex *t = calloc(1, sizeof(GfxTex));
    t->w = iw;
    t->h = ih;
    t->px = malloc((size_t)(iw * ih * 4));
    for (int y = 0; y < ih; y++) {
        int r = y; /* top row is stored first (v = 1.0) */
        for (int x = 0; x < iw; x++) {
            int idx = ((r >> 3) * (tw >> 3) + (x >> 3)) * 64 + morton(x, r);
            const u8 *s = pix + idx * bpp;
            u8 *d = t->px + (y * iw + x) * 4;
            if (fmt == 0) {
                d[0] = s[3]; d[1] = s[2]; d[2] = s[1]; d[3] = s[0];
            } else if (fmt == 1) {
                d[0] = s[2]; d[1] = s[1]; d[2] = s[0]; d[3] = 255;
            } else {
                u16 v = (u16)(s[0] | (s[1] << 8));
                d[0] = (u8)(((v >> 11) & 31) * 255 / 31);
                d[1] = (u8)(((v >> 5) & 63) * 255 / 63);
                d[2] = (u8)((v & 31) * 255 / 31);
                d[3] = 255;
            }
        }
    }
    free(pix);
    *bytes = (u32)(tw * th * bpp);
    return t;
}

void gfx_tex_free(GfxTex *t)
{
    if (!t)
        return;
    free(t->px);
    free(t->native);
    free(t);
}

static void untile(GfxTex *t, const u8 *pix, int fmt, int tw, int th)
{
    int bpp = fmt == 0 ? 4 : fmt == 1 ? 3 : 2;
    for (int y = 0; y < t->h; y++) {
        for (int x = 0; x < t->w; x++) {
            int idx = ((y >> 3) * (tw >> 3) + (x >> 3)) * 64 + morton(x, y);
            const u8 *s = pix + idx * bpp;
            u8 *d = t->px + (y * t->w + x) * 4;
            if (fmt == 0) {
                d[0] = s[3]; d[1] = s[2]; d[2] = s[1]; d[3] = s[0];
            } else if (fmt == 1) {
                d[0] = s[2]; d[1] = s[1]; d[2] = s[0]; d[3] = 255;
            } else {
                u16 v = (u16)(s[0] | (s[1] << 8));
                d[0] = (u8)(((v >> 11) & 31) * 255 / 31);
                d[1] = (u8)(((v >> 5) & 63) * 255 / 63);
                d[2] = (u8)((v & 31) * 255 / 31);
                d[3] = 255;
            }
        }
    }
    (void)th;
}

GfxTex *gfx_tex_create(int tw, int th, int fmt, int iw, int ih)
{
    int bpp = fmt == 0 ? 4 : fmt == 1 ? 3 : 2;
    GfxTex *t = calloc(1, sizeof(GfxTex));
    t->w = iw;
    t->h = ih;
    t->tw = tw;
    t->th = th;
    t->fmt = fmt;
    t->px = calloc((size_t)(iw * ih), 4);
    t->native = calloc((size_t)(tw * th), (size_t)bpp);
    return t;
}

void *gfx_tex_data(GfxTex *t) { return t->native; }

void gfx_tex_commit(GfxTex *t)
{
    untile(t, t->native, t->fmt, t->tw, t->th);
}

/* ---- targets ---------------------------------------------------------- */

static void clear(Surf *s, u32 c)
{
    for (int i = 0; i < s->w * s->h; i++) {
        s->px[i * 4 + 0] = (u8)(c >> 24);
        s->px[i * 4 + 1] = (u8)(c >> 16);
        s->px[i * 4 + 2] = (u8)(c >> 8);
        s->px[i * 4 + 3] = 255;
    }
}

void gfx_frame_begin(void) {}
void gfx_frame_end(void) {}

void gfx_target_top(int eye, u32 c)
{
    cur = &top_s[eye];
    clear(cur, c);
}

void gfx_target_bottom(u32 c)
{
    cur = &bot_s;
    clear(cur, c);
}

void gfx_target_snapshot(u32 c)
{
    cur = &snap_s;
    clear(cur, c);
}

bool gfx_snapshot_read(u16 *out, int w, int h)
{
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            const u8 *p = snap_s.px + ((y * TOP_H / h) * TOP_W + x * TOP_W / w) * 4;
            out[y * w + x] = (u16)(((p[0] >> 3) << 11) | ((p[1] >> 2) << 5) | (p[2] >> 3));
        }
    return true;
}

GfxTex *gfx_tex_from_rgb565(const u16 *px, int w, int h)
{
    GfxTex *t = calloc(1, sizeof(GfxTex));
    if (!t)
        return NULL;
    t->w = w;
    t->h = h;
    t->px = malloc((size_t)(w * h * 4));
    for (int i = 0; i < w * h; i++) {
        u16 v = px[i];
        t->px[i * 4 + 0] = (u8)(((v >> 11) & 31) * 255 / 31);
        t->px[i * 4 + 1] = (u8)(((v >> 5) & 63) * 255 / 63);
        t->px[i * 4 + 2] = (u8)((v & 31) * 255 / 31);
        t->px[i * 4 + 3] = 255;
    }
    return t;
}

void gfx_target_capture(int eye, u32 c)
{
    cur = &cap_s[eye];
    clear(cur, c);
}

static inline void blend(u8 *d, float r, float g, float b, float a)
{
    if (a <= 0)
        return;
    if (a > 1)
        a = 1;
    d[0] = (u8)(d[0] + (r - d[0]) * a);
    d[1] = (u8)(d[1] + (g - d[1]) * a);
    d[2] = (u8)(d[2] + (b - d[2]) * a);
}

void gfx_draw_capture(int eye, float alpha)
{
    const Surf *s = &cap_s[eye];
    for (int i = 0; i < s->w * s->h; i++)
        blend(cur->px + i * 4, s->px[i * 4], s->px[i * 4 + 1], s->px[i * 4 + 2], alpha);
}

/* ---- primitives ----------------------------------------------------------- */

void gfx_rect(float x, float y, float w, float h, u32 c)
{
    int x0 = (int)fmaxf(0, floorf(x + 0.5f)), y0 = (int)fmaxf(0, floorf(y + 0.5f));
    int x1 = (int)fminf((float)cur->w, floorf(x + w + 0.5f));
    int y1 = (int)fminf((float)cur->h, floorf(y + h + 0.5f));
    float a = (float)(c & 0xFF) / 255.0f;
    for (int py = y0; py < y1; py++)
        for (int px = x0; px < x1; px++)
            blend(cur->px + (py * cur->w + px) * 4, (float)(c >> 24), (float)((c >> 16) & 0xFF),
                  (float)((c >> 8) & 0xFF), a);
}

void gfx_gradient(float x, float y, float w, float h, u32 a, u32 b)
{
    for (int i = 0; i < (int)h; i++) {
        float t = h > 1 ? (float)i / (h - 1) : 0;
        u32 c = 0;
        for (int k = 0; k < 4; k++) {
            float va = (float)((a >> (24 - 8 * k)) & 0xFF), vb = (float)((b >> (24 - 8 * k)) & 0xFF);
            c |= (u32)(va + (vb - va) * t) << (24 - 8 * k);
        }
        gfx_rect(x, y + (float)i, w, 1, c);
    }
}

static inline void blend_c(u8 *d, u32 c)
{
    blend(d, (float)(c >> 24), (float)((c >> 16) & 0xFF), (float)((c >> 8) & 0xFF),
          (float)(c & 0xFF) / 255.0f);
}

static float edge(float ax, float ay, float bx, float by, float px, float py)
{
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax);
}

void gfx_triangle(float x0, float y0, float x1, float y1, float x2, float y2, u32 c)
{
    if ((c & 0xFF) == 0)
        return;
    float area = edge(x0, y0, x1, y1, x2, y2);
    if (fabsf(area) < 1e-6f)
        return;
    int minx = (int)fmaxf(0, floorf(fminf(x0, fminf(x1, x2))));
    int maxx = (int)fminf((float)cur->w - 1, ceilf(fmaxf(x0, fmaxf(x1, x2))));
    int miny = (int)fmaxf(0, floorf(fminf(y0, fminf(y1, y2))));
    int maxy = (int)fminf((float)cur->h - 1, ceilf(fmaxf(y0, fmaxf(y1, y2))));
    for (int py = miny; py <= maxy; py++)
        for (int px = minx; px <= maxx; px++) {
            float cx = (float)px + 0.5f, cy = (float)py + 0.5f;
            float w0 = edge(x1, y1, x2, y2, cx, cy), w1 = edge(x2, y2, x0, y0, cx, cy);
            float w2 = edge(x0, y0, x1, y1, cx, cy);
            if (area > 0 ? (w0 >= 0 && w1 >= 0 && w2 >= 0) : (w0 <= 0 && w1 <= 0 && w2 <= 0))
                blend_c(cur->px + (py * cur->w + px) * 4, c);
        }
}

void gfx_circle(float x, float y, float r, u32 c)
{
    if ((c & 0xFF) == 0 || r <= 0)
        return;
    int x0 = (int)fmaxf(0, floorf(x - r)), x1 = (int)fminf((float)cur->w - 1, ceilf(x + r));
    int y0 = (int)fmaxf(0, floorf(y - r)), y1 = (int)fminf((float)cur->h - 1, ceilf(y + r));
    for (int py = y0; py <= y1; py++)
        for (int px = x0; px <= x1; px++) {
            float dx = (float)px + 0.5f - x, dy = (float)py + 0.5f - y;
            if (dx * dx + dy * dy <= r * r)
                blend_c(cur->px + (py * cur->w + px) * 4, c);
        }
}

void gfx_line(float x0, float y0, float x1, float y1, float thick, u32 c)
{
    float dx = x1 - x0, dy = y1 - y0, len = sqrtf(dx * dx + dy * dy);
    if (len < 1e-4f)
        return;
    float nx = -dy / len * thick / 2, ny = dx / len * thick / 2;
    gfx_triangle(x0 + nx, y0 + ny, x1 + nx, y1 + ny, x1 - nx, y1 - ny, c);
    gfx_triangle(x0 + nx, y0 + ny, x1 - nx, y1 - ny, x0 - nx, y0 - ny, c);
}

void gfx_draw_capture_part(int eye, float sx, float sy, float sw, float sh,
                           float dx, float dy, float dw, float dh, float alpha)
{
    const Surf *s = &cap_s[eye];
    if (alpha <= 0 || sw <= 0 || sh <= 0 || dw <= 0 || dh <= 0)
        return;
    int x0 = (int)fmaxf(0, floorf(dx)), x1 = (int)fminf((float)cur->w, ceilf(dx + dw));
    int y0 = (int)fmaxf(0, floorf(dy)), y1 = (int)fminf((float)cur->h, ceilf(dy + dh));
    for (int py = y0; py < y1; py++)
        for (int px = x0; px < x1; px++) {
            float u = sx + ((float)px + 0.5f - dx) / dw * sw;
            float v = sy + ((float)py + 0.5f - dy) / dh * sh;
            int iu = (int)u, iv = (int)v;
            if (iu < 0 || iv < 0 || iu >= s->w || iv >= s->h)
                continue;
            const u8 *p = s->px + (iv * s->w + iu) * 4;
            blend(cur->px + (py * cur->w + px) * 4, p[0], p[1], p[2], alpha);
        }
}

/* Bilinear sample of an RGBA image (u, v in texels, clamped). */
static void sample(const u8 *px, int w, int h, int stride_ch, float u, float v, float out[4])
{
    u -= 0.5f;
    v -= 0.5f;
    int x0 = (int)floorf(u), y0 = (int)floorf(v);
    float fx = u - (float)x0, fy = v - (float)y0;
    for (int k = 0; k < stride_ch; k++)
        out[k] = 0;
    for (int j = 0; j < 2; j++) {
        for (int i = 0; i < 2; i++) {
            int xx = x0 + i, yy = y0 + j;
            xx = xx < 0 ? 0 : (xx >= w ? w - 1 : xx);
            yy = yy < 0 ? 0 : (yy >= h ? h - 1 : yy);
            float wgt = (i ? fx : 1 - fx) * (j ? fy : 1 - fy);
            const u8 *p = px + (yy * w + xx) * stride_ch;
            for (int k = 0; k < stride_ch; k++)
                out[k] += p[k] * wgt;
        }
    }
}

void gfx_image(GfxTex *t, float x, float y, float w, float h, float angle, float alpha)
{
    if (!t || w == 0 || h == 0)
        return;
    float aw = fabsf(w), ah = fabsf(h);
    float cx = x + aw / 2, cy = y + ah / 2;
    float ca = cosf(angle), sa = sinf(angle);
    /* bounding box of the rotated quad */
    float ex = fabsf(ca) * aw / 2 + fabsf(sa) * ah / 2;
    float ey = fabsf(sa) * aw / 2 + fabsf(ca) * ah / 2;
    int x0 = (int)fmaxf(0, floorf(cx - ex)), x1 = (int)fminf((float)cur->w, ceilf(cx + ex));
    int y0 = (int)fmaxf(0, floorf(cy - ey)), y1 = (int)fminf((float)cur->h, ceilf(cy + ey));
    for (int py = y0; py < y1; py++) {
        for (int px = x0; px < x1; px++) {
            float dx = (float)px + 0.5f - cx, dy = (float)py + 0.5f - cy;
            float qx = ca * dx + sa * dy, qy = -sa * dx + ca * dy;
            float u = (qx + aw / 2) / aw, v = (qy + ah / 2) / ah;
            if (u < 0 || u >= 1 || v < 0 || v >= 1)
                continue;
            if (w < 0)
                u = 1 - u;
            if (h < 0)
                v = 1 - v;
            float s[4];
            sample(t->px, t->w, t->h, 4, u * (float)t->w, v * (float)t->h, s);
            blend(cur->px + (py * cur->w + px) * 4, s[0], s[1], s[2], s[3] / 255.0f * alpha);
        }
    }
}

/* ---- text ----------------------------------------------------------- */

static const FontGlyph *glyph(u32 cp)
{
    for (int i = 0; i < FONT_NGLYPHS; i++)
        if (FONT_GLYPHS[i].cp == cp)
            return &FONT_GLYPHS[i];
    if (cp != '?')
        return glyph('?');
    return NULL;
}

float gfx_glyph_advance(u32 cp, float scale)
{
    const FontGlyph *g = glyph(cp);
    return g ? g->adv * scale : 0;
}

float gfx_line_height(float scale)
{
    return FONT_LINE_FEED * scale;
}

float gfx_text_width(const char *s, float scale)
{
    float w = 0, best = 0;
    u32 cp;
    int k;
    while ((k = utf8_decode(s, &cp)) > 0) {
        if (cp == '\n') {
            best = fmaxf(best, w);
            w = 0;
        } else {
            w += gfx_glyph_advance(cp, scale);
        }
        s += k;
    }
    return fmaxf(best, w);
}

void gfx_text(const char *s, float x, float y, float scale, u32 color)
{
    float pen = x;
    float r = (float)(color >> 24), g = (float)((color >> 16) & 0xFF), b = (float)((color >> 8) & 0xFF);
    float a = (float)(color & 0xFF) / 255.0f;
    u32 cp;
    int k;
    while ((k = utf8_decode(s, &cp)) > 0) {
        s += k;
        if (cp == '\n') {
            pen = x;
            y += FONT_LINE_FEED * scale;
            continue;
        }
        const FontGlyph *gl = glyph(cp);
        if (!gl)
            continue;
        float gx = pen + gl->ox * scale, gy = y + gl->oy * scale;
        float gw = gl->w * scale, gh = gl->h * scale;
        int x0 = (int)fmaxf(0, floorf(gx)), x1 = (int)fminf((float)cur->w, ceilf(gx + gw));
        int y0 = (int)fmaxf(0, floorf(gy)), y1 = (int)fminf((float)cur->h, ceilf(gy + gh));
        for (int py = y0; py < y1; py++) {
            for (int px = x0; px < x1; px++) {
                /* 3x3 supersampling of the glyph's coverage */
                float cov = 0;
                for (int sy = 0; sy < 3; sy++) {
                    for (int sx = 0; sx < 3; sx++) {
                        float u = ((float)px + (sx + 0.5f) / 3 - gx) / scale;
                        float v = ((float)py + (sy + 0.5f) / 3 - gy) / scale;
                        if (u < 0 || v < 0 || u >= gl->w || v >= gl->h)
                            continue;
                        cov += FONT_ATLAS[(gl->y + (int)v) * FONT_ATLAS_W + gl->x + (int)u];
                    }
                }
                blend(cur->px + (py * cur->w + px) * 4, r, g, b, cov / (9 * 255.0f) * a);
            }
        }
        pen += gl->adv * scale;
    }
}

float gfx_slider(void)
{
    return host_slider_value;
}
