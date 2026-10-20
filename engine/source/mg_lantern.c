/* Lantern Rhythm: keep the Lantern Watch's lanterns lit by tapping in time
 * with the music's motif. Paper lanterns float out of the attic window along
 * three perspective lanes and reach the hit line on their beat. Ember watches
 * from the window and brightens with your streak.
 *
 * The chart is timed from the moment the music starts (the same moment the
 * framework calls start()) on the game's own clock, so the visual beat holds
 * even if the music is missing or late.
 *
 * Score: weighted accuracy (perfect 1, good 0.6, miss 0; later sections weigh
 * more; stray taps cost a little) * 0.92 + longest streak / notes * 0.08. */

#include "minigame.h"

/* ---- tempo contract with the "lantern" music loop ------------------------- */

#define BPM 96.0f                /* exactly; 4/4, no pickup */
#define BEATS_PER_BAR 4
#define BARS 16                  /* one loop = 64 beats = 40.0 s */
#define OFFSET 0.0f              /* seconds from music start to bar 1, beat 1 */
#define BEAT (60.0f / BPM)       /* 0.625 s */

/* ---- rules ------------------------------------------------------------------ */

#define PERFECT_W 0.060f         /* +/- seconds for a perfect */
#define GOOD_W 0.120f            /* +/- seconds for a good; later is a miss */
#define NEAR_W 0.220f            /* a press this close to any lantern is never a stray */
#define STRAY_COST 0.15f         /* of a note's weight, per stray tap */
#define APPROACH_BEATS 3.0f      /* lanterns are visible this long before their beat */
#define APPROACH_T (APPROACH_BEATS * BEAT)
#define CHEAT_BEATS 8
#define SECTIONS 4
#define MAX_NOTES 128
#define STREAK_STEP 10           /* a streak sound every 10 */

static const float SEC_W[SECTIONS] = {1.0f, 1.2f, 1.4f, 1.6f};
static const char *const SEC_NAME[SECTIONS] = {"First Light", "Drift", "Between Worlds", "Ember's Chorus"};
static const char *const SEC_SUB[SECTIONS] = {"on the beat", "eighth notes", "off the beat", "two at once"};

/* One bell sample, pitched per lane: root, major third, fifth. */
static const float LANE_RATE[3] = {1.0f, 1.259921f, 1.498307f};

/* ---- view ------------------------------------------------------------------ */

#define VP_Y 84.0f               /* y of the vanishing point (s = 0) */
#define HIT_Y 196.0f             /* y of the hit line (s = 1) */
#define LANE_SPREAD 100.0f       /* lane spacing at the hit line */
#define Z_FAR 6.0f               /* spawn distance (hit line = 1) */
#define S_FAR (1.0f / Z_FAR)
#define D_HIT -0.12f             /* stereo depth at the hit line */
#define D_FAR 0.9f               /* stereo depth where lanterns appear */
#define EMBER_X 200.0f
#define EMBER_Y 70.0f

/* the framework's Cheat button: touches there are not lane taps */
#define CHEAT_RX MG_CHEAT_X
#define CHEAT_RY MG_CHEAT_Y
#define CHEAT_RW MG_CHEAT_W
#define CHEAT_RH MG_CHEAT_H

static const u32 LANE_COL[3] = {RGBA(255, 140, 120, 255), RGBA(255, 200, 110, 255), RGBA(200, 160, 255, 255)};
static const char *const LANE_KEYS[3] = {"Y / Left", "X / Up", "A / Right"};

/* ---- chart ------------------------------------------------------------------ */

/* Rhythm per bar as bitmasks over the eight eighth-note slots (bit 0 = beat 1,
 * bit 1 = the "and" of 1, ...). `optional` notes may be dropped by the seed;
 * the rhythm never gains notes, so the melody always has an onset under every
 * lantern. `chords` marks two-lane chords. */
typedef struct {
    u8 slots, chords, optional;
} BarRhythm;

#define B(x) (1u << (x))
#define QUARTERS (B(0) | B(2) | B(4) | B(6))
#define MOTIF (B(0) | B(2) | B(3) | B(4) | B(6) | B(7))  /* 1, 2, 2&, 3, 4, 4& */
#define TRESILLO (B(0) | B(3) | B(6) | B(7))            /* 1, 2&, 4, 4& */

static const BarRhythm RHYTHM[BARS] = {
    /* 1. First Light: count-in, then quarters */
    {0, 0, 0},
    {QUARTERS, 0, 0},
    {QUARTERS, 0, 0},
    {B(0) | B(2) | B(4), 0, 0},
    /* 2. Drift: the motif in eighths */
    {MOTIF, 0, B(3) | B(7)},
    {MOTIF, 0, B(3) | B(7)},
    {MOTIF, 0, B(7)},
    {B(0) | B(1) | B(2) | B(4), 0, 0},
    /* 3. Between Worlds: syncopation */
    {TRESILLO, 0, B(7)},
    {B(1) | B(3) | B(4) | B(6), 0, 0},
    {TRESILLO, 0, B(7)},
    {B(0) | B(3) | B(4), 0, 0},
    /* 4. Ember's Chorus: the motif again with chords on 1 and 3 */
    {MOTIF, B(0) | B(4), B(7)},
    {MOTIF, B(0) | B(4), 0},
    {MOTIF | B(5), B(0) | B(4), B(5)},
    {B(0) | B(2) | B(3) | B(4), B(0) | B(4), 0},
};

