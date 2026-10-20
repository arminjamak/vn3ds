/* Miso's Hunt: Miso stalks the glitch dots ("the leak") that seep out of the
 * walls of Aron's flat, while Commander Seraphiel's angels sweep the room
 * with soft, slow beams of light.
 *
 * The flat is seen from a high three-quarter angle. Game logic works in
 * room units on the floor: X 0..320 (left to right), Y 0..160 (back wall to
 * the front). pj() projects a room point (and a height above the floor) to
 * the screen and to a stereo depth: the back of the room sits behind the
 * screen, the front of the floor slightly in front of it.
 *
 * Controls: D-pad / Circle Pad move, A pounces (a short dash; only a
 * pounce catches dots). The cheat, "Nap", stops every beam for 5 seconds and
 * slows the dots down.
 *
 * Run: 75 seconds in three phases of 25 s. Each phase spawns more dots and
 * adds a beam, and every beam sweeps faster.
 *
 * Score (0..100):
 *     60 * min(1, points / 125)      a catch is worth the combo multiplier
 *                                    at that moment (x1..x4)
 *   + 20 * min(1, best combo / 15)
 *   + 20 * max(0, 1 - spotted / 5)
 */

#include "minigame.h"

/* ---- tuning ---------------------------------------------------------------- */

#define RW 320.0f            /* room width in floor units */
#define RD 160.0f            /* room depth */
#define FLOOR_TOP 84.0f      /* screen y of the back edge of the floor */
#define FLOOR_YS 0.9f        /* screen px per room unit of depth */
#define FLOOR_FAR 173.4f     /* room depth that reaches the bottom of the screen */

#define RUN_TIME 75.0f
#define PHASE_LEN 25.0f
#define SIT_TIME 2.4f        /* "Meow." stays up this long */

#define MISO_SPEED 112.0f
#define POUNCE_SPEED 300.0f
#define POUNCE_TIME 0.2f
#define POUNCE_COOL 0.42f
#define CATCH_R 21.0f
#define COMBO_WINDOW 3.0f
#define SPOT_DELAY 0.22f     /* seconds inside a beam before it spots Miso */
#define SPOT_FREEZE 1.4f
#define SPOT_GRACE 1.6f
#define NAP_TIME 5.0f
#define EMERGE_TIME 0.7f

#define PTS_FULL 125.0f
#define COMBO_FULL 15.0f
#define SPOT_ZERO 5.0f

#define MAX_DOTS 12
#define MAX_BEAMS 3
#define MAX_PARTS 48
#define MAX_POPS 8

#define PI_F 3.14159265f
#define TAU_F 6.2831853f

enum { DOT_DRIFT, DOT_BLINK, DOT_SHY };

typedef struct {
    float interval, life;
    int maxdots, beams;
    float bspeed, shy, blink;
} PhaseDef;

static const PhaseDef PH[3] = {
    {1.9f, 8.5f, 4, 1, 0.40f, 0.00f, 0.25f},
    {1.35f, 7.5f, 6, 2, 0.52f, 0.30f, 0.30f},
    {1.0f, 7.0f, 8, 3, 0.64f, 0.45f, 0.30f},
};

static const char *const PHASE_NAME[3] = {
    "Phase 1: something leaks",
    "Phase 2: the leak widens",
    "Phase 3: all eyes on Miso",
};

/* A beam's spot follows a Lissajous path around (cx, cy); it shines from
 * (ox, oy) on the screen at depth od (the window, or a halo near the
 * ceiling, which is close to the viewer). */
typedef struct {
    float cx, cy, ax, ay, ratio, off, r;
    float ox, oy, od;
} BeamDef;

static const BeamDef BD[MAX_BEAMS] = {
    {170, 70, 120, 45, 0.61f, 0.0f, 30, 244, 38, 0.45f},   /* through the window */
    {110, 98, 82, 52, 1.37f, 1.7f, 27, 100, 7, -0.3f},     /* ceiling, left */
    {215, 88, 88, 56, 0.83f, 3.9f, 27, 304, 7, -0.3f},     /* ceiling, right */
};

/* Furniture the cat and the dots cannot enter (room units). */
typedef struct {
    float x0, y0, x1, y1;
} Box;

static const Box OBST[] = {
    {14, 0, 100, 20},    /* bookshelf */
    {0, 62, 48, 142},    /* sofa */
    {278, 122, 320, 160} /* plant */
};

/* ---- state ------------------------------------------------------------------- */

typedef struct {
    bool on;
    int kind;
    float x, y, vx, vy;
    float wx, wy, nx, ny;  /* the wall point it leaks from, inward normal */
    float emerge;          /* 0..1 while leaking out of the wall */
    float age, life;
    float blink_t, flee_cd;
    bool fleeing;
    u32 seed;
} Dot;

typedef struct {
    float ph;              /* path parameter */
    float fade;            /* 0..1 fading in */
    float lock;            /* > 0: flashing after spotting Miso */
    float warn_cd;
    bool near;
} Beam;

typedef struct {
    float x, y, vx, vy, d, life, max, size;
    u32 c;
} Part;

typedef struct {
    float x, y, d, t;
    char text[16];
    u32 c;
} Pop;

static struct {
    float t;
    int phase;
    float banner;
    bool over;
    float outro;          /* seconds since time ran out */
    bool sat;             /* Miso reached the rug and sat down */
    float sit_t;

    /* Miso */
    float x, y, fx, fy, face;
    float walk, movespd;
    float pounce_t, pounce_cd, pdx, pdy;
    int pounce_hits;
    float frozen, grace, expose;
    float step_t;
    float nap;

    /* scoring */
    int caught, combo, best_combo, mult, points, spotted;
    float combo_t;

    Dot dots[MAX_DOTS];
    float spawn_t;
    int spawned, expired;
    Beam beams[MAX_BEAMS];
    int nbeams;
    float beam_on_t;

    Part parts[MAX_PARTS];
    Pop pops[MAX_POPS];
    float shake;
    float quiet;           /* seconds since the last sound other than a step */
    int bird_slot;
    int last_tick;
} S;

/* ---- small helpers ---------------------------------------------------------- */

static float hashf(u32 a)
{
    a ^= a >> 16;
    a *= 0x7feb352du;
    a ^= a >> 15;
    a *= 0x846ca68bu;
    a ^= a >> 16;
    return (float)(a & 0xFFFFFF) / 16777216.0f;
}

static float dist2(float ax, float ay, float bx, float by)
{
    float dx = ax - bx, dy = ay - by;
    return dx * dx + dy * dy;
}

static void sfx(const char *name)
{
    mg_sfx(name);
    S.quiet = 0;
}

static int cur_phase(float t) { return t < PHASE_LEN ? 0 : t < 2 * PHASE_LEN ? 1 : 2; }

static void beam_xy_at(int i, float ph, float *x, float *y)
{
    const BeamDef *b = &BD[i];
    *x = b->cx + b->ax * sinf(ph);
    *y = b->cy + b->ay * sinf(ph * b->ratio + b->off);
}

static void beam_xy(int i, float *x, float *y) { beam_xy_at(i, S.beams[i].ph, x, y); }

/* Push a circle of radius r out of the furniture and keep it in the room. */
static bool keep_out(float *x, float *y, float r, float lo_x, float hi_x, float lo_y, float hi_y)
{
    bool hit = false;
    for (unsigned i = 0; i < ARRAY_LEN(OBST); i++) {
        const Box *b = &OBST[i];
        float x0 = b->x0 - r, x1 = b->x1 + r, y0 = b->y0 - r, y1 = b->y1 + r;
        if (*x <= x0 || *x >= x1 || *y <= y0 || *y >= y1)
            continue;
        float pl = *x - x0, pr = x1 - *x, pt = *y - y0, pb = y1 - *y;
        /* never push through the room's walls */
        if (x0 <= lo_x) pl = 1e9f;
        if (x1 >= hi_x) pr = 1e9f;
        if (y0 <= lo_y) pt = 1e9f;
        if (y1 >= hi_y) pb = 1e9f;
        float m = fminf(fminf(pl, pr), fminf(pt, pb));
        if (m == pl) *x = x0;
        else if (m == pr) *x = x1;
        else if (m == pt) *y = y0;
        else *y = y1;
        hit = true;
    }
    if (*x < lo_x) *x = lo_x, hit = true;
    if (*x > hi_x) *x = hi_x, hit = true;
    if (*y < lo_y) *y = lo_y, hit = true;
    if (*y > hi_y) *y = hi_y, hit = true;
    return hit;
}

/* ---- projection --------------------------------------------------------------- */

typedef struct {
    float x, y, d, k;
} P3;

static float k_at(float Y) { return 0.82f + 0.30f * (Y / RD); }
static float d_at(float Y) { return 0.45f - 0.57f * (Y / RD); }

static P3 pj(float X, float Y, float H)
{
    P3 p;
    p.k = k_at(Y);
    p.x = 200.0f + (X - RW / 2) * p.k;
    p.y = FLOOR_TOP + Y * FLOOR_YS - H * p.k;
    p.d = d_at(Y) - H * 0.0016f;
    return p;
}

static P3 sp(float x, float y, float d)
{
    P3 p = {x, y, d, 1};
    return p;
}

/* ---- effects (update side) --------------------------------------------------- */

static void burst(float sx, float sy, float d, int n, float speed, u32 c)
{
    for (int k = 0; k < n; k++) {
        for (int i = 0; i < MAX_PARTS; i++) {
            Part *p = &S.parts[i];
            if (p->life > 0)
                continue;
            float a = mg_randf() * TAU_F, v = speed * (0.4f + 0.6f * mg_randf());
            p->x = sx;
            p->y = sy;
            p->vx = cosf(a) * v;
            p->vy = sinf(a) * v - speed * 0.4f;
            p->d = d - 0.05f * mg_randf();
            p->life = p->max = 0.35f + 0.35f * mg_randf();
            p->size = 1.5f + 2.0f * mg_randf();
            p->c = (mg_rand() & 1) ? c : RGBA(255, 255, 255, 255);
            break;
        }
    }
}

static void popup(float sx, float sy, float d, const char *text, u32 c)
{
    int best = 0;
    for (int i = 0; i < MAX_POPS; i++)
        if (S.pops[i].t > S.pops[best].t)
            best = i;
    for (int i = 0; i < MAX_POPS; i++)
        if (S.pops[i].t <= 0) {
            best = i;
            break;
        }
    Pop *p = &S.pops[best];
    p->x = sx;
    p->y = sy;
    p->d = d;
    p->t = 0.001f;
    p->c = c;
    snprintf(p->text, sizeof(p->text), "%s", text);
}

