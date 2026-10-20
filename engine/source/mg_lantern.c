/* Lantern Rhythm: fly a path of light through the night sky, past floating
 * lantern-lit islands, and keep the Lantern Watch's lanterns lit by tapping
 * in time with the music's motif. Lanterns float out from under the band's
 * cloud stage along three lanes and reach the ring on their beat.
 *
 * The band plays along at the far end of the path: two angels (harp,
 * trumpet), an angel choir, Pim on drums and Dross on keys, with Ember
 * conducting at the front of the stage. Hits fire up the band in four
 * stages (swaying, nodding, jumping, ecstatic); a miss knocks them down one
 * stage with a wince, never further.
 *
 * The chart is timed from the moment the music starts (the same moment the
 * framework calls start()) on the game's own clock, so the visual beat holds
 * even if the music is missing or late.
 *
 * Score: weighted accuracy (perfect 1, good 0.6, miss 0; later sections weigh
 * more; stray taps cost a little) * 0.92 + longest streak / notes * 0.08. */

#include "minigame.h"

/* Count the top screen's draw calls per eye: build with -DLAN_DEBUG. */
#ifdef LAN_DEBUG
static int dc;
#define mg_rect(...) (dc++, mg_rect(__VA_ARGS__))
#define mg_circle(...) (dc++, mg_circle(__VA_ARGS__))
#define mg_tri(...) (dc++, mg_tri(__VA_ARGS__))
#define mg_line(...) (dc++, mg_line(__VA_ARGS__))
#define mg_text(...) (dc++, mg_text(__VA_ARGS__))
#define mg_text_centered(...) (dc++, mg_text_centered(__VA_ARGS__))
#define gfx_triangle(...) (dc++, gfx_triangle(__VA_ARGS__))
#endif

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

/* ---- the band's enthusiasm ---------------------------------------------------- */

/* Hits in a row (the band's "hype") needed for each stage. A miss drops the
 * band to the start of the stage below. */
#define STAGES 4
static const int STAGE_AT[STAGES] = {0, 6, 16, 30};
static const char *const STAGE_NAME[STAGES] = {"Swaying", "Nodding along", "Jumping!", "Ecstatic!"};
#define WINCE_T 0.7f             /* seconds the band winces after a miss */

/* ---- view ------------------------------------------------------------------ */

/* The world is seen down a straight path: a point at distance z (the hit
 * line is z = 1) and world offsets (X, Yw) lands on screen at
 * x = 200 + X / z, y = VP_Y + Yw / z. The path itself lies at Yw = PATH_Y. */
#define VP_Y 94.0f               /* y of the vanishing point (s = 0) */
#define HIT_Y 196.0f             /* y of the hit line (s = 1) */
#define PATH_Y (HIT_Y - VP_Y)
#define LANE_SPREAD 100.0f       /* lane spacing at the hit line */
#define Z_FAR 6.0f               /* spawn distance (hit line = 1) */
#define S_FAR (1.0f / Z_FAR)
#define Z_SPEED ((Z_FAR - 1) / APPROACH_T)   /* how fast we fly, in z per second */
#define D_HIT -0.15f             /* stereo depth at the hit line */
#define D_FAR 0.8f               /* stereo depth where lanterns appear */
#define D_NEAR -0.45f            /* nearest anything rushing past gets */
#define D_BAND 0.9f              /* the band's stage, behind the path */
#define EMBER_X 200.0f
#define EMBER_Y 87.0f

/* the band on its cloud stage (feet positions) */
#define FLOOR_Y 93.0f
#define TIER_Y 70.0f
#define HARP_X 40.0f
#define TRUMP_X 98.0f
#define CHOIR_X 163.0f           /* first of three, 37 apart */
#define DROSS_X 302.0f
#define PIM_X 360.0f

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
    /* the band */
    int hype;         /* hits since the last setback */
    int stage;        /* 0..3, see STAGE_AT */
    int stage_dir;    /* +1 after a stage up, -1 after a stage down */
    float stage_t;
    float excite;     /* the stage, eased: drives the animation */
    float band_t[3];  /* last hit per band group (left angels, choir, spirits) */
    float bub_t;      /* speech bubble */
    int bub_who;      /* 0 Pim, 1 Dross */
    const char *bub_msg;
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

static float accuracy(void);

static void start(u32 seed)
{
    memset(&S, 0, sizeof(S));
    gen_chart(seed);
    S.etime = E.time;
    S.last_beat = -1;
    S.cheat_t = S.cheer_t = S.worry_t = S.banner_t = S.resync_t = S.finale_t = -100;
    S.stage_t = S.bub_t = -100;
    for (int l = 0; l < 3; l++)
        S.press_t[l] = S.pop_t[l] = S.band_t[l] = -100;
}

static int sec_at(float T)
{
    int bar = (int)floorf((T - OFFSET) / (BEAT * BEATS_PER_BAR));
    return bar < 0 ? 0 : (bar / 4 >= SECTIONS ? SECTIONS - 1 : bar / 4);
}

/* Pim (0) or Dross (1) pipes up in a speech bubble. */
static void say(int who, const char *msg)
{
    S.bub_who = who;
    S.bub_msg = msg;
    S.bub_t = S.T;
}

/* Every hit warms the band up; enough in a row lifts them a stage. */
static void band_up(void)
{
    static const char *const UP[STAGES] = {"", "Ooh, a groove!", "...Fine. It's fun.", "WOOOO!"};
    static const float UP_RATE[STAGES] = {1.0f, 1.0f, 1.122462f, 1.259921f};
    S.hype++;
    int st = S.stage;
    while (st + 1 < STAGES && S.hype >= STAGE_AT[st + 1])
        st++;
    if (st > S.stage) {
        S.stage = st;
        S.stage_dir = 1;
        S.stage_t = S.T;
        mg_sfx_pitch("lantern_stage_up", UP_RATE[st]);
        if (st == STAGES - 1)
            mg_sfx("lantern_band_cheer");
        say(st == 2 ? 1 : 0, UP[st]);
    }
}

