/* Ogg Opus / Ogg Vorbis streaming on NDSP. Opus is decoded with opusfile
 * (fixed-point libopus, 48 kHz), Vorbis with Tremor (libvorbisidec); see
 * audio_dec.c. The codec is sniffed from the file, so both play anywhere:
 * music, sounds, voices, the minigame sfx bank and the machine voices.
 *
 * Each channel keeps NBUF wave buffers that are refilled from the main loop,
 * about half a second of audio queued, enough to ride out a texture load.
 * A buffer is decoded a slice per frame (twice real time) instead of all
 * at once, so the decoder's cost is spread evenly over the frames; only a
 * channel that is about to run dry is filled in one go. NDSP needs
 * sdmc:/3ds/dspfirm.cdc (dumped with DSP1); without it the game runs
 * silently. */

#include <3ds.h>

#include "../audio.h"
#include "../audio_dec.h"

#define NBUF 3
/* Bytes per wave buffer: 8192 stereo frames. A stream uses at most
 * max(4096, rate / 6) frames of it, so 48 kHz Opus queues 0.5 s. */
#define BUF_BYTES (8192 * 2 * sizeof(s16))

typedef struct {
    bool active, loop, ending, open;
    ADec dec;
    int channels;
    u32 buf_frames;  /* frames per wave buffer for this file */
    int cur;         /* wave buffer being decoded into */
    u32 filled;      /* frames already decoded into it */
    ndspWaveBuf wb[NBUF];
    s16 *pcm[NBUF];
    float vol, fade_in, fade_out;
    float user_vol;
    bool has_next, next_loop;
    char next[300];
    u64 dec_ticks;   /* time spent decoding this file, for the log */
    u64 dec_frames;
} Stream;

static Stream S[CH_COUNT];
static bool ndsp_ok;
static float music_duck = 1.0f;

/* machine-voice syllables: decoded once, mono PCM16 in linear memory */
#define VOX_CH 3
#define VOX_MAX 32
static s16 *vox_pcm[VOX_MAX];
static u32 vox_len[VOX_MAX];
static long vox_rate[VOX_MAX];
static int nvox;
static ndspWaveBuf vox_wb;

static void apply_mix(int ch)
{
    float mix[12] = {0};
    mix[0] = mix[1] = S[ch].vol * S[ch].user_vol * (ch == CH_MUSIC ? music_duck : 1.0f);
    ndspChnSetMix(ch, mix);
}

bool audio_init(void)
{
    for (int ch = 0; ch < CH_COUNT; ch++)
        S[ch].user_vol = 1.0f;
    ndsp_ok = R_SUCCEEDED(ndspInit());
    if (!ndsp_ok) {
        LOG("ndspInit failed: put dspfirm.cdc in sdmc:/3ds/ for sound");
        return false;
    }
    ndspSetOutputMode(NDSP_OUTPUT_STEREO);
    for (int ch = 0; ch < CH_COUNT; ch++)
        for (int i = 0; i < NBUF; i++)
            S[ch].pcm[i] = linearAlloc(BUF_BYTES);
    return true;
}

static double ticks_ms(u64 t) { return (double)t * 1000.0 / SYSCLOCK_ARM11; }

static void close_stream(int ch)
{
    Stream *s = &S[ch];
    if (ndsp_ok)
        ndspChnWaveBufClear(ch);
    /* the decoder's cost on this console, to check the CPU budget */
    if (s->open && s->dec_frames >= (u64)s->dec.rate * 5)
        LOG("audio ch%d: %s %d ch %ld Hz, %.2f ms CPU per second of audio (%.1f s decoded)", ch,
            adec_codec_name(s->dec.codec), s->channels, s->dec.rate,
            ticks_ms(s->dec_ticks) * s->dec.rate / (double)s->dec_frames,
            (double)s->dec_frames / s->dec.rate);
    if (s->open)
        adec_close(&s->dec);
    s->open = false;
    s->active = false;
}

void audio_vox_free(void);

void audio_exit(void)
{
    if (!ndsp_ok)
        return;
    audio_vox_free();
    audio_sfx_free();
    for (int ch = 0; ch < CH_COUNT; ch++) {
        close_stream(ch);
        for (int i = 0; i < NBUF; i++)
            linearFree(S[ch].pcm[i]);
    }
    ndspExit();
    ndsp_ok = false;
}

