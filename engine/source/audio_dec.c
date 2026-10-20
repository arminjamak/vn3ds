/* Ogg Opus (opusfile) and Ogg Vorbis (Tremor) decoding; see audio_dec.h. */

#include "audio_dec.h"

#include <limits.h>

#ifdef VN_HAVE_OPUS
#include <opusfile.h>
#endif
#ifdef VN_HAVE_TREMOR
#include <tremor/ivorbisfile.h>
#define VORBIS_READ(vf, buf, len, sec) ov_read(vf, buf, len, sec)
#elif defined(VN_HAVE_VORBISFILE)
/* the desktop build: the reference libvorbisfile, same API but floating
 * point (so its output can differ from the 3DS's by a bit of rounding) */
#include <vorbis/vorbisfile.h>
#define VN_HAVE_TREMOR 1
#define VORBIS_READ(vf, buf, len, sec) ov_read(vf, buf, len, 0, 2, 1, sec)
#endif

#define HOLE (-3) /* OP_HOLE and OV_HOLE: a gap in the data, skipped */

int adec_sniff(const u8 *head, size_t n)
{
    if (n < 28 || memcmp(head, "OggS", 4) != 0)
        return ADEC_NONE;
    size_t pkt = 27 + head[26]; /* after the segment table */
    if (pkt + 8 <= n && memcmp(head + pkt, "OpusHead", 8) == 0)
        return ADEC_OPUS;
    if (pkt + 7 <= n && memcmp(head + pkt, "\x01vorbis", 7) == 0)
        return ADEC_VORBIS;
    return ADEC_NONE;
}

const char *adec_codec_name(int codec)
{
    return codec == ADEC_OPUS ? "opus" : codec == ADEC_VORBIS ? "vorbis" : "unknown";
}

bool adec_open(ADec *d, const char *path)
{
    memset(d, 0, sizeof(*d));
    FILE *f = fopen(path, "rb");
    if (!f)
        return false;
    u8 head[512];
    size_t n = fread(head, 1, sizeof(head), f);
    int codec = adec_sniff(head, n);
#ifdef VN_HAVE_OPUS
    if (codec == ADEC_OPUS) {
        fclose(f);
        int err = 0;
        OggOpusFile *of = op_open_file(path, &err);
        if (!of)
            return false;
        int ch = op_channel_count(of, -1);
        d->codec = ADEC_OPUS;
        d->h = of;
        d->channels = ch > 2 ? 2 : ch;
        d->downmix = ch > 2;
        d->rate = 48000;
        if (ch < 1) {
            adec_close(d);
            return false;
        }
        return true;
    }
#endif
#ifdef VN_HAVE_TREMOR
    if (codec == ADEC_VORBIS) {
        OggVorbis_File *vf = malloc(sizeof(*vf));
        if (!vf || fseek(f, 0, SEEK_SET) != 0 || ov_open(f, vf, NULL, 0) < 0) {
            free(vf);
            fclose(f);
            return false;
        }
        /* from here ov_clear() closes the FILE */
        vorbis_info *vi = ov_info(vf, -1);
        d->codec = ADEC_VORBIS;
        d->h = vf;
        if (!vi || vi->channels < 1 || vi->channels > 2) {
            adec_close(d);
            return false;
        }
        d->channels = vi->channels;
        d->rate = vi->rate;
        return true;
    }
#endif
    (void)codec;
    fclose(f);
    return false;
}

/* ---- files in memory ---------------------------------------------------- */

typedef struct {
    u8 *p;
    size_t n, at;
} MemSrc;

u8 *adec_read_file(const char *path, size_t max, size_t *len)
{
    *len = 0;
    FILE *f = fopen(path, "rb");
    if (!f)
        return NULL;
    u8 *buf = NULL;
    size_t n = 0, cap = 0;
    for (;;) {
        if (n == cap) {
            cap = cap ? cap * 2 : 256 * 1024;
            if (cap > max + 1)
                cap = max + 1;
            if (n == cap) {   /* too big */
                free(buf);
                fclose(f);
                return NULL;
            }
            u8 *g = realloc(buf, cap);
            if (!g) {
                free(buf);
                fclose(f);
                return NULL;
            }
            buf = g;
        }
        size_t got = fread(buf + n, 1, cap - n < 65536 ? cap - n : 65536, f);
        if (got == 0)
            break;
        n += got;
    }
    fclose(f);
    if (n == 0 || n > max) {
        free(buf);
        return NULL;
    }
    *len = n;
    return buf;
}

#ifdef VN_HAVE_TREMOR
static size_t mem_read(void *ptr, size_t size, size_t nmemb, void *src)
{
    MemSrc *m = src;
    size_t want = size * nmemb, left = m->n - m->at;
    if (want > left)
        want = left;
    memcpy(ptr, m->p + m->at, want);
    m->at += want;
    return size ? want / size : 0;
}

static int mem_seek(void *src, ogg_int64_t off, int whence)
{
    MemSrc *m = src;
    ogg_int64_t base = whence == SEEK_SET ? 0 : whence == SEEK_CUR ? (ogg_int64_t)m->at : (ogg_int64_t)m->n;
    ogg_int64_t to = base + off;
    if (to < 0 || to > (ogg_int64_t)m->n)
        return -1;
    m->at = (size_t)to;
    return 0;
}

static int mem_close(void *src)
{
    (void)src;
    return 0;
}

static long mem_tell(void *src) { return (long)((MemSrc *)src)->at; }
#endif

