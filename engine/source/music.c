/* The music mixer: see music.h.
 *
 * Changing the music. A change asked for while a track plays is planned on
 * the playing track's tempo grid (MusicMeta, from vn3ds.json "music"):
 *   1. the end of the current loop, if it comes within CAP_S: the track
 *      finishes its loop and the new one starts on the downbeat;
 *   2. else the next phrase boundary (phrase_bars bars, also within CAP_S);
 *   3. else (no grid, or no boundary in time) the next beat, with an
 *      equal-power crossfade of XFADE_S.
 * At 1 and 2 the old track gets a short raised-cosine fade around the
 * boundary (SPLICE_PRE_S before, SPLICE_POST_S after) and the new one starts
 * exactly on it after a few milliseconds of fade-in, so it sounds like one
 * piece of music turning a corner rather than a cut. The new track has to be
 * decoded far enough ahead (READY_S) before a plan is made, so a splice can
 * never stall; the mixer's clock counts mixed frames, so where a splice lands
 * does not depend on how far ahead the output is queued.
 *
 * Ownership. A deck's decoder and the write end of its buffer belong to the
 * background thread; the read end, the voices and everything else to the
 * mixer, under `mx`. The main thread only ever moves a deck from FREE to OPEN
 * (or asks for it to be closed); the background thread does the rest. */

#include "music.h"

#include "audio_dec.h"
#include "bg.h"
#include "platform.h"

#define NDECK 4
#define DECK_CAP 65536u    /* frames of decoded audio a deck can hold (a power of two) */
#define WANT_PLAY_S 1.2f   /* kept decoded ahead of a playing track */
#define WANT_PREFETCH_S 0.6f
#define READY_S 0.35f      /* decoded before a planned change may use the track */
#define READY_NOW_S 0.08f  /* ... before an immediate start */
#define CHUNK 1024         /* frames per decoder call (short, so the audio thread never holds the CPU long) */
#define CAP_S 8.0f         /* the longest a change of music waits for its moment */
#define LEAD_S 0.25f       /* a planned splice is at least this far ahead */
#define SPLICE_PRE_S 0.03f
#define SPLICE_POST_S 0.15f
#define SPLICE_IN_S 0.015f
#define XFADE_S 1.5f
#define NVOICE 3
#define BLOCK 32           /* frames per gain step */

#define LD(x) __atomic_load_n(&(x), __ATOMIC_ACQUIRE)
#define ST(x, v) __atomic_store_n(&(x), (v), __ATOMIC_RELEASE)

enum { DK_FREE, DK_OPEN, DK_READY, DK_FAILED };
enum { CUR_LIN, CUR_COS, CUR_EQP };
enum { PLAN_LOOP, PLAN_PHRASE, PLAN_BEAT, PLAN_NOW };
static const char *const PLAN_NAME[] = {"loop end", "phrase", "beat crossfade", "crossfade"};

typedef struct {
    int state;     /* DK_*; FREE -> OPEN by the main thread, the rest by the background thread */
    int close_req; /* the main thread asks for the deck back */
    int loop;
    u32 want;      /* frames to keep decoded */
    u32 wr, rd;    /* free-running frame counters into buf */
    int eof;
    char path[300];
    MusicMeta meta;
    bool has_meta;
    ADec dec;      /* background thread only */
    bool dec_open;
    int channels;  /* valid once READY */
    long rate;
    s64 len;
    s16 *buf;      /* DECK_CAP frames, stereo */
    u64 req_us, dec_us, dec_frames;
} Deck;

typedef struct {
    bool on;
    int deck;
    s64 start;      /* mixer frame at which it begins */
    s64 pos;        /* deck frames consumed: the position in the track, loops unwrapped */
    s64 stop_pos;   /* ends when pos reaches it (-1: no) */
    int after;      /* queued: starts when voice `after` ends (-1: no) */
    double step, frac;
    s16 cur[2], nxt[2];
    bool primed, logged_start;
    s64 e0, e1;     /* gain envelope: g0 until e0, g1 from e1 */
    float g0, g1;
    u8 curve;
    bool ends;      /* off once the envelope is over */
    u32 underruns;
    int plan;       /* how it came in (PLAN_*, -1 = a plain start) */
} Voice;