static bool wb_busy(const ndspWaveBuf *wb)
{
    return wb->status == NDSP_WBUF_QUEUED || wb->status == NDSP_WBUF_PLAYING;
}

/* Decodes into the free wave buffers in order and queues each one when it
 * is full (or the file ended). `budget` caps the frames decoded in this
 * call; it is ignored while fewer than two buffers are queued, so a
 * channel that is running dry catches up at once. */
static void fill(int ch, long budget)
{
    Stream *s = &S[ch];
    if (!s->open || !s->pcm[0])
        return;
    int queued = 0;
    for (int i = 0; i < NBUF; i++)
        queued += wb_busy(&s->wb[i]);
    while (!s->ending && !wb_busy(&s->wb[s->cur])) {
        bool hurry = queued < 2;
        if (!hurry && budget <= 0)
            break;
        s16 *dst = s->pcm[s->cur];
        long want = (long)(s->buf_frames - s->filled);
        if (!hurry && want > budget)
            want = budget;
        bool ended = false;
        u64 t0 = svcGetSystemTick();
        long got = adec_fill(&s->dec, dst + s->filled * s->channels, want, s->loop, &ended);
        s->dec_ticks += svcGetSystemTick() - t0;
        s->dec_frames += (u64)got;
        s->filled += (u32)got;
        budget -= got;
        if (ended)
            s->ending = true;
        if (s->filled < s->buf_frames && !ended)
            continue; /* budget used up or a short read: more next time */
        if (s->filled > 0) {
            ndspWaveBuf *wb = &s->wb[s->cur];
            memset(wb, 0, sizeof(*wb));
            wb->data_vaddr = dst;
            wb->nsamples = s->filled;
            DSP_FlushDataCache(dst, s->filled * s->channels * sizeof(s16));
            ndspChnWaveBufAdd(ch, wb);
            queued++;
            s->cur = (s->cur + 1) % NBUF;
        }
        s->filled = 0;
    }
}

static bool open_stream(int ch, const char *path, bool loop, float fadein)
{
    Stream *s = &S[ch];
    close_stream(ch);
    if (!adec_open(&s->dec, path)) {
        LOG("audio: cannot play %s (missing, or not Ogg Opus / Vorbis)", path);
        return false;
    }
    s->open = true;
    s->channels = s->dec.channels;
    u32 frames = (u32)(s->dec.rate / 6);
    u32 cap = (u32)(BUF_BYTES / (s->channels * sizeof(s16)));
    s->buf_frames = frames < 4096 ? 4096 : frames > cap ? cap : frames;
    s->cur = 0;
    s->filled = 0;
    s->dec_ticks = s->dec_frames = 0;
    ndspChnReset(ch);
    ndspChnSetInterp(ch, NDSP_INTERP_LINEAR);
    ndspChnSetRate(ch, (float)s->dec.rate);
    ndspChnSetFormat(ch, s->channels == 2 ? NDSP_FORMAT_STEREO_PCM16 : NDSP_FORMAT_MONO_PCM16);
    memset(s->wb, 0, sizeof(s->wb));
    for (int i = 0; i < NBUF; i++)
        s->wb[i].status = NDSP_WBUF_DONE;
    s->active = true;
    s->loop = loop;
    s->ending = false;
    s->fade_out = 0;
    s->fade_in = fadein > 0 ? 1.0f / fadein : 0;
    s->vol = fadein > 0 ? 0.0f : 1.0f;
    apply_mix(ch);
    fill(ch, 0);
    return true;
}

void audio_play(int ch, const char *path, bool loop, float fadein, bool queue)
{
    if (!ndsp_ok || ch < 0 || ch >= CH_COUNT)
        return;
    Stream *s = &S[ch];
    if (queue && s->active) {
        snprintf(s->next, sizeof(s->next), "%s", path);
        s->next_loop = loop;
        s->has_next = true;
        s->loop = false; /* let the current file finish */
        return;
    }
    s->has_next = false;
    open_stream(ch, path, loop, fadein);
}