/* Contours of the motif (0 left/low, 1 middle, 2 right/high). */
static const u8 SHAPES[8][4] = {
    {0, 1, 2, 1}, {2, 1, 0, 1}, {0, 2, 1, 2}, {1, 0, 1, 2},
    {1, 2, 1, 0}, {0, 1, 0, 2}, {2, 1, 2, 0}, {1, 2, 0, 1},
};

enum { N_PENDING, N_PERFECT, N_GOOD, N_MISS, N_SKIP };
enum { POP_PERFECT, POP_GOOD, POP_MISS };

typedef struct {
    float t;       /* beat time, seconds from music start */
    float jt;      /* when it was judged */
    s16 partner;   /* other note of a chord, or -1 */
    u8 lane, sec, state;
    bool reserved; /* Ember's help will hit it */
    bool autohit;
} Note;

static struct {
    Note notes[MAX_NOTES];
    int n;
    float T;          /* own clock: seconds since the music started */
    float etime;      /* E.time last frame, to notice pauses */
    int last_beat;
    float cheat_t, cheat_until;
    bool cheat_on;
    int streak, max_streak;
    int perfect, good, miss, strays;
    float stray_pen;
    float press_t[3];
    float pop_t[3];
    u8 pop_kind[3];
    float cheer_t, worry_t;
    float banner_t;
    int banner_sec;
    float resync_t;
    bool finale;
    float finale_t;
    u32 rng;
} S;

static u32 crand(void)
{
    S.rng ^= S.rng << 13;
    S.rng ^= S.rng >> 17;
    S.rng ^= S.rng << 5;
    return S.rng;
}

static void add_note(float t, int lane, int sec, int partner)
{
    if (S.n >= MAX_NOTES)
        return;
    Note *n = &S.notes[S.n++];
    memset(n, 0, sizeof(*n));
    n->t = t;
    n->lane = (u8)lane;
    n->sec = (u8)sec;
    n->partner = (s16)partner;
}

static void gen_chart(u32 seed)
{
    static const u8 WALK[8] = {0, 1, 2, 3, 2, 1, 0, 1};
    S.rng = seed ? seed : 0x2545F491u;
    for (int i = 0; i < 4; i++)
        crand();
    int theme = (int)(crand() % 8);
    S.n = 0;
    for (int sec = 0; sec < SECTIONS; sec++) {
        u8 shape[4];
        int rot = sec == 2 ? 1 : 0;   /* "Between Worlds" starts the motif one step later */
        for (int k = 0; k < 4; k++)
            shape[k] = SHAPES[theme][(k + rot) % 4];
        int var = (int)(crand() % 3);   /* the answering bar: mirror, retrograde or both */
        bool open = crand() & 1;        /* chord colour: outer lanes or neighbours */
        for (int j = 0; j < 4; j++) {
            int bar = sec * 4 + j;
            const BarRhythm *r = &RHYTHM[bar];
            u32 slots = r->slots;
            if (r->optional && crand() % 100 < 35) {
                u32 opts[8], no = 0;
                for (int b = 0; b < 8; b++)
                    if (r->optional & B(b))
                        opts[no++] = B(b);
                slots &= ~opts[crand() % no];
            }
            u8 sh[4];
            for (int k = 0; k < 4; k++) {
                int src = (j == 1 && var >= 1) ? 3 - k : k;
                int l = shape[src];
                sh[k] = (u8)((j == 1 && var != 1) ? 2 - l : l);
            }
            int count = 0, k = 0;
            for (int b = 0; b < 8; b++)
                count += (slots >> b) & 1;
            for (int b = 0; b < 8; b++) {
                if (!(slots & B(b)))
                    continue;
                int lane = sh[WALK[k % 8]];
                if (j == 3 && k == count - 1)
                    lane = 1;   /* phrases come home to the middle */
                float t = OFFSET + ((float)(bar * BEATS_PER_BAR) + b * 0.5f) * BEAT;
                if (r->chords & B(b)) {
                    int other;
                    if (lane == 1)
                        other = (open ^ (j & 1)) ? 0 : 2;
                    else
                        other = open ? 2 - lane : 1;
                    add_note(t, lane, sec, S.n + 1);
                    add_note(t, other, sec, S.n - 1);
                } else {
                    add_note(t, lane, sec, -1);
                }
                k++;
            }
        }
    }
}

/* ---- play ------------------------------------------------------------------- */

static void start(u32 seed)
{
    memset(&S, 0, sizeof(S));
    gen_chart(seed);
    S.etime = E.time;
    S.last_beat = -1;
    S.cheat_t = S.cheer_t = S.worry_t = S.banner_t = S.resync_t = S.finale_t = -100;
    for (int l = 0; l < 3; l++)
        S.press_t[l] = S.pop_t[l] = -100;
}

static int sec_at(float T)
{
    int bar = (int)floorf((T - OFFSET) / (BEAT * BEATS_PER_BAR));
    return bar < 0 ? 0 : (bar / 4 >= SECTIONS ? SECTIONS - 1 : bar / 4);
}