/* A miss: the band winces and drops one stage, never more. */
static void band_down(void)
{
    static const char *const OOPS[3] = {"Oops! Again!", "Eh. Keep going.", "Whoa, close one!"};
    if (S.T - S.worry_t < 0.25f)
        return;   /* one stumble per moment, chords included */
    if (S.stage > 0) {
        S.stage--;
        S.stage_dir = -1;
        S.stage_t = S.T;
        mg_sfx("lantern_band_gasp");
        int k = S.miss % 3;
        say(k == 1 ? 1 : 0, OOPS[k]);
    }
    S.hype = STAGE_AT[S.stage];
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
    S.band_t[n->lane] = S.T;
    if (S.streak % STREAK_STEP == 0) {
        mg_sfx("lantern_streak");
        S.cheer_t = S.T;
    }
    band_up();
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
    band_down();
    S.worry_t = S.T;
#ifdef LAN_DEBUG
    printf("lantern: miss at %.2f s, band stage %d\n", S.T, S.stage);
#endif
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
    /* a floating island rushes past on beat 3 of every bar (see draw_islands) */
    if (b % 4 == 2 && !S.finale)
        mg_sfx_pitch("lantern_whoosh_past", (b / 4) & 1 ? 1.06f : 0.94f);
}

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
        say(0, "Go, Ember!");
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
        if (accuracy() >= 0.75f) {
            mg_sfx("lantern_band_cheer");
            say(0, "Bravo!!");
        } else {
            say(1, "Not bad. Again?");
        }
    }

    /* the band eases into its stage; for the finale they all celebrate */
    float target = (float)S.stage;
    if (S.finale)
        target = fmaxf(target, accuracy() >= 0.75f ? 3.0f : 2.0f);
    float rate = target > S.excite ? 2.5f : 4.0f;
    S.excite += (target - S.excite) * clampf(dt * rate, 0, 1);

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
    const char *line = s >= 90 ? "The band wants an encore." :
                       s >= 70 ? "Ember is beaming." :
                       s >= 45 ? "Ember relit the rest." : "Ember keeps one lit anyway.";
    snprintf(buf, sizeof(buf), "%d perfect, %d good, %d dark. %s", S.perfect, S.good, S.miss, line);
    return buf;
}

/* ---- drawing: helpers ------------------------------------------------------------ */

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

static float frac(float x) { return x - floorf(x); }

/* A fixed pseudo-random number in 0..1 for scenery item i, property k. */
static float hashf(int i, int k)
{
    u32 h = (u32)i * 73856093u ^ (u32)k * 19349663u ^ 0x9E3779B9u;
    h ^= h >> 15;
    h *= 2246822519u;
    h ^= h >> 13;
    h *= 3266489917u;
    h ^= h >> 16;
    return (float)(h & 0xFFFFFF) / 16777216.0f;
}

static float s_y(float s) { return VP_Y + PATH_Y * s; }
static float s_x(float X, float s) { return 200 + X * s; }
static float s_depth(float s)
{
    return clampf(D_FAR + (D_HIT - D_FAR) * (s - S_FAR) / (1 - S_FAR), D_NEAR, 1.0f);
}
/* Distance of something that reaches the hit line at time `te`. */
static float z_at(float te) { return 1 + (te - S.T) * Z_SPEED; }
/* Perspective scale of a lantern due `ahead` seconds from now. */
static float ahead_s(float ahead)
{
    float z = 1 + ahead * Z_SPEED;
    return 1 / (z < 0.75f ? 0.75f : z);
}

/* A strip of the path plane between a far row (s = a) and a near row (b).
 * Each row gets its own stereo shift, so the path slopes smoothly out of
 * the screen instead of stepping. */
static void plane_quad(int eye, float X0, float X1, float a, float b, u32 c)
{
    float sa = mg_shift(eye, s_depth(a)), sb = mg_shift(eye, s_depth(b));
    float ya = s_y(a), yb = s_y(b);
    gfx_triangle(s_x(X0, a) + sa, ya, s_x(X1, a) + sa, ya, s_x(X1, b) + sb, yb, c);
    gfx_triangle(s_x(X0, a) + sa, ya, s_x(X1, b) + sb, yb, s_x(X0, b) + sb, yb, c);
}

/* Everything the band's animation needs this frame, read from S. */
typedef struct {
    float beat, ph, pulse;   /* beats since bar 1; phase in the beat; 1 on the beat, fading */
    float w1, w2, w3;        /* how much they nod, jump, go wild (0..1 each) */
    float wince, wt;         /* after a miss: 1 fading to 0; seconds since */
    float acc[3];            /* your hits per group: left angels, choir, spirits */
    float up;                /* stage-up flash, 1 fading to 0 */
} Vibe;

static void get_vibe(Vibe *v)
{
    v->beat = (S.T - OFFSET) / BEAT;
    v->ph = v->beat >= 0 ? frac(v->beat) : 0;
    v->pulse = v->beat >= 0 ? powf(1 - v->ph, 3) : 0;
    v->w1 = clampf(S.excite, 0, 1);
    v->w2 = clampf(S.excite - 1, 0, 1);
    v->w3 = clampf(S.excite - 2, 0, 1);
    v->wt = S.T - S.worry_t;
    v->wince = clampf(1 - v->wt / WINCE_T, 0, 1);
    for (int g = 0; g < 3; g++)
        v->acc[g] = clampf(1 - (S.T - S.band_t[g]) / 0.35f, 0, 1);
    v->up = S.stage_dir > 0 ? clampf(1 - (S.T - S.stage_t) / 0.8f, 0, 1) : 0;
}

/* A band member's motion: a calm sway, a nod on the beat, hops between
 * beats (landing on them), and a little stumble after a miss. `off` (in
 * beats) staggers members so they don't move as one block. */
static void member_move(const Vibe *v, float off, float *dx, float *dy, float *nod)
{
    float b = v->beat + off, ph = frac(b);
    float hop = 4 * ph * (1 - ph);
    *dx = 2.2f * sinf(b * 1.5708f) * (1 - 0.7f * v->w2) + 2.5f * v->wince * sinf(v->wt * 22);
    *dy = 1.2f * v->w1 * powf(1 - ph, 3) - v->w2 * (4 + 4 * v->w3) * hop + 3 * v->wince;
    *nod = 2.5f * v->w1 * powf(1 - ph, 2) + 1.5f * v->wince;
}

/* Wing flaps: slow and lazy when calm, two quick beats per beat when the
 * band jumps; drooping in a wince. */
static float flap_of(const Vibe *v, float off)
{
    float b = v->beat + off;
    float calm = 1.5f + 1.5f * sinf(b * 1.5708f);
    float fast = 3 + 6 * sinf(frac(b) * 12.566f);
    return lerpf(calm, fast, v->w2) - 5 * v->wince;
}

static void eyes(int eye, float x, float y, float dx, float r, float d, u32 ink, const Vibe *v, bool happy)
{
    if (v->wince > 0.25f) {   /* squeezed shut: > < */
        mg_line(eye, x - dx - r, y - r, x - dx + r, y, 1, d, ink);
        mg_line(eye, x + dx + r, y - r, x + dx - r, y, 1, d, ink);
    } else if (happy) {       /* ^ ^ */
        for (int side = -1; side <= 1; side += 2) {
            float ex = x + side * dx;
            mg_line(eye, ex - r, y + 0.4f * r, ex, y - 0.7f * r, 1, d, ink);
            mg_line(eye, ex, y - 0.7f * r, ex + r, y + 0.4f * r, 1, d, ink);
        }
    } else {
        mg_circle(eye, x - dx, y, r * 0.75f, d, ink);
        mg_circle(eye, x + dx, y, r * 0.75f, d, ink);
    }
}

/* ---- drawing: the sky and the journey ----------------------------------------------- */

