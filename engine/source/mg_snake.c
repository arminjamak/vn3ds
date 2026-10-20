/* Crown of the Worm: snake on a 20x12 board while the leak bends the view.
 *
 * Eat apples. The run is a fixed series of stages, each a little harder to
 * read than the last: Clear, Tidewave, Mirror, Chromatic Split, Shuffled
 * Slices, Fourfold, Upside Down. A stage lasts until its apples are eaten (or
 * STAGE_CAP seconds under the filter, when the leak tires), then the next
 * one is announced for WARN_TIME seconds before it bends the view. After the
 * last stage the crown appears; eating it ends the run with the crowned worm
 * and a cheering crowd.
 *
 * Fairness: under every filter the head and the current apple are redrawn
 * crisp on top of the distorted view, at the place the view shows them;
 * Mirror and Upside Down are drawn into the capture already reflected (whole
 * worm, eyes and all) and the D-pad follows the view; slices are numbered
 * and stay put for the whole stage, the real walls glow red wherever the
 * view puts them, a pip marks the cell the head enters next, and the bottom
 * screen always shows the true board. The worm slows a little under the
 * hard filters (constant tempo, so the rhythm stays readable) and freezes
 * for FREEZE_TIME whenever the view switches, so you can take it in. An
 * announced stage's apple only ripens when its filter starts, so no filter
 * can be skipped by eating fast during the warning.
 *
 * The board is drawn into the eye's capture (draw_offscreen) and draw_top
 * re-assembles it from capture pieces.
 *
 * Score: for every apple and the crown we record the shortest path at the
 * moment it spawned (a BFS that knows the body's tail moves away over time)
 * and the steps the player actually took. With r = sum(actual) / sum(min):
 *     tempo = 1 / (1 + (max(0, r - 1.05) / 0.9) ^ 1.6)
 * Crowned: 30 + 70 * tempo. Died: 45 * progress * (0.6 + 0.4 * tempo), with
 * progress the share of stages (and the crown) done. */

#include "minigame.h"

#define GW 20
#define GH 12
#define NC (GW * GH)
#define CELL 18
#define BX 20
#define BY 20
#define FW (GW * CELL) /* 360 */
#define FH (GH * CELL) /* 216 */
#define MAXLEN 64
#define GRACE 1.0f
#define SHED_TIME 6.0f
#define BOOST_TIME 1.0f
#define BOOST_COOLDOWN 3.0f
#define WARN_TIME 2.6f    /* the next filter is announced this long */
#define STAGE_CAP 25.0f   /* the leak tires after this long under one filter */
#define GOLD_TIME 8.0f    /* a golden apple turns red after this */
#define GULP_TIME 0.35f
#define FINALE_TIME 4.2f
#define FREEZE_TIME 0.45f /* the worm freezes while the view switches */

#define D_BOARD 0.25f
#define D_FOOD (-0.05f)
#define D_WORM (-0.15f)
#define D_HEAD (-0.2f)
#define D_MARK (-0.26f)
#define D_CROWN (-0.3f)

enum { DIR_R, DIR_D, DIR_L, DIR_U };
static const int DX[4] = {1, 0, -1, 0}, DY[4] = {0, 1, 0, -1};
static const u32 DIR_KEY[4] = {KEY_RIGHT_, KEY_DOWN_, KEY_LEFT_, KEY_UP_};

enum { F_NONE, F_WAVE, F_MIRROR, F_CHROMA, F_SLICES, F_QUAD, F_FLIP, F_COUNT };
static const char *const FNAME[F_COUNT] = {
    "Clear", "Tidewave", "Mirror", "Chromatic Split", "Shuffled Slices", "Fourfold", "Upside Down",
};
static const char *const FHINT[F_COUNT] = {
    "Eat the apples to move on.",
    "The rows sway a little. Steer as usual.",
    "Left and right swap - so does the D-pad.",
    "Colour ghosts: follow the solid worm.",
    "Five numbered slices: count 1 to 5.",
    "Shifted by half: the walls are in the middle.",
    "Up and down swap - so does the D-pad.",
};
static const bool FHARD[F_COUNT] = {false, false, true, false, true, true, true};
static const u32 FCOL[F_COUNT] = {
    RGBA(150, 220, 150, 255), RGBA(90, 170, 255, 255), RGBA(200, 140, 255, 255),
    RGBA(255, 90, 120, 255), RGBA(80, 230, 255, 255), RGBA(255, 170, 60, 255),
    RGBA(255, 90, 220, 255),
};

typedef struct {
    u8 filter, apples;
} WormStage;
static const WormStage STAGES[] = {
    {F_NONE, 2}, {F_WAVE, 2}, {F_MIRROR, 3}, {F_CHROMA, 2}, {F_SLICES, 3}, {F_QUAD, 3}, {F_FLIP, 3},
};
#define NSTAGES ((int)(sizeof(STAGES) / sizeof(STAGES[0])))

enum { S_PLAY, S_DYING, S_CROWNED };

#define NSL 5
#define SW (FW / NSL) /* 72 = 4 cells */
#define WAVE_H 12
static const u32 SLC[NSL] = {
    RGBA(255, 110, 110, 255), RGBA(255, 200, 90, 255), RGBA(130, 230, 120, 255),
    RGBA(90, 200, 255, 255), RGBA(200, 140, 255, 255),
};

static struct {
    int state;
    float t, state_t;
    /* the worm, head first; p* is the body before the last step */
    u8 bx[MAXLEN], by[MAXLEN];
    int len;
    u8 px[MAXLEN], py[MAXLEN];
    int plen;
    int dir, queue[2], nq, pad_dir;
    float step_acc;
    float boost, boost_cd;
    /* the current target */
    int fx, fy;
    bool crown, golden;
    float target_t, gold_t;
    int gulp_x, gulp_y;
    float gulp_t;
    bool gulp_gold;
    int apples;   /* golden ones count twice */
    int cur_min, cur_steps;
    int sum_min, sum_act;
    /* the series */
    int stage, stage_apples;
    int filter, warn_filter;
    float warn_t, stage_t, glitch, banner_t, tired_t, freeze;
    int perm[NSL];
    /* cheat */
    float shed;
    bool shed_warned;
    u8 skin_x[MAXLEN], skin_y[MAXLEN];
    int skin_len;
    float skin_t;
    bool died_wall;
} S;

static u32 hash(u32 x)
{
    x ^= x >> 16;
    x *= 0x7feb352du;
    x ^= x >> 15;
    x *= 0x846ca68bu;
    x ^= x >> 16;
    return x;
}

static u32 mixc(u32 a, u32 b, float t)
{
    t = clampf(t, 0, 1);
    u32 o = 0;
    for (int s = 0; s < 32; s += 8) {
        float ca = (float)((a >> s) & 0xFF), cb = (float)((b >> s) & 0xFF);
        o |= (u32)(ca + (cb - ca) * t + 0.5f) << s;
    }
    return o;
}

/* ---- path finding ---------------------------------------------------------- */

/* Time-aware BFS from bx[0]: body cell j frees up after len - j steps, so it
 * may be entered on step t >= len - j. dist -1 = unreachable; first = the
 * first move on a shortest route to each cell. */
static s16 bdist[NC];
static s8 bfirst[NC];

static void bfs(const u8 *bx, const u8 *by, int len, bool wrap)
{
    static u8 occ[NC];
    static s16 q[NC];
    memset(occ, 0, sizeof(occ));
    for (int i = 0; i < NC; i++) {
        bdist[i] = -1;
        bfirst[i] = -1;
    }
    for (int j = 0; j < len; j++) {
        int c = by[j] * GW + bx[j], v = len - j;
        if (v > occ[c])
            occ[c] = (u8)v;
    }
    int h = by[0] * GW + bx[0], qh = 0, qt = 0;
    bdist[h] = 0;
    q[qt++] = (s16)h;
    while (qh < qt) {
        int c = q[qh++], x = c % GW, y = c / GW, d = bdist[c];
        for (int k = 0; k < 4; k++) {
            int nx = x + DX[k], ny = y + DY[k];
            if (nx < 0 || nx >= GW || ny < 0 || ny >= GH) {
                if (!wrap)
                    continue;
                nx = (nx + GW) % GW;
                ny = (ny + GH) % GH;
            }
            int n = ny * GW + nx;
            if (bdist[n] >= 0 || occ[n] > d + 1)
                continue;
            bdist[n] = (s16)(d + 1);
            bfirst[n] = (s8)(c == h ? k : bfirst[c]);
            q[qt++] = (s16)n;
        }
    }
}

static bool on_body(int x, int y, int from, int to)
{
    for (int j = from; j < to; j++)
        if (S.bx[j] == x && S.by[j] == y)
            return true;
    return false;
}

/* ---- the series -------------------------------------------------------------- */

static int need(void) { return S.stage < NSTAGES ? STAGES[S.stage].apples : 1; }

/* Mirror and Upside Down reflect the view, and the D-pad with it: a pressed
 * direction (as seen) becomes the true direction. Its own inverse, so it
 * also turns a true direction into the one seen. */
static int view_dir(int d)
{
    if (S.filter == F_MIRROR && (d == DIR_L || d == DIR_R))
        return d ^ 2;
    if (S.filter == F_FLIP && (d == DIR_U || d == DIR_D))
        return d ^ 2;
    return d;
}

/* The shortest route to the target from here (after spawn_target's bfs). */
static void price_target(void)
{
    int c = S.fy * GW + S.fx;
    S.cur_steps = 0;
    S.cur_min = bdist[c] > 0 ? bdist[c] : abs(S.fx - S.bx[0]) + abs(S.fy - S.by[0]) + 2;
}