static void hit(int i, float err, bool autohit)
{
    Note *n = &S.notes[i];
    bool perfect = autohit || fabsf(err) <= PERFECT_W;
    n->state = perfect ? N_PERFECT : N_GOOD;
    n->jt = S.T;
    n->autohit = autohit;
    if (perfect)
        S.perfect++;
    else
        S.good++;
    S.streak++;
    if (S.streak > S.max_streak)
        S.max_streak = S.streak;
    mg_sfx_pitch(perfect ? "lantern_hit_perfect" : "lantern_hit_good", LANE_RATE[n->lane]);
    S.pop_t[n->lane] = S.T;
    S.pop_kind[n->lane] = perfect ? POP_PERFECT : POP_GOOD;
    if (S.streak % STREAK_STEP == 0) {
        mg_sfx("lantern_streak");
        S.cheer_t = S.T;
    }
}

static void miss(int i)
{
    Note *n = &S.notes[i];
    n->state = N_MISS;
    n->jt = S.T;
    S.miss++;
    if (S.streak >= STREAK_STEP)
        mg_sfx("lantern_streak_break");
    S.streak = 0;
    mg_sfx_pitch("lantern_miss", 0.94f + 0.06f * n->lane);
    S.pop_t[n->lane] = S.T;
    S.pop_kind[n->lane] = POP_MISS;
    S.worry_t = S.T;
}

static void press(int lane)
{
    int best = -1;
    float bd = 1e9f;
    bool near = false;
    for (int i = 0; i < S.n; i++) {
        Note *n = &S.notes[i];
        if (n->lane != lane)
            continue;
        float d = fabsf(S.T - n->t);
        if (d < NEAR_W)
            near = true;
        if (n->state == N_PENDING && !n->reserved && d <= GOOD_W && d < bd) {
            bd = d;
            best = i;
        }
    }
    S.press_t[lane] = S.T;
    if (best >= 0) {
        hit(best, S.T - S.notes[best].t, false);
    } else if (!near) {
        S.strays++;
        S.stray_pen += SEC_W[sec_at(S.T)] * STRAY_COST;
        mg_sfx_pitch("lantern_stray", LANE_RATE[lane]);
    }
}

static void on_beat(int b)
{
    if (b >= 0 && b < 3)
        mg_sfx("lantern_count");
    else if (b == 3)
        mg_sfx("lantern_go");
    /* the last beat of each section's cadence bar leads into the next section */
    if (b % 16 == 15 && b / 16 + 1 < SECTIONS) {
        S.banner_sec = b / 16 + 1;
        S.banner_t = S.T;
        mg_sfx("lantern_section");
    }
}

/* The framework keeps the music playing while paused but stops calling
 * update(); jump the clock by the pause so the chart stays on the music,
 * and let the lanterns that drifted by meanwhile go unscored. */

static u32 lanes_pressed(const Input *in, bool cheat)
{
    u32 d = in->down, m = 0;
    if (d & (KEY_LEFT_ | KEY_Y_))
        m |= 1;
    if (d & (KEY_UP_ | KEY_X_))
        m |= 2;
    if (d & (KEY_RIGHT_ | KEY_A_))
        m |= 4;
    if (d & KEY_TOUCH_) {
        bool on_cheat = in->tx >= CHEAT_RX && in->tx < CHEAT_RX + CHEAT_RW && in->ty >= CHEAT_RY &&
                        in->ty < CHEAT_RY + CHEAT_RH;
        if (!(on_cheat && (cheat || !MG.cheat_used))) {
            int l = in->tx * 3 / BOT_W;
            m |= 1u << (l < 0 ? 0 : (l > 2 ? 2 : l));
        }
    }
    return m;
}

static bool update(const Input *in, float dt, bool cheat)
{
    /* The framework pauses the music together with the game, so the chart
     * clock (S.T) and the song stay in step across a pause. */
    S.T += dt;

    int b = (int)floorf((S.T - OFFSET) / BEAT);
    while (S.last_beat < b)
        on_beat(++S.last_beat);

    if (cheat) {
        S.cheat_on = true;
        S.cheat_t = S.T;
        S.cheat_until = S.T + CHEAT_BEATS * BEAT;
        for (int i = 0; i < S.n; i++) {
            Note *n = &S.notes[i];
            if (n->state == N_PENDING && n->t >= S.T - GOOD_W && n->t <= S.cheat_until)
                n->reserved = true;
        }
        mg_sfx("lantern_ember_help");
    }
    if (S.cheat_on && S.T > S.cheat_until + GOOD_W)
        S.cheat_on = false;

    /* Ember lights her lanterns exactly on the beat */
    for (int i = 0; i < S.n; i++)
        if (S.notes[i].state == N_PENDING && S.notes[i].reserved && S.T >= S.notes[i].t)
            hit(i, 0, true);

    u32 lanes = lanes_pressed(in, cheat);
    for (int l = 0; l < 3; l++)
        if (lanes & (1u << l))
            press(l);

    bool all = true;
    for (int i = 0; i < S.n; i++) {
        Note *n = &S.notes[i];
        if (n->state == N_PENDING && !n->reserved && S.T - n->t > GOOD_W)
            miss(i);
        if (n->state == N_PENDING)
            all = false;
    }
    if (all && !S.finale) {
        S.finale = true;
        S.finale_t = S.T;
        mg_sfx("lantern_finale");
    }
    return !(S.finale && S.T > S.finale_t + 2.0f);
}

/* ---- scoring ------------------------------------------------------------------ */

