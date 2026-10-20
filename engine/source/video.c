/* Video playback for Ren'Py Movie() images. Two formats, both written by
 * tools/vnpack/assets.py:
 *
 * .cvh  H.264 (no B-frames, an IDR frame at the start of every GOP) with a
 *       table of each frame's NAL units, and its first frame as a normal
 *       .ctex next to it (the "poster"). On a New 3DS the hardware decoder
 *       (MVD service) decodes it:
 *         mvdstdProcessVideoFrame() per NAL unit, mvdstdRenderVideoFrame()
 *         into an RGB565 buffer in linear RAM, then the GPU's transfer engine
 *         tiles it (GX DisplayTransfer, linear -> tiled) and copies it into
 *         one of two textures (TextureCopy, which adds the gap to the
 *         texture's power-of-two width). The CPU never touches the pixels.
 *       There is only one hardware decoder and a stream can only be entered
 *       at an IDR frame, so one clip plays at a time: the most recently
 *       opened one. Others on screen keep the last picture they showed (or
 *       their poster) and carry on, from the keyframe before that picture,
 *       when they get the decoder back. Old 3DS, the desktop build and any
 *       decoder error: the poster, which is the clip's first frame.
 *       The desktop build can decode with an ffmpeg subprocess instead, to
 *       test timing: VN3DS_VIDEO_FFMPEG=1 vn3ds-host ...
 * .cvid zlib'd changed 8x8 tiles, already in the GPU's tiled layout (older,
 *       low frame rate, works everywhere).
 *
 * A playing clip is double buffered: the frame being written is never the
 * one the GPU may still be drawing. Videos are drawn like any other image
 * (render.c), so depth and parallax apply to them. Build with
 * -DVIDEO_FAKE_MVD to replace the decoder with a moving test pattern (to
 * check the GPU path on an emulator, which has no MVD). */

#ifdef __3DS__
#include <3ds.h>
#include <citro3d.h>
#endif

#include "app.h"
#include "video.h"

#include <zlib.h>

#define MAX_VIDEOS 4
#define CVH_HEADER 64
#define MAX_STEP 3            /* frames decoded per update at most (catching up) */
#define IDLE_RELEASE 180      /* frames without a clip before the decoder is freed */
#define MAX_FAILS 3           /* decoder errors before giving up for this game */

enum { FMT_CVID = 1, FMT_CVH = 2 };

typedef struct {
    u32 off, size;
    u16 nals, flags;          /* flags & 1: IDR frame */
} CvhFrame;

typedef struct {
    bool used;
    s32 res;
    int fmt;
    FILE *f;
    u32 nframes;
    float fps;
    bool loop;
    GfxTex *tex[2];
    int cur;
    float t;
    int shown;                /* frame in tex[cur]; -1: none yet */
    u32 last_used;
    /* .cvid */
    int version;
    u32 ntiles;
    u32 *offs, *sizes;
    u8 *accum, *delta, *zbuf;
    size_t raw, zcap;
    /* .cvh */
    int w, h, tw, th;
    CvhFrame *frames;
    u32 params_off, params_size, max_frame;
    GfxTex *poster;
    u32 seq;                  /* open order: the newest clip gets the decoder */
    int decoded;              /* last frame fed to the decoder; -1: start at a keyframe */
    bool failed;              /* the decoder gave up on it: keeps its last picture */
} Video;

static Video V[MAX_VIDEOS];
static s32 bad_res = -1;      /* last resource that failed to open (don't retry every frame) */

/* ---- the decoder (one, shared) ------------------------------------------ */

static struct {
    Video *owner;
    u32 seq;
    int fails;
    u32 idle;                 /* frames with no .cvh clip open */
#ifdef __3DS__
    u8 *buf;                  /* CPU copy of a frame with several NAL units */
    u32 buf_cap;
    int state;                /* 0 not started, 1 running, -1 unavailable */
    bool reset;               /* HOME / sleep happened: start it again */
    bool cleared;             /* already emptied the texture cache once for it */
    bool hooked;
    aptHookCookie hook;
    u32 retry_frame;
    u8 *in;                   /* NAL unit input (linear RAM) */
    u32 in_cap;
    u8 *out, *stage;          /* decoder output (linear RGB565), tiled staging */
    u32 out_cap;
    int w, h;
    MVDSTD_Config cfg;
    int log_left;
    int render_misses;        /* RenderVideoFrame failures in a row */
#else
    int enabled;              /* VN3DS_VIDEO_FFMPEG: -1 unknown */
    FILE *pipe;
    Video *pipe_of;
    int pipe_next;            /* frame the pipe delivers next */
    u16 *px;
    size_t px_cap;
#endif
} D = {
#ifndef __3DS__
    .enabled = -1,
#endif
};

