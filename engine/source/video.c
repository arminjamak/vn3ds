/* Video playback for Ren'Py Movie() images (.cvid, see tools/vnpack/assets.py).
 *
 * Each frame is a zlib-compressed XOR delta against the previous frame,
 * already in the GPU's tiled layout. A player keeps the current frame in
 * memory, applies deltas as time passes and uploads into one of two
 * textures (double buffered, so the GPU never reads a half-written frame). */

#include "app.h"
#include "video.h"

#include <zlib.h>

#define MAX_VIDEOS 4

typedef struct {
    bool used;
    s32 res;
    FILE *f;
    u32 nframes;
    float fps;
    bool loop;
    int version;
    u32 ntiles;
    u32 *offs, *sizes;
    u8 *accum, *delta, *zbuf;
    size_t raw, zcap;
    GfxTex *tex[2];
    int cur;
    float t;
    int shown;
    u32 last_used;
} Video;

static Video V[MAX_VIDEOS];

static void close_video(Video *v)
{
    if (v->f)
        fclose(v->f);
    for (int i = 0; i < 2; i++)
        if (v->tex[i])
            gfx_tex_free(v->tex[i]);
    free(v->offs);
    free(v->sizes);
    free(v->accum);
    free(v->delta);
    free(v->zbuf);
    memset(v, 0, sizeof(*v));
}

static bool open_video(Video *v, s32 res)
{
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    memset(v, 0, sizeof(*v));
    v->f = fopen(path, "rb");
    if (!v->f)
        return false;
    u8 h[40];
    if (fread(h, 1, 40, v->f) != 40 || memcmp(h, "CVID", 4) != 0 || rd_u16(h + 6) != 2 ||
        (rd_u16(h + 4) != 1 && rd_u16(h + 4) != 2)) {
        close_video(v);
        return false;
    }
    int tw = rd_u16(h + 8), th = rd_u16(h + 10), iw = rd_u16(h + 12), ih = rd_u16(h + 14);
    v->fps = rd_f32(h + 24);
    v->nframes = rd_u32(h + 28);
    v->loop = rd_u32(h + 32) & 1;
    v->version = rd_u16(h + 4);
    v->raw = (size_t)tw * th * 2;
    v->ntiles = (u32)(tw / 8) * (u32)(th / 8);
    v->offs = malloc(4 * v->nframes);
    v->sizes = malloc(4 * v->nframes);
    v->accum = calloc(1, v->raw);
    v->delta = malloc(v->raw + v->ntiles / 8 + 8);
    if (!v->offs || !v->sizes || !v->accum || !v->delta || v->nframes == 0 ||
        fread(v->offs, 4, v->nframes, v->f) != v->nframes ||
        fread(v->sizes, 4, v->nframes, v->f) != v->nframes) {
        close_video(v);
        return false;
    }
    for (int i = 0; i < 2; i++) {
        v->tex[i] = gfx_tex_create(tw, th, 2, iw, ih);
        if (!v->tex[i]) {
            close_video(v);
            return false;
        }
    }
    v->used = true;
    v->res = res;
    v->shown = -1;
    return true;
}

static bool decode(Video *v, u32 k)
{
    u32 n = v->sizes[k];
    if (n > v->zcap) {
        free(v->zbuf);
        v->zbuf = malloc(n);
        v->zcap = v->zbuf ? n : 0;
        if (!v->zbuf)
            return false;
    }
    if (fseek(v->f, (long)v->offs[k], SEEK_SET) != 0 || fread(v->zbuf, 1, n, v->f) != n)
        return false;
    if (v->version == 1) {   /* whole-frame XOR delta */
        uLongf out = (uLongf)v->raw;
        if (uncompress(v->delta, &out, v->zbuf, n) != Z_OK || out != v->raw)
            return false;
        u32 *a = (u32 *)v->accum;
        const u32 *d = (const u32 *)v->delta;
        for (size_t i = 0; i < v->raw / 4; i++)
            a[i] ^= d[i];
        return true;
    }
    /* version 2: bitmap of changed 8x8 tiles, then those tiles */
    uLongf out = (uLongf)(v->raw + v->ntiles / 8 + 8);
    if (uncompress(v->delta, &out, v->zbuf, n) != Z_OK || out < v->ntiles / 8)
        return false;
    const u8 *bits = v->delta;
    const u8 *tile = v->delta + v->ntiles / 8;
    const u8 *end = v->delta + out;
    for (u32 t = 0; t < v->ntiles; t++) {
        if (!(bits[t >> 3] & (1u << (t & 7))))
            continue;
        if (tile + 128 > end)
            return false;
        memcpy(v->accum + (size_t)t * 128, tile, 128);
        tile += 128;
    }
    return true;
}

static void present(Video *v)
{
    int next = v->cur ^ 1;
    memcpy(gfx_tex_data(v->tex[next]), v->accum, v->raw);
    gfx_tex_commit(v->tex[next]);
    v->cur = next;
}

GfxTex *video_tex(s32 res)
{
    Video *free_slot = NULL;
    for (int i = 0; i < MAX_VIDEOS; i++) {
        if (V[i].used && V[i].res == res) {
            V[i].last_used = E.frame;
            return V[i].shown >= 0 ? V[i].tex[V[i].cur] : NULL;
        }
        if (!V[i].used && !free_slot)
            free_slot = &V[i];
    }
    if (!free_slot) {   /* reuse the least recently drawn */
        free_slot = &V[0];
        for (int i = 1; i < MAX_VIDEOS; i++)
            if (V[i].last_used < free_slot->last_used)
                free_slot = &V[i];
        close_video(free_slot);
    }
    if (!open_video(free_slot, res)) {
        LOG("cannot open video resource %d", (int)res);
        return NULL;
    }
    free_slot->last_used = E.frame;
    if (decode(free_slot, 0)) {
        free_slot->shown = 0;
        present(free_slot);
    }
    return free_slot->shown >= 0 ? free_slot->tex[free_slot->cur] : NULL;
}

void video_update(float dt)
{
    for (int i = 0; i < MAX_VIDEOS; i++) {
        Video *v = &V[i];
        if (!v->used)
            continue;
        if (E.frame - v->last_used > 3) {   /* not on screen any more */
            close_video(v);
            continue;
        }
        v->t += dt;
        int target = (int)(v->t * v->fps);
        if (target >= (int)v->nframes) {
            if (v->loop) {
                v->t = fmodf(v->t, v->nframes / v->fps);
                target = (int)(v->t * v->fps);
                if (v->version == 1)
                    memset(v->accum, 0, v->raw);   /* v1 deltas restart from black */
                v->shown = -1;
            } else {
                target = (int)v->nframes - 1;   /* hold the last frame */
            }
        }
        if (target <= v->shown)
            continue;
        bool ok = true;
        for (int k = v->shown + 1; k <= target && ok; k++)
            ok = decode(v, (u32)k);
        if (ok) {
            v->shown = target;
            present(v);
        } else {
            LOG("video %d: bad frame data", (int)v->res);
            close_video(v);
        }
    }
}

void video_close_all(void)
{
    for (int i = 0; i < MAX_VIDEOS; i++)
        if (V[i].used)
            close_video(&V[i]);
}