static u32 dot_color(int kind)
{
    return kind == DOT_SHY ? RGBA(255, 120, 70, 255) : kind == DOT_BLINK ? RGBA(90, 240, 255, 255)
                                                                         : RGBA(235, 90, 255, 255);
}

/* ---- dots ------------------------------------------------------------------------ */

static int dot_count(void)
{
    int n = 0;
    for (int i = 0; i < MAX_DOTS; i++)
        n += S.dots[i].on;
    return n;
}

static void spawn_dot(void)
{
    Dot *d = NULL;
    for (int i = 0; i < MAX_DOTS; i++)
        if (!S.dots[i].on) {
            d = &S.dots[i];
            break;
        }
    if (!d)
        return;
    memset(d, 0, sizeof(*d));
    const PhaseDef *ph = &PH[S.phase];
    int wall = mg_randi(0, 3);   /* the back wall is twice as likely */
    if (wall >= 2) {
        d->wx = 110 + mg_randf() * 190;
        d->wy = 0;
        d->nx = 0, d->ny = 1;
    } else if (wall == 0) {
        d->wx = 0;
        d->wy = mg_randf() < 0.8f ? 26 + mg_randf() * 32 : 146 + mg_randf() * 8;
        d->nx = 1, d->ny = 0;
    } else {
        d->wx = RW;
        d->wy = 16 + mg_randf() * 104;
        d->nx = -1, d->ny = 0;
    }
    d->on = true;
    d->x = d->wx;
    d->y = d->wy;
    float r = mg_randf();
    d->kind = r < ph->shy ? DOT_SHY : r < ph->shy + ph->blink ? DOT_BLINK : DOT_DRIFT;
    float a = atan2f(d->ny, d->nx) + (mg_randf() - 0.5f) * 1.4f, v = 20 + 12 * mg_randf();
    d->vx = cosf(a) * v;
    d->vy = sinf(a) * v;
    d->life = ph->life * (0.9f + 0.25f * mg_randf());
    d->blink_t = 0.8f + 0.6f * mg_randf();
    d->seed = mg_rand();
    S.spawned++;
    sfx("miso_dot_spawn");
}

static void catch_dot(Dot *d)
{
    P3 p = pj(d->x, d->y, 8);
    int old = S.mult;
    S.caught++;
    S.combo++;
    S.combo_t = COMBO_WINDOW;
    if (S.combo > S.best_combo)
        S.best_combo = S.combo;
    S.mult = S.combo / 3 + 1;
    if (S.mult > 4)
        S.mult = 4;
    S.points += S.mult;
    S.pounce_hits++;
    d->on = false;
    burst(p.x, p.y, p.d - 0.05f, 9, 90, dot_color(d->kind));
    char buf[16];
    snprintf(buf, sizeof(buf), "+%d", S.mult);
    popup(p.x, p.y - 10, p.d - 0.15f, buf, S.mult > 1 ? MG_GOLD : MG_WHITE);
    if (S.mult > old) {
        snprintf(buf, sizeof(buf), "Combo x%d!", S.mult);
        popup(p.x, p.y - 26, p.d - 0.25f, buf, RGBA(255, 160, 220, 255));
        sfx("miso_combo");
    } else {
        sfx("miso_catch");
    }
}

static void update_dots(float dt, float sf)
{
    float mdx, mdy;
    for (int i = 0; i < MAX_DOTS; i++) {
        Dot *d = &S.dots[i];
        if (!d->on)
            continue;
        float st = dt * sf;
        if (d->emerge < 1) {
            d->emerge += st / EMERGE_TIME;
            float e = clampf(d->emerge, 0, 1);
            e = e * (2 - e);
            d->x = d->wx + d->nx * 20 * e;
            d->y = d->wy + d->ny * 20 * e;
            continue;
        }
        d->age += st;
        if (d->age >= d->life) {
            P3 p = pj(d->x, d->y, 8);
            burst(p.x, p.y, p.d, 6, 40, RGBA(160, 160, 190, 255));
            d->on = false;
            S.expired++;
            sfx("miso_dot_fade");
            continue;
        }
        d->flee_cd -= dt;
        mdx = d->x - S.x;
        mdy = d->y - S.y;
        float md = sqrtf(mdx * mdx + mdy * mdy) + 0.001f;
        if (d->kind == DOT_BLINK) {
            d->blink_t -= st;
            if (d->blink_t <= 0) {
                P3 p0 = pj(d->x, d->y, 8);
                burst(p0.x, p0.y, p0.d, 3, 30, dot_color(DOT_BLINK));
                float a = mg_randf() * TAU_F, r = 22 + 26 * mg_randf();
                d->x += cosf(a) * r;
                d->y += sinf(a) * r * 0.7f;
                d->blink_t = 0.9f + 0.7f * mg_randf();
                keep_out(&d->x, &d->y, 6, 8, RW - 8, 8, RD - 4);
                if (md < 110 && S.quiet > 0.2f)
                    sfx("miso_dot_blink");
            }
            d->x += d->vx * 0.25f * st;
            d->y += d->vy * 0.25f * st;
        } else {
            bool flee = d->kind == DOT_SHY && md < 72 && S.frozen <= 0;
            if (flee && !d->fleeing && d->flee_cd <= 0) {
                sfx("miso_dot_flee");
                d->flee_cd = 2.0f;
            }
            d->fleeing = flee;
            if (flee) {
                float v = S.phase >= 2 ? 82 : 72;
                /* run away, with a little sideways wobble */
                float wob = sinf(d->age * 7 + (float)(d->seed & 63)) * 0.5f;
                float ex = mdx / md - mdy / md * wob, ey = mdy / md + mdx / md * wob;
                float el = sqrtf(ex * ex + ey * ey) + 0.001f;
                d->vx = lerpf(d->vx, ex / el * v, clampf(dt * 6, 0, 1));
                d->vy = lerpf(d->vy, ey / el * v, clampf(dt * 6, 0, 1));
            } else {
                float sp2 = sqrtf(d->vx * d->vx + d->vy * d->vy) + 0.001f;
                float a = atan2f(d->vy, d->vx) + sinf(d->age * 1.3f + (float)(d->seed & 255)) * 0.9f * st;
                float v = d->kind == DOT_SHY ? 24 : 26;
                v = lerpf(sp2, v, clampf(dt * 2, 0, 1));
                d->vx = cosf(a) * v;
                d->vy = sinf(a) * v;
            }
            float ox = d->x, oy = d->y;
            d->x += d->vx * st;
            d->y += d->vy * st;
            if (keep_out(&d->x, &d->y, 6, 8, RW - 8, 8, RD - 4) && !flee) {
                if (fabsf(d->x - ox - d->vx * st) > 0.01f)
                    d->vx = -d->vx;
                if (fabsf(d->y - oy - d->vy * st) > 0.01f)
                    d->vy = -d->vy;
            }
        }
    }
}

/* ---- the run ------------------------------------------------------------------- */

static void start(u32 seed)
{
    (void)seed;
    memset(&S, 0, sizeof(S));
    S.x = 160;
    S.y = 112;
    S.fx = 1;
    S.face = 1;
    S.mult = 1;
    S.spawn_t = 0.6f;
    S.nbeams = PH[0].beams;
    for (int i = 0; i < MAX_BEAMS; i++)
        S.beams[i].ph = BD[i].off * 0.5f + 0.4f;
    S.beam_on_t = 0.8f;
    S.banner = 2.2f;
    S.last_tick = 99;
    S.bird_slot = -1;
}

static void be_spotted(int beam)
{
    S.frozen = SPOT_FREEZE;
    S.spotted++;
    if (S.combo >= 3)
        popup(pj(S.x, S.y, 0).x, pj(S.x, S.y, 40).y, -0.25f, "Combo lost", RGBA(200, 200, 220, 255));
    S.combo = 0;
    S.mult = 1;
    S.combo_t = 0;
    S.expose = 0;
    S.pounce_t = 0;
    S.beams[beam].lock = 1.0f;
    S.shake = 0.35f;
    P3 p = pj(S.x, S.y, 30);
    popup(p.x, p.y - 26, p.d - 0.3f, "Spotted!", MG_GOLD);
    sfx("miso_spotted");
}