static void spawn_target(bool crown)
{
    bfs(S.bx, S.by, S.len, false);
    int pick = -1, seen = 0, want = crown ? 8 : 5;
    /* prefer a reachable cell at least `want` steps away, then any reachable,
     * then any free cell */
    for (int pass = 0; pass < 3 && pick < 0; pass++) {
        seen = 0;
        for (int c = 0; c < NC; c++) {
            int x = c % GW, y = c / GW;
            if (on_body(x, y, 0, S.len))
                continue;
            if (pass == 0 && bdist[c] < want)
                continue;
            if (pass == 1 && bdist[c] < 1)
                continue;
            if (mg_randi(0, seen++) == 0)
                pick = c;
        }
    }
    if (pick < 0)
        pick = 0;
    S.fx = pick % GW;
    S.fy = pick / GW;
    S.crown = crown;
    S.target_t = 0;
    S.cur_steps = 0;
    price_target();
    /* now and then a golden apple: worth two, but only for GOLD_TIME */
    S.golden = !crown && S.stage >= 1 && S.stage < NSTAGES && S.warn_t <= 0 && mg_randi(0, 5) == 0;
    S.gold_t = S.golden ? GOLD_TIME : 0;
    if (S.golden)
        mg_sfx("snake_golden_spawn");
}

/* A fixed shuffle for the whole stage, with at most one slice in place. */
static void shuffle_slices(void)
{
    for (int tries = 0; tries < 24; tries++) {
        for (int i = 0; i < NSL; i++)
            S.perm[i] = i;
        for (int i = NSL - 1; i > 0; i--) {
            int j = mg_randi(0, i), k = S.perm[i];
            S.perm[i] = S.perm[j];
            S.perm[j] = k;
        }
        int fixed = 0;
        for (int i = 0; i < NSL; i++)
            fixed += S.perm[i] == i;
        if (fixed <= 1)
            return;
    }
    for (int i = 0; i < NSL; i++)
        S.perm[i] = (i + 2) % NSL;
}

static void worm_stage_clear(bool tired)
{
    if (S.filter != F_NONE) {
        S.filter = F_NONE;
        S.glitch = 1;
        S.freeze = FREEZE_TIME;
        mg_sfx(tired ? "snake_leak_tires" : "snake_filter_off");
    }
    S.tired_t = tired ? 2.2f : 0;
    S.warn_t = 0;
    S.stage++;
    S.stage_apples = 0;
    S.stage_t = 0;
    if (S.stage >= NSTAGES) {
        spawn_target(true);
        S.banner_t = 2.5f;
        mg_sfx("snake_crown_appears");
        return;
    }
    S.warn_filter = STAGES[S.stage].filter;
    S.warn_t = WARN_TIME;
    mg_sfx("snake_stage_next");
}

static void start(u32 seed)
{
    (void)seed;
    memset(&S, 0, sizeof(S));
    S.len = 3;
    for (int i = 0; i < S.len; i++) {
        S.bx[i] = (u8)(5 - i);
        S.by[i] = GH / 2;
    }
    memcpy(S.px, S.bx, sizeof(S.px));
    memcpy(S.py, S.by, sizeof(S.py));
    S.plen = S.len;
    S.dir = DIR_R;
    S.pad_dir = -1;
    for (int i = 0; i < NSL; i++)
        S.perm[i] = i;
    spawn_target(false);
}

static float tempo_of(int smin, int sact)
{
    if (smin <= 0 || sact <= 0)
        return 0.5f;
    float over = (float)sact / (float)smin - 1.0f;
    float x = fmaxf(0, over - 0.05f) / 0.9f;
    return 1.0f / (1.0f + powf(x, 1.6f));
}

static float progress(void)
{
    if (S.state == S_CROWNED)
        return 1;
    float p = S.stage < NSTAGES ? S.stage + fminf(1, (float)S.stage_apples / need()) : NSTAGES;
    return p / (NSTAGES + 1);
}

static int score(void)
{
    float tp = tempo_of(S.sum_min, S.sum_act);
    if (S.state == S_CROWNED)
        return (int)(30 + 70 * tp + 0.5f);
    return (int)(45.0f * progress() * (0.6f + 0.4f * tp) + 0.5f);
}

static const char *rating_name(int sc)
{
    return sc >= 95 ? "Worm Emperor" : sc >= 85 ? "Glitch Monarch" : sc >= 72 ? "Crowned Wriggler"
         : sc >= 58 ? "Careful Duke of Dirt" : "Very Safe Noodle";
}

static int route_pct(void)
{
    return S.sum_min > 0 ? (int)(100.0f * S.sum_act / S.sum_min + 0.5f) : 100;
}

static const char *verdict(void)
{
    static char buf[128];
    if (S.state == S_CROWNED)
        snprintf(buf, sizeof(buf), "Crowned in %d%% of the shortest route: %s", route_pct(),
                 rating_name(score()));
    else if (S.stage >= NSTAGES)
        snprintf(buf, sizeof(buf), "Fell one bite short of the crown.");
    else
        snprintf(buf, sizeof(buf), "Fell in stage %d of %d (%s) - the crown waits.", S.stage + 1,
                 NSTAGES, FNAME[STAGES[S.stage].filter]);
    return buf;
}

static void die(bool wall)
{
    S.state = S_DYING;
    S.state_t = 0;
    S.died_wall = wall;
    memcpy(S.px, S.bx, sizeof(S.px));
    memcpy(S.py, S.by, sizeof(S.py));
    S.plen = S.len;
    mg_sfx("snake_die");
}

static void eat(void)
{
    S.sum_min += S.cur_min;
    S.sum_act += S.cur_steps > S.cur_min ? S.cur_steps : S.cur_min; /* the cheat can't beat par */
    S.gulp_x = S.fx;
    S.gulp_y = S.fy;
    S.gulp_t = GULP_TIME;
    S.gulp_gold = S.golden;
    if (S.crown) {
        S.state = S_CROWNED;
        S.state_t = 0;
        S.filter = F_NONE;
        S.warn_t = 0;
        mg_sfx("snake_crown");
        return;
    }
    int worth = S.golden ? 2 : 1;
    S.apples += worth;
    S.stage_apples += worth;
    if (S.golden)
        mg_sfx("snake_golden_apple");
    else
        mg_sfx_pitch("snake_apple_crunch", 0.92f + 0.16f * mg_randf());
    if (S.stage_apples >= need())
        worm_stage_clear(false);
    if (!S.crown)
        spawn_target(false);
}

static void step(void)
{
    if (S.nq) {
        S.dir = S.queue[0];
        S.queue[0] = S.queue[1];
        S.nq--;
    }
    int nx = S.bx[0] + DX[S.dir], ny = S.by[0] + DY[S.dir];
    if (nx < 0 || nx >= GW || ny < 0 || ny >= GH) {
        if (S.shed <= 0) {
            die(true);
            return;
        }
        nx = (nx + GW) % GW;
        ny = (ny + GH) % GH;
        mg_sfx("snake_wrap");
    }
    bool grow = nx == S.fx && ny == S.fy && S.warn_t <= 0;   /* it ripens with the filter */
    if (on_body(nx, ny, 0, grow ? S.len : S.len - 1)) {
        if (S.shed <= 0) {
            die(false);
            return;
        }
        mg_sfx("snake_phase");
    }
    memcpy(S.px, S.bx, sizeof(S.px));
    memcpy(S.py, S.by, sizeof(S.py));
    S.plen = S.len;
    if (grow && S.len < MAXLEN)
        S.len++;
    for (int i = S.len - 1; i > 0; i--) {
        S.bx[i] = S.bx[i - 1];
        S.by[i] = S.by[i - 1];
    }
    S.bx[0] = (u8)nx;
    S.by[0] = (u8)ny;
    if (S.warn_t <= 0)
        S.cur_steps++;
    if (grow)
        eat();
}

/* `d` is a true direction (already through view_dir). */
static void enqueue(int d)
{
    int last = S.nq ? S.queue[S.nq - 1] : S.dir;
    if (d == last || d == (last + 2) % 4 || S.nq >= 2)
        return;
    S.queue[S.nq++] = d;
    mg_sfx("snake_turn");
}

static float interval(void)
{
    float iv = fmaxf(0.15f, 0.21f - 0.0035f * S.apples);
    if (S.filter != F_NONE)
        iv *= FHARD[S.filter] ? 1.25f : 1.1f;
    return S.boost > 0 ? iv * 0.5f : iv;
}