static float accuracy(void)
{
    int judged = S.perfect + S.good + S.miss;
    return judged ? (S.perfect + 0.6f * S.good) / judged : 0;
}

static int score(void)
{
    float total = 0, earned = 0;
    int count = 0;
    for (int i = 0; i < S.n; i++) {
        const Note *n = &S.notes[i];
        if (n->state == N_SKIP)
            continue;
        float w = SEC_W[n->sec];
        total += w;
        count++;
        if (n->state == N_PERFECT)
            earned += w;
        else if (n->state == N_GOOD)
            earned += 0.6f * w;
    }
    if (total <= 0 || !count)
        return 0;
    earned -= S.stray_pen;
    float acc = clampf(earned / total, 0, 1);
    float streak = clampf((float)S.max_streak / count, 0, 1);
    return (int)clampf(100.0f * (0.92f * acc + 0.08f * streak) + 0.5f, 0, 100);
}

static const char *verdict(void)
{
    static char buf[128];
    int s = score();
    const char *line = s >= 90 ? "Every lantern burns for Aron." :
                       s >= 70 ? "Ember is beaming." :
                       s >= 45 ? "Ember relit the rest." : "Ember keeps one lit anyway.";
    snprintf(buf, sizeof(buf), "%d perfect, %d good, %d dark. %s", S.perfect, S.good, S.miss, line);
    return buf;
}

/* ---- drawing ------------------------------------------------------------------- */

static u32 mix(u32 a, u32 b, float f)
{
    f = clampf(f, 0, 1);
    u32 out = 0;
    for (int sh = 0; sh < 32; sh += 8) {
        float ca = (float)((a >> sh) & 0xFF), cb = (float)((b >> sh) & 0xFF);
        out |= (u32)(ca + (cb - ca) * f + 0.5f) << sh;
    }
    return out;
}

static float s_y(float s) { return VP_Y + (HIT_Y - VP_Y) * s; }
static float s_x(float X, float s) { return 200 + X * s; }
static float s_depth(float s)
{
    return clampf(D_FAR + (D_HIT - D_FAR) * (s - S_FAR) / (1 - S_FAR), -0.4f, 1.0f);
}
/* Perspective scale of a lantern due `ahead` seconds from now. */
static float ahead_s(float ahead)
{
    float z = 1 + ahead / APPROACH_T * (Z_FAR - 1);
    return 1 / (z < 0.75f ? 0.75f : z);
}

static void lantern(int eye, float x, float y, float r, float d, u32 paper, float glow, float flame,
                    float alpha)
{
    u32 warm = RGBA(255, 170, 70, 255);
    if (glow > 0.01f) {
        mg_circle(eye, x, y, r * 2.6f, d + 0.02f, rgba_alpha(warm, 0.14f * glow * alpha));
        mg_circle(eye, x, y, r * 1.7f, d + 0.01f, rgba_alpha(warm, 0.28f * glow * alpha));
    }
    u32 wood = rgba_alpha(RGBA(70, 40, 30, 255), alpha);
    if (r > 5)
        mg_line(eye, x, y - r * 1.1f, x, y - r * 1.9f, 1, d, rgba_alpha(RGBA(40, 30, 30, 255), alpha * 0.8f));
    mg_rect(eye, x - r * 0.78f, y - r * 0.98f, r * 1.56f, r * 1.96f, d, rgba_alpha(paper, alpha));
    mg_circle(eye, x, y, r, d, rgba_alpha(paper, alpha));
    if (r > 6) {
        u32 rib = rgba_alpha(mix(paper, RGBA(60, 30, 20, 255), 0.45f), alpha * 0.6f);
        mg_line(eye, x - r * 0.42f, y - r * 0.9f, x - r * 0.42f, y + r * 0.9f, 1, d, rib);
        mg_line(eye, x + r * 0.42f, y - r * 0.9f, x + r * 0.42f, y + r * 0.9f, 1, d, rib);
    }
    if (flame > 0.01f)
        mg_circle(eye, x, y + r * 0.15f, r * (0.25f + 0.2f * flame), d - 0.01f,
                  rgba_alpha(RGBA(255, 245, 200, 255), flame * alpha));
    mg_rect(eye, x - r * 0.55f, y - r * 1.18f, r * 1.1f, r * 0.3f, d - 0.01f, wood);
    mg_rect(eye, x - r * 0.5f, y + r * 0.9f, r * 1.0f, r * 0.26f, d - 0.01f, wood);
}