static bool update(const Input *in, float dt, bool cheat)
{
    /* effects keep running in the outro */
    for (int i = 0; i < MAX_PARTS; i++) {
        Part *p = &S.parts[i];
        if (p->life <= 0)
            continue;
        p->life -= dt;
        p->x += p->vx * dt;
        p->y += p->vy * dt;
        p->vy += 160 * dt;
    }
    for (int i = 0; i < MAX_POPS; i++)
        if (S.pops[i].t > 0 && (S.pops[i].t += dt) > 1.0f)
            S.pops[i].t = 0;
    if (S.shake > 0)
        S.shake -= dt;
    S.quiet += dt;

    if (S.over) {
        /* trot to the middle of the rug, sit, have the last word */
        S.outro += dt;
        if (!S.sat) {
            float dx = 160 - S.x, dy = 104 - S.y, dl = sqrtf(dx * dx + dy * dy), stp = 190 * dt;
            if (dl <= stp || S.outro > 1.3f) {
                S.sat = true;
                S.movespd = 0;
                sfx("miso_meow");
            } else {
                S.x += dx / dl * stp;
                S.y += dy / dl * stp;
                keep_out(&S.x, &S.y, 9, 12, RW - 12, 10, RD - 6);
                S.walk += dt * 15;
                S.movespd = 190;
                if (fabsf(dx) > 3)
                    S.face = dx > 0 ? 1.0f : -1.0f;
            }
        } else {
            S.sit_t += dt;
        }
        return !S.sat || S.sit_t < SIT_TIME;
    }

    S.t += dt;
    if (S.banner > 0)
        S.banner -= dt;

    /* the end: Miso sits down and has the last word */
    if (S.t >= RUN_TIME) {
        S.over = true;
        S.outro = 0;
        S.pounce_t = 0;
        S.frozen = 0;
        S.nap = 0;
        S.grace = 0;
        S.expose = 0;
        sfx("miso_time_up");
        return true;
    }
    int left = (int)ceilf(RUN_TIME - S.t);
    if (left <= 5 && left != S.last_tick) {
        S.last_tick = left;
        sfx("miso_tick");
    }

    /* the cheat: a nap */
    if (cheat) {
        S.nap = NAP_TIME;
        S.frozen = 0;
        S.expose = 0;
        P3 p = pj(S.x, S.y, 30);
        popup(p.x, p.y - 10, p.d - 0.3f, "Nap time", RGBA(170, 200, 255, 255));
        sfx("miso_nap");
    }
    bool napping = S.nap > 0;
    if (napping) {
        S.nap -= dt;
        if (S.nap <= 0) {
            S.nap = 0;
            S.grace = 1.0f;
            sfx("miso_wake");
        }
    }

    /* phases */
    int np = cur_phase(S.t);
    if (np != S.phase) {
        S.phase = np;
        S.nbeams = PH[np].beams;
        S.banner = 2.4f;
        S.beam_on_t = 1.0f;
        S.spawn_t = fminf(S.spawn_t, 0.4f);
        sfx("miso_phase");
    }
    if (S.beam_on_t > 0 && (S.beam_on_t -= dt) <= 0)
        sfx("miso_beam_on");

    /* the bird outside chirps now and then */
    int slot = (int)(S.t / 4.0f);
    if (slot != S.bird_slot) {
        S.bird_slot = slot;
        if (slot > 0 && hashf((u32)slot * 7919u) < 0.45f && S.quiet > 0.4f)
            sfx("miso_bird");
    }

    /* ---- Miso ---- */
    float ix = in->cx, iy = -in->cy;
    if (fabsf(ix) < 0.15f) ix = 0;
    if (fabsf(iy) < 0.15f) iy = 0;
    if (in->held & KEY_LEFT_) ix -= 1;
    if (in->held & KEY_RIGHT_) ix += 1;
    if (in->held & KEY_UP_) iy -= 1;
    if (in->held & KEY_DOWN_) iy += 1;
    float il = sqrtf(ix * ix + iy * iy);
    if (il > 1) {
        ix /= il;
        iy /= il;
        il = 1;
    }

    float ox = S.x, oy = S.y;
    bool pouncing_before = S.pounce_t > 0;
    if (S.pounce_cd > 0)
        S.pounce_cd -= dt;
    if (S.grace > 0)
        S.grace -= dt;
    if (S.frozen > 0) {
        S.frozen -= dt;
        if (S.frozen <= 0) {
            S.grace = SPOT_GRACE;
            sfx("miso_recover");
        }
    } else if (S.pounce_t > 0) {
        S.x += S.pdx * POUNCE_SPEED * dt;
        S.y += S.pdy * POUNCE_SPEED * dt;
        S.pounce_t -= dt;
    } else {
        S.x += ix * MISO_SPEED * dt;
        S.y += iy * MISO_SPEED * dt;
        if (il > 0.2f) {
            S.fx = ix / il;
            S.fy = iy / il;
            if (fabsf(ix) > 0.1f)
                S.face = ix > 0 ? 1.0f : -1.0f;
        }
        if ((in->down & KEY_A_) && S.pounce_cd <= 0) {
            if (il > 0.2f) {
                S.pdx = ix / il;
                S.pdy = iy / il;
            } else {
                S.pdx = S.fx;
                S.pdy = S.fy;
            }
            if (fabsf(S.pdx) > 0.1f)
                S.face = S.pdx > 0 ? 1.0f : -1.0f;
            S.pounce_t = POUNCE_TIME;
            S.pounce_cd = POUNCE_COOL;
            S.pounce_hits = 0;
            sfx("miso_pounce");
        }
    }
    keep_out(&S.x, &S.y, 9, 12, RW - 12, 10, RD - 6);
    float moved = sqrtf(dist2(S.x, S.y, ox, oy));
    S.movespd = dt > 0 ? moved / dt : 0;
    if (S.movespd > 15 && S.pounce_t <= 0) {
        S.walk += dt * 13;
        S.step_t += dt;
        if (S.step_t > 0.3f) {
            S.step_t = 0;
            if (S.quiet > 0.25f)
                mg_sfx("miso_step");
        }
    } else {
        S.step_t = 0.25f;
    }

    /* catching: only a pounce catches, anything within reach */
    if (pouncing_before || S.pounce_t > 0) {
        for (int i = 0; i < MAX_DOTS; i++) {
            Dot *d = &S.dots[i];
            if (d->on && d->emerge >= 1 && dist2(d->x, d->y, S.x, S.y) < CATCH_R * CATCH_R)
                catch_dot(d);
        }
        if (S.pounce_t <= 0 && S.pounce_hits == 0)
            sfx("miso_whiff");   /* landed with nothing */
    }

    /* combo window */
    if (S.combo > 0) {
        S.combo_t -= dt;
        if (S.combo_t <= 0) {
            if (S.combo >= 3)
                sfx("miso_combo_break");
            S.combo = 0;
            S.mult = 1;
        }
    }

    /* ---- beams ---- */
    bool inside_any = false;
    int inside_beam = 0;
    for (int i = 0; i < MAX_BEAMS; i++) {
        Beam *b = &S.beams[i];
        if (b->lock > 0)
            b->lock -= dt;
        if (i >= S.nbeams)
            continue;
        if (b->warn_cd > 0)
            b->warn_cd -= dt;
        if (napping)
            continue;
        b->fade = fminf(1, b->fade + dt / 1.5f);
        b->ph += PH[S.phase].bspeed * dt;
        float bx, by;
        beam_xy(i, &bx, &by);
        float dd = sqrtf(dist2(bx, by, S.x, S.y));
        if (b->fade >= 1 && dd < BD[i].r * 0.9f) {
            inside_any = true;
            inside_beam = i;
        }
        bool near = dd < BD[i].r + 40;
        if (near && !b->near && b->warn_cd <= 0 && S.frozen <= 0 && S.quiet > 0.3f) {
            sfx("miso_beam_sweep");
            b->warn_cd = 4.0f;
        }
        b->near = near;
    }
    if (inside_any && !napping && S.frozen <= 0 && S.grace <= 0) {
        S.expose += dt;
        if (S.expose >= SPOT_DELAY)
            be_spotted(inside_beam);
    } else {
        S.expose = fmaxf(0, S.expose - dt * 2);
    }

    /* ---- dots ---- */
    float sf = napping ? 0.3f : 1.0f;
    S.spawn_t -= dt * sf;
    if (S.spawn_t <= 0) {
        if (dot_count() < PH[S.phase].maxdots)
            spawn_dot();
        S.spawn_t = PH[S.phase].interval * (0.8f + 0.4f * mg_randf());
    }
    update_dots(dt, sf);
    return true;
}

/* ---- drawing helpers --------------------------------------------------------------- */

static void tri3(int eye, P3 a, P3 b, P3 c, u32 col)
{
    gfx_triangle(a.x + mg_shift(eye, a.d), a.y, b.x + mg_shift(eye, b.d), b.y, c.x + mg_shift(eye, c.d), c.y,
                 col);
}

static void quad3(int eye, P3 a, P3 b, P3 c, P3 d, u32 col)
{
    tri3(eye, a, b, c, col);
    tri3(eye, a, c, d, col);
}

static void line3(int eye, P3 a, P3 b, float th, u32 col)
{
    gfx_line(a.x + mg_shift(eye, a.d), a.y, b.x + mg_shift(eye, b.d), b.y, th, col);
}

/* Screen-space ellipse at one depth. */
static void ell(int eye, float cx, float cy, float rx, float ry, float d, u32 c, int n)
{
    float s = mg_shift(eye, d), px = cx + rx + s, py = cy;
    for (int i = 1; i <= n; i++) {
        float a = (float)i * TAU_F / (float)n;
        float x = cx + cosf(a) * rx + s, y = cy + sinf(a) * ry;
        gfx_triangle(cx + s, cy, px, py, x, y, c);
        px = x;
        py = y;
    }
}

/* Ellipse lying on the floor (or at height H), in perspective. */
static void fell(int eye, float cx, float cy, float rx, float ry, float H, u32 c, int n)
{
    P3 o = pj(cx, cy, H), prev = pj(cx + rx, cy, H);
    for (int i = 1; i <= n; i++) {
        float a = (float)i * TAU_F / (float)n;
        P3 q = pj(cx + cosf(a) * rx, cy + sinf(a) * ry, H);
        tri3(eye, o, prev, q, c);
        prev = q;
    }
}

/* A box standing on the floor: the side facing the room's centre, the
 * front and the top. */
static void box3(int eye, float x0, float y0, float x1, float y1, float h, u32 top, u32 side, u32 front)
{
    if (x1 < RW / 2)
        quad3(eye, pj(x1, y0, 0), pj(x1, y1, 0), pj(x1, y1, h), pj(x1, y0, h), side);
    else if (x0 > RW / 2)
        quad3(eye, pj(x0, y0, 0), pj(x0, y1, 0), pj(x0, y1, h), pj(x0, y0, h), side);
    quad3(eye, pj(x0, y1, 0), pj(x1, y1, 0), pj(x1, y1, h), pj(x0, y1, h), front);
    quad3(eye, pj(x0, y0, h), pj(x1, y0, h), pj(x1, y1, h), pj(x0, y1, h), top);
}

static u32 mixc(u32 a, u32 b, float t)
{
    int r = (int)lerpf((float)(a >> 24), (float)(b >> 24), t);
    int g = (int)lerpf((float)((a >> 16) & 255), (float)((b >> 16) & 255), t);
    int bl = (int)lerpf((float)((a >> 8) & 255), (float)((b >> 8) & 255), t);
    int al = (int)lerpf((float)(a & 255), (float)(b & 255), t);
    return RGBA(r, g, bl, al);
}

/* ---- the room ------------------------------------------------------------------------ */

#define WALL_D 0.45f
#define WIN_X0 196.0f
#define WIN_X1 292.0f
#define WIN_Y0 10.0f
#define WIN_Y1 62.0f

