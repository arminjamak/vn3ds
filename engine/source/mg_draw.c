/* Echo of a Shape: Pim, a Purgatorium spirit, teaches shapes at a
 * whiteboard. Each exercise Pim draws a shape on the board with a marker,
 * lets you look at it for a few seconds, then flips the board over. Draw it
 * from memory on the touch screen's pad, at any size and anywhere: only the
 * shape counts. Pim then holds your drawing up next to the original and
 * reacts. Five exercises, each harder, shown for less time and worth more.
 *
 * Matching (compute_match) compares shapes, not placement:
 *   1. Both the target and your strokes are resampled to ~112 points spread
 *      evenly along their length (more points on longer strokes).
 *   2. Each is normalised: moved to its centroid and scaled to unit RMS
 *      radius, so where you drew and how big never matter. Your drawing's
 *      aspect ratio is pulled towards the target's (up to 1.5x), and only a
 *      very different aspect (beyond 1.4x) costs up to 20%.
 *   3. A small rotation search (-12..+12 degrees in 4 degree steps), each
 *      refined by two rounds of symmetric nearest-point alignment (offset
 *      and +-15% size), keeps the best reading.
 *   4. Four measures, each mapped to 0..1 over the range where hand copies
 *      and wrong shapes part ways, are blended (30/25/25/20%), and the
 *      weakest one drags the blend down a little:
 *        coverage both ways: the F-score of how much of your ink lies near
 *          the shape and how much of the shape your ink covers (full credit
 *          within 0.08 RMS radii, none beyond 0.25);
 *        the symmetric chamfer distance (mean point-to-stroke distance both
 *          ways);
 *        a direction histogram (12 bins of undirected stroke direction,
 *          weighted by length): the overall form;
 *        a corner profile (how sharply the strokes turn, point by point):
 *          tells a circle from a square and a star from a blob even where
 *          their outlines overlap well.
 *   5. A piecewise-linear curve turns that likeness into the match %. The
 *      knobs (K_*) were tuned with a harness of synthetic drawings: exact,
 *      careful, sloppy and small-in-a-corner copies, other shapes from the
 *      same exercise, scribbles and partial drawings.
 *
 * Score: exercise k (1..5) has weight k; the final score is the weighted
 * average of the five match percentages. The cheat: Pim gets distracted (a
 * moth at the window) and forgets to hide the board this exercise. */

#include "minigame.h"

#define LEVELS 5
#define MAX_PATHS 6
#define MAX_PPTS 64
#define MAX_UPTS 480
#define MAX_USTROKES 48

/* The pad on the bottom screen (clear of the Cheat button at y 206-234). */
#define CV_X 6.0f
#define CV_Y 22.0f
#define CV_W 308.0f
#define CV_H 180.0f

/* Buttons (clear of the framework's Cheat button at x 236-314, y 206-234). */
#define BTN_Y 208
#define BTN_H 26
static const float BTN_X[3] = {8, 82, 156};
static const float BTN_W[3] = {68, 68, 72};
static const char *const BTN_LABEL[3] = {"B: Undo", "Y: Clear", "A: Done"};

/* The whiteboard on the top screen: shapes live in a 400x240 frame that is
 * drawn onto the board's surface at BS. */
#define BS 0.6f
#define BX 146.0f
#define BY 22.0f
#define BW (400 * BS)
#define BH (240 * BS)
#define BCX (BX + BW / 2)
#define BCY (BY + BH / 2)

/* Review layout on the board: your paper (left) and Pim's shape (right). */
#define REV_PX 204.0f
#define REV_TX 326.0f
#define REV_Y 84.0f
#define REV_FIT 90.0f
#define PAPER 104.0f
#define REV_SCORE_X 318.0f  /* the score, under Pim's shape */

/* Pim's home in front of the window, and during the review. */
#define PIM_X 66.0f
#define PIM_Y 96.0f
#define PIM_RX 94.0f
#define PIM_R 28.0f

static const float VIEW_TIME[LEVELS] = {5.0f, 4.5f, 4.0f, 3.5f, 3.0f};
#define DRAW_TIME 25.0f
#define WIPE_TIME 0.8f
#define INTRO_TIME 1.9f
#define HIDE_TIME 0.8f
#define FLIP_TIME 0.55f
#define REV_MORPH 0.65f    /* review: the shapes move into place */
#define REV_STAMP 1.35f    /* review: the score goes up, Pim reacts */
#define REV_END 5.5f
#define SAY_CPS 38.0f      /* speech: characters per second */

enum { PH_WIPE, PH_INTRO, PH_SKETCH, PH_VIEW, PH_HIDE, PH_DRAW, PH_REVIEW };

typedef struct {
    int n;
    float x[MAX_PPTS], y[MAX_PPTS]; /* shape frame coordinates (400x240) */
} Path;

#define NR 128              /* resampled points per shape */

static struct {
    int level;
    int phase;
    float pt;               /* seconds in this phase */
    float t;                /* seconds since start */
    Path paths[MAX_PATHS];
    int npaths;
    float scx, scy, sw, sh; /* target bounding box: centre and size */
    /* Pim's marker while sketching */
    float sk_s, sk_total, sk_ink, sk_speed;
    float mk_x, mk_y;
    bool mk_up;
    float squeak_t;
    /* the board: 0 = front, 1 = flipped to its back */
    float flip, flip_goal;
    bool peek;              /* the cheat: Pim forgot to hide it */
    bool peek_level[LEVELS];
    /* your drawing, pad coordinates (0..CV_W, 0..CV_H) */
    float ux[MAX_UPTS], uy[MAX_UPTS];
    int nu;
    int sstart[MAX_USTROKES];
    int ns;
    bool touching, stroking;
    /* results */
    int match[LEVELS];
    bool timed_out;
    bool low_warned, stamped, reacted, papered;
    int react;              /* 0 meh, 1 encouraging, 2 delighted */
    int last_tick;
    float hint_t;
    const char *hint;
    float idle_t;
    /* speech */
    const char *say;
    int say_len, say_n;
    float say_t;
    /* alignment of the last match, for the review */
    float tcx, tcy, tr;            /* target centroid and RMS radius (frame) */
    float ucx, ucy;                /* your centroid (pad) */
    float A[4], At[2], Ai[4];      /* pad -> normalised: A (p - uc) + At */
    float rev_k, rev_cx, rev_cy;   /* normalised -> review pixels */
    float rx[NR], ry[NR];          /* your drawing, aligned and resampled */
    u8 rs[NR];
    int rn;
} G;

/* ---- shapes ------------------------------------------------------------------ */

static float randr(float lo, float hi) { return lo + (hi - lo) * mg_randf(); }

static Path *new_path(void)
{
    if (G.npaths >= MAX_PATHS)
        return NULL;
    Path *p = &G.paths[G.npaths++];
    p->n = 0;
    return p;
}

static void put(Path *p, float x, float y)
{
    if (p && p->n < MAX_PPTS) {
        p->x[p->n] = clampf(x, 8, 400 - 8);
        p->y[p->n] = clampf(y, 8, 240 - 8);
        p->n++;
    }
}

/* Closed regular polygon; many sides make a circle. */
static void add_poly(float cx, float cy, float r, int sides, float rot)
{
    Path *p = new_path();
    for (int i = 0; i <= sides; i++) {
        float a = rot + 6.2831853f * i / sides;
        put(p, cx + cosf(a) * r, cy + sinf(a) * r);
    }
}

static void add_circle(float cx, float cy, float r) { add_poly(cx, cy, r, 24, 0); }

static void add_line(float x0, float y0, float x1, float y1)
{
    Path *p = new_path();
    put(p, x0, y0);
    put(p, x1, y1);
}

static void add_star(float cx, float cy, float r, int points, float rot)
{
    Path *p = new_path();
    for (int i = 0; i <= points * 2; i++) {
        float a = rot + 3.1415927f * i / points, rr = (i & 1) ? r * 0.42f : r;
        put(p, cx + cosf(a) * rr, cy + sinf(a) * rr);
    }
}

static void add_spiral(float cx, float cy, float r, float turns, float rot, float dir)
{
    Path *p = new_path();
    int n = 52;
    for (int i = 0; i < n; i++) {
        float f = (float)i / (n - 1), a = rot + dir * f * turns * 6.2831853f;
        float rr = r * (0.08f + 0.92f * f);
        put(p, cx + cosf(a) * rr, cy + sinf(a) * rr * 0.9f);
    }
}

static void add_zigzag(float x0, float x1, float cy, float amp, int peaks, float tilt)
{
    Path *p = new_path();
    int n = peaks * 2 + 1;
    for (int i = 0; i < n; i++) {
        float f = (float)i / (n - 1), x = lerpf(x0, x1, f);
        float y = cy + (x - (x0 + x1) / 2) * tilt + ((i & 1) ? -amp : amp) * (i == 0 || i == n - 1 ? 0.5f : 1);
        put(p, x, y);
    }
}

static void add_arc(float cx, float cy, float r, float a0, float a1)
{
    Path *p = new_path();
    for (int i = 0; i <= 12; i++) {
        float a = lerpf(a0, a1, i / 12.0f);
        put(p, cx + cosf(a) * r, cy + sinf(a) * r);
    }
}

/* One of the simple forms: 0 circle, 1 triangle, 2 square. */
static void add_form(int kind, float cx, float cy, float r)
{
    if (kind == 0)
        add_circle(cx, cy, r);
    else if (kind == 1)
        add_poly(cx, cy + r * 0.15f, r * 1.12f, 3, -1.5708f + randr(-0.5f, 0.5f));
    else
        add_poly(cx, cy, r * 1.15f, 4, (mg_randi(0, 1) ? 0.7854f : 0) + randr(-0.25f, 0.25f));
}

/* Small part for the level-4 composite. */
static void add_part(int kind, float cx, float cy, float r)
{
    float a = randr(0, 6.2831853f);
    switch (kind) {
    case 0: case 1: case 2: add_form(kind, cx, cy, r); break;
    case 3: add_line(cx - cosf(a) * r * 1.3f, cy - sinf(a) * r * 1.3f, cx + cosf(a) * r * 1.3f,
                     cy + sinf(a) * r * 1.3f); break;
    case 4: add_arc(cx, cy, r, a, a + 3.1415927f); break;
    case 5: add_zigzag(cx - r * 1.2f, cx + r * 1.2f, cy, r * 0.5f, 2, randr(-0.3f, 0.3f)); break;
    default: add_star(cx, cy, r * 1.1f, 5, a); break;
    }
}

static void gen_level5(void)
{
    float x[8] = {0}, y[8] = {0};
    int n = mg_randi(6, 8), k = 1;
    for (int attempt = 0; attempt < 40 && k < n; attempt++) {
        x[0] = randr(90, 310);
        y[0] = randr(55, 185);
        float h = randr(0, 6.2831853f);
        k = 1;
        for (int tries = 0; k < n && tries < 200; tries++) {
            float turn = randr(0.7f, 2.4f) * (mg_randi(0, 1) ? 1 : -1);
            float hh = h + turn, d = randr(70, 110);
            float nx = x[k - 1] + cosf(hh) * d, ny = y[k - 1] + sinf(hh) * d * 0.8f;
            if (nx < 60 || nx > 340 || ny < 38 || ny > 202)
                continue;
            bool near = false;
            for (int j = 0; j < k - 1; j++)
                if (fabsf(nx - x[j]) + fabsf(ny - y[j]) < 60)
                    near = true;
            if (near)
                continue;
            x[k] = nx, y[k] = ny, h = hh, k++;
        }
    }
    if (k < 2)
        x[1] = x[0] + 80, y[1] = y[0], k = 2;
    n = k;   /* practically always the full 6-8 */
    /* one segment becomes a curve */
    int cs = mg_randi(0, n - 2);
    Path *p = new_path();
    for (int i = 0; i < n; i++) {
        if (i == cs + 1) {
            float mx = (x[cs] + x[i]) / 2, my = (y[cs] + y[i]) / 2;
            float dx = x[i] - x[cs], dy = y[i] - y[cs], side = mg_randi(0, 1) ? 1 : -1;
            float kk = randr(0.45f, 0.7f) * side;
            float qx = clampf(mx - dy * kk, 30, 370), qy = clampf(my + dx * kk, 30, 210);
            for (int s = 1; s < 12; s++) {
                float f = s / 12.0f, a = (1 - f) * (1 - f), b = 2 * f * (1 - f), c = f * f;
                put(p, a * x[cs] + b * qx + c * x[i], a * y[cs] + b * qy + c * y[i]);
            }
        }
        put(p, x[i], y[i]);
    }
}