static void draw_sky(int eye)
{
    mg_sky(eye, RGBA(10, 12, 38, 255), RGBA(46, 30, 72, 255));
    mg_circle(eye, 200, 96, 170, 1.0f, RGBA(110, 80, 190, 26));   /* the nebula the path heads into */
    for (int i = 0; i < 22; i++) {
        float x = hashf(i, 1) * TOP_W, y = hashf(i, 2) * 236;
        float tw = 0.5f + 0.5f * sinf(S.T * (1.1f + hashf(i, 3)) + i * 2.0f);
        float sz = hashf(i, 4) < 0.25f ? 2.0f : 1.3f;
        mg_rect(eye, x, y, sz, sz, 1.0f, rgba_alpha(MG_WHITE, 0.25f + 0.55f * tw));
    }
}

/* Motes of light streaming past on all sides: the feeling of flying. */
static void draw_motes(int eye)
{
    const float span = 11;
    for (int i = 0; i < 20; i++) {
        float side = hashf(i, 5) < 0.5f ? -1.0f : 1.0f;
        float X = side * (190 + 280 * hashf(i, 6)), Yw = -40 + 230 * hashf(i, 7);
        float u = hashf(i, 8) * span - S.T * Z_SPEED;
        u -= span * floorf(u / span);
        float z = 0.55f + u, s = 1 / z, s2 = 1 / (z + 0.6f);
        float x1 = 200 + X * s, y1 = VP_Y + Yw * s;
        if (x1 < -10 || x1 > TOP_W + 10 || y1 < -10 || y1 > TOP_H + 10)
            continue;
        float a = clampf((span + 0.55f - z) / 3, 0, 1) * 0.55f;
        mg_line(eye, 200 + X * s2, VP_Y + Yw * s2, x1, y1, 0.8f + 1.6f * s, s_depth(s),
                rgba_alpha(RGBA(225, 220, 255, 255), a));
    }
}

/* Floating lantern-lit islands: a big one passes the camera on beat 3 of
 * every bar, alternating sides (on_beat() plays its whoosh), and a small
 * one further out on beat 1. */
static void draw_islands(int eye, const Vibe *v)
{
    for (int j = 41; j >= 0; j--) {
        int k = j >> 1;
        bool big = j & 1;
        float z = z_at(OFFSET + (4 * k + (big ? 2 : 0)) * BEAT);
        if (z < 0.5f || z > 13)
            continue;
        float s = 1 / z, side = ((k + !big) & 1) ? 1.0f : -1.0f;
        bool low = ((k >> 1) & 1) ^ !big;
        float X = side * (big ? (low ? 300 : 262) : (low ? 340 : 300)), Yw = big ? (low ? 150 : 72) : (low ? 175 : 30);
        float x = 200 + X * s, y = VP_Y + Yw * s, w = (big ? 44 : 26) * s, d = s_depth(s);
        if (x + w < -5 || x - w > TOP_W + 5 || y - w > TOP_H)
            continue;
        float a = clampf((13 - z) / 3, 0, 1);
        float tip = x + 0.2f * w * side;
        mg_tri(eye, x - w, y, x + w, y, tip, y + 1.25f * w, d, rgba_alpha(RGBA(78, 62, 112, 255), a));
        mg_tri(eye, x - 0.1f * w * side, y, x + w * side, y, tip, y + 1.25f * w, d - 0.003f,
               rgba_alpha(RGBA(56, 44, 86, 255), a));
        mg_rect(eye, x - w, y - 0.2f * w, 2 * w, 0.24f * w, d - 0.005f, rgba_alpha(RGBA(84, 150, 138, 255), a));
        float tx = x + side * 0.4f * w;   /* a little tree */
        mg_tri(eye, tx - 0.17f * w, y - 0.18f * w, tx + 0.17f * w, y - 0.18f * w, tx, y - 0.75f * w, d - 0.006f,
               rgba_alpha(RGBA(40, 96, 96, 255), a));
        float px = x - side * 0.4f * w, py = y - 1.0f * w;   /* and its lantern on a post */
        mg_line(eye, px, y - 0.2f * w, px, py, fmaxf(1, 2.5f * s), d - 0.006f, rgba_alpha(RGBA(70, 45, 40, 255), a));
        mg_circle(eye, px, py + 0.05f * w, 0.5f * w, d - 0.004f,
                  rgba_alpha(RGBA(255, 170, 70, 255), a * (0.18f + 0.1f * v->pulse)));
        mg_rect(eye, px - 0.1f * w, py - 0.08f * w, 0.2f * w, 0.26f * w, d - 0.008f,
                rgba_alpha(RGBA(255, 196, 120, 255), a));
    }
}

/* The path of light: three lanes sloping out of the screen, with a rung on
 * every beat and lamps at its edges rushing toward you. */
static void draw_path(int eye, const Vibe *v)
{
    static const float ROW[5] = {0.07f, 0.25f, 0.55f, 1.0f, 1.45f};
    static const float ROW_A[4] = {0.05f, 0.1f, 0.16f, 0.2f};
    float T = S.T;
    for (int l = 0; l < 3; l++) {
        float flash = clampf(1 - (T - S.press_t[l]) / 0.18f, 0, 1);
        float X0 = (l - 1) * LANE_SPREAD - 46, X1 = X0 + 92;
        for (int k = 0; k < 4; k++)
            plane_quad(eye, X0, X1, ROW[k], ROW[k + 1],
                       rgba_alpha(LANE_COL[l], ROW_A[k] + (k ? 0.28f * flash : 0)));
    }
    for (int e = 0; e < 4; e++) {
        float X = -150.0f + e * 100;
        bool edge = e == 0 || e == 3;
        float hw = edge ? 3.0f : 1.2f;
        plane_quad(eye, X - hw, X + hw, 0.07f, 0.6f, RGBA(255, 225, 170, edge ? 90 : 45));
        plane_quad(eye, X - hw, X + hw, 0.6f, 1.45f, RGBA(255, 225, 170, edge ? 150 : 70));
    }

    int b0 = (int)floorf((T - OFFSET) / BEAT) - 1;
    for (int b = b0 + 7; b >= b0; b--) {
        float z = z_at(OFFSET + b * BEAT);
        if (z < 0.72f || z > Z_FAR + 1.2f)
            continue;
        float s = 1 / z, y = s_y(s), d = s_depth(s);
        float a = clampf((Z_FAR + 1.2f - z) / 1.5f, 0, 1);
        bool bar = (b & 3) == 0;
        mg_line(eye, s_x(-150, s), y, s_x(150, s), y, (bar ? 2.4f : 1.2f) * 1.3f * s + 0.3f, d,
                rgba_alpha(bar ? RGBA(255, 228, 160, 255) : RGBA(220, 205, 255, 255), a * (bar ? 0.55f : 0.3f)));
        for (int side = -1; side <= 1; side += 2) {
            float px = s_x(side * 168.0f, s), py = y - 10 * s;
            mg_circle(eye, px, py, 8 * s, d + 0.01f, rgba_alpha(RGBA(255, 190, 110, 255), 0.25f * a));
            mg_circle(eye, px, py, 3 * s, d, rgba_alpha(RGBA(255, 240, 200, 255), a));
        }
    }

    /* hit targets, pulsing with the beat */
    for (int l = 0; l < 3; l++) {
        float x = s_x((l - 1) * LANE_SPREAD, 1), flash = clampf(1 - (T - S.press_t[l]) / 0.18f, 0, 1);
        mg_circle(eye, x, HIT_Y, 20 + 2 * v->pulse, D_HIT + 0.02f,
                  rgba_alpha(LANE_COL[l], 0.35f + 0.35f * v->pulse + 0.3f * flash));
        mg_circle(eye, x, HIT_Y, 17, D_HIT + 0.01f, RGBA(28, 18, 34, 210));
        if (flash > 0)
            mg_circle(eye, x, HIT_Y, 17 * flash, D_HIT, rgba_alpha(LANE_COL[l], 0.5f * flash));
        mg_circle(eye, x, HIT_Y, 3, D_HIT, rgba_alpha(LANE_COL[l], 0.8f));
    }
}