static void draw_window(int eye)
{
    /* outside, far behind: sky, a rooftop, the wire and the bird */
    float s1 = mg_shift(eye, 1.0f);
    gfx_gradient(WIN_X0 - 8 + s1, WIN_Y0 - 4, WIN_X1 - WIN_X0 + 16, WIN_Y1 - WIN_Y0 + 8, RGBA(120, 170, 220, 255),
                 RGBA(250, 200, 170, 255));
    mg_rect(eye, WIN_X0 - 8, 44, 40, 24, 0.95f, RGBA(90, 90, 120, 255));
    mg_rect(eye, WIN_X0 + 34, 50, 30, 18, 0.95f, RGBA(110, 100, 130, 255));
    mg_rect(eye, WIN_X0 + 70, 40, 40, 28, 0.95f, RGBA(80, 85, 115, 255));
    for (int i = 0; i < 4; i++)
        mg_rect(eye, WIN_X0 + 76 + i * 8, 46, 3, 4, 0.95f, RGBA(255, 230, 150, 200));
    /* the wire sags between two poles out of view */
    float wy0 = 26, wy1 = 33, wy2 = 28;
    mg_line(eye, WIN_X0 - 8, wy0, 240, wy1, 1.2f, 0.8f, RGBA(40, 40, 50, 255));
    mg_line(eye, 240, wy1, WIN_X1 + 8, wy2, 1.2f, 0.8f, RGBA(40, 40, 50, 255));
    /* the bird hops along the wire every few seconds */
    int slot = (int)(S.t / 4.0f);
    float u = hashf((u32)slot * 2654435761u + 17u);
    float bx = WIN_X0 + 18 + u * (WIN_X1 - WIN_X0 - 36);
    float hop = S.t - (float)slot * 4.0f;
    float by = (bx < 240 ? lerpf(wy0, wy1, (bx - (WIN_X0 - 8)) / (240 - (WIN_X0 - 8)))
                         : lerpf(wy1, wy2, (bx - 240) / (WIN_X1 + 8 - 240)));
    if (hop < 0.25f)
        by -= sinf(hop / 0.25f * PI_F) * 5;
    float bf = hashf((u32)slot * 31u + 5u) < 0.5f ? -1.0f : 1.0f;
    if (S.over)
        bf = -1;
    float bd = 0.78f;
    mg_line(eye, bx - bf * 4, by - 3, bx - bf * 8, by - 1, 2.0f, bd, RGBA(70, 60, 60, 255));    /* tail */
    ell(eye, bx, by - 4, 4.5f, 3.4f, bd, RGBA(110, 90, 80, 255), 8);                          /* body */
    ell(eye, bx + bf * 0.5f, by - 3, 3.0f, 2.2f, bd, RGBA(230, 150, 110, 255), 6);            /* breast */
    mg_circle(eye, bx + bf * 3.5f, by - 7.5f, 2.6f, bd, RGBA(110, 90, 80, 255));               /* head */
    mg_tri(eye, bx + bf * 5.8f, by - 8.2f, bx + bf * 8.0f, by - 7.4f, bx + bf * 5.8f, by - 6.6f, bd,
           RGBA(240, 190, 80, 255));
    mg_rect(eye, bx + bf * 4.2f - 0.6f, by - 8.6f, 1.2f, 1.2f, bd, MG_INK);
    mg_line(eye, bx - 1, by - 1, bx - 1, by + 1, 0.8f, bd, RGBA(60, 50, 40, 255));
    mg_line(eye, bx + 1, by - 1, bx + 1, by + 1, 0.8f, bd, RGBA(60, 50, 40, 255));
}

static void draw_room(int eye)
{
    const u32 wall = RGBA(214, 196, 178, 255), wall_side = RGBA(178, 160, 148, 255);
    /* the window first, so the wall around it covers the sky's edges */
    draw_window(eye);
    mg_rect(eye, 69, 0, WIN_X0 - 69, FLOOR_TOP, WALL_D, wall);
    mg_rect(eye, WIN_X1, 0, 331 - WIN_X1, FLOOR_TOP, WALL_D, wall);
    mg_rect(eye, WIN_X0, 0, WIN_X1 - WIN_X0, WIN_Y0, WALL_D, wall);
    mg_rect(eye, WIN_X0, WIN_Y1, WIN_X1 - WIN_X0, FLOOR_TOP - WIN_Y1, WALL_D, wall);
    /* wallpaper stripes */
    for (int i = 0; i < 12; i++) {
        float x = 76 + i * 22.5f;
        if (x + 6 > WIN_X0 - 4 && x < WIN_X1 + 4)
            mg_rect(eye, x, WIN_Y1 + 6, 6, FLOOR_TOP - WIN_Y1 - 6, WALL_D, RGBA(200, 180, 165, 255));
        else
            mg_rect(eye, x, 0, 6, FLOOR_TOP, WALL_D, RGBA(200, 180, 165, 255));
    }
    /* window frame, cross bars and sill */
    const u32 frame = RGBA(245, 240, 232, 255);
    mg_rect(eye, WIN_X0 - 3, WIN_Y0 - 3, WIN_X1 - WIN_X0 + 6, 4, WALL_D - 0.01f, frame);
    mg_rect(eye, WIN_X0 - 3, WIN_Y1 - 1, WIN_X1 - WIN_X0 + 6, 4, WALL_D - 0.01f, frame);
    mg_rect(eye, WIN_X0 - 3, WIN_Y0 - 3, 4, WIN_Y1 - WIN_Y0 + 6, WALL_D - 0.01f, frame);
    mg_rect(eye, WIN_X1 - 1, WIN_Y0 - 3, 4, WIN_Y1 - WIN_Y0 + 6, WALL_D - 0.01f, frame);
    mg_rect(eye, (WIN_X0 + WIN_X1) / 2 - 1.5f, WIN_Y0, 3, WIN_Y1 - WIN_Y0, WALL_D - 0.01f, frame);
    mg_rect(eye, WIN_X0 - 7, WIN_Y1 + 2, WIN_X1 - WIN_X0 + 14, 5, WALL_D - 0.05f, RGBA(230, 222, 210, 255));
    /* a framed photo on the wall: a snapshot */
    mg_rect(eye, 157, 22, 26, 20, WALL_D - 0.01f, RGBA(90, 70, 55, 255));
    mg_rect(eye, 160, 25, 20, 14, WALL_D - 0.01f, RGBA(170, 200, 210, 255));
    mg_circle(eye, 167, 34, 3, WALL_D - 0.01f, RGBA(120, 110, 100, 255));
    mg_circle(eye, 174, 35, 2.5f, WALL_D - 0.01f, RGBA(150, 150, 160, 255));

    /* side walls lean towards the viewer */
    P3 tl = sp(0, 0, 0.25f), bl = sp(0, 240, -0.15f);
    P3 ctl = sp(69, 0, WALL_D), cbl = pj(0, 0, 0), fl = pj(0, FLOOR_FAR, 0);
    tri3(eye, tl, ctl, cbl, wall_side);
    tri3(eye, tl, cbl, fl, wall_side);
    tri3(eye, tl, fl, bl, wall_side);
    P3 tr = sp(400, 0, 0.25f), br = sp(400, 240, -0.15f);
    P3 ctr = sp(331, 0, WALL_D), cbr = pj(RW, 0, 0), fr = pj(RW, FLOOR_FAR, 0);
    tri3(eye, tr, ctr, cbr, wall_side);
    tri3(eye, tr, cbr, fr, wall_side);
    tri3(eye, tr, fr, br, wall_side);
    /* the room's corners */
    line3(eye, ctl, cbl, 1.5f, RGBA(170, 150, 138, 255));
    line3(eye, ctr, cbr, 1.5f, RGBA(170, 150, 138, 255));

    /* floor: wooden boards in strips that get warmer towards the front */
    const int strips = 6;
    for (int i = 0; i < strips; i++) {
        float y0 = FLOOR_FAR * i / strips, y1 = FLOOR_FAR * (i + 1) / strips;
        u32 c = mixc(RGBA(128, 92, 68, 255), RGBA(168, 120, 86, 255), (float)i / (strips - 1));
        quad3(eye, pj(0, y0, 0), pj(RW, y0, 0), pj(RW, y1, 0), pj(0, y1, 0), c);
    }
    for (int i = 1; i < 10; i++)
        line3(eye, pj(i * 32.0f, 0, 0), pj(i * 32.0f, FLOOR_FAR, 0), 1.0f, RGBA(95, 66, 50, 160));
    for (int i = 0; i < 10; i += 2) {
        float y = 20 + (float)((i * 53) % 140);
        float x = (float)(i * 32) + 0.5f;
        line3(eye, pj(x, y, 0), pj(x + 32, y, 0), 1.0f, RGBA(95, 66, 50, 120));
    }
    /* skirting boards */
    line3(eye, pj(0, 0, 0), pj(RW, 0, 0), 3.0f, RGBA(240, 232, 220, 255));
    line3(eye, pj(0, 0, 0), pj(0, FLOOR_FAR, 0), 3.0f, RGBA(225, 215, 200, 255));
    line3(eye, pj(RW, 0, 0), pj(RW, FLOOR_FAR, 0), 3.0f, RGBA(225, 215, 200, 255));

    /* the window's patch of light on the floor */
    quad3(eye, pj(196, 2, 0), pj(262, 2, 0), pj(250, 40, 0), pj(176, 40, 0), RGBA(255, 235, 200, 40));

    /* rug */
    fell(eye, 162, 94, 92, 42, 0, RGBA(120, 50, 60, 255), 14);
    fell(eye, 162, 94, 84, 37, 0.3f, RGBA(196, 150, 96, 255), 14);
    fell(eye, 162, 94, 72, 31, 0.6f, RGBA(150, 64, 72, 255), 14);
    fell(eye, 162, 94, 30, 13, 0.9f, RGBA(220, 180, 110, 255), 8);
}

