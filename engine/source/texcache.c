#include "app.h"
#include "bg.h"
#include "jpeg.h"

#include <zlib.h>

/* Textures live in linear RAM on the 3DS; keep the working set bounded and
 * evict least-recently-drawn ones. Anything drawn this frame is kept, since
 * the GPU may still read it.
 *
 * Preloading. After each step of the story, predict.c lists the pictures
 * the next few statements may show (texcache_want); they are read and
 * decoded on the background thread while the player reads, so pressing A
 * never waits for the SD card. A preload goes in stages:
 *   QUEUED   -> the background thread reads the .ctex file(s) (READ);
 *   READ     -> the main thread allocates the texture (texcache_pump), as
 *               linear memory may only be allocated there (DECODE);
 *   DECODE   -> the background thread decodes into it (DONE);
 *   DONE     -> the main thread flushes it for the GPU and it is cached.
 * A picture needed before its preload is done is finished on the spot (the
 * main thread does the remaining stages itself, or waits for the one the
 * background thread is in the middle of). Preloads the story turned away
 * from (another branch) are cancelled if they haven't started, otherwise
 * kept as ordinary cache entries.
 *
 * Memory: CACHE_BUDGET for everything cached, of which at most
 * PRELOAD_BUDGET may be preloaded pictures that haven't been drawn yet, and
 * at most MAX_JOBS preloads in flight; a preload that doesn't fit is
 * dropped (and loaded when needed, as before). */

#define CACHE_MAX 160
#define CACHE_BUDGET (20u << 20)
#define PRELOAD_BUDGET (8u << 20)
#define MAX_JOBS 24

enum { J_QUEUED, J_READING, J_READ, J_DECODE, J_DECODING, J_DONE, J_FAILED };

/* A .ctex file's header and stored bytes. */
typedef struct {
    int fmt, tw, th, iw, ih;
    u32 flags, raw, stored;
    u8 *payload;
} Ctex;

typedef struct {
    int state;           /* J_*, under bg_lock */
    s32 res, base;       /* base >= 0: res is a patch laid over base at (px, py) */
    int px, py;
    Ctex a, b;           /* the picture (or the base), and the patch */
    GfxTex *tex;
    u32 bytes;
    bool ok;
    u64 t_queue, read_us, dec_us;
} Job;

typedef struct {
    s32 res;
    s32 base;          /* patched images: the picture res is laid over; else -1 */
    GfxTex *tex;
    u32 bytes;
    u32 last;
    bool failed;
    Job *job;          /* a preload in flight */
    u32 want;          /* the prediction that last asked for it */
    bool preloaded, used;
} Entry;

static Entry cache[CACHE_MAX];
static int ncache;
static u32 total;
static u32 want_gen = 1;
static Job *jobs[MAX_JOBS];   /* in the order they were asked for */
static int njobs;

static void jobs_remove(Job *j)
{
    bg_lock();
    for (int i = 0; i < njobs; i++)
        if (jobs[i] == j) {
            memmove(jobs + i, jobs + i + 1, sizeof(jobs[0]) * (size_t)(njobs - i - 1));
            njobs--;
            break;
        }
    bg_unlock();
}

static void job_free(Job *j)
{
    if (!j)
        return;
    free(j->a.payload);
    free(j->b.payload);
    if (j->tex)
        gfx_tex_free(j->tex);
    free(j);
}

static void drop(int i)
{
    if (cache[i].job) {
        /* only reached when the background thread isn't using it */
        jobs_remove(cache[i].job);
        job_free(cache[i].job);
    }
    if (cache[i].tex)
        gfx_tex_free(cache[i].tex);
    total -= cache[i].bytes;
    cache[i] = cache[--ncache];
}

static int find(s32 res, s32 base)
{
    for (int i = 0; i < ncache; i++)
        if (cache[i].res == res && cache[i].base == base)
            return i;
    return -1;
}

/* ---- reading and decoding (any thread) -------------------------------------- */

static int bpp_of(int fmt) { return fmt == 0 ? 4 : fmt == 1 ? 3 : 2; }

static bool ctex_read(s32 res, Ctex *c)
{
    memset(c, 0, sizeof(*c));
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    FILE *f = fopen(path, "rb");
    if (!f)
        return false;
    u8 hdr[36];
    bool ok = fread(hdr, 1, 36, f) == 36 && memcmp(hdr, "CTEX", 4) == 0;
    if (ok) {
        c->fmt = rd_u16(hdr + 6);
        c->tw = rd_u16(hdr + 8);
        c->th = rd_u16(hdr + 10);
        c->iw = rd_u16(hdr + 12);
        c->ih = rd_u16(hdr + 14);
        c->flags = rd_u32(hdr + 24);
        c->raw = rd_u32(hdr + 28);
        c->stored = rd_u32(hdr + 32);
        ok = c->fmt >= 0 && c->fmt <= 2 && c->raw == (u32)c->tw * (u32)c->th * (u32)bpp_of(c->fmt) &&
             c->stored > 0 && c->stored <= (16u << 20) && (!(c->flags & 2) || c->fmt == 2);
    }
    if (ok) {
        c->payload = malloc(c->stored);
        ok = c->payload && fread(c->payload, 1, c->stored, f) == c->stored;
    }
    fclose(f);
    if (!ok) {
        free(c->payload);
        c->payload = NULL;
    }
    return ok;
}

