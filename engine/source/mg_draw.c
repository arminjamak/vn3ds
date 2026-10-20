/* Echo of a Shape: an abstract shape floats on the top screen for a few
 * seconds, slowly turning in 3D, then vanishes. Draw it from memory on the
 * touch screen. Five exercises, each harder, shown for less time and worth
 * more.
 *
 * Matching: target and drawing are rasterised with a thick pen onto an
 * 80x48 grid that covers the top screen's frame (the canvas mirrors it).
 * The drawing is first aligned to the target by its bounding box (centre and
 * size, aspect only half-corrected), then
 *   precision = how much of your ink lies near the shape,
 *   recall    = how much of the shape your ink covers,
 * each with soft credit by distance (full within 1.5 cells, none beyond 5),
 * and match = F-score (2PR / (P + R)) times a placement factor that costs up
 * to 20% for drawing it in the wrong place or at the wrong size.
 *
 * Score: exercise k (1..5) has weight k; the final score is the weighted
 * average of the five match percentages. The cheat ("Trace it") makes the
 * current exercise count as 90%. */

#include "minigame.h"

#define LEVELS 5
#define MAX_PATHS 6
#define MAX_PPTS 64
#define MAX_UPTS 480
#define MAX_USTROKES 48
#define GW 80
#define GH 48
#define CELL 5.0f          /* frame pixels per grid cell (400 / 80) */

/* The canvas on the bottom screen mirrors the top screen's 400x240 frame. */
#define CV_X 10.0f
#define CV_Y 22.0f
#define CV_S 0.75f         /* canvas pixels per frame pixel: 300x180 */
#define CV_W (TOP_W * CV_S)
#define CV_H (TOP_H * CV_S)

/* Buttons (clear of the framework's Cheat button at x 236-314, y 206-234). */
#define BTN_Y 208
#define BTN_H 26
static const float BTN_X[3] = {8, 82, 156};
static const float BTN_W[3] = {68, 68, 72};
static const char *const BTN_LABEL[3] = {"B: Undo", "Y: Clear", "A: Done"};

static const float VIEW_TIME[LEVELS] = {5.0f, 4.5f, 4.0f, 3.5f, 3.0f};
#define DRAW_TIME 25.0f
#define INTRO_TIME 1.3f
#define VANISH_TIME 0.6f
#define TRACE_TIME 1.8f
#define REVIEW_TIME 3.2f
#define CHEAT_MATCH 90

enum { PH_INTRO, PH_VIEW, PH_VANISH, PH_DRAW, PH_TRACE, PH_REVIEW };

typedef struct {
    int n;
    float x[MAX_PPTS], y[MAX_PPTS]; /* frame coordinates (top screen pixels) */
} Path;

/* Each target stroke floats at its own depth. */
static const float PATH_DEPTH[MAX_PATHS] = {-0.10f, 0.10f, -0.22f, 0.02f, -0.16f, 0.14f};