static void gen_shape(int level)
{
    G.npaths = 0;
    float cx = 200 + randr(-20, 20), cy = 120 + randr(-10, 10);
    switch (level) {
    case 0:
        add_form(mg_randi(0, 2), cx, cy, randr(56, 70));
        break;
    case 1:
        if (mg_randi(0, 1)) {   /* two forms side by side, perhaps touching */
            int a = mg_randi(0, 2), b = (a + mg_randi(1, 2)) % 3;
            float gap = randr(55, 80), dy = randr(-25, 25);
            add_form(a, cx - gap, cy - dy, randr(36, 46));
            add_form(b, cx + gap, cy + dy, randr(36, 46));
        } else {                /* a form crossed or flanked by a line */
            float r = randr(46, 58), a = randr(0, 3.1415927f), off = randr(0, r * 1.2f);
            float len = randr(90, 120), px = cx + cosf(a + 1.5708f) * off, py = cy + sinf(a + 1.5708f) * off;
            add_form(mg_randi(0, 2), cx, cy, r);
            add_line(px - cosf(a) * len, py - sinf(a) * len * 0.75f, px + cosf(a) * len,
                     py + sinf(a) * len * 0.75f);
        }
        break;
    case 2: {
        int k = mg_randi(0, 2);
        if (k == 0)
            add_star(cx, cy, randr(70, 84), mg_randi(5, 6), randr(0, 6.28f));
        else if (k == 1)
            add_spiral(cx, cy, randr(74, 88), randr(2.0f, 2.6f), randr(0, 6.28f), mg_randi(0, 1) ? 1 : -1);
        else
            add_zigzag(randr(60, 90), randr(310, 340), cy, randr(34, 50), mg_randi(3, 5), randr(-0.25f, 0.25f));
        break;
    }
    case 3: {
        /* three parts on a loose triangle of positions, all different kinds */
        float px[3] = {125, 275, 200}, py[3] = {80, 80, 165};
        if (mg_randi(0, 1))
            py[0] = py[1] = 165, py[2] = 78;
        int kinds[7] = {0, 1, 2, 3, 4, 5, 6};
        for (int i = 6; i > 0; i--) {
            int j = mg_randi(0, i), tmp = kinds[i];
            kinds[i] = kinds[j];
            kinds[j] = tmp;
        }
        for (int i = 0; i < 3; i++)
            add_part(kinds[i], px[i] + randr(-15, 15), py[i] + randr(-10, 10), randr(30, 38));
        break;
    }
    default:
        gen_level5();
        break;
    }
    float x0 = 1e9f, y0 = 1e9f, x1 = -1e9f, y1 = -1e9f;
    for (int i = 0; i < G.npaths; i++)
        for (int j = 0; j < G.paths[i].n; j++) {
            x0 = fminf(x0, G.paths[i].x[j]), x1 = fmaxf(x1, G.paths[i].x[j]);
            y0 = fminf(y0, G.paths[i].y[j]), y1 = fmaxf(y1, G.paths[i].y[j]);
        }
    G.scx = (x0 + x1) / 2, G.scy = (y0 + y1) / 2;
    G.sw = x1 - x0, G.sh = y1 - y0;
}

static float path_len(const Path *p)
{
    float l = 0;
    for (int i = 1; i < p->n; i++)
        l += hypotf(p->x[i] - p->x[i - 1], p->y[i] - p->y[i - 1]);
    return l;
}

/* Calls fn for each target segment, up to `len` frame pixels of ink (the
 * last one cut short): used to draw the shape and to sketch it. */
typedef void (*SegFn)(const void *ctx, float x0, float y0, float x1, float y1);

static void walk_target(float len, SegFn fn, const void *ctx)
{
    float left = len;
    for (int pi = 0; pi < G.npaths; pi++) {
        const Path *p = &G.paths[pi];
        for (int i = 1; i < p->n; i++) {
            if (left <= 0)
                return;
            float x0 = p->x[i - 1], y0 = p->y[i - 1], x1 = p->x[i], y1 = p->y[i];
            float l = hypotf(x1 - x0, y1 - y0);
            if (l > left) {
                float f = left / l;
                x1 = x0 + (x1 - x0) * f, y1 = y0 + (y1 - y0) * f;
            }
            left -= l;
            fn(ctx, x0, y0, x1, y1);
        }
    }
}

/* Point at fraction f along path p. */
static void path_at(const Path *p, float f, float *x, float *y)
{
    float want = path_len(p) * clampf(f, 0, 1);
    for (int i = 1; i < p->n; i++) {
        float l = hypotf(p->x[i] - p->x[i - 1], p->y[i] - p->y[i - 1]);
        if (want <= l || i == p->n - 1) {
            float k = l > 0 ? clampf(want / l, 0, 1) : 0;
            *x = lerpf(p->x[i - 1], p->x[i], k);
            *y = lerpf(p->y[i - 1], p->y[i], k);
            return;
        }
        want -= l;
    }
    *x = p->x[0], *y = p->y[0];
}

/* The sketch timeline: ink along each path, then a pen-up hop to the next
 * one (hops cost half their length). Fills ink drawn so far and the marker. */
static float sketch_at(float s, float *ink, float *mx, float *my, bool *up)
{
    float total = 0, done = 0;
    *ink = 0, *up = false;
    *mx = G.npaths ? G.paths[0].x[0] : 200, *my = G.npaths ? G.paths[0].y[0] : 120;
    for (int k = 0; k < G.npaths; k++) {
        const Path *p = &G.paths[k];
        float l = path_len(p);
        if (s >= total && s < total + l) {
            path_at(p, (s - total) / l, mx, my);
            *ink = done + (s - total);
        } else if (s >= total + l) {
            *mx = p->x[p->n - 1], *my = p->y[p->n - 1];
            *ink = done + l;
        }
        total += l, done += l;
        if (k + 1 < G.npaths) {
            const Path *q = &G.paths[k + 1];
            float hop = hypotf(q->x[0] - p->x[p->n - 1], q->y[0] - p->y[p->n - 1]) * 0.5f;
            if (s >= total && s < total + hop) {
                float f = (s - total) / hop;
                *mx = lerpf(p->x[p->n - 1], q->x[0], f);
                *my = lerpf(p->y[p->n - 1], q->y[0], f);
                *up = true;
            }
            total += hop;
        }
    }
    return total;
}

/* ---- matching ------------------------------------------------------------------- */

typedef struct {
    float x[NR], y[NR];
    u8 s[NR];   /* stroke number: consecutive points of one stroke are joined */
    int n;
} PSet;

static float flat_x[MAX_PATHS * MAX_PPTS], flat_y[MAX_PATHS * MAX_PPTS];
static int flat_st[MAX_PATHS];

/* Spreads about N points evenly along the strokes (by length). */
static void resample(const float *xs, const float *ys, const int *st, int ns, int np, int N, PSet *o)
{
    float L = 0;
    o->n = 0;
    for (int k = 0; k < ns; k++) {
        int a = st[k], b = k + 1 < ns ? st[k + 1] : np;
        for (int i = a + 1; i < b; i++)
            L += hypotf(xs[i] - xs[i - 1], ys[i] - ys[i - 1]);
    }
    for (int k = 0; k < ns; k++) {
        int a = st[k], b = k + 1 < ns ? st[k + 1] : np;
        if (b <= a)
            continue;
        float Lk = 0;
        for (int i = a + 1; i < b; i++)
            Lk += hypotf(xs[i] - xs[i - 1], ys[i] - ys[i - 1]);
        int m = Lk < 0.5f || L <= 0 ? 1 : (int)(N * Lk / L + 0.5f);
        if (m < 2 && Lk >= 0.5f)
            m = 2;
        if (o->n + m > NR)
            m = NR - o->n;
        if (m <= 0)
            break;
        if (m == 1) {
            o->x[o->n] = xs[a], o->y[o->n] = ys[a], o->s[o->n++] = (u8)k;
            continue;
        }
        int i = a;
        float acc = 0;
        for (int j = 0; j < m; j++) {
            float want = Lk * j / (m - 1);
            float l = hypotf(xs[i + 1] - xs[i], ys[i + 1] - ys[i]);
            while (i + 2 < b && acc + l < want) {
                acc += l, i++;
                l = hypotf(xs[i + 1] - xs[i], ys[i + 1] - ys[i]);
            }
            float f = l > 0 ? clampf((want - acc) / l, 0, 1) : 0;
            o->x[o->n] = lerpf(xs[i], xs[i + 1], f);
            o->y[o->n] = lerpf(ys[i], ys[i + 1], f);
            o->s[o->n++] = (u8)k;
        }
    }
}

static void moments(const PSet *S, float *cx, float *cy, float *r)
{
    float sx = 0, sy = 0, ss = 0;
    for (int i = 0; i < S->n; i++)
        sx += S->x[i], sy += S->y[i];
    *cx = S->n ? sx / S->n : 0, *cy = S->n ? sy / S->n : 0;
    for (int i = 0; i < S->n; i++)
        ss += (S->x[i] - *cx) * (S->x[i] - *cx) + (S->y[i] - *cy) * (S->y[i] - *cy);
    *r = S->n ? sqrtf(ss / S->n) : 0;
}

/* Squared distance from (px, py) to the segment a-b. */
static float seg_d2(float px, float py, float ax, float ay, float bx, float by)
{
    float dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy;
    float f = l2 > 0 ? clampf(((px - ax) * dx + (py - ay) * dy) / l2, 0, 1) : 0;
    float ex = ax + dx * f - px, ey = ay + dy * f - py;
    return ex * ex + ey * ey;
}

/* Distance from a point to the strokes of S (lone points count as dots). */
static float dist_to(const PSet *S, float x, float y)
{
    float best = 1e9f;
    for (int i = 0; i < S->n; i++) {
        bool next = i + 1 < S->n && S->s[i + 1] == S->s[i];
        if (next)
            best = fminf(best, seg_d2(x, y, S->x[i], S->y[i], S->x[i + 1], S->y[i + 1]));
        else if (i == 0 || S->s[i - 1] != S->s[i])
            best = fminf(best, (x - S->x[i]) * (x - S->x[i]) + (y - S->y[i]) * (y - S->y[i]));
    }
    return sqrtf(best);
}

static int nearest(const PSet *S, float x, float y)
{
    int bi = 0;
    float best = 1e9f;
    for (int i = 0; i < S->n; i++) {
        float d = (x - S->x[i]) * (x - S->x[i]) + (y - S->y[i]) * (y - S->y[i]);
        if (d < best)
            best = d, bi = i;
    }
    return bi;
}