/* Into the texture's pixels (the PICA200 tiled layout, as stored). */
static bool ctex_decode(const Ctex *c, void *dst)
{
    if (c->flags & 2) {
        int w = 0, h = 0;
        return jpeg_decode_tiled565(c->payload, c->stored, dst, c->tw, c->th, &w, &h) == JPEG_OK &&
               w == c->iw && h == c->ih;
    }
    if (c->flags & 1) {
        uLongf n = c->raw;
        return uncompress(dst, &n, c->payload, c->stored) == Z_OK && n == c->raw;
    }
    if (c->stored != c->raw)
        return false;
    memcpy(dst, c->payload, c->raw);
    return true;
}

/* Texel index in the PICA200 layout: 8x8 tiles row-major, Morton inside. */
static inline u32 texel(int x, int y, int tw)
{
    return (u32)(((y >> 3) * (tw >> 3) + (x >> 3)) * 64) |
           (u32)((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) |
                 ((y & 4) << 3));
}

/* Patched images (vnpack --cg-patches): the base picture with the patch
 * decoded into it at texel (px, py). Both are JPEG .ctex files. */
static bool patch_ok(const Job *j)
{
    const Ctex *a = &j->a, *b = &j->b;
    return (a->flags & 2) && (b->flags & 2) && j->px >= 0 && j->py >= 0 && j->px + b->iw <= a->iw &&
           j->py + b->ih <= a->ih && !(a->tw & 7) && !(a->th & 7);
}

static bool decode_patched(const Job *j, u16 *d)
{
    const Ctex *a = &j->a, *b = &j->b;
    int tw = a->tw, iw = a->iw, ih = a->ih, px = j->px, py = j->py, pw = b->iw, ph = b->ih;
    if (!ctex_decode(a, d))
        return false;
    int ptw = (pw + 7) & ~7, pth = (ph + 7) & ~7, w, h;
    u16 *pp = malloc((size_t)ptw * (size_t)pth * 2);
    bool ok = pp && jpeg_decode_tiled565(b->payload, b->stored, pp, ptw, pth, &w, &h) == JPEG_OK &&
              w == pw && h == ph;
    if (ok) {
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
            for (int y = ih; y < a->th; y++)
                for (int x = px; x < x1; x++)
                    d[texel(x, y, tw)] = d[texel(x, ih - 1, tw)];
        }
    }
    free(pp);
    return ok;
}

/* The stages; the job is in the matching -ING state while they run. */
static bool stage_read(Job *j)
{
    u64 t0 = platform_us();
    bool ok;
    if (j->base >= 0)
        ok = ctex_read(j->base, &j->a) && ctex_read(j->res, &j->b) && patch_ok(j);
    else
        ok = ctex_read(j->res, &j->a);
    j->read_us = platform_us() - t0;
    return ok;
}

static bool stage_decode(Job *j)
{
    u64 t0 = platform_us();
    bool ok = j->base >= 0 ? decode_patched(j, gfx_tex_data(j->tex)) : ctex_decode(&j->a, gfx_tex_data(j->tex));
    j->dec_us = platform_us() - t0;
    free(j->a.payload);
    free(j->b.payload);
    j->a.payload = j->b.payload = NULL;
    return ok;
}

bool texcache_bg_work(void)
{
    Job *j = NULL;
    int st = -1;
    bg_lock();
    /* finish what has memory first, then read the next file */
    for (int pass = 0; pass < 2 && !j; pass++)
        for (int i = 0; i < njobs; i++) {
            int want = pass == 0 ? J_DECODE : J_QUEUED;
            if (jobs[i]->state == want) {
                j = jobs[i];
                st = want;
                j->state = want == J_DECODE ? J_DECODING : J_READING;
                break;
            }
        }
    bg_unlock();
    if (!j)
        return false;
    bool ok = st == J_DECODE ? stage_decode(j) : stage_read(j);
    bg_lock();
    j->state = !ok ? J_FAILED : st == J_DECODE ? J_DONE : J_READ;
    bg_unlock();
    return true;
}

/* ---- the main thread's part ------------------------------------------------------- */

/* Frees cache memory until `bytes` more fit: least recently drawn first,
 * never what was drawn this frame or last, or what the current prediction
 * wants. */