static bool update(const Input *in, float dt, bool cheat)
{
    S.t += dt;
    S.target_t += dt;
    if (S.glitch > 0)
        S.glitch -= dt * 2.5f;
    if (S.skin_t > 0)
        S.skin_t -= dt;
    if (S.gulp_t > 0)
        S.gulp_t -= dt;
    if (S.banner_t > 0)
        S.banner_t -= dt;
    if (S.tired_t > 0)
        S.tired_t -= dt;

    if (S.state == S_DYING) {
        S.state_t += dt;
        return S.state_t < 2.0f;
    }
    if (S.state == S_CROWNED) {
        float before = S.state_t;
        S.state_t += dt;
        if (before < 0.8f && S.state_t >= 0.8f)
            mg_sfx("snake_crowd_cheer");
        if (before < 1.2f && S.state_t >= 1.2f)
            mg_sfx("snake_rating");
        if (S.state_t > 0.6f && (in->down & KEY_A_))
            return false;
        return S.state_t < FINALE_TIME;
    }

    if (cheat) {
        S.shed = SHED_TIME;
        S.shed_warned = false;
        memcpy(S.skin_x, S.bx, sizeof(S.skin_x));
        memcpy(S.skin_y, S.by, sizeof(S.skin_y));
        S.skin_len = S.len;
        S.skin_t = 2.0f;
        mg_sfx("snake_shed");
    }

    /* steering: D-pad presses and circle pad flicks (as seen), two turns
     * buffered */
    for (int d = 0; d < 4; d++)
        if (in->down & DIR_KEY[d])
            enqueue(view_dir(d));
    int pd = -1;
    if (fabsf(in->cx) > fabsf(in->cy)) {
        if (fabsf(in->cx) > 0.55f)
            pd = in->cx > 0 ? DIR_R : DIR_L;
    } else if (fabsf(in->cy) > 0.55f) {
        pd = in->cy > 0 ? DIR_U : DIR_D;
    }
    if (pd >= 0 && pd != S.pad_dir)
        enqueue(view_dir(pd));
    S.pad_dir = pd;

    /* boost */
    if (S.boost > 0)
        S.boost -= dt;
    if (S.boost_cd > 0) {
        S.boost_cd -= dt;
        if (S.boost_cd <= 0)
            mg_sfx("snake_boost_ready");
    }
    if ((in->down & KEY_A_) && S.boost_cd <= 0 && S.t >= GRACE) {
        S.boost = BOOST_TIME;
        S.boost_cd = BOOST_COOLDOWN;
        mg_sfx("snake_boost");
    }

    /* the shed skin */
    if (S.shed > 0) {
        S.shed -= dt;
        if (!S.shed_warned && S.shed < 1.5f) {
            S.shed_warned = true;
            mg_sfx("snake_shed_fading");
        }
        if (S.shed <= 0) {
            if (on_body(S.bx[0], S.by[0], 1, S.len)) {
                S.shed = 0.01f;   /* stay a ghost until the head is clear */
            } else {
                S.shed = 0;
                mg_sfx("snake_shed_end");
            }
        }
    }

    /* a golden apple ripens back to red */
    if (S.golden && (S.gold_t -= dt) <= 0) {
        S.golden = false;
        mg_sfx("snake_golden_fade");
    }

    /* the leak: announce, then bend the view until the stage is done */
    if (S.warn_t > 0) {
        float before = S.warn_t;
        S.warn_t -= dt;
        if (before > 1.0f && S.warn_t <= 1.0f)
            mg_sfx("snake_filter_warn");
        if (S.warn_t <= 0) {
            S.warn_t = 0;
            S.filter = S.warn_filter;
            S.stage_t = 0;
            S.glitch = 1;
            S.freeze = FREEZE_TIME;
            if (S.filter == F_SLICES)
                shuffle_slices();
            /* the apple ripens now: its route counts from here (and if the
             * worm is lying on it, it rolls somewhere free) */
            if (!S.crown && on_body(S.fx, S.fy, 0, S.len)) {
                spawn_target(false);
            } else {
                bfs(S.bx, S.by, S.len, false);
                price_target();
            }
            mg_sfx("snake_filter_on");
        }
    } else if (S.filter != F_NONE) {
        S.stage_t += dt;
        if (S.stage_t >= STAGE_CAP)
            worm_stage_clear(true);
    }

    if (S.t < GRACE)
        return true;
    if (S.freeze > 0) {   /* a beat to take in the new view */
        S.freeze -= dt;
        return true;
    }
    S.step_acc += dt / interval();
    while (S.step_acc >= 1.0f && S.state == S_PLAY) {
        S.step_acc -= 1.0f;
        step();
    }
    return true;
}

/* ---- where things are drawn -------------------------------------------------- */

static float cell_cx(float gx) { return BX + (gx + 0.5f) * CELL; }
static float cell_cy(float gy) { return BY + (gy + 0.5f) * CELL; }

/* Grid cell -> position in the capture. Mirror and Upside Down are drawn
 * reflected right here, so the worm and its eyes look right. */
static void cap_xy(float gx, float gy, float *x, float *y)
{
    float sx = cell_cx(gx), sy = cell_cy(gy);
    if (S.filter == F_MIRROR)
        sx = 2 * BX + FW - sx;
    if (S.filter == F_FLIP)
        sy = 2 * BY + FH - sy;
    *x = sx;
    *y = sy;
}

/* Interpolated capture position of segment i. */
static void seg_pos(int i, float *x, float *y)
{
    float f = S.state == S_PLAY && S.t >= GRACE ? clampf(S.step_acc, 0, 1) : 1.0f;
    int cx = S.bx[i], cy = S.by[i];
    int j = i < S.plen ? i : S.plen - 1;
    int px = S.px[j], py = S.py[j];
    float gx = (float)cx, gy = (float)cy;
    if (abs(px - cx) + abs(py - cy) == 1) {
        gx = px + (cx - px) * f;
        gy = py + (cy - py) * f;
    }
    cap_xy(gx, gy, x, y);
}

static float filter_env(void)
{
    return S.filter == F_NONE ? 0 : clampf(S.stage_t / 0.6f, 0, 1);
}

static int wave_off(int band)
{
    return (int)lroundf(filter_env() * 9 * sinf(band * 0.5f + S.t * 2.2f));
}

/* Capture position -> where draw_top shows it. */
static void view_pos(float x, float y, float *ox, float *oy)
{
    *ox = x;
    *oy = y;
    switch (S.filter) {
    case F_WAVE: {
        int k = (int)clampf((y - BY) / WAVE_H, 0, FH / WAVE_H - 1);
        *ox = x + wave_off(k);
        break;
    }
    case F_SLICES: {
        int s = (int)clampf((x - BX) / SW, 0, NSL - 1);
        for (int i = 0; i < NSL; i++)
            if (S.perm[i] == s)
                *ox = x + (float)((i - s) * SW);
        break;
    }
    case F_QUAD:
        *ox = x < BX + FW / 2 ? x + FW / 2 : x - FW / 2;
        *oy = y < BY + FH / 2 ? y + FH / 2 : y - FH / 2;
        break;
    }
}

/* ---- drawing helpers -------------------------------------------------------- */

static void draw_crown(int eye, float cx, float cy, float s, float depth, float a)
{
    u32 gold = rgba_alpha(MG_GOLD, a), deep = rgba_alpha(RGBA(220, 150, 40, 255), a);
    float h = 8 * s;
    mg_circle(eye, cx, cy - h * 0.3f, 11 * s, depth + 0.05f, rgba_alpha(RGBA(255, 210, 110, 60), a));
    mg_tri(eye, cx - 7 * s, cy, cx - 2.5f * s, cy, cx - 6 * s, cy - h * 0.85f, depth, deep);
    mg_tri(eye, cx + 7 * s, cy, cx + 2.5f * s, cy, cx + 6 * s, cy - h * 0.85f, depth, deep);
    mg_tri(eye, cx - 3.5f * s, cy, cx + 3.5f * s, cy, cx, cy - h, depth, gold);
    mg_rect(eye, cx - 7 * s, cy - 0.5f * s, 14 * s, 4 * s, depth, gold);
    mg_circle(eye, cx, cy + 1.5f * s, 1.4f * s, depth - 0.02f, rgba_alpha(RGBA(230, 60, 90, 255), a));
    mg_circle(eye, cx - 4.5f * s, cy + 1.5f * s, 0.9f * s, depth - 0.02f, rgba_alpha(RGBA(90, 200, 255, 255), a));
    mg_circle(eye, cx + 4.5f * s, cy + 1.5f * s, 0.9f * s, depth - 0.02f, rgba_alpha(RGBA(90, 200, 255, 255), a));
    mg_circle(eye, cx, cy - h, 1.2f * s, depth - 0.02f, rgba_alpha(MG_WHITE, a));
}

/* A tiny crown for the crowd to toss about (4 draws). */
static void mini_crown(int eye, float cx, float cy, float s, float depth, u32 c)
{
    mg_rect(eye, cx - 5 * s, cy - 1 * s, 10 * s, 3 * s, depth, c);
    mg_tri(eye, cx - 5 * s, cy, cx - 1.5f * s, cy, cx - 4.5f * s, cy - 5 * s, depth, c);
    mg_tri(eye, cx - 2 * s, cy, cx + 2 * s, cy, cx, cy - 6 * s, depth, c);
    mg_tri(eye, cx + 5 * s, cy, cx + 1.5f * s, cy, cx + 4.5f * s, cy - 5 * s, depth, c);
}