static Deck D[NDECK];
static Voice V[NVOICE];
static BgMutex mx = BG_MUTEX_INIT;
static s64 clk;
static long out_rate = 32000;
static int prefetch_deck = -1;
static bool flush_flag;
static struct {
    bool on, change;
    int deck;
    float fadein;
    u64 since_us;
} pend;

/* ---- decks ------------------------------------------------------------------ */

void music_init(void)
{
    for (int i = 0; i < NDECK; i++)
        if (!D[i].buf)
            D[i].buf = malloc(DECK_CAP * 2 * sizeof(s16));
    for (int v = 0; v < NVOICE; v++)
        V[v].on = false;
    pend.on = false;
    prefetch_deck = -1;
}

void music_exit(void)
{
    for (int i = 0; i < NDECK; i++) {
        if (D[i].dec_open)
            adec_close(&D[i].dec);
        D[i].dec_open = false;
        D[i].state = DK_FREE;
        D[i].close_req = 0;
        free(D[i].buf);
        D[i].buf = NULL;
    }
}

static bool deck_used(int d)
{
    if (d == prefetch_deck || (pend.on && pend.deck == d))
        return true;
    for (int v = 0; v < NVOICE; v++)
        if (V[v].on && V[v].deck == d)
            return true;
    return false;
}

static void deck_release(int d)
{
    if (d < 0 || deck_used(d))
        return;
    ST(D[d].close_req, 1);
    bg_wake();
}

static u32 secs_to_frames(const Deck *d, float s)
{
    long rate = LD(d->state) == DK_READY ? d->rate : 48000;
    u32 f = (u32)(rate * s);
    return f > DECK_CAP - CHUNK ? DECK_CAP - CHUNK : f;
}

/* The prefetched deck for `path`, or a free deck asked to open it; -1 if
 * every deck is busy. */
static int deck_get(const char *path, bool loop, float want_s)
{
    int d = -1;
    if (prefetch_deck >= 0 && !strcmp(D[prefetch_deck].path, path) &&
        LD(D[prefetch_deck].state) != DK_FAILED) {
        d = prefetch_deck;
        prefetch_deck = -1;
    } else {
        for (int i = 0; i < NDECK && d < 0; i++)
            if (LD(D[i].state) == DK_FREE && !LD(D[i].close_req) && !deck_used(i) && D[i].buf)
                d = i;
        if (d < 0 && prefetch_deck >= 0) {   /* make room: drop the prefetch */
            int p = prefetch_deck;
            prefetch_deck = -1;
            deck_release(p);
        }
        if (d < 0) {
            LOG("music: no free deck for %s", path);
            return -1;
        }
        Deck *k = &D[d];
        snprintf(k->path, sizeof(k->path), "%s", path);
        k->has_meta = app_music_meta(path, &k->meta);
        k->wr = k->rd = 0;
        k->eof = 0;
        k->dec_us = k->dec_frames = 0;
        k->req_us = platform_us();
        ST(k->state, DK_OPEN);
    }
    ST(D[d].loop, loop ? 1 : 0);
    ST(D[d].want, secs_to_frames(&D[d], want_s));
    bg_wake();
    return d;
}

/* ---- background thread -------------------------------------------------------- */

