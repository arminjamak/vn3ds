/* Miso's Hunt: the leak is spitting cat food out of the walls of Aron's
 * flat, and Miso wants all of it. Pouches, boxes and the odd golden tin
 * shimmer out of the walls and land around the room, while Commander
 * Seraphiel's angels sweep the floor with soft, slow beams of light.
 *
 * The flat is seen from a high three-quarter angle. Game logic works in
 * room units on the floor: X 0..320 (left to right), Y 0..160 (back wall to
 * the front). pj() projects a room point (and a height above the floor) to
 * the screen and to a stereo depth: the back of the room sits behind the
 * screen, the front of the floor slightly in front of it.
 *
 * Controls: D-pad / Circle Pad walk (walking over a package grabs it), A or
 * B leaps a long way in the steered (or facing) direction, grabbing
 * everything on the way; furniture stops a leap. Each of the four leap
 * directions has its own animation: side-on to the left and right, from
 * behind going up the room (away from the camera), from the front coming
 * down the room (towards the camera, popping out of the screen).
 * The cheat, "Nap", stops every beam for 5 seconds and stops the packages'
 * clocks.
 *
 * Run: 75 seconds in three phases of 25 s. Each phase drops packages faster,
 * adds a beam, and every beam sweeps faster.
 *
 * Score (0..100):
 *     60 * min(1, points / 250)     a package is worth 1 (pouch), 2 (box) or
 *                                   3 (golden tin) times the combo multiplier
 *                                   (x1..x4); each extra package grabbed in
 *                                   the same leap adds +1 x multiplier
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

#define MISO_R 9.0f          /* Miso's footprint against furniture */
#define MISO_SPEED 112.0f
#define PICK_RX 17.0f        /* walking over a package: an ellipse round Miso */
#define PICK_RY 12.0f
#define LEAP_RX 21.0f        /* a leap sweeps a wider path */
#define LEAP_RY 15.0f
#define LEAP_DIST 108.0f
#define LEAP_CROUCH 0.07f    /* squash before take-off */
#define LEAP_AIR 0.28f
#define LEAP_LAND 0.14f      /* squash on landing (Miso stays put) */
#define LEAP_COOL 0.6f       /* from one take-off to the next */
#define LEAP_H 15.0f         /* height of the arc */
#define COMBO_WINDOW 3.0f
#define SPOT_DELAY 0.22f     /* seconds inside a beam before it spots Miso */
#define SPOT_FREEZE 1.4f
#define SPOT_GRACE 1.6f
#define NAP_TIME 5.0f
#define SHIMMER_TIME 0.5f    /* a package shimmering in the wall */
#define FLY_TIME 0.6f        /* ... then tossed out onto the floor */
#define TIN_LIFE 4.2f        /* golden tins don't wait */

#define PTS_FULL 250.0f
#define COMBO_FULL 15.0f
#define SPOT_ZERO 5.0f

#define MAX_PACKS 10
#define MAX_BEAMS 3
#define MAX_PARTS 48
#define MAX_POPS 6

#define PI_F 3.14159265f
#define TAU_F 6.2831853f

enum { PK_POUCH, PK_BOX, PK_TIN };
static const int PK_VALUE[3] = {1, 2, 3};

enum { LD_RIGHT, LD_LEFT, LD_UP, LD_DOWN };
enum { LS_CROUCH, LS_AIR, LS_LAND };

typedef struct {
    float interval, life;
    int maxpacks, beams;
    float bspeed, box, tin, hard;
} PhaseDef;