/* A shiny apple with a leaf, centred on (x, y). */
static void draw_apple(int eye, float x, float y, float s, float depth, bool gold, float a)
{
    u32 body = gold ? RGBA(255, 196, 50, 255) : RGBA(222, 32, 48, 255);
    u32 dark = gold ? RGBA(160, 100, 16, 255) : RGBA(110, 8, 28, 255);
    u32 shine = gold ? RGBA(255, 252, 220, 255) : RGBA(255, 190, 190, 255);
    if (gold) {
        mg_circle(eye, x, y, 12 * s, depth + 0.03f, rgba_alpha(RGBA(255, 220, 90, 70), a));
        for (int k = 0; k < 2; k++) {
            float an = S.t * 2.6f + k * 3.14f;
            mg_rect(eye, x + cosf(an) * 11 * s - 1, y + sinf(an) * 11 * s - 1, 2, 2, depth - 0.03f,
                    rgba_alpha(MG_WHITE, a));
        }
    }
    mg_rect(eye, x - 5.5f * s, y + 6.2f * s, 11 * s, 2 * s, depth + 0.02f, RGBA(0, 0, 0, (u32)(70 * a)));
    mg_circle(eye, x - 2.5f * s, y + 0.4f * s, 6.3f * s, depth + 0.01f, rgba_alpha(dark, a));
    mg_circle(eye, x + 2.5f * s, y + 0.4f * s, 6.3f * s, depth + 0.01f, rgba_alpha(dark, a));
    mg_circle(eye, x - 2.4f * s, y, 5.3f * s, depth, rgba_alpha(body, a));
    mg_circle(eye, x + 2.4f * s, y, 5.3f * s, depth, rgba_alpha(body, a));
    mg_circle(eye, x, y + 1.4f * s, 5.0f * s, depth, rgba_alpha(body, a));
    mg_circle(eye, x - 3.4f * s, y - 2.2f * s, 1.7f * s, depth - 0.01f, rgba_alpha(shine, 0.85f * a));
    mg_circle(eye, x, y - 4.6f * s, 1.3f * s, depth - 0.005f, rgba_alpha(dark, a));
    mg_line(eye, x, y - 4.2f * s, x + 1.2f * s, y - 8.6f * s, 1.6f * s, depth - 0.02f,
            rgba_alpha(RGBA(110, 70, 30, 255), a));
    float lx = x + 1.0f * s, ly = y - 7.2f * s;
    mg_tri(eye, lx, ly, lx + 3 * s, ly - 3.6f * s, lx + 7 * s, ly - 2.6f * s, depth - 0.02f,
           rgba_alpha(RGBA(120, 220, 90, 255), a));
    mg_tri(eye, lx, ly, lx + 7 * s, ly - 2.6f * s, lx + 3.6f * s, ly + 0.4f * s, depth - 0.02f,
           rgba_alpha(RGBA(60, 160, 60, 255), a));
    if (fmodf(S.t + x * 0.01f, 1.9f) < 0.22f)   /* a glint */
        mg_rect(eye, x + 2.2f * s, y - 1.8f * s, 2, 2, depth - 0.03f, rgba_alpha(MG_WHITE, a));
}

static float apple_bob(void) { return sinf(S.t * 3.2f) * 1.3f; }

/* The bitten apple: shrinks away and sprays bits. k goes 1 -> 0. */
static void draw_crunch(int eye, float x, float y, float k, bool gold)
{
    if (k > 0.45f)
        draw_apple(eye, x, y, (k - 0.45f) / 0.55f, D_FOOD, gold, 1);
    float u = 1 - k;
    static const u32 BITS[3] = {RGBA(255, 240, 200, 255), RGBA(222, 32, 48, 255), RGBA(110, 200, 80, 255)};
    for (int i = 0; i < 7; i++) {
        u32 h = hash((u32)i * 97 + (u32)S.gulp_x * 13 + (u32)S.gulp_y * 7);
        float an = i * 0.9f + (float)(h % 100) / 60.0f, d = u * (12 + (float)(h % 8));
        u32 c = gold && i % 3 == 1 ? MG_GOLD : BITS[i % 3];
        mg_rect(eye, x + cosf(an) * d - 1.5f, y + sinf(an) * d * 0.7f + u * u * 10 - 1.5f, 3, 3,
                D_FOOD - 0.04f, rgba_alpha(c, k * 1.4f));
    }
}

static void draw_face(int eye, float x, float y, int d, float r, float depth, bool dead)
{
    float fx = (float)DX[d], fy = (float)DY[d], sx = -fy, sy = fx;
    u32 ink = RGBA(40, 16, 36, 255);
    for (int k = -1; k <= 1; k += 2) {
        float ex = x + fx * r * 0.25f + sx * r * 0.5f * k, ey = y + fy * r * 0.25f + sy * r * 0.5f * k;
        if (dead) {
            float e = r * 0.28f;
            mg_line(eye, ex - e, ey - e, ex + e, ey + e, 1.4f, depth - 0.02f, ink);
            mg_line(eye, ex - e, ey + e, ex + e, ey - e, 1.4f, depth - 0.02f, ink);
        } else if (fmodf(S.t, 3.1f) < 0.12f) {
            mg_rect(eye, ex - r * 0.3f, ey - 0.6f, r * 0.6f, 1.4f, depth - 0.02f, ink);
        } else {
            mg_circle(eye, ex, ey, r * 0.36f, depth - 0.01f, MG_WHITE);
            mg_circle(eye, ex + fx * r * 0.14f, ey + fy * r * 0.14f, r * 0.18f, depth - 0.02f, ink);
        }
    }
    /* mouth: gapes when the target is close */
    int dist = abs(S.fx - S.bx[0]) + abs(S.fy - S.by[0]);
    float m = dist <= 2 && S.state == S_PLAY ? r * 0.32f : r * 0.16f;
    mg_circle(eye, x + fx * r * 0.7f, y + fy * r * 0.7f, m, depth - 0.02f, ink);
}

static void worm_colors(u32 *outline, u32 *head, u32 *tail)
{
    *outline = RGBA(90, 30, 70, 255);
    *head = RGBA(255, 150, 175, 255);
    *tail = RGBA(190, 80, 140, 255);
    if (S.shed > 0) {
        *outline = RGBA(70, 120, 170, 255);
        *head = RGBA(190, 240, 255, 255);
        *tail = RGBA(120, 180, 240, 255);
    }
    if (S.state == S_DYING && ((int)(S.state_t * 12) & 1))
        *head = *tail = RGBA(255, 80, 80, 255);
}

/* The worm as a chain of soft circles (in the capture). */
static void draw_worm(int eye)
{
    float xs[MAXLEN], ys[MAXLEN];
    bool dying = S.state == S_DYING;
    float sh = S.shed > 0 ? 0.35f + 0.15f * sinf(S.t * 10) : 1.0f;
    for (int i = 0; i < S.len; i++) {
        seg_pos(i, &xs[i], &ys[i]);
        if (dying) {   /* the worm unravels */
            u32 h = hash((u32)i * 31 + 7);
            float ang = (float)(h % 628) / 100.0f, k = S.state_t * S.state_t * 14;
            xs[i] += cosf(ang) * k;
            ys[i] += sinf(ang) * k;
        }
    }
    u32 outline, head, tail;
    worm_colors(&outline, &head, &tail);
    float a = S.shed > 0 ? 0.4f + sh * 0.4f : 1.0f;
    /* outlines (segments + joints), then fills, then highlights */
    for (int i = S.len - 1; i >= 0; i--) {
        float r = i == 0 ? 9.0f : 8.0f - 2.0f * i / S.len;
        float dp = i == 0 ? D_HEAD : D_WORM + 0.004f * i;
        mg_circle(eye, xs[i], ys[i], r + 1.5f, dp, rgba_alpha(outline, a));
        if (i > 0 && !dying)
            mg_circle(eye, (xs[i] + xs[i - 1]) / 2, (ys[i] + ys[i - 1]) / 2, r, dp, rgba_alpha(outline, a));
    }
    for (int i = S.len - 1; i >= 0; i--) {
        float r = i == 0 ? 9.0f : 8.0f - 2.0f * i / S.len;
        float dp = i == 0 ? D_HEAD : D_WORM + 0.004f * i;
        u32 c = mixc(head, tail, (float)i / (S.len - 1));
        if (i > 0 && !dying)
            mg_circle(eye, (xs[i] + xs[i - 1]) / 2, (ys[i] + ys[i - 1]) / 2, r - 1.5f, dp, rgba_alpha(c, a));
        mg_circle(eye, xs[i], ys[i], r, dp, rgba_alpha(c, a));
        mg_circle(eye, xs[i] - r * 0.3f, ys[i] - r * 0.35f, r * 0.3f, dp - 0.01f,
                  RGBA(255, 255, 255, (u32)(110 * a)));
    }
    draw_face(eye, xs[0], ys[0], view_dir(S.dir), 9, D_HEAD, dying);
}

/* ---- the board (into the capture) -------------------------------------------- */