static void deck_fill(Deck *k)
{
    u32 wr = k->wr, rd = LD(k->rd), fill = wr - rd, want = LD(k->want);
    u32 n = want > fill ? want - fill : 0;
    if (n > CHUNK)
        n = CHUNK;
    u32 at = wr % DECK_CAP;
    if (n > DECK_CAP - at)
        n = DECK_CAP - at;
    if (n == 0)
        return;
    bool ended = false;
    u64 t0 = platform_us();
    long got = adec_fill(&k->dec, k->buf + at * (u32)k->channels, (long)n, LD(k->loop) != 0, &ended);
    k->dec_us += platform_us() - t0;
    k->dec_frames += (u64)(got > 0 ? got : 0);
    ST(k->wr, wr + (u32)(got > 0 ? got : 0));
    if (ended)
        ST(k->eof, 1);
}

/* Closing and decoding: the thread that decodes (the 3DS audio thread). A
 * deck still being opened is left alone until the opener is done with it. */
bool music_decode_work(void)
{
    for (int i = 0; i < NDECK; i++) {
        Deck *k = &D[i];
        int st = LD(k->state);
        if (!LD(k->close_req) || st == DK_OPEN)
            continue;
        if (k->dec_open) {
            if (k->dec_frames >= (u64)k->rate * 5)
                PERF("music: %s: %s, %.2f ms of decoding per second of audio", k->path,
                     adec_codec_name(k->dec.codec), k->dec_us / 1000.0 * k->rate / (double)k->dec_frames);
            adec_close(&k->dec);
            k->dec_open = false;
        }
        ST(k->state, DK_FREE);
        ST(k->close_req, 0);
        return true;
    }
    Deck *best = NULL;
    float best_r = 2;
    for (int i = 0; i < NDECK; i++) {
        Deck *k = &D[i];
        if (LD(k->state) != DK_READY || LD(k->eof) || LD(k->close_req))
            continue;
        u32 fill = k->wr - LD(k->rd), want = LD(k->want);
        float r = want ? (float)fill / (float)want : 1;
        if (r < best_r && fill < want) {
            best_r = r;
            best = k;
        }
    }
    if (best) {
        deck_fill(best);
        return true;
    }
    return false;
}

/* Opening: the background thread. The whole file is read into memory
 * (Snapshot's loops are under a megabyte), so decoding never waits for the
 * SD card behind texture reads. */
bool music_open_work(void)
{
    for (int i = 0; i < NDECK; i++) {
        Deck *k = &D[i];
        if (LD(k->state) != DK_OPEN)
            continue;
        if (LD(k->close_req)) {
            ST(k->state, DK_FAILED);   /* (freed by music_decode_work) */
            return true;
        }
        u64 t0 = platform_us();
        size_t len = 0;
        u8 *data = adec_read_file(k->path, 8u << 20, &len);
        u64 t1 = platform_us();
        bool ok = data ? adec_open_mem(&k->dec, data, len) : adec_open(&k->dec, k->path);
        if (!ok) {
#ifdef __3DS__
            LOG("music: cannot play %s (missing, or not Ogg Opus / Vorbis)", k->path);
#else
            /* (the desktop build already says so: "[audio] MISSING") */
            PERF("music: cannot play %s", k->path);
#endif
            ST(k->state, DK_FAILED);
            return true;
        }
        k->dec_open = true;
        k->channels = k->dec.channels;
        k->rate = k->dec.rate;
        k->len = adec_length(&k->dec);
        u64 t2 = platform_us();
        PERF("music: opened %s (%u KB read in %.1f ms, decoder set up in %.1f ms; %s, %d ch, %ld Hz, "
             "%.2f s loop), %.1f ms after the request",
             k->path, (unsigned)(len >> 10), (t1 - t0) / 1000.0, (t2 - t1) / 1000.0,
             adec_codec_name(k->dec.codec), k->channels, k->rate,
             k->len > 0 ? (double)k->len / k->rate : -1.0, (t2 - k->req_us) / 1000.0);
        ST(k->state, DK_READY);
        return true;
    }
    return false;
}

bool music_bg_work(void)
{
    /* one thread for everything (the desktop build) */
    bool did = music_open_work();
    return music_decode_work() || did;
}

/* ---- voices -------------------------------------------------------------------- */

