#include "app.h"
#include "jpeg.h"

/* Textures live in linear RAM on the 3DS; keep the working set bounded and
 * evict least-recently-drawn ones. Anything drawn this frame is kept, since
 * the GPU may still read it. */

#define CACHE_MAX 128
#define CACHE_BUDGET (20u << 20)

typedef struct {
    s32 res;
    s32 base;          /* patched images: the picture res is laid over; else -1 */
    GfxTex *tex;
    u32 bytes;
    u32 last;
    bool failed;
} Entry;

static Entry cache[CACHE_MAX];
static int ncache;
static u32 total;

static void drop(int i)
{
    if (cache[i].tex)
        gfx_tex_free(cache[i].tex);
    total -= cache[i].bytes;
    cache[i] = cache[--ncache];
}

/* ---- patched images (vnpack --cg-patches) ------------------------------- */

/* Texel index in the PICA200 layout: 8x8 tiles row-major, Morton inside. */
static inline u32 texel(int x, int y, int tw)
{
    return (u32)(((y >> 3) * (tw >> 3) + (x >> 3)) * 64) |
           (u32)((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) |
                 ((y & 4) << 3));
}

/* A JPEG .ctex file: the header fields and the JPEG payload (malloc'd). */
static u8 *read_jpeg_ctex(s32 res, int *tw, int *th, int *iw, int *ih, u32 *len)
{
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    FILE *f = fopen(path, "rb");
    if (!f)
        return NULL;
    u8 hdr[36];
    u8 *jpg = NULL;
    if (fread(hdr, 1, 36, f) == 36 && memcmp(hdr, "CTEX", 4) == 0 && rd_u16(hdr + 6) == 2 &&
        (rd_u32(hdr + 24) & 2)) {
        *tw = rd_u16(hdr + 8);
        *th = rd_u16(hdr + 10);
        *iw = rd_u16(hdr + 12);
        *ih = rd_u16(hdr + 14);
        *len = rd_u32(hdr + 32);
        jpg = *len > 0 && *len < (8u << 20) ? malloc(*len) : NULL;
        if (jpg && fread(jpg, 1, *len, f) != *len) {
            free(jpg);
            jpg = NULL;
        }
    }
    fclose(f);
    return jpg;
}

/* The base picture with the patch decoded into it at texel (px, py). */
static GfxTex *load_patched(s32 base, s32 patch, int px, int py, u32 *bytes)
{
    int tw, th, iw, ih, ptw, pth, pw, ph, w, h;
    u32 blen, plen;
    u8 *bj = read_jpeg_ctex(base, &tw, &th, &iw, &ih, &blen);
    u8 *pj = bj ? read_jpeg_ctex(patch, &ptw, &pth, &pw, &ph, &plen) : NULL;
    GfxTex *t = NULL;
    u16 *pp = NULL;
    if (!pj || px < 0 || py < 0 || px + pw > iw || py + ph > ih || (tw & 7) || (th & 7))
        goto out;
    ptw = (pw + 7) & ~7;
    pth = (ph + 7) & ~7;
    pp = malloc((size_t)ptw * (size_t)pth * 2);
    t = gfx_tex_create(tw, th, 2, iw, ih);
    if (!pp || !t)
        goto fail;
    u16 *d = gfx_tex_data(t);
    if (jpeg_decode_tiled565(bj, blen, d, tw, th, &w, &h) != JPEG_OK || w != iw || h != ih ||
        jpeg_decode_tiled565(pj, plen, pp, ptw, pth, &w, &h) != JPEG_OK || w != pw || h != ph)
        goto fail;
    for (int y = 0; y < ph; y++)
        for (int x = 0; x < pw; x++)
            d[texel(px + x, py + y, tw)] = pp[texel(x, y, ptw)];
    /* the padding repeats the edge texels, as when the picture is loaded alone */
    if (px + pw == iw)
        for (int y = py; y < py + ph; y++)
            for (int x = iw; x < tw; x++)
                d[texel(x, y, tw)] = d[texel(iw - 1, y, tw)];
    if (py + ph == ih) {
        int x1 = px + pw == iw ? tw : px + pw;
        for (int y = ih; y < th; y++)
            for (int x = px; x < x1; x++)
                d[texel(x, y, tw)] = d[texel(x, ih - 1, tw)];
    }
    gfx_tex_commit(t);
    *bytes = (u32)tw * (u32)th * 2;
    goto out;
fail:
    if (t)
        gfx_tex_free(t);
    t = NULL;
out:
    free(pp);
    free(bj);
    free(pj);
    return t;
}

static GfxTex *cache_get(s32 res, s32 base, int px, int py)
{
    if (res < 0 || !E.loaded)
        return NULL;
    for (int i = 0; i < ncache; i++) {
        if (cache[i].res == res && cache[i].base == base) {
            cache[i].last = E.frame;
            return cache[i].tex;
        }
    }
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    u32 bytes = 0;
    GfxTex *tex = base >= 0 ? load_patched(base, res, px, py, &bytes) : gfx_tex_load(path, &bytes);
    if (!tex)
        LOG("cannot load texture %s", path);
    for (;;) {
        if (total + bytes <= CACHE_BUDGET && ncache < CACHE_MAX)
            break;
        int lru = -1;
        for (int i = 0; i < ncache; i++)
            if (cache[i].last < E.frame && (lru < 0 || cache[i].last < cache[lru].last))
                lru = i;
        if (lru < 0)
            break;
        drop(lru);
    }
    if (ncache >= CACHE_MAX) {
        if (tex)
            gfx_tex_free(tex);
        return NULL;
    }
    Entry *e = &cache[ncache++];
    e->res = res;
    e->base = base;
    e->tex = tex;
    e->bytes = bytes;
    e->last = E.frame;
    e->failed = tex == NULL;
    total += bytes;
    return tex;
}

GfxTex *texcache_get(s32 res)
{
    return cache_get(res, -1, 0, 0);
}

GfxTex *texcache_image(const ImageDef *im)
{
    if (im->patch_res >= 0 && im->res >= 0) {
        GfxTex *t = cache_get(im->patch_res, im->res, im->patch_x, im->patch_y);
        if (t)
            return t;   /* else the base picture alone: close, and better than nothing */
    }
    return texcache_get(im->res);
}

void texcache_clear(void)
{
    while (ncache > 0)
        drop(ncache - 1);
    total = 0;
}