/* Undirected stroke directions, length-weighted, smoothed, summing to 1. */
#define HB 12
static void dir_hist(const PSet *S, float *h)
{
    float raw[HB] = {0}, sum = 0;
    for (int i = 0; i + 1 < S->n; i++) {
        if (S->s[i + 1] != S->s[i])
            continue;
        float dx = S->x[i + 1] - S->x[i], dy = S->y[i + 1] - S->y[i], l = hypotf(dx, dy);
        if (l <= 0)
            continue;
        float a = atan2f(dy, dx);
        if (a < 0)
            a += 3.1415927f;
        float f = a / 3.1415927f * HB;
        int b0 = (int)f % HB;
        float w = f - floorf(f);
        raw[b0] += l * (1 - w);
        raw[(b0 + 1) % HB] += l * w;
    }
    for (int i = 0; i < HB; i++) {
        h[i] = 0.5f * raw[i] + 0.25f * raw[(i + 1) % HB] + 0.25f * raw[(i + HB - 1) % HB];
        sum += h[i];
    }
    for (int i = 0; i < HB; i++)
        h[i] = sum > 0 ? h[i] / sum : 1.0f / HB;
}

/* How sharply the strokes turn (corners against curves), per point: the
 * turn between the chords to the points two steps back and two ahead. */
#define TB 6
static void turn_hist(const PSet *S, float *h)
{
    static const float EDGE[TB - 1] = {0.105f, 0.26f, 0.52f, 0.96f, 1.57f};   /* 6, 15, 30, 55, 90 degrees */
    float n = 0;
    for (int i = 0; i < TB; i++)
        h[i] = 0;
    for (int i = 2; i + 2 < S->n; i++) {
        if (S->s[i - 2] != S->s[i] || S->s[i + 2] != S->s[i])
            continue;
        float a1 = atan2f(S->y[i] - S->y[i - 2], S->x[i] - S->x[i - 2]);
        float a2 = atan2f(S->y[i + 2] - S->y[i], S->x[i + 2] - S->x[i]);
        float d = fabsf(a2 - a1);
        if (d > 3.1415927f)
            d = 6.2831853f - d;
        int b = 0;
        while (b < TB - 1 && d > EDGE[b])
            b++;
        h[b] += 1, n += 1;
    }
    for (int i = 0; i < TB; i++)
        h[i] = n > 0 ? h[i] / n : (i == 0);
}

static void xform(const PSet *U, const float *A, const float *t, float ucx, float ucy, PSet *o)
{
    o->n = U->n;
    for (int i = 0; i < U->n; i++) {
        float x = U->x[i] - ucx, y = U->y[i] - ucy;
        o->x[i] = A[0] * x + A[1] * y + t[0];
        o->y[i] = A[2] * x + A[3] * y + t[1];
        o->s[i] = U->s[i];
    }
}

#ifdef MATCH_DEBUG
static float dbg_F, dbg_ch, dbg_dir, dbg_pen, dbg_turn;
#endif

/* The scoring's knobs (see the header). */
#ifdef MATCH_DEBUG
#define KNOB static float
#else
#define KNOB static const float
#endif
KNOB K_T1 = 0.08f, K_T2 = 0.25f;      /* coverage: full credit within T1, none beyond T2 */
KNOB K_F0 = 0.50f, K_FW = 0.48f;      /* coverage F-score: 0 at F0, 1 at F0 + FW */
KNOB K_CH0 = 0.03f, K_CHW = 0.17f;    /* chamfer: 1 at CH0, 0 at CH0 + CHW */
KNOB K_DIR0 = 0.66f, K_DIRW = 0.30f;  /* direction histogram overlap: 0 at DIR0, 1 at DIR0 + DIRW */
KNOB K_TURN0 = 0.55f, K_TURNW = 0.35f; /* corner profile overlap: 0 at TURN0, 1 at TURN0 + TURNW */
KNOB K_WF = 0.30f, K_WC = 0.25f, K_WD = 0.25f, K_WT = 0.20f;
KNOB K_SOFT = 0.3f;                   /* how much the weakest measure drags the blend down */
/* likeness -> match %: a careful copy by hand is about 0.9, a sloppy but
 * recognisable one 0.45-0.7, a different shape 0.1-0.25, a scribble 0.1 */
static const float MAP_L[6] = {0.12f, 0.25f, 0.45f, 0.70f, 0.90f, 0.95f};
static const float MAP_P[6] = {0, 20, 60, 85, 98, 100};

static float credit(float d) { return clampf((K_T2 - d) / (K_T2 - K_T1), 0, 1); }

/* The likeness of the aligned drawing P to the normalised target T, 0..1. */
static float likeness(const PSet *P, const PSet *T, const float *ht, float s_turn)
{
    float pc = 0, rc = 0, dp = 0, dr = 0, hp[HB], inter = 0;
    for (int i = 0; i < P->n; i++) {
        float d = dist_to(T, P->x[i], P->y[i]);
        pc += credit(d), dp += d;
    }
    for (int j = 0; j < T->n; j++) {
        float d = dist_to(P, T->x[j], T->y[j]);
        rc += credit(d), dr += d;
    }
    float prec = pc / P->n, rec = rc / T->n;
    float F = prec + rec > 0 ? 2 * prec * rec / (prec + rec) : 0;
    float cham = 0.5f * (dp / P->n + dr / T->n);
    float s_f = clampf((F - K_F0) / K_FW, 0, 1);
    float s_ch = clampf(1 - (cham - K_CH0) / K_CHW, 0, 1);
    dir_hist(P, hp);
    for (int i = 0; i < HB; i++)
        inter += fminf(hp[i], ht[i]);
    float s_dir = clampf((inter - K_DIR0) / K_DIRW, 0, 1);
#ifdef MATCH_DEBUG
    dbg_F = F, dbg_ch = cham, dbg_dir = inter;
#endif
    float lin = K_WF * s_f + K_WC * s_ch + K_WD * s_dir + K_WT * s_turn;
    float worst = fminf(fminf(s_f, s_ch), fminf(s_dir, s_turn));
    return lin * (1 - K_SOFT + K_SOFT * worst);
}

static int compute_match(void)
{
    G.rn = 0;
    if (G.nu < 2)
        return 0;
    static PSet T, U, P;
    int np = 0, ns = 0;
    for (int k = 0; k < G.npaths; k++) {
        flat_st[ns++] = np;
        for (int i = 0; i < G.paths[k].n; i++)
            flat_x[np] = G.paths[k].x[i], flat_y[np] = G.paths[k].y[i], np++;
    }
    resample(flat_x, flat_y, flat_st, ns, np, 112, &T);
    resample(G.ux, G.uy, G.sstart, G.ns, G.nu, 112, &U);
    float tcx, tcy, tr, ucx, ucy, ur;
    moments(&T, &tcx, &tcy, &tr);
    moments(&U, &ucx, &ucy, &ur);
    G.tcx = tcx, G.tcy = tcy, G.tr = tr, G.ucx = ucx, G.ucy = ucy;
    if (ur < 3 || tr <= 0 || U.n < 2)
        return 0;   /* a dot */

    /* the target in its normalised frame */
    float tsx = 0, tsy = 0, usx = 0, usy = 0, ht[HB];
    for (int i = 0; i < T.n; i++) {
        T.x[i] = (T.x[i] - tcx) / tr, T.y[i] = (T.y[i] - tcy) / tr;
        tsx += T.x[i] * T.x[i], tsy += T.y[i] * T.y[i];
    }
    for (int i = 0; i < U.n; i++) {
        float x = (U.x[i] - ucx) / ur, y = (U.y[i] - ucy) / ur;
        usx += x * x, usy += y * y;
    }
    tsx = sqrtf(tsx / T.n), tsy = sqrtf(tsy / T.n), usx = sqrtf(usx / U.n), usy = sqrtf(usy / U.n);
    dir_hist(&T, ht);
    float th1[TB], th2[TB], turn = 0;
    turn_hist(&T, th1);
    turn_hist(&U, th2);
    for (int i = 0; i < TB; i++)
        turn += fminf(th1[i], th2[i]);
    float s_turn = clampf((turn - K_TURN0) / K_TURNW, 0, 1);

    /* aspect: pull yours towards the target's, a mild cost only when far off */
    float ratio = (fmaxf(tsx, 0.1f) / fmaxf(tsy, 0.1f)) / (fmaxf(usx, 0.1f) / fmaxf(usy, 0.1f));
    float c = clampf(ratio, 1 / 1.5f, 1.5f), sc = sqrtf(c);
    float g = 1 / sqrtf(c * usx * usx + usy * usy / c);
    float ax = sc * g / ur, ay = g / (sc * ur);
    float lr = fabsf(logf(ratio));
    float aspect_pen = 1 - 0.2f * clampf((lr - 0.336f) / (1.03f - 0.336f), 0, 1);

    float best = -1, bestA[4] = {1, 0, 0, 1}, bestT[2] = {0, 0};
    for (int ri = -3; ri <= 3; ri++) {
        float th = ri * 4 * 3.1415927f / 180, cs = cosf(th), sn = sinf(th);
        float A[4] = {cs * ax, -sn * ay, sn * ax, cs * ay}, t[2] = {0, 0};
        /* refine offset and size by symmetric nearest points */
        for (int it = 0; it < 2; it++) {
            xform(&U, A, t, ucx, ucy, &P);
            static float px[2 * NR], py[2 * NR], qx[2 * NR], qy[2 * NR];
            int m = 0;
            for (int i = 0; i < P.n; i++) {
                int j = nearest(&T, P.x[i], P.y[i]);
                px[m] = P.x[i], py[m] = P.y[i], qx[m] = T.x[j], qy[m] = T.y[j], m++;
            }
            for (int j = 0; j < T.n; j++) {
                int i = nearest(&P, T.x[j], T.y[j]);
                px[m] = P.x[i], py[m] = P.y[i], qx[m] = T.x[j], qy[m] = T.y[j], m++;
            }
            float mpx = 0, mpy = 0, mqx = 0, mqy = 0, num = 0, den = 0;
            for (int i = 0; i < m; i++)
                mpx += px[i], mpy += py[i], mqx += qx[i], mqy += qy[i];
            mpx /= m, mpy /= m, mqx /= m, mqy /= m;
            for (int i = 0; i < m; i++) {
                num += (px[i] - mpx) * (qx[i] - mqx) + (py[i] - mpy) * (qy[i] - mqy);
                den += (px[i] - mpx) * (px[i] - mpx) + (py[i] - mpy) * (py[i] - mpy);
            }
            float s = den > 0 ? clampf(num / den, 0.87f, 1.15f) : 1;
            float dx = clampf(mqx - s * mpx, -0.25f, 0.25f), dy = clampf(mqy - s * mpy, -0.25f, 0.25f);
            for (int k = 0; k < 4; k++)
                A[k] *= s;
            t[0] = s * t[0] + dx, t[1] = s * t[1] + dy;
        }
        xform(&U, A, t, ucx, ucy, &P);
        float l = likeness(&P, &T, ht, s_turn);
        if (l > best) {
            best = l;
            memcpy(bestA, A, sizeof(bestA));
            memcpy(bestT, t, sizeof(bestT));
        }
    }
    best *= aspect_pen;
#ifdef MATCH_DEBUG
    xform(&U, bestA, bestT, ucx, ucy, &P);
    likeness(&P, &T, ht, s_turn);
    dbg_pen = aspect_pen;
    dbg_turn = turn;
#endif

    /* keep the alignment for the review */
    memcpy(G.A, bestA, sizeof(G.A));
    memcpy(G.At, bestT, sizeof(G.At));
    float det = bestA[0] * bestA[3] - bestA[1] * bestA[2];
    G.Ai[0] = bestA[3] / det, G.Ai[1] = -bestA[1] / det, G.Ai[2] = -bestA[2] / det, G.Ai[3] = bestA[0] / det;
    xform(&U, bestA, bestT, ucx, ucy, &P);
    float x0 = 1e9f, y0 = 1e9f, x1 = -1e9f, y1 = -1e9f;
    for (int i = 0; i < T.n; i++)
        x0 = fminf(x0, T.x[i]), x1 = fmaxf(x1, T.x[i]), y0 = fminf(y0, T.y[i]), y1 = fmaxf(y1, T.y[i]);
    G.rev_cx = (x0 + x1) / 2, G.rev_cy = (y0 + y1) / 2;
    G.rev_k = REV_FIT / fmaxf(fmaxf(x1 - x0, y1 - y0), 0.5f);
    G.rn = P.n;
    memcpy(G.rx, P.x, sizeof(float) * P.n);
    memcpy(G.ry, P.y, sizeof(float) * P.n);
    memcpy(G.rs, P.s, (size_t)P.n);

    float pf = 100;
    for (int i = 0; i < 6; i++)
        if (best < MAP_L[i]) {
            pf = i == 0 ? 0 : lerpf(MAP_P[i - 1], MAP_P[i], (best - MAP_L[i - 1]) / (MAP_L[i] - MAP_L[i - 1]));
            break;
        }
    int pct = (int)(pf + 0.5f);
    return pct < 0 ? 0 : (pct > 100 ? 100 : pct);
}