static bool make_room(u32 bytes, bool for_preload)
{
    for (;;) {
        if (total + bytes <= CACHE_BUDGET && ncache < CACHE_MAX)
            return true;
        int lru = -1;
        for (int i = 0; i < ncache; i++) {
            const Entry *e = &cache[i];
            if (e->job || e->last + 1 >= E.frame || (e->want == want_gen && e->preloaded && !e->used))
                continue;
            if (for_preload && e->want == want_gen)
                continue;
            if (lru < 0 || e->last < cache[lru].last)
                lru = i;
        }
        if (lru < 0)
            return false;
        drop(lru);
    }
}

static u32 preload_bytes(void)
{
    u32 n = 0;
    for (int i = 0; i < ncache; i++)
        if (cache[i].preloaded && !cache[i].used)
            n += cache[i].bytes;
    return n;
}

/* READ -> DECODE: give the job its texture. False if it doesn't fit.
 * (Making room can move cache entries around.) */
static bool job_alloc(Job *j, bool needed_now)
{
    const Ctex *a = &j->a;
    u32 bytes = a->raw;
    if (!needed_now && preload_bytes() + bytes > PRELOAD_BUDGET)
        return false;
    if (!make_room(bytes, !needed_now) && !needed_now)
        return false;
    j->tex = gfx_tex_alloc(a->tw, a->th, a->fmt, a->iw, a->ih);
    if (!j->tex)
        return false;
    j->bytes = bytes;
    int i = find(j->res, j->base);
    if (i >= 0)
        cache[i].bytes = bytes;
    total += bytes;
    return true;
}

/* DONE -> cached. */
static void job_finish(int i)
{
    Entry *e = &cache[i];
    Job *j = e->job;
    jobs_remove(j);
    e->job = NULL;
    if (j->state == J_DONE) {
        gfx_tex_commit(j->tex);
        e->tex = j->tex;
        j->tex = NULL;
        char path[400];
        game_res_path(&E.game, e->res, path, sizeof(path));
        PERF("texture %s: preloaded (read %.1f ms, decoded %.1f ms on the background thread, %u KB), "
             "ready %.0f ms after it was predicted",
             path, j->read_us / 1000.0, j->dec_us / 1000.0, (unsigned)(j->bytes >> 10),
             (platform_us() - j->t_queue) / 1000.0);
        job_free(j);
        return;
    }
    job_free(j);
    total -= e->bytes;
    e->bytes = 0;
    cache[i] = cache[--ncache];   /* failed: try again (on the spot) when it is needed */
}

void texcache_pump(void)
{
    int allocs = 0;
    for (int i = 0; i < ncache; i++) {
        Entry *e = &cache[i];
        if (!e->job)
            continue;
        bg_lock();
        int st = e->job->state;
        bg_unlock();
        if (st == J_READ && allocs < 4) {
            allocs++;
            Job *j = e->job;
            bool ok = job_alloc(j, false);
            bg_lock();
            j->state = ok ? J_DECODE : J_FAILED;
            bg_unlock();
            if (ok)
                bg_wake();
            else
                PERF("texture res %d: preload dropped (no room)", (int)j->res);
        } else if (st == J_DONE || st == J_FAILED) {
            job_finish(i);
            i--;   /* (the entry may have moved) */
        }
    }
}

/* A preload that is needed right now: do its remaining stages here. */
static void job_wait(int i)
{
    u64 t0 = platform_us();
    Job *j = cache[i].job;
    int waits = 0;
    for (;;) {
        bg_lock();
        int st = j->state;
        if (st == J_QUEUED)
            j->state = J_READING;
        else if (st == J_DECODE)
            j->state = J_DECODING;
        bg_unlock();
        if (st == J_QUEUED || st == J_DECODE) {
            bool ok = st == J_QUEUED ? stage_read(j) : stage_decode(j);
            bg_lock();
            j->state = !ok ? J_FAILED : st == J_DECODE ? J_DONE : J_READ;
            bg_unlock();
        } else if (st == J_READ) {
            bool ok = job_alloc(j, true);
            bg_lock();
            j->state = ok ? J_DECODE : J_FAILED;
            bg_unlock();
        } else if (st == J_DONE || st == J_FAILED) {
            break;
        } else {
            waits++;
            bg_sleep_ms(1);   /* the background thread is on it */
        }
    }
    u64 us = platform_us() - t0;
    FP.tex_sync++;
    FP.tex_sync_bytes += j->bytes;
    FP.tex_sync_us += us;
    char path[400];
    game_res_path(&E.game, j->res, path, sizeof(path));
    PERF("texture %s: needed before its preload was done, finished on the main thread in %.2f ms "
         "(%d ms waiting)", path, us / 1000.0, waits);
    job_finish(find(j->res, j->base));
}