static void draw_attic(int eye, float beat)
{
    float T = S.T;
    /* back wall and floor */
    mg_sky(eye, RGBA(30, 20, 32, 255), RGBA(70, 42, 44, 255));
    gfx_gradient(0, s_y(0.15f), TOP_W, TOP_H - s_y(0.15f), RGBA(44, 28, 26, 255), RGBA(90, 58, 40, 255));

    /* round window onto the stars */
    mg_circle(eye, 200, 52, 43, 0.97f, RGBA(96, 64, 44, 255));
    mg_circle(eye, 200, 52, 37, 0.96f, RGBA(14, 18, 50, 255));
    mg_circle(eye, 200, 66, 26, 0.96f, RGBA(28, 30, 74, 255));
    for (int i = 0; i < 14; i++) {
        float a = i * 2.39996f, rr = 8 + (float)((i * 53) % 26);
        float x = 200 + cosf(a) * rr, y = 52 + sinf(a) * rr;
        float tw = 0.5f + 0.5f * sinf(T * (1.3f + 0.21f * (i % 5)) + i);
        mg_rect(eye, x, y, 1.5f, 1.5f, 1.0f, rgba_alpha(MG_WHITE, 0.35f + 0.6f * tw));
    }
    mg_circle(eye, 218, 34, 5, 1.0f, RGBA(240, 235, 210, 230));
    mg_line(eye, 200, 15, 200, 89, 3, 0.95f, RGBA(96, 64, 44, 255));
    mg_line(eye, 163, 52, 237, 52, 3, 0.95f, RGBA(96, 64, 44, 255));
    mg_rect(eye, 150, 89, 100, 6, 0.93f, RGBA(110, 74, 50, 255));

    /* Ember on the sill: brighter with the streak, arms up on a milestone */
    float bright = 0.55f + 0.45f * clampf(S.streak / 20.0f, 0, 1);
    float worry = clampf(1 - (T - S.worry_t) / 0.7f, 0, 1);
    float cheer = clampf(1 - (T - S.cheer_t) / 0.9f, 0, 1);
    if (S.cheat_on || S.finale)
        cheer = 1, bright = 1;
    bright *= 1 - 0.4f * worry;
    float pulse = beat >= 0 ? powf(1 - (beat - floorf(beat)), 3) : 0;
    float bob = -3 * cheer * fabsf(sinf(T * 9)) + (S.cheat_on ? 1.5f * sinf(T * 6) : 0);
    float ex = EMBER_X + (S.cheat_on ? 2 * sinf(T * 3) : 0), ey = EMBER_Y + bob, ed = 0.88f;
    u32 glow = S.cheat_on ? RGBA(255, 215, 120, 255) : RGBA(255, 160, 80, 255);
    mg_circle(eye, ex, ey, 30 + 10 * bright + 4 * pulse, ed + 0.02f, rgba_alpha(glow, 0.16f * bright));
    mg_circle(eye, ex, ey, 18 + 4 * bright, ed + 0.01f, rgba_alpha(glow, 0.32f * bright));
    u32 robe = mix(RGBA(150, 80, 50, 255), RGBA(255, 150, 70, 255), bright);
    mg_tri(eye, ex, ey - 10, ex - 14, ey + 19, ex + 14, ey + 19, ed, robe);
    mg_tri(eye, ex, ey - 4, ex - 7, ey + 17, ex + 7, ey + 17, ed - 0.01f,
           mix(robe, RGBA(255, 230, 160, 255), 0.6f));
    float hand_y = cheer > 0 ? ey - 20 : ey + 6;
    float hand_x = cheer > 0 ? 13 : 9;
    mg_line(eye, ex - 5, ey - 4, ex - hand_x, hand_y, 2.5f, ed, robe);
    mg_line(eye, ex + 5, ey - 4, ex + hand_x, hand_y, 2.5f, ed, robe);
    if (cheer > 0) {
        mg_circle(eye, ex - hand_x, hand_y, 2.5f, ed - 0.01f, RGBA(255, 240, 200, 255));
        mg_circle(eye, ex + hand_x, hand_y, 2.5f, ed - 0.01f, RGBA(255, 240, 200, 255));
    }
    mg_circle(eye, ex, ey - 13, 6.5f, ed - 0.01f, mix(RGBA(200, 150, 110, 255), RGBA(255, 244, 210, 255), bright));

    /* rafters, collar beam, posts */
    u32 beam = RGBA(58, 38, 32, 255), beam2 = RGBA(74, 50, 38, 255);
    mg_line(eye, 120, -30, -30, 64, 9, 0.8f, beam2);
    mg_line(eye, 280, -30, 430, 64, 9, 0.8f, beam2);
    mg_line(eye, 200, -40, -40, 136, 15, 0.7f, beam);
    mg_line(eye, 200, -40, 440, 136, 15, 0.7f, beam);
    mg_rect(eye, 0, 0, TOP_W, 7, 0.72f, beam2);
    mg_line(eye, 40, 20, 40, 128, 9, 0.6f, beam);
    mg_line(eye, 360, 20, 360, 128, 9, 0.6f, beam);

    /* the Watch's own lanterns along the rafters, lit by the streak */
    int lit = S.finale && accuracy() >= 0.8f ? 6 : S.streak / 5;
    for (int i = 0; i < 6; i++) {
        float u = 0.42f + 0.18f * (i / 2);
        float x = i & 1 ? 200 + 240 * u : 200 - 240 * u, y = -40 + 176 * u + 3;
        bool on = (i < lit);
        mg_line(eye, x, y, x, y + 10, 1, 0.66f, RGBA(30, 20, 20, 200));
        float fl = on ? 0.8f + 0.2f * sinf(T * 7 + i) : 0;
        lantern(eye, x, y + 17, 5, 0.65f, on ? RGBA(255, 190, 110, 255) : RGBA(110, 80, 70, 255), fl, fl, 1);
    }

    /* floor planks, converging on the window */
    static const float SEG[5] = {0.15f, 0.36f, 0.62f, 0.95f, 1.4f};
    for (int p = -3; p <= 3; p++) {
        if (p >= -1 && p <= 1)
            continue;
        float X = p * 100.0f + (p > 0 ? -50 : 50);
        for (int k = 0; k < 4; k++)
            mg_line(eye, s_x(X, SEG[k]), s_y(SEG[k]), s_x(X, SEG[k + 1]), s_y(SEG[k + 1]), 1,
                    s_depth((SEG[k] + SEG[k + 1]) / 2), RGBA(30, 18, 16, 160));
    }

    /* the three lanes: ribbons of light on the floor */
    for (int l = 0; l < 3; l++) {
        float flash = clampf(1 - (T - S.press_t[l]) / 0.18f, 0, 1);
        float X0 = (l - 1) * LANE_SPREAD - 46, X1 = X0 + 92;
        for (int k = 0; k < 4; k++) {
            float a = SEG[k], b2 = SEG[k + 1], d = s_depth((a + b2) / 2);
            u32 c = rgba_alpha(LANE_COL[l], 0.05f + 0.05f * k + 0.25f * flash);
            mg_tri(eye, s_x(X0, a), s_y(a), s_x(X1, a), s_y(a), s_x(X1, b2), s_y(b2), d, c);
            mg_tri(eye, s_x(X0, a), s_y(a), s_x(X1, b2), s_y(b2), s_x(X0, b2), s_y(b2), d, c);
        }
    }
    for (int e = 0; e < 4; e++) {
        float X = -150.0f + e * 100;
        for (int k = 0; k < 4; k++)
            mg_line(eye, s_x(X, SEG[k]), s_y(SEG[k]), s_x(X, SEG[k + 1]), s_y(SEG[k + 1]), 1,
                    s_depth((SEG[k] + SEG[k + 1]) / 2), RGBA(255, 210, 160, 50 + 15 * k));
    }

    /* hit targets, pulsing with the beat */
    for (int l = 0; l < 3; l++) {
        float x = s_x((l - 1) * LANE_SPREAD, 1), flash = clampf(1 - (T - S.press_t[l]) / 0.18f, 0, 1);
        mg_circle(eye, x, HIT_Y, 20 + 2 * pulse, D_HIT + 0.02f,
                  rgba_alpha(LANE_COL[l], 0.35f + 0.35f * pulse + 0.3f * flash));
        mg_circle(eye, x, HIT_Y, 17, D_HIT + 0.01f, RGBA(28, 18, 24, 200));
        if (flash > 0)
            mg_circle(eye, x, HIT_Y, 17 * flash, D_HIT, rgba_alpha(LANE_COL[l], 0.5f * flash));
        mg_circle(eye, x, HIT_Y, 3, D_HIT, rgba_alpha(LANE_COL[l], 0.8f));
    }
}