/* ---- speech ----------------------------------------------------------------------- */

static void say(const char *s)
{
    G.say = s;
    G.say_len = s ? (int)strlen(s) : 0;
    G.say_n = 0;
    G.say_t = 0;
}

static const char *pick(const char *const *lines, int n) { return lines[mg_randi(0, n - 1)]; }
#define PICK(a) pick(a, (int)ARRAY_LEN(a))

static const char *const L_INTRO[LEVELS][2] = {
    {"Welcome to shapes class! An easy one first.", "Hello, class! Let's warm up with a simple one."},
    {"Exercise two: now there are two bits.", "Number two! A pair of things this time."},
    {"Exercise three. This one's a bit fancy.", "Three! Something with a little flourish."},
    {"Exercise four: three shapes at once!", "Four! A whole little family of shapes."},
    {"Last one! A long, twisty line. Good luck!", "The final exam! One long wiggly line."},
};
static const char *const L_SKETCH[] = {"Watch closely...", "Like so... and so...", "Squeak, squeak...",
                                       "Mind the corners..."};
static const char *const L_VIEW[] = {"Memorise it! I'll hide it soon.", "Got it? Take a good look!",
                                     "Look closely now..."};
static const char *const L_HIDE[] = {"Aaand... flip!", "Gone! No peeking.", "Hup! Hidden."};
static const char *const L_DRAW[] = {"Your turn! Only the shape counts.", "Draw it! Big or small, I don't mind.",
                                     "Your turn! Anywhere on your pad."};
static const char *const L_IDLE[] = {"Hmm hm hmm...", "Take your time.", "Ooh, I'm curious!",
                                     "Shape, not size. Shape!", "I'm not looking. Much."};
static const char *const L_GOOD[] = {"Wonderful! That's exactly it!", "Oh! I'm framing this one!",
                                     "A perfect echo! Gold star!", "Yes! Just like mine!"};
static const char *const L_OK[] = {"Not bad! I can see it.", "Close! A little wobbly.", "Good bones! Nearly there.",
                                   "Mostly right! Mostly."};
static const char *const L_BAD[] = {"...What is this.", "Is that... a potato?", "Bold. Wrong, but bold.",
                                    "Hm. I'll pretend I didn't see that."};

/* ---- flow ------------------------------------------------------------------------- */

static void set_phase(int ph)
{
    G.phase = ph;
    G.pt = 0;
}

static void clear_drawing(void)
{
    G.nu = G.ns = 0;
    G.stroking = false;
}

/* A fresh shape for the current exercise (after the wipe). */
static void new_shape(void)
{
    gen_shape(G.level);
    G.rn = 0;
    G.sk_s = G.sk_ink = 0;
    G.sk_total = sketch_at(0, &G.sk_ink, &G.mk_x, &G.mk_y, &G.mk_up);
    G.sk_speed = clampf(G.sk_total / 2.0f, 240, 520);
}

static void begin_round(void)
{
    clear_drawing();
    G.timed_out = G.low_warned = G.stamped = G.reacted = G.papered = false;
    G.peek = false;
    G.last_tick = 99;
    G.hint = NULL;
    if (G.level == 0) {
        new_shape();
        set_phase(PH_INTRO);
        say(L_INTRO[0][mg_randi(0, 1)]);
    } else {   /* last exercise's shape stays until it is wiped */
        set_phase(PH_WIPE);
        mg_sfx("draw_board_wipe");
    }
}

static void start(u32 seed)
{
    (void)seed;   /* mg_rand() is already seeded for this run */
    memset(&G, 0, sizeof(G));
    begin_round();
}

static void end_stroke(void)
{
    if (G.stroking) {
        G.stroking = false;
        mg_sfx("draw_stroke_end");
    }
}

static void submit(bool timeout)
{
    end_stroke();
    G.match[G.level] = compute_match();
    G.react = G.match[G.level] >= 75 ? 2 : G.match[G.level] >= 40 ? 1 : 0;
    G.timed_out = timeout;
    mg_sfx(timeout ? "draw_timeout" : "draw_submit");
    say(timeout ? "Time's up! Let's have a look." : "Done? Let's see it!");
    set_phase(PH_REVIEW);
}

static void show_hint(const char *s)
{
    G.hint = s;
    G.hint_t = 1.6f;
}

static bool in_canvas(int x, int y) { return x >= CV_X && x < CV_X + CV_W && y >= CV_Y && y < CV_Y + CV_H; }

static void add_point(int tx, int ty, bool first)
{
    float x = clampf(tx - CV_X, 0, CV_W - 1), y = clampf(ty - CV_Y, 0, CV_H - 1);
    if (!first && G.nu > 0 && hypotf(x - G.ux[G.nu - 1], y - G.uy[G.nu - 1]) < 3)
        return;
    if (G.nu >= MAX_UPTS) {
        show_hint("Out of ink: Undo or Clear");
        return;
    }
    G.ux[G.nu] = x, G.uy[G.nu] = y, G.nu++;
}

static void undo(void)
{
    end_stroke();
    if (G.ns > 0) {
        G.nu = G.sstart[--G.ns];
        mg_sfx("draw_undo");
    }
}

static void clear(void)
{
    end_stroke();
    if (G.nu > 0) {
        clear_drawing();
        mg_sfx("draw_clear");
    }
}

static void done(void)
{
    if (G.nu < 2) {
        end_stroke();
        show_hint("Draw something first");
        mg_sfx("draw_empty");
        return;
    }
    submit(false);
}

static void update_draw(const Input *in, bool touch, bool fresh)
{
    if (fresh) {
        if (in_canvas(in->tx, in->ty)) {
            if (G.ns < MAX_USTROKES && G.nu < MAX_UPTS) {
                G.sstart[G.ns++] = G.nu;
                G.stroking = true;
                add_point(in->tx, in->ty, true);
                mg_sfx("draw_stroke_start");
            } else {
                show_hint("Out of ink: Undo or Clear");
            }
        } else if (in->ty >= BTN_Y && in->ty < BTN_Y + BTN_H) {
            for (int i = 0; i < 3; i++)
                if (in->tx >= BTN_X[i] && in->tx < BTN_X[i] + BTN_W[i]) {
                    if (i == 0) undo();
                    else if (i == 1) clear();
                    else done();
                    return;
                }
        }
    } else if (touch && G.stroking) {
        add_point(in->tx, in->ty, false);
    } else if (!touch) {
        end_stroke();
    }
    if (G.phase != PH_DRAW)
        return;
    if (in->down & KEY_B_)
        undo();
    else if (in->down & KEY_Y_)
        clear();
    else if (in->down & KEY_A_)
        done();
}

/* The cheat: Pim gets distracted and the board stays (or flips back) up. */
static bool can_cheat(void) { return G.phase >= PH_INTRO && G.phase <= PH_DRAW && !G.peek; }

static void use_cheat(void)
{
    G.peek = G.peek_level[G.level] = true;
    mg_sfx("draw_spirit_oops");
    if (G.phase == PH_HIDE || G.phase == PH_DRAW)
        say("Whoops! The board slipped. I'm not looking!");
    else
        say("Ooh! A moth! Hello, little moth...");
}

/* Voice blips as the speech bubble types itself out. */
static void update_speech(float dt)
{
    if (!G.say)
        return;
    G.say_t += dt;
    int n = (int)(G.say_t * SAY_CPS);
    if (n > G.say_len)
        n = G.say_len;
    bool blip = false;
    for (int i = G.say_n; i < n; i++) {
        char ch = G.say[i];
        if (!blip && i % 3 == 0 && ch != ' ' && ch != '.') {
            float pitch = 0.92f + 0.05f * (float)((ch * 7) % 7);
            if (strchr("aeiouAEIOU", ch))
                pitch += 0.12f;
            mg_sfx_pitch("draw_spirit_voice", pitch);
            blip = true;
        }
    }
    G.say_n = n;
}

static void update_board(float dt)
{
    float goal = (G.phase == PH_HIDE || G.phase == PH_DRAW) && !G.peek ? 1.0f : 0.0f;
    if (goal != G.flip_goal) {
        G.flip_goal = goal;
        if (fabsf(G.flip - goal) > 0.01f)
            mg_sfx("draw_board_flip");
    }
    float step = dt / FLIP_TIME;
    G.flip = G.flip < goal ? fminf(goal, G.flip + step) : fmaxf(goal, G.flip - step);
}

