/* Ogg Opus / Ogg Vorbis streaming on NDSP. Opus is decoded with opusfile
 * (fixed-point libopus, 48 kHz), Vorbis with Tremor (libvorbisidec); see
 * audio_dec.c. The codec is sniffed from the file, so both play anywhere:
 * music, sounds, voices, the minigame sfx bank and the machine voices.
 *
 * The audio thread. Music, sounds and voices are decoded and queued on NDSP
 * by a thread of their own, one priority step above the main thread on the
 * same core: whenever it wakes (every few milliseconds, or at once when the
 * main thread posts a command) it preempts the main thread, tops up what is
 * running low and goes back to sleep. So a frame that stalls on a texture
 * load, a scene change or the SD card can never starve the speaker. The
 * main thread only posts commands (play, stop, pause, volume) to it; the
 * music's own calls (music.c) take the mixer's lock instead. Each NDSP
 * channel is driven from one thread: music, sound and voice from the audio
 * thread, the machine voices and the minigame sound effects (short clips
 * decoded into memory once) from the main thread.
 *
 * Music is mixed in software (music.c) from decks the background thread
 * opens (each file read into memory whole, so decoding never waits for the
 * SD card behind the texture preloads); about MUSIC_AHEAD_S of the mix is
 * kept queued. Sounds and voices stream from their files with NBUF wave
 * buffers, about two thirds of a second queued.
 *
 * Underruns (a channel that should be playing with nothing queued) are
 * counted and logged, with the thread's own timings every half minute.
 * NDSP needs sdmc:/3ds/dspfirm.cdc (dumped with DSP1); without it the game
 * runs silently. */

#include <3ds.h>

#include "../audio.h"
#include "../audio_dec.h"
#include "../bg.h"
#include "../music.h"
#include "../platform.h"

/* the music channel's output */
#define MOUT 40
#define MOUT_FRAMES 1024
#define MUSIC_AHEAD_S 0.7f
static ndspWaveBuf mwb[MOUT];
static s16 *mpcm[MOUT];
static int mnext;
static long mrate;
static bool m_producing;   /* the mixer had something to play last time */

#define NBUF 4
/* Bytes per wave buffer: 8192 stereo frames. A stream uses at most
 * max(4096, rate / 6) frames of it. */
#define BUF_BYTES (8192 * 2 * sizeof(s16))

/* A sound or voice stream: the audio thread's alone. */
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
    float mix;       /* the gain last given to NDSP */
    bool has_next, next_loop;
    char next[300];
    u32 gen, next_gen;
    u64 dec_ticks;   /* time spent decoding this file, for the log */
    u64 dec_frames;
} Stream;

static Stream S[CH_COUNT];
static bool ndsp_ok;

/* ---- what the main thread shares with the audio thread ----------------------- */

enum { C_PLAY, C_STOP };
typedef struct {
    u8 type, ch;
    bool loop, queue;
    float fade;
    u32 gen;
    char path[300];
} Cmd;
#define NCMD 32
static Cmd cmdq[NCMD];
static int cmd_head, cmd_tail;
static LightLock cmd_lock = 1;

static volatile float user_vol[CH_COUNT] = {1, 1, 1};
static volatile float music_duck = 1.0f;
static volatile bool want_pause, music_paused_now;
/* audio_playing() for sounds and voices: the main thread's last command, and
 * the stream that ran out by itself */
static volatile bool cmd_playing[CH_COUNT];
static volatile u32 play_gen[CH_COUNT], done_gen[CH_COUNT];

static Thread athread;
static LightEvent aev;
static volatile bool aquit;
static bool athread_ok;

/* the thread's statistics, for the log */
static u32 underruns[CH_COUNT], passes;
static double pass_max_ms, music_queue_min_ms = 1e9;

static double ticks_ms(u64 t) { return (double)t * 1000.0 / SYSCLOCK_ARM11; }

static bool wb_busy(const ndspWaveBuf *wb)
{
    return wb->status == NDSP_WBUF_QUEUED || wb->status == NDSP_WBUF_PLAYING;
}