void audio_stop(int ch, float fadeout)
{
    if (!ndsp_ok || ch < 0 || ch >= CH_COUNT)
        return;
    Stream *s = &S[ch];
    s->has_next = false;
    if (!s->active)
        return;
    if (fadeout > 0) {
        s->fade_in = 0;
        s->fade_out = 1.0f / fadeout;
    } else {
        close_stream(ch);
    }
}

void audio_pause(int ch, bool paused)
{
    if (!ndsp_ok || ch < 0 || ch >= CH_COUNT)
        return;
    ndspChnSetPaused(ch, paused);
    if (ch == CH_MUSIC)
        for (int v = 0; v < 6; v++)   /* the minigame sound voices (SFX_CH0..) */
            ndspChnSetPaused(4 + v, paused);
}

bool audio_playing(int ch)
{
    return ch >= 0 && ch < CH_COUNT && S[ch].active;
}

void audio_set_volume(int ch, float v)
{
    if (ch < 0 || ch >= CH_COUNT)
        return;
    S[ch].user_vol = v;
    if (ndsp_ok && S[ch].active)
        apply_mix(ch);
}

void audio_update(float dt)
{
    if (!ndsp_ok)
        return;
    for (int ch = 0; ch < CH_COUNT; ch++) {
        Stream *s = &S[ch];
        if (!s->active)
            continue;
        if (s->fade_in > 0) {
            s->vol += s->fade_in * dt;
            if (s->vol >= 1) {
                s->vol = 1;
                s->fade_in = 0;
            }
            apply_mix(ch);
        } else if (s->fade_out > 0) {
            s->vol -= s->fade_out * dt;
            if (s->vol <= 0) {
                close_stream(ch);
                continue;
            }
            apply_mix(ch);
        }
        /* twice real time per frame (at least a 60th of a second) */
        fill(ch, (long)(s->dec.rate * 2 * (dt > 1.0f / 60 ? (dt < 0.25f ? dt : 0.25f) : 1.0f / 60)));
        if (s->ending && !ndspChnIsPlaying(ch)) {
            bool all_done = true;
            for (int i = 0; i < NBUF; i++)
                if (s->wb[i].status == NDSP_WBUF_QUEUED || s->wb[i].status == NDSP_WBUF_PLAYING)
                    all_done = false;
            if (all_done) {
                if (s->has_next) {
                    s->has_next = false;
                    open_stream(ch, s->next, s->next_loop, 0);
                } else {
                    close_stream(ch);
                }
            }
        }
    }
}

/* ---- machine voices ------------------------------------------------------ */

void audio_vox_free(void)
{
    if (ndsp_ok)
        ndspChnWaveBufClear(VOX_CH);
    for (int i = 0; i < nvox; i++)
        linearFree(vox_pcm[i]);
    nvox = 0;
}

/* Decodes a short clip (Opus or Vorbis) into mono PCM16 in linear memory
 * (at most `seconds`). */
static s16 *decode_short(const char *path, float seconds, u32 *frames_out, long *rate_out)
{
    u32 frames = 0;
    long rate = 0;
    s16 *tmp = adec_load_mono(path, seconds, &frames, &rate);
    s16 *pcm = tmp ? linearAlloc(frames * sizeof(s16)) : NULL;
    if (pcm) {
        memcpy(pcm, tmp, frames * sizeof(s16));
        DSP_FlushDataCache(pcm, frames * sizeof(s16));
    }
    free(tmp);
    *frames_out = pcm ? frames : 0;
    *rate_out = rate;
    return pcm;
}

void audio_vox_load(const char **paths, int n)
{
    audio_vox_free();
    if (!ndsp_ok)
        return;
    u64 t0 = svcGetSystemTick();
    for (int i = 0; i < n && nvox < VOX_MAX; i++) {
        u32 frames;
        long rate;
        s16 *pcm = decode_short(paths[i], 1.0f, &frames, &rate);   /* syllables are short */
        if (pcm) {
            vox_pcm[nvox] = pcm;
            vox_len[nvox] = frames;
            vox_rate[nvox] = rate;
            nvox++;
        }
    }
    ndspChnReset(VOX_CH);
    ndspChnSetInterp(VOX_CH, NDSP_INTERP_LINEAR);
    ndspChnSetFormat(VOX_CH, NDSP_FORMAT_MONO_PCM16);
    LOG("voice bank: %d syllables, decoded in %.0f ms", nvox, ticks_ms(svcGetSystemTick() - t0));
}