/* For the timing log: the image a texture belongs to. */
static const char *image_name(s32 res)
{
    for (u32 i = 0; i < E.game.nimages; i++) {
        const ImageDef *im = &E.game.images[i];
        if (im->res == res || im->patch_res == res)
            return im->name;
        for (int k = 0; k < im->nlayers; k++)
            if (im->layers[k].res == res)
                return im->name;
    }
    return "?";
}

static GfxTex *cache_get(s32 res, s32 base, int px, int py)
{
    if (res < 0 || !E.loaded)
        return NULL;
    int i = find(res, base);
    if (i >= 0 && cache[i].job) {
        job_wait(i);
        i = find(res, base);
    }
    if (i >= 0) {
        Entry *e = &cache[i];
        e->last = E.frame;
        if (e->preloaded && !e->used) {
            e->used = true;
            FP.tex_ready++;
        }
        return e->tex;
    }
    /* not predicted: load it here */
    Job j;
    memset(&j, 0, sizeof(j));
    j.res = res;
    j.base = base;
    j.px = px;
    j.py = py;
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    u64 t0 = platform_us();
    GfxTex *tex = NULL;
    u32 bytes = 0;
    if (stage_read(&j)) {
        bytes = j.a.raw;
        make_room(bytes, false);
        j.tex = gfx_tex_alloc(j.a.tw, j.a.th, j.a.fmt, j.a.iw, j.a.ih);
        if (j.tex && stage_decode(&j)) {
            gfx_tex_commit(j.tex);
            tex = j.tex;
            j.tex = NULL;
        }
    }
    free(j.a.payload);
    free(j.b.payload);
    if (j.tex)
        gfx_tex_free(j.tex);
    if (!tex)
        bytes = 0;
    u64 us = platform_us() - t0;
    FP.tex_sync++;
    FP.tex_sync_bytes += bytes;
    FP.tex_sync_us += us;
    PERF("texture %s (%s): not preloaded, loaded on the main thread in %.2f ms (read %.2f, decode %.2f; %u KB)",
         path, image_name(res), us / 1000.0, j.read_us / 1000.0, j.dec_us / 1000.0, (unsigned)(bytes >> 10));
    if (!tex)
        LOG("cannot load texture %s", path);
    if (ncache >= CACHE_MAX) {
        if (tex)
            gfx_tex_free(tex);
        return NULL;
    }
    Entry *e = &cache[ncache++];
    memset(e, 0, sizeof(*e));
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

/* ---- predictions ------------------------------------------------------------------ */

void texcache_want_begin(void)
{
    want_gen++;
}

static void want_one(s32 res, s32 base, int px, int py)
{
    if (res < 0 || !E.loaded)
        return;
    int i = find(res, base);
    if (i >= 0) {
        cache[i].want = want_gen;
        return;
    }
    if (njobs >= MAX_JOBS || ncache >= CACHE_MAX - 8)
        return;
    Job *j = calloc(1, sizeof(Job));
    if (!j)
        return;
    j->res = res;
    j->base = base;
    j->px = px;
    j->py = py;
    j->state = J_QUEUED;
    j->t_queue = platform_us();
    Entry *e = &cache[ncache++];
    memset(e, 0, sizeof(*e));
    e->res = res;
    e->base = base;
    e->last = E.frame;
    e->job = j;
    e->want = want_gen;
    e->preloaded = true;
    bg_lock();
    jobs[njobs++] = j;
    bg_unlock();
    bg_wake();
}

void texcache_want(const ImageDef *im)
{
    if (im->flags & IMG_VIDEO)
        return;
    if (im->patch_res >= 0 && im->res >= 0)
        want_one(im->patch_res, im->res, im->patch_x, im->patch_y);
    else
        want_one(im->res, -1, 0, 0);
    for (int k = 0; k < im->nlayers; k++)
        want_one(im->layers[k].res, -1, 0, 0);
}

void texcache_want_end(void)
{
    /* preloads the story has turned away from, not started yet: cancel */
    for (int i = 0; i < ncache; i++) {
        Entry *e = &cache[i];
        if (!e->job || e->want == want_gen)
            continue;
        bg_lock();
        bool idle = e->job->state == J_QUEUED;
        if (idle)
            e->job->state = J_FAILED;
        bg_unlock();
        if (idle) {
            job_finish(i);
            i--;
        }
    }
}

void texcache_init(void)
{
    jpeg_init();
}

void texcache_clear(void)
{
    /* let the background thread finish what it is in the middle of */
    for (int k = 0; k < 2000; k++) {
        bool busy = false;
        bg_lock();
        for (int i = 0; i < njobs; i++)
            if (jobs[i]->state == J_READING || jobs[i]->state == J_DECODING)
                busy = true;
        bg_unlock();
        if (!busy)
            break;
        bg_sleep_ms(1);
    }
    while (ncache > 0)
        drop(ncache - 1);
    total = 0;
    njobs = 0;
}