static void draw_bookshelf(int eye)
{
    const float x0 = 16, x1 = 98, y1 = 18, h = 82;
    box3(eye, x0, 0, x1, y1, h, RGBA(150, 104, 70, 255), RGBA(110, 74, 52, 255), RGBA(70, 46, 34, 255));
    const u32 wood = RGBA(140, 96, 64, 255);
    /* posts and shelves on the front face */
    quad3(eye, pj(x0, y1, 0), pj(x0 + 4, y1, 0), pj(x0 + 4, y1, h), pj(x0, y1, h), wood);
    quad3(eye, pj(x1 - 4, y1, 0), pj(x1, y1, 0), pj(x1, y1, h), pj(x1 - 4, y1, h), wood);
    for (int s = 0; s < 4; s++) {
        float hb = 2 + s * 26.0f;
        quad3(eye, pj(x0, y1, hb), pj(x1, y1, hb), pj(x1, y1, hb + 3), pj(x0, y1, hb + 3), wood);
    }
    static const u32 BOOK[6] = {
        RGBA(180, 60, 60, 255), RGBA(60, 110, 160, 255), RGBA(220, 190, 90, 255),
        RGBA(90, 140, 90, 255), RGBA(200, 200, 190, 255), RGBA(120, 80, 140, 255),
    };
    for (int s = 0; s < 3; s++) {
        float base = 5 + s * 26.0f, bx = x0 + 6;
        for (int i = 0; bx < x1 - 8 && i < 11; i++) {
            u32 hsh = (u32)(s * 31 + i * 7 + 3);
            float w = 4 + 3 * hashf(hsh), hh = 13 + 8 * hashf(hsh + 99);
            if (s == 1 && i == 6) {   /* a gap, and a book leaning */
                bx += 10;
                continue;
            }
            quad3(eye, pj(bx, y1 + 0.5f, base), pj(bx + w, y1 + 0.5f, base), pj(bx + w, y1 + 0.5f, base + hh),
                  pj(bx, y1 + 0.5f, base + hh), BOOK[(s * 5 + i * 3) % 6]);
            bx += w + 0.6f;
        }
    }
    /* on top: a small lamp and a stack of notes (theories) */
    P3 lamp = pj(30, 10, h);
    mg_rect(eye, lamp.x - 1, lamp.y - 14, 2, 14, lamp.d - 0.02f, RGBA(60, 60, 60, 255));
    mg_tri(eye, lamp.x - 8, lamp.y - 12, lamp.x + 8, lamp.y - 12, lamp.x, lamp.y - 22, lamp.d - 0.03f,
           RGBA(240, 210, 140, 255));
    P3 notes = pj(80, 9, h);
    mg_rect(eye, notes.x - 9, notes.y - 4, 16, 4, notes.d - 0.02f, RGBA(250, 250, 240, 255));
    mg_rect(eye, notes.x - 8, notes.y - 7, 15, 3, notes.d - 0.03f, RGBA(255, 240, 160, 255));
}

static void draw_sofa(int eye)
{
    const u32 top = RGBA(96, 140, 150, 255), side = RGBA(70, 108, 118, 255), front = RGBA(58, 92, 102, 255);
    box3(eye, 0, 64, 12, 140, 46, top, side, front);       /* back rest */
    box3(eye, 0, 62, 48, 74, 30, top, side, front);        /* far arm */
    box3(eye, 10, 74, 46, 130, 20, top, side, front);      /* seat */
    /* cushions */
    line3(eye, pj(12, 102, 20.5f), pj(46, 102, 20.5f), 1.2f, RGBA(60, 96, 106, 255));
    quad3(eye, pj(22, 80, 20.5f), pj(40, 80, 20.5f), pj(40, 96, 20.5f), pj(22, 96, 20.5f), RGBA(230, 200, 120, 255));
    box3(eye, 0, 130, 48, 142, 30, top, side, front);      /* near arm */
}

static void draw_plant(int eye)
{
    box3(eye, 288, 138, 312, 154, 18, RGBA(160, 80, 50, 255), RGBA(170, 90, 60, 255), RGBA(190, 100, 66, 255));
    fell(eye, 300, 146, 10, 6, 18.5f, RGBA(70, 50, 36, 255), 10);
    P3 b = pj(300, 146, 18);
    float sway = sinf(S.t * 1.3f) * 2.0f;
    static const float ANG[7] = {-2.6f, -2.2f, -1.8f, -1.45f, -1.1f, -0.75f, -0.45f};
    static const float LEN[7] = {28, 38, 44, 48, 42, 36, 25};
    for (int i = 0; i < 7; i++) {
        float a = ANG[i], L = LEN[i] * b.k;
        float d = b.d - 0.04f - 0.03f * (float)(i % 3);
        float tx = b.x + cosf(a) * L + sway * (float)(i - 3) * 0.3f, ty = b.y + sinf(a) * L;
        float mx = b.x + cosf(a) * L * 0.5f, my = b.y + sinf(a) * L * 0.5f;
        float nx = -sinf(a) * 7 * b.k, ny = cosf(a) * 7 * b.k;
        u32 c = (i & 1) ? RGBA(70, 150, 80, 255) : RGBA(90, 175, 95, 255);
        mg_tri(eye, b.x, b.y, mx + nx, my + ny, tx, ty, d, c);
        mg_tri(eye, b.x, b.y, mx - nx, my - ny, tx, ty, d, mixc(c, RGBA(30, 80, 40, 255), 0.3f));
    }
}

/* ---- beams ------------------------------------------------------------------------------ */

static float beam_alpha(int i)
{
    float a = S.beams[i].fade;
    if (S.over)
        a *= clampf(1 - S.outro / 1.0f, 0, 1);
    return a;
}

static void draw_beam_spots(int eye)
{
    for (int i = 0; i < S.nbeams; i++) {
        float a = beam_alpha(i);
        if (a <= 0)
            continue;
        float x, y, r = BD[i].r;
        beam_xy(i, &x, &y);
        bool lock = S.beams[i].lock > 0;
        u32 c = lock ? RGBA(255, 220, 120, 255) : S.nap > 0 ? RGBA(170, 180, 210, 255) : RGBA(255, 248, 225, 255);
        float k = S.nap > 0 ? 0.5f : 1.0f;
        fell(eye, x, y, r, r * 0.8f, 0.4f, rgba_alpha(c, 0.24f * a * k), 14);
        fell(eye, x, y, r * 0.6f, r * 0.48f, 0.5f, rgba_alpha(c, 0.26f * a * k), 10);
    }
}

static void draw_halo(int eye, float x, float y, float d, float a)
{
    u32 gold = rgba_alpha(RGBA(255, 220, 130, 255), a);
    u32 wing = rgba_alpha(RGBA(255, 255, 255, 255), a * 0.75f);
    /* little wings either side of a ring */
    mg_tri(eye, x - 9, y + 3, x - 26, y - 2, x - 20, y + 9, d + 0.02f, wing);
    mg_tri(eye, x - 9, y + 5, x - 22, y + 10, x - 14, y + 13, d + 0.02f, wing);
    mg_tri(eye, x + 9, y + 3, x + 26, y - 2, x + 20, y + 9, d + 0.02f, wing);
    mg_tri(eye, x + 9, y + 5, x + 22, y + 10, x + 14, y + 13, d + 0.02f, wing);
    float px = x + 11, py = y + 4;
    for (int i = 1; i <= 8; i++) {
        float ang = (float)i * TAU_F / 8;
        float qx = x + cosf(ang) * 11, qy = y + 4 + sinf(ang) * 3.5f;
        mg_line(eye, px, py, qx, qy, 2.0f, d, gold);
        px = qx;
        py = qy;
    }
}

static void draw_beam_cones(int eye)
{
    for (int i = 0; i < S.nbeams; i++) {
        float a = beam_alpha(i);
        if (a <= 0)
            continue;
        const BeamDef *bd = &BD[i];
        float x, y, r = bd->r;
        beam_xy(i, &x, &y);
        bool lock = S.beams[i].lock > 0;
        float k = S.nap > 0 ? 0.35f : 1.0f;
        u32 c = lock ? RGBA(255, 220, 120, 255) : RGBA(255, 250, 230, 255);
        P3 o = sp(bd->ox, bd->oy + 6, bd->od);
        P3 l = pj(x - r, y, 0), rr = pj(x + r, y, 0);
        P3 l2 = pj(x - r * 0.5f, y, 0), r2 = pj(x + r * 0.5f, y, 0);
        tri3(eye, o, l, rr, rgba_alpha(c, 0.10f * a * k));
        tri3(eye, o, l2, r2, rgba_alpha(c, 0.10f * a * k));
        if (i == 0) {
            /* light pours through the window */
            mg_rect(eye, WIN_X0, WIN_Y0, WIN_X1 - WIN_X0, WIN_Y1 - WIN_Y0, WALL_D - 0.02f,
                    rgba_alpha(c, 0.25f * a * k));
        } else {
            draw_halo(eye, bd->ox, bd->oy, bd->od, a * (S.nap > 0 ? 0.4f : 1.0f));
        }
    }
}

/* ---- dots -------------------------------------------------------------------------------- */

static void draw_leak(int eye, const Dot *d)
{
    /* a crack of corrupted pixels where the wall gives way */
    P3 b = pj(d->wx, d->wy, 0);
    float e = clampf(d->emerge, 0, 1), a = 1 - e * 0.6f;
    u32 seed = d->seed + (u32)(S.t * 14);
    float dir = d->nx > 0 ? 1.0f : d->nx < 0 ? -1.0f : 0.0f;
    float px = b.x, py = b.y;
    for (int i = 0; i < 4; i++) {
        float qx = px + (hashf(seed + i) - 0.5f) * 8 + dir * 1.5f, qy = py - 5 - 3 * hashf(seed + 10 + i);
        mg_line(eye, px, py, qx, qy, 1.5f, b.d, rgba_alpha(i & 1 ? RGBA(90, 240, 255, 255) : RGBA(235, 90, 255, 255), a));
        px = qx;
        py = qy;
    }
    for (int i = 0; i < 4; i++) {
        float ox = (hashf(seed * 3 + i) - 0.5f) * 16, oy = -hashf(seed * 5 + i) * 18;
        mg_rect(eye, b.x + ox, b.y + oy, 2, 2, b.d - 0.01f, rgba_alpha(MG_WHITE, a * 0.8f));
    }
}