void audio_vox_play(int index, float rate, float volume)
{
    if (!ndsp_ok || nvox == 0)
        return;
    index = ((index % nvox) + nvox) % nvox;
    ndspChnWaveBufClear(VOX_CH);   /* one syllable at a time, like a mouth */
    ndspChnSetRate(VOX_CH, (float)vox_rate[index] * rate);
    float mix[12] = {0};
    mix[0] = mix[1] = volume;
    ndspChnSetMix(VOX_CH, mix);
    memset(&vox_wb, 0, sizeof(vox_wb));
    vox_wb.data_vaddr = vox_pcm[index];
    vox_wb.nsamples = vox_len[index];
    ndspChnWaveBufAdd(VOX_CH, &vox_wb);
}

/* ---- minigame sound effects ---------------------------------------------- */

#define SFX_CH0 4
#define SFX_VOICES 6
#define SFX_MAX 64
static s16 *sfx_pcm[SFX_MAX];
static u32 sfx_len[SFX_MAX];
static long sfx_rate[SFX_MAX];
static int nsfx, sfx_next;
static ndspWaveBuf sfx_wb[SFX_VOICES];

void audio_sfx_free(void)
{
    if (ndsp_ok)
        for (int v = 0; v < SFX_VOICES; v++)
            ndspChnWaveBufClear(SFX_CH0 + v);
    for (int i = 0; i < nsfx; i++)
        if (sfx_pcm[i])
            linearFree(sfx_pcm[i]);
    nsfx = 0;
}

void audio_sfx_load(const char **paths, int n)
{
    audio_sfx_free();
    if (!ndsp_ok)
        return;
    u64 t0 = svcGetSystemTick();
    for (int i = 0; i < n && nsfx < SFX_MAX; i++) {
        /* keep indices aligned with `paths` even if one fails */
        sfx_pcm[nsfx] = decode_short(paths[i], 3.0f, &sfx_len[nsfx], &sfx_rate[nsfx]);
        nsfx++;
    }
    for (int v = 0; v < SFX_VOICES; v++) {
        ndspChnReset(SFX_CH0 + v);
        ndspChnSetInterp(SFX_CH0 + v, NDSP_INTERP_LINEAR);
        ndspChnSetFormat(SFX_CH0 + v, NDSP_FORMAT_MONO_PCM16);
    }
    LOG("sfx bank: %d clips, decoded in %.0f ms", nsfx, ticks_ms(svcGetSystemTick() - t0));
}

void audio_sfx_play(int index, float volume, float rate)
{
    if (!ndsp_ok || index < 0 || index >= nsfx || !sfx_pcm[index])
        return;
    /* round-robin; prefer a voice that has finished */
    int v = sfx_next;
    for (int k = 0; k < SFX_VOICES; k++) {
        int c = (sfx_next + k) % SFX_VOICES;
        if (!ndspChnIsPlaying(SFX_CH0 + c)) {
            v = c;
            break;
        }
    }
    sfx_next = (v + 1) % SFX_VOICES;
    int ch = SFX_CH0 + v;
    ndspChnWaveBufClear(ch);
    ndspChnSetRate(ch, (float)sfx_rate[index] * (rate > 0 ? rate : 1.0f));
    float mix[12] = {0};
    mix[0] = mix[1] = volume * S[CH_SOUND].user_vol;
    ndspChnSetMix(ch, mix);
    memset(&sfx_wb[v], 0, sizeof(sfx_wb[v]));
    sfx_wb[v].data_vaddr = sfx_pcm[index];
    sfx_wb[v].nsamples = sfx_len[index];
    ndspChnWaveBufAdd(ch, &sfx_wb[v]);
}

void audio_music_duck(float gain)
{
    if (fabsf(gain - music_duck) < 0.002f)
        return;
    music_duck = gain;
    if (ndsp_ok && S[CH_MUSIC].active)
        apply_mix(CH_MUSIC);
}