/* ---- drawing: the band ------------------------------------------------------------- */

#define PIM_COL RGBA(150, 200, 255, 255)
#define DROSS_COL RGBA(170, 240, 190, 255)
#define GOLD_TRIM RGBA(255, 205, 90, 255)

static void draw_stage(int eye, const Vibe *v)
{
    float d = D_BAND + 0.03f;
    u32 c1 = RGBA(146, 130, 204, 255), c2 = RGBA(212, 202, 246, 255);
    /* warm stage light, brighter as the band gets going */
    mg_circle(eye, 200, 70, 110 + 20 * v->w3, 0.98f,
              rgba_alpha(RGBA(255, 180, 140, 255), 0.07f + 0.07f * v->w1 + 0.1f * v->w3 * v->pulse));
    if (v->up > 0)
        mg_circle(eye, 200, 66, 40 + 190 * (1 - v->up), 0.96f, rgba_alpha(RGBA(255, 225, 140, 255), 0.25f * v->up));
    /* light beams sweeping the sky when the band goes wild */
    if (v->w3 > 0.02f) {
        static const float BX[4] = {60, 150, 250, 340};
        for (int i = 0; i < 4; i++) {
            float a = 0.45f * sinf(S.T * 0.9f + i * 1.9f) + (i < 2 ? -0.25f : 0.25f);
            float ca = cosf(a), sa = sinf(a), tx = BX[i] + sa * 260, ty = FLOOR_Y - ca * 260;
            mg_tri(eye, BX[i], FLOOR_Y, tx - ca * 22, ty - sa * 22, tx + ca * 22, ty + sa * 22, 0.97f,
                   rgba_alpha(i & 1 ? RGBA(255, 160, 210, 255) : RGBA(255, 220, 140, 255),
                              0.13f * v->w3 * (0.7f + 0.3f * v->pulse)));
        }
    }
    /* the side floors and the choir's raised tier */
    static const float PX[6] = {16, 58, 100, 300, 342, 384};
    for (int i = 0; i < 6; i++)
        mg_circle(eye, PX[i], FLOOR_Y + 5, 17 - 3 * (i == 2 || i == 3), d, c1);
    for (int side = 0; side < 2; side++) {
        float x0 = side ? 284 : -4, w = 120;
        mg_rect(eye, x0, FLOOR_Y - 1, w, 6, d - 0.005f, c2);
        mg_circle(eye, side ? x0 : x0 + w, FLOOR_Y + 2, 3, d - 0.005f, c2);
    }
    for (int i = 0; i < 3; i++)
        mg_circle(eye, CHOIR_X + 37 * i, TIER_Y + 5, 14, d + 0.01f, c1);
    mg_rect(eye, CHOIR_X - 16, TIER_Y - 1, 106, 5, d, c2);
}

/* An angel in the game's style: white wings with a gold edge, a white robe
 * with a gold hem, pale gold hair and a floating golden halo that glows when
 * the band goes wild. Feet at (x, y). mouth < 0: none (the trumpet's there). */
static void draw_angel(int eye, float x, float y, float sc, float d, float flap, float nod, float mouth,
                       const Vibe *v, bool happy)
{
    u32 wing = RGBA(246, 246, 255, 255), wing2 = RGBA(212, 216, 240, 255), gold = GOLD_TRIM;
    float wy = y - 20 * sc;
    for (int side = -1; side <= 1; side += 2) {
        float tipx = x + side * 17 * sc, tipy = wy - 9 * sc - flap * sc;
        mg_tri(eye, x + side * 2 * sc, wy, tipx, tipy, x + side * 13 * sc, wy + 8 * sc, d + 0.01f, wing);
        mg_tri(eye, x + side * 2 * sc, wy + 3 * sc, x + side * 13 * sc, wy + 8 * sc, x + side * 7 * sc,
               wy + 14 * sc - 0.4f * flap * sc, d + 0.01f, wing2);
        mg_line(eye, x + side * 2 * sc, wy, tipx, tipy, 1.2f, d + 0.005f, gold);
    }
    mg_tri(eye, x, wy - 5 * sc, x - 8 * sc, y, x + 8 * sc, y, d, RGBA(250, 250, 255, 255));
    mg_line(eye, x - 7.5f * sc, y - 1 * sc, x + 7.5f * sc, y - 1 * sc, 1.5f * sc, d - 0.005f, gold);
    float hy = y - 28 * sc + nod;
    mg_circle(eye, x, hy - 1.2f * sc, 6.3f * sc, d - 0.005f, RGBA(250, 226, 150, 255));
    mg_circle(eye, x, hy + 0.8f * sc, 5.3f * sc, d - 0.01f, RGBA(255, 233, 210, 255));
    u32 ink = RGBA(60, 50, 80, 255);
    eyes(eye, x, hy + 0.4f * sc, 2.1f * sc, 1.3f * sc, d - 0.015f, ink, v, happy);
    if (mouth > 0.15f)
        mg_circle(eye, x, hy + 3.4f * sc, (0.7f + 1.5f * mouth) * sc, d - 0.015f, RGBA(170, 70, 90, 255));
    else if (mouth >= 0)
        mg_line(eye, x - 1.3f * sc, hy + 3.3f * sc, x + 1.3f * sc, hy + 3.3f * sc, 1, d - 0.015f, RGBA(170, 90, 100, 255));
    if (happy) {
        mg_circle(eye, x - 3.7f * sc, hy + 2.4f * sc, 1.3f * sc, d - 0.012f, RGBA(255, 150, 170, 140));
        mg_circle(eye, x + 3.7f * sc, hy + 2.4f * sc, 1.3f * sc, d - 0.012f, RGBA(255, 150, 170, 140));
    }
    /* halo */
    /* glowing: brighter, thicker and a little bigger, with a twinkle */
    float glow = clampf(v->w3 * (0.55f + 0.45f * v->pulse) + 0.6f * v->up, 0, 1);
    float yy = hy - 9.5f * sc, hw = (5 + 1.5f * glow) * sc, hh = (1.7f + 0.5f * glow) * sc, th = 1.3f + 0.9f * glow;
    u32 halo = mix(gold, RGBA(255, 252, 225, 255), glow);
    mg_line(eye, x - hw, yy, x, yy - hh, th, d - 0.02f, halo);
    mg_line(eye, x, yy - hh, x + hw, yy, th, d - 0.02f, halo);
    mg_line(eye, x - hw, yy, x, yy + hh, th, d - 0.02f, halo);
    mg_line(eye, x, yy + hh, x + hw, yy, th, d - 0.02f, halo);
    if (glow > 0.3f) {
        float tw = (glow - 0.3f) * (2 + 2 * v->pulse) * sc, tx = x + hw, ty = yy - hh;
        u32 sp = rgba_alpha(RGBA(255, 255, 235, 255), glow);
        mg_line(eye, tx - tw, ty, tx + tw, ty, 1, d - 0.025f, sp);
        mg_line(eye, tx, ty - tw, tx, ty + tw, 1, d - 0.025f, sp);
    }
}