static float env(const Voice *v, s64 f)
{
    if (f <= v->e0)
        return v->g0;
    if (f >= v->e1)
        return v->g1;
    float x = (float)(f - v->e0) / (float)(v->e1 - v->e0);
    switch (v->curve) {
    case CUR_COS: return v->g0 + (v->g1 - v->g0) * (0.5f - 0.5f * cosf(3.14159265f * x));
    case CUR_EQP:
        return v->g1 >= v->g0 ? v->g0 + (v->g1 - v->g0) * sinf(x * 1.5707963f)
                              : v->g1 + (v->g0 - v->g1) * cosf(x * 1.5707963f);
    default: return v->g0 + (v->g1 - v->g0) * x;
    }
}

static void set_env(Voice *v, s64 e0, s64 e1, float g0, float g1, u8 curve, bool ends)
{
    v->e0 = e0;
    v->e1 = e1 > e0 ? e1 : e0 + 1;
    v->g0 = g0;
    v->g1 = g1;
    v->curve = curve;
    v->ends = ends;
}

static int voice_new(int deck, s64 start, int plan)
{
    for (int i = 0; i < NVOICE; i++) {
        Voice *v = &V[i];
        if (v->on)
            continue;
        memset(v, 0, sizeof(*v));
        v->on = true;
        v->deck = deck;
        v->start = start;
        v->stop_pos = -1;
        v->after = -1;
        v->plan = plan;
        const Deck *k = &D[deck];
        v->step = (double)k->rate / (double)out_rate;
        set_env(v, start, start, 1, 1, CUR_LIN, false);
        return i;
    }
    return -1;
}

static void voice_off(int i)
{
    Voice *v = &V[i];
    if (!v->on)
        return;
    v->on = false;
    if (v->underruns)
        PERF("music: %s ran dry %u times (decoding fell behind)", D[v->deck].path, (unsigned)v->underruns);
    deck_release(v->deck);
}

/* The track that is playing and not on its way out, or -1. */
static int main_voice(void)
{
    int best = -1;
    for (int i = 0; i < NVOICE; i++) {
        const Voice *v = &V[i];
        if (v->on && v->after < 0 && !v->ends && (best < 0 || v->start > V[best].start))
            best = i;
    }
    return best;
}

/* 1 = a frame, 0 = nothing decoded yet (underrun), -1 = the track is over. */
static int pop(Voice *v, s16 o[2])
{
    Deck *k = &D[v->deck];
    if (v->stop_pos >= 0 && v->pos >= v->stop_pos)
        return -1;
    u32 rd = k->rd;
    if (LD(k->wr) == rd) {
        if (LD(k->eof) && LD(k->wr) == rd)
            return -1;
        return 0;
    }
    const s16 *s = k->buf + (rd % DECK_CAP) * (u32)k->channels;
    o[0] = s[0];
    o[1] = k->channels == 2 ? s[1] : s[0];
    ST(k->rd, rd + 1);
    v->pos++;
    return 1;
}

/* The voice's next output frame; false once it has ended. */
static bool voice_frame(Voice *v, float out[2])
{
    if (v->step <= 0) {   /* a queued file still opening */
        const Deck *k = &D[v->deck];
        if (LD(k->state) == DK_FAILED)
            return false;
        if (LD(k->state) != DK_READY) {
            v->underruns++;
            out[0] = out[1] = 0;
            return true;
        }
        v->step = (double)k->rate / (double)out_rate;
    }
    if (v->step == 1.0) {
        s16 o[2];
        int r = pop(v, o);
        if (r < 0)
            return false;
        if (r == 0) {
            v->underruns++;
            out[0] = out[1] = 0;
            return true;
        }
        out[0] = o[0];
        out[1] = o[1];
        return true;
    }
    /* another sample rate than the output: linear interpolation */
    if (!v->primed) {
        if (pop(v, v->cur) < 0 || pop(v, v->nxt) < 0)
            return false;
        v->primed = true;
    }
    float t = (float)v->frac;
    out[0] = v->cur[0] + (v->nxt[0] - v->cur[0]) * t;
    out[1] = v->cur[1] + (v->nxt[1] - v->cur[1]) * t;
    v->frac += v->step;
    while (v->frac >= 1.0) {
        v->frac -= 1.0;
        v->cur[0] = v->nxt[0];
        v->cur[1] = v->nxt[1];
        int r = pop(v, v->nxt);
        if (r < 0)
            return false;
        if (r == 0)
            v->underruns++;
    }
    return true;
}