static void draw_offscreen(int eye)
{
    float s = mg_shift(eye, D_BOARD);
    gfx_gradient(BX - 12 + s, BY - 12, FW + 24, FH + 24, RGBA(22, 16, 40, 255), RGBA(30, 18, 46, 255));
    for (int x = 1; x < GW; x++)
        mg_rect(eye, BX + x * CELL, BY, 1, FH, D_BOARD, RGBA(255, 255, 255, 16));
    for (int y = 1; y < GH; y++)
        mg_rect(eye, BX, BY + y * CELL, FW, 1, D_BOARD, RGBA(255, 255, 255, 16));
    /* the leak: dead pixels flicker on the board */
    u32 tick = (u32)(S.t * 4);
    int n = S.warn_t > 0 ? 14 : 5;
    for (int i = 0; i < n; i++) {
        u32 h = hash(tick * 131 + (u32)i * 977);
        float x = BX + (float)(h % FW), y = BY + (float)((h >> 10) % FH);
        u32 c = (h >> 20) & 1 ? RGBA(255, 60, 200, 60) : RGBA(60, 230, 255, 60);
        mg_rect(eye, x, y, 2 + (float)((h >> 24) % 7), 2, D_BOARD - 0.02f, c);
    }
    /* the shed skin, fading where it was left */
    if (S.skin_t > 0)
        for (int i = 0; i < S.skin_len; i++) {
            float x, y;
            cap_xy(S.skin_x[i], S.skin_y[i], &x, &y);
            mg_circle(eye, x, y, 8, D_WORM + 0.08f,
                      RGBA(200, 230, 255, (u32)(70 * clampf(S.skin_t / 2.0f, 0, 1))));
        }
    /* the apple being crunched */
    if (S.gulp_t > 0 && S.state != S_CROWNED) {
        float x, y;
        cap_xy(S.gulp_x, S.gulp_y, &x, &y);
        draw_crunch(eye, x, y, S.gulp_t / GULP_TIME, S.gulp_gold);
    }
    /* the target */
    if (S.state != S_CROWNED) {
        float x, y;
        cap_xy(S.fx, S.fy, &x, &y);
        if (S.crown) {
            float pop = clampf(S.target_t / 0.5f, 0, 1);
            float bob = sinf(S.t * 4) * 2;
            for (int k = 0; k < 4; k++) {
                float a = S.t * 2 + k * 1.571f;
                mg_rect(eye, x + cosf(a) * 13 - 1, y + sinf(a) * 13 - 1, 2, 2, D_CROWN, MG_WHITE);
            }
            draw_crown(eye, x, y + 3 + bob, 0.9f * pop + 0.6f * (1 - pop) * sinf(pop * 9), D_CROWN, pop);
        } else {
            float pop = clampf(S.target_t / 0.25f, 0, 1);
            if (S.warn_t > 0) {   /* still ripening: where it will be, and a dial */
                float k = 1 - S.warn_t / WARN_TIME;
                draw_apple(eye, x, y, (0.55f + 0.3f * k) * pop, D_FOOD, false, 0.7f);
                for (int i = 0; i < 8; i++) {
                    float an = -1.5708f + i * 0.785f;
                    bool lit = i < (int)(k * 8.0f + 0.999f);
                    mg_rect(eye, x + cosf(an) * 12 - 1.5f, y + sinf(an) * 12 - 1.5f, 3, 3, D_FOOD - 0.02f,
                            lit ? RGBA(255, 220, 110, 230) : RGBA(255, 255, 255, 60));
                }
            } else
                draw_apple(eye, x, y + apple_bob(), 0.4f + 0.6f * pop, D_FOOD, S.golden, 1);
        }
    }
    draw_worm(eye);
}

/* ---- the view (from capture pieces) ----------------------------------------------- */

static void part(int eye, float sx, float sy, float sw, float sh, float dx, float dy, float dw, float dh, float a)
{
    gfx_draw_capture_part(eye, sx, sy, sw, sh, dx, dy, dw, dh, a);
}

static void ghost_entities(int eye, float ox, float oy, u32 c)
{
    for (int i = 0; i < S.len; i++) {
        float x, y;
        seg_pos(i, &x, &y);
        mg_circle(eye, x + ox, y + oy, i ? 7.0f : 8.5f, D_WORM, c);
    }
    float x, y;
    cap_xy(S.fx, S.fy, &x, &y);
    x += ox;
    y += oy;
    if (S.crown)
        mg_tri(eye, x - 8, y + 4, x + 8, y + 4, x, y - 8, D_CROWN, c);
    else
        mg_circle(eye, x, y, 6, D_FOOD, c);
}

static void draw_field(int eye)
{
    float env = filter_env();
    switch (S.filter) {
    case F_NONE:
    case F_MIRROR:   /* reflected in the capture already */
    case F_FLIP:
        part(eye, BX, BY, FW, FH, BX, BY, FW, FH, 1);
        break;
    case F_WAVE:     /* 18 rows sway sideways by up to half a cell */
        for (int k = 0; k < FH / WAVE_H; k++) {
            float y0 = BY + k * WAVE_H;
            int o = wave_off(k);
            if (o > 0) {
                part(eye, BX, y0, FW - o, WAVE_H, BX + o, y0, FW - o, WAVE_H, 1);
                mg_rect(eye, BX, y0, o, WAVE_H, D_BOARD, RGBA(16, 10, 30, 255));
            } else if (o < 0) {
                o = -o;
                part(eye, BX + o, y0, FW - o, WAVE_H, BX, y0, FW - o, WAVE_H, 1);
                mg_rect(eye, BX + FW - o, y0, o, WAVE_H, D_BOARD, RGBA(16, 10, 30, 255));
            } else {
                part(eye, BX, y0, FW, WAVE_H, BX, y0, FW, WAVE_H, 1);
            }
        }
        break;
    case F_CHROMA: {
        part(eye, BX, BY, FW, FH, BX, BY, FW, FH, 1);
        int gx = (int)(env * (6 + 3 * sinf(S.t * 1.3f))), gy = (int)(env * 4 * cosf(S.t * 1.1f));
        int ay = abs(gy);
        part(eye, BX, BY + (gy < 0 ? ay : 0), FW - gx, FH - ay, BX + gx, BY + (gy > 0 ? ay : 0), FW - gx,
             FH - ay, 0.3f * env);
        float ox = env * (4 + 2 * sinf(S.t * 2.1f)), oy = env * 2 * cosf(S.t * 1.7f);
        ghost_entities(eye, ox, oy, RGBA(255, 40, 70, 80));
        ghost_entities(eye, -ox, -oy, RGBA(40, 220, 255, 80));
        break;
    }
    case F_SLICES: { /* five wide slices, shuffled once per stage */
        for (int i = 0; i < NSL; i++)
            part(eye, BX + S.perm[i] * SW, BY, SW, FH, BX + i * SW, BY, SW, FH, 1);
        for (int i = 1; i < NSL; i++)
            mg_rect(eye, BX + i * SW - 1, BY, 2, FH, D_BOARD - 0.05f, RGBA(80, 230, 255, 120));
        char num[4];
        for (int i = 0; i < NSL; i++) {
            float x0 = BX + i * SW;
            /* the real walls glow red wherever the view puts them */
            if (S.perm[i] == 0)
                mg_rect(eye, x0 - 1.5f, BY, 3, FH, D_BOARD - 0.07f, RGBA(255, 60, 70, 230));
            if (S.perm[i] == NSL - 1)
                mg_rect(eye, x0 + SW - 1.5f, BY, 3, FH, D_BOARD - 0.07f, RGBA(255, 60, 70, 230));
            mg_rect(eye, x0 + 3, BY + FH - 4, SW - 6, 3, D_BOARD - 0.06f, rgba_alpha(SLC[S.perm[i]], 0.8f));
            mg_rect(eye, x0 + SW / 2.0f - 8, BY + 1, 16, 13, D_MARK + 0.04f, RGBA(0, 0, 0, 150));
            snprintf(num, sizeof(num), "%d", S.perm[i] + 1);
            mg_text_centered(eye, num, x0 + SW / 2.0f, BY + 0.5f, 0.42f, D_MARK + 0.02f, SLC[S.perm[i]]);
        }
        break;
    }
    case F_QUAD:     /* the board shifted by half both ways: the walls cross the middle */
        for (int q = 0; q < 4; q++) {
            int qx = q & 1, qy = q >> 1;
            part(eye, BX + qx * FW / 2, BY + qy * FH / 2, FW / 2, FH / 2, BX + (1 - qx) * FW / 2,
                 BY + (1 - qy) * FH / 2, FW / 2, FH / 2, 1);
        }
        mg_rect(eye, BX + FW / 2 - 1.5f, BY, 3, FH, D_BOARD - 0.07f, RGBA(255, 60, 70, 230));
        mg_rect(eye, BX, BY + FH / 2 - 1.5f, FW, 3, D_BOARD - 0.07f, RGBA(255, 60, 70, 230));
        break;
    }
    /* switching glitch: a few torn bands */
    if (S.glitch > 0) {
        u32 tick = (u32)(S.t * 30);
        for (int i = 0; i < 5; i++) {
            u32 h = hash(tick * 53 + (u32)i * 7919);
            int bh = 6 + (int)(h % 14), y0 = BY + (int)((h >> 8) % (FH - bh));
            int o = (int)((float)((int)((h >> 16) % 61) - 30) * S.glitch);
            int sx = o > 0 ? BX : BX - o, w = FW - abs(o);
            part(eye, (float)sx, (float)y0, (float)w, (float)bh, (float)(sx + o), (float)y0, (float)w,
                 (float)bh, 0.9f);
            if (i < 2)
                mg_rect(eye, BX, (float)y0, FW, 2, -0.05f,
                        (h >> 4) & 1 ? RGBA(255, 60, 200, (u32)(160 * S.glitch))
                                     : RGBA(60, 230, 255, (u32)(160 * S.glitch)));
        }
    }
}

/* The head redrawn crisp (outside the capture), facing `vd` as seen. */
static void draw_head(int eye, float x, float y, int vd, float depth)
{
    u32 outline, head, tail;
    worm_colors(&outline, &head, &tail);
    mg_circle(eye, x, y, 10.5f, depth + 0.01f, outline);
    mg_circle(eye, x, y, 9, depth, head);
    mg_circle(eye, x - 2.7f, y - 3.1f, 2.7f, depth - 0.005f, RGBA(255, 255, 255, 110));
    draw_face(eye, x, y, vd, 9, depth, S.state == S_DYING);
}

/* Under a filter: the head and the target, undistorted, where the view
 * shows them; the next cell on split views; a heading arrow at first. */