static void draw_dot(int eye, const Dot *d)
{
    float fade = 1;
    if (S.over)
        fade = clampf(1 - S.outro / 0.6f, 0, 1);
    if (fade <= 0)
        return;
    if (d->emerge < 1)
        draw_leak(eye, d);
    float left = d->life - d->age;
    if (d->emerge >= 1 && left < 1.6f && fmodf(S.t, 0.2f) < 0.08f + 0.06f * left / 1.6f)
        return;   /* flickering out */
    float bob = sinf(S.t * 4 + (float)(d->seed & 31)) * 2;
    P3 g = pj(d->x, d->y, 0);
    P3 p = pj(d->x, d->y, 9 + bob);
    float k = p.k, e = clampf(d->emerge * 1.4f, 0.2f, 1);
    u32 c = dot_color(d->kind);
    float dz = p.d - 0.05f;
    mg_circle(eye, g.x, g.y, 4.5f * k, g.d, RGBA(30, 10, 40, (int)(80 * fade)));
    mg_circle(eye, p.x, p.y, 12 * k * e, dz + 0.01f, rgba_alpha(c, 0.22f * fade));
    mg_circle(eye, p.x, p.y, 7.5f * k * e, dz + 0.01f, rgba_alpha(c, 0.3f * fade));
    float s = 7 * k * e, j = 2.0f + 1.6f * hashf(d->seed + (u32)(S.t * 10));
    mg_rect(eye, p.x - s / 2 - 1, p.y - s / 2 - 1, s + 2, s + 2, dz + 0.005f, RGBA(30, 10, 50, (int)(200 * fade)));
    mg_rect(eye, p.x - s / 2 - j, p.y - s / 2, s, s, dz, rgba_alpha(RGBA(0, 255, 255, 255), 0.6f * fade));
    mg_rect(eye, p.x - s / 2 + j, p.y - s / 2, s, s, dz, rgba_alpha(RGBA(255, 0, 200, 255), 0.6f * fade));
    u32 core = (int)(S.t * 8 + (float)(d->seed & 7)) % 3 == 0 ? MG_WHITE : c;
    mg_rect(eye, p.x - s / 2, p.y - s / 2, s, s, dz - 0.01f, rgba_alpha(core, fade));
    /* stray pixels */
    u32 hs = d->seed + (u32)(S.t * 12);
    for (int i = 0; i < 2; i++) {
        float ox = (hashf(hs + i * 13) - 0.5f) * 22 * k, oy = (hashf(hs + i * 29) - 0.5f) * 14 * k;
        mg_rect(eye, p.x + ox, p.y + oy, 2.5f, 2.5f, dz, rgba_alpha(c, 0.8f * fade));
    }
    if (d->kind == DOT_SHY && d->fleeing)
        mg_text_centered(eye, "!", p.x, p.y - 20 * k, 0.4f, dz - 0.05f, RGBA(255, 160, 120, 255));
}

/* ---- Miso ---------------------------------------------------------------------------------- */

#define FUR RGBA(236, 150, 62, 255)          /* orange, like the story sprites */
#define FUR_DARK RGBA(196, 108, 38, 255)
#define FUR_WHITE RGBA(252, 238, 214, 255)
#define EAR_PINK RGBA(240, 160, 170, 255)

static void draw_head(int eye, float hx, float hy, float k, float d, float f, int eyes)
{
    /* eyes: 0 open, 1 closed, 2 wide (startled) */
    mg_tri(eye, hx - 6.5f * k, hy - 2 * k, hx - 5 * k + f * k, hy - 11.5f * k, hx - 0.5f * k, hy - 6 * k, d, FUR);
    mg_tri(eye, hx + 0.5f * k, hy - 6 * k, hx + 5 * k + f * k, hy - 11.5f * k, hx + 6.5f * k, hy - 2 * k, d, FUR);
    mg_tri(eye, hx - 5 * k, hy - 3.5f * k, hx - 4.6f * k + f * k, hy - 9 * k, hx - 2 * k, hy - 5.5f * k, d - 0.005f,
           EAR_PINK);
    mg_tri(eye, hx + 2 * k, hy - 5.5f * k, hx + 4.6f * k + f * k, hy - 9 * k, hx + 5 * k, hy - 3.5f * k, d - 0.005f,
           EAR_PINK);
    mg_circle(eye, hx, hy, 7.2f * k, d, FUR);
    /* tabby "M" on the forehead */
    mg_line(eye, hx - 1.5f * k, hy - 6.6f * k, hx - 1.2f * k, hy - 3.6f * k, 1.2f * k, d - 0.005f, FUR_DARK);
    mg_line(eye, hx + 1.5f * k, hy - 6.6f * k, hx + 1.2f * k, hy - 3.6f * k, 1.2f * k, d - 0.005f, FUR_DARK);
    mg_line(eye, hx - 6.6f * k, hy - 0.5f * k, hx - 4.2f * k, hy + 0.2f * k, 1.0f * k, d - 0.005f, FUR_DARK);
    mg_line(eye, hx + 6.6f * k, hy - 0.5f * k, hx + 4.2f * k, hy + 0.2f * k, 1.0f * k, d - 0.005f, FUR_DARK);
    /* white muzzle */
    float mx = hx + f * 1.6f * k;
    ell(eye, mx, hy + 3 * k, 4.4f * k, 3.0f * k, d - 0.01f, FUR_WHITE, 8);
    float ex = hx + f * 1.3f * k, ey = hy - 1.0f * k;
    for (int s = -1; s <= 1; s += 2) {
        float x = ex + (float)s * 2.8f * k;
        if (eyes == 1) {
            mg_line(eye, x - 1.4f * k, ey + 0.4f * k, x + 1.4f * k, ey + 0.4f * k, 1.0f * k, d - 0.015f, MG_INK);
        } else if (eyes == 2) {
            mg_circle(eye, x, ey, 1.9f * k, d - 0.015f, MG_WHITE);
            mg_circle(eye, x, ey, 0.8f * k, d - 0.02f, MG_INK);
        } else {
            mg_circle(eye, x, ey, 1.45f * k, d - 0.015f, RGBA(40, 70, 40, 255));
            mg_circle(eye, x + 0.45f * k, ey - 0.5f * k, 0.5f * k, d - 0.02f, MG_WHITE);
        }
    }
    mg_tri(eye, mx - 1.0f * k, hy + 1.4f * k, mx + 1.0f * k, hy + 1.4f * k, mx, hy + 2.5f * k, d - 0.02f,
           RGBA(230, 120, 140, 255));
}

static void draw_tail(int eye, float x, float y, float k, float d, float f, float swish, bool curl)
{
    float a = -PI_F / 2 - f * 0.7f + swish, px = x, py = y;
    for (int i = 0; i < 4; i++) {
        float L = 5.0f * k;
        float qx = px + cosf(a) * L, qy = py + sinf(a) * L;
        mg_line(eye, px, py, qx, qy, 3.2f * k, d + 0.005f, (i & 1) ? FUR_DARK : FUR);
        px = qx;
        py = qy;
        a += f * (curl ? -0.55f : 0.35f) + swish * 0.3f;
    }
    mg_circle(eye, px, py, 1.6f * k, d + 0.005f, FUR_DARK);
}

static void draw_miso(int eye)
{
    if (S.grace > 0 && fmodf(S.grace, 0.2f) < 0.07f)
        return;
    P3 b = pj(S.x, S.y, 0);
    float k = b.k * 1.08f, d = b.d - 0.04f, f = S.face;
    bool moving = S.movespd > 15 && S.pounce_t <= 0 && !(S.over && S.sat);
    bool napping = S.nap > 0 && !S.over;
    float sh = S.shake > 0 ? sinf(S.shake * 90) * 2 : 0;
    float bx = b.x + sh, by = b.y;

    fell(eye, S.x, S.y, 14, 7, 0, RGBA(30, 20, 30, 70), 10);

    if (S.over && S.sat) {
        /* sitting up, tail curled round the paws */
        ell(eye, bx, by - 11 * k, 8.5f * k, 11 * k, d, FUR, 12);
        mg_line(eye, bx - 6 * k, by - 16 * k, bx - 3 * k, by - 14 * k, 1.4f * k, d - 0.005f, FUR_DARK);
        mg_line(eye, bx - 7 * k, by - 10 * k, bx - 4 * k, by - 8 * k, 1.4f * k, d - 0.005f, FUR_DARK);
        mg_line(eye, bx + 6 * k, by - 16 * k, bx + 3 * k, by - 14 * k, 1.4f * k, d - 0.005f, FUR_DARK);
        ell(eye, bx + f * 1 * k, by - 12 * k, 4.5f * k, 7 * k, d - 0.01f, FUR_WHITE, 10);
        mg_circle(eye, bx - 3 * k, by - 1.5f * k, 2.4f * k, d - 0.02f, FUR_WHITE);
        mg_circle(eye, bx + 3 * k, by - 1.5f * k, 2.4f * k, d - 0.02f, FUR_WHITE);
        /* tail wrapped round the paws, its tip twitching */
        float px = bx - f * 8 * k, py = by - 3 * k;
        for (int i = 1; i <= 5; i++) {
            float u = (float)i / 5;
            float qx = bx - f * cosf(u * PI_F * 0.9f) * 9 * k, qy = by - 3 * k + sinf(u * PI_F * 0.9f) * 4 * k;
            if (i == 5)
                qy -= (1 + sinf(S.t * 6)) * 1.5f * k;
            mg_line(eye, px, py, qx, qy, 3.0f * k, d - 0.03f, (i & 1) ? FUR_DARK : FUR);
            px = qx;
            py = qy;
        }
        float hx = bx + f * 1 * k, hy = by - 25 * k;
        draw_head(eye, hx, hy, k, d - 0.03f, f * 0.3f, S.sit_t > 1.5f ? 1 : 0);
        if (S.sit_t < 1.2f)
            mg_circle(eye, hx + f * 0.5f * k, hy + 4.4f * k, 1.3f * k, d - 0.05f, RGBA(120, 40, 60, 255));
        return;
    }

    if (napping && !moving && S.pounce_t <= 0) {
        /* curled up in a ball */
        ell(eye, bx, by - 7 * k, 13 * k, 8.5f * k, d, FUR, 14);
        for (int i = -1; i <= 1; i++)
            mg_line(eye, bx + i * 5 * k, by - 15 * k, bx + i * 5 * k - f * 1.5f * k, by - 10 * k, 1.6f * k,
                    d - 0.005f, FUR_DARK);
        /* tail wrapped round the front */
        float px = bx - f * 12 * k, py = by - 4 * k;
        for (int i = 1; i <= 4; i++) {
            float u = (float)i / 4;
            float qx = bx - f * 12 * k + f * 22 * k * u, qy = by - 4 * k + sinf(u * PI_F) * 4 * k;
            mg_line(eye, px, py, qx, qy, 3.4f * k, d - 0.01f, (i & 1) ? FUR_DARK : FUR);
            px = qx;
            py = qy;
        }
        draw_head(eye, bx + f * 8 * k, by - 9 * k, k * 0.92f, d - 0.02f, f, 1);
        for (int i = 0; i < 3; i++) {
            float u = fmodf(S.t * 0.7f + i * 0.33f, 1.0f);
            mg_text(eye, "z", bx + f * 12 * k + u * 14, by - 22 * k - u * 22, 0.35f + 0.2f * u, d - 0.1f - u * 0.15f,
                    rgba_alpha(RGBA(200, 220, 255, 255), 1 - u));
        }
        return;
    }

    float bob = moving ? fabsf(sinf(S.walk)) * 1.6f * k : 0, lift = 0, stretch = 1;
    if (S.pounce_t > 0) {
        float u = 1 - S.pounce_t / POUNCE_TIME;
        lift = sinf(u * PI_F) * 8 * k;
        stretch = 1.25f;
    }
    float cy = by - 10 * k - bob - lift, cx = bx;
    float rx = 12.5f * k * stretch, ry = 7 * k / (stretch > 1 ? 1.1f : 1.0f);
    float swish = sinf(S.t * (moving ? 5.0f : 2.2f)) * 0.45f;
    if (S.frozen > 0)
        swish = 0.9f * f;   /* bottle-brush tail, straight up */

    /* far legs, tail, body, near legs */
    float sw = moving ? sinf(S.walk) * 3 * k : 0;
    float footy = by - lift * 0.6f;
    float reach = S.pounce_t > 0 ? 5 * k : 0;
    mg_line(eye, cx - f * 7 * k, cy + 3 * k, cx - f * (7 * k + reach) - sw, footy, 2.8f * k, d + 0.01f, FUR_DARK);
    mg_line(eye, cx + f * 7 * k, cy + 3 * k, cx + f * (7 * k + reach) + sw, footy, 2.8f * k, d + 0.01f, FUR_DARK);
    draw_tail(eye, cx - f * rx * 0.85f, cy - 2 * k, k, d, f, swish, false);
    ell(eye, cx, cy, rx, ry, d, FUR, 12);
    for (int i = -1; i <= 1; i++) {
        float sx = cx + (float)i * 4.5f * k - f * 1 * k;
        mg_line(eye, sx, cy - ry * 0.95f, sx - f * 1.5f * k, cy - ry * 0.25f, 1.7f * k, d - 0.005f, FUR_DARK);
    }
    ell(eye, cx + f * 4 * k, cy + 3 * k, 6 * k, 3.2f * k, d - 0.01f, FUR_WHITE, 8);
    mg_line(eye, cx - f * 9 * k, cy + 3 * k, cx - f * (9 * k + reach) + sw, footy, 3.0f * k, d - 0.01f, FUR);
    mg_line(eye, cx + f * 5 * k, cy + 3 * k, cx + f * (5 * k + reach) - sw, footy, 3.0f * k, d - 0.01f, FUR);
    mg_circle(eye, cx - f * (9 * k + reach) + sw, footy, 1.7f * k, d - 0.015f, FUR_WHITE);
    mg_circle(eye, cx + f * (5 * k + reach) - sw, footy, 1.7f * k, d - 0.015f, FUR_WHITE);

    float hx = cx + f * rx * 0.95f, hy = cy - 7 * k + (S.pounce_t > 0 ? 3 * k : 0);
    draw_head(eye, hx, hy, k, d - 0.02f, f, S.frozen > 0 ? 2 : 0);

    if (S.frozen > 0) {
        mg_text_centered(eye, "!", hx + 1, hy - 29 * k, 0.8f, d - 0.25f, RGBA(60, 40, 20, 255));
        mg_text_centered(eye, "!", hx, hy - 30 * k, 0.8f, d - 0.25f, MG_GOLD);
    } else if (S.expose > 0) {
        mg_text_centered(eye, "?", hx, hy - 26 * k, 0.6f, d - 0.2f, rgba_alpha(MG_WHITE, S.expose / SPOT_DELAY));
    }
    if (S.nap > 0)
        mg_text(eye, "z", hx + 8 * k, hy - 18 * k - fmodf(S.t * 10, 6), 0.4f, d - 0.12f, RGBA(200, 220, 255, 220));
}