static bool update(const Input *in, float dt, bool cheat)
{
    /* Touch state from held or down (the desktop bot only sets `down`);
     * a fresh touch is one that was not there last frame. */
    bool touch = ((in->held | in->down) & KEY_TOUCH_) != 0;
    bool fresh = touch && !G.touching;
    G.touching = touch;
    G.t += dt;
    G.pt += dt;
    if (G.hint_t > 0)
        G.hint_t -= dt;
    if (cheat && can_cheat())
        use_cheat();
    update_speech(dt);
    update_board(dt);
    switch (G.phase) {
    case PH_WIPE:
        if (G.pt >= WIPE_TIME) {
            new_shape();
            set_phase(PH_INTRO);
            mg_sfx("draw_level_up");
            say(L_INTRO[G.level][mg_randi(0, 1)]);
        }
        break;
    case PH_INTRO:
        if (G.pt >= INTRO_TIME) {
            set_phase(PH_SKETCH);
            mg_sfx("draw_marker_uncap");
            G.squeak_t = 0.12f;
            if (!G.peek)
                say(PICK(L_SKETCH));
        }
        break;
    case PH_SKETCH: {
        if (G.pt < 0.25f)
            break;   /* uncapping */
        bool was_up = G.mk_up;
        G.sk_s += G.sk_speed * dt;
        sketch_at(G.sk_s, &G.sk_ink, &G.mk_x, &G.mk_y, &G.mk_up);
        G.squeak_t -= dt;
        if (!G.mk_up && (was_up || G.squeak_t <= 0)) {
            mg_sfx_pitch("draw_marker_squeak", 0.85f + 0.35f * mg_randf());
            G.squeak_t = randr(0.16f, 0.28f);
        }
        if (G.sk_s >= G.sk_total) {
            G.sk_ink = 1e9f;
            set_phase(PH_VIEW);
            mg_sfx("draw_board_tap");
            if (!G.peek)
                say(PICK(L_VIEW));
        }
        break;
    }
    case PH_VIEW: {
        float left = VIEW_TIME[G.level] - G.pt;
        int sec = (int)ceilf(left);
        if (sec < G.last_tick && sec <= 3 && sec >= 1 && left < VIEW_TIME[G.level] - 0.5f)
            mg_sfx("draw_tick");
        G.last_tick = sec;
        if (left <= 0) {
            set_phase(PH_HIDE);
            if (G.peek)
                say("...little moth... so fluffy...");
            else
                say(PICK(L_HIDE));
        }
        break;
    }
    case PH_HIDE:
        if (G.pt >= HIDE_TIME) {
            set_phase(PH_DRAW);   /* a touch held from before starts no stroke */
            G.idle_t = 7.5f;
            if (!G.peek)
                say(G.level == 0 ? "Your turn! Any size, anywhere on your pad." : PICK(L_DRAW));
        }
        break;
    case PH_DRAW:
        update_draw(in, touch, fresh);
        if (G.phase != PH_DRAW)
            break;
        G.idle_t -= dt;
        if (!G.low_warned && G.pt >= DRAW_TIME - 5) {
            G.low_warned = true;
            mg_sfx("draw_time_low");
            say("Five seconds!");
        } else if (G.idle_t <= 0 && G.pt < DRAW_TIME - 6) {
            G.idle_t = 7.0f;
            if (!G.peek)
                say(PICK(L_IDLE));
        }
        if (G.pt >= DRAW_TIME)
            submit(true);
        break;
    case PH_REVIEW: {
        if (!G.papered && G.pt >= REV_MORPH) {
            G.papered = true;
            mg_sfx("draw_paper_hold");
        }
        if (!G.stamped && G.pt >= REV_STAMP) {
            G.stamped = true;
            mg_sfx(G.react == 2 ? "draw_score_good" : G.react == 1 ? "draw_score_ok" : "draw_score_bad");
            if (G.peek && G.react == 2)
                say("Wow! Almost as if you could see it...");
            else
                say(G.react == 2 ? PICK(L_GOOD) : G.react == 1 ? PICK(L_OK) : PICK(L_BAD));
        }
        if (!G.reacted && G.pt >= REV_STAMP + 0.2f) {
            G.reacted = true;
            mg_sfx(G.react == 2 ? "draw_spirit_delight" : G.react == 1 ? "draw_spirit_hmm" : "draw_spirit_meh");
        }
        if (G.pt >= REV_END || (G.pt > REV_STAMP + 0.3f && ((in->down & KEY_A_) || fresh))) {
            if (++G.level >= LEVELS)
                return false;
            begin_round();
        }
        break;
    }
    }
    return true;
}

/* ---- drawing: helpers --------------------------------------------------------------- */

static float ease(float f)
{
    f = clampf(f, 0, 1);
    return f * f * (3 - 2 * f);
}

/* A line whose two ends sit at different depths. */
static void line_d(int eye, float x0, float y0, float d0, float x1, float y1, float d1, float th, u32 c)
{
    gfx_line(x0 + mg_shift(eye, d0), y0, x1 + mg_shift(eye, d1), y1, th, c);
}

/* A quad (corners in order) whose corners sit at different depths. */
static void quad_d(int eye, const float *x, const float *y, const float *d, u32 c)
{
    float s[4];
    for (int i = 0; i < 4; i++)
        s[i] = x[i] + mg_shift(eye, d[i]);
    gfx_triangle(s[0], y[0], s[1], y[1], s[2], y[2], c);
    gfx_triangle(s[0], y[0], s[2], y[2], s[3], y[3], c);
}

/* The board panel turns about its horizontal centre line: a screen point
 * (x, y) on the flat panel goes to (*ox, *oy) at depth *od. */
static void board_pt(float x, float y, float *ox, float *oy, float *od)
{
    float a = G.flip * 3.1415927f, c = fabsf(cosf(a)), s = sinf(a);
    float rel = (y - BCY) / (BH / 2 + 4);
    *od = -rel * s * 0.45f;
    *oy = BCY + (y - BCY) * c;
    *ox = BCX + (x - BCX) * (1 - 0.1f * *od);
}

static bool board_front(void) { return G.flip < 0.5f; }

/* Shape frame -> screen: the board, morphed towards the review spot. */
static void target_pt(float x, float y, float morph, float *ox, float *oy)
{
    float bx = BX + x * BS, by = BY + y * BS;
    if (morph > 0) {
        float rx = REV_TX + ((x - G.tcx) / G.tr - G.rev_cx) * G.rev_k;
        float ry = REV_Y + ((y - G.tcy) / G.tr - G.rev_cy) * G.rev_k;
        bx = lerpf(bx, rx, morph), by = lerpf(by, ry, morph);
    }
    *ox = bx, *oy = by;
}

static const u32 MARKER_COL[LEVELS] = {
    RGBA(36, 44, 80, 255), RGBA(30, 120, 70, 255), RGBA(200, 50, 60, 255), RGBA(40, 90, 200, 255),
    RGBA(120, 50, 160, 255),
};
#define PAD_INK RGBA(40, 70, 170, 255)
#define BODY RGBA(168, 206, 250, 255)
#define BODY_DARK RGBA(130, 170, 225, 255)
#define FACE RGBA(30, 30, 50, 255)

typedef struct {
    int eye;
    float morph, alpha, thick;
    u32 col;
} InkCtx;

static void ink_seg(const void *ctx, float x0, float y0, float x1, float y1)
{
    const InkCtx *c = ctx;
    float ax, ay, bx, by, sx, sy, sd, ex, ey, ed;
    target_pt(x0, y0, c->morph, &ax, &ay);
    target_pt(x1, y1, c->morph, &bx, &by);
    board_pt(ax, ay, &sx, &sy, &sd);
    board_pt(bx, by, &ex, &ey, &ed);
    line_d(c->eye, sx, sy, sd - 0.01f, ex, ey, ed - 0.01f, c->thick, rgba_alpha(c->col, c->alpha));
    mg_circle(c->eye, ex, ey, c->thick * 0.5f, ed - 0.01f, rgba_alpha(c->col, c->alpha));
}

static void draw_target(int eye, float len, float morph, float alpha)
{
    float th = lerpf(3.0f, 2.4f, morph);
    InkCtx c = {eye, morph, alpha, th, MARKER_COL[G.level]};
    walk_target(len, ink_seg, &c);
}

/* ---- drawing: the room ----------------------------------------------------------- */

static void draw_room(int eye)
{
    mg_sky(eye, RGBA(64, 46, 104, 255), RGBA(104, 78, 142, 255));
    /* the arched window behind Pim: the Purgatorium's night outside */
    mg_circle(eye, 67, 64, 52, 0.75f, RGBA(80, 56, 70, 255));
    mg_rect(eye, 15, 64, 104, 96, 0.75f, RGBA(80, 56, 70, 255));
    mg_circle(eye, 67, 64, 46, 0.74f, RGBA(26, 18, 58, 255));
    mg_rect(eye, 21, 64, 92, 90, 0.74f, RGBA(26, 18, 58, 255));
    for (int i = 0; i < 9; i++) {   /* stars and drifting lights far outside */
        float x = 30 + fmodf(i * 37.3f + G.t * (2 + i % 3), 74);
        float y = 34 + fmodf(i * 53.1f, 110);
        float tw = 0.4f + 0.6f * fabsf(sinf(G.t * 1.4f + i * 1.7f));
        mg_circle(eye, x, y, i % 3 == 0 ? 1.8f : 1.0f, 0.95f, rgba_alpha(RGBA(255, 236, 190, 255), tw));
    }
    mg_rect(eye, 65, 18, 4, 136, 0.73f, RGBA(80, 56, 70, 255));
    mg_rect(eye, 21, 92, 92, 4, 0.73f, RGBA(80, 56, 70, 255));
    mg_rect(eye, 10, 154, 114, 6, 0.7f, RGBA(120, 90, 96, 255));   /* sill */
    /* the moth Pim can't resist */
    if (G.peek) {
        float mx = 54 + 22 * sinf(G.t * 1.7f), my = 70 + 16 * sinf(G.t * 2.9f), f = 4 * fabsf(sinf(G.t * 18));
        mg_tri(eye, mx, my, mx - 6, my - f, mx - 5, my + 3, 0.68f, RGBA(240, 230, 200, 255));
        mg_tri(eye, mx, my, mx + 6, my - f, mx + 5, my + 3, 0.68f, RGBA(240, 230, 200, 255));
    }
    /* the floor */
    mg_rect(eye, -10, 172, TOP_W + 20, 6, 0.42f, RGBA(70, 46, 70, 255));
    mg_rect(eye, -10, 178, TOP_W + 20, 70, 0.36f, RGBA(120, 84, 96, 255));
    mg_line(eye, -10, 196, TOP_W + 10, 196, 1, 0.26f, RGBA(96, 64, 80, 255));
    mg_line(eye, -10, 218, TOP_W + 10, 218, 1, 0.16f, RGBA(96, 64, 80, 255));
    /* a couple of little lights drifting in the room */
    for (int i = 0; i < 4; i++) {
        float x = fmodf(20 + i * 97 + G.t * (6 + i * 2), 420) - 10;
        float y = 30 + fmodf(i * 61.0f - G.t * (4 + i), 150) + (i * 61.0f - G.t * (4 + i) < 0 ? 150 : 0);
        float d = 0.5f + 0.08f * i;
        mg_circle(eye, x, y, 5, d, RGBA(255, 210, 140, 40));
        mg_circle(eye, x, y, 1.6f, d, RGBA(255, 236, 190, 220));
    }
}

/* ---- drawing: the board ---------------------------------------------------------- */

static void panel_quad(int eye, float x0, float y0, float x1, float y1, u32 c)
{
    float xs[4], ys[4], ds[4];
    board_pt(x0, y0, &xs[0], &ys[0], &ds[0]);
    board_pt(x1, y0, &xs[1], &ys[1], &ds[1]);
    board_pt(x1, y1, &xs[2], &ys[2], &ds[2]);
    board_pt(x0, y1, &xs[3], &ys[3], &ds[3]);
    quad_d(eye, xs, ys, ds, c);
}

static void board_text(int eye, const char *s, float x, float y, float sc, u32 c)
{
    if (G.flip > 0.02f)
        return;   /* text can't turn with the panel */
    mg_text(eye, s, x, y, sc, -0.01f, c);
}

static u32 stamp_col(int react)
{
    return react == 2 ? RGBA(40, 150, 80, 255) : react == 1 ? RGBA(210, 140, 30, 255) : RGBA(210, 60, 60, 255);
}