static void draw_harpist(int eye, const Vibe *v)
{
    float dx, dy, nod;
    member_move(v, 0, &dx, &dy, &nod);
    float x = HARP_X + dx, y = FLOOR_Y + dy, d = D_BAND;
    bool happy = v->w3 > 0.5f;
    draw_angel(eye, x, y, 1, d, flap_of(v, 0), nod, 0.2f * v->w2 + (happy ? 0.4f : 0), v, happy);
    /* the harp at her side: a gold frame, three strings that shimmer on your
     * left-lane hits */
    u32 gold = GOLD_TRIM;
    float hx = x + 11, top = y - 30, bot = y - 3, acc = v->acc[0];
    mg_line(eye, hx, bot, hx + 2, top, 2, d - 0.02f, gold);
    mg_line(eye, hx + 2, top, hx + 12, top + 9, 2, d - 0.02f, gold);
    mg_line(eye, hx + 12, top + 9, hx, bot, 1.6f, d - 0.02f, gold);
    for (int k = 0; k < 3; k++) {
        float f = 0.3f + 0.25f * k, sx = hx + 2 + 10 * f, sy = top + 9 * f;
        float u = (hx + 12 - sx) / 12, by = top + 9 + u * (bot - top - 9);
        float vib = acc * 1.2f * sinf(S.T * 70 + k * 2.1f);
        mg_line(eye, sx, sy, sx + vib, by, 0.8f, d - 0.025f, RGBA(255, 250, 230, (int)(150 + 100 * acc)));
    }
    float pluck = 2 * sinf(v->beat * 6.283f);
    mg_line(eye, x + 3, y - 19, hx + 5, y - 15 + pluck, 2, d - 0.03f, RGBA(250, 250, 255, 255));
}

static void draw_trumpeter(int eye, const Vibe *v)
{
    float dx, dy, nod;
    member_move(v, 0.03f, &dx, &dy, &nod);
    float x = TRUMP_X + dx, y = FLOOR_Y + dy, d = D_BAND;
    bool happy = v->w3 > 0.5f;
    draw_angel(eye, x, y, 1, d, flap_of(v, 0.03f), nod, -1, v, happy);
    /* the trumpet: lifted on your left-lane hits, skyward when the band's wild */
    float lift = clampf(0.15f + 0.35f * v->acc[0] + 0.5f * v->w3 - 0.4f * v->wince, -0.3f, 1);
    float ang = -0.6f * lift, ca = cosf(ang), sa = sinf(ang);
    float mx = x + 2.5f, my = y - 28 + nod + 3.3f, ex = mx + ca * 17, ey = my + sa * 17;
    u32 gold = GOLD_TRIM;
    mg_line(eye, mx, my, ex, ey, 2.2f, d - 0.02f, gold);
    mg_tri(eye, ex - ca * 3, ey - sa * 3, ex + ca * 1.5f - sa * 4.5f, ey + sa * 1.5f + ca * 4.5f,
           ex + ca * 1.5f + sa * 4.5f, ey + sa * 1.5f - ca * 4.5f, d - 0.02f, gold);
    mg_rect(eye, mx + ca * 7 - 1.5f, my + sa * 7 - 3.5f, 3, 3, d - 0.025f, RGBA(230, 175, 70, 255));
    mg_line(eye, x + 3, y - 19, mx + ca * 8, my + sa * 8 + 1.5f, 2, d - 0.03f, RGBA(250, 250, 255, 255));
    float blast = fmaxf(v->acc[0], 0.5f * v->w3 * v->pulse);
    if (blast > 0.02f)
        mg_circle(eye, ex + ca * 5, ey + sa * 5, 3 + 7 * (1 - blast), d - 0.035f,
                  rgba_alpha(RGBA(255, 240, 180, 255), 0.6f * blast));
}

/* Three angels singing, mouths wide on the beat and on your middle-lane hits. */
static void draw_choir(int eye, const Vibe *v)
{
    bool happy = v->w3 > 0.5f;
    for (int i = 0; i < 3; i++) {
        float dx, dy, nod;
        member_move(v, 0.04f * (i - 1), &dx, &dy, &nod);
        float x = CHOIR_X + 37 * i + dx, y = TIER_Y + dy, d = D_BAND + 0.01f;
        float mouth = clampf(0.3f + 0.3f * v->pulse * (0.5f + v->w1) + 0.6f * v->acc[1] + 0.3f * v->w2 - 0.5f * v->wince,
                             0, 1.2f);
        draw_angel(eye, x, y, 0.85f, d, flap_of(v, 0.1f * i), nod, mouth, v, happy);
        if (v->w2 > 0.3f) {   /* arms up, waving */
            float up = (v->w2 - 0.3f) / 0.7f;
            for (int side = -1; side <= 1; side += 2)
                mg_line(eye, x + side * 3, y - 17, x + side * 8, y - 17 - 9 * up * (0.7f + 0.3f * sinf(S.T * 8 + i + side)),
                        1.8f, d - 0.03f, RGBA(250, 250, 255, 255));
        }
    }
}