static void draw_markers(int eye)
{
    float pulse = 0.5f + 0.5f * sinf(S.t * 7);
    float x, y;
    cap_xy(S.fx, S.fy, &x, &y);
    view_pos(x, y, &x, &y);
    mg_circle(eye, x, y, 13 + pulse * 1.5f, D_MARK + 0.03f,
              S.crown ? RGBA(255, 220, 120, (u32)(50 + 50 * pulse)) : RGBA(255, 255, 255, (u32)(35 + 40 * pulse)));
    if (S.crown)
        draw_crown(eye, x, y + 3, 0.8f, D_MARK - 0.02f, 1);
    else
        draw_apple(eye, x, y + apple_bob(), clampf(S.target_t / 0.25f, 0.4f, 1), D_MARK, S.golden, 1);

    if (S.state != S_PLAY)
        return;
    int nd = S.nq ? S.queue[0] : S.dir;
    if (S.filter == F_SLICES || S.filter == F_QUAD) {
        int nx = S.bx[0] + DX[nd], ny = S.by[0] + DY[nd];
        if (nx >= 0 && nx < GW && ny >= 0 && ny < GH) {
            cap_xy(nx, ny, &x, &y);
            view_pos(x, y, &x, &y);
            mg_rect(eye, x - 5, y - 5, 10, 10, D_MARK + 0.02f, RGBA(255, 220, 120, (u32)(50 + 70 * pulse)));
            mg_rect(eye, x - 1.5f, y - 1.5f, 3, 3, D_MARK, RGBA(255, 240, 180, 230));
        }
    }
    float hx, hy;
    seg_pos(0, &hx, &hy);
    view_pos(hx, hy, &hx, &hy);
    mg_circle(eye, hx, hy, 13.5f, D_MARK + 0.03f, RGBA(255, 230, 120, (u32)(60 + 60 * pulse)));
    int vd = view_dir(nd);
    draw_head(eye, hx, hy, vd, D_MARK - 0.02f);
    if (S.stage_t < 2.5f) {   /* "this way" while you get your bearings */
        float a = clampf((2.5f - S.stage_t) / 0.5f, 0, 1) * (0.6f + 0.4f * pulse);
        float dx = (float)DX[vd], dy = (float)DY[vd], px = -dy, py = dx;
        float x0 = hx + dx * 15, y0 = hy + dy * 15, x1 = hx + dx * 30, y1 = hy + dy * 30;
        u32 c = RGBA(255, 220, 110, (u32)(230 * a));
        mg_line(eye, x0, y0, x1, y1, 4, D_MARK - 0.04f, c);
        mg_tri(eye, x1 + dx * 9, y1 + dy * 9, x1 + px * 7, y1 + py * 7, x1 - px * 7, y1 - py * 7,
               D_MARK - 0.04f, c);
    }
}

/* ---- the finale: the crowned worm and its cheering crowd ---------------------------- */

#define KX 200.0f
#define KY 92.0f
#define KN 9

static void king_seg(int i, float t, float *x, float *y, float *r)
{
    float k = (float)i / (KN - 1);
    *x = KX + sinf(i * 0.8f - 0.4f) * (4 + i * 2.6f) + sinf(t * 3 - i * 0.6f) * 2.5f * k;
    *y = KY + i * 9.5f;
    *r = 18 - i * 1.0f;
}

static void crowd_worm(int eye, float x, float base, float s, float depth, u32 col, float ph, float t,
                       float a, bool flag)
{
    float bounce = fabsf(sinf(t * 6.5f + ph));
    float hop = bounce * 8 * s, sway = sinf(t * 3.3f + ph * 1.7f) * 3 * s;
    u32 dark = mixc(col, RGBA(40, 16, 36, 255), 0.4f), lite = mixc(col, MG_WHITE, 0.3f);
    u32 ink = rgba_alpha(RGBA(40, 16, 36, 255), a);
    float y0 = base - 5 * s - hop * 0.3f, y1 = base - 14 * s - hop * 0.65f, y2 = base - 24 * s - hop;
    float x1 = x + sway * 0.5f, x2 = x + sway;
    mg_circle(eye, x, y0, 7 * s, depth + 0.02f, rgba_alpha(dark, a));
    mg_circle(eye, x1, y1, 6.5f * s, depth + 0.01f, rgba_alpha(col, a));
    mg_circle(eye, x2, y2, 7.5f * s, depth, rgba_alpha(lite, a));
    mg_circle(eye, x2 - 2.6f * s, y2 - 1.6f * s, 1.3f * s, depth - 0.01f, ink);
    mg_circle(eye, x2 + 2.6f * s, y2 - 1.6f * s, 1.3f * s, depth - 0.01f, ink);
    mg_circle(eye, x2, y2 + 2.8f * s, (1.2f + 1.6f * bounce) * s, depth - 0.01f,
              rgba_alpha(RGBA(120, 20, 50, 255), a));
    if (flag) {   /* a little pennant, waved */
        float tx = x2 + 9 * s, ty = y2 - 14 * s, w = sinf(t * 9 + ph) * 2 * s;
        mg_line(eye, x2 + 6 * s, y2 + 4 * s, tx, ty, 1.2f, depth - 0.02f, rgba_alpha(RGBA(230, 220, 200, 255), a));
        mg_tri(eye, tx, ty, tx, ty + 6 * s, tx + 10 * s + w, ty + 2 * s + w * 0.5f, depth - 0.02f,
               rgba_alpha((hash((u32)(ph * 100)) & 1) ? MG_GOLD : RGBA(255, 110, 200, 255), a));
    }
}

static const u32 CROWD_COL[6] = {
    RGBA(255, 150, 175, 255), RGBA(140, 230, 180, 255), RGBA(255, 225, 120, 255),
    RGBA(140, 200, 255, 255), RGBA(205, 160, 255, 255), RGBA(255, 180, 130, 255),
};

static void crowd_row(int eye, int n, float x0, float dx, float base, float s, float depth, float t,
                      float a, u32 salt)
{
    for (int i = 0; i < n; i++) {
        u32 h = hash((u32)i * 7919u + salt);
        float x = x0 + i * dx + (float)((int)(h % 13) - 6);
        crowd_worm(eye, x, base + (float)((h >> 8) % 5), s, depth, CROWD_COL[(h >> 12) % 6],
                   (float)(h % 628) / 100.0f, t, a, (h >> 16) % 3 == 0);
    }
}

static void draw_final(int eye)
{
    float t = S.state_t;
    part(eye, BX, BY, FW, FH, BX, BY, FW, FH, 1);
    gfx_rect(0, 0, TOP_W, TOP_H, RGBA(8, 4, 20, (u32)clampf(t * 400, 0, 230)));
    float ap = clampf((t - 0.15f) / 0.4f, 0, 1);
    if (ap <= 0)
        return;
    /* light rays behind the king */
    for (int i = 0; i < 8; i++) {
        float a = t * 0.4f + i * 0.785f;
        mg_tri(eye, KX, KY, KX + cosf(a) * 230, KY + sinf(a) * 230, KX + cosf(a + 0.22f) * 230,
               KY + sinf(a + 0.22f) * 230, 0.5f, RGBA(255, 210, 110, (u32)(26 * ap)));
    }
    /* the back of the crowd, then the dais and the king */
    crowd_row(eye, 10, 22, 40, 196, 0.62f, 0.32f, t, ap, 11);
    mg_rect(eye, KX - 36, 170, 72, 16, 0.08f, rgba_alpha(RGBA(90, 50, 120, 255), ap));
    mg_rect(eye, KX - 36, 170, 72, 3, 0.07f, rgba_alpha(MG_GOLD, ap));
    u32 head = RGBA(255, 150, 175, 255), tail = RGBA(190, 80, 140, 255);
    float xs[KN], ys[KN], rs[KN];
    for (int i = 0; i < KN; i++)
        king_seg(i, t, &xs[i], &ys[i], &rs[i]);
    for (int i = KN - 1; i >= 0; i--)
        mg_circle(eye, xs[i], ys[i], rs[i] + 2.5f, -0.3f + i * 0.03f, rgba_alpha(RGBA(90, 30, 70, 255), ap));
    for (int i = KN - 1; i >= 0; i--) {
        float dp = -0.3f + i * 0.03f;
        mg_circle(eye, xs[i], ys[i], rs[i], dp, rgba_alpha(mixc(head, tail, i / (float)(KN - 1)), ap));
        mg_circle(eye, xs[i] - rs[i] * 0.3f, ys[i] - rs[i] * 0.35f, rs[i] * 0.3f, dp - 0.01f,
                  RGBA(255, 255, 255, (u32)(110 * ap)));
    }
    /* proud face */
    u32 ink = rgba_alpha(RGBA(40, 16, 36, 255), ap);
    float hx = xs[0], hy = ys[0];
    for (int k = -1; k <= 1; k += 2) {
        float ex = hx + k * 6.5f, ey = hy - 3;
        mg_circle(eye, ex, ey, 4.3f, -0.34f, rgba_alpha(MG_WHITE, ap));
        mg_circle(eye, ex, ey - 1.2f, 2.1f, -0.35f, ink);
        mg_circle(eye, ex + k * 2.5f, ey + 7, 2.8f, -0.33f, RGBA(255, 110, 140, (u32)(150 * ap)));
    }
    mg_circle(eye, hx, hy + 7, 4, -0.34f, ink);
    mg_circle(eye, hx, hy + 5, 4.3f, -0.345f, rgba_alpha(head, ap));
    /* the crown drops onto the head */
    float land = clampf(t / 0.8f, 0, 1);
    float e = 1 - (1 - land) * (1 - land);
    float cy = lerpf(-30, hy - rs[0] + 2, e) + (land >= 1 ? sinf(t * 2) * 1.5f : 0);
    draw_crown(eye, hx, cy, 2.3f, -0.42f, 1);
    if (land >= 1)
        for (int i = 0; i < 6; i++) {
            float a = t * 1.5f + i * 1.047f, r = 32 + 4 * sinf(t * 5 + i);
            mg_rect(eye, hx + cosf(a) * r - 1.5f, cy - 8 + sinf(a) * r * 0.6f - 1.5f, 3, 3, -0.38f,
                    RGBA(255, 255, 220, 220));
        }
    /* the front of the crowd, popping out */
    crowd_row(eye, 9, 22, 45, 222, 0.82f, 0.1f, t, ap, 23);
    crowd_row(eye, 7, 30, 57, 250, 1.1f, -0.22f, t, ap, 37);
    /* tiny crowns tossed in the air, and confetti */
    for (int i = 0; i < 5; i++) {
        float tt = t - (0.9f + i * 0.45f);
        if (tt < 0)
            continue;
        float x = 50 + i * 75 + ((i & 1) ? -22 : 22) * tt, y = 205 - 190 * tt + 0.5f * 300 * tt * tt;
        if (y < 250)
            mini_crown(eye, x, y, 1.1f, -0.15f, MG_GOLD);
    }
    static const u32 CONF[5] = {RGBA(255, 210, 110, 255), RGBA(255, 90, 200, 255), RGBA(90, 220, 255, 255),
                                RGBA(140, 240, 140, 255), RGBA(255, 255, 255, 255)};
    float ct = t - 0.8f;
    if (ct > 0)
        for (int i = 0; i < 30; i++) {
            u32 h = hash((u32)i * 2654435761u + 5);
            float y = -10 - (float)(h % 140) + ct * (60 + (float)((h >> 8) % 60));
            if (y < -4 || y > TOP_H)
                continue;
            float x = (float)((h >> 4) % TOP_W) + sinf(ct * 3 + i) * 8;
            bool wide = sinf(ct * 8 + i * 1.3f) > 0;
            mg_rect(eye, x, y, wide ? 4 : 2, wide ? 2 : 4, -0.35f + (float)((h >> 16) % 70) / 100.0f,
                    CONF[(h >> 20) % 5]);
        }
    /* the rating */
    char buf[64];
    if (t >= 0.8f) {
        const char *cheer = "LONG LIVE THE WORM KING!";
        mg_text_centered(eye, cheer, TOP_W / 2 + 1.5f, 7.5f, 0.62f, -0.18f, RGBA(0, 0, 0, 200));
        mg_text_centered(eye, cheer, TOP_W / 2, 6, 0.62f, -0.2f, MG_GOLD);
    }
    mg_text_centered(eye, "Route", 64, 52, 0.45f, -0.1f, rgba_alpha(RGBA(200, 200, 230, 255), ap));
    snprintf(buf, sizeof(buf), "%d%%", route_pct());
    mg_text_centered(eye, buf, 64, 68, 0.7f, -0.12f, rgba_alpha(MG_WHITE, ap));
    mg_text_centered(eye, "of shortest", 64, 94, 0.42f, -0.1f, rgba_alpha(RGBA(200, 200, 230, 255), ap));
    if (t >= 1.2f) {
        float pop = clampf((t - 1.2f) / 0.25f, 0, 1);
        snprintf(buf, sizeof(buf), "%d%%", score());
        mg_text_centered(eye, buf, 336, 50, 0.7f + 0.35f * pop, -0.3f, MG_WHITE);
        mg_text_centered(eye, rating_name(score()), 336, 96, 0.42f, -0.2f, MG_GOLD);
    }
    if (t >= 1.6f)
        mg_text_centered(eye, "A: continue", 336, 120, 0.4f, -0.05f, RGBA(200, 200, 230, 255));
}