static void grid(const Deck *k, double *bar, double *beat, double *phrase)
{
    const MusicMeta *m = &k->meta;
    int bpb = m->beats_per_bar ? m->beats_per_bar : 4;
    *bar = m->bars > 0 && k->len > 0 ? (double)k->len / m->bars : k->rate * 60.0 * bpb / m->bpm;
    *beat = *bar / bpb;
    *phrase = *bar * (m->phrase_bars ? m->phrase_bars : 4);
}

/* Where (in the playing track's frames) the next track should come in. */
static s64 plan_change(const Voice *a, int *kind)
{
    const Deck *k = &D[a->deck];
    double lead = LEAD_S * k->rate, cap = CAP_S * k->rate;
    double pos = (double)a->pos;
    if (!k->has_meta || k->meta.bpm <= 0) {
        *kind = PLAN_NOW;
        return a->pos + (s64)lead;
    }
    double bar, beat, phrase;
    grid(k, &bar, &beat, &phrase);
    double base = 0, len = (double)k->len;
    if (len > 0)
        base = floor(pos / len) * len;
    double in = pos - base;
    if (len > 0 && LD(k->loop)) {
        double end = base + len;
        if (end - pos < lead)
            end += len;
        if (end - pos <= cap) {
            *kind = PLAN_LOOP;
            return (s64)end;
        }
    }
    double ph = base + ceil((in + lead) / phrase) * phrase;
    if (len > 0 && ph > base + len)
        ph = base + len;
    if (ph - pos >= lead && ph - pos <= cap) {
        *kind = ph == base + len ? PLAN_LOOP : PLAN_PHRASE;
        return (s64)llround(ph);
    }
    *kind = PLAN_BEAT;
    return (s64)llround(base + ceil((in + lead) / beat) * beat);
}

static const char *base_name(const char *p)
{
    const char *s = strrchr(p, '/');
    return s ? s + 1 : p;
}