/* A Purgatorium spirit: a translucent blob with a wavy tail. */
static void draw_spirit(int eye, float x, float y, float d, u32 col, const Vibe *v, bool dross, float mouth)
{
    float wob = sinf(S.T * 5 + x);
    bool happy = v->w2 > 0.5f;
    mg_circle(eye, x, y + 2, 15, d + 0.01f, rgba_alpha(col, 0.16f + 0.12f * v->w3));
    u32 body = rgba_alpha(col, 0.88f);
    mg_tri(eye, x - 10, y + 1, x + 2, y + 1, x - 6 + 2 * wob, y + 16, d, body);
    mg_tri(eye, x - 2, y + 1, x + 10, y + 1, x + 6 - 2 * wob, y + 15, d, body);
    mg_circle(eye, x, y, 10, d, body);
    mg_circle(eye, x - 3.5f, y - 4, 3, d - 0.005f, RGBA(255, 255, 255, 90));   /* sheen */
    u32 ink = RGBA(30, 30, 50, 255);
    eyes(eye, x, y - 1, 3.6f, 1.8f, d - 0.01f, ink, v, happy);
    if (dross && !happy && v->wince < 0.25f) {   /* Dross's resting grump, gone once he's having fun */
        float g = 1 - v->w1 * 0.5f;
        mg_line(eye, x - 6, y - 5 - g, x - 2, y - 4, 1, d - 0.01f, ink);
        mg_line(eye, x + 6, y - 5 - g, x + 2, y - 4, 1, d - 0.01f, ink);
    }
    if (mouth > 0.25f)
        mg_circle(eye, x, y + 4, 1 + 2 * mouth, d - 0.01f, RGBA(110, 50, 80, 255));
    else
        mg_line(eye, x - 2, y + 4, x + 2, y + 4 - (dross ? 0 : 0.6f), 1, d - 0.01f, ink);
    if (happy) {
        mg_circle(eye, x - 6, y + 2, 1.8f, d - 0.008f, RGBA(255, 140, 170, 140));
        mg_circle(eye, x + 6, y + 2, 1.8f, d - 0.008f, RGBA(255, 140, 170, 140));
    }
}

static float bubble_on(int who)
{
    float a = S.T - S.bub_t;
    return S.bub_msg && S.bub_who == who && a >= 0 && a < 1.6f ? 1.0f : 0.0f;
}

/* Dross on keys: a chord lights up on your right-lane hits. */
static void draw_dross(int eye, const Vibe *v)
{
    float dx, dy, nod;
    member_move(v, 0.06f, &dx, &dy, &nod);
    float x = DROSS_X + 0.6f * dx, y = FLOOR_Y - 21 + dy, d = D_BAND;
    float talk = bubble_on(1) * (0.5f + 0.5f * sinf(S.T * 18));
    draw_spirit(eye, x, y, d, DROSS_COL, v, true, fmaxf(0.7f * v->w3 + 0.4f * v->acc[2], talk));
    float ky = 81, kx = DROSS_X - 15;
    u32 stand = RGBA(60, 46, 90, 255);
    mg_line(eye, DROSS_X - 10, ky + 5, DROSS_X - 7, FLOOR_Y + 1, 1.5f, d - 0.02f, stand);
    mg_line(eye, DROSS_X + 10, ky + 5, DROSS_X + 7, FLOOR_Y + 1, 1.5f, d - 0.02f, stand);
    mg_rect(eye, kx - 1.5f, ky, 33, 6, d - 0.025f, stand);
    mg_rect(eye, kx, ky + 1, 30, 3.5f, d - 0.03f, RGBA(240, 240, 250, 255));
    int key = (int)floorf(v->beat * (v->w2 > 0.5f ? 2 : 1)) % 3 * 2 + ((int)floorf(v->beat / 2) & 1);
    u32 lit = mix(DROSS_COL, MG_WHITE, 0.2f);
    mg_rect(eye, kx + key * 5, ky + 1, 5, 3.5f, d - 0.035f, rgba_alpha(lit, 0.8f));
    if (v->acc[2] > 0)
        mg_rect(eye, kx + 2, ky + 0.5f, 26, 4.5f, d - 0.035f, rgba_alpha(RGBA(255, 240, 170, 255), 0.6f * v->acc[2]));
    float bounce = 1.5f * (1 - v->pulse);
    mg_line(eye, x - 7, y + 3, kx + key * 5 + 2.5f, ky - bounce, 2, d - 0.04f, rgba_alpha(DROSS_COL, 0.9f));
    mg_line(eye, x + 7, y + 3, kx + 24, ky - 1.5f + bounce, 2, d - 0.04f, rgba_alpha(DROSS_COL, 0.9f));
}

/* Pim on drums: sticks alternate on the beats (eighths once the band
 * jumps); the cymbal crashes on your right-lane hits. */
static void draw_pim(int eye, const Vibe *v)
{
    float dx, dy, nod;
    member_move(v, 0.0f, &dx, &dy, &nod);
    float x = PIM_X + 0.6f * dx, y = FLOOR_Y - 23 + dy, d = D_BAND;
    float talk = bubble_on(0) * (0.5f + 0.5f * sinf(S.T * 18));
    draw_spirit(eye, x, y, d, PIM_COL, v, false, fmaxf(0.3f * v->w1 + 0.5f * v->w3 * v->pulse + 0.4f * v->acc[2], talk));
    u32 shell = RGBA(70, 110, 200, 255), head = RGBA(235, 240, 255, 255), gold = GOLD_TRIM;
    /* bass drum, thumping on the beat */
    mg_circle(eye, PIM_X, FLOOR_Y - 6, 7.5f, d - 0.02f, shell);
    mg_circle(eye, PIM_X, FLOOR_Y - 6, 5.5f, d - 0.025f, mix(head, gold, 0.6f * v->pulse));
    /* tom and cymbal */
    float tx = PIM_X - 16, ty = FLOOR_Y - 14;
    mg_rect(eye, tx - 6, ty, 12, 5, d - 0.02f, shell);
    mg_rect(eye, tx - 6, ty, 12, 1.8f, d - 0.025f, head);
    float cx = PIM_X + 16, cy = FLOOR_Y - 24;
    float crash = fmaxf(v->acc[2], v->w2 * ((((int)floorf(v->beat)) & 3) == 0 ? v->pulse : 0));
    float tilt = 1.5f + 2.5f * crash * sinf(S.T * 40);
    mg_line(eye, cx, cy, cx, FLOOR_Y, 1, d - 0.02f, RGBA(90, 80, 120, 255));
    mg_line(eye, cx - 7, cy + tilt, cx + 7, cy - tilt, 2, d - 0.025f, mix(gold, MG_WHITE, 0.5f * crash));
    /* sticks */
    float per = v->w2 > 0.5f ? 1.0f : 2.0f;
    float hl = 8 * sinf(3.14159f * frac(v->beat / per)), hr = 8 * sinf(3.14159f * frac(v->beat / per + 0.5f));
    u32 stick = RGBA(250, 230, 190, 255);
    mg_line(eye, x - 6, y + 4, tx, ty - hl, 1.4f, d - 0.03f, stick);
    mg_line(eye, x + 6, y + 4, cx - 2, cy - 1 - hr, 1.4f, d - 0.03f, stick);
}

/* Ember, conducting at the front of the stage in 4/4 (down, in, out, up),
 * brighter with the band's mood, golden while she helps. */