/* Announcements sit at the top of the board, or at the bottom when the
 * head or the target is up there (and not down there). */
static float banner_y(void)
{
    float hx, hy, ax, ay;
    seg_pos(0, &hx, &hy);
    view_pos(hx, hy, &hx, &hy);
    cap_xy(S.fx, S.fy, &ax, &ay);
    view_pos(ax, ay, &ax, &ay);
    int top = 2 * (hy < BY + 76) + (ay < BY + 76);
    int bottom = 2 * (hy > BY + FH - 70) + (ay > BY + FH - 70);
    return bottom < top ? BY + FH - 54 : BY + 8;
}

static void shadow_text(int eye, const char *s, float y, float scale, float depth, u32 c)
{
    mg_text_centered(eye, s, TOP_W / 2 + 1.5f, y + 1.5f, scale, depth + 0.02f, RGBA(0, 0, 0, 210));
    mg_text_centered(eye, s, TOP_W / 2, y, scale, depth, c);
}

static void draw_top(int eye)
{
    mg_sky(eye, RGBA(10, 8, 26, 255), RGBA(36, 18, 50, 255));
    for (int i = 0; i < 18; i++)
        mg_rect(eye, (float)((i * 97 + 13) % TOP_W), (float)((i * 61 + 7) % TOP_H), 2, 2, 1.0f,
                RGBA(255, 255, 255, 60 + (i % 3) * 40));
    if (S.state == S_CROWNED) {
        draw_final(eye);
        return;
    }
    /* the frame, flickering during a warning */
    u32 frame = RGBA(70, 50, 110, 255);
    if (S.warn_t > 0 && ((int)(S.t * 8) & 1))
        frame = FCOL[S.warn_filter];
    else if (S.filter == F_QUAD)
        frame = RGBA(60, 200, 230, 255);   /* the edges are open: you come out the far side */
    else if (S.filter != F_NONE)
        frame = mixc(FCOL[S.filter], RGBA(70, 50, 110, 255), 0.45f);
    else if (S.shed > 0)
        frame = RGBA(80, 160, 210, 255);
    mg_rect(eye, BX - 5, BY - 5, FW + 10, FH + 10, D_BOARD + 0.02f, frame);
    draw_field(eye);
    if (S.filter != F_NONE)
        draw_markers(eye);

    /* the top line: apples, stage or skin, route */
    char buf[64];
    if (S.crown)
        snprintf(buf, sizeof(buf), "The crown is out!");
    else
        snprintf(buf, sizeof(buf), "Apples %d/%d", S.stage_apples < need() ? S.stage_apples : need(), need());
    mg_text(eye, buf, BX, 2, 0.42f, -0.05f, S.crown ? MG_GOLD : MG_WHITE);
    snprintf(buf, sizeof(buf), "Route %d%%", route_pct());
    mg_text(eye, buf, BX + FW - gfx_text_width(buf, 0.42f), 2, 0.42f, -0.05f, RGBA(200, 200, 230, 255));
    if (S.shed > 0) {
        snprintf(buf, sizeof(buf), "SKIN SHED %.1f", fmaxf(0, S.shed));
        mg_text_centered(eye, buf, TOP_W / 2, 2, 0.42f, -0.1f, RGBA(150, 230, 255, 255));
    } else if (S.stage < NSTAGES) {
        snprintf(buf, sizeof(buf), "%d/%d %s", S.stage + 1, NSTAGES, FNAME[STAGES[S.stage].filter]);
        mg_text_centered(eye, buf, TOP_W / 2, 2, 0.42f, -0.1f,
                         S.filter != F_NONE ? FCOL[S.filter] : RGBA(200, 200, 230, 255));
    }

    /* announcements: shadowed text only, so the board stays readable */
    float ty = banner_y();
    if (S.warn_t > 0) {
        u32 c = ((int)(S.t * 8) & 1) ? FCOL[S.warn_filter] : MG_WHITE;
        snprintf(buf, sizeof(buf), "NEXT: %s in %d", FNAME[S.warn_filter], (int)ceilf(S.warn_t));
        shadow_text(eye, buf, ty, 0.62f, -0.3f, c);
        shadow_text(eye, FHINT[S.warn_filter], ty + 24, 0.45f, -0.28f, MG_WHITE);
    } else if (S.filter != F_NONE && S.stage_t < 2.5f) {
        shadow_text(eye, FHINT[S.filter], ty, 0.45f, -0.28f, MG_WHITE);
    } else if (S.tired_t > 0 && S.banner_t <= 0) {
        shadow_text(eye, "The leak tires... the view clears.", ty, 0.5f, -0.28f, RGBA(180, 230, 255, 255));
    }
    if (S.banner_t > 0)
        shadow_text(eye, "THE CROWN IS OUT - EAT IT!", ty, 0.62f, -0.3f, MG_GOLD);
    if (S.t < GRACE + 0.4f && S.state == S_PLAY) {
        shadow_text(eye, S.t < GRACE ? "Ready..." : "GO!", BY + 40, 0.8f, -0.3f, MG_GOLD);
        shadow_text(eye, "Eat the apples!", BY + 72, 0.5f, -0.25f, MG_WHITE);
    }
    if (S.state == S_DYING) {
        gfx_rect(0, 0, TOP_W, TOP_H, RGBA(255, 40, 60, (u32)clampf(120 - S.state_t * 120, 0, 120)));
        const char *msg = S.died_wall ? "The worm hit the edge of the world." : "The worm bit itself.";
        shadow_text(eye, msg, BY + FH / 2.0f - 12, 0.6f, -0.3f, MG_WHITE);
    }
}

/* ---- bottom screen ------------------------------------------------------------- */