bool adec_open_mem(ADec *d, u8 *data, size_t len)
{
    memset(d, 0, sizeof(*d));
    MemSrc *m = malloc(sizeof(*m));
    if (!m) {
        free(data);
        return false;
    }
    m->p = data;
    m->n = len;
    m->at = 0;
    d->mem = m;
    int codec = adec_sniff(data, len < 512 ? len : 512);
#ifdef VN_HAVE_OPUS
    if (codec == ADEC_OPUS) {
        int err = 0;
        OggOpusFile *of = op_open_memory(data, len, &err);
        if (of) {
            int ch = op_channel_count(of, -1);
            d->codec = ADEC_OPUS;
            d->h = of;
            d->channels = ch > 2 ? 2 : ch;
            d->downmix = ch > 2;
            d->rate = 48000;
            if (ch >= 1)
                return true;
        }
    }
#endif
#ifdef VN_HAVE_TREMOR
    if (codec == ADEC_VORBIS) {
        OggVorbis_File *vf = malloc(sizeof(*vf));
        ov_callbacks cb = {mem_read, mem_seek, mem_close, mem_tell};
        if (vf && ov_open_callbacks(m, vf, NULL, 0, cb) == 0) {
            vorbis_info *vi = ov_info(vf, -1);
            d->codec = ADEC_VORBIS;
            d->h = vf;
            if (vi && vi->channels >= 1 && vi->channels <= 2) {
                d->channels = vi->channels;
                d->rate = vi->rate;
                return true;
            }
        } else {
            free(vf);
        }
    }
#endif
    (void)codec;
    adec_close(d);
    return false;
}

void adec_close(ADec *d)
{
#ifdef VN_HAVE_OPUS
    if (d->codec == ADEC_OPUS && d->h)
        op_free(d->h);
#endif
#ifdef VN_HAVE_TREMOR
    if (d->codec == ADEC_VORBIS && d->h) {
        ov_clear(d->h); /* also closes the FILE */
        free(d->h);
    }
#endif
    if (d->mem) {
        free(((MemSrc *)d->mem)->p);
        free(d->mem);
    }
    memset(d, 0, sizeof(*d));
}

bool adec_rewind(ADec *d)
{
#ifdef VN_HAVE_OPUS
    if (d->codec == ADEC_OPUS)
        return op_pcm_seek(d->h, 0) == 0;
#endif
#ifdef VN_HAVE_TREMOR
    if (d->codec == ADEC_VORBIS)
        return ov_pcm_seek(d->h, 0) == 0;
#endif
    return false;
}

s64 adec_length(ADec *d)
{
#ifdef VN_HAVE_OPUS
    if (d->codec == ADEC_OPUS)
        return op_pcm_total(d->h, -1);
#endif
#ifdef VN_HAVE_TREMOR
    if (d->codec == ADEC_VORBIS)
        return ov_pcm_total(d->h, -1);
#endif
    return -1;
}

/* One decoder call: frames written, 0 at the end, HOLE, or another
 * negative value on an error. */
static long read_some(ADec *d, s16 *pcm, long frames)
{
    long samples = frames * d->channels;
    int want = samples > INT_MAX ? INT_MAX : (int)samples;
#ifdef VN_HAVE_OPUS
    if (d->codec == ADEC_OPUS) {
        int li = 0, r;
        if (d->downmix)
            return op_read_stereo(d->h, pcm, want);
        r = op_read(d->h, pcm, want, &li);
        /* a chained file whose channel count changes: stop there */
        if (r > 0 && op_channel_count(d->h, li) != d->channels)
            return -1;
        return r;
    }
#endif
#ifdef VN_HAVE_TREMOR
    if (d->codec == ADEC_VORBIS) {
        int section;
        long bytes = VORBIS_READ(d->h, (char *)pcm, want * 2 > 0 ? want * 2 : INT_MAX - 1, &section);
        return bytes > 0 ? bytes / (2 * d->channels) : bytes;
    }
#endif
    (void)pcm;
    (void)want;
    return -1;
}

long adec_fill(ADec *d, s16 *pcm, long frames, bool loop, bool *ended)
{
    long got = 0;
    int empty = 0;
    *ended = false;
    while (got < frames) {
        long r = read_some(d, pcm + got * d->channels, frames - got);
        if (r > 0) {
            got += r;
            empty = 0;
        } else if (r == 0) {
            if (loop && empty++ < 2 && adec_rewind(d))
                continue;
            *ended = true;
            break;
        } else if (r != HOLE) {
            *ended = true;
            break;
        }
    }
    return got;
}

s16 *adec_load_mono(const char *path, float max_seconds, u32 *frames_out, long *rate_out)
{
    ADec d;
    *frames_out = 0;
    if (!adec_open(&d, path))
        return NULL;
    long rate = d.rate;
    int ch = d.channels;
    long cap = (long)(rate * max_seconds);
    s16 *pcm = cap > 0 ? malloc((size_t)cap * ch * sizeof(s16)) : NULL;
    bool ended;
    long got = pcm ? adec_fill(&d, pcm, cap, false, &ended) : 0;
    adec_close(&d);
    if (got <= 0) {
        free(pcm);
        return NULL;
    }
    if (ch == 2)
        for (long k = 0; k < got; k++)
            pcm[k] = (s16)((pcm[2 * k] + pcm[2 * k + 1]) / 2);
    s16 *small = realloc(pcm, (size_t)got * sizeof(s16));
    *frames_out = (u32)got;
    *rate_out = rate;
    return small ? small : pcm;
}