static int keyframe_before(const Video *v, int k)
{
    while (k > 0 && !(v->frames[k].flags & 1))
        k--;
    return k;
}

#ifdef __3DS__

/* Reads frame k into dst (cap bytes). */
static bool read_frame(Video *v, int k, u8 *dst, u32 cap)
{
    const CvhFrame *fr = &v->frames[k];
    return fr->size <= cap && fseek(v->f, (long)fr->off, SEEK_SET) == 0 &&
           fread(dst, 1, fr->size, v->f) == fr->size;
}

/* The NAL unit starting at p[0] (with its 00 00 01 prefix): its length. */
static u32 nal_len(const u8 *p, u32 n)
{
    for (u32 j = 3; j + 3 <= n; j++)
        if (p[j] == 0 && p[j + 1] == 0 && p[j + 2] == 1)
            return j;
    return n;
}

/* MVD's "BGR565" is the bit order the GPU calls RGB565 (red in the top
 * bits): libctru's example writes it straight into an RGB565 framebuffer. */
#ifndef VIDEO_MVD_OUTPUT
#define VIDEO_MVD_OUTPUT MVD_OUTPUT_BGR565
#endif

/* Linear RGB565 in, tiled RGB565 out; no flip: row 0 (the top of the
 * picture) goes to the first tile row, as in .ctex files. */
#define TILE_FLAGS (GX_TRANSFER_FLIP_VERT(0) | GX_TRANSFER_OUT_TILED(1) | GX_TRANSFER_RAW_COPY(0) | \
                    GX_TRANSFER_IN_FORMAT(GX_TRANSFER_FMT_RGB565) |                            \
                    GX_TRANSFER_OUT_FORMAT(GX_TRANSFER_FMT_RGB565) |                           \
                    GX_TRANSFER_SCALING(GX_TRANSFER_SCALE_NO))

static void on_apt(APT_HookType type, void *param)
{
    (void)param;
    if (type == APTHOOK_ONSUSPEND || type == APTHOOK_ONSLEEP)
        D.reset = true;
}

static void free_linear(u8 **p)
{
    if (*p)
        linearFree(*p);
    *p = NULL;
}

/* Stops the decoder and frees its memory (keeps "unavailable"). */
static void dec_stop(void)
{
#ifndef VIDEO_FAKE_MVD
    if (D.state == 1)
        mvdstdExit();
#endif
    if (D.state == 1)
        D.state = 0;
    free_linear(&D.in);
    free_linear(&D.out);
    free_linear(&D.stage);
    D.in_cap = D.out_cap = 0;
    D.w = D.h = 0;
}

static bool dec_usable(void)
{
    if (D.state == 0) {
        bool n3ds = false;
        if (R_FAILED(APT_CheckNew3DS(&n3ds)) || !n3ds) {
            LOG("video: Old 3DS (no hardware H.264 decoder): movies show their first frame");
            D.state = -1;
        }
    }
    return D.state >= 0;
}

static u8 *grow_linear(u8 **p, u32 *cap, u32 need)
{
    if (*cap >= need)
        return *p;
    free_linear(p);
    *cap = 0;
    *p = linearAlloc(need);
    if (!*p)
        return NULL;
    /* Nothing of ours may sit dirty in the CPU cache over memory the GPU or
     * the decoder writes. */
    GSPGPU_FlushDataCache(*p, need);
    *cap = need;
    return *p;
}

/* Starts MVD for w x h (no-op when it already runs at that size).
 * 1 ready, 0 not yet (try again on a later frame), -1 failed. */