static void draw_note(int eye, int i)
{
    const Note *n = &S.notes[i];
    float T = S.T, ahead = n->t - T;
    float hx = s_x((n->lane - 1) * LANE_SPREAD, 1);
    u32 tint = LANE_COL[n->lane];
    switch (n->state) {
    case N_PENDING: {
        if (ahead > APPROACH_T)
            return;
        float s = ahead_s(ahead), x = s_x((n->lane - 1) * LANE_SPREAD, s), y = s_y(s) - 4 * s;
        float r = 15 * s, d = s_depth(s);
        float alpha = clampf((APPROACH_T - ahead) / 0.3f, 0, 1);
        float flick = 0.75f + 0.25f * sinf(T * 11 + i * 1.7f);
        if (n->reserved)
            mg_circle(eye, x, y, r * (2.0f + 0.3f * sinf(T * 8)), d + 0.02f,
                      rgba_alpha(RGBA(255, 220, 120, 255), 0.35f * alpha));
        if (n->partner > i) {
            const Note *p = &S.notes[n->partner];
            mg_line(eye, x, y, s_x((p->lane - 1) * LANE_SPREAD, s), y, 2, d + 0.01f,
                    rgba_alpha(MG_GOLD, 0.45f * alpha));
        }
        lantern(eye, x, y, r, d, mix(tint, RGBA(120, 90, 90, 255), 0.35f), 0.35f * flick, 0.45f * flick, alpha);
        break;
    }
    case N_PERFECT:
    case N_GOOD: {
        float a = T - n->jt;
        if (a > 1.4f)
            return;
        float k = a / 1.4f, warm = n->state == N_PERFECT ? 1.0f : 0.7f;
        float x = hx + 6 * sinf(a * 5 + i), y = HIT_Y - 4 - 80 * a - 30 * a * a;
        float d = clampf(D_HIT - 0.1f + 0.7f * k, -0.4f, 0.8f);
        float alpha = 1 - k * k;
        if (a < 0.25f)   /* a ring of light where it caught */
            mg_circle(eye, hx, HIT_Y, 18 + 60 * a, D_HIT - 0.05f, rgba_alpha(RGBA(255, 220, 140, 255), 0.5f * (1 - a / 0.25f)));
        lantern(eye, x, y, 15 * (1 - 0.35f * k), d, mix(tint, RGBA(255, 244, 210, 255), 0.55f * warm),
                warm * (1.2f - 0.4f * k), 1, alpha);
        break;
    }
    case N_MISS: {
        float a = T - n->jt;
        if (a > 0.9f)
            return;
        float s = ahead_s(ahead);
        float x = s_x((n->lane - 1) * LANE_SPREAD, s), y = s_y(s) - 4 * s + 30 * a * a, r = 15 * s;
        float d = s_depth(s), alpha = 1 - a / 0.9f;
        float spark = a < 0.3f && sinf(T * 70 + i) > 0 ? 0.6f : 0;
        lantern(eye, x, y, r, d, RGBA(70, 60, 70, 255), spark * 0.5f, spark, alpha);
        for (int p = 0; p < 3; p++)   /* a little smoke */
            mg_circle(eye, x + (p - 1) * 4 + 3 * sinf(a * 6 + p), y - r - 6 - 30 * a - 7 * p, 2.5f + 4 * a,
                      d, rgba_alpha(RGBA(150, 140, 150, 255), 0.4f * alpha));
        break;
    }
    case N_SKIP: {
        float a = T - n->jt;
        if (a > 0.4f || ahead < -0.5f)
            return;
        float s = ahead_s(ahead > 0 ? ahead : 0);
        lantern(eye, s_x((n->lane - 1) * LANE_SPREAD, s), s_y(s), 15 * s, s_depth(s), RGBA(120, 100, 100, 255), 0, 0,
                1 - a / 0.4f);
        break;
    }
    }
}