static const PhaseDef PH[3] = {
    {1.7f, 8.0f, 4, 1, 0.40f, 0.25f, 0.10f, 0.15f},
    {1.25f, 7.0f, 6, 2, 0.52f, 0.30f, 0.16f, 0.20f},
    {0.95f, 6.5f, 7, 3, 0.64f, 0.30f, 0.22f, 0.25f},
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

/* Furniture Miso cannot enter (room units). */
typedef struct {
    float x0, y0, x1, y1;
} Box;

static const Box OBST[] = {
    {14, 0, 100, 20},    /* bookshelf */
    {0, 62, 48, 142},    /* sofa */
    {278, 122, 320, 160} /* plant */
};

/* Hard-to-reach spots: tucked against furniture and in the far corners. */
static const float HARD[][2] = {
    {28, 33},    /* between the bookshelf and the sofa */
    {116, 15},   /* against the bookshelf */
    {304, 15},   /* the back right corner */
    {272, 106},  /* tucked beside the plant */
    {262, 151},  /* in front of the plant */
    {30, 152},   /* in front of the sofa, by the wall */
    {64, 98},    /* right up against the sofa */
};
#define NHARD ((int)ARRAY_LEN(HARD))

/* ---- state ------------------------------------------------------------------- */

typedef struct {
    bool on, landed, hard;
    int kind;
    float x, y;            /* where it lands */
    float wx, wy, wh;      /* the wall point it shimmers out of, and how high */
    float t;               /* since it appeared */
    float age, life;       /* on the floor */
    u32 seed;
} Pack;

typedef struct {
    float ph;              /* path parameter */
    float fade;            /* 0..1 fading in */
    float lock;            /* > 0: flashing after spotting Miso */
    float warn_cd;
    bool near;
} Beam;

typedef struct {
    float x, y, vx, vy, d, life, max, size, g;
    bool round;
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
    float frozen, grace, expose;
    float step_t;
    float nap;

    /* the leap */
    bool leaping, bonk;
    int ldir, lstage, lhits;
    float lt, lair, land_at;   /* since take-off was pressed; in the air; when it landed */
    float lu, lh;              /* air progress 0..1, height above the floor */
    float ldx, ldy, lsx, lsy;
    float leap_cd;

    /* scoring */
    int got, leap_got, combo, best_combo, mult, points, spotted, leaps, best_multi;
    float combo_t;

    Pack packs[MAX_PACKS];
    float spawn_t;
    int spawned, vanished;
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

static float smooth01(float u)
{
    u = clampf(u, 0, 1);
    return u * u * (3 - 2 * u);
}

static void sfx(const char *name)
{
    mg_sfx(name);
    S.quiet = 0;
}

static void sfx_pitch(const char *name, float rate)
{
    mg_sfx_pitch(name, rate);
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

static void keep_miso(float *x, float *y) { keep_out(x, y, MISO_R, 12, RW - 12, 10, RD - 6); }

/* Inside furniture (grown by r) or outside the room Miso can walk in. */
static bool blocked(float x, float y, float r)
{
    if (x < 12 || x > RW - 12 || y < 10 || y > RD - 6)
        return true;
    for (unsigned i = 0; i < ARRAY_LEN(OBST); i++)
        if (x > OBST[i].x0 - r && x < OBST[i].x1 + r && y > OBST[i].y0 - r && y < OBST[i].y1 + r)
            return true;
    return false;
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

static Part *new_part(void)
{
    for (int i = 0; i < MAX_PARTS; i++)
        if (S.parts[i].life <= 0)
            return &S.parts[i];
    return NULL;
}

static void burst(float sx, float sy, float d, int n, float speed, u32 c)
{
    for (int k = 0; k < n; k++) {
        Part *p = new_part();
        if (!p)
            return;
        float a = mg_randf() * TAU_F, v = speed * (0.4f + 0.6f * mg_randf());
        p->x = sx;
        p->y = sy;
        p->vx = cosf(a) * v;
        p->vy = sinf(a) * v - speed * 0.4f;
        p->d = d - 0.05f * mg_randf();
        p->life = p->max = 0.35f + 0.35f * mg_randf();
        p->size = 1.5f + 2.0f * mg_randf();
        p->g = 160;
        p->round = false;
        p->c = (mg_rand() & 1) ? c : RGBA(255, 255, 255, 255);
    }
}

/* Little puffs of dust kicked up along the floor at a take-off or landing. */
static void dust(float X, float Y, int n, float spread)
{
    P3 g = pj(X, Y, 0);
    for (int k = 0; k < n; k++) {
        Part *p = new_part();
        if (!p)
            return;
        float side = (k & 1) ? 1.0f : -1.0f, v = spread * (0.5f + 0.5f * mg_randf());
        p->x = g.x + side * (3 + 4 * mg_randf());
        p->y = g.y - 1 - 2 * mg_randf();
        p->vx = side * v;
        p->vy = -8 - 10 * mg_randf();
        p->d = g.d - 0.03f;
        p->life = p->max = 0.3f + 0.2f * mg_randf();
        p->size = 2.2f + 1.6f * mg_randf();
        p->g = 0;
        p->round = true;
        p->c = RGBA(236, 222, 200, 200);
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

/* A pouch comes in three flavours (colours); boxes are card, tins gold. */
static u32 pack_color(const Pack *p)
{
    static const u32 POUCH[3] = {RGBA(150, 92, 200, 255), RGBA(54, 160, 170, 255), RGBA(224, 96, 140, 255)};
    return p->kind == PK_TIN ? RGBA(240, 196, 70, 255) : p->kind == PK_BOX ? RGBA(206, 160, 104, 255)
                                                                           : POUCH[p->seed % 3];
}

/* ---- packages ------------------------------------------------------------------ */

static int pack_count(void)
{
    int n = 0;
    for (int i = 0; i < MAX_PACKS; i++)
        n += S.packs[i].on;
    return n;
}

static bool spot_free(float x, float y, float near_miso)
{
    if (dist2(x, y, S.x, S.y) < near_miso * near_miso)
        return false;
    for (int i = 0; i < MAX_PACKS; i++)
        if (S.packs[i].on && dist2(x, y, S.packs[i].x, S.packs[i].y) < 26 * 26)
            return false;
    return true;
}

static void spawn_pack(void)
{
    Pack *p = NULL;
    for (int i = 0; i < MAX_PACKS; i++)
        if (!S.packs[i].on) {
            p = &S.packs[i];
            break;
        }
    if (!p)
        return;
    memset(p, 0, sizeof(*p));
    const PhaseDef *ph = &PH[S.phase];
    float r = mg_randf();
    p->kind = r < ph->tin ? PK_TIN : r < ph->tin + ph->box ? PK_BOX : PK_POUCH;
    p->seed = mg_rand();

    /* where it lands: tins (and some pouches) in a hard spot far from Miso */
    bool placed = false;
    if (p->kind == PK_TIN || mg_randf() < ph->hard) {
        int start = mg_randi(0, NHARD - 1);
        for (int k = 0; k < NHARD && !placed; k++) {
            const float *h = HARD[(start + k) % NHARD];
            if (spot_free(h[0], h[1], 90)) {
                p->x = h[0] + (mg_randf() - 0.5f) * 4;
                p->y = h[1] + (mg_randf() - 0.5f) * 3;
                placed = p->hard = true;
            }
        }
    }
    for (int tries = 0; tries < 24 && !placed; tries++) {
        float x = 24 + mg_randf() * 272, y = 18 + mg_randf() * 130;
        if (!blocked(x, y, 4) && spot_free(x, y, 46)) {
            p->x = x;
            p->y = y;
            placed = true;
        }
    }
    if (!placed) {
        p->on = false;
        return;
    }
    if (p->kind == PK_TIN && !p->hard)
        p->kind = PK_BOX;

    /* the nearest stretch of wall the leak can push it through */
    float bx = clampf(p->x, 108, 312), by = 0;
    float lx = 0, ly = clampf(p->y, 24, 56);
    float rx = RW, ry = clampf(p->y, 10, 116);
    float db = dist2(bx, by, p->x, p->y), dl = dist2(lx, ly, p->x, p->y), dr = dist2(rx, ry, p->x, p->y);
    if (db <= dl && db <= dr)
        p->wx = bx, p->wy = by;
    else if (dl <= dr)
        p->wx = lx, p->wy = ly;
    else
        p->wx = rx, p->wy = ry;
    p->wh = 16 + 10 * mg_randf();
    p->life = p->kind == PK_TIN ? TIN_LIFE : ph->life * (0.9f + 0.25f * mg_randf());
    p->on = true;
    S.spawned++;
    if (p->kind == PK_TIN)
        sfx("miso_rare_appear");
    else
        sfx("miso_package_appear");
}

/* Where a package is right now: on the floor, or tumbling out of the wall. */
static void pack_pos(const Pack *p, float *x, float *y, float *h)
{
    if (p->landed || p->t >= SHIMMER_TIME + FLY_TIME) {
        *x = p->x, *y = p->y, *h = 0;
        return;
    }
    float u = clampf((p->t - SHIMMER_TIME) / FLY_TIME, 0, 1);
    float dist = sqrtf(dist2(p->wx, p->wy, p->x, p->y));
    *x = lerpf(p->wx, p->x, u);
    *y = lerpf(p->wy, p->y, u);
    *h = lerpf(p->wh, 0, u) + sinf(u * PI_F) * (10 + dist * 0.12f);
}

static void collect(Pack *p, bool leap)
{
    P3 g = pj(p->x, p->y, 10);
    int old = S.mult;
    S.got++;
    S.combo++;
    S.combo_t = COMBO_WINDOW;
    if (S.combo > S.best_combo)
        S.best_combo = S.combo;
    S.mult = S.combo / 3 + 1;
    if (S.mult > 4)
        S.mult = 4;
    int pts = PK_VALUE[p->kind] * S.mult;
    S.points += pts;
    if (leap) {
        S.leap_got++;
        S.lhits++;
    }
    p->on = false;
    burst(g.x, g.y, g.d - 0.05f, p->kind == PK_TIN ? 14 : 9, 90, pack_color(p));
    char buf[16];
    snprintf(buf, sizeof(buf), "+%d", pts);
    popup(g.x, g.y - 8, g.d - 0.15f, buf, S.mult > 1 || p->kind == PK_TIN ? MG_GOLD : MG_WHITE);
    if (S.mult > old) {
        snprintf(buf, sizeof(buf), "Combo x%d!", S.mult);
        popup(g.x, g.y - 24, g.d - 0.25f, buf, RGBA(255, 160, 220, 255));
        sfx("miso_combo");
    } else if (p->kind == PK_TIN) {
        sfx("miso_pickup_rare");
    } else {
        /* a pouch sounds lighter than a box; a combo climbs in pitch */
        sfx_pitch("miso_pickup", (p->kind == PK_BOX ? 0.85f : 1.05f) + 0.04f * (float)(S.combo % 3));
    }
}

static void update_packs(float dt, bool napping)
{
    for (int i = 0; i < MAX_PACKS; i++) {
        Pack *p = &S.packs[i];
        if (!p->on)
            continue;
        p->t += dt;
        if (!p->landed) {
            if (p->t >= SHIMMER_TIME + FLY_TIME) {
                p->landed = true;
                dust(p->x, p->y, 2, 14);
                if (S.quiet > 0.15f)
                    sfx("miso_package_land");
            }
            continue;
        }
        if (!napping)
            p->age += dt;
        if (p->age >= p->life) {
            /* the leak takes it back: it breaks up into glitch pixels */
            P3 g = pj(p->x, p->y, 6);
            burst(g.x, g.y, g.d, 4, 40, RGBA(90, 240, 255, 255));
            burst(g.x, g.y, g.d, 4, 40, RGBA(235, 90, 255, 255));
            p->on = false;
            S.vanished++;
            sfx("miso_package_vanish");
        }
    }
}

/* Grab every landed package within reach (an ellipse: Miso is long). */
static void pickups(float rx, float ry, bool leap)
{
    for (int i = 0; i < MAX_PACKS; i++) {
        Pack *p = &S.packs[i];
        if (!p->on || !p->landed)
            continue;
        float dx = (p->x - S.x) / rx, dy = (p->y - S.y) / ry;
        if (dx * dx + dy * dy < 1)
            collect(p, leap);
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
    S.leaping = false;   /* caught mid-air: she drops where she is */
    S.lh = 0;
    S.beams[beam].lock = 1.0f;
    S.shake = 0.35f;
    P3 p = pj(S.x, S.y, 30);
    popup(p.x, p.y - 26, p.d - 0.3f, "Spotted!", MG_GOLD);
    sfx("miso_spotted");
}

static void start_leap(float dx, float dy)
{
    S.leaping = true;
    S.bonk = false;
    S.lstage = LS_CROUCH;
    S.lt = S.lair = S.lu = S.lh = 0;
    S.ldx = dx;
    S.ldy = dy;
    S.lhits = 0;
    S.leap_cd = LEAP_COOL;
    S.leaps++;
    if (fabsf(dx) >= fabsf(dy)) {
        S.ldir = dx > 0 ? LD_RIGHT : LD_LEFT;
        S.face = dx > 0 ? 1.0f : -1.0f;
        sfx("miso_leap_side");
    } else {
        S.ldir = dy < 0 ? LD_UP : LD_DOWN;
        sfx(dy < 0 ? "miso_leap_up" : "miso_leap_down");
    }
}

static void land(bool bonk)
{
    S.lstage = LS_LAND;
    S.land_at = S.lt;
    S.bonk = bonk;
    S.lh = 0;
    dust(S.x, S.y, bonk ? 3 : 6, bonk ? 18 : 34);
    if (bonk) {
        P3 p = pj(S.x, S.y, 26);
        popup(p.x + S.ldx * 14, p.y - 6, p.d - 0.2f, "Bonk!", RGBA(255, 230, 200, 255));
        S.shake = 0.18f;
        sfx("miso_bonk");
    } else {
        sfx("miso_land");
    }
    if (S.lhits >= 2) {
        /* a bonus for every extra package swept up in one leap */
        int bonus = (S.lhits - 1) * S.mult;
        S.points += bonus;
        if (S.lhits > S.best_multi)
            S.best_multi = S.lhits;
        char buf[16];
        snprintf(buf, sizeof(buf), "%d in one leap!", S.lhits);
        P3 p = pj(S.x, S.y, 40);
        popup(p.x, p.y - 10, p.d - 0.3f, buf, RGBA(150, 230, 255, 255));
        sfx("miso_leap_multi");
    }
}

static void update_leap(float dt)
{
    S.lt += dt;
    if (S.lstage == LS_CROUCH) {
        if (S.lt < LEAP_CROUCH)
            return;
        S.lstage = LS_AIR;
        S.lsx = S.x;
        S.lsy = S.y;
        dust(S.x, S.y, 4, 26);
    }
    if (S.lstage == LS_AIR) {
        S.lair += dt;
        float u = clampf(S.lair / LEAP_AIR, 0, 1);
        float p = u * (1.4f - 0.4f * u);   /* quick off the floor, softer at the end */
        float tx = S.lsx + S.ldx * LEAP_DIST * p, ty = S.lsy + S.ldy * LEAP_DIST * p;
        float mx = tx - S.x, my = ty - S.y, ml = sqrtf(mx * mx + my * my);
        int n = (int)(ml / 3) + 1;
        bool stop = false, bonk = false;
        for (int i = 0; i < n && !stop; i++) {
            float px = S.x + mx / (float)n, py = S.y + my / (float)n, wx = px, wy = py;
            keep_miso(&px, &py);
            float got = sqrtf(dist2(px, py, S.x, S.y));
            S.x = px;
            S.y = py;
            pickups(LEAP_RX, LEAP_RY, true);
            /* sliding along something is fine; running into it ends the leap:
             * furniture with a bonk, a wall with an early landing */
            if (got < ml / (float)n * 0.5f) {
                stop = true;
                wx = clampf(wx, 12, RW - 12);
                wy = clampf(wy, 10, RD - 6);
                bonk = blocked(wx, wy, MISO_R - 0.5f);
            }
        }
        S.lu = u;
        S.lh = sinf(u * PI_F) * LEAP_H;
        if (stop || u >= 1)
            land(bonk);
        return;
    }
    if (S.lt - S.land_at >= LEAP_LAND)
        S.leaping = false;
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
        p->vy += p->g * dt;
        if (p->round)
            p->vx *= 1 - clampf(dt * 5, 0, 1);
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
                keep_miso(&S.x, &S.y);
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
        S.leaping = false;
        S.lh = 0;
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
    if (S.leap_cd > 0)
        S.leap_cd -= dt;
    if (S.grace > 0)
        S.grace -= dt;
    if (S.frozen > 0) {
        S.frozen -= dt;
        if (S.frozen <= 0) {
            S.grace = SPOT_GRACE;
            sfx("miso_recover");
        }
    } else if (S.leaping) {
        update_leap(dt);
    } else {
        S.x += ix * MISO_SPEED * dt;
        S.y += iy * MISO_SPEED * dt;
        if (il > 0.2f) {
            S.fx = ix / il;
            S.fy = iy / il;
            if (fabsf(ix) > 0.1f)
                S.face = ix > 0 ? 1.0f : -1.0f;
        }
        keep_miso(&S.x, &S.y);
        if ((in->down & (KEY_A_ | KEY_B_)) && S.leap_cd <= 0) {
            if (il > 0.2f)
                start_leap(ix / il, iy / il);
            else
                start_leap(S.fx, S.fy);
        }
        pickups(PICK_RX, PICK_RY, false);
    }
    float moved = sqrtf(dist2(S.x, S.y, ox, oy));
    S.movespd = dt > 0 ? moved / dt : 0;
    if (S.movespd > 15 && !S.leaping) {
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

    /* ---- packages ---- */
    S.spawn_t -= dt * (napping ? 0.5f : 1.0f);
    if (S.spawn_t <= 0) {
        if (pack_count() < PH[S.phase].maxpacks)
            spawn_pack();
        S.spawn_t = PH[S.phase].interval * (0.8f + 0.4f * mg_randf());
    }
    update_packs(dt, napping);
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

/* A face of furniture turned to the camera (constant room Y) is a screen
 * rectangle: one draw instead of two triangles. */
static void face(int eye, float x0, float x1, float y, float h0, float h1, u32 col)
{
    P3 a = pj(x0, y, h1), b = pj(x1, y, h0);
    mg_rect(eye, a.x, a.y, b.x - a.x, b.y - a.y, (a.d + b.d) / 2, col);
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
    fell(eye, 162, 94, 92, 42, 0, RGBA(120, 50, 60, 255), 12);
    fell(eye, 162, 94, 84, 37, 0.3f, RGBA(196, 150, 96, 255), 12);
    fell(eye, 162, 94, 72, 31, 0.6f, RGBA(150, 64, 72, 255), 12);
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
    for (int s = 0; s < 4; s++)
        face(eye, x0, x1, y1, 2 + s * 26.0f, 5 + s * 26.0f, wood);
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
            face(eye, bx, bx + w, y1 + 0.5f, base, base + hh, BOOK[(s * 5 + i * 3) % 6]);
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
        fell(eye, x, y, r, r * 0.8f, 0.4f, rgba_alpha(c, 0.24f * a * k), 12);
        fell(eye, x, y, r * 0.6f, r * 0.48f, 0.5f, rgba_alpha(c, 0.26f * a * k), 8);
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

/* ---- packages ----------------------------------------------------------------------------- */

static const u32 LEAK_C = RGBA(90, 240, 255, 255), LEAK_M = RGBA(235, 90, 255, 255);

/* The fish on every package: a body and a tail, facing right. */
static void draw_fish(int eye, float x, float y, float s, float d, u32 c)
{
    ell(eye, x + 0.6f * s, y, 2.4f * s, 1.45f * s, d, c, 5);
    mg_tri(eye, x - 1.4f * s, y, x - 3.4f * s, y - 1.6f * s, x - 3.4f * s, y + 1.6f * s, d, c);
}

/* One package standing on the floor at screen (x, y), `lift` px up. */
static void draw_pack_shape(int eye, const Pack *p, float x, float y, float k, float d, float sy, float a)
{
    u32 c = rgba_alpha(pack_color(p), a);
    if (p->kind == PK_POUCH) {
        /* an upright foil pouch with a crimped top */
        float w = 9.5f * k, h = 12.5f * k * sy;
        u32 dark = rgba_alpha(mixc(pack_color(p), RGBA(30, 20, 40, 255), 0.35f), a);
        u32 light = rgba_alpha(mixc(pack_color(p), MG_WHITE, 0.45f), a);
        mg_rect(eye, x - w / 2, y - h, w, h, d, c);
        mg_rect(eye, x + w / 2 - 2 * k, y - h, 2 * k, h, d - 0.002f, dark);
        mg_rect(eye, x - w / 2, y - h - 1.2f * k, w, 2.6f * k, d - 0.003f, light);
        mg_rect(eye, x - w / 2 + 1.5f * k, y - h * 0.62f, 1.2f * k, h * 0.45f, d - 0.003f, rgba_alpha(MG_WHITE, a * 0.35f));
        draw_fish(eye, x - 0.3f * k, y - h * 0.42f, 1.15f * k, d - 0.006f, rgba_alpha(MG_WHITE, a));
    } else if (p->kind == PK_BOX) {
        /* a card box: front, top and side, with a blue label */
        float w = 14.5f * k, h = 9.5f * k * sy, t = 4.0f * k;
        u32 top = rgba_alpha(RGBA(232, 192, 140, 255), a), side = rgba_alpha(RGBA(160, 118, 76, 255), a);
        mg_rect(eye, x - w / 2, y - h, w, h, d, c);
        mg_tri(eye, x - w / 2, y - h, x + w / 2, y - h, x + w / 2 + t * 0.6f, y - h - t, d + 0.004f, top);
        mg_tri(eye, x - w / 2, y - h, x + w / 2 + t * 0.6f, y - h - t, x - w / 2 + t * 0.6f, y - h - t, d + 0.004f,
               top);
        mg_tri(eye, x + w / 2, y - h, x + w / 2 + t * 0.6f, y - h - t, x + w / 2 + t * 0.6f, y - t, d + 0.004f, side);
        mg_tri(eye, x + w / 2, y - h, x + w / 2 + t * 0.6f, y - t, x + w / 2, y, d + 0.004f, side);
        mg_rect(eye, x - w / 2, y - h * 0.78f, w, h * 0.56f, d - 0.003f, rgba_alpha(RGBA(70, 120, 205, 255), a));
        draw_fish(eye, x, y - h * 0.5f, 1.25f * k, d - 0.006f, rgba_alpha(MG_WHITE, a));
    } else {
        /* a golden tin, glinting */
        float w = 11 * k, h = 9 * k * sy;
        u32 rim = rgba_alpha(RGBA(176, 128, 40, 255), a);
        ell(eye, x, y, w / 2, 2.2f * k, d + 0.002f, rim, 6);
        mg_rect(eye, x - w / 2, y - h, w, h, d, c);
        mg_rect(eye, x - w / 2, y - h * 0.68f, w, h * 0.4f, d - 0.003f, rgba_alpha(RGBA(46, 80, 160, 255), a));
        draw_fish(eye, x + 0.3f * k, y - h * 0.48f, 0.95f * k, d - 0.006f, rgba_alpha(MG_WHITE, a));
        mg_rect(eye, x - w / 2 + 1.2f * k, y - h + 1 * k, 1.4f * k, h - 2 * k, d - 0.004f, rgba_alpha(MG_WHITE, a * 0.45f));
        ell(eye, x, y - h, w / 2, 2.2f * k, d - 0.004f, rgba_alpha(RGBA(255, 232, 160, 255), a), 6);
        mg_line(eye, x - w / 2 + 1.5f * k, y - h, x + w / 2 - 1.5f * k, y - h, 1.2f * k, d - 0.006f, rim);
        float tw = fmodf(S.t * 1.7f + (float)(p->seed & 15) * 0.1f, 1.0f);
        if (tw < 0.25f) {   /* a glint */
            float g = sinf(tw / 0.25f * PI_F) * 4 * k, gx = x + w * 0.3f, gy = y - h - 1 * k;
            mg_line(eye, gx - g, gy, gx + g, gy, 1.2f, d - 0.03f, rgba_alpha(MG_WHITE, a));
            mg_line(eye, gx, gy - g, gx, gy + g, 1.2f, d - 0.03f, rgba_alpha(MG_WHITE, a));
        }
    }
}

/* The leak opening in the wall: a crack of corrupted pixels. */
static void draw_leak(int eye, const Pack *p, float a)
{
    P3 b = pj(p->wx, p->wy, p->wh);
    u32 seed = p->seed + (u32)(S.t * 14);
    float px = b.x, py = b.y + 9;
    for (int i = 0; i < 4; i++) {
        float qx = px + (hashf(seed + i) - 0.5f) * 7, qy = py - 4.5f - 2 * hashf(seed + 10 + i);
        mg_line(eye, px, py, qx, qy, 1.5f, b.d - 0.01f, rgba_alpha(i & 1 ? LEAK_C : LEAK_M, a));
        px = qx;
        py = qy;
    }
    for (int i = 0; i < 3; i++) {
        float ox = (hashf(seed * 3 + i) - 0.5f) * 16, oy = (hashf(seed * 5 + i) - 0.5f) * 18;
        mg_rect(eye, b.x + ox, b.y + oy, 2, 2, b.d - 0.02f, rgba_alpha(MG_WHITE, a * 0.8f));
    }
}

static void draw_pack(int eye, const Pack *p)
{
    float fade = 1;
    if (S.over)
        fade = clampf(1 - S.outro / 0.6f, 0, 1);
    if (fade <= 0)
        return;
    if (p->t < SHIMMER_TIME + 0.3f)
        draw_leak(eye, p, fade * clampf(1 - (p->t - SHIMMER_TIME) / 0.3f, 0, 1));
    float x, y, h;
    pack_pos(p, &x, &y, &h);
    P3 g = pj(x, y, 0), q = pj(x, y, h);
    float k = q.k * 1.05f, d = q.d - 0.03f;
    if (p->t < SHIMMER_TIME) {
        /* a ghost of the package shimmers in the wall, in the leak's colours */
        P3 w = pj(p->wx, p->wy, p->wh - 6);
        float u = p->t / SHIMMER_TIME, j = (1 - u) * 3 + hashf(p->seed + (u32)(S.t * 20)) * 1.5f;
        draw_pack_shape(eye, p, w.x - j, w.y, k * u, w.d - 0.02f, 1, 0.45f * fade);
        mg_rect(eye, w.x - 6 * k * u + j, w.y - 12 * k * u, 12 * k * u, 12 * k * u, w.d - 0.025f,
                rgba_alpha(LEAK_C, 0.3f * u * fade));
        return;
    }
    if (p->landed) {
        float left = p->life - p->age;
        if (left < 1.6f && fmodf(S.t, 0.2f) < 0.08f + 0.06f * left / 1.6f)
            return;   /* flickering out */
    }
    /* shadow, bigger and softer while it's in the air */
    float hs = clampf(h / 40, 0, 1);
    mg_circle(eye, g.x, g.y, (5.5f - 2.5f * hs) * g.k, g.d, RGBA(30, 16, 30, (int)((90 - 50 * hs) * fade)));
    float sy = 1, lift = 0;
    if (p->landed && p->age < 0.32f) {   /* a little bounce on landing */
        float u = p->age / 0.32f;
        sy = u < 0.25f ? 1 - 0.35f * sinf(u / 0.25f * PI_F) : 1;
        lift = u >= 0.25f ? sinf((u - 0.25f) / 0.75f * PI_F) * 4 * k : 0;
    }
    float bx = q.x, by = q.y - lift;
    /* now and then a flicker of the leak: a cyan / magenta double */
    float gl = hashf(p->seed + (u32)(S.t * 12));
    if (!p->landed || gl < 0.05f) {
        float o = 2.2f;
        mg_rect(eye, bx - 5 * k - o, by - 12 * k, 10 * k, 11 * k, d + 0.01f, rgba_alpha(LEAK_C, 0.35f * fade));
        mg_rect(eye, bx - 5 * k + o, by - 12 * k, 10 * k, 11 * k, d + 0.01f, rgba_alpha(LEAK_M, 0.35f * fade));
    }
    draw_pack_shape(eye, p, bx, by, k, d, sy, fade);
    /* a golden tin's clock: a ring of ticks round it on the floor */
    if (p->kind == PK_TIN && p->landed && !S.over) {
        float left = clampf(1 - p->age / p->life, 0, 1);
        int n = 8, lit = (int)ceilf(left * n);
        for (int i = 0; i < lit; i++) {
            float a0 = -PI_F / 2 + (float)i * TAU_F / n, a1 = a0 + TAU_F / n * 0.6f;
            line3(eye, pj(x + cosf(a0) * 14, y + sinf(a0) * 9, 0.5f), pj(x + cosf(a1) * 14, y + sinf(a1) * 9, 0.5f),
                  1.6f, left < 0.35f ? RGBA(255, 140, 110, 230) : RGBA(255, 220, 120, 200));
        }
    }
}

/* ---- Miso ---------------------------------------------------------------------------------- */

#define FUR RGBA(236, 150, 62, 255)          /* orange, like the story sprites */
#define FUR_DARK RGBA(196, 108, 38, 255)
#define FUR_WHITE RGBA(252, 238, 214, 255)
#define EAR_PINK RGBA(240, 160, 170, 255)
#define PAD_PINK RGBA(236, 136, 150, 255)
#define MISO_K 1.12f                          /* Miso's size against the room */

static void draw_head(int eye, float hx, float hy, float k, float d, float f, int eyes)
{
    /* eyes: 0 open, 1 closed, 2 wide (startled, or thrilled mid-leap) */
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

/* Tail: `n` segments from (x, y) starting at screen angle a0, turning by
 * `bend` per segment; dd moves each segment in depth (a tail streaming
 * towards the viewer comes out of the screen). */
static void draw_tail(int eye, float x, float y, float k, float d, float a0, float bend, float dd)
{
    float a = a0, px = x, py = y;
    for (int i = 0; i < 4; i++) {
        float L = 5.0f * k;
        float qx = px + cosf(a) * L, qy = py + sinf(a) * L;
        mg_line(eye, px, py, qx, qy, (3.3f - 0.25f * (float)i) * k, d + 0.005f + dd * (float)i,
                (i & 1) ? FUR_DARK : FUR);
        px = qx;
        py = qy;
        a += bend;
    }
    mg_circle(eye, px, py, 1.6f * k, d + 0.005f + dd * 4, FUR_DARK);
}

/* Rotated screen ellipse. */
static void ellr(int eye, float cx, float cy, float rx, float ry, float ang, float d, u32 c, int n)
{
    float s = mg_shift(eye, d), ca = cosf(ang), sa = sinf(ang);
    float px = cx + ca * rx + s, py = cy + sa * rx;
    for (int i = 1; i <= n; i++) {
        float a = (float)i * TAU_F / (float)n, lx = cosf(a) * rx, ly = sinf(a) * ry;
        float x = cx + lx * ca - ly * sa + s, y = cy + lx * sa + ly * ca;
        gfx_triangle(cx + s, cy, px, py, x, y, c);
        px = x;
        py = y;
    }
}

typedef struct {
    float x, y;
} V2;

/* Miso side-on, facing f (+1 right). The body is an ellipse at (cx, cy)
 * pitched by ang (positive: nose down); paws are screen points: front far,
 * front near, hind far, hind near. */
typedef struct {
    float cx, cy, rx, ry, ang;
    V2 ff, fn, hf, hn;
    float ta, tb;      /* tail start angle and bend */
    int eyes;
    float head_dy;     /* extra head drop */
    bool pads;         /* show the pink pads of the hind paws (pushing off) */
} Side;

static void draw_side(int eye, const Side *s, float k, float d, float f)
{
    float Ax = f * cosf(s->ang), Ay = sinf(s->ang), Nx = -f * sinf(s->ang), Ny = cosf(s->ang);
    float sc = s->rx / (12.5f * k), sn = s->ry / (7 * k);
#define BP(a_, n_) ((V2){s->cx + Ax * (a_) + Nx * (n_), s->cy + Ay * (a_) + Ny * (n_)})
    V2 r;
    /* far legs, tail, body, near legs, head */
    r = BP(-7 * k * sc, 3 * k * sn);
    mg_line(eye, r.x, r.y, s->hf.x, s->hf.y, 2.8f * k, d + 0.01f, FUR_DARK);
    r = BP(7 * k * sc, 3 * k * sn);
    mg_line(eye, r.x, r.y, s->ff.x, s->ff.y, 2.8f * k, d + 0.01f, FUR_DARK);
    r = BP(-s->rx * 0.85f, -2 * k * sn);
    draw_tail(eye, r.x, r.y, k, d, s->ta, s->tb, 0);
    ellr(eye, s->cx, s->cy, s->rx, s->ry, f > 0 ? s->ang : -s->ang, d, FUR, 12);
    for (int i = -1; i <= 1; i++) {
        V2 a = BP((float)i * 4.5f * k * sc - 1 * k, -s->ry * 0.95f), b = BP((float)i * 4.5f * k * sc - 2.5f * k,
                                                                             -s->ry * 0.25f);
        mg_line(eye, a.x, a.y, b.x, b.y, 1.7f * k, d - 0.005f, FUR_DARK);
    }
    r = BP(4 * k * sc, 3 * k * sn);
    ellr(eye, r.x, r.y, 6 * k * sc, 3.2f * k * sn, f > 0 ? s->ang : -s->ang, d - 0.01f, FUR_WHITE, 8);
    r = BP(-9 * k * sc, 3 * k * sn);
    mg_line(eye, r.x, r.y, s->hn.x, s->hn.y, 3.0f * k, d - 0.01f, FUR);
    r = BP(5 * k * sc, 3 * k * sn);
    mg_line(eye, r.x, r.y, s->fn.x, s->fn.y, 3.0f * k, d - 0.01f, FUR);
    mg_circle(eye, s->hn.x, s->hn.y, 1.7f * k, d - 0.015f, FUR_WHITE);
    mg_circle(eye, s->fn.x, s->fn.y, 1.7f * k, d - 0.015f, FUR_WHITE);
    if (s->pads)
        mg_circle(eye, s->hn.x - Ax * 0.6f * k, s->hn.y - Ay * 0.6f * k, 0.9f * k, d - 0.02f, PAD_PINK);
    r = BP(s->rx * 0.95f, -7 * k);
    draw_head(eye, r.x, r.y + s->head_dy, k, d - 0.02f, f, s->eyes);
#undef BP
}

/* Squash before take-off and on landing, stretch in the air. `u` is the
 * progress through the stage. */
typedef struct {
    int dir, stage;
    float u, h;      /* stage progress; height above the floor (room units) */
    bool bonk;
} Leap;

static void speed_lines(int eye, float x, float y, float dx, float dy, float len, float spread, float d, float a)
{
    float nx = -dy, ny = dx;
    for (int i = -1; i <= 1; i++) {
        float o = (float)i * spread, l = len * (i == 0 ? 1.0f : 0.7f);
        float x0 = x + nx * o - dx * fabsf(o) * 0.4f, y0 = y + ny * o - dy * fabsf(o) * 0.4f;
        mg_line(eye, x0, y0, x0 - dx * l, y0 - dy * l, 1.3f, d, rgba_alpha(MG_WHITE, a));
    }
}

/* Left and right: side-on, the body stretched long, front paws reaching,
 * hind legs kicking back, the tail streaming out behind. */
static void draw_leap_side(int eye, float bx, float by, float k, float d, float f, const Leap *L)
{
    Side s;
    float lift = L->h * k;
    s.pads = false;
    s.head_dy = 0;
    if (L->stage == LS_CROUCH) {
        /* low and wound up, rump wiggling, tail flat out behind */
        float q = sinf(clampf(L->u, 0, 1) * PI_F / 2);
        s.rx = 12.5f * k * (1 + 0.16f * q);
        s.ry = 7 * k * (1 - 0.3f * q);
        s.ang = 0.18f * q;
        s.cx = bx - f * 1.5f * k * q + sinf(S.t * 45) * 0.7f * k * q;
        s.cy = by - 10 * k + 5 * k * q;
        s.ff = (V2){s.cx + f * 11 * k, by};
        s.fn = (V2){s.cx + f * 9 * k, by};
        s.hf = (V2){s.cx - f * 5 * k, by};
        s.hn = (V2){s.cx - f * 7 * k, by};
        s.ta = (f > 0 ? PI_F + 0.2f : -0.2f);
        s.tb = f * (0.1f + 0.2f * sinf(S.t * 40));
        s.eyes = 0;
        s.head_dy = 2.5f * k * q;
    } else if (L->stage == LS_AIR) {
        float u = L->u, e = smooth01(u);
        float st = 1 + 0.42f * sinf(PI_F * (0.12f + 0.76f * u));
        s.rx = 12.5f * k * st;
        s.ry = 7 * k / sqrtf(st) * 0.95f;
        s.ang = lerpf(-0.36f, 0.32f, u);
        s.cx = bx;
        s.cy = by - 10 * k - lift;
        float Ax = f * cosf(s.ang), Ay = sinf(s.ang), Nx = -f * sinf(s.ang), Ny = cosf(s.ang);
        /* front paws reach out ahead, then down for the landing */
        float fa = s.rx * 0.55f + lerpf(15, 8, e) * k, fnn = lerpf(2.5f, 7.5f, e) * k;
        s.fn = (V2){s.cx + Ax * (fa + 1.5f * k) + Nx * fnn, s.cy + Ay * (fa + 1.5f * k) + Ny * fnn};
        s.ff = (V2){s.cx + Ax * (fa - 1.5f * k) + Nx * (fnn + 1 * k), s.cy + Ay * (fa - 1.5f * k) + Ny * (fnn + 1 * k)};
        /* hind legs kick out straight behind, then tuck */
        float ha = -s.rx * 0.55f - lerpf(12, 4, e) * k, hnn = lerpf(3.5f, 6.5f, e) * k;
        s.hn = (V2){s.cx + Ax * ha + Nx * hnn, s.cy + Ay * ha + Ny * hnn};
        s.hf = (V2){s.cx + Ax * (ha + 2 * k) + Nx * (hnn - 1 * k), s.cy + Ay * (ha + 2 * k) + Ny * (hnn - 1 * k)};
        s.pads = u < 0.5f;
        /* the tail streams out behind, rippling */
        s.ta = atan2f(-Ay, -Ax) + f * 0.2f;
        s.tb = f * (0.06f + 0.14f * sinf(S.t * 22));
        s.eyes = 0;
        speed_lines(eye, s.cx - Ax * (s.rx + 9 * k), s.cy - Ay * (s.rx + 9 * k) - 1 * k, Ax, Ay, 9 * k, 4.5f * k,
                    d + 0.02f, 0.55f * (1 - u * 0.6f));
    } else {
        float l = 1 - clampf(L->u, 0, 1), q = l * l * (L->bonk ? 1.2f : 1);
        s.rx = 12.5f * k * (1 + 0.22f * q);
        s.ry = 7 * k * (1 - 0.32f * q);
        s.ang = (L->bonk ? -0.1f : 0.1f) * q;
        s.cx = bx;
        s.cy = by - 10 * k + 4.2f * k * q;
        s.ff = (V2){s.cx + f * (9 + 3 * q) * k, by};
        s.fn = (V2){s.cx + f * (7 + 4 * q) * k, by};
        s.hf = (V2){s.cx - f * (7 + 1 * q) * k, by};
        s.hn = (V2){s.cx - f * (9 + 2 * q) * k, by};
        s.ta = -PI_F / 2 - f * (0.7f + 0.9f * q);
        s.tb = f * 0.35f;
        s.eyes = L->bonk ? 1 : 0;
        s.head_dy = 1.5f * k * q;
    }
    draw_side(eye, &s, k, d, f);
}

/* Up the room, away from the camera: Miso from behind, her back, the back
 * of her head and ears, hind legs pushing off with their pads showing; she
 * gets a little smaller as she flies off. */
static void draw_leap_up(int eye, float bx, float by, float k, float d, const Leap *L)
{
    float sq = 0, st = 1, push = 0, reach = 0, sm = 1, dd = d;
    if (L->stage == LS_CROUCH) {
        sq = 0.26f * sinf(clampf(L->u, 0, 1) * PI_F / 2);
    } else if (L->stage == LS_AIR) {
        float u = L->u;
        st = 1 + 0.26f * sinf(PI_F * (0.1f + 0.8f * u));
        sm = 1 - 0.12f * sinf(PI_F * u);
        push = 1 - smooth01(u * 1.6f);
        reach = sinf(PI_F * clampf(u * 1.2f, 0, 1));
        dd = d + 0.06f * sinf(PI_F * u);
    } else {
        float l = 1 - clampf(L->u, 0, 1);
        sq = 0.3f * l * l * (L->bonk ? 1.2f : 1);
    }
    float kk = k * sm, lift = L->h * k;
    float rx = 9.8f * kk * (1 + 0.4f * sq) / sqrtf(st), ry = 9.0f * kk * (1 - 0.3f * sq) * st;
    float cx = bx, cy = by - 8.5f * kk - lift + 2.5f * kk * sq / 0.3f * 0.6f;
    float hx = cx, hy = cy - ry * 0.95f + 1.5f * kk * sq / 0.3f;
    /* front legs reach up ahead of her (furthest away: drawn first) */
    if (reach > 0.05f)
        for (int s = -1; s <= 1; s += 2) {
            float x0 = cx + (float)s * 4.5f * kk, y0 = cy - ry * 0.55f;
            float x1 = cx + (float)s * (7 + 2.5f * reach) * kk, y1 = hy - (1 + 5 * reach) * kk;
            mg_line(eye, x0, y0, x1, y1, 2.6f * kk, dd + 0.015f, FUR_DARK);
            mg_circle(eye, x1, y1, 1.7f * kk, dd + 0.01f, FUR_WHITE);
        }
    ell(eye, cx, cy, rx, ry, dd, FUR, 12);
    /* haunches: from behind she's pear-shaped */
    for (int s = -1; s <= 1; s += 2)
        ell(eye, cx + (float)s * rx * 0.5f, cy + ry * 0.52f, rx * 0.6f, ry * 0.44f, dd - 0.003f, FUR, 8);
    /* tabby stripes across the back */
    for (int i = -1; i <= 1; i++) {
        float y = cy + (float)i * ry * 0.34f, w = rx * (0.62f - 0.12f * fabsf((float)i));
        mg_line(eye, cx - w, y - 1 * kk, cx - w * 0.2f, y + 0.6f * kk, 1.6f * kk, dd - 0.005f, FUR_DARK);
        mg_line(eye, cx + w * 0.2f, y + 0.6f * kk, cx + w, y - 1 * kk, 1.6f * kk, dd - 0.005f, FUR_DARK);
    }
    /* the back of her head: ears up, no face */
    float hd = dd - 0.006f;
    mg_tri(eye, hx - 6.6f * kk, hy - 1.5f * kk, hx - 5 * kk, hy - 11.5f * kk, hx - 0.8f * kk, hy - 6 * kk, hd, FUR);
    mg_tri(eye, hx + 0.8f * kk, hy - 6 * kk, hx + 5 * kk, hy - 11.5f * kk, hx + 6.6f * kk, hy - 1.5f * kk, hd, FUR);
    mg_tri(eye, hx - 5.6f * kk, hy - 3 * kk, hx - 5 * kk, hy - 10.5f * kk, hx - 4.2f * kk, hy - 4 * kk, hd - 0.004f,
           FUR_DARK);
    mg_tri(eye, hx + 4.2f * kk, hy - 4 * kk, hx + 5 * kk, hy - 10.5f * kk, hx + 5.6f * kk, hy - 3 * kk, hd - 0.004f,
           FUR_DARK);
    mg_circle(eye, hx, hy + 0.6f * kk, 7.3f * kk, hd + 0.002f, FUR_DARK);   /* where the head meets the back */
    mg_circle(eye, hx, hy, 7 * kk, hd, FUR);
    mg_line(eye, hx - 2 * kk, hy - 6 * kk, hx - 1.6f * kk, hy - 1.5f * kk, 1.3f * kk, hd - 0.005f, FUR_DARK);
    mg_line(eye, hx + 2 * kk, hy - 6 * kk, hx + 1.6f * kk, hy - 1.5f * kk, 1.3f * kk, hd - 0.005f, FUR_DARK);
    mg_line(eye, hx, hy - 6.8f * kk, hx, hy - 2.5f * kk, 1.3f * kk, hd - 0.005f, FUR_DARK);
    /* hind legs: nearest the camera, kicking back towards it */
    for (int s = -1; s <= 1; s += 2) {
        float x0 = cx + (float)s * 5 * kk, y0 = cy + ry * 0.45f, x1, y1;
        if (L->stage == LS_AIR) {
            x1 = cx + (float)s * lerpf(5, 6.5f, push) * kk;
            y1 = lerpf(cy + ry + 0.5f * kk, cy + ry + 8 * kk, push);
        } else {
            x1 = cx + (float)s * (6.5f + 3 * sq) * kk;
            y1 = by - 0.5f * kk;
        }
        mg_line(eye, x0, y0, x1, y1, 3.4f * kk, dd - 0.02f, FUR);
        mg_circle(eye, x1, y1, 2.2f * kk, dd - 0.025f, FUR_WHITE);
        if (push > 0.25f || L->stage != LS_AIR)
            mg_circle(eye, x1, y1 + 0.3f * kk, 1.1f * kk, dd - 0.03f, PAD_PINK);
    }
    /* the tail streams back towards the camera, out of the screen */
    float sway = sinf(S.t * 16) * 0.25f;
    if (L->stage == LS_AIR)
        draw_tail(eye, cx, cy + ry * 0.8f, kk, dd - 0.03f, PI_F / 2 + sway, -sway * 0.6f, -0.012f);
    else
        draw_tail(eye, cx, cy + ry * 0.75f, kk, dd - 0.03f, PI_F / 2 + 0.7f, -0.35f + sway * 0.4f, -0.006f);
    if (L->stage == LS_AIR)
        speed_lines(eye, cx, cy + ry + 10 * kk, 0, -1, 8 * kk, 5 * kk, dd - 0.04f, 0.5f * (1 - L->u * 0.6f));
}

/* Down the room, towards the camera: Miso from the front, paws out, eyes
 * wide, growing a little and popping out of the screen. */
static void draw_leap_down(int eye, float bx, float by, float k, float d, const Leap *L)
{
    float sq = 0, st = 1, reach = 0, gr = 1, dd = d;
    int eyes = 0;
    if (L->stage == LS_CROUCH) {
        sq = 0.26f * sinf(clampf(L->u, 0, 1) * PI_F / 2);
    } else if (L->stage == LS_AIR) {
        float u = L->u;
        st = 1 + 0.22f * sinf(PI_F * (0.1f + 0.8f * u));
        gr = 1 + 0.2f * sinf(PI_F * u);
        reach = sinf(PI_F * clampf(u * 1.15f, 0, 1));
        dd = d - 0.22f * sinf(PI_F * u);
        eyes = 2;
    } else {
        float l = 1 - clampf(L->u, 0, 1);
        sq = 0.3f * l * l * (L->bonk ? 1.2f : 1);
        eyes = L->bonk ? 1 : 0;
    }
    float kk = k * gr, lift = L->h * k, sqn = sq / 0.3f;
    float rx = 9 * kk * (1 + 0.35f * sq) / sqrtf(st), ry = 8.2f * kk * (1 - 0.3f * sq) * st;
    float cx = bx, cy = by - 8.5f * kk - lift + 2.2f * kk * sqn;
    float hx = cx, hy = cy - ry * 0.95f + 1.5f * kk * sqn;
    /* the tail waves up behind her */
    float sway = sinf(S.t * (L->stage == LS_AIR ? 14.0f : 30.0f)) * 0.3f;
    draw_tail(eye, cx + 3 * kk, cy - ry * 0.3f, kk, dd + 0.03f, -PI_F / 2 + 0.55f + sway, -0.3f - sway * 0.5f, 0.004f);
    /* haunches either side when she's down on the floor */
    if (L->stage != LS_AIR)
        for (int s = -1; s <= 1; s += 2)
            ell(eye, cx + (float)s * 7 * kk, cy + ry * 0.55f, 4.2f * kk, 3.6f * kk, dd + 0.01f, FUR_DARK, 8);
    ell(eye, cx, cy, rx, ry, dd, FUR, 12);
    ell(eye, cx, cy + ry * 0.15f, rx * 0.5f, ry * 0.68f, dd - 0.008f, FUR_WHITE, 10);
    /* front legs: out towards the camera in the air, planted otherwise */
    for (int s = -1; s <= 1; s += 2) {
        float x0 = cx + (float)s * 4.5f * kk, y0 = cy - ry * 0.05f, x1, y1, pd;
        if (L->stage == LS_AIR) {
            x1 = cx + (float)s * (5.5f + 4.5f * reach) * kk;
            y1 = cy + ry + (1.5f - 1.5f * reach) * kk;
            pd = dd - 0.05f - 0.08f * reach;
        } else {
            x1 = cx + (float)s * (4 + 2.5f * sq) * kk;
            y1 = by - 0.5f * kk;
            pd = dd - 0.02f;
        }
        mg_line(eye, x0, y0, x1, y1, 3.3f * kk, (dd + pd) / 2 - 0.01f, FUR);
        mg_circle(eye, x1, y1, (L->stage == LS_AIR ? 2.7f : 2.2f) * kk, pd, FUR_WHITE);
        if (L->stage == LS_AIR && reach > 0.3f) {   /* paws turned to the camera: pink beans */
            mg_circle(eye, x1, y1 + 0.4f * kk, 1.2f * kk, pd - 0.005f, PAD_PINK);
            for (int t = -1; t <= 1; t++)
                mg_circle(eye, x1 + (float)t * 1.3f * kk, y1 - 1.5f * kk, 0.55f * kk, pd - 0.005f, PAD_PINK);
        }
    }
    draw_head(eye, hx, hy, kk * 1.04f, dd - 0.03f, 0, eyes);
    if (L->stage == LS_AIR) {   /* rushing at the viewer */
        float a = 0.5f * (1 - L->u * 0.5f);
        for (int s = -1; s <= 1; s += 2) {
            float x = cx + (float)s * (rx + 6 * kk), y = cy - 2 * kk;
            mg_line(eye, x, y, x + (float)s * 6 * kk, y - 4 * kk, 1.3f, dd - 0.02f, rgba_alpha(MG_WHITE, a));
            mg_line(eye, x, y + 6 * kk, x + (float)s * 7 * kk, y + 6 * kk, 1.3f, dd - 0.02f, rgba_alpha(MG_WHITE, a));
        }
    }
}

static void draw_leap(int eye, float bx, float by, float k, float d, float f, const Leap *L)
{
    if (L->dir == LD_UP)
        draw_leap_up(eye, bx, by, k, d, L);
    else if (L->dir == LD_DOWN)
        draw_leap_down(eye, bx, by, k, d, L);
    else
        draw_leap_side(eye, bx, by, k, d, f, L);
}

static void draw_miso(int eye)
{
    if (S.grace > 0 && fmodf(S.grace, 0.2f) < 0.07f)
        return;
    P3 b = pj(S.x, S.y, 0);
    float k = b.k * MISO_K, d = b.d - 0.04f, f = S.face;
    bool leaping = S.leaping && S.frozen <= 0 && !S.over;
    bool moving = S.movespd > 15 && !leaping && !(S.over && S.sat);
    bool napping = S.nap > 0 && !S.over;
    float sh = S.shake > 0 ? sinf(S.shake * 90) * 2 : 0;
    float bx = b.x + sh, by = b.y;

    /* the shadow shrinks and fades as she leaves the floor */
    float hs = leaping ? clampf(S.lh / LEAP_H, 0, 1) : 0;
    fell(eye, S.x, S.y, 14 * (1 - 0.35f * hs), 7 * (1 - 0.35f * hs), 0, RGBA(30, 20, 30, (int)(70 - 30 * hs)), 8);

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

    if (leaping) {
        Leap L;
        L.dir = S.ldir;
        L.stage = S.lstage;
        L.bonk = S.bonk;
        L.h = S.lh;
        L.u = S.lstage == LS_CROUCH ? S.lt / LEAP_CROUCH : S.lstage == LS_AIR ? S.lu : (S.lt - S.land_at) / LEAP_LAND;
        draw_leap(eye, bx, by, k, d - S.lh * 0.0016f, f, &L);
        return;
    }

    if (napping && !moving) {
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

    /* standing or walking, side-on */
    float bob = moving ? fabsf(sinf(S.walk)) * 1.6f * k : 0;
    float swish = sinf(S.t * (moving ? 5.0f : 2.2f)) * 0.45f;
    if (S.frozen > 0)
        swish = 0.9f * f;   /* bottle-brush tail, straight up */
    float sw = moving ? sinf(S.walk) * 3 * k : 0;
    Side s;
    s.cx = bx;
    s.cy = by - 10 * k - bob;
    s.rx = 12.5f * k;
    s.ry = 7 * k;
    s.ang = 0;
    s.hf = (V2){bx - f * 7 * k - sw, by};
    s.ff = (V2){bx + f * 7 * k + sw, by};
    s.hn = (V2){bx - f * 9 * k + sw, by};
    s.fn = (V2){bx + f * 5 * k - sw, by};
    s.ta = -PI_F / 2 - f * 0.7f + swish;
    s.tb = f * 0.35f + swish * 0.3f;
    s.eyes = S.frozen > 0 ? 2 : 0;
    s.head_dy = 0;
    s.pads = false;
    draw_side(eye, &s, k, d, f);

    float hx = bx + f * s.rx * 0.95f, hy = s.cy - 7 * k;
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

enum { OBJ_PACK, OBJ_MISO, OBJ_SOFA, OBJ_PLANT };

static void draw_top(int eye)
{
    draw_room(eye);
    draw_bookshelf(eye);
    draw_beam_spots(eye);

    /* painter's order by depth into the room */
    int kind[MAX_PACKS + 3], idx[MAX_PACKS + 3], n = 0;
    float key[MAX_PACKS + 3];
    kind[n] = OBJ_SOFA, idx[n] = 0, key[n++] = 70;
    kind[n] = OBJ_PLANT, idx[n] = 0, key[n++] = 140;
    kind[n] = OBJ_MISO, idx[n] = 0, key[n++] = S.y;
    for (int i = 0; i < MAX_PACKS; i++)
        if (S.packs[i].on) {
            float x, y, h;
            pack_pos(&S.packs[i], &x, &y, &h);
            kind[n] = OBJ_PACK, idx[n] = i, key[n++] = y + h * 0.5f;
        }
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
        default: draw_pack(eye, &S.packs[idx[i]]); break;
        }
    }

    draw_beam_cones(eye);

    /* sparks, dust and score pop-ups */
    for (int i = 0; i < MAX_PARTS; i++) {
        const Part *p = &S.parts[i];
        if (p->life <= 0)
            continue;
        float a = p->life / p->max;
        if (p->round)
            mg_circle(eye, p->x, p->y, p->size * (1.6f - 0.6f * a), p->d, rgba_alpha(p->c, a));
        else
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
    for (int i = 0; i < MAX_PACKS; i++) {
        const Pack *p = &S.packs[i];
        if (!p->on || S.over)
            continue;
        float x, y, h, mx, my;
        pack_pos(p, &x, &y, &h);
        map_pt(x, y, &mx, &my);
        if (p->landed && p->life - p->age < 1.6f && fmodf(S.t, 0.2f) < 0.08f)
            continue;
        u32 c = p->landed ? pack_color(p) : rgba_alpha(LEAK_C, 0.7f);
        if (p->kind == PK_TIN) {
            gfx_circle(mx, my, 3.5f, c);
            if (p->landed)
                gfx_rect(mx - 3.5f, my + 5, 7 * clampf(1 - p->age / p->life, 0, 1), 1.5f, MG_GOLD);
        } else if (p->kind == PK_BOX) {
            gfx_rect(mx - 4, my - 3, 8, 6, c);
        } else {
            gfx_rect(mx - 2.5f, my - 3.5f, 5, 7, c);
        }
    }
    {   /* Miso: a little cat head, and where a leap would take her */
        float mx, my;
        map_pt(S.x, S.y, &mx, &my);
        u32 c = S.frozen > 0 ? MG_GOLD : RGBA(235, 235, 245, 255);
        gfx_triangle(mx - 6, my - 1, mx - 5, my - 9, mx - 1, my - 5, c);
        gfx_triangle(mx + 1, my - 5, mx + 5, my - 9, mx + 6, my - 1, c);
        gfx_circle(mx, my, 5.5f, c);
        gfx_circle(mx - 2, my - 0.5f, 1, MG_INK);
        gfx_circle(mx + 2, my - 0.5f, 1, MG_INK);
        if (S.leaping && S.lstage == LS_AIR) {
            float ex, ey;
            map_pt(S.lsx, S.lsy, &ex, &ey);
            gfx_line(ex, ey, mx, my, 2, RGBA(255, 255, 255, 70));
        }
    }

    /* stats */
    float y = 180;
    snprintf(buf, sizeof(buf), "Packages %d   Points %d", S.got, S.points);
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
    /* leap: ready, or recharging */
    float ready = S.leaping ? 0 : clampf(1 - S.leap_cd / LEAP_COOL, 0, 1);
    gfx_text("Leap", 172, y + 38, 0.45f, ready >= 1 ? MG_WHITE : RGBA(120, 120, 130, 255));
    gfx_rect(204, y + 44, 26, 4, RGBA(255, 255, 255, 40));
    gfx_rect(204, y + 44, 26 * ready, 4, ready >= 1 ? RGBA(150, 230, 255, 255) : RGBA(120, 150, 170, 255));
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
    static char buf[112];
    int sc = score();
    const char *tail = sc >= 90 ? "Purr-fect." : sc >= 70 ? "Well fed." : sc >= 45 ? "A decent snack."
                                                                                    : "Still hungry.";
    snprintf(buf, sizeof(buf), "%d packages (%d on the leap), best combo %d, spotted %d. %s", S.got, S.leap_got,
             S.best_combo, S.spotted, tail);
    return buf;
}

/* ---- bot: chase the best package, leap when the way is clear ------------------------------ */

/* No furniture along the way (for a body of radius r). */
static bool path_clear(float x0, float y0, float x1, float y1, float r)
{
    for (int i = 1; i <= 12; i++) {
        float u = (float)i / 12;
        if (blocked(lerpf(x0, x1, u), lerpf(y0, y1, u), r))
            return false;
    }
    return true;
}

/* No beam along the way, now or a moment later. */
static bool path_safe(float x0, float y0, float x1, float y1)
{
    if (S.nap > 0.4f || S.grace > 0.5f)
        return true;
    for (int b = 0; b < S.nbeams; b++) {
        if (S.beams[b].fade < 0.5f)
            continue;
        for (int s = 0; s < 3; s++) {
            float bx, by;
            beam_xy_at(b, S.beams[b].ph + PH[S.phase].bspeed * 0.2f * (float)s, &bx, &by);
            float r = BD[b].r + 10;
            for (int i = 0; i <= 8; i++) {
                float u = (float)i / 8;
                if (dist2(lerpf(x0, x1, u), lerpf(y0, y1, u), bx, by) < r * r)
                    return false;
            }
        }
    }
    return true;
}

static void bot(Input *in, float t)
{
    static bool napped;
    if (t < 0.05f)
        napped = false;
    if (S.over)
        return;
    bool napping = S.nap > 0;

    /* pick a target: worth a lot, close, not inside a beam, still there when she arrives */
    int best = -1;
    float best_cost = 1e9f, tx = 160, ty = 100;
    for (int i = 0; i < MAX_PACKS; i++) {
        const Pack *p = &S.packs[i];
        if (!p->on)
            continue;
        float dd = sqrtf(dist2(p->x, p->y, S.x, S.y));
        float eta = dd < 50 ? dd / MISO_SPEED : 0.3f + (dd - 50) / 260;
        float cost = eta - 0.25f * (float)PK_VALUE[p->kind];
        if (!p->landed)
            cost += fmaxf(0, SHIMMER_TIME + FLY_TIME - p->t - eta) + 0.2f;
        else if (!napping && p->life - p->age < eta + 0.15f)
            cost += 10;
        if (!napping)
            for (int b = 0; b < S.nbeams; b++) {
                float bx, by;
                beam_xy(b, &bx, &by);
                if (dist2(bx, by, p->x, p->y) < (BD[b].r + 12) * (BD[b].r + 12))
                    cost += 1.0f;
            }
        if (cost < best_cost) {
            best_cost = cost;
            best = i;
            tx = p->x;
            ty = p->y;
        }
    }

    /* round the furniture: head for the corner that gets her there */
    float gx = tx, gy = ty;
    if (!path_clear(S.x, S.y, tx, ty, MISO_R - 1)) {
        float bestw = 1e9f;
        for (unsigned o = 0; o < ARRAY_LEN(OBST); o++)
            for (int c = 0; c < 4; c++) {
                float cx = (c & 1) ? OBST[o].x1 + 14 : OBST[o].x0 - 14;
                float cy = (c & 2) ? OBST[o].y1 + 14 : OBST[o].y0 - 14;
                if (blocked(cx, cy, 2) || !path_clear(S.x, S.y, cx, cy, MISO_R - 1))
                    continue;
                float w = sqrtf(dist2(S.x, S.y, cx, cy)) + sqrtf(dist2(cx, cy, tx, ty));
                if (w < bestw) {
                    bestw = w;
                    gx = cx;
                    gy = cy;
                }
            }
    }
    float dx = gx - S.x, dy = gy - S.y, dl = sqrtf(dx * dx + dy * dy) + 0.001f;
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
    float wx = vx + ax, wy = vy + ay, wl = sqrtf(wx * wx + wy * wy);
    if (wl > 0.001f) {
        wx /= wl;
        wy /= wl;
    }

    /* leap when the goal is a fair way off and the whole leap is clear */
    if (best >= 0 && !S.leaping && S.leap_cd <= 0 && S.frozen <= 0 && dl > 36) {
        float reach = fminf(LEAP_DIST, dl + 12);
        float ex = S.x + vx * LEAP_DIST, ey = S.y + vy * LEAP_DIST;
        bool landed_soon = S.packs[best].landed || S.packs[best].t + dl / 300 > SHIMMER_TIME + FLY_TIME;
        if (landed_soon && path_clear(S.x, S.y, S.x + vx * reach, S.y + vy * reach, MISO_R - 1) &&
            path_safe(S.x, S.y, ex, ey)) {
            wx = vx;
            wy = vy;
            in->down |= (t > 30 && ((int)(t * 10) & 1)) ? KEY_B_ : KEY_A_;
        }
    }
    in->cx = wx;
    in->cy = -wy;

    /* nap once, when a beam is closing in during the busy middle */
    if (!napped && t > 38 && (danger > 0.8f || t > 58)) {
        in->down |= KEY_L_;
        napped = true;
    }
}

const MiniGame MG_MISO = {
    .id = "miso",
    .title = "Miso's Hunt",
    .rules = "Cat food is leaking out of the walls of Aron's\n"
             "flat! Walk Miso over the packages to grab them,\n"
             "or leap to cover ground fast. Golden tins hide\n"
             "in corners and vanish fast; nothing waits long.\n"
             "Grab them back to back for a combo multiplier.\n"
             "The angels' beams are watching: if one spots\n"
             "Miso she freezes and the combo resets. 75 s.",
    .controls = "D-pad / Circle Pad: walk (walk over a\n"
                "     package to grab it)\n"
                "A or B: leap the way you steer: far and\n"
                "     fast, grabbing all on the way\n"
                "Furniture stops a leap. Mind the beams.\n"
                "START: pause",
    .cheat = "Nap: beams stop for 5 s, packages stay put",
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