static int dec_start(int w, int h)
{
    if (D.state < 0)
        return -1;
    if (D.state == 1 && !D.reset && D.w == w && D.h == h)
        return 1;
    if (D.state == 1)
        dec_stop();   /* other size, or after sleep/HOME */
    D.reset = false;
    if (E.frame < D.retry_frame)
        return 0;
    u32 px = (u32)w * (u32)h * 2;
    if (D.out_cap < px) {
        free_linear(&D.stage);
        D.out_cap = 0;
        u32 cap = 0;
        if (!grow_linear(&D.out, &D.out_cap, px) || !grow_linear(&D.stage, &cap, px)) {
            LOG("video: no linear memory for the decoder's %ux%u output", w, h);
            dec_stop();
            return -1;
        }
    }
    u32 work = MVD_DEFAULT_WORKBUF_SIZE, calc = 0;
#ifndef VIDEO_FAKE_MVD
    /* srvGetServiceHandle waits forever for a service nobody registered:
     * make sure MVD is there (it is on a New 3DS; emulators may lack it or
     * register it under another name), and don't wait for a busy port. */
    bool registered = false;
    Result sr = srvIsServiceRegistered(&registered, "mvd:STD");
    if (R_FAILED(sr) || !registered) {
        LOG("video: no mvd:STD service (0x%08lx); movies show their first frame",
            (unsigned long)sr);
        D.state = -1;
        return -1;
    }
    MVDSTD_CalculateWorkBufSizeConfig cc;
    memset(&cc, 0, sizeof(cc));
    cc.level.enable = 1;
    cc.level.flag = MVD_CALC_WITH_LEVEL_FLAG_ENABLE_CALC;
    cc.level.level = MVD_H264_LEVEL_3_0;
    cc.width = (u32)w;
    cc.height = (u32)h;
    srvSetBlockingPolicy(true);
    Result cr = mvdstdCalculateBufferSize(&cc, &calc);
    srvSetBlockingPolicy(false);
    LOG("video: MVD work buffer for level 3.0 %dx%d: 0x%08lx, size 0x%lx (default 0x%x)", w, h,
        (unsigned long)cr, (unsigned long)calc, MVD_DEFAULT_WORKBUF_SIZE);
    if (calc > 0x2000000u)
        calc = 0;
    if (calc > work)
        work = calc;
#endif
    u32 free_now = linearSpaceFree();
    u32 margin = 1u << 20;   /* leave some for textures and audio */
    if (free_now < work + margin && !D.cleared) {
        /* The texture cache usually holds most of linear RAM; it refills
         * with what's on screen. Its memory is released at the next frame. */
        LOG("video: %u KiB linear RAM free, decoder needs %u KiB: emptying the texture cache",
            (unsigned)(free_now >> 10), (unsigned)(work >> 10));
        texcache_clear();
        D.cleared = true;
        D.retry_frame = E.frame + 2;
        return 0;
    }
    if (free_now < work + margin && calc >= (1u << 20) && calc < work &&
        free_now >= calc + margin) {
        LOG("video: using the calculated work buffer size");
        work = calc;
    }
    if (free_now < work + margin) {
        LOG("video: not enough linear RAM for the decoder (%u KiB free); showing posters",
            (unsigned)(free_now >> 10));
        D.retry_frame = E.frame + 600;   /* maybe later, when less is in use */
        return 0;
    }
#ifdef VIDEO_FAKE_MVD
    Result r = 0;
#else
    srvSetBlockingPolicy(true);
    Result r = mvdstdInit(MVDMODE_VIDEOPROCESSING, MVD_INPUT_H264, VIDEO_MVD_OUTPUT, work, NULL);
    srvSetBlockingPolicy(false);
#endif
    LOG("video: mvdstdInit(video, H.264 -> RGB565, work 0x%lx) = 0x%08lx (linear free %u KiB)",
        (unsigned long)work, (unsigned long)r, (unsigned)(linearSpaceFree() >> 10));
    if (r != 0) {
        /* libctru returns 0 on success; anything else (no service, a status
         * code from MVD, no memory) means no hardware decoding. */
        LOG("video: hardware decoder unavailable; movies show their first frame");
        D.state = -1;
        free_linear(&D.out);
        free_linear(&D.stage);
        D.out_cap = 0;
        return -1;
    }
    mvdstdGenerateDefaultConfig(&D.cfg, (u32)w, (u32)h, (u32)w, (u32)h, NULL, (u32 *)D.out,
                                (u32 *)D.out);
    D.state = 1;
    D.w = w;
    D.h = h;
    D.log_left = 16;
    D.render_misses = 0;
    if (!D.hooked) {
        aptHook(&D.hook, on_apt, NULL);
        D.hooked = true;
    }
    return 1;
}

