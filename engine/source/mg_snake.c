/* Crown of the Worm: snake on a 20x12 board while the leak bends the view.
 *
 * Eat glitch pixels; after FOODS_TO_CROWN of them the crown appears, and
 * eating it ends the run. Every few foods the leak runs a view filter for
 * 6-10 s (split view, wave, mirror, shuffled slices, upside down, zoom
 * wobble, chromatic split). The board is drawn into the eye's capture
 * (draw_offscreen) and draw_top re-assembles it from capture pieces.
 *
 * Score: for every food and the crown we record the shortest path at the
 * moment it spawned (a BFS that knows the body's tail moves away over time)
 * and the steps the player actually took. With r = sum(actual) / sum(min):
 *     tempo = 1 / (1 + (max(0, r - 1.05) / 0.9) ^ 1.6)
 * Crowned: 30 + 70 * tempo. Died: 45 * eaten/13 * (0.6 + 0.4 * tempo). */

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
#define FOODS_TO_CROWN 12
#define TARGETS (FOODS_TO_CROWN + 1)
#define GRACE 1.0f
#define SHED_TIME 6.0f
#define BOOST_TIME 1.0f
#define BOOST_COOLDOWN 3.0f

#define D_BOARD 0.25f
#define D_FOOD (-0.05f)
#define D_WORM (-0.15f)
#define D_HEAD (-0.2f)
#define D_CROWN (-0.3f)

enum { DIR_R, DIR_D, DIR_L, DIR_U };
static const int DX[4] = {1, 0, -1, 0}, DY[4] = {0, 1, 0, -1};
static const u32 DIR_KEY[4] = {KEY_RIGHT_, KEY_DOWN_, KEY_LEFT_, KEY_UP_};

enum { F_NONE, F_QUAD, F_WAVE, F_MIRROR, F_SLICES, F_FLIP, F_ZOOM, F_CHROMA, F_COUNT };
static const char *const FNAME[F_COUNT] = {
    "None", "Fourfold", "Tidewave", "Mirror", "Shuffled Slices", "Upside Down", "Zoom Wobble",
    "Chromatic Split",
};

enum { S_PLAY, S_DYING, S_CROWNED };

#define SLICES 10

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
    bool crown;
    float target_t;
    int gulp_x, gulp_y;
    float gulp_t;
    int eaten;
    int cur_min, cur_steps;
    int sum_min, sum_act;
    /* filters */
    int filter, warn_filter;
    float filter_t, filter_len, warn_t, glitch;
    int next_filter_at, forder[F_COUNT - 1], fidx;
    int perm[SLICES];
    float reshuffle_t;
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

/* ---- game ------------------------------------------------------------------ */

static void spawn_target(bool crown)
{
    bfs(S.bx, S.by, S.len, false);
    int pick = -1, seen = 0, want = crown ? 8 : 3;
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
    S.cur_min = bdist[pick] > 0 ? bdist[pick] : abs(S.fx - S.bx[0]) + abs(S.fy - S.by[0]) + 2;
}