static void post(const Cmd *c)
{
    for (int tries = 0; tries < 200; tries++) {
        LightLock_Lock(&cmd_lock);
        bool full = (cmd_tail + 1) % NCMD == cmd_head;
        if (!full) {
            cmdq[cmd_tail] = *c;
            cmd_tail = (cmd_tail + 1) % NCMD;
        }
        LightLock_Unlock(&cmd_lock);
        if (!full)
            break;
        LightEvent_Signal(&aev);
        svcSleepThread(1000000LL);
    }
    LightEvent_Signal(&aev);   /* the audio thread runs at once (it outranks us) */
}

static bool pop(Cmd *c)
{
    LightLock_Lock(&cmd_lock);
    bool any = cmd_head != cmd_tail;
    if (any) {
        *c = cmdq[cmd_head];
        cmd_head = (cmd_head + 1) % NCMD;
    }
    LightLock_Unlock(&cmd_lock);
    return any;
}

/* ---- sounds and voices (audio thread) ---------------------------------------- */

static void stream_mix(int ch)
{
    Stream *s = &S[ch];
    float g = s->vol * user_vol[ch];
    if (fabsf(g - s->mix) < 0.001f)
        return;
    s->mix = g;
    float mix[12] = {0};
    mix[0] = mix[1] = g;
    ndspChnSetMix(ch, mix);
}

static void close_stream(int ch)
{
    Stream *s = &S[ch];
    ndspChnWaveBufClear(ch);
    if (s->open && s->dec_frames >= (u64)s->dec.rate * 5)
        PERF("audio ch%d: %s %d ch %ld Hz, %.2f ms CPU per second of audio (%.1f s decoded)", ch,
             adec_codec_name(s->dec.codec), s->channels, s->dec.rate,
             ticks_ms(s->dec_ticks) * s->dec.rate / (double)s->dec_frames,
             (double)s->dec_frames / s->dec.rate);
    if (s->open)
        adec_close(&s->dec);
    s->open = false;
    s->active = false;
}

/* Decodes into the free wave buffers in order and queues each one when it
 * is full (or the file ended): one buffer per call, unless fewer than two
 * are queued (then it catches up at once). */
static void fill(int ch)
{
    Stream *s = &S[ch];
    if (!s->open || !s->pcm[0])
        return;
    int queued = 0;
    for (int i = 0; i < NBUF; i++)
        queued += wb_busy(&s->wb[i]);
    int done = 0;
    while (!s->ending && !wb_busy(&s->wb[s->cur]) && (queued < 2 || done == 0)) {
        s16 *dst = s->pcm[s->cur];
        long want = (long)(s->buf_frames - s->filled);
        bool ended = false;
        u64 t0 = svcGetSystemTick();
        long got = adec_fill(&s->dec, dst + s->filled * s->channels, want, s->loop, &ended);
        s->dec_ticks += svcGetSystemTick() - t0;
        s->dec_frames += (u64)got;
        s->filled += (u32)got;
        if (ended)
            s->ending = true;
        if (s->filled < s->buf_frames && !ended)
            continue;
        if (s->filled > 0) {
            ndspWaveBuf *wb = &s->wb[s->cur];
            memset(wb, 0, sizeof(*wb));
            wb->data_vaddr = dst;
            wb->nsamples = s->filled;
            DSP_FlushDataCache(dst, s->filled * s->channels * sizeof(s16));
            ndspChnWaveBufAdd(ch, wb);
            queued++;
            done++;
            s->cur = (s->cur + 1) % NBUF;
        }
        s->filled = 0;
    }
}