static void draw_minimap(float mx, float my)
{
    const float C = 7;
    bool on = S.filter != F_NONE;
    gfx_rect(mx - 2, my - 2, GW * C + 4, GH * C + 4, on ? FCOL[S.filter] : RGBA(70, 50, 110, 255));
    gfx_rect(mx, my, GW * C, GH * C, RGBA(22, 16, 40, 255));
    if (S.state != S_CROWNED) {
        float x = mx + S.fx * C, y = my + S.fy * C;
        if (S.crown) {
            gfx_triangle(x, y + C, x + C, y + C, x + C / 2, y, MG_GOLD);
        } else {
            gfx_rect(x + 1, y + 1, C - 2, C - 2, S.golden ? MG_GOLD : RGBA(230, 40, 55, 255));
            gfx_rect(x + C / 2, y, 2, 2, RGBA(110, 210, 90, 255));
        }
    }
    u32 body = S.shed > 0 ? RGBA(120, 180, 240, 255) : RGBA(220, 110, 160, 255);
    for (int i = S.len - 1; i >= 0; i--)
        gfx_rect(mx + S.bx[i] * C + 0.5f, my + S.by[i] * C + 0.5f, C - 1, C - 1,
                 i ? body : RGBA(255, 235, 240, 255));
    gfx_text(on ? "True view" : "Board", mx, my + GH * C + 3, 0.4f,
             on ? FCOL[S.filter] : RGBA(150, 150, 170, 255));
}

static void draw_bottom(void)
{
    char buf[96];
    gfx_text("Crown of the Worm", 12, 4, 0.55f, MG_GOLD);
    bool crowned = S.state == S_CROWNED;
    if (crowned)
        snprintf(buf, sizeof(buf), "Long live the Worm King!");
    else if (S.stage >= NSTAGES)
        snprintf(buf, sizeof(buf), "The crown is out - eat it!");
    else
        snprintf(buf, sizeof(buf), "Stage %d/%d: %s", S.stage + 1, NSTAGES, FNAME[STAGES[S.stage].filter]);
    gfx_text(buf, 12, 26, 0.47f, crowned || S.stage >= NSTAGES ? MG_GOLD : MG_WHITE);
    if (!crowned && S.stage < NSTAGES) {
        snprintf(buf, sizeof(buf), "Apples %d/%d", S.stage_apples < need() ? S.stage_apples : need(), need());
        gfx_text(buf, 308 - gfx_text_width(buf, 0.47f), 26, 0.47f, MG_WHITE);
    }
    /* the series: one chip per stage, then the crown */
    for (int i = 0; i < NSTAGES; i++) {
        float x = 12 + i * 24;
        u32 c = FCOL[STAGES[i].filter];
        bool done = crowned || i < S.stage;
        gfx_rect(x, 46, 18, 14, done ? c : i == S.stage ? rgba_alpha(c, 0.5f) : RGBA(255, 255, 255, 30));
        if (i == S.stage && !crowned)
            gfx_rect(x - 1, 62, 20, 2, MG_WHITE);
    }
    float cx = 12 + NSTAGES * 24 + 10, cy = 60;
    u32 cc = S.crown || crowned ? MG_GOLD : RGBA(255, 210, 110, 70);
    gfx_rect(cx - 9, cy - 4, 18, 4, cc);
    gfx_triangle(cx - 9, cy - 4, cx - 3, cy - 4, cx - 8, cy - 13, cc);
    gfx_triangle(cx - 4, cy - 4, cx + 4, cy - 4, cx, cy - 15, cc);
    gfx_triangle(cx + 9, cy - 4, cx + 3, cy - 4, cx + 8, cy - 13, cc);

    if (S.warn_t > 0) {
        snprintf(buf, sizeof(buf), "Next: %s in %d s", FNAME[S.warn_filter], (int)ceilf(S.warn_t));
        gfx_text(buf, 12, 68, 0.42f, FCOL[S.warn_filter]);
    } else {
        const char *h = crowned ? "The crowd goes wild." : S.stage >= NSTAGES ? "Eat the crown to end the run."
                      : FHINT[S.filter];
        gfx_text(h, 12, 68, 0.42f, RGBA(190, 190, 210, 255));
    }

    draw_minimap(12, 88);

    /* efficiency: shortest / actual over all targets so far */
    float rx = 166;
    float eff = S.sum_act > 0 ? (float)S.sum_min / S.sum_act : 1.0f;
    snprintf(buf, sizeof(buf), "Route efficiency %d%%", (int)(eff * 100 + 0.5f));
    gfx_text(buf, rx, 86, 0.42f, MG_WHITE);
    gfx_rect(rx, 102, 142, 8, RGBA(255, 255, 255, 40));
    u32 ec = eff >= 0.85f ? RGBA(120, 230, 150, 255) : eff >= 0.6f ? RGBA(255, 210, 110, 255)
                                                                 : RGBA(240, 110, 100, 255);
    gfx_rect(rx, 102, 142 * clampf(eff, 0, 1), 8, ec);
    gfx_rect(rx + 142 * 0.85f, 99, 1, 14, RGBA(255, 255, 255, 140));
    snprintf(buf, sizeof(buf), "This bite: %d steps / %d", S.cur_steps, S.cur_min);
    gfx_text(buf, rx, 114, 0.4f, RGBA(200, 200, 230, 255));

    gfx_text(S.boost > 0 ? "A boost: GO" : S.boost_cd > 0 ? "A boost: recharging" : "A boost: ready", rx, 134,
             0.42f, MG_WHITE);
    gfx_rect(rx, 150, 142, 6, RGBA(255, 255, 255, 40));
    gfx_rect(rx, 150, 142 * clampf(1 - S.boost_cd / BOOST_COOLDOWN, 0, 1), 6, RGBA(120, 200, 255, 255));
    float y = 162;
    if (S.shed > 0) {
        snprintf(buf, sizeof(buf), "Skin shed: %.1f s", fmaxf(0, S.shed));
        gfx_text(buf, rx, y, 0.42f, RGBA(150, 230, 255, 255));
        y += 16;
    }
    if (S.golden && S.state == S_PLAY) {
        snprintf(buf, sizeof(buf), "Golden apple: %d s", (int)ceilf(S.gold_t));
        gfx_text(buf, rx, y, 0.42f, MG_GOLD);
        y += 16;
    }
    if (S.filter == F_MIRROR || S.filter == F_FLIP)
        gfx_text("D-pad follows the view", rx, y, 0.4f, FCOL[S.filter]);
    gfx_text("START: pause", 12, 216, 0.42f, RGBA(180, 180, 200, 255));
}

/* ---- bot ------------------------------------------------------------------------- */

/* Reachable cells after a move, -1 if the move kills. */
static int bot_area_after(int k)
{
    static u8 tx[MAXLEN], ty[MAXLEN];
    int nx = S.bx[0] + DX[k], ny = S.by[0] + DY[k];
    if (nx < 0 || nx >= GW || ny < 0 || ny >= GH)
        return -1;
    bool grow = nx == S.fx && ny == S.fy && S.warn_t <= 0;
    if (on_body(nx, ny, 0, grow ? S.len : S.len - 1))
        return -1;
    int len = S.len + (grow && S.len < MAXLEN);
    tx[0] = (u8)nx;
    ty[0] = (u8)ny;
    for (int j = 1; j < len; j++) {
        tx[j] = S.bx[j - 1];
        ty[j] = S.by[j - 1];
    }
    bfs(tx, ty, len, false);
    int area = 0;
    for (int c = 0; c < NC; c++)
        area += bdist[c] >= 0;
    return area;
}

/* The true direction the bot wants, -1 for straight on. */
static int bot_choice(void)
{
    bfs(S.bx, S.by, S.len, false);
    int tc = S.fy * GW + S.fx;
    int want = bdist[tc] >= 0 && S.warn_t <= 0 ? bfirst[tc] : -1;   /* wander while it ripens */
    int best = S.dir, besta = -2, wanta = -1;
    for (int k = 0; k < 4; k++) {
        if (k == (S.dir + 2) % 4)
            continue;
        int a = bot_area_after(k);
        if (k == want)
            wanta = a;
        if (a > besta) {
            besta = a;
            best = k;
        }
    }
    int d = want >= 0 && wanta >= S.len + 4 ? want : best;
    return d == S.dir ? -1 : d;
}

static void bot(Input *in, float t)
{
    if (t > 6.0f && !MG.cheat_used && S.state == S_PLAY)
        in->down |= KEY_L_;
    if (S.state == S_CROWNED && S.state_t > 3.6f)
        in->down |= KEY_A_;
    if (S.state != S_PLAY || S.nq || t < GRACE)
        return;
    int d = bot_choice();
    if (d >= 0)
        in->down |= DIR_KEY[view_dir(d)];   /* press it as seen */
    bfs(S.bx, S.by, S.len, false);
    if (bdist[S.fy * GW + S.fx] > 6 && S.boost_cd <= 0)
        in->down |= KEY_A_;
}

static bool can_cheat(void) { return S.state == S_PLAY; }

const MiniGame MG_SNAKE = {
    .id = "snake",
    .title = "Crown of the Worm",
    .rules = "Steer the worm to the apples. Golden\n"
             "ones count twice, but only for 8 s.\n"
             "The leak bends the view, stage by stage:\n"
             "your head and the apple stay marked.\n"
             "After the last stage, eat the crown!\n"
             "Score: shortest route vs. steps taken.",
    .controls = "D-pad / Circle Pad: steer\n"
                "A: boost (short burst, recharges)\n"
                "START: pause\n"
                "\n"
                "Mirror and Upside Down: the D-pad\n"
                "follows the view (right goes right).",
    .cheat = "Shed your skin: pass through\nyourself and wrap at walls for 6 s",
    .music = "snake",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .draw_offscreen = draw_offscreen,
    .score = score,
    .verdict = verdict,
    .can_cheat = can_cheat,
    .bot = bot,
};