#ifdef VIDEO_FAKE_MVD
/* Test pattern instead of decoding: red grows left to right, green top to
 * bottom; white block top-left, blue block bottom-right, and a yellow bar
 * that moves one frame's worth per frame. */
static void fake_frame(int k)
{
    u16 *o = (u16 *)D.out;
    int bar = (k * 4) % D.w;
    for (int y = 0; y < D.h; y++)
        for (int x = 0; x < D.w; x++) {
            u16 c = (u16)(((x * 31 / D.w) << 11) | ((y * 63 / D.h) << 5) | 8);
            if (x < 64 && y < 32)
                c = 0xFFFF;
            else if (x >= D.w - 64 && y >= D.h - 32)
                c = 0x001F;
            else if (x >= bar && x < bar + 8)
                c = 0xFFE0;
            o[y * D.w + x] = c;
        }
    GSPGPU_FlushDataCache(D.out, (u32)D.w * D.h * 2);
}
#endif

/* Feeds n bytes of NAL units (each with a 00 00 01 prefix) at D.in.
 * *ready: a picture came out (rendered into D.out). */
static bool feed(const u8 *src, u32 n, int k, bool *ready)
{
    u32 i = 0;
    while (i < n) {
        u32 len = nal_len(src + i, n - i);
        if (src + i != D.in)
            memmove(D.in, src + i, len);   /* each NAL unit from the start of the buffer */
        GSPGPU_FlushDataCache(D.in, len);
        int type = len > 3 ? (D.in[3] & 0x1F) : -1;
#ifdef VIDEO_FAKE_MVD
        Result r = (type == 7 || type == 8) ? MVD_STATUS_PARAMSET : MVD_STATUS_FRAMEREADY;
#else
        MVDSTD_ProcessNALUnitOut po;
        memset(&po, 0, sizeof(po));
        Result r = mvdstdProcessVideoFrame(D.in, len, 0, &po);
#endif
        if (D.log_left > 0) {
            D.log_left--;
            LOG("video: frame %d nal type %d (%u bytes) -> 0x%08lx", k, type, (unsigned)len,
                (unsigned long)r);
        }
        if (!MVD_CHECKNALUPROC_SUCCESS(r)) {
            LOG("video: mvdstdProcessVideoFrame(frame %d, nal type %d, %u bytes) = 0x%08lx", k,
                type, (unsigned)len, (unsigned long)r);
            return false;
        }
        /* As in libctru's example: a picture is ready unless the unit was a
         * parameter set or wasn't used up. */
        if (r != MVD_STATUS_PARAMSET && r != MVD_STATUS_INCOMPLETEPROCESSING && k >= 0) {
#ifdef VIDEO_FAKE_MVD
            fake_frame(k);
            Result rr = MVD_STATUS_OK;
#else
            Result rr = mvdstdRenderVideoFrame(&D.cfg, true);
#endif
            if (rr != MVD_STATUS_OK) {
                /* Tolerate a few (a decoder may hold the first picture
                 * back); a run of them means it's not working. */
                LOG("video: mvdstdRenderVideoFrame(frame %d) = 0x%08lx", k, (unsigned long)rr);
                if (++D.render_misses > 8)
                    return false;
            } else {
                D.render_misses = 0;
                *ready = true;
            }
        }
        i += len;
    }
    return true;
}