/* The pending change, once its track is decoded far enough. */
static void start_pending(void)
{
    if (!pend.on)
        return;
    Deck *b = &D[pend.deck];
    int st = LD(b->state);
    if (st == DK_FAILED) {
        pend.on = false;
        deck_release(pend.deck);
        int a = main_voice();
        if (a >= 0 && pend.change)   /* the script wanted this music gone */
            set_env(&V[a], clk, clk + (s64)(XFADE_S * out_rate), env(&V[a], clk), 0, CUR_LIN, true);
        return;
    }
    if (st != DK_READY)
        return;
    u32 fill = LD(b->wr) - b->rd;
    if (fill < (u32)(READY_S * b->rate) && !LD(b->eof) && fill < LD(b->want))
        return;
    int a = main_voice();
    bool silent = true;
    for (int i = 0; i < NVOICE; i++)
        silent &= !V[i].on;
    if (silent)
        out_rate = b->rate;
    ST(b->want, secs_to_frames(b, WANT_PLAY_S));
    pend.on = false;
    u64 waited = platform_us() - pend.since_us;
    if (a < 0) {
        int v = voice_new(pend.deck, clk, -1);
        if (v < 0) {
            deck_release(pend.deck);
            return;
        }
        float fi = pend.fadein > 0.01f ? pend.fadein : 0.01f;
        set_env(&V[v], clk, clk + (s64)(fi * out_rate), 0, 1, CUR_EQP, false);
        PERF("music: start %s (fade-in %.2f s) %.1f ms after it was asked for", base_name(b->path), fi,
             waited / 1000.0);
        return;
    }
    Voice *va = &V[a];
    const Deck *ka = &D[va->deck];
    int kind;
    s64 at = plan_change(va, &kind);
    s64 s = clk + (s64)llround((double)(at - va->pos) / va->step);
    int v = voice_new(pend.deck, s, kind);
    if (v < 0) {
        deck_release(pend.deck);
        return;
    }
    Voice *vb = &V[v];
    if (kind == PLAN_LOOP || kind == PLAN_PHRASE) {
        set_env(va, s - (s64)(SPLICE_PRE_S * out_rate), s + (s64)(SPLICE_POST_S * out_rate),
                env(va, clk), 0, CUR_COS, true);
        set_env(vb, s, s + (s64)(SPLICE_IN_S * out_rate), 0, 1, CUR_COS, false);
    } else {
        set_env(va, s, s + (s64)(XFADE_S * out_rate), env(va, clk), 0, CUR_EQP, true);
        set_env(vb, s, s + (s64)(XFADE_S * out_rate), 0, 1, CUR_EQP, false);
    }
    double bar = 0, beat = 0, phrase = 0;
    if (ka->has_meta && ka->meta.bpm > 0)
        grid(ka, &bar, &beat, &phrase);
    double tr = ka->len > 0 ? fmod((double)at, (double)ka->len) : (double)at;
    PERF("music: change %s -> %s: %s at %.3f s into the loop (bar %.3f, beat %.3f, phrase %.3f; "
         "loop %.3f s), in %.2f s; out frame %lld at %ld Hz; track frame %lld, loop %lld frames, "
         "bar %.3f frames, phrase %.3f frames; ready %.1f ms after the request",
         base_name(ka->path), base_name(b->path), PLAN_NAME[kind], tr / ka->rate,
         bar > 0 ? tr / bar : -1.0, beat > 0 ? tr / beat : -1.0, phrase > 0 ? tr / phrase : -1.0,
         ka->len > 0 ? (double)ka->len / ka->rate : -1.0, (double)(s - clk) / out_rate, (long long)s,
         out_rate, (long long)at, (long long)ka->len, bar, phrase, waited / 1000.0);
}

/* Undo a change that is planned but has not begun. */
static void cancel_planned(void)
{
    int a = main_voice();
    for (int i = 0; i < NVOICE; i++) {
        Voice *v = &V[i];
        if (!v->on || v->start <= clk || v->after >= 0)
            continue;
        /* the outgoing track: the one whose fade starts after now */
        for (int j = 0; j < NVOICE; j++) {
            Voice *o = &V[j];
            if (j != i && o->on && o->ends && o->e0 > clk)
                set_env(o, 0, 0, 1, 1, CUR_LIN, false);
        }
        voice_off(i);
    }
    (void)a;
}

static void cancel_pending(void)
{
    if (!pend.on)
        return;
    pend.on = false;
    deck_release(pend.deck);
}

/* ---- the calls -------------------------------------------------------------------- */

void music_change(const char *path, bool loop, float fadein)
{
    bg_mutex_lock(&mx);
    int a = main_voice();
    if (a >= 0 && !strcmp(D[V[a].deck].path, path)) {
        /* the same music: it carries on */
        cancel_pending();
        cancel_planned();
        ST(D[V[a].deck].loop, loop ? 1 : 0);
        bg_mutex_unlock(&mx);
        return;
    }
    if (pend.on && !strcmp(D[pend.deck].path, path)) {
        pend.fadein = fadein;
        bg_mutex_unlock(&mx);
        return;
    }
    cancel_pending();
    cancel_planned();
    int d = deck_get(path, loop, WANT_PLAY_S);
    if (d >= 0) {
        pend.on = true;
        pend.deck = d;
        pend.fadein = fadein;
        pend.change = main_voice() >= 0;
        pend.since_us = platform_us();
    }
    bg_mutex_unlock(&mx);
}

