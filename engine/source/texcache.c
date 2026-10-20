#include "app.h"

/* Textures live in linear RAM on the 3DS; keep the working set bounded and
 * evict least-recently-drawn ones. Anything drawn this frame is kept, since
 * the GPU may still read it. */

#define CACHE_MAX 128
#define CACHE_BUDGET (20u << 20)

typedef struct {
    s32 res;
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

GfxTex *texcache_get(s32 res)
{
    if (res < 0 || !E.loaded)
        return NULL;
    for (int i = 0; i < ncache; i++) {
        if (cache[i].res == res) {
            cache[i].last = E.frame;
            return cache[i].tex;
        }
    }
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    u32 bytes = 0;
    GfxTex *tex = gfx_tex_load(path, &bytes);
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
    e->tex = tex;
    e->bytes = bytes;
    e->last = E.frame;
    e->failed = tex == NULL;
    total += bytes;
    return tex;
}

void texcache_clear(void)
{
    while (ncache > 0)
        drop(ncache - 1);
    total = 0;
}