static void shuffle_slices(void)
{
    for (int i = 0; i < SLICES; i++)
        S.perm[i] = i;
    for (int i = SLICES - 1; i > 0; i--) {
        int j = mg_randi(0, i), k = S.perm[i];
        S.perm[i] = S.perm[j];
        S.perm[j] = k;
    }
    int fixed = 0;
    for (int i = 0; i < SLICES; i++)
        fixed += S.perm[i] == i;
    if (fixed > 3) {   /* make sure it really looks shuffled */
        int k = S.perm[0];
        for (int i = 0; i < SLICES - 1; i++)
            S.perm[i] = S.perm[i + 1];
        S.perm[SLICES - 1] = k;
    }
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
    for (int i = 0; i < F_COUNT - 1; i++)
        S.forder[i] = i + 1;
    for (int i = F_COUNT - 2; i > 0; i--) {
        int j = mg_randi(0, i), k = S.forder[i];
        S.forder[i] = S.forder[j];
        S.forder[j] = k;
    }
    S.next_filter_at = mg_randi(2, 3);
    shuffle_slices();
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

static int score(void)
{
    float tp = tempo_of(S.sum_min, S.sum_act);
    if (S.state == S_CROWNED)
        return (int)(30 + 70 * tp + 0.5f);
    return (int)(45.0f * (float)S.eaten / TARGETS * (0.6f + 0.4f * tp) + 0.5f);
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
    else
        snprintf(buf, sizeof(buf), "Fell %d bite%s short of the crown.", TARGETS - S.eaten,
                 TARGETS - S.eaten == 1 ? "" : "s");
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
    S.gulp_t = 0.25f;
    if (S.crown) {
        S.state = S_CROWNED;
        S.state_t = 0;
        S.filter = F_NONE;
        S.warn_t = 0;
        S.eaten = TARGETS;
        mg_sfx("snake_crown");
        return;
    }
    S.eaten++;
    mg_sfx("snake_eat");
    if (S.eaten >= S.next_filter_at) {
        if (S.filter == F_NONE && S.warn_t <= 0) {
            S.warn_filter = S.forder[S.fidx++ % (F_COUNT - 1)];
            S.warn_t = 2.0f;
            S.filter_len = 6.0f + mg_randf() * 4.0f;
            S.next_filter_at = S.eaten + mg_randi(2, 3);
            mg_sfx("snake_filter_warn");
        } else {
            S.next_filter_at = S.eaten + 1;
        }
    }
    if (S.eaten >= FOODS_TO_CROWN) {
        spawn_target(true);
        mg_sfx("snake_crown_appears");
    } else {
        spawn_target(false);
    }
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
    bool grow = nx == S.fx && ny == S.fy;
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
    S.cur_steps++;
    if (grow)
        eat();
}

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
    float iv = fmaxf(0.12f, 0.22f - 0.008f * S.eaten);
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

    if (S.state == S_DYING) {
        S.state_t += dt;
        return S.state_t < 2.0f;
    }
    if (S.state == S_CROWNED) {
        float before = S.state_t;
        S.state_t += dt;
        if (before < 1.2f && S.state_t >= 1.2f)
            mg_sfx("snake_rating");
        if (S.state_t > 2.0f && (in->down & KEY_A_))
            return false;
        return S.state_t < 7.0f;
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

    /* steering: D-pad presses and circle pad flicks, two turns buffered */
    for (int d = 0; d < 4; d++)
        if (in->down & DIR_KEY[d])
            enqueue(d);
    int pd = -1;
    if (fabsf(in->cx) > fabsf(in->cy)) {
        if (fabsf(in->cx) > 0.55f)
            pd = in->cx > 0 ? DIR_R : DIR_L;
    } else if (fabsf(in->cy) > 0.55f) {
        pd = in->cy > 0 ? DIR_U : DIR_D;
    }
    if (pd >= 0 && pd != S.pad_dir)
        enqueue(pd);
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

    /* the leak */
    if (S.warn_t > 0) {
        S.warn_t -= dt;
        if (S.warn_t <= 0) {
            S.warn_t = 0;
            S.filter = S.warn_filter;
            S.filter_t = S.filter_len;
            S.glitch = 1;
            S.reshuffle_t = 2.5f;
            if (S.filter == F_SLICES)
                shuffle_slices();
            mg_sfx("snake_filter_on");
        }
    } else if (S.filter != F_NONE) {
        S.filter_t -= dt;
        if (S.filter == F_SLICES && (S.reshuffle_t -= dt) <= 0 && S.filter_t > 1.0f) {
            S.reshuffle_t = 2.5f;
            shuffle_slices();
            mg_sfx("snake_reshuffle");
        }
        if (S.filter_t <= 0) {
            S.filter = F_NONE;
            S.glitch = 1;
            mg_sfx("snake_filter_off");
        }
    }

    if (S.t < GRACE)
        return true;
    S.step_acc += dt / interval();
    while (S.step_acc >= 1.0f && S.state == S_PLAY) {
        S.step_acc -= 1.0f;
        step();
    }
    return true;
}

/* ---- drawing helpers -------------------------------------------------------- */

static float cell_cx(float gx) { return BX + (gx + 0.5f) * CELL; }
static float cell_cy(float gy) { return BY + (gy + 0.5f) * CELL; }

/* Interpolated screen position of segment i. */
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
    *x = cell_cx(gx);
    *y = cell_cy(gy);
}