/* 1 ok, 0 not yet, -1 failed */
static int dec_begin(Video *v, int kf)
{
    int s = dec_start(v->w, v->h);
    if (s <= 0)
        return s;
    u32 need = (v->max_frame > v->params_size ? v->max_frame : v->params_size) + 64;
    if (!grow_linear(&D.in, &D.in_cap, need)) {
        LOG("video: no linear memory for a %u-byte frame", (unsigned)need);
        return -1;
    }
    if (fseek(v->f, (long)v->params_off, SEEK_SET) != 0 ||
        fread(D.in, 1, v->params_size, v->f) != v->params_size)
        return -1;
    bool ready = false;
    (void)kf;   /* the decoder just takes the IDR frame next */
    return feed(D.in, v->params_size, -1, &ready) ? 1 : -1;
}

static void to_texture(Video *v, GfxTex *t)
{
    u32 *dst = gfx_tex_data(t);
    if (v->w == v->tw) {
        C3D_SyncDisplayTransfer((u32 *)D.out, GX_BUFFER_DIM(v->w, v->h), dst,
                                GX_BUFFER_DIM(v->w, v->h), TILE_FLAGS);
        return;
    }
    /* Tile at the picture's own width, then copy each band of 8 rows (w*16
     * bytes) into the wider texture: line and gap are in 16-byte units. */
    C3D_SyncDisplayTransfer((u32 *)D.out, GX_BUFFER_DIM(v->w, v->h), (u32 *)D.stage,
                            GX_BUFFER_DIM(v->w, v->h), TILE_FLAGS);
    C3D_SyncTextureCopy((u32 *)D.stage, GX_BUFFER_DIM(v->w, 0), dst,
                        GX_BUFFER_DIM(v->w, v->tw - v->w), (u32)v->w * (u32)v->h * 2,
                        GX_TRANSFER_RAW_COPY(1));
}

static bool dec_frame(Video *v, int k, bool show)
{
    const CvhFrame *fr = &v->frames[k];
    u8 *src = D.in;
    if (fr->nals > 1) {   /* several units: each is copied to the start of D.in */
        if (D.buf_cap < fr->size) {
            free(D.buf);
            D.buf = malloc(fr->size);
            D.buf_cap = D.buf ? fr->size : 0;
        }
        src = D.buf;
    }
    if (!src || !read_frame(v, k, src, src == D.in ? D.in_cap : D.buf_cap)) {
        LOG("video %d: cannot read frame %d", (int)v->res, k);
        return false;
    }
    bool ready = false;
    if (!feed(src, fr->size, k, &ready))
        return false;
    if (show && ready) {
        int next = v->cur ^ 1;
        to_texture(v, v->tex[next]);
        v->cur = next;
        v->shown = k;
    }
    return true;
}

static void dec_release(void) {}

static void dec_shutdown(void)
{
    dec_stop();
    free(D.buf);
    D.buf = NULL;
    D.buf_cap = 0;
    D.state = 0;
    D.cleared = false;
    D.retry_frame = 0;
}

#else /* desktop: optional ffmpeg subprocess */

static int morton8(int x, int y)
{
    return (x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3);
}

static bool dec_usable(void)
{
    if (D.enabled < 0) {
        const char *s = getenv("VN3DS_VIDEO_FFMPEG");
        D.enabled = s && *s && strcmp(s, "0") != 0;
    }
    return D.enabled > 0;
}

static void pipe_close(void)
{
    if (D.pipe)
        pclose(D.pipe);
    D.pipe = NULL;
    D.pipe_of = NULL;
}

static bool pipe_open(Video *v)
{
    char path[400], quoted[900], cmd[1200];
    game_res_path(&E.game, v->res, path, sizeof(path));
    size_t q = 0;
    quoted[q++] = '\'';
    for (const char *p = path; *p && q + 5 < sizeof(quoted); p++) {
        if (*p == '\'') {
            memcpy(quoted + q, "'\\''", 4);
            q += 4;
        } else {
            quoted[q++] = *p;
        }
    }
    quoted[q++] = '\'';
    quoted[q] = 0;
    snprintf(cmd, sizeof(cmd),
             "ffmpeg -v fatal -nostdin -threads 1 -skip_initial_bytes %u -f h264 -i %s "
             "-f rawvideo -pix_fmt rgb565le -fps_mode passthrough -",
             (unsigned)v->params_off, quoted);
    D.pipe = popen(cmd, "r");
    D.pipe_of = v;
    D.pipe_next = 0;
    if (!D.pipe)
        LOG("video: cannot run ffmpeg");
    return D.pipe != NULL;
}