void music_prefetch(const char *path, bool loop)
{
    bg_mutex_lock(&mx);
    bool have = prefetch_deck >= 0 && !strcmp(D[prefetch_deck].path, path);
    if (pend.on && !strcmp(D[pend.deck].path, path))
        have = true;
    for (int i = 0; i < NVOICE; i++)
        if (V[i].on && !V[i].ends && !strcmp(D[V[i].deck].path, path))
            have = true;
    if (!have) {
        if (prefetch_deck >= 0) {
            int p = prefetch_deck;
            prefetch_deck = -1;
            deck_release(p);
        }
        int d = deck_get(path, loop, WANT_PREFETCH_S);
        prefetch_deck = d;
        if (d >= 0)
            PERF("music: prefetch %s", base_name(path));
    }
    bg_mutex_unlock(&mx);
}

void music_play_now(const char *path, bool loop, float fadein)
{
    bg_mutex_lock(&mx);
    cancel_pending();
    for (int i = 0; i < NVOICE; i++)
        voice_off(i);
    flush_flag = true;
    int d = deck_get(path, loop, WANT_PLAY_S);
    bg_mutex_unlock(&mx);
    if (d < 0)
        return;
    /* wait for the start of the file: a start has to be on time */
    u64 t0 = platform_us();
    Deck *k = &D[d];
    for (;;) {
        int st = LD(k->state);
        if (st == DK_FAILED)
            break;
        if (st == DK_READY &&
            (LD(k->wr) - k->rd >= (u32)(READY_NOW_S * k->rate) || LD(k->eof)))
            break;
        if (platform_us() - t0 > 1500000)
            break;
        if (bg_running()) {
            bg_wake();
            bg_sleep_ms(1);   /* (the decoding thread runs meanwhile) */
        } else {
            music_open_work();
            bg_sleep_ms(1);
        }
    }
    bg_mutex_lock(&mx);
    if (LD(k->state) == DK_READY) {
        out_rate = k->rate;
        int v = voice_new(d, clk, -1);
        if (v >= 0) {
            float fi = fadein > 0.005f ? fadein : 0.005f;
            set_env(&V[v], clk, clk + (s64)(fi * out_rate), 0, 1, CUR_EQP, false);
        } else {
            deck_release(d);
        }
    } else {
        deck_release(d);
    }
    bg_mutex_unlock(&mx);
    PERF("music: play %s at once: waited %.1f ms for it to be ready", base_name(path),
         (platform_us() - t0) / 1000.0);
}

void music_queue(const char *path, bool loop)
{
    bg_mutex_lock(&mx);
    int a = main_voice();
    if (a < 0) {
        bg_mutex_unlock(&mx);
        music_change(path, loop, 0);
        return;
    }
    for (int i = 0; i < NVOICE; i++)   /* one queued file at a time, like Ren'Py's queue */
        if (V[i].on && V[i].after >= 0)
            voice_off(i);
    int d = deck_get(path, loop, WANT_PLAY_S);
    if (d >= 0) {
        Voice *va = &V[a];
        Deck *ka = &D[va->deck];
        /* the current file plays to the end of this loop, then stops */
        if (ka->len > 0 && LD(ka->state) == DK_READY)
            va->stop_pos = (va->pos / ka->len + 1) * ka->len;
        ST(ka->loop, 0);
        int v = voice_new(d, 0, -1);
        if (v >= 0)
            V[v].after = a;
        else
            deck_release(d);
    }
    bg_mutex_unlock(&mx);
}

void music_stop(float fadeout)
{
    bg_mutex_lock(&mx);
    cancel_pending();
    for (int i = 0; i < NVOICE; i++) {
        Voice *v = &V[i];
        if (!v->on)
            continue;
        if (fadeout <= 0 || v->after >= 0 || v->start > clk) {
            voice_off(i);
            continue;
        }
        s64 e1 = clk + (s64)(fadeout * out_rate);
        if (v->ends && v->e1 <= e1)
            continue;   /* already fading out sooner */
        set_env(v, clk, e1, env(v, clk), 0, CUR_LIN, true);
    }
    if (fadeout <= 0)
        flush_flag = true;
    bg_mutex_unlock(&mx);
}