static void draw_top(int eye)
{
    float T = S.T, beat = (T - OFFSET) / BEAT;
    char buf[64];
    draw_attic(eye, beat);

    for (int i = S.n - 1; i >= 0; i--)
        draw_note(eye, i);

    /* judgements over the targets */
    static const char *const POP[3] = {"Perfect", "Good", "Dark"};
    static const u32 POP_COL[3] = {RGBA(255, 230, 150, 255), RGBA(255, 255, 255, 255), RGBA(170, 160, 190, 255)};
    for (int l = 0; l < 3; l++) {
        float a = T - S.pop_t[l];
        if (a < 0 || a > 0.5f)
            continue;
        mg_text_centered(eye, POP[S.pop_kind[l]], s_x((l - 1) * LANE_SPREAD, 1), 219 - 6 * a, 0.45f, -0.25f,
                         rgba_alpha(POP_COL[S.pop_kind[l]], 1 - a / 0.5f));
    }

    /* song progress and streak */
    float prog = clampf((T - OFFSET) / (BARS * BEATS_PER_BAR * BEAT), 0, 1);
    mg_rect(eye, 0, 7, TOP_W * prog, 2, -0.05f, rgba_alpha(MG_GOLD, 0.7f));
    if (S.streak >= 3) {
        snprintf(buf, sizeof(buf), "%d lit", S.streak);
        mg_text(eye, buf, TOP_W - 8 - gfx_text_width(buf, 0.5f), 12, 0.5f, -0.1f, MG_GOLD);
    }

    /* banners, on a dark plate so they read over the lanterns */
    float plate = beat < 4 ? 1 : clampf(3 - (T - S.banner_t) / BEAT, 0, 1);
    if (S.finale)
        plate = clampf((T - S.finale_t) / 0.5f, 0, 1);
    if (T - S.resync_t < 1.5f)
        plate = 1;
    if (plate > 0)
        mg_rect(eye, 100, 108, 200, 66, -0.14f, RGBA(24, 14, 22, (int)(150 * plate)));
    if (beat < 4) {
        mg_text_centered(eye, SEC_NAME[0], 200, 112, 0.7f, -0.2f, MG_GOLD);
        mg_text_centered(eye, "Ready...", 200, 136, 0.5f, -0.15f, MG_WHITE);
        for (int k = 0; k < 4; k++)
            mg_circle(eye, 170 + k * 20, 166, 4, -0.15f,
                      k <= (int)floorf(beat) && beat >= 0 ? MG_GOLD : RGBA(255, 255, 255, 60));
    } else if (T - S.banner_t < 3 * BEAT) {
        float a = clampf(3 - (T - S.banner_t) / BEAT, 0, 1);
        mg_text_centered(eye, SEC_NAME[S.banner_sec], 200, 112, 0.7f, -0.2f, rgba_alpha(MG_GOLD, a));
        mg_text_centered(eye, SEC_SUB[S.banner_sec], 200, 136, 0.45f, -0.15f, rgba_alpha(MG_WHITE, a));
    }
    if (S.cheat_on) {
        int left = (int)ceilf((S.cheat_until - T) / BEAT);
        snprintf(buf, sizeof(buf), "Ember's help: %d", left < 0 ? 0 : left);
        mg_text(eye, buf, 8, 12, 0.5f, -0.1f, rgba_alpha(RGBA(255, 220, 130, 255), 0.75f + 0.25f * sinf(T * 6)));
    }
    if (T - S.resync_t < 1.5f)
        mg_text_centered(eye, "The Watch kept the beat", 200, 124, 0.5f, -0.2f, MG_WHITE);
    if (S.finale) {
        float a = clampf((T - S.finale_t) / 0.5f, 0, 1);
        mg_text_centered(eye, S.miss == 0 ? "Every lantern lit" : "The Watch keeps the light", 200, 116, 0.7f,
                         -0.3f, rgba_alpha(MG_GOLD, a));
    }
}