static void draw_ember(int eye, const Vibe *v)
{
    static const float PX[4] = {0, -1, 1, 0.2f}, PY[4] = {1, 0.2f, 0.2f, -1};
    float T = S.T;
    bool help = S.cheat_on;
    float bright = (help || S.finale) ? 1 : 0.55f + 0.15f * S.excite;
    bright *= 1 - 0.3f * v->wince;
    float bob = 1.5f * sinf(T * 2.4f) - v->w2 * 3 * 4 * v->ph * (1 - v->ph);
    float ex = EMBER_X + (help ? 2 * sinf(T * 3) : 0), ey = EMBER_Y + bob, d = D_BAND - 0.06f;
    u32 glow = help ? RGBA(255, 215, 120, 255) : RGBA(255, 160, 80, 255);
    mg_circle(eye, ex, ey + 2, 18 + 8 * bright + 4 * v->pulse, d + 0.02f, rgba_alpha(glow, 0.16f * bright));
    u32 body = mix(RGBA(200, 120, 80, 255), help ? RGBA(255, 210, 120, 255) : RGBA(255, 180, 110, 255), bright);
    mg_tri(eye, ex - 8, ey + 1, ex + 8, ey + 1, ex + 3 * sinf(T * 5), ey + 15, d, body);
    mg_circle(eye, ex, ey, 8, d, body);
    eyes(eye, ex, ey - 1, 2.8f, 1.4f, d - 0.01f, RGBA(70, 40, 30, 255), v, v->w3 > 0.5f || help);
    float cheer = clampf(1 - (T - S.cheer_t) / 0.9f, 0, 1);
    mg_circle(eye, ex, ey + 3, 0.9f + 0.9f * fmaxf(cheer, v->w3 * v->pulse), d - 0.01f, RGBA(150, 60, 40, 255));
    /* the baton lands on each beat's point of the pattern */
    int bi = ((int)floorf(v->beat)) & 3, bn = (bi + 1) & 3;
    float e = v->ph * v->ph * (3 - 2 * v->ph), amp = 1 + 0.6f * v->w2;
    float hx = ex + 10, hy = ey - 1;
    float tx = hx + 5 + lerpf(PX[bi], PX[bn], e) * 7 * amp, ty = hy - 6 + lerpf(PY[bi], PY[bn], e) * 6 * amp;
    mg_line(eye, ex + 6, ey + 2, hx, hy, 2.5f, d - 0.01f, body);
    mg_line(eye, hx, hy, tx, ty, 1.2f, d - 0.015f, RGBA(255, 240, 200, 255));
    mg_circle(eye, tx, ty, 1.6f + 1.2f * v->pulse + (help ? 1.5f : 0), d - 0.02f, RGBA(255, 245, 200, 255));
}

/* Notes floating up from the band once they're into it. */
static void draw_music_notes(int eye, const Vibe *v)
{
    static const float GX[3] = {70, 200, 330};
    static const u32 NC[3] = {RGBA(255, 225, 140, 255), RGBA(255, 255, 255, 255), RGBA(180, 245, 210, 255)};
    if (v->w1 < 0.05f)
        return;
    for (int i = 0; i < 6; i++) {
        float c = v->beat / 2 + i / 6.0f, life = frac(c);
        int g = i % 3;
        float x = GX[g] + (hashf(i, (int)floorf(c)) - 0.5f) * 44 + 4 * sinf(life * 6 + i);
        float y = (g == 1 ? 34 : 54) - 30 * life;
        u32 col = rgba_alpha(NC[g], v->w1 * sinf(life * 3.14159f) * 0.85f);
        mg_circle(eye, x, y, 2.2f, 0.88f, col);
        mg_line(eye, x + 1.8f, y, x + 1.8f, y - 7, 1, 0.88f, col);
    }
}

static void draw_bubble(int eye)
{
    float a = S.T - S.bub_t;
    if (!S.bub_msg || a < 0 || a > 1.6f)
        return;
    float al = clampf(a / 0.12f, 0, 1) * clampf((1.6f - a) / 0.3f, 0, 1);
    float sx = S.bub_who ? DROSS_X : PIM_X;
    float w = gfx_text_width(S.bub_msg, 0.42f) + 14, lh = gfx_line_height(0.42f);
    float cx = clampf(sx - 22, w / 2 + 4, TOP_W - w / 2 - 4), cy = 42 - 3 * (1 - clampf(a / 0.15f, 0, 1));
    float d = D_BAND - 0.12f;
    u32 white = rgba_alpha(RGBA(255, 255, 255, 235), al);
    mg_tri(eye, sx - 7, cy + 5, sx + 1, cy + 5, sx - 1, cy + 14, d, white);
    mg_rect(eye, cx - w / 2 + 7, cy - 7, w - 14, 14, d, white);
    mg_circle(eye, cx - w / 2 + 7, cy, 7, d, white);
    mg_circle(eye, cx + w / 2 - 7, cy, 7, d, white);
    mg_text_centered(eye, S.bub_msg, cx, cy - lh / 2, 0.42f, d - 0.01f, rgba_alpha(RGBA(40, 34, 70, 255), al));
}

static void draw_band(int eye, const Vibe *v)
{
    draw_stage(eye, v);
    draw_choir(eye, v);
    draw_harpist(eye, v);
    draw_trumpeter(eye, v);
    draw_dross(eye, v);
    draw_pim(eye, v);
    draw_ember(eye, v);
    draw_music_notes(eye, v);
    draw_bubble(eye);
}

static void draw_confetti(int eye, const Vibe *v)
{
    static const u32 CC[5] = {RGBA(255, 215, 110, 255), RGBA(255, 140, 190, 255), RGBA(150, 240, 200, 255),
                              RGBA(140, 200, 255, 255), RGBA(255, 255, 255, 255)};
    if (v->w3 < 0.02f)
        return;
    for (int i = 0; i < 26; i++) {
        float x = hashf(i, 11) * 420 - 10 + 8 * sinf(S.T * 2.2f + i);
        float y = hashf(i, 13) * 270 + S.T * (30 + 30 * hashf(i, 12));
        y -= 270 * floorf(y / 270);
        float fl = fabsf(sinf(S.T * (4 + 4 * hashf(i, 15)) + i));
        mg_rect(eye, x, y - 15, 3.5f, 0.6f + 2.4f * fl, -0.3f + 1.1f * hashf(i, 14), rgba_alpha(CC[i % 5], v->w3));
    }
}

/* ---- drawing: lanterns ------------------------------------------------------------- */

