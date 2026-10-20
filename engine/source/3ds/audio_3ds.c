/* Ogg Vorbis streaming on NDSP, decoded with Tremor (libvorbisidec).
 *
 * Each channel keeps NBUF wave buffers that are refilled from the main loop;
 * at 32 kHz that is ~0.4 s of audio queued, enough to ride out a texture
 * load. NDSP needs sdmc:/3ds/dspfirm.cdc (dumped with DSP1); without it the
 * game runs silently. */

#include <3ds.h>
#include <tremor/ivorbisfile.h>

#include "../audio.h"

#define NBUF 3
#define BUF_FRAMES 4096

typedef struct {
    bool active, loop, ending, open;
    OggVorbis_File vf;
    int channels;
    ndspWaveBuf wb[NBUF];
    s16 *pcm[NBUF];
    float vol, fade_in, fade_out;
    float user_vol;
    bool has_next, next_loop;
    char next[300];
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
            S[ch].pcm[i] = linearAlloc(BUF_FRAMES * 2 * sizeof(s16));
    return true;
}

static void close_stream(int ch)
{
    Stream *s = &S[ch];
    if (ndsp_ok)
        ndspChnWaveBufClear(ch);
    if (s->open)
        ov_clear(&s->vf); /* also closes the FILE */
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

static void fill(int ch)
{
    Stream *s = &S[ch];
    size_t frame_bytes = (size_t)s->channels * sizeof(s16);
    for (int i = 0; i < NBUF; i++) {
        ndspWaveBuf *wb = &s->wb[i];
        if (s->ending || (wb->status != NDSP_WBUF_DONE && wb->status != NDSP_WBUF_FREE))
            continue;
        char *dst = (char *)s->pcm[i];
        size_t want = BUF_FRAMES * frame_bytes, got = 0;
        int empty_loops = 0;
        while (got < want) {
            int section;
            long r = ov_read(&s->vf, dst + got, (int)(want - got), &section);
            if (r > 0) {
                got += (size_t)r;
                empty_loops = 0;
            } else if (r == 0) {
                if (s->loop && empty_loops++ < 2) {
                    ov_pcm_seek(&s->vf, 0);
                    continue;
                }
                s->ending = true;
                break;
            } else if (r != OV_HOLE) {
                s->ending = true;
                break;
            }
        }
        if (got < frame_bytes)
            continue;
        memset(wb, 0, sizeof(*wb));
        wb->data_vaddr = dst;
        wb->nsamples = (u32)(got / frame_bytes);
        DSP_FlushDataCache(dst, (u32)got);
        ndspChnWaveBufAdd(ch, wb);
    }
}

static bool open_stream(int ch, const char *path, bool loop, float fadein)
{
    Stream *s = &S[ch];
    close_stream(ch);
    FILE *f = fopen(path, "rb");
    if (!f) {
        LOG("audio: cannot open %s", path);
        return false;
    }
    if (ov_open(f, &s->vf, NULL, 0) < 0) {
        LOG("audio: %s is not Ogg Vorbis", path);
        fclose(f);
        return false;
    }
    s->open = true;
    vorbis_info *vi = ov_info(&s->vf, -1);
    if (!vi || vi->channels < 1 || vi->channels > 2) {
        close_stream(ch);
        return false;
    }
    s->channels = vi->channels;
    ndspChnReset(ch);
    ndspChnSetInterp(ch, NDSP_INTERP_LINEAR);
    ndspChnSetRate(ch, (float)vi->rate);
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
    fill(ch);
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
        fill(ch);
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

/* Decodes a short Ogg into mono PCM16 in linear memory (at most `seconds`). */
static s16 *decode_short(const char *path, float seconds, u32 *frames_out, long *rate_out)
{
    FILE *f = fopen(path, "rb");
    OggVorbis_File vf;
    if (!f)
        return NULL;
    if (ov_open(f, &vf, NULL, 0) < 0) {
        fclose(f);
        return NULL;
    }
    vorbis_info *vi = ov_info(&vf, -1);
    int chans = vi ? vi->channels : 1;
    long rate = vi ? vi->rate : 32000;
    size_t cap = (size_t)(rate * seconds) * 2 * chans, got = 0;
    s16 *tmp = malloc(cap);
    while (tmp && got < cap) {
        int section;
        long r = ov_read(&vf, (char *)tmp + got, (int)(cap - got), &section);
        if (r <= 0)
            break;
        got += (size_t)r;
    }
    ov_clear(&vf);
    u32 frames = (u32)(got / (2 * chans));
    s16 *pcm = frames ? linearAlloc(frames * 2) : NULL;
    if (pcm) {
        for (u32 k = 0; k < frames; k++)
            pcm[k] = chans == 2 ? (s16)((tmp[2 * k] + tmp[2 * k + 1]) / 2) : tmp[k];
        DSP_FlushDataCache(pcm, frames * 2);
    }
    free(tmp);
    *frames_out = frames;
    *rate_out = rate;
    return pcm;
}

void audio_vox_load(const char **paths, int n)
{
    audio_vox_free();
    if (!ndsp_ok)
        return;
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
    LOG("voice bank: %d syllables", nvox);
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
    LOG("sfx bank: %d clips", nsfx);
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