static void draw_board(int eye)
{
    char buf[48];
    /* the stand: two posts on feet, pivots at the panel's centre line */
    for (int s = 0; s < 2; s++) {
        float x = s ? BX + BW + 6 : BX - 10;
        mg_rect(eye, x, 40, 4, 154, 0.04f, RGBA(150, 150, 170, 255));
        mg_rect(eye, x - 10, 192, 24, 4, 0.04f, RGBA(110, 110, 130, 255));
        mg_circle(eye, x + 2, BCY, 4, 0.02f, RGBA(190, 190, 210, 255));
    }
    /* the panel */
    panel_quad(eye, BX - 4, BY - 4, BX + BW + 4, BY + BH + 4, RGBA(176, 180, 196, 255));
    bool front = board_front();
    panel_quad(eye, BX, BY, BX + BW, BY + BH, front ? RGBA(250, 250, 246, 255) : RGBA(232, 232, 226, 255));
    if (!front) {
        /* Pim's doodle on the back: a little ghost with a heart */
        float cx = BCX, cy = BCY, x, y, d, x1, y1, d1;
        board_pt(cx, cy - 8, &x, &y, &d);
        mg_circle(eye, x, y, 14 * fabsf(cosf(G.flip * 3.1415927f)) + 0.1f, d - 0.01f, RGBA(150, 190, 240, 120));
        board_pt(cx + 40, cy - 30, &x1, &y1, &d1);
        mg_circle(eye, x1 - 3, y1, 4, d1 - 0.01f, RGBA(240, 120, 140, 160));
        mg_circle(eye, x1 + 3, y1, 4, d1 - 0.01f, RGBA(240, 120, 140, 160));
        mg_tri(eye, x1 - 7, y1 + 1, x1 + 7, y1 + 1, x1, y1 + 8, d1 - 0.01f, RGBA(240, 120, 140, 160));
        if (G.flip > 0.98f)
            mg_text_centered(eye, "no peeking!", cx, cy + 14, 0.45f, -0.01f, RGBA(150, 150, 170, 255));
        return;
    }
    /* the front's contents */
    switch (G.phase) {
    case PH_WIPE: {
        /* last exercise's review being wiped away */
        float f = G.pt / WIPE_TIME;
        if (G.level > 0) {
            int prev = G.level - 1;
            InkCtx c = {eye, 1, clampf(1 - f * 1.3f, 0, 1), 2.4f, MARKER_COL[prev]};
            walk_target(1e9f, ink_seg, &c);
            snprintf(buf, sizeof(buf), "%d%%", G.match[prev]);
            mg_text_centered(eye, buf, REV_SCORE_X, 140, 0.8f, -0.01f, rgba_alpha(stamp_col(G.react), 1 - f));
        }
        break;
    }
    case PH_INTRO:
    case PH_SKETCH:
    case PH_VIEW:
    case PH_HIDE:
    case PH_DRAW: {
        snprintf(buf, sizeof(buf), "Exercise %d", G.level + 1);
        board_text(eye, buf, BX + 6, BY + 3, 0.42f, RGBA(150, 150, 170, 255));
        if (G.phase == PH_INTRO)
            break;
        draw_target(eye, G.phase == PH_SKETCH ? G.sk_ink : 1e9f, 0, 1);
        break;
    }
    case PH_REVIEW: {
        float morph = ease((G.pt - REV_MORPH) / 0.5f);
        draw_target(eye, 1e9f, morph, 1);
        if (G.pt >= REV_STAMP) {
            int m = G.match[G.level];
            float pop = ease((G.pt - REV_STAMP) / 0.25f);
            snprintf(buf, sizeof(buf), "%d%%", m);
            u32 col = stamp_col(G.react);
            mg_text_centered(eye, buf, REV_SCORE_X, 140, 0.5f + 0.3f * pop, -0.01f - 0.08f * (1 - pop), col);
            if (G.peek)
                board_text(eye, "(peeked)", BX + 8, BY + BH - 14, 0.4f, RGBA(150, 150, 170, 255));
            else if (G.timed_out)
                board_text(eye, "(time up)", BX + 8, BY + BH - 14, 0.4f, RGBA(150, 150, 170, 255));
        }
        break;
    }
    }
}

/* Your drawing on the sheet of paper Pim holds up. */
static void draw_paper(int eye, float lift)
{
    if (lift <= 0)
        return;
    float dy = (1 - ease(lift)) * 150, x0 = REV_PX - PAPER / 2, y0 = REV_Y - PAPER / 2 + dy;
    float d = -0.1f;
    mg_rect(eye, x0 + 2, y0 + 3, PAPER, PAPER, d + 0.02f, RGBA(0, 0, 0, 50));
    mg_rect(eye, x0, y0, PAPER, PAPER, d, RGBA(246, 242, 228, 255));
    for (int i = 1; i < 5; i++)
        mg_rect(eye, x0 + 4, y0 + i * 20, PAPER - 8, 1, d - 0.002f, RGBA(150, 180, 230, 90));
    for (int i = 0; i + 1 < G.rn; i++) {
        if (G.rs[i + 1] != G.rs[i])
            continue;
        float ax = REV_PX + (G.rx[i] - G.rev_cx) * G.rev_k, ay = REV_Y + dy + (G.ry[i] - G.rev_cy) * G.rev_k;
        float bx = REV_PX + (G.rx[i + 1] - G.rev_cx) * G.rev_k, by = REV_Y + dy + (G.ry[i + 1] - G.rev_cy) * G.rev_k;
        ax = clampf(ax, x0 + 2, x0 + PAPER - 2), bx = clampf(bx, x0 + 2, x0 + PAPER - 2);
        ay = clampf(ay, y0 + 2, y0 + PAPER - 2), by = clampf(by, y0 + 2, y0 + PAPER - 2);
        mg_line(eye, ax, ay, bx, by, 2.2f, d - 0.004f, PAD_INK);
    }
}

/* ---- drawing: Pim ------------------------------------------------------------------- */

enum { MOOD_NEUTRAL, MOOD_CHATTY, MOOD_HAPPY, MOOD_MEH, MOOD_SURPRISED, MOOD_FOCUS };

typedef struct {
    float x, y;            /* head centre */
    int mood;
    bool talk;
    float lx, ly;          /* where the eyes look (-1..1) */
    bool arm;              /* the right arm reaches for (ax, ay) */
    float ax, ay;
    bool both_up;          /* delighted: both arms up */
} Pose;

static void eye_at(int eye, float ex, float ey, float d, const Pose *p)
{
    const float R = PIM_R;
    float px = ex + p->lx * 0.06f * R, py = ey + p->ly * 0.06f * R;
    switch (p->mood) {
    case MOOD_HAPPY:   /* ^ ^ */
        mg_line(eye, ex - 0.14f * R, ey + 0.04f * R, ex, ey - 0.1f * R, 2.2f, d, FACE);
        mg_line(eye, ex, ey - 0.1f * R, ex + 0.14f * R, ey + 0.04f * R, 2.2f, d, FACE);
        break;
    case MOOD_SURPRISED:
        mg_circle(eye, ex, ey, 0.17f * R, d, MG_WHITE);
        mg_circle(eye, px, py, 0.09f * R, d - 0.002f, FACE);
        break;
    case MOOD_MEH:   /* flat half-lids, looking aside */
        mg_circle(eye, px + 0.04f * R, ey + 0.03f * R, 0.12f * R, d, FACE);
        mg_rect(eye, ex - 0.18f * R, ey - 0.2f * R, 0.36f * R, 0.21f * R, d - 0.002f, BODY);
        mg_line(eye, ex - 0.16f * R, ey + 0.01f * R, ex + 0.16f * R, ey + 0.01f * R, 2, d - 0.004f, FACE);
        break;
    default: {
        bool blink = fmodf(G.t + p->x * 0.01f, 3.7f) < 0.12f;
        if (blink) {
            mg_line(eye, ex - 0.12f * R, ey, ex + 0.12f * R, ey, 2, d, FACE);
            break;
        }
        mg_circle(eye, px, py - 0.05f * R, 0.12f * R, d, FACE);
        mg_circle(eye, px, py + 0.05f * R, 0.12f * R, d, FACE);
        mg_circle(eye, px + 0.04f * R, py - 0.08f * R, 0.045f * R, d - 0.002f, MG_WHITE);
        break;
    }
    }
}

static void draw_pim(int eye, const Pose *p)
{
    const float R = PIM_R;
    float x = p->x, y = p->y, d = -0.16f, fd = -0.175f;
    /* a soft glow, then the body: the dome of a head over a wavy tail */
    mg_circle(eye, x, y + 0.5f * R, R * 1.7f, d + 0.03f, RGBA(170, 215, 255, 34));
    float tx[7], ty[7];
    float w0 = 3 * sinf(G.t * 3.1f), w1 = 3 * sinf(G.t * 3.1f + 2.1f), w2 = 3 * sinf(G.t * 3.1f + 4.2f);
    tx[0] = x - R, ty[0] = y + 0.1f * R;
    tx[1] = x + R, ty[1] = y + 0.1f * R;
    tx[2] = x + 0.72f * R + w0, ty[2] = y + 2.05f * R;
    tx[3] = x + 0.3f * R + w1 * 0.5f, ty[3] = y + 1.7f * R;
    tx[4] = x + w1, ty[4] = y + 2.2f * R;
    tx[5] = x - 0.35f * R + w2 * 0.5f, ty[5] = y + 1.72f * R;
    tx[6] = x - 0.72f * R + w2, ty[6] = y + 2.05f * R;
    float cx = x, cy = y + 0.95f * R;
    for (int i = 0; i < 7; i++) {
        int j = (i + 1) % 7;
        mg_tri(eye, cx, cy, tx[i], ty[i], tx[j], ty[j], d, BODY);
    }
    mg_circle(eye, x, y, R, d, BODY);
    mg_circle(eye, x - 0.42f * R, y - 0.48f * R, 0.2f * R, d - 0.005f, RGBA(236, 246, 255, 200));

    /* a teacher's bow tie */
    float by = y + 1.02f * R;
    mg_tri(eye, x, by, x - 0.32f * R, by - 0.16f * R, x - 0.32f * R, by + 0.16f * R, fd, RGBA(220, 70, 90, 255));
    mg_tri(eye, x, by, x + 0.32f * R, by - 0.16f * R, x + 0.32f * R, by + 0.16f * R, fd, RGBA(220, 70, 90, 255));
    mg_circle(eye, x, by, 0.08f * R, fd - 0.003f, RGBA(180, 50, 70, 255));

    /* face */
    float ey = y - 0.02f * R;
    eye_at(eye, x - 0.36f * R, ey, fd, p);
    eye_at(eye, x + 0.36f * R, ey, fd, p);
    float brow = p->mood == MOOD_SURPRISED || p->mood == MOOD_HAPPY ? 0.42f : p->mood == MOOD_MEH ? 0.24f : 0.34f;
    for (int s = -1; s <= 1; s += 2) {
        float bx = x + s * 0.36f * R, bys = ey - brow * R;
        float tilt = p->mood == MOOD_FOCUS ? 0.05f * R : 0;
        mg_line(eye, bx - 0.13f * R, bys - s * tilt, bx + 0.13f * R, bys + s * tilt, 2, fd, FACE);
    }
    if (p->mood != MOOD_MEH) {   /* blush */
        mg_circle(eye, x - 0.62f * R, y + 0.22f * R, 0.13f * R, fd + 0.002f, RGBA(255, 150, 180, 110));
        mg_circle(eye, x + 0.62f * R, y + 0.22f * R, 0.13f * R, fd + 0.002f, RGBA(255, 150, 180, 110));
    }
    float my = y + 0.34f * R;
    bool open = p->talk && fmodf(G.t * 9, 2) < 1.2f;
    if (p->mood == MOOD_HAPPY) {   /* big open smile */
        mg_circle(eye, x, my, 0.22f * R, fd, RGBA(120, 30, 50, 255));
        mg_rect(eye, x - 0.24f * R, my - 0.24f * R, 0.48f * R, 0.24f * R, fd - 0.002f, BODY);
        mg_circle(eye, x, my + 0.13f * R, 0.08f * R, fd - 0.003f, RGBA(240, 120, 130, 255));
    } else if (p->mood == MOOD_SURPRISED || (open && p->mood == MOOD_MEH)) {
        mg_circle(eye, x, my + 0.04f * R, 0.09f * R, fd, RGBA(120, 30, 50, 255));
    } else if (open) {
        mg_circle(eye, x, my + 0.02f * R, 0.13f * R, fd, RGBA(120, 30, 50, 255));
        mg_rect(eye, x - 0.15f * R, my - 0.13f * R, 0.3f * R, 0.12f * R, fd - 0.002f, BODY);
    } else if (p->mood == MOOD_MEH) {
        mg_line(eye, x - 0.14f * R, my + 0.03f * R, x + 0.14f * R, my + 0.03f * R, 2, fd, FACE);
    } else {   /* a soft little smile */
        mg_line(eye, x - 0.14f * R, my - 0.02f * R, x - 0.05f * R, my + 0.05f * R, 2, fd, FACE);
        mg_line(eye, x - 0.05f * R, my + 0.05f * R, x + 0.05f * R, my + 0.05f * R, 2, fd, FACE);
        mg_line(eye, x + 0.05f * R, my + 0.05f * R, x + 0.14f * R, my - 0.02f * R, 2, fd, FACE);
    }
    if (p->mood == MOOD_MEH) {   /* a sweat drop */
        float sx = x + 0.8f * R, sy = y - 0.45f * R + fmodf(G.t * 6, 6);
        mg_tri(eye, sx, sy - 6, sx - 3, sy, sx + 3, sy, fd - 0.01f, RGBA(200, 230, 255, 230));
        mg_circle(eye, sx, sy + 0.5f, 3, fd - 0.01f, RGBA(200, 230, 255, 230));
    }

    /* arms: little nubs, stretchy when reaching */
    float ad = -0.2f;
    float lsx = x - 0.86f * R, lsy = y + 0.62f * R;
    float rsx = x + 0.86f * R, rsy = y + 0.62f * R;
    if (p->both_up) {
        float w = 4 * sinf(G.t * 12);
        mg_line(eye, lsx, lsy, lsx - 10, lsy - 22 + w, 0.32f * R, ad, BODY);
        mg_circle(eye, lsx - 10, lsy - 22 + w, 0.2f * R, ad, BODY);
        mg_line(eye, rsx, rsy, rsx + 10, rsy - 22 - w, 0.32f * R, ad, BODY);
        mg_circle(eye, rsx + 10, rsy - 22 - w, 0.2f * R, ad, BODY);
    } else {
        mg_circle(eye, lsx + 2, lsy + 3, 0.2f * R, ad + 0.01f, BODY_DARK);
        if (p->arm) {
            mg_line(eye, rsx, rsy, p->ax, p->ay, 0.32f * R, ad, BODY);
            mg_circle(eye, p->ax, p->ay, 0.2f * R, ad, BODY);
        } else {
            mg_circle(eye, rsx - 2, rsy + 3, 0.2f * R, ad + 0.01f, BODY_DARK);
        }
    }
}