/* ---- top screen ------------------------------------------------------------------------------ */

enum { OBJ_DOT, OBJ_MISO, OBJ_SOFA, OBJ_PLANT };

static void draw_top(int eye)
{
    draw_room(eye);
    draw_bookshelf(eye);
    draw_beam_spots(eye);

    /* painter's order by depth into the room */
    int kind[MAX_DOTS + 3], idx[MAX_DOTS + 3], n = 0;
    float key[MAX_DOTS + 3];
    kind[n] = OBJ_SOFA, idx[n] = 0, key[n++] = 70;
    kind[n] = OBJ_PLANT, idx[n] = 0, key[n++] = 140;
    kind[n] = OBJ_MISO, idx[n] = 0, key[n++] = S.y;
    for (int i = 0; i < MAX_DOTS; i++)
        if (S.dots[i].on)
            kind[n] = OBJ_DOT, idx[n] = i, key[n++] = S.dots[i].y;
    for (int i = 1; i < n; i++)
        for (int j = i; j > 0 && key[j - 1] > key[j]; j--) {
            float tk = key[j]; key[j] = key[j - 1]; key[j - 1] = tk;
            int ti = kind[j]; kind[j] = kind[j - 1]; kind[j - 1] = ti;
            ti = idx[j]; idx[j] = idx[j - 1]; idx[j - 1] = ti;
        }
    for (int i = 0; i < n; i++) {
        switch (kind[i]) {
        case OBJ_SOFA: draw_sofa(eye); break;
        case OBJ_PLANT: draw_plant(eye); break;
        case OBJ_MISO: draw_miso(eye); break;
        default: draw_dot(eye, &S.dots[idx[i]]); break;
        }
    }

    draw_beam_cones(eye);

    /* sparks and score pop-ups */
    for (int i = 0; i < MAX_PARTS; i++) {
        const Part *p = &S.parts[i];
        if (p->life <= 0)
            continue;
        float a = p->life / p->max;
        mg_rect(eye, p->x - p->size / 2, p->y - p->size / 2, p->size, p->size, p->d, rgba_alpha(p->c, a));
    }
    for (int i = 0; i < MAX_POPS; i++) {
        const Pop *p = &S.pops[i];
        if (p->t <= 0)
            continue;
        float a = clampf((1.0f - p->t) * 3, 0, 1), y = p->y - p->t * 18, d = p->d - p->t * 0.1f;
        mg_text_centered(eye, p->text, p->x + 1, y + 1, 0.5f, d, rgba_alpha(RGBA(20, 14, 30, 255), a * 0.8f));
        mg_text_centered(eye, p->text, p->x, y, 0.5f, d, rgba_alpha(p->c, a));
    }

    /* nap: the room dims to a cool blue */
    if (S.nap > 0 && !S.over) {
        float a = clampf(fminf(S.nap, NAP_TIME - S.nap) * 2, 0, 1);
        gfx_rect(0, 0, TOP_W, TOP_H, rgba_alpha(RGBA(30, 40, 90, 255), 0.25f * a));
        char buf[24];
        snprintf(buf, sizeof(buf), "Nap  %.1f", S.nap);
        mg_text_centered(eye, buf, 200, 214, 0.5f, -0.15f, rgba_alpha(RGBA(200, 215, 255, 255), a));
    }

    /* glitch tear when a phase starts */
    if (S.banner > 1.8f && S.t > 1) {
        u32 hs = (u32)(S.t * 20);
        for (int i = 0; i < 6; i++) {
            float y = hashf(hs * 7 + i) * TOP_H, x = hashf(hs * 13 + i) * 200;
            mg_rect(eye, x, y, 120 + hashf(hs + i * 3) * 180, 2 + 4 * hashf(hs * 3 + i), -0.1f,
                    (i & 1) ? RGBA(90, 240, 255, 90) : RGBA(235, 90, 255, 90));
        }
    }

    /* HUD: time and combo, floating just in front of the screen */
    if (!S.over) {
        char buf[32];
        float left = fmaxf(0, RUN_TIME - S.t);
        snprintf(buf, sizeof(buf), "%d:%02d", (int)left / 60, (int)left % 60);
        mg_rect(eye, 6, 5, 46, 18, -0.12f, RGBA(20, 16, 34, 170));
        mg_text_centered(eye, buf, 29, 6, 0.5f, -0.14f, left <= 5 ? RGBA(255, 140, 120, 255) : MG_WHITE);
        if (S.combo > 0) {
            snprintf(buf, sizeof(buf), "x%d  combo %d", S.mult, S.combo);
            float w = gfx_text_width(buf, 0.45f) + 12;
            mg_rect(eye, 394 - w, 5, w, 18, -0.12f, RGBA(20, 16, 34, 170));
            mg_rect(eye, 394 - w, 21, w * clampf(S.combo_t / COMBO_WINDOW, 0, 1), 2, -0.13f, MG_GOLD);
            mg_text(eye, buf, 400 - w, 7, 0.45f, -0.14f, S.mult > 1 ? MG_GOLD : MG_WHITE);
        }
    }
    if (S.banner > 0 && !S.over) {
        float a = clampf(S.banner * 2, 0, 1);
        mg_rect(eye, 90, 66, 220, 24, -0.2f, rgba_alpha(RGBA(20, 16, 34, 255), 0.7f * a));
        mg_text_centered(eye, PHASE_NAME[S.phase], 200, 69, 0.52f, -0.25f, rgba_alpha(MG_GOLD, a));
    }

    /* the end: "Meow." */
    if (S.over && S.sat) {
        float u = clampf(S.sit_t / 0.35f, 0, 1);
        float sc = 0.6f + 1.0f * u * (1.15f - 0.15f * u);
        P3 b = pj(S.x, S.y, 0);
        float hx = b.x + S.face * 1, hy = b.y - 34 * b.k;
        float bx = 268, by = 78;
        float w = gfx_text_width("Meow.", sc) + 26, h = gfx_line_height(sc) + 10;
        ell(eye, bx, by + h / 2 - 4, w / 2 + 6, h / 2 + 4, -0.45f, RGBA(255, 255, 255, 240), 20);
        mg_tri(eye, bx - 22, by + h - 6, bx - 6, by + h - 2, hx + 8, hy - 2, -0.42f, RGBA(255, 255, 255, 240));
        mg_text_centered(eye, "Meow.", bx, by, sc, -0.5f, MG_INK);
    }
}

/* ---- bottom screen ------------------------------------------------------------------------- */

#define MAP_X 16.0f
#define MAP_Y 30.0f
#define MAP_S 0.9f

static void map_pt(float x, float y, float *mx, float *my)
{
    *mx = MAP_X + x * MAP_S;
    *my = MAP_Y + y * MAP_S;
}