static float filter_env(void)
{
    if (S.filter == F_NONE)
        return 0;
    float in = S.filter_len - S.filter_t;
    return clampf(fminf(in, S.filter_t) / 0.4f, 0, 1);
}

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

static void draw_food(int eye, float x, float y, float size)
{
    float pulse = 0.5f + 0.5f * sinf(S.t * 6);
    static const u32 PAL[4] = {RGBA(80, 240, 255, 255), RGBA(255, 70, 220, 255), RGBA(255, 240, 90, 255),
                               RGBA(255, 255, 255, 255)};
    u32 tick = (u32)(S.t * 8);
    u32 glow = PAL[hash(tick / 4) & 1];
    mg_rect(eye, x - 10 * size, y - 10 * size, 20 * size, 20 * size, D_FOOD + 0.05f,
            rgba_alpha(glow, (0.12f + 0.12f * pulse)));
    mg_rect(eye, x - 7 * size, y - 7 * size, 14 * size, 14 * size, D_FOOD + 0.02f,
            rgba_alpha(glow, (0.25f + 0.2f * pulse)));
    float jx = (hash(tick * 7 + 3) % 6 == 0) ? 2.0f : 0.0f;
    for (int k = 0; k < 4; k++) {
        float ox = (k & 1) ? 0 : -5, oy = (k & 2) ? 0 : -5;
        mg_rect(eye, x + (ox + (k == 1 ? jx : 0)) * size, y + oy * size, 5 * size, 5 * size, D_FOOD,
                PAL[hash(tick + (u32)k * 17) & 3]);
    }
    float a = S.t * 3;
    mg_rect(eye, x + cosf(a) * 9 * size - 1, y + sinf(a) * 9 * size - 1, 2, 2, D_FOOD - 0.03f, MG_WHITE);
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

/* The worm as a chain of soft circles. */
static void draw_worm(int eye)
{
    float xs[MAXLEN], ys[MAXLEN];
    bool dying = S.state == S_DYING;
    bool ghost = S.shed > 0;
    float sh = ghost ? 0.35f + 0.15f * sinf(S.t * 10) : 1.0f;
    for (int i = 0; i < S.len; i++) {
        seg_pos(i, &xs[i], &ys[i]);
        if (dying) {   /* the worm unravels */
            u32 h = hash((u32)i * 31 + 7);
            float ang = (float)(h % 628) / 100.0f, k = S.state_t * S.state_t * 14;
            xs[i] += cosf(ang) * k;
            ys[i] += sinf(ang) * k;
        }
    }
    u32 outline = RGBA(90, 30, 70, 255), head = RGBA(255, 150, 175, 255), tail = RGBA(190, 80, 140, 255);
    if (ghost)
        outline = RGBA(70, 120, 170, 255), head = RGBA(190, 240, 255, 255), tail = RGBA(120, 180, 240, 255);
    if (dying && ((int)(S.state_t * 12) & 1))
        head = tail = RGBA(255, 80, 80, 255);
    float a = ghost ? 0.4f + sh * 0.4f : 1.0f;
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
    draw_face(eye, xs[0], ys[0], S.dir, 9, D_HEAD, dying);
    if (S.state == S_CROWNED)
        draw_crown(eye, xs[0], ys[0] - 9, 1.0f, D_CROWN, 1);
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
        for (int i = 0; i < S.skin_len; i++)
            mg_circle(eye, cell_cx(S.skin_x[i]), cell_cy(S.skin_y[i]), 8, D_WORM + 0.08f,
                      RGBA(200, 230, 255, (u32)(70 * clampf(S.skin_t / 2.0f, 0, 1))));
    /* the food being swallowed */
    if (S.gulp_t > 0 && S.state != S_CROWNED)
        draw_food(eye, cell_cx(S.gulp_x), cell_cy(S.gulp_y), S.gulp_t / 0.25f);
    /* the target */
    if (S.state != S_CROWNED) {
        float x = cell_cx(S.fx), y = cell_cy(S.fy);
        if (S.crown) {
            float pop = clampf(S.target_t / 0.5f, 0, 1);
            float bob = sinf(S.t * 4) * 2;
            for (int k = 0; k < 4; k++) {
                float a = S.t * 2 + k * 1.571f;
                mg_rect(eye, x + cosf(a) * 13 - 1, y + sinf(a) * 13 - 1, 2, 2, D_CROWN, MG_WHITE);
            }
            draw_crown(eye, x, y + 3 + bob, 0.9f * pop + 0.6f * (1 - pop) * sinf(pop * 9), D_CROWN, pop);
        } else {
            draw_food(eye, x, y, 1);
        }
    }
    draw_worm(eye);
}

/* ---- the view (from capture pieces) ----------------------------------------------- */

enum { V_NORMAL, V_MIRROR, V_FLIP, V_SWAP };

static void part(int eye, int sx, int sy, int sw, int sh, float dx, float dy, float dw, float dh, float a)
{
    gfx_draw_capture_part(eye, (float)sx, (float)sy, (float)sw, (float)sh, dx, dy, dw, dh, a);
}

/* The whole field into (x, y, w, h). Flips reverse cell-wide strips. */
static void put_field(int eye, float x, float y, float w, float h, int mode)
{
    float kx = w / FW, ky = h / FH;
    switch (mode) {
    case V_NORMAL:
        part(eye, BX, BY, FW, FH, x, y, w, h, 1);
        break;
    case V_MIRROR:   /* 20 strips */
        for (int c = 0; c < GW; c++)
            part(eye, BX + c * CELL, BY, CELL, FH, x + (GW - 1 - c) * CELL * kx, y, CELL * kx, h, 1);
        break;
    case V_FLIP:     /* 12 strips */
        for (int r = 0; r < GH; r++)
            part(eye, BX, BY + r * CELL, FW, CELL, x, y + (GH - 1 - r) * CELL * ky, w, CELL * ky, 1);
        break;
    case V_SWAP:     /* the four quarters turned half way round */
        for (int q = 0; q < 4; q++) {
            int qx = q & 1, qy = q >> 1;
            part(eye, BX + qx * FW / 2, BY + qy * FH / 2, FW / 2, FH / 2, x + (1 - qx) * w / 2,
                 y + (1 - qy) * h / 2, w / 2, h / 2, 1);
        }
        break;
    }
}

static void ghost_entities(int eye, float ox, float oy, u32 c)
{
    for (int i = 0; i < S.len; i++) {
        float x, y;
        seg_pos(i, &x, &y);
        mg_circle(eye, x + ox, y + oy, i ? 7.0f : 8.5f, D_WORM, c);
    }
    float x = cell_cx(S.fx) + ox, y = cell_cy(S.fy) + oy;
    if (S.crown)
        mg_tri(eye, x - 8, y + 4, x + 8, y + 4, x, y - 8, D_CROWN, c);
    else
        mg_rect(eye, x - 5, y - 5, 10, 10, D_FOOD, c);
}

static void draw_field(int eye)
{
    float env = filter_env();
    switch (S.filter) {
    case F_NONE:
        put_field(eye, BX, BY, FW, FH, V_NORMAL);
        break;
    case F_QUAD: {
        float hw = FW / 2.0f, hh = FH / 2.0f;
        put_field(eye, BX, BY, hw, hh, V_NORMAL);
        put_field(eye, BX + hw, BY, hw, hh, V_MIRROR);
        put_field(eye, BX, BY + hh, hw, hh, V_FLIP);
        put_field(eye, BX + hw, BY + hh, hw, hh, V_SWAP);
        mg_rect(eye, BX + hw - 1.5f, BY, 3, FH, D_BOARD - 0.05f, RGBA(255, 70, 200, 200));
        mg_rect(eye, BX, BY + hh - 1.5f, FW, 3, D_BOARD - 0.05f, RGBA(255, 70, 200, 200));
        break;
    }
    case F_WAVE: {   /* 18 rows, each wrapping round in up to two pieces */
        const int SH = 12;
        for (int k = 0; k < FH / SH; k++) {
            int y0 = BY + k * SH;
            int o = (int)lroundf(env * 22 * sinf(k * 0.55f + S.t * 3.2f));
            if (o > 0) {
                part(eye, BX, y0, FW - o, SH, BX + o, y0, FW - o, SH, 1);
                part(eye, BX + FW - o, y0, o, SH, BX, y0, o, SH, 1);
            } else if (o < 0) {
                o = -o;
                part(eye, BX + o, y0, FW - o, SH, BX, y0, FW - o, SH, 1);
                part(eye, BX, y0, o, SH, BX + FW - o, y0, o, SH, 1);
            } else {
                part(eye, BX, y0, FW, SH, BX, y0, FW, SH, 1);
            }
        }
        break;
    }
    case F_MIRROR:
        put_field(eye, BX, BY, FW, FH, V_MIRROR);
        break;
    case F_SLICES: {
        const int SW = FW / SLICES;
        for (int i = 0; i < SLICES; i++)
            part(eye, BX + S.perm[i] * SW, BY, SW, FH, BX + i * SW, BY, SW, FH, 1);
        for (int i = 1; i < SLICES; i++)
            mg_rect(eye, BX + i * SW - 1, BY, 2, FH, D_BOARD - 0.05f, RGBA(80, 230, 255, 140));
        break;
    }
    case F_FLIP:
        put_field(eye, BX, BY, FW, FH, V_FLIP);
        break;
    case F_ZOOM: {
        float z = 1.0f + env * (0.34f + 0.14f * sinf(S.t * 2.3f));
        float hx, hy;
        seg_pos(0, &hx, &hy);
        int sw = (int)(FW / z * (1.0f + 0.05f * env * sinf(S.t * 3.1f)));
        int sh = (int)(FH / z);
        sw = sw > FW ? FW : sw;
        float cx = lerpf(BX + FW / 2.0f, hx, 0.6f) + env * 18 * sinf(S.t * 0.9f);
        float cy = lerpf(BY + FH / 2.0f, hy, 0.6f) + env * 12 * cosf(S.t * 1.1f);
        int sx = (int)clampf(cx - sw / 2.0f, BX, BX + FW - sw);
        int sy = (int)clampf(cy - sh / 2.0f, BY, BY + FH - sh);
        part(eye, sx, sy, sw, sh, BX, BY, FW, FH, 1);
        break;
    }
    case F_CHROMA: {
        put_field(eye, BX, BY, FW, FH, V_NORMAL);
        int gx = (int)(env * (10 + 6 * sinf(S.t * 1.3f))), gy = (int)(env * 6 * cosf(S.t * 1.1f));
        int ay = abs(gy);
        part(eye, BX, BY + (gy < 0 ? ay : 0), FW - gx, FH - ay, BX + gx, BY + (gy > 0 ? ay : 0), FW - gx,
             FH - ay, 0.35f * env);
        float ox = env * (5 + 3 * sinf(S.t * 2.1f)), oy = env * 3 * cosf(S.t * 1.7f);
        ghost_entities(eye, ox, oy, RGBA(255, 40, 70, 95));
        ghost_entities(eye, -ox, -oy, RGBA(40, 220, 255, 95));
        break;
    }
    }
    /* switching glitch: a few torn bands */
    if (S.glitch > 0) {
        u32 tick = (u32)(S.t * 30);
        for (int i = 0; i < 5; i++) {
            u32 h = hash(tick * 53 + (u32)i * 7919);
            int bh = 6 + (int)(h % 14), y0 = BY + (int)((h >> 8) % (FH - bh));
            int o = (int)((float)((int)((h >> 16) % 61) - 30) * S.glitch);
            int sx = o > 0 ? BX : BX - o, w = FW - abs(o);
            part(eye, sx, y0, w, bh, (float)(sx + o), (float)y0, (float)w, (float)bh, 0.9f);
            if (i < 2)
                mg_rect(eye, BX, (float)y0, FW, 2, -0.05f,
                        (h >> 4) & 1 ? RGBA(255, 60, 200, (u32)(160 * S.glitch))
                                     : RGBA(60, 230, 255, (u32)(160 * S.glitch)));
        }
    }
}

static void draw_final(int eye)
{
    float t = S.state_t;
    put_field(eye, BX, BY, FW, FH, V_NORMAL);
    gfx_rect(0, 0, TOP_W, TOP_H, RGBA(8, 4, 20, (u32)clampf(t * 360, 0, 225)));
    float ap = clampf((t - 0.2f) / 0.5f, 0, 1);
    if (ap <= 0)
        return;
    /* light rays behind the crowned worm */
    for (int i = 0; i < 8; i++) {
        float a = t * 0.4f + i * 0.785f;
        mg_tri(eye, 130, 112, 130 + cosf(a) * 170, 112 + sinf(a) * 170, 130 + cosf(a + 0.22f) * 170,
               112 + sinf(a + 0.22f) * 170, 0.5f, RGBA(255, 210, 110, (u32)(28 * ap)));
    }
    /* the worm, big */
    const int N = 9;
    float xs[9], ys[9], rs[9];
    for (int i = 0; i < N; i++) {
        xs[i] = 130 - i * 13.0f;
        ys[i] = 150 + sinf(i * 0.9f - t * 3) * 9 * (i ? 1.0f : 0.3f);
        rs[i] = 19 - i * 1.2f;
    }
    xs[0] += 4;
    u32 head = RGBA(255, 150, 175, 255), tail = RGBA(190, 80, 140, 255);
    for (int i = N - 1; i >= 0; i--)
        mg_circle(eye, xs[i], ys[i], rs[i] + 2.5f, -0.2f + i * 0.03f, rgba_alpha(RGBA(90, 30, 70, 255), ap));
    for (int i = N - 1; i >= 0; i--) {
        float dp = -0.2f + i * 0.03f;
        mg_circle(eye, xs[i], ys[i], rs[i], dp, rgba_alpha(mixc(head, tail, i / (float)(N - 1)), ap));
        mg_circle(eye, xs[i] - rs[i] * 0.3f, ys[i] - rs[i] * 0.35f, rs[i] * 0.3f, dp - 0.01f,
                  RGBA(255, 255, 255, (u32)(110 * ap)));
    }
    /* proud face */
    u32 ink = rgba_alpha(RGBA(40, 16, 36, 255), ap);
    float hx = xs[0], hy = ys[0];
    for (int k = 0; k < 2; k++) {
        float ex = hx + (k ? 9 : -3), ey = hy - 4;
        mg_circle(eye, ex, ey, 4.5f, -0.24f, rgba_alpha(MG_WHITE, ap));
        mg_circle(eye, ex + 1.5f, ey - 1, 2.2f, -0.25f, ink);
        mg_circle(eye, ex - 1 + (k ? 3 : -2), ey + 8, 3, -0.23f, RGBA(255, 110, 140, (u32)(150 * ap)));
    }
    mg_circle(eye, hx + 4, hy + 6, 4, -0.24f, ink);
    mg_circle(eye, hx + 4, hy + 4, 4.2f, -0.245f, rgba_alpha(head, ap));
    /* the crown drops onto the head */
    float land = clampf(t / 0.8f, 0, 1);
    float e = 1 - (1 - land) * (1 - land);
    float cy = lerpf(-30, hy - rs[0] + 1, e) + (land >= 1 ? sinf(t * 2) * 1.5f : 0);
    draw_crown(eye, hx + 1, cy, 2.4f, -0.4f, 1);
    if (land >= 1)
        for (int i = 0; i < 6; i++) {
            float a = t * 1.5f + i * 1.047f, r = 34 + 4 * sinf(t * 5 + i);
            mg_rect(eye, hx + cosf(a) * r - 1.5f, cy - 8 + sinf(a) * r * 0.6f - 1.5f, 3, 3, -0.35f,
                    RGBA(255, 255, 220, 220));
        }
    /* the rating */
    char buf[64];
    mg_text_centered(eye, "CROWNED", 290, 30, 0.95f, -0.2f, rgba_alpha(MG_GOLD, ap));
    snprintf(buf, sizeof(buf), "Route: %d%% of shortest", route_pct());
    mg_text_centered(eye, buf, 290, 70, 0.48f, -0.1f, rgba_alpha(MG_WHITE, ap));
    if (t >= 1.2f) {
        float pop = clampf((t - 1.2f) / 0.25f, 0, 1);
        snprintf(buf, sizeof(buf), "%d%%", score());
        mg_text_centered(eye, buf, 290, 94, 1.0f + 0.5f * pop, -0.35f, MG_WHITE);
        mg_text_centered(eye, rating_name(score()), 290, 160, 0.6f, -0.2f, MG_GOLD);
    }
    if (t >= 2.0f)
        mg_text_centered(eye, "A: continue", 290, 206, 0.45f, -0.05f, RGBA(200, 200, 230, 255));
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
        frame = RGBA(255, 60, 200, 255);
    else if (S.filter != F_NONE)
        frame = RGBA(120, 60, 160, 255);
    else if (S.shed > 0)
        frame = RGBA(80, 160, 210, 255);
    mg_rect(eye, BX - 5, BY - 5, FW + 10, FH + 10, D_BOARD + 0.02f, frame);
    draw_field(eye);

    /* the top line: foods, filter or warning, route */
    char buf[64];
    if (S.crown)
        snprintf(buf, sizeof(buf), "The crown is out!");
    else
        snprintf(buf, sizeof(buf), "Food %d/%d", S.eaten, FOODS_TO_CROWN);
    mg_text(eye, buf, BX, 2, 0.42f, -0.05f, S.crown ? MG_GOLD : MG_WHITE);
    snprintf(buf, sizeof(buf), "Route %d%%", route_pct());
    mg_text(eye, buf, BX + FW - gfx_text_width(buf, 0.42f), 2, 0.42f, -0.05f, RGBA(200, 200, 230, 255));
    if (S.shed > 0) {
        snprintf(buf, sizeof(buf), "SKIN SHED %.1f", fmaxf(0, S.shed));
        mg_text_centered(eye, buf, TOP_W / 2, 2, 0.42f, -0.1f, RGBA(150, 230, 255, 255));
    } else if (S.filter != F_NONE) {
        snprintf(buf, sizeof(buf), "%s %.0fs", FNAME[S.filter], ceilf(S.filter_t));
        mg_text_centered(eye, buf, TOP_W / 2, 2, 0.42f, -0.1f, RGBA(255, 120, 220, 255));
    }

    if (S.warn_t > 0) {
        /* text only, with a shadow, so the board stays readable */
        float y = BY + 10;
        u32 c = ((int)(S.t * 8) & 1) ? RGBA(255, 80, 210, 255) : MG_WHITE;
        snprintf(buf, sizeof(buf), "THE LEAK: %s in %.1f", FNAME[S.warn_filter], S.warn_t);
        mg_text_centered(eye, buf, TOP_W / 2 + 1.5f, y + 1.5f, 0.6f, -0.28f, RGBA(0, 0, 0, 200));
        mg_text_centered(eye, buf, TOP_W / 2, y, 0.6f, -0.3f, c);
    }
    if (S.t < GRACE + 0.4f && S.state == S_PLAY)
        mg_text_centered(eye, S.t < GRACE ? "Ready..." : "GO!", TOP_W / 2, BY + 40, 0.8f, -0.3f, MG_GOLD);
    if (S.state == S_DYING) {
        gfx_rect(0, 0, TOP_W, TOP_H, RGBA(255, 40, 60, (u32)clampf(120 - S.state_t * 120, 0, 120)));
        const char *msg = S.died_wall ? "The worm hit the edge of the world." : "The worm bit itself.";
        mg_text_centered(eye, msg, TOP_W / 2 + 1.5f, BY + FH / 2.0f - 10.5f, 0.6f, -0.28f, RGBA(0, 0, 0, 200));
        mg_text_centered(eye, msg, TOP_W / 2, BY + FH / 2.0f - 12, 0.6f, -0.3f, MG_WHITE);
    }
}

/* ---- bottom screen ------------------------------------------------------------- */

static void draw_bottom(void)
{
    char buf[96];
    gfx_text("Crown of the Worm", 12, 6, 0.55f, MG_GOLD);
    if (S.crown || S.state == S_CROWNED)
        snprintf(buf, sizeof(buf), "The crown is out - eat it!");
    else
        snprintf(buf, sizeof(buf), "Foods until the crown: %d", FOODS_TO_CROWN - S.eaten);
    gfx_text(buf, 12, 30, 0.47f, MG_WHITE);
    for (int i = 0; i < FOODS_TO_CROWN; i++)
        gfx_rect(12 + i * 20, 54, 14, 14, i < S.eaten ? RGBA(255, 90, 220, 255) : RGBA(255, 255, 255, 40));
    float cx = 12 + FOODS_TO_CROWN * 20 + 10, cy = 66;
    u32 cc = S.crown ? MG_GOLD : RGBA(255, 210, 110, 70);
    gfx_rect(cx - 9, cy - 4, 18, 4, cc);
    gfx_triangle(cx - 9, cy - 4, cx - 3, cy - 4, cx - 8, cy - 13, cc);
    gfx_triangle(cx - 4, cy - 4, cx + 4, cy - 4, cx, cy - 15, cc);
    gfx_triangle(cx + 9, cy - 4, cx + 3, cy - 4, cx + 8, cy - 13, cc);

    if (S.warn_t > 0)
        snprintf(buf, sizeof(buf), "Filter: %s incoming!", FNAME[S.warn_filter]);
    else if (S.filter != F_NONE)
        snprintf(buf, sizeof(buf), "Filter: %s (%.0f s)", FNAME[S.filter], ceilf(S.filter_t));
    else
        snprintf(buf, sizeof(buf), "Filter: none");
    gfx_text(buf, 12, 80, 0.47f, S.filter != F_NONE || S.warn_t > 0 ? RGBA(255, 120, 220, 255)
                                                                   : RGBA(190, 190, 210, 255));

    /* efficiency: shortest / actual over all targets so far */
    float eff = S.sum_act > 0 ? (float)S.sum_min / S.sum_act : 1.0f;
    snprintf(buf, sizeof(buf), "Route efficiency %d%%", (int)(eff * 100 + 0.5f));
    gfx_text(buf, 12, 104, 0.47f, MG_WHITE);
    gfx_rect(12, 126, 296, 12, RGBA(255, 255, 255, 40));
    u32 ec = eff >= 0.85f ? RGBA(120, 230, 150, 255) : eff >= 0.6f ? RGBA(255, 210, 110, 255)
                                                                 : RGBA(240, 110, 100, 255);
    gfx_rect(12, 126, 296 * clampf(eff, 0, 1), 12, ec);
    gfx_rect(12 + 296 * 0.85f, 122, 1, 20, RGBA(255, 255, 255, 140));
    snprintf(buf, sizeof(buf), "This bite: %d steps, shortest %d", S.cur_steps, S.cur_min);
    gfx_text(buf, 12, 144, 0.42f, RGBA(200, 200, 230, 255));

    if (S.boost > 0)
        snprintf(buf, sizeof(buf), "A boost: GO");
    else if (S.boost_cd > 0)
        snprintf(buf, sizeof(buf), "A boost: recharging");
    else
        snprintf(buf, sizeof(buf), "A boost: ready");
    gfx_text(buf, 12, 166, 0.45f, MG_WHITE);
    gfx_rect(170, 170, 120, 8, RGBA(255, 255, 255, 40));
    gfx_rect(170, 170, 120 * clampf(1 - S.boost_cd / BOOST_COOLDOWN, 0, 1), 8, RGBA(120, 200, 255, 255));
    if (S.shed > 0) {
        snprintf(buf, sizeof(buf), "Skin shed: %.1f s", fmaxf(0, S.shed));
        gfx_text(buf, 12, 188, 0.45f, RGBA(150, 230, 255, 255));
    }
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
    bool grow = nx == S.fx && ny == S.fy;
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

static void bot(Input *in, float t)
{
    if (t > 6.0f && !MG.cheat_used && S.state == S_PLAY)
        in->down |= KEY_L_;
    if (S.state == S_CROWNED && S.state_t > 3.5f)
        in->down |= KEY_A_;
    if (S.state != S_PLAY || S.nq || t < GRACE)
        return;
    bfs(S.bx, S.by, S.len, false);
    int tc = S.fy * GW + S.fx;
    int want = bdist[tc] >= 0 ? bfirst[tc] : -1, far = bdist[tc];
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
    if (d != S.dir)
        in->down |= DIR_KEY[d];
    if (far > 6 && S.boost_cd <= 0)
        in->down |= KEY_A_;
}

static bool can_cheat(void) { return S.state == S_PLAY; }

const MiniGame MG_SNAKE = {
    .id = "snake",
    .title = "Crown of the Worm",
    .rules = "Steer the worm to the glitch pixels.\n"
             "After 12 bites the crown appears: eat it!\n"
             "Walls and your own body are deadly.\n"
             "The leak bends the view now and then.\n"
             "Score: shortest route vs. steps taken.\n"
             "Bold, direct routes score best.",
    .controls = "D-pad / Circle Pad: steer\n"
                "A: boost (short burst, recharges)\n"
                "START: pause\n"
                "\n"
                "Count your steps: every detour\n"
                "lowers your crown rating.",
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