static bool open_stream(int ch, const char *path, bool loop, float fadein, u32 gen)
{
    Stream *s = &S[ch];
    close_stream(ch);
    s->gen = gen;
    u64 t0 = svcGetSystemTick();
    if (!adec_open(&s->dec, path)) {
        LOG("audio: cannot play %s (missing, or not Ogg Opus / Vorbis)", path);
        done_gen[ch] = gen;
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
    s->mix = -1;
    stream_mix(ch);
    fill(ch);
    PERF("audio ch%d: started %s in %.1f ms (audio thread)", ch, path, ticks_ms(svcGetSystemTick() - t0));
    return true;
}

static void exec(const Cmd *c)
{
    Stream *s = &S[c->ch];
    if (c->type == C_PLAY) {
        if (c->queue && s->active) {
            snprintf(s->next, sizeof(s->next), "%s", c->path);
            s->next_loop = c->loop;
            s->next_gen = c->gen;
            s->has_next = true;
            s->loop = false; /* let the current file finish */
            return;
        }
        s->has_next = false;
        open_stream(c->ch, c->path, c->loop, c->fade, c->gen);
    } else {
        s->has_next = false;
        if (!s->active)
            return;
        if (c->fade > 0) {
            s->fade_in = 0;
            s->fade_out = 1.0f / c->fade;
        } else {
            close_stream(c->ch);
        }
    }
}

static void streams_update(float dt)
{
    for (int ch = 0; ch < CH_COUNT; ch++) {
        Stream *s = &S[ch];
        if (ch == CH_MUSIC || !s->active)
            continue;
        if (s->fade_in > 0) {
            s->vol += s->fade_in * dt;
            if (s->vol >= 1) {
                s->vol = 1;
                s->fade_in = 0;
            }
        } else if (s->fade_out > 0) {
            s->vol -= s->fade_out * dt;
            if (s->vol <= 0) {
                close_stream(ch);
                done_gen[ch] = s->gen;
                continue;
            }
        }
        stream_mix(ch);
        int queued = 0;
        for (int i = 0; i < NBUF; i++)
            queued += wb_busy(&s->wb[i]);
        if (queued == 0 && !s->ending && s->dec_frames > 0)
            underruns[ch]++;
        fill(ch);
        if (s->ending && !ndspChnIsPlaying(ch)) {
            bool all_done = true;
            for (int i = 0; i < NBUF; i++)
                if (wb_busy(&s->wb[i]))
                    all_done = false;
            if (all_done) {
                if (s->has_next) {
                    s->has_next = false;
                    open_stream(ch, s->next, s->next_loop, 0, s->next_gen);
                } else {
                    close_stream(ch);
                    done_gen[ch] = s->gen;
                }
            }
        }
    }
}

/* ---- music (audio thread) -------------------------------------------------------- */

static float music_gain_set = -1;

static void music_out(void)
{
    if (!mpcm[MOUT - 1])
        return;
    if (want_pause != music_paused_now) {
        music_paused_now = want_pause;
        ndspChnSetPaused(CH_MUSIC, music_paused_now);
    }
    float g = user_vol[CH_MUSIC] * music_duck;
    if (fabsf(g - music_gain_set) > 0.001f) {
        music_gain_set = g;
        float mix[12] = {0};
        mix[0] = mix[1] = g;
        ndspChnSetMix(CH_MUSIC, mix);
    }
    if (music_take_flush()) {
        ndspChnWaveBufClear(CH_MUSIC);
        for (int i = 0; i < MOUT; i++)
            mwb[i].status = NDSP_WBUF_DONE;
        mnext = 0;
        m_producing = false;
    }
    u32 queued = 0;
    int busy = 0;
    for (int i = 0; i < MOUT; i++)
        if (wb_busy(&mwb[i])) {
            queued += mwb[i].nsamples;
            busy++;
        }
    if (m_producing && busy == 0 && !music_paused_now)
        underruns[CH_MUSIC]++;
    if (m_producing && mrate > 0) {
        double ms = queued * 1000.0 / mrate;
        if (ms < music_queue_min_ms && !music_paused_now)
            music_queue_min_ms = ms;
    }
    u32 ahead = (u32)(MUSIC_AHEAD_S * (mrate > 0 ? mrate : 32000));
    while (queued < ahead) {
        ndspWaveBuf *wb = &mwb[mnext];
        if (wb_busy(wb))
            break;
        long n = music_mix(mpcm[mnext], MOUT_FRAMES);
        m_producing = n > 0;
        if (n <= 0)
            break;
        long r = music_rate();
        if (r != mrate) {
            ndspChnSetRate(CH_MUSIC, (float)r);
            mrate = r;
        }
        memset(wb, 0, sizeof(*wb));
        wb->data_vaddr = mpcm[mnext];
        wb->nsamples = (u32)n;
        DSP_FlushDataCache(mpcm[mnext], (u32)n * 2 * sizeof(s16));
        ndspChnWaveBufAdd(CH_MUSIC, wb);
        queued += (u32)n;
        mnext = (mnext + 1) % MOUT;
    }
}

/* ---- the thread ------------------------------------------------------------------ */

static void audio_pass(float dt)
{
    u64 t0 = svcGetSystemTick();
    Cmd c;
    while (pop(&c))
        exec(&c);
    /* a little decoding per pass: the thread outranks the main thread, so it
     * must never hold the CPU for long */
    for (int k = 0; k < 2 && music_decode_work(); k++)
        ;
    if (!bg_running())   /* (no background thread to open files) */
        music_open_work();
    music_out();
    streams_update(dt);
    double ms = ticks_ms(svcGetSystemTick() - t0);
    if (ms > pass_max_ms)
        pass_max_ms = ms;
    passes++;
}

static void athread_main(void *arg)
{
    (void)arg;
    u64 last = svcGetSystemTick(), last_log = last;
    u32 seen_underruns = 0;
    while (!aquit) {
        LightEvent_WaitTimeout(&aev, 4 * 1000000LL);
        u64 now = svcGetSystemTick();
        float dt = (float)ticks_ms(now - last) / 1000.0f;
        last = now;
        audio_pass(dt > 0.25f ? 0.25f : dt);
        u32 total = underruns[0] + underruns[1] + underruns[2];
        if (total != seen_underruns || ticks_ms(now - last_log) > 30000) {
            PERF("audio thread: %s%u passes, longest %.2f ms; music queue at least %.0f ms; underruns: "
                 "music %u, sound %u, voice %u",
                 total != seen_underruns ? "UNDERRUN; " : "", (unsigned)passes, pass_max_ms, music_queue_min_ms > 1e8 ? -1.0 : music_queue_min_ms,
                 (unsigned)underruns[0], (unsigned)underruns[1], (unsigned)underruns[2]);
            /* (a PERF line, not LOG: this thread must never wait to write the SD card) */
            seen_underruns = total;
            last_log = now;
            pass_max_ms = 0;
            music_queue_min_ms = 1e9;
        }
    }
}

bool audio_init(void)
{
    ndsp_ok = R_SUCCEEDED(ndspInit());
    if (!ndsp_ok) {
        LOG("ndspInit failed: put dspfirm.cdc in sdmc:/3ds/ for sound");
        return false;
    }
    ndspSetOutputMode(NDSP_OUTPUT_STEREO);
    for (int ch = 0; ch < CH_COUNT; ch++)
        for (int i = 0; ch != CH_MUSIC && i < NBUF; i++)
            S[ch].pcm[i] = linearAlloc(BUF_BYTES);
    for (int i = 0; i < MOUT; i++) {
        mpcm[i] = linearAlloc(MOUT_FRAMES * 2 * sizeof(s16));
        mwb[i].status = NDSP_WBUF_DONE;
    }
    music_init();
    ndspChnReset(CH_MUSIC);
    ndspChnSetInterp(CH_MUSIC, NDSP_INTERP_LINEAR);
    ndspChnSetFormat(CH_MUSIC, NDSP_FORMAT_STEREO_PCM16);
    mrate = music_rate();
    ndspChnSetRate(CH_MUSIC, (float)mrate);
    LightEvent_Init(&aev, RESET_ONESHOT);
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    aquit = false;
    athread = threadCreate(athread_main, NULL, 96 * 1024, prio > 0x18 ? prio - 1 : prio, -2, false);
    athread_ok = athread != NULL;
    if (!athread_ok)
        LOG("audio: no audio thread; feeding NDSP from the main loop");
    return true;
}

void audio_vox_free(void);

void audio_exit(void)
{
    if (!ndsp_ok)
        return;
    if (athread_ok) {
        aquit = true;
        LightEvent_Signal(&aev);
        threadJoin(athread, U64_MAX);
        threadFree(athread);
        athread_ok = false;
    }
    audio_vox_free();
    audio_sfx_free();
    for (int ch = 0; ch < CH_COUNT; ch++) {
        if (ch != CH_MUSIC)
            close_stream(ch);
        for (int i = 0; i < NBUF; i++)
            if (S[ch].pcm[i])
                linearFree(S[ch].pcm[i]);
    }
    ndspChnWaveBufClear(CH_MUSIC);
    for (int i = 0; i < MOUT; i++) {
        linearFree(mpcm[i]);
        mpcm[i] = NULL;
    }
    music_exit();
    ndspExit();
    ndsp_ok = false;
}

/* ---- the calls (main thread) --------------------------------------------------------- */

void audio_play(int ch, const char *path, bool loop, float fadein, bool queue)
{
    if (!ndsp_ok || ch < 0 || ch >= CH_COUNT)
        return;
    if (ch == CH_MUSIC) {
        if (queue)
            music_queue(path, loop);
        else
            music_play_now(path, loop, fadein);
        LightEvent_Signal(&aev);
        return;
    }
    Cmd c = {C_PLAY, (u8)ch, loop, queue, fadein, ++play_gen[ch], ""};
    snprintf(c.path, sizeof(c.path), "%s", path);
    cmd_playing[ch] = true;
    post(&c);
}

void audio_stop(int ch, float fadeout)
{
    if (!ndsp_ok || ch < 0 || ch >= CH_COUNT)
        return;
    if (ch == CH_MUSIC) {
        music_stop(fadeout);
        LightEvent_Signal(&aev);
        return;
    }
    Cmd c = {C_STOP, (u8)ch, false, false, fadeout, ++play_gen[ch], ""};
    cmd_playing[ch] = false;
    post(&c);
}

void audio_pause(int ch, bool paused)
{
    if (!ndsp_ok || ch < 0 || ch >= CH_COUNT)
        return;
    if (ch == CH_MUSIC) {
        want_pause = paused;
        LightEvent_Signal(&aev);
        for (int v = 0; v < 6; v++)   /* the minigame sound voices (SFX_CH0..), ours */
            ndspChnSetPaused(4 + v, paused);
        return;
    }
    ndspChnSetPaused(ch, paused);
}

bool audio_playing(int ch)
{
    if (!ndsp_ok || ch < 0 || ch >= CH_COUNT)
        return false;
    if (ch == CH_MUSIC)
        return music_playing();
    return cmd_playing[ch] && done_gen[ch] != play_gen[ch];
}

void audio_music_change(const char *path, bool loop, float fadein)
{
    if (!ndsp_ok)
        return;
    music_change(path, loop, fadein);
    LightEvent_Signal(&aev);
}

void audio_music_prefetch(const char *path, bool loop)
{
    if (ndsp_ok)
        music_prefetch(path, loop);
}

void audio_set_volume(int ch, float v)
{
    if (ch < 0 || ch >= CH_COUNT)
        return;
    user_vol[ch] = v;
    if (ndsp_ok)
        LightEvent_Signal(&aev);
}

void audio_update(float dt)
{
    if (!ndsp_ok || athread_ok)
        return;
    /* no audio thread: the main loop does its work */
    audio_pass(dt);
}

/* The background thread opens music files (reading them into memory). */
bool audio_bg_work(void) { return ndsp_ok && music_open_work(); }

void audio_music_duck(float gain)
{
    music_duck = gain;   /* (the audio thread applies it) */
}

/* ---- machine voices ------------------------------------------------------ */

/* machine-voice syllables: decoded once, mono PCM16 in linear memory */
#define VOX_CH 3
#define VOX_MAX 32
static s16 *vox_pcm[VOX_MAX];
static u32 vox_len[VOX_MAX];
static long vox_rate[VOX_MAX];
static int nvox;
static ndspWaveBuf vox_wb;

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
    mix[0] = mix[1] = volume * user_vol[CH_SOUND];
    ndspChnSetMix(ch, mix);
    memset(&sfx_wb[v], 0, sizeof(sfx_wb[v]));
    sfx_wb[v].data_vaddr = sfx_pcm[index];
    sfx_wb[v].nsamples = sfx_len[index];
    ndspChnWaveBufAdd(ch, &sfx_wb[v]);
}