static void draw_bottom(void)
{
    char buf[64];
    gfx_text("Miso's Hunt", 10, 4, 0.5f, MG_GOLD);
    float left = fmaxf(0, RUN_TIME - S.t);
    snprintf(buf, sizeof(buf), "Phase %d/3   %d:%02d", S.phase + 1, (int)left / 60, (int)left % 60);
    gfx_text(buf, 310 - gfx_text_width(buf, 0.45f), 5, 0.45f, MG_WHITE);
    /* run progress with the phase marks */
    gfx_rect(MAP_X, 23, RW * MAP_S, 3, RGBA(255, 255, 255, 40));
    gfx_rect(MAP_X, 23, RW * MAP_S * clampf(S.t / RUN_TIME, 0, 1), 3, MG_GOLD);
    gfx_rect(MAP_X + RW * MAP_S / 3, 21, 1, 7, MG_WHITE);
    gfx_rect(MAP_X + RW * MAP_S * 2 / 3, 21, 1, 7, MG_WHITE);

    /* the map */
    gfx_rect(MAP_X - 3, MAP_Y - 3, RW * MAP_S + 6, RD * MAP_S + 6, RGBA(214, 196, 178, 255));
    gfx_rect(MAP_X, MAP_Y, RW * MAP_S, RD * MAP_S, RGBA(140, 100, 74, 255));
    {
        float cx, cy;
        map_pt(162, 94, &cx, &cy);
        float px = cx + 92 * MAP_S, py = cy;
        for (int i = 1; i <= 16; i++) {
            float a = (float)i * TAU_F / 16;
            float qx = cx + cosf(a) * 92 * MAP_S, qy = cy + sinf(a) * 42 * MAP_S;
            gfx_triangle(cx, cy, px, py, qx, qy, RGBA(150, 64, 72, 255));
            px = qx;
            py = qy;
        }
    }
    static const u32 FURN[] = {RGBA(90, 60, 44, 255), RGBA(70, 108, 118, 255), RGBA(80, 150, 85, 255)};
    for (unsigned i = 0; i < ARRAY_LEN(OBST); i++) {
        float x0, y0, x1, y1;
        map_pt(OBST[i].x0, OBST[i].y0, &x0, &y0);
        map_pt(OBST[i].x1, OBST[i].y1, &x1, &y1);
        gfx_rect(x0, y0, x1 - x0, y1 - y0, FURN[i]);
    }
    {   /* the window on the back wall */
        float x0, y0, x1, y1;
        map_pt(186, 0, &x0, &y0);
        map_pt(282, 0, &x1, &y1);
        gfx_rect(x0, y0 - 3, x1 - x0, 3, RGBA(170, 210, 240, 255));
    }
    for (int i = 0; i < S.nbeams; i++) {
        float a = beam_alpha(i);
        if (a <= 0)
            continue;
        float x, y, mx, my;
        beam_xy(i, &x, &y);
        map_pt(x, y, &mx, &my);
        u32 c = S.beams[i].lock > 0 ? RGBA(255, 220, 120, 255) : S.nap > 0 ? RGBA(160, 170, 210, 255)
                                                                            : RGBA(255, 248, 220, 255);
        gfx_circle(mx, my, BD[i].r * MAP_S, rgba_alpha(c, 0.35f * a));
        gfx_circle(mx, my, BD[i].r * MAP_S * 0.5f, rgba_alpha(c, 0.25f * a));
    }
    for (int i = 0; i < MAX_DOTS; i++) {
        const Dot *d = &S.dots[i];
        if (!d->on || S.over)
            continue;
        float mx, my;
        map_pt(d->x, d->y, &mx, &my);
        float left_t = d->life - d->age;
        if (d->emerge >= 1 && left_t < 1.6f && fmodf(S.t, 0.2f) < 0.08f)
            continue;
        float s = d->emerge < 1 ? 3 : 5;
        gfx_rect(mx - s / 2, my - s / 2, s, s, dot_color(d->kind));
    }
    {   /* Miso: a little cat head */
        float mx, my;
        map_pt(S.x, S.y, &mx, &my);
        u32 c = S.frozen > 0 ? MG_GOLD : RGBA(235, 235, 245, 255);
        gfx_triangle(mx - 6, my - 1, mx - 5, my - 9, mx - 1, my - 5, c);
        gfx_triangle(mx + 1, my - 5, mx + 5, my - 9, mx + 6, my - 1, c);
        gfx_circle(mx, my, 5.5f, c);
        gfx_circle(mx - 2, my - 0.5f, 1, MG_INK);
        gfx_circle(mx + 2, my - 0.5f, 1, MG_INK);
        if (S.pounce_t > 0)
            gfx_circle(mx, my, CATCH_R * MAP_S, RGBA(255, 255, 255, 50));
    }

    /* stats */
    float y = 180;
    snprintf(buf, sizeof(buf), "Caught %d   Points %d", S.caught, S.points);
    gfx_text(buf, 12, y, 0.45f, MG_WHITE);
    snprintf(buf, sizeof(buf), "Combo %d (x%d)   Best %d", S.combo, S.mult, S.best_combo);
    gfx_text(buf, 12, y + 18, 0.45f, S.mult > 1 ? MG_GOLD : MG_WHITE);
    if (S.combo > 0)
        gfx_rect(12, y + 34, 140 * clampf(S.combo_t / COMBO_WINDOW, 0, 1), 2, MG_GOLD);
    if (S.nap > 0)
        snprintf(buf, sizeof(buf), "Napping %.1f s   Spotted %d", S.nap, S.spotted);
    else
        snprintf(buf, sizeof(buf), "Spotted %d", S.spotted);
    gfx_text(buf, 12, y + 38, 0.45f, S.frozen > 0 ? MG_GOLD : S.nap > 0 ? RGBA(180, 200, 255, 255)
                                                                          : RGBA(200, 200, 215, 255));
}

/* The nap is wasted once time is up (Miso is sitting down to say her
 * piece) or while she is already asleep. */
static bool can_cheat(void) { return !S.over && S.nap <= 0; }

/* ---- results ---------------------------------------------------------------------------------- */

static int score(void)
{
    float s = 60.0f * fminf(1, (float)S.points / PTS_FULL) + 20.0f * fminf(1, (float)S.best_combo / COMBO_FULL) +
              20.0f * fmaxf(0, 1 - (float)S.spotted / SPOT_ZERO);
    int v = (int)(s + 0.5f);
    return v < 0 ? 0 : v > 100 ? 100 : v;
}

static const char *verdict(void)
{
    static char buf[96];
    int sc = score();
    const char *tail = sc >= 90 ? "Purr-fect." : sc >= 70 ? "Sharp claws." : sc >= 45 ? "A decent haul."
                                                                                      : "The leak got away.";
    snprintf(buf, sizeof(buf), "%d caught, best combo %d, spotted %d. %s", S.caught, S.best_combo, S.spotted, tail);
    return buf;
}

/* ---- bot: chase the safest nearby dot, steer round the beams --------------------------------- */

static void bot(Input *in, float t)
{
    static bool napped;
    if (t < 0.05f)
        napped = false;
    if (S.over)
        return;
    bool napping = S.nap > 0;

    /* pick a target: near, not inside a beam, not about to vanish */
    int best = -1;
    float best_cost = 1e9f, tx = 160, ty = 100;
    for (int i = 0; i < MAX_DOTS; i++) {
        const Dot *d = &S.dots[i];
        if (!d->on)
            continue;
        float x = d->emerge < 1 ? d->wx + d->nx * 20 : d->x, y = d->emerge < 1 ? d->wy + d->ny * 20 : d->y;
        float dd = sqrtf(dist2(x, y, S.x, S.y));
        float cost = dd;
        if (d->emerge >= 1 && d->life - d->age < dd / MISO_SPEED + 0.3f)
            cost += 400;
        if (d->kind == DOT_SHY)
            cost += 25;
        if (!napping)
            for (int b = 0; b < S.nbeams; b++) {
                float bx, by;
                beam_xy(b, &bx, &by);
                if (dist2(bx, by, x, y) < (BD[b].r + 12) * (BD[b].r + 12))
                    cost += 160;
            }
        if (cost < best_cost) {
            best_cost = cost;
            best = i;
            tx = x;
            ty = y;
        }
    }
    float dx = tx - S.x, dy = ty - S.y, dl = sqrtf(dx * dx + dy * dy) + 0.001f;
    float vx = dx / dl, vy = dy / dl;
    if (best < 0 && dl < 20)
        vx = vy = 0;

    /* steer away from beams, now and a moment ahead */
    float ax = 0, ay = 0, danger = 0;
    if (!napping && S.grace <= 0.3f) {
        for (int b = 0; b < S.nbeams; b++) {
            if (S.beams[b].fade < 0.6f)
                continue;
            for (int s = 0; s < 2; s++) {
                float bx, by;
                beam_xy_at(b, S.beams[b].ph + PH[S.phase].bspeed * 0.45f * (float)s, &bx, &by);
                float ex = S.x - bx, ey = S.y - by, el = sqrtf(ex * ex + ey * ey) + 0.001f;
                float zone = BD[b].r + 26;
                if (el < zone) {
                    float w = (zone - el) / zone * 3.0f;
                    ax += ex / el * w;
                    ay += ey / el * w;
                    danger = fmaxf(danger, w);
                }
            }
        }
    }
    vx += ax;
    vy += ay;
    float vl = sqrtf(vx * vx + vy * vy);
    if (vl > 0.001f) {
        vx /= vl;
        vy /= vl;
    }

    /* pounce when the target is in reach and the way is clear */
    if (best >= 0 && S.dots[best].emerge >= 1 && dl < 52 && S.pounce_cd <= 0 && S.frozen <= 0 &&
        danger < 1.2f) {
        vx = dx / dl;
        vy = dy / dl;
        in->down |= KEY_A_;
    }
    in->cx = vx;
    in->cy = -vy;

    /* nap once, when a beam is closing in during the busy middle */
    if (!napped && t > 38 && (danger > 0.8f || t > 58)) {
        in->down |= KEY_L_;
        napped = true;
    }
}

const MiniGame MG_MISO = {
    .id = "miso",
    .title = "Miso's Hunt",
    .rules = "Glitch dots are leaking out of the walls of\n"
             "Aron's flat. Steer Miso to them and pounce!\n"
             "Catch dots back to back for a combo multiplier.\n"
             "The angels' light beams are watching: if one\n"
             "spots Miso she freezes and the combo resets.\n"
             "75 seconds, three phases. Ignored dots fade.",
    .controls = "D-pad / Circle Pad: move Miso\n"
                "A: pounce (a quick dash that catches\n"
                "     every dot within reach)\n"
                "Stay out of the soft light beams\n"
                "START: pause",
    .cheat = "Nap: beams stop for 5 s, dots slow down",
    .music = "miso",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .verdict = verdict,
    .bot = bot,
    .can_cheat = can_cheat,
};