/* The marker: a fat pen with a cap end, tip at (x, y). */
static void draw_marker(int eye, float x, float y, float d, float ang)
{
    float c = cosf(ang), s = sinf(ang), L = 22;
    u32 col = MARKER_COL[G.level];
    mg_line(eye, x + c * 3, y + s * 3, x + c * L, y + s * L, 8, d + 0.002f, RGBA(30, 30, 46, 255));
    mg_line(eye, x + c * 4, y + s * 4, x + c * (L - 1), y + s * (L - 1), 5.5f, d, col);
    mg_line(eye, x + c * 9, y + s * 9, x + c * 15, y + s * 15, 5.5f, d - 0.002f, RGBA(245, 245, 245, 255));
    mg_line(eye, x, y, x + c * 4, y + s * 4, 3, d, col);
}

/* A dotted shimmer from Pim's hand to what it moves by spirit power. */
static void draw_shimmer(int eye, float x0, float y0, float x1, float y1, float d0, float d1)
{
    for (int i = 1; i < 6; i++) {
        float f = i / 6.0f, tw = 0.5f + 0.5f * sinf(G.t * 14 + i * 1.3f);
        mg_circle(eye, lerpf(x0, x1, f), lerpf(y0, y1, f) + 3 * sinf(G.t * 6 + i), 1.4f, lerpf(d0, d1, f),
                  rgba_alpha(RGBA(220, 240, 255, 255), 0.4f + 0.5f * tw));
    }
}

static void draw_bubble(int eye, float px, float py)
{
    if (!G.say)
        return;
    float d = -0.12f, x = 10, y = 192, w = 380, h = 40;
    float s = mg_shift(eye, d);
    ui_rrect(x + s, y, w, h, 12, RGBA(252, 252, 255, 240));
    mg_tri(eye, px - 4, y + 1, px + 14, y + 1, px - 2, py, d, RGBA(252, 252, 255, 240));
    ui_rrect(x + 12 + s, y - 7, 34, 14, 7, RGBA(130, 180, 240, 255));
    mg_text(eye, "Pim", x + 18, y - 7, 0.4f, d - 0.01f, MG_INK);
    char buf[96];
    int n = G.say_n < (int)sizeof(buf) - 1 ? G.say_n : (int)sizeof(buf) - 1;
    memcpy(buf, G.say, (size_t)n);
    buf[n] = 0;
    mg_text(eye, buf, x + 14, y + 13, 0.52f, d - 0.01f, MG_INK);
}

static void draw_top(int eye)
{
    draw_room(eye);
    draw_board(eye);

    /* Pim's pose follows the phase */
    float bob = 3 * sinf(G.t * 2.2f);
    Pose p = {PIM_X, PIM_Y + bob, MOOD_NEUTRAL, G.say && G.say_n < G.say_len, 0.4f, 0, false, 0, 0, false};
    bool marker = false, shimmer = false;
    float mx = 0, my = 0, ma = -0.9f;
    switch (G.phase) {
    case PH_WIPE: {
        /* the eraser zigzags over the board */
        float f = G.pt / WIPE_TIME, z = fabsf(fmodf(f * 3, 2) - 1);
        mx = BX + 30 + (BW - 60) * z, my = BY + 30 + (BH - 60) * f;
        mg_rect(eye, mx - 16, my - 8, 32, 16, -0.03f, RGBA(60, 60, 80, 255));
        mg_rect(eye, mx - 16, my + 4, 32, 4, -0.035f, RGBA(230, 230, 230, 255));
        draw_paper(eye, 1 - f * 2);
        p.arm = true, p.ax = PIM_X + 36, p.ay = PIM_Y + 10 + bob, p.lx = 1, p.mood = MOOD_FOCUS;
        draw_shimmer(eye, p.ax, p.ay, mx - 16, my, -0.2f, -0.04f);
        break;
    }
    case PH_INTRO:   /* waves hello */
        p.arm = true, p.mood = MOOD_CHATTY, p.lx = 0.3f;
        p.ax = PIM_X + 0.86f * PIM_R + 14 + 6 * sinf(G.t * 9), p.ay = PIM_Y - 18 + bob;
        break;
    case PH_SKETCH: {
        float bx = BX + G.mk_x * BS, by = BY + G.mk_y * BS;
        mx = bx, my = by - (G.mk_up ? 5 : 0) - (G.pt < 0.25f ? 8 : 0), ma = -0.9f;
        marker = shimmer = true;
        p.arm = true, p.mood = G.peek ? MOOD_SURPRISED : MOOD_FOCUS;
        p.ax = PIM_X + 38, p.ay = PIM_Y + 4 + bob;
        p.lx = 1, p.ly = clampf((by - PIM_Y) / 80, -1, 1);
        break;
    }
    case PH_VIEW: {   /* points at the board, tapping it now and then */
        float tap = fmaxf(0, sinf(G.pt * 5));
        p.arm = true, p.mood = G.peek ? MOOD_SURPRISED : MOOD_CHATTY, p.lx = 1;
        p.ax = PIM_X + 40, p.ay = PIM_Y + bob;
        mx = BX + 10 - 6 * tap, my = BCY + 10, ma = -2.6f;
        marker = shimmer = true;
        break;
    }
    case PH_HIDE:
    case PH_DRAW:
        if (G.peek) {   /* gazing at the moth */
            p.mood = G.phase == PH_DRAW && G.pt > DRAW_TIME - 5 ? MOOD_SURPRISED : MOOD_CHATTY;
            p.lx = -1, p.ly = -0.8f;
            p.talk = p.talk || (G.phase == PH_DRAW && fmodf(G.pt, 4) < 0.5f);
        } else {        /* watching your pad, humming */
            p.mood = G.phase == PH_DRAW && G.pt > DRAW_TIME - 5 ? MOOD_SURPRISED : MOOD_NEUTRAL;
            p.lx = 0.5f * sinf(G.t * 0.7f), p.ly = 1;
        }
        if (G.phase == PH_HIDE) {   /* gives the board a push */
            p.arm = true, p.ax = PIM_X + 46, p.ay = PIM_Y + 8 + bob, p.lx = 1, p.ly = 0;
        }
        break;
    case PH_REVIEW: {
        float f = ease((G.pt - REV_MORPH + 0.1f) / 0.5f);
        p.x = lerpf(PIM_X, PIM_RX, f);
        float lift = (G.pt - REV_MORPH) / 0.5f;
        draw_paper(eye, lift);
        p.lx = 1, p.ly = 0;
        if (lift > 0) {
            float dy = (1 - ease(lift)) * 150;
            p.arm = true, p.ax = REV_PX - PAPER / 2 + 2, p.ay = REV_Y + PAPER / 2 - 14 + dy;
        }
        if (G.pt >= REV_STAMP) {
            p.mood = G.react == 2 ? MOOD_HAPPY : G.react == 1 ? MOOD_CHATTY : MOOD_MEH;
            if (G.react == 2) {
                p.y -= 6 * fabsf(sinf(G.pt * 7));
                for (int i = 0; i < 4; i++) {   /* sparkles */
                    float a = G.t * 1.5f + i * 1.5708f, sx = p.x + cosf(a) * 44, sy = p.y + sinf(a) * 36;
                    float sz = 3 + 2 * sinf(G.t * 8 + i);
                    mg_line(eye, sx - sz, sy, sx + sz, sy, 1.6f, -0.24f, MG_GOLD);
                    mg_line(eye, sx, sy - sz, sx, sy + sz, 1.6f, -0.24f, MG_GOLD);
                }
            } else if (G.react == 1) {
                p.y += 3 * sinf(G.pt * 10) * clampf(REV_STAMP + 1 - G.pt, 0, 1);   /* a nod */
            }
        } else {
            p.mood = MOOD_FOCUS;
        }
        break;
    }
    }
    draw_pim(eye, &p);
    if (marker) {
        if (shimmer)
            draw_shimmer(eye, p.ax, p.ay, mx + 8, my - 8, -0.2f, -0.04f);
        draw_marker(eye, mx, my, -0.04f, ma);
    }
    draw_bubble(eye, p.x - 8, p.y + 2.1f * PIM_R);
}

/* ---- drawing: bottom screen -------------------------------------------------------- */

static void draw_user_bottom(u32 col)
{
    for (int k = 0; k < G.ns; k++) {
        int a = G.sstart[k], b = k + 1 < G.ns ? G.sstart[k + 1] : G.nu;
        if (b - a == 1)
            gfx_circle(CV_X + G.ux[a], CV_Y + G.uy[a], 1.6f, col);
        for (int i = a + 1; i < b; i++)
            gfx_line(CV_X + G.ux[i - 1], CV_Y + G.uy[i - 1], CV_X + G.ux[i], CV_Y + G.uy[i], 2.6f, col);
    }
}