static struct {
    int level;
    int phase;
    float pt;               /* seconds in this phase */
    float t;                /* seconds since start */
    Path paths[MAX_PATHS];
    int npaths;
    float scx, scy;         /* target centre (turning axis) */
    float yaw0;
    /* the player's drawing, frame coordinates */
    float ux[MAX_UPTS], uy[MAX_UPTS];
    int nu;
    int sstart[MAX_USTROKES];
    int ns;
    bool touching, stroking;
    int match[LEVELS];
    bool cheated[LEVELS];
    bool timed_out;
    bool low_warned;
    bool score_sounded;
    int last_tick;
    float hint_t;
    const char *hint;
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
        p->x[p->n] = clampf(x, 8, TOP_W - 8);
        p->y[p->n] = clampf(y, 8, TOP_H - 8);
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
            float k = randr(0.45f, 0.7f) * side;
            float qx = clampf(mx - dy * k, 30, 370), qy = clampf(my + dx * k, 30, 210);
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
    float cx = 200 + randr(-30, 30), cy = 120 + randr(-14, 14);
    switch (level) {
    case 0:
        add_form(mg_randi(0, 2), cx, cy, randr(48, 64));
        break;
    case 1:
        if (mg_randi(0, 1)) {   /* two forms side by side, perhaps touching */
            int a = mg_randi(0, 2), b = (a + mg_randi(1, 2)) % 3;
            float gap = randr(50, 75), dy = randr(-25, 25);
            add_form(a, cx - gap, cy - dy, randr(32, 42));
            add_form(b, cx + gap, cy + dy, randr(32, 42));
        } else {                /* a form crossed or flanked by a line */
            float r = randr(42, 54), a = randr(0, 3.1415927f), off = randr(0, r * 1.2f);
            float len = randr(85, 115), px = cx + cosf(a + 1.5708f) * off, py = cy + sinf(a + 1.5708f) * off;
            add_form(mg_randi(0, 2), cx, cy, r);
            add_line(px - cosf(a) * len, py - sinf(a) * len * 0.75f, px + cosf(a) * len,
                     py + sinf(a) * len * 0.75f);
        }
        break;
    case 2: {
        int k = mg_randi(0, 2);
        if (k == 0)
            add_star(cx, cy, randr(66, 78), mg_randi(5, 6), randr(0, 6.28f));
        else if (k == 1)
            add_spiral(cx, cy, randr(70, 82), randr(2.0f, 2.6f), randr(0, 6.28f), mg_randi(0, 1) ? 1 : -1);
        else
            add_zigzag(randr(70, 100), randr(300, 330), cy, randr(32, 48), mg_randi(3, 5), randr(-0.25f, 0.25f));
        break;
    }
    case 3: {
        /* three parts on a loose triangle of positions, all different kinds */
        float px[3] = {130, 270, 200}, py[3] = {85, 85, 165};
        if (mg_randi(0, 1))
            py[0] = py[1] = 160, py[2] = 80;
        int kinds[7] = {0, 1, 2, 3, 4, 5, 6};
        for (int i = 6; i > 0; i--) {
            int j = mg_randi(0, i), tmp = kinds[i];
            kinds[i] = kinds[j];
            kinds[j] = tmp;
        }
        for (int i = 0; i < 3; i++)
            add_part(kinds[i], px[i] + randr(-15, 15), py[i] + randr(-10, 10), randr(28, 36));
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
    G.scx = (x0 + x1) / 2;
    G.scy = (y0 + y1) / 2;
}

static float path_len(const Path *p)
{
    float l = 0;
    for (int i = 1; i < p->n; i++)
        l += hypotf(p->x[i] - p->x[i - 1], p->y[i] - p->y[i - 1]);
    return l;
}

static float total_len(void)
{
    float l = 0;
    for (int i = 0; i < G.npaths; i++)
        l += path_len(&G.paths[i]);
    return l;
}

/* Calls fn for each target segment, up to `frac` (0..1) of the total length
 * (the last one cut short): used to draw the shape and to trace it. */
typedef void (*SegFn)(const void *ctx, int pi, float x0, float y0, float x1, float y1);

static void walk_target(float frac, SegFn fn, const void *ctx)
{
    float left = frac >= 1 ? 1e9f : total_len() * clampf(frac, 0, 1);
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
            fn(ctx, pi, x0, y0, x1, y1);
        }
    }
}

/* ---- matching ------------------------------------------------------------------- */

static u8 grid_t[GH][GW], grid_d[GH][GW];
static float dist_t[GH][GW], dist_d[GH][GW];

/* The pen is one cell (5 frame px) wide; the tolerance does the rest. */
static void stamp(u8 g[GH][GW], float x, float y)
{
    int gx = (int)(x / CELL), gy = (int)(y / CELL);
    if (gx >= 0 && gx < GW && gy >= 0 && gy < GH)
        g[gy][gx] = 1;
}

static void stamp_seg(u8 g[GH][GW], float x0, float y0, float x1, float y1)
{
    int steps = 1 + (int)(hypotf(x1 - x0, y1 - y0) / (CELL * 0.5f));
    for (int i = 0; i <= steps; i++)
        stamp(g, lerpf(x0, x1, (float)i / steps), lerpf(y0, y1, (float)i / steps));
}

static void stamp_target_seg(const void *ctx, int pi, float x0, float y0, float x1, float y1)
{
    (void)ctx, (void)pi;
    stamp_seg(grid_t, x0, y0, x1, y1);
}