static void lantern(int eye, float x, float y, float r, float d, u32 paper, float glow, float flame,
                    float alpha)
{
    u32 warm = RGBA(255, 170, 70, 255);
    if (glow > 0.01f) {
        if (r > 6)
            mg_circle(eye, x, y, r * 2.6f, d + 0.02f, rgba_alpha(warm, 0.14f * glow * alpha));
        mg_circle(eye, x, y, r * 1.7f, d + 0.01f, rgba_alpha(warm, 0.28f * glow * alpha));
    }
    u32 wood = rgba_alpha(RGBA(70, 40, 30, 255), alpha);
    if (r > 5)
        mg_line(eye, x, y - r * 1.1f, x, y - r * 1.9f, 1, d, rgba_alpha(RGBA(40, 30, 30, 255), alpha * 0.8f));
    mg_rect(eye, x - r * 0.78f, y - r * 0.98f, r * 1.56f, r * 1.96f, d, rgba_alpha(paper, alpha));
    mg_circle(eye, x, y, r, d, rgba_alpha(paper, alpha));
    if (r > 8) {
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
        if (n->reserved) {   /* Ember's light reaches it from her baton */
            mg_line(eye, EMBER_X + 15, EMBER_Y - 4, x, y, 1, (d + D_BAND) / 2,
                    rgba_alpha(RGBA(255, 220, 120, 255), 0.25f * alpha));
            mg_circle(eye, x, y, r * (2.0f + 0.3f * sinf(T * 8)), d + 0.02f,
                      rgba_alpha(RGBA(255, 220, 120, 255), 0.35f * alpha));
        }
        if (n->partner > i) {
            const Note *p = &S.notes[n->partner];
            mg_line(eye, x, y, s_x((p->lane - 1) * LANE_SPREAD, s), y, 2, d + 0.01f,
                    rgba_alpha(MG_GOLD, 0.45f * alpha));
        }
        lantern(eye, x, y, r, d, mix(tint, RGBA(120, 90, 90, 255), 0.35f), 0.35f * flick, 0.45f * flick, alpha);
        break;
    }
    case N_PERFECT:
    case N_GOOD: {   /* lit, it floats up toward the band */
        float a = T - n->jt;
        if (a > 1.0f)
            return;
        float k = a, warm = n->state == N_PERFECT ? 1.0f : 0.7f;
        float x = hx + 6 * sinf(a * 5 + i), y = HIT_Y - 4 - 55 * a - 20 * a * a;
        float d = clampf(D_HIT - 0.1f + 0.7f * k, -0.4f, 0.8f);
        float alpha = 1 - k * k;
        if (a < 0.25f)   /* a ring of light where it caught */
            mg_circle(eye, hx, HIT_Y, 18 + 60 * a, D_HIT - 0.05f, rgba_alpha(RGBA(255, 220, 140, 255), 0.5f * (1 - a / 0.25f)));
        lantern(eye, x, y, 15 * (1 - 0.45f * k), d, mix(tint, RGBA(255, 244, 210, 255), 0.55f * warm),
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

/* ---- drawing: screens ------------------------------------------------------------- */

static void draw_top(int eye)
{
#ifdef LAN_DEBUG
    dc = 0;
#endif
    float T = S.T, beat = (T - OFFSET) / BEAT;
    char buf[64];
    Vibe v;
    get_vibe(&v);

    draw_sky(eye);
    draw_band(eye, &v);
    draw_motes(eye);
    draw_islands(eye, &v);
    draw_path(eye, &v);

    for (int i = S.n - 1; i >= 0; i--)
        draw_note(eye, i);
    draw_confetti(eye, &v);

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
    mg_rect(eye, 0, 0, TOP_W * prog, 2, -0.05f, rgba_alpha(MG_GOLD, 0.7f));
    if (S.streak >= 3) {
        snprintf(buf, sizeof(buf), "%d lit", S.streak);
        mg_text(eye, buf, TOP_W - 8 - gfx_text_width(buf, 0.5f), 5, 0.5f, -0.1f, MG_GOLD);
    }

    /* banners, on a dark plate so they read over the lanterns */
    float plate = beat < 4 ? 1 : clampf(3 - (T - S.banner_t) / BEAT, 0, 1);
    if (S.finale)
        plate = clampf((T - S.finale_t) / 0.5f, 0, 1);
    if (T - S.resync_t < 1.5f)
        plate = 1;
    if (plate > 0)
        mg_rect(eye, 100, 112, 200, 64, -0.14f, RGBA(24, 14, 32, (int)(150 * plate)));
    if (beat < 4) {
        mg_text_centered(eye, SEC_NAME[0], 200, 116, 0.7f, -0.2f, MG_GOLD);
        mg_text_centered(eye, "Ready...", 200, 140, 0.5f, -0.15f, MG_WHITE);
        for (int k = 0; k < 4; k++)
            mg_circle(eye, 170 + k * 20, 168, 4, -0.15f,
                      k <= (int)floorf(beat) && beat >= 0 ? MG_GOLD : RGBA(255, 255, 255, 60));
    } else if (T - S.banner_t < 3 * BEAT) {
        float a = clampf(3 - (T - S.banner_t) / BEAT, 0, 1);
        mg_text_centered(eye, SEC_NAME[S.banner_sec], 200, 116, 0.7f, -0.2f, rgba_alpha(MG_GOLD, a));
        mg_text_centered(eye, SEC_SUB[S.banner_sec], 200, 140, 0.45f, -0.15f, rgba_alpha(MG_WHITE, a));
    }
    if (S.cheat_on) {
        int left = (int)ceilf((S.cheat_until - T) / BEAT);
        snprintf(buf, sizeof(buf), "Ember's help: %d", left < 0 ? 0 : left);
        mg_text(eye, buf, 8, 5, 0.5f, -0.1f, rgba_alpha(RGBA(255, 220, 130, 255), 0.75f + 0.25f * sinf(T * 6)));
    }
    if (T - S.resync_t < 1.5f)
        mg_text_centered(eye, "The Watch kept the beat", 200, 128, 0.5f, -0.2f, MG_WHITE);
    if (S.finale) {
        float a = clampf((T - S.finale_t) / 0.5f, 0, 1);
        mg_text_centered(eye, S.miss == 0 ? "Every lantern lit" : "The band plays on", 200, 120, 0.7f,
                         -0.3f, rgba_alpha(MG_GOLD, a));
    }
#ifdef LAN_DEBUG
    static int dc_max;
    if (dc > dc_max) {
        dc_max = dc;
        printf("lantern: %d draw calls at %.2f s (stage %d)\n", dc, T, S.stage);
    }
#endif
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

    /* the band's mood: three bars to fill, one per stage (above the Cheat button) */
    static const u32 STAGE_COL[STAGES] = {RGBA(200, 190, 230, 255), RGBA(180, 230, 255, 255), RGBA(170, 240, 190, 255),
                                          RGBA(255, 215, 110, 255)};
    snprintf(buf, sizeof(buf), "Band: %s", STAGE_NAME[S.stage]);
    gfx_text(buf, 178, 180, 0.42f, STAGE_COL[S.stage]);
    for (int k = 1; k < STAGES; k++) {
        float x = 178 + (k - 1) * 46.0f;
        float f = clampf((float)(S.hype - STAGE_AT[k - 1]) / (STAGE_AT[k] - STAGE_AT[k - 1]), 0, 1);
        gfx_rect(x, 197, 42, 6, RGBA(255, 255, 255, 40));
        if (f > 0)
            gfx_rect(x, 197, 42 * f, 6, STAGE_COL[k]);
    }
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
    .rules = "Fly the path of light to the angel and spirit band.\n"
             "Lanterns float toward you along three lanes.\n"
             "Tap a lane as its lantern reaches the glowing\n"
             "ring, right on the beat. Perfect, Good, or Dark.\n"
             "Two lanterns side by side: tap both lanes.\n"
             "Hits in a row fire the band up; a miss calms them.\n"
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