static void draw_bottom(void)
{
    char buf[96];
    float T = S.T;
    int sec = sec_at(T);
    gfx_text(SEC_NAME[sec], 8, 4, 0.5f, MG_GOLD);
    int bar = (int)floorf((T - OFFSET) / (BEAT * BEATS_PER_BAR)) + 1;
    snprintf(buf, sizeof(buf), "Bar %d / %d", bar < 1 ? 1 : (bar > BARS ? BARS : bar), BARS);
    gfx_text(buf, BOT_W - 8 - gfx_text_width(buf, 0.45f), 6, 0.45f, RGBA(200, 190, 220, 255));

    float beat = (T - OFFSET) / BEAT, pulse = beat >= 0 ? powf(1 - (beat - floorf(beat)), 3) : 0;
    for (int l = 0; l < 3; l++) {
        float x = l * 107.0f + 3, cx = x + 50;
        float flash = clampf(1 - (T - S.press_t[l]) / 0.18f, 0, 1);
        gfx_rect(x, 26, 101, 150, rgba_alpha(LANE_COL[l], 0.12f + 0.4f * flash));
        gfx_text(LANE_KEYS[l], cx - gfx_text_width(LANE_KEYS[l], 0.45f) / 2, 30, 0.45f, MG_WHITE);
        gfx_circle(cx, 150, 16 + 2 * pulse, rgba_alpha(LANE_COL[l], 0.4f + 0.3f * pulse));
        gfx_circle(cx, 150, 13, RGBA(28, 20, 36, 255));
        for (int i = 0; i < S.n; i++) {   /* the lanterns coming down this lane */
            const Note *n = &S.notes[i];
            float ahead = n->t - T;
            if (n->lane != l || n->state != N_PENDING || ahead > APPROACH_T || ahead < -GOOD_W)
                continue;
            float k = 1 - ahead / APPROACH_T;
            gfx_circle(cx, 52 + 98 * k, 3 + 8 * k,
                       n->reserved ? RGBA(255, 220, 120, 230) : rgba_alpha(LANE_COL[l], 0.4f + 0.6f * k));
        }
    }

    int judged = S.perfect + S.good + S.miss;
    snprintf(buf, sizeof(buf), "Streak %d   (best %d)", S.streak, S.max_streak);
    gfx_text(buf, 8, 182, 0.45f, MG_WHITE);
    if (judged)
        snprintf(buf, sizeof(buf), "Accuracy %d%%", (int)(accuracy() * 100 + 0.5f));
    else
        snprintf(buf, sizeof(buf), "Accuracy --");
    gfx_text(buf, 8, 200, 0.45f, MG_GOLD);
    snprintf(buf, sizeof(buf), "Perfect %d  Good %d  Dark %d", S.perfect, S.good, S.miss);
    gfx_text(buf, 8, 218, 0.4f, RGBA(200, 190, 220, 255));
}

/* ---- bot: hits most lanterns a little off the beat, calls Ember once ----------- */

static void bot(Input *in, float t)
{
    static bool done[MAX_NOTES], cheated;
    static float last = 1e9f;
    const float dt = 1.0f / 60.0f;
    static const u32 KEYS[3][2] = {{KEY_LEFT_, KEY_Y_}, {KEY_UP_, KEY_X_}, {KEY_RIGHT_, KEY_A_}};
    if (t < last) {
        memset(done, 0, sizeof(done));
        cheated = false;
    }
    last = t;
    if (!cheated && t >= OFFSET + 34 * BEAT) {   /* Ember helps through bar 9's syncopation */
        in->down |= KEY_L_;
        cheated = true;
    }
    for (int i = 0; i < S.n; i++) {
        const Note *n = &S.notes[i];
        if (done[i])
            continue;
        if (n->t - t > 0.5f)
            break;
        if (n->state != N_PENDING || n->reserved) {
            done[i] = true;
            continue;
        }
        u32 h = (u32)(i + 1) * 2654435761u;
        h ^= h >> 15;
        h *= 2246822519u;
        h ^= h >> 13;
        if (h % 100 < 5) {   /* let a few go dark */
            done[i] = true;
            continue;
        }
        float err = (float)((int)((h >> 8) % 81) - 40) / 1000.0f;   /* +/- 40 ms */
        if ((h >> 4) % 100 < 25)
            err *= 2.6f;                                             /* some goods */
        if (t + dt >= n->t + err) {
            done[i] = true;
            if (n->partner < 0 && i % 7 == 3) {
                in->down |= KEY_TOUCH_;
                in->held |= KEY_TOUCH_;
                in->tx = n->lane * 107 + 50;
                in->ty = 100;
            } else {
                in->down |= KEYS[n->lane][i & 1];
            }
        }
    }
}

/* the cheat can't help once the run is wrapping up */
static bool can_cheat(void) { return !S.finale; }

const MiniGame MG_LANTERN = {
    .id = "lantern",
    .title = "Lantern Rhythm",
    .rules = "The Lantern Watch keeps lanterns lit for Aron.\n"
             "Lanterns float out of the attic window along\n"
             "three lanes. Tap a lane as its lantern reaches\n"
             "the glowing ring, right on the beat.\n"
             "On the beat: Perfect. Close: Good. Late: it goes dark.\n"
             "Two lanterns side by side: tap both lanes.\n"
             "Four parts, each busier and worth more.",
    .controls = "Left lane:    Y or D-pad Left\n"
                "Middle lane:  X or D-pad Up\n"
                "Right lane:   A or D-pad Right\n"
                "or touch the left, middle or right\n"
                "third of this screen\n"
                "START: pause",
    .cheat = "Ember's help: she lights the next 8 beats",
    .music = "lantern",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .verdict = verdict,
    .can_cheat = can_cheat,
    .bot = bot,
};