/* Two-pass chamfer distance (in cells) to the nearest ink cell. */
static void distance(u8 g[GH][GW], float d[GH][GW])
{
    for (int y = 0; y < GH; y++)
        for (int x = 0; x < GW; x++)
            d[y][x] = g[y][x] ? 0 : 1e6f;
    for (int y = 0; y < GH; y++)
        for (int x = 0; x < GW; x++) {
            float v = d[y][x];
            if (x > 0) v = fminf(v, d[y][x - 1] + 1);
            if (y > 0) {
                v = fminf(v, d[y - 1][x] + 1);
                if (x > 0) v = fminf(v, d[y - 1][x - 1] + 1.414f);
                if (x < GW - 1) v = fminf(v, d[y - 1][x + 1] + 1.414f);
            }
            d[y][x] = v;
        }
    for (int y = GH - 1; y >= 0; y--)
        for (int x = GW - 1; x >= 0; x--) {
            float v = d[y][x];
            if (x < GW - 1) v = fminf(v, d[y][x + 1] + 1);
            if (y < GH - 1) {
                v = fminf(v, d[y + 1][x] + 1);
                if (x < GW - 1) v = fminf(v, d[y + 1][x + 1] + 1.414f);
                if (x > 0) v = fminf(v, d[y + 1][x - 1] + 1.414f);
            }
            d[y][x] = v;
        }
}

/* Full credit within 1 cell (5 frame px, under 4 px on the canvas), none
 * beyond 3.5 cells (17.5 frame px, 13 px on the canvas). */
static float credit(float d) { return clampf((3.5f - d) / 2.5f, 0, 1); }

static void bbox(bool user, float *cx, float *cy, float *w, float *h)
{
    float x0 = 1e9f, y0 = 1e9f, x1 = -1e9f, y1 = -1e9f;
    if (user) {
        for (int i = 0; i < G.nu; i++)
            x0 = fminf(x0, G.ux[i]), x1 = fmaxf(x1, G.ux[i]), y0 = fminf(y0, G.uy[i]), y1 = fmaxf(y1, G.uy[i]);
    } else {
        for (int p = 0; p < G.npaths; p++)
            for (int i = 0; i < G.paths[p].n; i++) {
                float x = G.paths[p].x[i], y = G.paths[p].y[i];
                x0 = fminf(x0, x), x1 = fmaxf(x1, x), y0 = fminf(y0, y), y1 = fmaxf(y1, y);
            }
    }
    *cx = (x0 + x1) / 2, *cy = (y0 + y1) / 2, *w = x1 - x0, *h = y1 - y0;
}

/* F-score of the drawing mapped by x' = tcx + (x - ucx) * sx (and y alike)
 * against the target grid (grid_t / dist_t must be ready). */
static float fscore(float tcx, float tcy, float ucx, float ucy, float sx, float sy)
{
    memset(grid_d, 0, sizeof(grid_d));
    for (int k = 0; k < G.ns; k++) {
        int a = G.sstart[k], b = k + 1 < G.ns ? G.sstart[k + 1] : G.nu;
        for (int i = a; i < b; i++) {
            float x1 = tcx + (G.ux[i] - ucx) * sx, y1 = tcy + (G.uy[i] - ucy) * sy;
            if (i == a) {
                stamp(grid_d, x1, y1);
            } else {
                float x0 = tcx + (G.ux[i - 1] - ucx) * sx, y0 = tcy + (G.uy[i - 1] - ucy) * sy;
                stamp_seg(grid_d, x0, y0, x1, y1);
            }
        }
    }
    distance(grid_d, dist_d);
    float pn = 0, pd = 0, rn = 0, rd = 0;
    for (int y = 0; y < GH; y++)
        for (int x = 0; x < GW; x++) {
            if (grid_d[y][x])
                pn += credit(dist_t[y][x]), pd += 1;
            if (grid_t[y][x])
                rn += credit(dist_d[y][x]), rd += 1;
        }
    float P = pd > 0 ? pn / pd : 0, R = rd > 0 ? rn / rd : 0;
    /* far more ink than the shape has (filling it in, scribbling) costs precision */
    if (pd > rd * 1.4f)
        P *= rd * 1.4f / pd;
    return P + R > 0 ? 2 * P * R / (P + R) : 0;
}

/* The best of three readings: as drawn; moved onto the target (costs up to
 * 12% for the offset); moved and resized (also costs up to 8% for the size).
 * So a shape drawn a bit off is forgiven, but placement still counts, and a
 * half-finished drawing in the right place is not dragged out of place. */