bool music_playing(void)
{
    bg_mutex_lock(&mx);
    bool on = pend.on;
    for (int i = 0; i < NVOICE; i++)
        on |= V[i].on;
    bg_mutex_unlock(&mx);
    return on;
}

long music_rate(void) { return out_rate; }
s64 music_clock(void) { return clk; }

bool music_take_flush(void)
{
    bg_mutex_lock(&mx);
    bool f = flush_flag;
    flush_flag = false;
    bg_mutex_unlock(&mx);
    return f;
}

/* ---- mixing ------------------------------------------------------------------------ */

/* Mixes voice i into acc for the n frames from mixer frame c0. True if a
 * queued file took over from it. */
static bool mix_voice(int i, s64 c0, long n, float (*acc)[2])
{
    Voice *v = &V[i];
    if (v->start >= c0 + n)
        return false;
    float ga = env(v, c0), gb = env(v, c0 + n);
    for (long j = 0; j < n; j++) {
        s64 c = c0 + j;
        if (c < v->start)
            continue;
        if (!v->logged_start) {
            v->logged_start = true;
            if (v->plan >= 0)
                PERF("music: splice: %s comes in at out frame %lld (%s)", base_name(D[v->deck].path),
                     (long long)c, PLAN_NAME[v->plan]);
        }
        float smp[2];
        if (!voice_frame(v, smp)) {
            /* the end of the file: a queued file follows on this very frame */
            bool took = false;
            voice_off(i);
            for (int q = 0; q < NVOICE; q++)
                if (V[q].on && V[q].after == i) {
                    V[q].after = -1;
                    V[q].start = c;
                    V[q].step = LD(D[V[q].deck].state) == DK_READY
                                    ? (double)D[V[q].deck].rate / (double)out_rate : 0;
                    set_env(&V[q], c, c, 1, 1, CUR_LIN, false);
                    took = true;
                }
            return took;
        }
        float g = ga + (gb - ga) * ((float)j / (float)n);
        acc[j][0] += smp[0] * g;
        acc[j][1] += smp[1] * g;
    }
    if (v->on && v->ends && c0 + n >= v->e1 && v->g1 <= 0)
        voice_off(i);
    return false;
}

long music_mix(s16 *out, long frames)
{
    bg_mutex_lock(&mx);
    start_pending();
    bool any = false;
    for (int i = 0; i < NVOICE; i++)
        any |= V[i].on;
    if (!any) {
        /* the clock runs on through silence, so the desktop build's
         * recording keeps its frames in step with it */
        clk += frames;
        bg_mutex_unlock(&mx);
        return 0;
    }
    for (long f0 = 0; f0 < frames; f0 += BLOCK) {
        long n = frames - f0 < BLOCK ? frames - f0 : BLOCK;
        float acc[BLOCK][2];
        memset(acc, 0, sizeof(acc));
        /* (a queued file that starts in this block is mixed in the next pass) */
        bool done[NVOICE] = {false};
        for (bool again = true; again;) {
            again = false;
            for (int i = 0; i < NVOICE; i++) {
                Voice *v = &V[i];
                if (done[i] || !v->on || v->after >= 0)
                    continue;
                done[i] = true;
                if (mix_voice(i, clk + f0, n, acc))
                    again = true;
            }
        }
        for (long j = 0; j < n; j++)
            for (int c = 0; c < 2; c++) {
                float x = acc[j][c];
                out[(f0 + j) * 2 + c] = (s16)(x > 32767 ? 32767 : x < -32768 ? -32768 : x);
            }
    }
    clk += frames;
    bg_mutex_unlock(&mx);
    return frames;
}