/* Pim's shape laid over your drawing, at your drawing's place and size. */
static void ghost_seg(const void *ctx, float x0, float y0, float x1, float y1)
{
    u32 col = *(const u32 *)ctx;
    float p[4] = {x0, y0, x1, y1}, o[4];
    for (int k = 0; k < 2; k++) {
        float nx = (p[2 * k] - G.tcx) / G.tr - G.At[0], ny = (p[2 * k + 1] - G.tcy) / G.tr - G.At[1];
        o[2 * k] = CV_X + G.ucx + G.Ai[0] * nx + G.Ai[1] * ny;
        o[2 * k + 1] = CV_Y + G.ucy + G.Ai[2] * nx + G.Ai[3] * ny;
    }
    gfx_line(o[0], o[1], o[2], o[3], 2.0f, col);
}

static void text_center(const char *s, float cx, float y, float sc, u32 col)
{
    gfx_text(s, cx - gfx_text_width(s, sc) / 2, y, sc, col);
}

static u32 match_col(int m)
{
    return m >= 75 ? RGBA(130, 235, 160, 255) : m >= 40 ? MG_GOLD : RGBA(240, 120, 110, 255);
}

static void draw_bottom(void)
{
    char buf[64];
    snprintf(buf, sizeof(buf), "Exercise %d/%d  -  worth %d", G.level + 1, LEVELS, G.level + 1);
    gfx_text(buf, 10, 3, 0.45f, MG_GOLD);
    for (int i = 0; i < LEVELS; i++) {
        bool scored = i < G.level || (i == G.level && G.phase == PH_REVIEW && G.pt >= REV_STAMP);
        u32 c = scored ? match_col(G.match[i]) : i == G.level ? MG_WHITE : RGBA(255, 255, 255, 50);
        gfx_circle(196 + i * 12.0f, 10, i == G.level ? 4.5f : 3.5f, c);
    }

    /* the pad */
    bool active = G.phase == PH_DRAW;
    gfx_rect(CV_X - 2, CV_Y - 2, CV_W + 4, CV_H + 4, active ? RGBA(160, 190, 255, 200) : RGBA(160, 190, 255, 60));
    gfx_rect(CV_X, CV_Y, CV_W, CV_H, active ? RGBA(246, 242, 228, 255) : RGBA(200, 196, 186, 255));
    for (int i = 1; i < 9; i++)
        gfx_rect(CV_X + 4, CV_Y + i * 20.0f, CV_W - 8, 1, RGBA(120, 160, 230, 70));
    gfx_rect(CV_X + 26, CV_Y, 1, CV_H, RGBA(230, 120, 120, 90));

    float cx = CV_X + CV_W / 2;
    const u32 soft = RGBA(80, 80, 110, 255);
    switch (G.phase) {
    case PH_WIPE:
    case PH_INTRO:
        snprintf(buf, sizeof(buf), "Exercise %d", G.level + 1);
        text_center(buf, cx, CV_Y + 60, 0.75f, MG_INK);
        text_center("Watch Pim's board", cx, CV_Y + 96, 0.5f, soft);
        break;
    case PH_SKETCH:
        text_center("Watch closely...", cx, CV_Y + 76, 0.6f, MG_INK);
        break;
    case PH_VIEW: {
        float left = VIEW_TIME[G.level] - G.pt;
        text_center("Memorise the shape!", cx, CV_Y + 46, 0.6f, MG_INK);
        snprintf(buf, sizeof(buf), "%.1f", left > 0 ? left : 0);
        text_center(buf, cx, CV_Y + 80, 1.0f, RGBA(200, 120, 30, 255));
        float f = clampf(left / VIEW_TIME[G.level], 0, 1);
        gfx_rect(cx - 80, CV_Y + 134, 160, 4, RGBA(0, 0, 0, 40));
        gfx_rect(cx - 80, CV_Y + 134, 160 * f, 4, RGBA(200, 120, 30, 255));
        break;
    }
    case PH_HIDE:
        text_center(G.peek ? "The board is still up..." : "Get ready...", cx, CV_Y + 70, 0.6f, MG_INK);
        text_center("Any size, anywhere: only the shape counts", cx, CV_Y + 102, 0.45f, soft);
        break;
    case PH_DRAW: {
        float left = DRAW_TIME - G.pt;
        snprintf(buf, sizeof(buf), "%d s", (int)ceilf(left > 0 ? left : 0));
        gfx_text(buf, 312 - gfx_text_width(buf, 0.45f), 3, 0.45f, left <= 5 ? RGBA(240, 120, 110, 255) : MG_WHITE);
        gfx_rect(CV_X, CV_Y + CV_H - 3, CV_W * clampf(left / DRAW_TIME, 0, 1), 3, RGBA(220, 150, 50, 160));
        if (G.nu == 0) {
            text_center("Draw it here", cx, CV_Y + 70, 0.6f, RGBA(80, 80, 110, 120));
            text_center("any size, anywhere", cx, CV_Y + 96, 0.45f, RGBA(80, 80, 110, 100));
        }
        draw_user_bottom(PAD_INK);
        for (int i = 0; i < 3; i++) {
            bool on = i == 2 ? G.nu > 1 : G.nu > 0;
            gfx_rect(BTN_X[i], BTN_Y, BTN_W[i], BTN_H,
                     i == 2 && on ? RGBA(255, 255, 255, 230) : RGBA(255, 255, 255, on ? 60 : 25));
            text_center(BTN_LABEL[i], BTN_X[i] + BTN_W[i] / 2, BTN_Y + (BTN_H - gfx_line_height(0.45f)) / 2, 0.45f,
                        i == 2 && on ? MG_INK : rgba_alpha(MG_WHITE, on ? 1 : 0.5f));
        }
        break;
    }
    case PH_REVIEW: {
        int m = G.match[G.level];
        draw_user_bottom(PAD_INK);
        if (G.rn > 0 && G.pt >= REV_MORPH) {
            u32 col = rgba_alpha(RGBA(220, 70, 70, 255), 0.65f * ease((G.pt - REV_MORPH) / 0.5f));
            walk_target(1e9f, ghost_seg, &col);
        }
        if (G.pt >= REV_STAMP) {
            snprintf(buf, sizeof(buf), "%d%% %s", m, G.peek ? "(peeked)" : G.timed_out ? "(time up)" : "match");
            gfx_text(buf, 10, BTN_Y + 4, 0.55f, match_col(m));
            if (G.pt > REV_STAMP + 0.3f)
                gfx_text(G.level + 1 < LEVELS ? "A: next" : "A: finish", 160, BTN_Y + 6, 0.45f,
                         RGBA(200, 200, 225, 255));
        } else {
            gfx_text("Pim compares...", 10, BTN_Y + 6, 0.45f, RGBA(200, 200, 225, 255));
        }
        break;
    }
    }
    if (G.hint && G.hint_t > 0)
        text_center(G.hint, cx, CV_Y + CV_H - 24, 0.45f, rgba_alpha(RGBA(200, 80, 40, 255), clampf(G.hint_t, 0, 1)));
}

/* ---- result ------------------------------------------------------------------------- */

static int score(void)
{
    float s = 0;
    for (int i = 0; i < LEVELS; i++)
        s += (i + 1) * G.match[i];
    return (int)(s / 15.0f + 0.5f);
}

static const char *verdict(void)
{
    static char buf[110];
    int best = -1, sc = score();
    for (int i = 0; i < LEVELS; i++)   /* a peeked exercise doesn't count */
        if (!G.peek_level[i] && (best < 0 || G.match[i] >= G.match[best]))
            best = i;
    if (best < 0)
        best = 0;
    const char *grade = sc >= 90 ? "A+" : sc >= 80 ? "A" : sc >= 68 ? "B" : sc >= 55 ? "C" : sc >= 40 ? "D" : "F";
    const char *quip = sc >= 80 ? "Teacher's pet." : sc >= 55 ? "Shapes are your friends." : sc >= 40
                       ? "See me after class." : "Pim needs a lie-down.";
    snprintf(buf, sizeof(buf), "Pim's grade: %s. Best echo %d%% (exercise %d). %s", grade, G.match[best], best + 1,
             quip);
    return buf;
}

/* ---- bot ------------------------------------------------------------------------------ */

static float hash01(u32 h)
{
    h ^= h >> 16, h *= 0x7feb352du, h ^= h >> 15, h *= 0x846ca68bu, h ^= h >> 16;
    return (h & 0xFFFFFF) / 16777216.0f;
}

/* Draws each target stroke "from memory" at its own size and spot on the pad
 * (smaller than the board, in a corner), a little wobbly and squashed, then
 * presses A. Uses the cheat once, as exercise 4's drawing starts. */
static void bot(Input *in, float t)
{
    (void)t;
    if (!MG.cheat_used && G.level == 3 && G.phase == PH_DRAW && G.pt > 0.2f && G.pt < 0.3f) {
        in->down |= KEY_L_;
        return;
    }
    if (G.phase == PH_REVIEW && G.pt > REV_STAMP + 1.0f) {
        in->down |= KEY_A_;
        return;
    }
    if (G.phase != PH_DRAW || G.pt < 0.4f)
        return;
    u32 seed = (u32)G.level * 7919u + (u32)(G.scx * 13) + (u32)(G.scy * 7);
    /* pad pixels per shape pixel: 0.4-0.6 (the board shows it at 0.6, and
     * the pad would fit it at about 0.75) */
    float k = fminf(0.4f + 0.2f * hash01(seed), fminf((CV_W - 24) / G.sw, (CV_H - 24) / G.sh));
    float hw = G.sw * k / 2 + 8, hh = G.sh * k / 2 + 8;
    float px = hash01(seed + 1) < 0.5f ? hw : CV_W - hw, py = hash01(seed + 2) < 0.5f ? hh : CV_H - hh;
    float sq = 0.92f + 0.14f * hash01(seed + 3);   /* a little squashed or stretched */
    float e = G.pt - 0.5f;
    for (int s = 0; s < G.npaths; s++) {
        const Path *p = &G.paths[s];
        float dur = 0.3f + path_len(p) * k / 140.0f;
        if (e < 0)
            return;   /* lifted between strokes */
        if (e <= dur) {
            float x, y, f = e / dur;
            path_at(p, f, &x, &y);
            float dx = (x - G.scx) * k * sq, dy = (y - G.scy) * k / sq;
            float r = 1 + 0.05f * sinf(3 * atan2f(dy, dx) + hash01(seed + 4) * 6);
            x = px + dx * r + 1.5f * sinf(f * 19 + s);
            y = py + dy * r + 1.5f * cosf(f * 23 + s * 2);
            in->down |= KEY_TOUCH_;
            in->held |= KEY_TOUCH_;
            in->tx = (int)(CV_X + clampf(x, 1, CV_W - 2));
            in->ty = (int)(CV_Y + clampf(y, 1, CV_H - 2));
            return;
        }
        e -= dur + 0.15f;
    }
    if (e > 0.3f)
        in->down |= KEY_A_;
}

const MiniGame MG_DRAW = {
    .id = "draw",
    .title = "Echo of a Shape",
    .rules = "Pim teaches shapes at the whiteboard: watch it\n"
             "draw one, memorise it, then the board flips.\n"
             "Draw it from memory on your pad, any size and\n"
             "anywhere: only the shape counts, not where you\n"
             "put it or how big you make it. Pim holds your\n"
             "drawing up next to the original and grades it.\n"
             "Five exercises: each harder, shown for less\n"
             "time, and worth more.",
    .controls = "Stylus: draw on the pad (any strokes)\n"
                "A / Done: hand it in\n"
                "B / Undo: remove the last stroke\n"
                "Y / Clear: start over\n"
                "25 s to draw.   START: pause",
    .cheat = "Pim gets distracted: the board stays up",
    .music = "draw",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .verdict = verdict,
    .can_cheat = can_cheat,
    .bot = bot,
};