static int compute_match(void)
{
    if (G.nu < 2)
        return 0;
    float tcx, tcy, tw, th, ucx, ucy, uw, uh;
    bbox(false, &tcx, &tcy, &tw, &th);
    bbox(true, &ucx, &ucy, &uw, &uh);
    if (uw + uh < 6)
        return 0;   /* a dot */

    memset(grid_t, 0, sizeof(grid_t));
    walk_target(1, stamp_target_seg, NULL);
    distance(grid_t, dist_t);

    float s_raw = (tw + th) / (uw + uh), s = clampf(s_raw, 0.6f, 1.6f);
    float sx = s, sy = s;   /* aspect only half-corrected */
    if (uw > 24 && tw > 24)
        sx = sqrtf(s * clampf(tw / uw, 0.6f, 1.6f));
    if (uh > 24 && th > 24)
        sy = sqrtf(s * clampf(th / uh, 0.6f, 1.6f));
    float place = 1 - 0.12f * clampf((hypotf(tcx - ucx, tcy - ucy) - 10) / 70, 0, 1);
    float size = 1 - 0.08f * clampf((fabsf(logf(s_raw)) - 0.1f) / 0.5f, 0, 1);

    float best = fscore(0, 0, 0, 0, 1, 1);
    best = fmaxf(best, fscore(tcx, tcy, ucx, ucy, 1, 1) * place);
    best = fmaxf(best, fscore(tcx, tcy, ucx, ucy, sx, sy) * place * size);
    int m = (int)(best * 100 + 0.5f);
    return m < 0 ? 0 : (m > 100 ? 100 : m);
}

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

static void begin_round(void)
{
    gen_shape(G.level);
    clear_drawing();
    G.yaw0 = randr(0, 6.28f);
    G.timed_out = G.low_warned = G.score_sounded = false;
    G.last_tick = 99;
    G.hint = NULL;
    set_phase(PH_INTRO);
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
    G.timed_out = timeout;
    mg_sfx(timeout ? "draw_timeout" : "draw_submit");
    set_phase(PH_REVIEW);
}

static void show_hint(const char *s)
{
    G.hint = s;
    G.hint_t = 1.6f;
}

static bool in_canvas(int x, int y)
{
    return x >= CV_X && x < CV_X + CV_W && y >= CV_Y && y < CV_Y + CV_H;
}

