/* Ogg Opus (opusfile) and Ogg Vorbis (Tremor) decoding; see audio_dec.h. */

#include "audio_dec.h"

#include <limits.h>

#ifdef VN_HAVE_OPUS
#include <opusfile.h>
#endif
#ifdef VN_HAVE_TREMOR
#include <tremor/ivorbisfile.h>
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
        long bytes = ov_read(d->h, (char *)pcm, want * 2 > 0 ? want * 2 : INT_MAX - 1, &section);
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