static bool pipe_read(Video *v)
{
    size_t n = (size_t)v->w * v->h;
    if (D.px_cap < n) {
        free(D.px);
        D.px = malloc(n * 2);
        D.px_cap = D.px ? n : 0;
    }
    if (!D.px || fread(D.px, 2, n, D.pipe) != n)
        return false;
    D.pipe_next++;
    return true;
}

static int dec_begin(Video *v, int kf)
{
    if (!D.pipe || D.pipe_of != v || D.pipe_next > kf) {
        pipe_close();
        if (!pipe_open(v))
            return -1;
    }
    while (D.pipe_next < kf)
        if (!pipe_read(v))
            return -1;
    return 1;
}

static bool dec_frame(Video *v, int k, bool show)
{
    if (D.pipe_of != v || D.pipe_next != k || !pipe_read(v)) {
        LOG("video %d: ffmpeg gave no frame %d", (int)v->res, k);
        return false;
    }
    if (show) {
        int next = v->cur ^ 1;
        u16 *d = gfx_tex_data(v->tex[next]);
        for (int y = 0; y < v->h; y++)
            for (int x = 0; x < v->w; x++)
                d[((y / 8) * (v->tw / 8) + x / 8) * 64 + morton8(x & 7, y & 7)] = D.px[y * v->w + x];
        gfx_tex_commit(v->tex[next]);
        v->cur = next;
        v->shown = k;
    }
    return true;
}

static void dec_release(void) { pipe_close(); }

static void dec_shutdown(void)
{
    pipe_close();
    free(D.px);
    D.px = NULL;
    D.px_cap = 0;
}

#endif

/* ---- open / close -------------------------------------------------------- */

static void close_video(Video *v)
{
    if (D.owner == v) {
        D.owner = NULL;
        dec_release();
    }
    if (v->f)
        fclose(v->f);
    for (int i = 0; i < 2; i++)
        if (v->tex[i])
            gfx_tex_free(v->tex[i]);
    if (v->poster)
        gfx_tex_free(v->poster);
    free(v->offs);
    free(v->sizes);
    free(v->accum);
    free(v->delta);
    free(v->zbuf);
    free(v->frames);
    memset(v, 0, sizeof(*v));
}

static bool pow2_ok(int t, int v) { return t >= v && t >= 8 && t <= 1024 && !(t & (t - 1)); }

static bool open_cvh(Video *v, const char *path)
{
    u8 h[CVH_HEADER];
    if (fseek(v->f, 0, SEEK_SET) != 0 || fread(h, 1, CVH_HEADER, v->f) != CVH_HEADER ||
        rd_u16(h + 4) != 1 || rd_u16(h + 6) != 1)
        return false;
    v->fmt = FMT_CVH;
    v->w = rd_u16(h + 8);
    v->h = rd_u16(h + 10);
    v->tw = rd_u16(h + 12);
    v->th = rd_u16(h + 14);
    v->fps = rd_f32(h + 24);
    v->nframes = rd_u32(h + 28);
    v->loop = rd_u32(h + 32) & 1;
    v->params_off = rd_u32(h + 36);
    v->params_size = rd_u32(h + 40);
    v->max_frame = rd_u32(h + 48);
    if (v->w < 16 || v->h < 16 || (v->w & 15) || (v->h & 15) || !pow2_ok(v->tw, v->w) ||
        !pow2_ok(v->th, v->h) || !(v->fps > 0.5f && v->fps <= 120.0f) || v->nframes == 0 ||
        v->nframes > 1000000 || v->params_size < 8 || v->params_size > 4096 ||
        v->max_frame == 0 || v->max_frame > (4u << 20)) {
        LOG("video: %s: bad header", path);
        return false;
    }
    v->frames = malloc(sizeof(CvhFrame) * v->nframes);
    if (!v->frames)
        return false;
    for (u32 i = 0; i < v->nframes; i++) {
        u8 e[12];
        if (fread(e, 1, 12, v->f) != 12)
            return false;
        v->frames[i].off = rd_u32(e);
        v->frames[i].size = rd_u32(e + 4);
        v->frames[i].nals = rd_u16(e + 8);
        v->frames[i].flags = rd_u16(e + 10);
        if (v->frames[i].size == 0 || v->frames[i].size > v->max_frame || v->frames[i].nals == 0)
            return false;
    }
    /* The poster: same name, .ctex. */
    char pp[400];
    snprintf(pp, sizeof(pp), "%s", path);
    char *dot = strrchr(pp, '.');
    if (dot && (size_t)(dot - pp) + 6 <= sizeof(pp))
        strcpy(dot, ".ctex");
    u32 bytes = 0;
    v->poster = gfx_tex_load(pp, &bytes);
    if (!v->poster)
        LOG("video: no poster %s", pp);
    v->failed = !(v->frames[0].flags & 1);   /* must start with an IDR frame */
    v->decoded = -1;
    v->seq = ++D.seq;
    return true;
}