static void add_point(int tx, int ty, bool first)
{
    float x = clampf((tx - CV_X) / CV_S, 0, TOP_W - 1), y = clampf((ty - CV_Y) / CV_S, 0, TOP_H - 1);
    if (!first && G.nu > 0 && hypotf(x - G.ux[G.nu - 1], y - G.uy[G.nu - 1]) < 4)
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

static void use_cheat(void)
{
    end_stroke();
    G.cheated[G.level] = true;
    mg_sfx("draw_trace");
    if (G.phase == PH_REVIEW) {   /* already drawn: lift this one to a pass */
        if (G.match[G.level] < CHEAT_MATCH)
            G.match[G.level] = CHEAT_MATCH;
        G.pt = 0;
        G.score_sounded = false;
        return;
    }
    G.match[G.level] = CHEAT_MATCH;
    set_phase(PH_TRACE);
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
    if (cheat && !G.cheated[G.level]) {
        use_cheat();
        return true;
    }
    switch (G.phase) {
    case PH_INTRO:
        if (G.pt >= INTRO_TIME) {
            set_phase(PH_VIEW);
            mg_sfx("draw_reveal");
        }
        break;
    case PH_VIEW: {
        float left = VIEW_TIME[G.level] - G.pt;
        int sec = (int)ceilf(left);
        if (sec < G.last_tick && sec <= 3 && sec >= 1 && left < VIEW_TIME[G.level] - 0.5f)
            mg_sfx("draw_tick");
        G.last_tick = sec;
        if (left <= 0) {
            set_phase(PH_VANISH);
            mg_sfx("draw_vanish");
        }
        break;
    }
    case PH_VANISH:
        if (G.pt >= VANISH_TIME)
            set_phase(PH_DRAW);   /* a touch held from before starts no stroke */
        break;
    case PH_DRAW:
        update_draw(in, touch, fresh);
        if (G.phase != PH_DRAW)
            break;
        if (!G.low_warned && G.pt >= DRAW_TIME - 5) {
            G.low_warned = true;
            mg_sfx("draw_time_low");
        }
        if (G.pt >= DRAW_TIME)
            submit(true);
        break;
    case PH_TRACE:
        if (G.pt >= TRACE_TIME) {
            set_phase(PH_REVIEW);
            G.pt = 0.2f;
        }
        break;
    case PH_REVIEW: {
        if (!G.score_sounded && G.pt >= 0.35f) {
            int m = G.match[G.level];
            G.score_sounded = true;
            mg_sfx(m >= 70 ? "draw_score_good" : m >= 40 ? "draw_score_ok" : "draw_score_bad");
        }
        if (G.pt >= REVIEW_TIME || (G.pt > 0.8f && ((in->down & KEY_A_) || fresh))) {
            if (++G.level >= LEVELS)
                return false;
            mg_sfx("draw_level_up");
            begin_round();
        }
        break;
    }
    }
    return true;
}

/* ---- drawing: top screen ---------------------------------------------------------- */

typedef struct {
    int eye;
    float alpha, ca, sa, dz;
    bool flat;   /* no turning (review) */
} TopCtx;

static const u32 PATH_COL[MAX_PATHS] = {
    RGBA(255, 210, 110, 255), RGBA(255, 170, 120, 255), RGBA(250, 230, 150, 255),
    RGBA(255, 190, 140, 255), RGBA(240, 215, 120, 255), RGBA(255, 200, 160, 255),
};
#define USER_COL RGBA(120, 215, 255, 255)

static void top_point(const TopCtx *c, int pi, float x, float y, float *ox, float *oy, float *od)
{
    float dx = x - G.scx;
    *ox = c->flat ? x : G.scx + dx * c->ca;
    *oy = y;
    *od = PATH_DEPTH[pi] + c->dz + (c->flat ? 0 : dx / 200.0f * c->sa * 1.2f);
}

static void top_seg(const void *ctx, int pi, float x0, float y0, float x1, float y1)
{
    const TopCtx *c = ctx;
    float ax, ay, ad, bx, by, bd;
    top_point(c, pi, x0, y0, &ax, &ay, &ad);
    top_point(c, pi, x1, y1, &bx, &by, &bd);
    float d = (ad + bd) / 2;
    u32 col = PATH_COL[pi];
    mg_line(c->eye, ax, ay, bx, by, 9, d + 0.04f, rgba_alpha(col, 0.18f * c->alpha));
    mg_line(c->eye, ax, ay, bx, by, 3.2f, d, rgba_alpha(col, c->alpha));
    mg_circle(c->eye, ax, ay, 1.6f, ad, rgba_alpha(col, c->alpha));
}

static void draw_target_top(int eye, float frac, float alpha, float dz, bool flat)
{
    float yaw = 0.4f * sinf(G.t * 0.8f + G.yaw0);
    TopCtx c = {eye, alpha, cosf(yaw), sinf(yaw), dz, flat};
    walk_target(frac, top_seg, &c);
}

static void draw_user_top(int eye, float depth, u32 col)
{
    int stride = 1 + G.nu / 160;
    for (int k = 0; k < G.ns; k++) {
        int a = G.sstart[k], b = k + 1 < G.ns ? G.sstart[k + 1] : G.nu;
        if (b - a == 1)
            mg_circle(eye, G.ux[a], G.uy[a], 2, depth, col);
        int prev = a;
        for (int i = a + stride; i < b + stride - 1; i += stride) {
            int j = i < b ? i : b - 1;
            if (j == prev)
                break;
            mg_line(eye, G.ux[prev], G.uy[prev], G.ux[j], G.uy[j], 2.6f, depth, col);
            prev = j;
        }
    }
}

static u32 match_col(int m)
{
    return m >= 70 ? RGBA(130, 235, 160, 255) : m >= 40 ? MG_GOLD : RGBA(240, 120, 110, 255);
}

static void draw_top(int eye)
{
    char buf[64];
    mg_sky(eye, RGBA(16, 20, 34, 255), RGBA(34, 30, 52, 255));
    /* a faint grid far behind: the same grid as the canvas */
    for (int i = 1; i < 10; i++)
        mg_line(eye, i * 40.0f, 0, i * 40.0f, TOP_H, 1, 0.7f, RGBA(140, 160, 220, 22));
    for (int i = 1; i < 6; i++)
        mg_line(eye, 0, i * 40.0f, TOP_W, i * 40.0f, 1, 0.7f, RGBA(140, 160, 220, 22));

    /* exercise pips */
    for (int i = 0; i < LEVELS; i++) {
        u32 c = i < G.level || (i == G.level && G.phase == PH_REVIEW) ? match_col(G.match[i])
              : i == G.level ? MG_WHITE : RGBA(255, 255, 255, 50);
        mg_circle(eye, 18 + i * 18.0f, 14, i == G.level ? 6 : 4.5f, -0.12f, c);
    }
    snprintf(buf, sizeof(buf), "Exercise %d of %d", G.level + 1, LEVELS);
    mg_text(eye, buf, TOP_W - 12 - gfx_text_width(buf, 0.45f), 5, 0.45f, -0.1f, RGBA(220, 220, 240, 255));

    switch (G.phase) {
    case PH_INTRO: {
        float a = clampf(G.pt / 0.3f, 0, 1) * clampf((INTRO_TIME - G.pt) / 0.25f, 0, 1);
        snprintf(buf, sizeof(buf), "Exercise %d", G.level + 1);
        mg_text_centered(eye, buf, TOP_W / 2, 84, 1.0f, -0.25f, rgba_alpha(MG_GOLD, a));
        snprintf(buf, sizeof(buf), "%.1f seconds to look  -  worth %d", VIEW_TIME[G.level], G.level + 1);
        mg_text_centered(eye, buf, TOP_W / 2, 132, 0.5f, -0.1f, rgba_alpha(MG_WHITE, a));
        break;
    }
    case PH_VIEW: {
        float a = clampf(G.pt / 0.35f, 0, 1);
        draw_target_top(eye, 1, a, 0, false);
        float f = clampf(1 - G.pt / VIEW_TIME[G.level], 0, 1);
        mg_rect(eye, 100, 224, 200, 4, -0.15f, RGBA(255, 255, 255, 40));
        mg_rect(eye, 100, 224, 200 * f, 4, -0.15f, MG_GOLD);
        break;
    }
    case PH_VANISH: {
        float f = G.pt / VANISH_TIME;
        draw_target_top(eye, 1, (1 - f) * (1 - f), f * 0.8f, false);
        break;
    }
    case PH_DRAW:
        draw_user_top(eye, 0.05f, rgba_alpha(USER_COL, 0.85f));
        mg_text_centered(eye, "Draw it from memory", TOP_W / 2, 214, 0.45f, -0.05f, RGBA(200, 200, 225, 200));
        break;
    case PH_TRACE: {
        draw_user_top(eye, 0.15f, rgba_alpha(USER_COL, 0.35f));
        draw_target_top(eye, G.pt / (TRACE_TIME * 0.85f), 1, 0, true);
        mg_text_centered(eye, "Tracing...", TOP_W / 2, 210, 0.55f, -0.3f, RGBA(255, 200, 150, 255));
        break;
    }
    case PH_REVIEW: {
        int m = G.match[G.level];
        draw_user_top(eye, 0.18f, rgba_alpha(USER_COL, 0.9f));
        draw_target_top(eye, 1, 0.75f, -0.02f, true);
        float pop = clampf(G.pt / 0.3f, 0, 1);
        mg_rect(eye, 120, 196, 160, 36, -0.25f, RGBA(10, 10, 22, 165));
        snprintf(buf, sizeof(buf), "%d%%", m);
        mg_text_centered(eye, buf, TOP_W / 2 - 22, 198, 0.95f, -0.25f - 0.15f * pop, match_col(m));
        snprintf(buf, sizeof(buf), G.cheated[G.level] ? "traced\nx%d" : "match\nx%d", G.level + 1);
        mg_text(eye, buf, TOP_W / 2 + 24, 199, 0.42f, -0.28f, RGBA(220, 220, 240, 255));
        break;
    }
    }
}

/* ---- drawing: bottom screen -------------------------------------------------------- */

static void bot_seg(const void *ctx, int pi, float x0, float y0, float x1, float y1)
{
    u32 col = *(const u32 *)ctx;
    (void)pi;
    gfx_line(CV_X + x0 * CV_S, CV_Y + y0 * CV_S, CV_X + x1 * CV_S, CV_Y + y1 * CV_S, 2.6f, col);
}

static void draw_user_bottom(u32 col)
{
    for (int k = 0; k < G.ns; k++) {
        int a = G.sstart[k], b = k + 1 < G.ns ? G.sstart[k + 1] : G.nu;
        if (b - a == 1)
            gfx_circle(CV_X + G.ux[a] * CV_S, CV_Y + G.uy[a] * CV_S, 1.6f, col);
        for (int i = a + 1; i < b; i++)
            gfx_line(CV_X + G.ux[i - 1] * CV_S, CV_Y + G.uy[i - 1] * CV_S, CV_X + G.ux[i] * CV_S,
                     CV_Y + G.uy[i] * CV_S, 2.6f, col);
    }
}

static void text_center(const char *s, float cx, float y, float sc, u32 col)
{
    gfx_text(s, cx - gfx_text_width(s, sc) / 2, y, sc, col);
}

static void draw_bottom(void)
{
    char buf[64];
    snprintf(buf, sizeof(buf), "Exercise %d/%d  -  worth %d", G.level + 1, LEVELS, G.level + 1);
    gfx_text(buf, 10, 3, 0.45f, MG_GOLD);

    /* the canvas: the top screen's frame, with the same grid */
    bool active = G.phase == PH_DRAW;
    gfx_rect(CV_X - 2, CV_Y - 2, CV_W + 4, CV_H + 4, active ? RGBA(200, 210, 255, 120) : RGBA(200, 210, 255, 40));
    gfx_rect(CV_X, CV_Y, CV_W, CV_H, RGBA(14, 16, 30, 255));
    for (int i = 1; i < 10; i++)
        gfx_rect(CV_X + i * 30.0f, CV_Y, 1, CV_H, RGBA(140, 160, 220, 26));
    for (int i = 1; i < 6; i++)
        gfx_rect(CV_X, CV_Y + i * 30.0f, CV_W, 1, RGBA(140, 160, 220, 26));

    float cx = CV_X + CV_W / 2;
    switch (G.phase) {
    case PH_INTRO:
        text_center("Get ready", cx, CV_Y + 70, 0.7f, MG_WHITE);
        text_center("Watch the top screen", cx, CV_Y + 102, 0.45f, RGBA(200, 200, 225, 255));
        break;
    case PH_VIEW: {
        float left = VIEW_TIME[G.level] - G.pt;
        text_center("Memorise...", cx, CV_Y + 50, 0.75f, MG_WHITE);
        snprintf(buf, sizeof(buf), "%.1f", left > 0 ? left : 0);
        text_center(buf, cx, CV_Y + 86, 1.0f, MG_GOLD);
        float f = clampf(left / VIEW_TIME[G.level], 0, 1);
        gfx_rect(cx - 80, CV_Y + 140, 160, 4, RGBA(255, 255, 255, 40));
        gfx_rect(cx - 80, CV_Y + 140, 160 * f, 4, MG_GOLD);
        break;
    }
    case PH_VANISH:
        text_center("Gone. Now draw it.", cx, CV_Y + 76, 0.6f, rgba_alpha(MG_WHITE, G.pt / VANISH_TIME));
        break;
    case PH_DRAW: {
        float left = DRAW_TIME - G.pt;
        snprintf(buf, sizeof(buf), "%d s", (int)ceilf(left > 0 ? left : 0));
        gfx_text(buf, 310 - gfx_text_width(buf, 0.45f), 3, 0.45f, left <= 5 ? RGBA(240, 120, 110, 255) : MG_WHITE);
        gfx_rect(CV_X, CV_Y + CV_H - 3, CV_W * clampf(left / DRAW_TIME, 0, 1), 3, RGBA(255, 210, 110, 120));
        if (G.nu == 0)
            text_center("Draw here", cx, CV_Y + 80, 0.55f, RGBA(200, 200, 225, 90));
        draw_user_bottom(USER_COL);
        for (int i = 0; i < 3; i++) {
            bool on = i == 2 ? G.nu > 1 : G.nu > 0;
            gfx_rect(BTN_X[i], BTN_Y, BTN_W[i], BTN_H, i == 2 && on ? RGBA(255, 255, 255, 230) : RGBA(255, 255, 255, on ? 60 : 25));
            text_center(BTN_LABEL[i], BTN_X[i] + BTN_W[i] / 2, BTN_Y + (BTN_H - gfx_line_height(0.45f)) / 2, 0.45f,
                        i == 2 && on ? MG_INK : rgba_alpha(MG_WHITE, on ? 1 : 0.5f));
        }
        break;
    }
    case PH_TRACE: {
        u32 col = MG_GOLD;
        draw_user_bottom(rgba_alpha(USER_COL, 0.3f));
        walk_target(G.pt / (TRACE_TIME * 0.85f), bot_seg, &col);
        text_center("Trace it", cx, BTN_Y + 4, 0.5f, RGBA(255, 200, 150, 255));
        break;
    }
    case PH_REVIEW: {
        int m = G.match[G.level];
        u32 col = rgba_alpha(MG_GOLD, 0.8f);
        draw_user_bottom(USER_COL);
        walk_target(1, bot_seg, &col);
        snprintf(buf, sizeof(buf), "%d%% %s", m, G.cheated[G.level] ? "(traced)" : G.timed_out ? "(time up)" : "match");
        gfx_text(buf, 10, BTN_Y + 4, 0.55f, match_col(m));
        if (G.pt > 0.8f)
            gfx_text(G.level + 1 < LEVELS ? "A: next" : "A: finish", 160, BTN_Y + 6, 0.45f, RGBA(200, 200, 225, 255));
        break;
    }
    }
    if (G.hint && G.hint_t > 0)
        text_center(G.hint, cx, CV_Y + CV_H - 24, 0.45f, rgba_alpha(RGBA(255, 200, 150, 255), clampf(G.hint_t, 0, 1)));
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
    static char buf[96];
    int best = -1, sc = score();
    for (int i = 0; i < LEVELS; i++)   /* a traced exercise doesn't count */
        if (!G.cheated[i] && (best < 0 || G.match[i] >= G.match[best]))
            best = i;
    if (best < 0)
        best = 0;
    snprintf(buf, sizeof(buf), "Best echo: %d%% on exercise %d. %s", G.match[best], best + 1,
             sc >= 85 ? "Less, but better." : sc >= 65 ? "A faithful echo." : sc >= 40 ? "Blurred, but there."
             : "Was it ever there?");
    return buf;
}

/* ---- bot ------------------------------------------------------------------------------ */

static float hash01(u32 h)
{
    h ^= h >> 16, h *= 0x7feb352du, h ^= h >> 15, h *= 0x846ca68bu, h ^= h >> 16;
    return (h & 0xFFFFFF) / 16777216.0f;
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

/* Traces each target stroke "from memory": a little off in place, size and
 * proportion, wobbly, then presses A. Uses the cheat once, on exercise 3. */
static void bot(Input *in, float t)
{
    (void)t;
    if (!MG.cheat_used && G.level == 2 && G.phase == PH_VIEW && G.pt > 1.0f) {
        in->down |= KEY_L_;
        return;
    }
    if (G.phase == PH_REVIEW && G.pt > 1.6f) {
        in->down |= KEY_A_;
        return;
    }
    if (G.phase != PH_DRAW)
        return;
    u32 seed = (u32)G.level * 7919u + (u32)(G.scx * 13) + (u32)(G.scy * 7);
    float ox = (hash01(seed) - 0.5f) * 24, oy = (hash01(seed + 1) - 0.5f) * 16;
    float sc = 0.9f + 0.2f * hash01(seed + 2);
    float e = G.pt - 0.5f;
    for (int k = 0; k < G.npaths; k++) {
        const Path *p = &G.paths[k];
        float dur = 0.3f + path_len(p) / 280.0f;
        if (e < 0)
            return;   /* lifted between strokes */
        if (e <= dur) {
            float x, y, f = e / dur;
            path_at(p, f, &x, &y);
            float dx = x - G.scx, dy = y - G.scy;
            float r = sc * (1 + 0.12f * sinf(3 * atan2f(dy, dx) + hash01(seed + 3) * 6));
            x = G.scx + dx * r + ox + 5 * sinf(f * 19 + k);
            y = G.scy + dy * r + oy + 5 * cosf(f * 23 + k * 2);
            in->down |= KEY_TOUCH_;
            in->held |= KEY_TOUCH_;
            in->tx = (int)(CV_X + clampf(x, 0, TOP_W - 1) * CV_S);
            in->ty = (int)(CV_Y + clampf(y, 0, TOP_H - 1) * CV_S);
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
    .rules = "A shape floats in front of you for a few\n"
             "seconds, then vanishes. Draw it from memory\n"
             "on the touch screen: the frame there is the\n"
             "top screen, so place it where you saw it.\n"
             "Your match % weighs how much of your ink lies\n"
             "on the shape and how much of it you drew.\n"
             "Five exercises: each harder, shown for less\n"
             "time, and worth more.",
    .controls = "Stylus: draw in the frame (any strokes)\n"
                "A / Done: submit your drawing\n"
                "B / Undo: remove the last stroke\n"
                "Y / Clear: start over\n"
                "25 s to draw.   START: pause",
    .cheat = "Trace it: this exercise counts as 90%",
    .music = "draw",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .verdict = verdict,
    .bot = bot,
};