static bool open_cvid(Video *v, const u8 *h)
{
    if (rd_u16(h + 6) != 2 || (rd_u16(h + 4) != 1 && rd_u16(h + 4) != 2))
        return false;
    v->fmt = FMT_CVID;
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
        fread(v->sizes, 4, v->nframes, v->f) != v->nframes)
        return false;
    for (int i = 0; i < 2; i++) {
        v->tex[i] = gfx_tex_create(tw, th, 2, iw, ih);
        if (!v->tex[i])
            return false;
    }
    return true;
}

static bool open_video(Video *v, s32 res)
{
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    memset(v, 0, sizeof(*v));
    v->shown = -1;
    v->f = fopen(path, "rb");
    if (!v->f)
        return false;
    u8 h[40];
    bool ok = fread(h, 1, 40, v->f) == 40;
    if (ok && memcmp(h, "CVH1", 4) == 0)
        ok = open_cvh(v, path);
    else if (ok && memcmp(h, "CVID", 4) == 0)
        ok = open_cvid(v, h);
    else
        ok = false;
    if (!ok) {
        close_video(v);
        return false;
    }
    v->used = true;
    v->res = res;
    return true;
}

/* ---- .cvid --------------------------------------------------------------- */

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

static void update_cvid(Video *v, float dt)
{
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
        return;
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

/* ---- .cvh ---------------------------------------------------------------- */

static void cvh_fail(Video *v, const char *why)
{
    LOG("video %d: %s at frame %d; keeping its %s", (int)v->res, why, v->decoded + 1,
        v->shown >= 0 ? "last picture" : "poster");
    v->failed = true;
    if (D.owner == v) {
        D.owner = NULL;
        dec_release();
    }
    if (++D.fails >= MAX_FAILS)
        LOG("video: %d decoder errors; no more hardware decoding for this game", D.fails);
#ifdef __3DS__
    D.reset = true;   /* start the decoder afresh for the next clip */
#endif
}

static bool ensure_textures(Video *v)
{
    for (int i = 0; i < 2; i++) {
        if (v->tex[i])
            continue;
        v->tex[i] = gfx_tex_create(v->tw, v->th, 2, v->w, v->h);
        if (!v->tex[i])
            return false;
        /* Write the zeroed pixels back now: afterwards only the GPU writes. */
        gfx_tex_commit(v->tex[i]);
    }
    return true;
}

/* The owner: decode up to the frame due now. */
static void update_owner(Video *v, float dt)
{
    v->t += dt;
    int n = (int)v->nframes;
    int target = (int)(v->t * v->fps);
    if (target >= n) {
        if (v->loop) {
            v->t = fmodf(v->t, n / v->fps);
            target = (int)(v->t * v->fps);
            if (target >= n)
                target = n - 1;
        } else {
            target = n - 1;   /* hold the last frame */
        }
    }
    if (target == v->decoded)
        return;
    if (v->decoded < 0 || target < v->decoded || target - v->decoded > MAX_STEP) {
        /* (Re)start at a keyframe: first use, loop, getting the decoder back,
         * or too far behind. */
        int kf = keyframe_before(v, target);
        if (v->decoded < 0 || target < v->decoded || kf > v->decoded + 1) {
            if (!ensure_textures(v)) {
                cvh_fail(v, "no memory for its textures");
                return;
            }
            int s = dec_begin(v, kf);
            if (s == 0) {   /* decoder not ready yet: stay where we are */
                v->t -= dt;
                return;
            }
            if (s < 0) {
                cvh_fail(v, "decoder start failed");
                return;
            }
            v->decoded = kf - 1;
        }
        if (target - v->decoded > MAX_STEP) {   /* slow down rather than skip */
            target = v->decoded + MAX_STEP;
            v->t = (target + 0.5f) / v->fps;
        }
    }
    for (int k = v->decoded + 1; k <= target; k++) {
        if (!dec_frame(v, k, k == target)) {
            cvh_fail(v, "decoding failed");
            return;
        }
        v->decoded = k;
    }
    if (v->shown >= 0 && v->poster) {   /* moving now: the poster isn't needed */
        gfx_tex_free(v->poster);
        v->poster = NULL;
    }
}

/* ---- API ----------------------------------------------------------------- */

static GfxTex *picture(Video *v)
{
    if (v->shown >= 0)
        return v->tex[v->cur];
    return v->fmt == FMT_CVH ? v->poster : NULL;
}

GfxTex *video_tex(s32 res)
{
    Video *free_slot = NULL;
    for (int i = 0; i < MAX_VIDEOS; i++) {
        if (V[i].used && V[i].res == res) {
            V[i].last_used = E.frame;
            return picture(&V[i]);
        }
        if (!V[i].used && !free_slot)
            free_slot = &V[i];
    }
    if (res == bad_res)
        return NULL;
    if (!free_slot) {   /* reuse the least recently drawn */
        free_slot = &V[0];
        for (int i = 1; i < MAX_VIDEOS; i++)
            if (V[i].last_used < free_slot->last_used)
                free_slot = &V[i];
        close_video(free_slot);
    }
    if (!open_video(free_slot, res)) {
        LOG("cannot open video resource %d", (int)res);
        bad_res = res;
        return NULL;
    }
    free_slot->last_used = E.frame;
    if (free_slot->fmt == FMT_CVID && decode(free_slot, 0)) {
        free_slot->shown = 0;
        present(free_slot);
    }
    /* .cvh: the poster now; decoding starts in video_update (outside the frame). */
    return picture(free_slot);
}

void video_update(float dt)
{
    Video *newest = NULL;
    bool any_cvh = false;
    for (int i = 0; i < MAX_VIDEOS; i++) {
        Video *v = &V[i];
        if (!v->used)
            continue;
        if (E.frame - v->last_used > 3) {   /* not on screen any more */
            close_video(v);
            continue;
        }
        if (v->fmt == FMT_CVID) {
            update_cvid(v, dt);
            continue;
        }
        any_cvh = true;
        if (!v->failed && (!newest || v->seq > newest->seq))
            newest = v;
    }
    D.idle = any_cvh ? 0 : D.idle + 1;
#ifdef __3DS__
    if (D.idle == IDLE_RELEASE && D.state == 1) {
        /* No movie for a while: give its memory back to the textures. */
        LOG("video: no movie on screen; stopping the decoder");
        dec_stop();
        D.cleared = false;
    }
    if (D.reset && D.owner)
        D.owner->decoded = -1;   /* after sleep/HOME: re-enter at a keyframe */
#endif
    if (!newest || D.fails >= MAX_FAILS || !dec_usable())
        return;
    if (D.owner != newest) {
        /* The old owner keeps its picture; the new one starts at a keyframe. */
        if (D.owner)
            dec_release();
        D.owner = newest;
        newest->decoded = -1;
        if (newest->shown >= 0)
            newest->t = (newest->shown + 0.5f) / newest->fps;
    }
    update_owner(newest, dt);
}

void video_close_all(void)
{
    for (int i = 0; i < MAX_VIDEOS; i++)
        if (V[i].used)
            close_video(&V[i]);
    D.owner = NULL;
    D.fails = 0;
    D.idle = 0;
    bad_res = -1;
    dec_shutdown();
}
