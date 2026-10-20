/* The Tower: a vertical platformer around a tall stone tower.
 *
 * Tiny Aron climbs 300 m on ledges that grow out of the wall: leafy ledges,
 * stone outcrops, wooden planks sliding along rails, cracked stones that
 * crumble a moment after he steps on them, bouncy mushrooms, and the old leaf
 * discs that orbit the tower. The map is built row by row from the run's seed
 * as he climbs, into a ring buffer of RING rows. Every row has a "path"
 * platform placed within a jump-reach model of the previous one (never two
 * movers in a row), so there is always a way up; extra platforms, enemies
 * and pickups are scattered around it.
 *
 * Walking left and right goes around the tower: the camera turns with Aron,
 * ledges in front pop out of the screen, ledges at the sides recede, those
 * behind are hidden, and the backdrop turns the other way.
 *
 * Glitch beetles and grumpy crows patrol ledges (higher up crows also fly):
 * jump on them for a bounce (hold A for a big one); touching them otherwise
 * costs one of three hearts. Acorns, roof tiles and falling stars drop from
 * the sky, each announced by a marker at the top of the screen and a shadow
 * where it will land. Every 75 m is a tier: the music changes and enemies,
 * movers and falling things get denser and faster. A mist rises slowly from
 * below: dropping under the screen, or losing all hearts, ends the run. At
 * the top Aron hops through the hatch and pops out in a scenery picked at
 * random for the run.
 *
 * The cheat is an updraft that lifts Aron one whole tier (75 m), blowing
 * enemies and falling things away.
 *
 * Score, with h = height reached / 300 m:
 *     62 h + 10 (top) + 10 tq (top) + 3 h hearts + 0.75 min(stomps, 12)
 * where tq is 1 at 90 s or less and 0 at 200 s or more. */

#include "minigame.h"


/* ---- world -------------------------------------------------------------- */

#define CX 200.0f
#define ANCH 150.0f          /* screen y of the camera height */
#define TR 88.0f             /* tower radius */
#define RO 130.0f            /* outer edge of the ledges */
#define RA 116.0f            /* Aron walks at this radius; arc lengths u are measured here */
#define CIRC (6.2831853f * RA)
#define PX_M 10.0f           /* world px per metre */
#define TOP_Y 3000.0f        /* 300 m */
#define TIER_Y 750.0f        /* 75 m */
#define TILT_K 0.0022f       /* how much of a ledge's top you see per px below the eye */
#define FACE_K 2.2f          /* and how much deeper its top face is drawn */
#define BRICK 28.0f
#define RING 32
#define SLOTS 3
#define NEN 12
#define NFALL 8
#define NPART 48
#define NPOP 4
#define NSCENE 5
#define TOP_END 5.2f
#define TIME_CAP 300.0f
#define OVER_T 2.2f
#define GUST_T 2.2f
#define CRACK_T 0.8f
#define GONE_T 4.0f

/* ---- physics (px, s) ------------------------------------------------------ */

#define VMAX 118.0f
#define ACC 950.0f
#define TURN 2000.0f
#define FRIC 1100.0f
#define ACC_AIR 700.0f
#define V0 400.0f            /* jump: 80 px with A held, 31 px tapped */
#define G_UP 1000.0f
#define G_CUT 2600.0f
#define G_FALL 1650.0f
#define VTERM 440.0f
#define COYOTE 0.1f
#define BUFFER 0.13f
#define BOUNCE_V 590.0f      /* mushrooms: 174 px */
#define STOMP_V 340.0f
#define STOMP_VH 470.0f      /* stomp with A held: 110 px */
#define AW 5.0f              /* Aron's half width */
#define AH 22.0f             /* and height */
#define ASC 1.3f             /* his drawing scale */

static const char *const MUSIC[4] = {"tower_1", "tower_2", "tower_3", "tower_4"};
static const char *const SCENE_NAME[NSCENE] = {
    "A flower meadow", "The city at night", "The Purgatorium's little lights", "The seaside",
    "The angels' clouds",
};
static const char *const SCENE_FOUND[NSCENE] = {
    "a flower meadow", "a bustling city", "the Purgatorium's lights", "the seaside", "the angels' clouds",
};

enum { ST_PLAY, ST_GUST, ST_TOP, ST_OVER };
enum { K_NONE, K_FULL, K_STATIC, K_SLIDE, K_ORBIT, K_CRUMBLE, K_BOUNCE };
enum { L_LEAF, L_STONE, L_DISC, L_WOOD, L_CRACK, L_SHROOM, L_GROUND, L_ROOF };
enum { E_BEETLE, E_CROW, E_FLYER };
enum { F_ACORN, F_TILE, F_STAR };
enum { FS_WARN, FS_FALL };

typedef struct {
    u8 kind, look, heart;
    float u0, hw, amp, spd, ph;   /* slide: u0 + amp sin(ph + spd t); orbit: u0 + spd t */
    float u, du;                  /* now, and how far it moved this frame */
    float crack, gone, squash;
} Plat;

typedef struct {
    float Y;
    int n, path;
    Plat p[SLOTS];
} Row;

typedef struct {
    bool on, dying, blown, pass;   /* pass: Aron is jumping up through it */
    u8 kind;
    int row, slot;            /* walkers: their ledge (absolute row index) */
    float off, dir, spd;      /* walkers: offset along it */
    float bu, bY, amp, w;     /* flyers: patrol */
    float u, Y, t;
} Enemy;

typedef struct {
    bool on;
    u8 kind, st;
    float u, Y, vy, t, warn, sup;   /* sup: the surface it will hit (or -1e9) */
} Fall;

typedef struct {
    float x, y, vx, vy, g, life, max, size;
    u32 c;
    bool scr;   /* screen space (the ending) instead of world (u, Y) */
} Part;

typedef struct {
    char txt[32];
    float t, max, x, y, scale, depth;
    u32 c;
} Pop;

static struct {
    int st, reason;
    float t, st_t, end_t, anim, pt;     /* pt: the platforms' clock */
    /* Aron */
    float u, Y, vx, vy, prevY;
    bool ground, jump_held, boost, hold, skid;
    int on_row, on_slot;
    float coyote, buffer, invuln, knock, walk, step_t;
    int face, hearts, stomps, combo, hurts;
    float best;
    /* camera */
    float cam, camu, floor;
    /* map */
    Row rows[RING];
    int nrows;
    u32 seed;
    float gen_y, gen_u, gen_hw, next_heart;
    int gen_dir;
    u8 gen_prev;
    bool gen_done;
    Enemy en[NEN];
    Fall fall[NFALL];
    float fall_cd;
    int tier, milestone;
    /* the cheat */
    float gust_t, gust_y0, gust_y1, gust_u0, gust_tu;
    bool cheated_top;
    /* the ending */
    bool done;
    int scene;
    float hop_u, hop_Y, flash;
    Part p[NPART];
    Pop pop[NPOP];
    float cloud[14][3];
    float star[24][2];
    float sc[28][4];   /* scenery bits: x, y, size, extra */
} S;

static struct {
    bool cheated, has, hold;
    int tr, ts, te;
    float hop, wait, lt, best, prog_t;
    int vrow[4], vslot[4], vn, lrow, lslot;   /* ledges landed on lately */
    float vt[4];
} B;

/* ---- helpers ---------------------------------------------------------------- */

static float wrapu(float u)
{
    u = fmodf(u, CIRC);
    return u < 0 ? u + CIRC : u;
}

static float wrapd(float d)
{
    d = fmodf(d, CIRC);
    if (d > CIRC * 0.5f)
        d -= CIRC;
    else if (d < -CIRC * 0.5f)
        d += CIRC;
    return d;
}

static float wrapa(float a)
{
    a = fmodf(a, 6.2831853f);
    if (a > 3.14159265f)
        a -= 6.2831853f;
    else if (a < -3.14159265f)
        a += 6.2831853f;
    return a;
}

static float approach(float v, float t, float a) { return v < t ? fminf(v + a, t) : fmaxf(v - a, t); }
static float pitch(int n) { return powf(2.0f, (float)n / 12.0f); }
static int tier_at(float Y)
{
    int t = (int)(Y / TIER_Y);
    return t < 0 ? 0 : t > 3 ? 3 : t;
}

static u32 mix(u32 a, u32 b, float t)
{
    t = clampf(t, 0, 1);
    u32 r = 0;
    for (int s = 0; s < 32; s += 8) {
        float va = (float)((a >> s) & 0xFF), vb = (float)((b >> s) & 0xFF);
        r |= (u32)(va + (vb - va) * t + 0.5f) << s;
    }
    return r;
}

/* The map has its own generator, seeded once per run. */
static u32 mrand(void)
{
    S.seed ^= S.seed << 13;
    S.seed ^= S.seed >> 17;
    S.seed ^= S.seed << 5;
    return S.seed;
}
static float mrandf(void) { return (float)(mrand() >> 8) / 16777216.0f; }
static int mrandi(int lo, int hi) { return hi <= lo ? lo : lo + (int)(mrand() % (u32)(hi - lo + 1)); }

/* ---- projection: (u, Y, radius) to the screen ------------------------------- */

static float sy(float Y) { return ANCH - (Y - S.cam); }
static float tilt(float Y) { return clampf((S.cam + 40 - Y) * TILT_K, -0.45f, 0.45f); }
static float phi(float u) { return wrapd(u - S.camu) / RA; }
static float scx(float r, float a) { return CX + r * sinf(a); }
static float scy(float Y, float r, float a) { return sy(Y) + tilt(Y) * r * cosf(a); }
static float dep(float r, float a) { return 0.22f - 0.42f * (r / RO) * cosf(a); }
static float shade(float a) { return 0.5f + 0.5f * clampf(cosf(a + 0.45f), 0, 1); }

/* ---- platforms ---------------------------------------------------------------- */

static Row *row_at(int i)
{
    if (i < 0 || i >= S.nrows || i < S.nrows - RING)
        return NULL;
    return &S.rows[i % RING];
}

static int first_row(void) { return S.nrows > RING ? S.nrows - RING : 0; }

static bool solid(const Plat *p) { return p->kind != K_NONE && p->gone <= 0; }

static float plat_u_at(const Plat *p, float t)
{
    if (p->kind == K_SLIDE)
        return wrapu(p->u0 + p->amp * sinf(p->ph + p->spd * t));
    if (p->kind == K_ORBIT)
        return wrapu(p->u0 + p->spd * t);
    return p->u0;
}

static bool over(const Plat *p, float u, float pad)
{
    return p->kind == K_FULL || fabsf(wrapd(u - p->u)) <= p->hw + pad;
}

/* Seconds until feet at y, moving up at vy, come down to `top` (-1: never). */
static float fly_time(float y, float vy, float top, bool hold)
{
    float t = 0;
    if (vy > 0) {
        float g = hold ? G_UP : G_CUT;
        t = vy / g;
        y += vy * vy / (2 * g);
        vy = 0;
    }
    if (y < top)
        return -1;
    return t + (vy + sqrtf(vy * vy + 2 * G_FALL * (y - top))) / G_FALL;
}

/* How far sideways a jump of speed v gets to a ledge dy higher. */
static float reach(float v, float dy)
{
    float t = fly_time(0, v, dy, true);
    return t < 0 ? 0 : VMAX * fmaxf(t - 0.1f, 0);
}

static void set_plat(Plat *p, u8 kind, u8 look, float u, float hw)
{
    memset(p, 0, sizeof(*p));
    p->kind = kind;
    p->look = look;
    p->u0 = wrapu(u);
    p->hw = hw;
}

static void make_kind(Plat *p, u8 kind, float u, int tier, float spd)
{
    switch (kind) {
    case K_SLIDE:
        set_plat(p, K_SLIDE, L_WOOD, u, 23 + mrandf() * 8);
        p->amp = 26 + mrandf() * 22;
        p->spd = (0.9f + mrandf() * 0.5f) * fminf(spd, 1.5f);
        p->ph = mrandf() * 6.28f;
        break;
    case K_ORBIT:
        set_plat(p, K_ORBIT, L_DISC, u, 20 + mrandf() * 3);
        break;
    case K_CRUMBLE:
        set_plat(p, K_CRUMBLE, L_CRACK, u, 23 + mrandf() * 10);
        break;
    case K_BOUNCE:
        set_plat(p, K_BOUNCE, L_SHROOM, u, 16 + mrandf() * 4);
        break;
    default: {
        float r = mrandf();
        if (r < 0.5f)
            set_plat(p, K_STATIC, L_LEAF, u, 28 + mrandf() * (16 - 3 * tier));
        else if (r < 0.82f)
            set_plat(p, K_STATIC, L_STONE, u, 21 + mrandf() * 12);
        else
            set_plat(p, K_STATIC, L_DISC, u, 19 + mrandf() * 4);
        break;
    }
    }
    p->u = plat_u_at(p, S.pt);
}

static Enemy *free_enemy(void)
{
    for (int i = 0; i < NEN; i++)
        if (!S.en[i].on) {
            memset(&S.en[i], 0, sizeof(S.en[i]));
            return &S.en[i];
        }
    return NULL;
}

static void spawn_walker(int idx, const Row *r, int tier)
{
    int cand[SLOTS], nc = 0;
    for (int s = 0; s < r->n; s++) {
        const Plat *p = &r->p[s];
        if ((p->kind == K_STATIC || p->kind == K_SLIDE) && p->look != L_DISC && p->hw >= 20)
            cand[nc++] = s;
    }
    Enemy *e = nc ? free_enemy() : NULL;
    if (!e)
        return;
    e->on = true;
    e->kind = tier >= 1 && mrandf() < 0.45f ? E_CROW : E_BEETLE;
    e->row = idx;
    e->slot = cand[mrandi(0, nc - 1)];
    e->off = (mrandf() * 2 - 1) * (r->p[e->slot].hw - 8);
    e->dir = mrand() & 1 ? 1.0f : -1.0f;
    e->spd = (e->kind == E_BEETLE ? 20.0f : 14.0f) * (1 + 0.22f * tier);
    e->u = wrapu(r->p[e->slot].u + e->off);
    e->Y = r->Y;
    e->t = mrandf() * 3;
}

static void spawn_flyer(float Y, float u, int tier)
{
    Enemy *e = free_enemy();
    if (!e)
        return;
    e->on = true;
    e->kind = E_FLYER;
    e->row = -1;
    e->bu = u;
    e->bY = Y;
    e->amp = 30 + mrandf() * 40;
    e->w = (0.8f + 0.3f * tier) * (0.8f + 0.4f * mrandf());
    e->t = mrandf() * 6;
    e->u = u;
    e->Y = Y;
    e->dir = 1;
}

/* One more row of the map, above the last. */
static void gen_row(void)
{
    int idx = S.nrows++;
    Row *r = &S.rows[idx % RING];
    memset(r, 0, sizeof(*r));
    if (idx == 0) {   /* the ground, all around the tower */
        r->n = 1;
        set_plat(&r->p[0], K_FULL, L_GROUND, 0, CIRC);
        S.gen_y = 0;
        S.gen_u = 0;
        S.gen_hw = 40;
        S.gen_prev = K_STATIC;
        S.gen_dir = 1;
        return;
    }
    int tier = tier_at(S.gen_y);
    float h = S.gen_y / TOP_Y, spd = 1 + 0.22f * tier + 0.25f * h;
    bool after_bounce = S.gen_prev == K_BOUNCE;
    bool prev_moving = S.gen_prev == K_SLIDE || S.gen_prev == K_ORBIT;
    if (TOP_Y - S.gen_y <= (after_bounce ? 120 : 60)) {   /* the roof, all around too */
        r->Y = TOP_Y;
        r->n = 1;
        set_plat(&r->p[0], K_FULL, L_ROOF, 0, CIRC);
        S.gen_done = true;
        S.gen_y = TOP_Y;
        return;
    }
    u8 kind = K_STATIC;
    float roll = mrandf();
    float pm = 0.10f + 0.07f * tier + 0.06f * h, pc = 0.03f + 0.05f * tier, pb = 0.07f;
    if (idx >= 3 && !after_bounce) {
        if (roll < pm) {
            if (!prev_moving && S.gen_prev != K_CRUMBLE)
                kind = mrandf() < 0.55f ? K_SLIDE : K_ORBIT;
        } else if (roll < pm + pc) {
            if (S.gen_prev != K_CRUMBLE)
                kind = K_CRUMBLE;
        } else if (roll < pm + pc + pb) {
            kind = K_BOUNCE;
        }
    }
    float dy = after_bounce ? 92 + mrandf() * 30 : 34 + mrandf() * (10 + 5 * tier);
    if (kind == K_SLIDE || kind == K_ORBIT || prev_moving)
        dy = fminf(dy, 44);
    float Y = fminf(S.gen_y + dy, TOP_Y - 30);
    dy = Y - S.gen_y;
    r->Y = Y;

    /* the path platform, within reach of the previous one */
    float rch = reach(after_bounce ? BOUNCE_V : V0, dy) * 0.6f;
    float prev_u = S.gen_u;
    r->path = 0;
    if (kind == K_ORBIT) {   /* three discs: one passes over every spot every few seconds */
        float sp = (50 + mrandf() * 12) * fminf(spd, 1.4f) * (mrand() & 1 ? 1 : -1), ph = mrandf() * CIRC;
        for (int k = 0; k < 3; k++) {
            make_kind(&r->p[k], K_ORBIT, S.gen_u + ph + k * CIRC / 3, tier, spd);
            r->p[k].spd = sp;
            r->p[k].u = plat_u_at(&r->p[k], S.pt);
        }
        r->n = 3;
        S.gen_hw = 20;   /* the next row is placed from where we were */
    } else {
        Plat *p = &r->p[0];
        make_kind(p, kind, 0, tier, spd);
        float maxc = S.gen_hw + rch + p->hw * 0.4f;
        if (mrandf() < 0.22f)
            S.gen_dir = -S.gen_dir;
        p->u0 = wrapu(S.gen_u + S.gen_dir * (0.2f + 0.8f * mrandf()) * maxc);
        p->u = plat_u_at(p, S.pt);
        r->n = 1;
        S.gen_u = p->u0;
        S.gen_hw = p->hw;
        if (Y >= S.next_heart && kind == K_STATIC) {
            p->heart = 1;
            S.next_heart = Y + 650 + mrandf() * 300;
        }
        /* extras: side branches a short hop from the path ledge, so none is a dead end */
        int ne = mrandi(tier < 2 ? 1 : 0, 2);
        for (int e = 0; e < ne && r->n < SLOTS; e++)
            for (int tries = 0; tries < 6; tries++) {
                float x = mrandf();
                u8 k = x < 0.62f ? K_STATIC : x < 0.78f ? K_SLIDE : x < 0.9f ? K_CRUMBLE : K_BOUNCE;
                Plat q;
                make_kind(&q, k, 0, tier, spd);
                const Plat *ref = &r->p[mrandi(0, r->n - 1)];
                float gap = 28 + mrandf() * 26;   /* edge to edge, where a slider comes nearest */
                q.u0 = wrapu(ref->u0 + (mrandf() < 0.5f ? -1 : 1) * (ref->hw + ref->amp + q.hw + q.amp + gap));
                q.u = plat_u_at(&q, S.pt);
                bool ok = true;
                for (int s = 0; s < r->n; s++)
                    if (fabsf(wrapd(q.u0 - r->p[s].u0)) < q.hw + r->p[s].hw + q.amp + r->p[s].amp + 26)
                        ok = false;
                if (ok) {
                    r->p[r->n++] = q;
                    break;
                }
            }
    }
    if (idx >= 4) {
        if (mrandf() < 0.13f + 0.08f * tier + 0.08f * h)
            spawn_walker(idx, r, tier);
        if (tier >= 1 && mrandf() < 0.04f + 0.07f * tier)
            spawn_flyer(S.gen_y + dy * 0.5f + 4, wrapu(prev_u + (mrandf() * 2 - 1) * 50), tier);
    }
    S.gen_y = Y;
    S.gen_prev = kind;
}

static void gen_ahead(float y)
{
    while (!S.gen_done && (S.nrows == 0 || S.gen_y < y))
        gen_row();
}

/* ---- effects ---------------------------------------------------------------- */

static void burst(float x, float y, bool scr, int n, u32 c, float speed)
{
    for (int i = 0, k = 0; i < NPART && k < n; i++) {
        Part *p = &S.p[i];
        if (p->life > 0)
            continue;
        float a = mg_randf() * 6.2832f, v = speed * (0.4f + 0.6f * mg_randf());
        p->x = x;
        p->y = y;
        p->vx = cosf(a) * v;
        p->vy = sinf(a) * v * (scr ? -1 : 1) + (scr ? -speed * 0.5f : speed * 0.5f);
        p->g = scr ? 260 : -260;
        p->max = p->life = 0.5f + 0.6f * mg_randf();
        p->size = 1.5f + 2.0f * mg_randf();
        p->c = c;
        if (c == 0) {   /* confetti */
            static const u32 CONF[5] = {RGBA(255, 120, 120, 255), RGBA(255, 220, 110, 255),
                                         RGBA(120, 220, 255, 255), RGBA(170, 255, 140, 255),
                                         RGBA(240, 150, 255, 255)};
            p->c = CONF[mg_randi(0, 4)];
            p->max = p->life = 1.4f + mg_randf();
        }
        p->scr = scr;
        k++;
    }
}

static void popup(const char *txt, float x, float y, float scale, u32 c, float depth, float dur)
{
    int best = 0;
    for (int i = 1; i < NPOP; i++)
        if (S.pop[i].t < S.pop[best].t)
            best = i;
    Pop *p = &S.pop[best];
    snprintf(p->txt, sizeof(p->txt), "%s", txt);
    p->t = p->max = dur;
    p->x = clampf(x, 50, TOP_W - 50);
    p->y = clampf(y, 30, TOP_H - 40);
    p->scale = scale;
    p->c = c;
    p->depth = depth;
}

/* ---- the run ------------------------------------------------------------------- */

static void start(u32 seed)
{
    memset(&S, 0, sizeof(S));
    memset(&B, 0, sizeof(B));
    B.te = -1;
    B.lrow = -1;
    for (int k = 0; k < 4; k++)
        B.vrow[k] = -1;
    S.seed = seed ? seed : 0x2545F491u;
    S.face = 1;
    S.hearts = 3;
    S.ground = true;
    S.cam = 22;
    S.next_heart = 900;
    S.fall_cd = 3;
    S.gen_dir = 1;
    for (int i = 0; i < 14; i++) {
        S.cloud[i][0] = mg_randf() * 480;
        S.cloud[i][1] = mg_randf() * 330;
        S.cloud[i][2] = 8 + mg_randf() * 9;
    }
    for (int i = 0; i < 24; i++) {
        S.star[i][0] = mg_randf() * 420;
        S.star[i][1] = mg_randf() * 250;
    }
    for (int i = 0; i < 28; i++)
        for (int k = 0; k < 4; k++)
            S.sc[i][k] = mg_randf();
    S.scene = mg_randi(0, NSCENE - 1);
    gen_ahead(S.cam + 430);
}

static void set_tier(int t)
{
    S.tier = t;
    mg_music(MUSIC[t]);
    mg_sfx("tower_faster");
    popup(t == 2 ? "Faster!" : "Higher!", CX, 60, 1.1f, RGBA(255, 190, 90, 255), -0.45f, 1.4f);
}

static void game_over(int reason)
{
    S.st = ST_OVER;
    S.st_t = 0;
    S.reason = reason;
    S.end_t = S.t;
    S.ground = false;
    static const char *const SFX[3] = {"tower_fall", "tower_ko", "tower_timeout"};
    static const char *const TXT[3] = {"Too far down!", "Out of hearts!", "Time's up!"};
    mg_sfx(SFX[reason]);
    popup(TXT[reason], CX, 90, 1.0f, RGBA(255, 150, 130, 255), -0.4f, OVER_T);
    if (reason == 1) {   /* knocked out: a little flip off the ledge */
        S.vy = 300;
        S.vx = S.face * -40.0f;
    }
}

static void start_top(void)
{
    S.st = ST_TOP;
    S.st_t = 0;
    S.done = true;
    S.end_t = S.t;
    S.best = TOP_Y;
    S.hop_u = S.u;
    S.hop_Y = S.Y;
    S.ground = true;
    for (int i = 0; i < NFALL; i++)
        S.fall[i].on = false;
    for (int i = 0; i < NEN; i++)
        S.en[i].on = false;
    mg_sfx("tower_summit");
}

/* dir: knocked that way (an enemy), or 0 (something fell on him: no knockback) */
static void hurt(float dir)
{
    if (S.invuln > 0 || S.st != ST_PLAY)
        return;
    S.hearts--;
    S.hurts++;
    S.invuln = 1.5f;
    if (dir != 0) {
        S.knock = 0.22f;
        S.vx = dir * 120;
        S.vy = 200;
        S.ground = false;
        S.jump_held = S.boost = false;
    }
    mg_sfx("tower_hurt");
    burst(S.u, S.Y + 10, false, 10, RGBA(255, 110, 120, 255), 80);
    if (S.hearts <= 0)
        game_over(1);
}

static void pickup_heart(Plat *p, const Row *r)
{
    p->heart = 0;
    burst(p->u, r->Y + 14, false, 12, RGBA(255, 120, 150, 255), 70);
    if (S.hearts < 3) {
        S.hearts++;
        mg_sfx("tower_heart");
        popup("+1 heart", CX, 110, 0.6f, RGBA(255, 140, 170, 255), -0.3f, 1.0f);
    } else {
        mg_sfx_pitch("tower_heart", 1.25f);
    }
}

static void land(int idx, int slot)
{
    Row *r = &S.rows[idx % RING];
    Plat *p = &r->p[slot];
    S.Y = r->Y;
    S.vy = 0;
    S.on_row = idx;
    S.on_slot = slot;
    S.combo = 0;
    if (p->kind == K_BOUNCE) {
        S.ground = false;
        S.vy = BOUNCE_V * (S.hold ? 1.06f : 1.0f);
        S.boost = true;
        S.jump_held = S.hold;
        p->squash = 0.3f;
        mg_sfx_pitch("tower_bounce", 0.95f + 0.1f * mg_randf());
        burst(S.u, S.Y, false, 8, RGBA(255, 200, 200, 255), 70);
        if (r->Y > S.best)
            S.best = r->Y;
        return;
    }
    S.ground = true;
    S.boost = false;
    if (r->Y > S.best)
        S.best = r->Y;
    if (p->kind == K_FULL && p->look == L_ROOF) {
        start_top();
        return;
    }
    mg_sfx_pitch("tower_land", pitch(S.tier * 2));
    burst(S.u, S.Y, false, 5, p->look == L_LEAF || p->look == L_DISC ? RGBA(170, 240, 150, 255)
                                                                       : RGBA(220, 210, 200, 255), 40);
    if (p->kind == K_CRUMBLE && p->crack <= 0) {
        p->crack = CRACK_T;
        mg_sfx("tower_crack");
    }
}

static void try_land(void)
{
    int bi = -1, bs = -1;
    for (int i = S.nrows - 1; i >= first_row(); i--) {
        const Row *r = &S.rows[i % RING];
        if (r->Y > S.prevY + 0.01f || r->Y < S.Y || (bi >= 0 && r->Y <= S.rows[bi % RING].Y))
            continue;
        for (int s = 0; s < r->n; s++)
            if (solid(&r->p[s]) && over(&r->p[s], S.u, AW * 0.6f)) {
                bi = i;
                bs = s;
                break;
            }
    }
    if (bi >= 0)
        land(bi, bs);
}

static void do_gust(void)
{
    if (S.st != ST_PLAY)
        return;
    S.st = ST_GUST;
    S.gust_t = 0;
    S.gust_y0 = S.Y;
    S.gust_u0 = S.u;
    float y1 = S.Y + TIER_Y;
    if (y1 > TOP_Y - 60)
        y1 = TOP_Y + 30;
    gen_ahead(y1 + 80);
    /* set him down on a solid ledge just under the destination */
    S.gust_tu = S.u;
    S.gust_y1 = y1;
    for (int i = S.nrows - 1; i >= first_row(); i--) {
        Row *r = &S.rows[i % RING];
        if (r->Y > y1 - 6)
            continue;
        int s = r->path;   /* the path's ledges lead on; a static one is a safe landing */
        if (r->p[s].kind != K_FULL && r->p[s].kind != K_STATIC)
            continue;
        S.gust_y1 = r->Y + 26;
        S.gust_tu = r->p[s].kind == K_FULL ? S.u : r->p[s].u;
        break;
    }
    S.vx = S.vy = 0;
    S.ground = false;
    S.jump_held = S.boost = false;
    S.knock = 0;
    for (int i = 0; i < NEN; i++) {   /* blown away */
        Enemy *e = &S.en[i];
        if (e->on && !e->dying && e->Y > S.Y - 160 && e->Y < y1 + 200) {
            e->dying = e->blown = true;
            e->t = 0;
        }
    }
    for (int i = 0; i < NFALL; i++)
        if (S.fall[i].on) {
            S.fall[i].on = false;
            burst(S.fall[i].u, fminf(S.fall[i].Y, S.cam + 140), false, 4, RGBA(220, 240, 255, 255), 60);
        }
    S.fall_cd = 3;
    mg_sfx("tower_gust");
    popup("Updraft!", CX, 70, 1.0f, RGBA(200, 230, 255, 255), -0.4f, 1.4f);
    burst(S.u, S.Y + 6, false, 14, RGBA(220, 240, 255, 255), 90);
}

static void update_gust(float dt)
{
    S.gust_t += dt;
    float p = clampf(S.gust_t / GUST_T, 0, 1), e = p * p * (3 - 2 * p);
    S.prevY = S.Y;
    S.Y = lerpf(S.gust_y0, S.gust_y1, e);
    S.u = wrapu(S.gust_u0 + wrapd(S.gust_tu - S.gust_u0) * e);
    S.walk += dt * 10;
    if (p >= 1) {
        S.st = ST_PLAY;
        S.vy = 0;
        S.invuln = 1.6f;
        S.prevY = S.Y;
        S.floor = fmaxf(S.floor, S.Y - 100);
    }
}

static void update_aron(const Input *in, float dt)
{
    float mv = in->cx;
    if (fabsf(mv) < 0.25f)
        mv = 0;
    if (in->held & KEY_LEFT_)
        mv = -1;
    if (in->held & KEY_RIGHT_)
        mv = 1;
    bool press = (in->down & (KEY_A_ | KEY_B_)) != 0;
    S.hold = (in->held & (KEY_A_ | KEY_B_)) != 0;
    if (S.knock > 0) {
        S.knock -= dt;
        mv = 0;
    }
    if (mv)
        S.face = mv > 0 ? 1 : -1;

    /* running: Mario-like acceleration, skids and friction */
    if (S.ground) {
        if (mv) {
            bool turning = S.vx * mv < 0;
            if (turning && fabsf(S.vx) > 70 && !S.skid) {
                S.skid = true;
                mg_sfx("tower_skid");
                burst(S.u, S.Y + 1, false, 3, RGBA(230, 220, 210, 255), 30);
            }
            if (!turning)
                S.skid = false;
            S.vx = approach(S.vx, mv * VMAX, (turning ? TURN : ACC) * dt);
        } else {
            S.vx = approach(S.vx, 0, FRIC * dt);
        }
    } else {
        S.vx = approach(S.vx, mv * VMAX, (mv ? ACC_AIR : 120) * dt);
    }
    S.u = wrapu(S.u + S.vx * dt);

    /* riding a platform; walking off it */
    if (S.ground) {
        Row *r = row_at(S.on_row);
        Plat *p = r ? &r->p[S.on_slot] : NULL;
        if (p && solid(p) && p->kind != K_FULL)
            S.u = wrapu(S.u + p->du);
        if (!p || !solid(p) || !over(p, S.u, AW * 0.6f)) {
            S.ground = false;
            S.vy = 0;
        } else {
            S.Y = r->Y;
        }
    }

    /* jumping: buffered presses and coyote time */
    S.buffer = press ? BUFFER : S.buffer - dt;
    if (!S.hold)
        S.jump_held = false;
    S.coyote = S.ground ? COYOTE : S.coyote - dt;
    if (S.buffer > 0 && S.coyote > 0 && S.knock <= 0) {
        S.vy = V0 + fabsf(S.vx) * 0.12f;
        S.ground = false;
        S.coyote = S.buffer = 0;
        S.jump_held = true;
        S.boost = false;
        S.skid = false;
        mg_sfx_pitch("tower_jump", 0.96f + 0.08f * mg_randf());
        burst(S.u, S.Y, false, 3, RGBA(230, 220, 210, 255), 30);
    }

    S.prevY = S.Y;
    if (S.ground) {
        float sp = fabsf(S.vx);
        if (sp > 25) {
            S.walk += sp * dt * 0.13f;
            S.step_t -= dt;
            if (S.step_t <= 0) {
                mg_sfx("tower_step");
                S.step_t = 0.22f;
            }
        } else {
            S.walk = 0;
            S.step_t = 0;
        }
    } else {
        float g = S.vy > 0 ? (S.jump_held || S.boost ? G_UP : G_CUT) : G_FALL;
        S.vy = fmaxf(S.vy - g * dt, -VTERM);
        if (S.vy <= 0)
            S.boost = false;
        S.Y += S.vy * dt;
        if (S.vy <= 0)
            try_land();
    }

    /* hearts float over their ledges */
    for (int i = first_row(); i < S.nrows; i++) {
        Row *r = &S.rows[i % RING];
        if (fabsf(r->Y - S.Y) > 30)
            continue;
        for (int s = 0; s < r->n; s++) {
            Plat *p = &r->p[s];
            if (p->heart && S.Y >= r->Y - 2 && S.Y < r->Y + 24 && fabsf(wrapd(p->u - S.u)) < 10)
                pickup_heart(p, r);
        }
    }
}

static void update_plats(float dt)
{
    S.pt += dt;
    for (int i = first_row(); i < S.nrows; i++) {
        Row *r = &S.rows[i % RING];
        for (int s = 0; s < r->n; s++) {
            Plat *p = &r->p[s];
            if (p->kind == K_FULL)
                continue;
            float nu = plat_u_at(p, S.pt);
            p->du = wrapd(nu - p->u);
            p->u = nu;
            if (p->squash > 0)
                p->squash -= dt;
            if (p->crack > 0) {
                p->crack -= dt;
                if (p->crack <= 0) {
                    p->crack = 0;
                    p->gone = GONE_T;
                    mg_sfx("tower_crumble");
                    burst(p->u, r->Y - 4, false, 10, RGBA(150, 132, 120, 255), 60);
                }
            } else if (p->gone > 0) {
                p->gone = fmaxf(p->gone - dt, 0);
            }
        }
    }
}

static void stomp(Enemy *e)
{
    e->dying = true;
    e->t = 0;
    S.stomps++;
    S.combo++;
    S.vy = S.hold ? STOMP_VH : STOMP_V;
    S.jump_held = S.hold;
    S.boost = false;
    S.ground = false;
    mg_sfx_pitch("tower_stomp", pitch(S.combo > 8 ? 7 : S.combo - 1));
    burst(e->u, e->Y + 6, false, 10, e->kind == E_BEETLE ? RGBA(150, 110, 230, 255) : RGBA(80, 76, 96, 255), 70);
    char buf[16];
    if (S.combo > 1)
        snprintf(buf, sizeof(buf), "x%d!", S.combo);
    else
        snprintf(buf, sizeof(buf), "Stomp!");
    float a = phi(e->u);
    popup(buf, scx(RA, a), scy(e->Y, RA, a) - 26, 0.6f, MG_GOLD, -0.3f, 0.8f);
}

static void update_enemies(float dt)
{
    for (int i = 0; i < NEN; i++) {
        Enemy *e = &S.en[i];
        if (!e->on)
            continue;
        e->t += dt;
        if (e->dying) {
            if (e->blown) {
                e->Y += 160 * dt;
                e->u = wrapu(e->u + 60 * dt);
            }
            if (e->t > 0.5f)
                e->on = false;
            continue;
        }
        if (e->kind == E_FLYER) {
            e->u = wrapu(e->bu + e->amp * sinf(e->t * e->w));
            e->Y = e->bY + 5 * sinf(e->t * 2.3f);
            e->dir = cosf(e->t * e->w) >= 0 ? 1.0f : -1.0f;
        } else {
            Row *r = row_at(e->row);
            if (!r || !solid(&r->p[e->slot])) {   /* its ledge is gone */
                if (r)
                    burst(e->u, e->Y + 4, false, 6, RGBA(150, 110, 230, 255), 50);
                e->on = false;
                continue;
            }
            Plat *p = &r->p[e->slot];
            e->off += e->dir * e->spd * dt;
            float lim = p->hw - 6;
            if (e->off > lim) {
                e->off = lim;
                e->dir = -1;
            } else if (e->off < -lim) {
                e->off = -lim;
                e->dir = 1;
            }
            e->u = wrapu(p->u + e->off);
            float hy = 0;
            if (e->kind == E_CROW) {   /* grumpy little hops */
                float c = fmodf(e->t, 2.6f);
                if (c < 0.4f)
                    hy = sinf(c / 0.4f * 3.14159f) * 9;
            }
            e->Y = r->Y + hy;
        }
        if (e->Y < S.cam - 220) {
            e->on = false;
            continue;
        }
        if (S.st != ST_PLAY)
            continue;
        float du = wrapd(e->u - S.u);
        float ew = e->kind == E_BEETLE ? 8 : 9, eh = e->kind == E_BEETLE ? 10 : 12;
        bool touch = fabsf(du) < ew + AW - 2 && S.Y < e->Y + eh && S.Y + AH - 4 > e->Y;
        if (!touch) {
            e->pass = false;
        } else if (S.vy > 0 && S.prevY + AH - 4 <= e->Y + 3) {   /* from below: jump up past it */
            e->pass = true;
        } else if (!e->pass) {
            if ((S.vy < 0 || S.prevY > S.Y + 0.01f) && S.prevY >= e->Y + eh * 0.45f) {
                stomp(e);
            }
            else {
                hurt(du > 0 ? -1.0f : 1.0f);
            }
        }
    }
}

/* The highest solid surface at u at or below height y. */
static float support_below(float u, float y)
{
    float best = -1e9f;
    for (int i = first_row(); i < S.nrows; i++) {
        const Row *r = &S.rows[i % RING];
        if (r->Y > y || r->Y <= best)
            continue;
        for (int s = 0; s < r->n; s++)
            if (solid(&r->p[s]) && over(&r->p[s], u, 0))
                best = r->Y;
    }
    return best;
}

static void spawn_fall(void)
{
    static const float CD[4] = {4.2f, 3.0f, 2.2f, 1.6f};
    float h = S.best / TOP_Y;
    S.fall_cd = CD[S.tier] * (0.75f + 0.5f * mg_randf()) * (1.1f - 0.2f * h);
    Fall *f = NULL;
    for (int i = 0; i < NFALL && !f; i++)
        if (!S.fall[i].on)
            f = &S.fall[i];
    if (!f)
        return;
    memset(f, 0, sizeof(*f));
    float x = mg_randf();
    u8 k = S.tier == 0   ? F_ACORN
           : S.tier == 1 ? (x < 0.5f ? F_ACORN : F_TILE)
           : S.tier == 2 ? (x < 0.3f ? F_ACORN : x < 0.7f ? F_TILE : F_STAR)
                         : (x < 0.45f ? F_TILE : F_STAR);
    f->on = true;
    f->kind = k;
    f->st = FS_WARN;
    f->u = wrapu(S.u + (mg_randf() < 0.45f ? S.vx * 0.9f : (mg_randf() * 2 - 1) * 110));
    f->Y = S.cam + 178;
    f->vy = k == F_STAR ? -240.0f : -30.0f;
    f->warn = 1.0f - 0.1f * S.tier;
    f->sup = support_below(f->u, f->Y);
    mg_sfx_pitch("tower_falling_warn", k == F_STAR ? 1.2f : 1.0f);
}

static void update_falls(float dt)
{
    if (S.st == ST_PLAY && S.best > 160) {
        S.fall_cd -= dt;
        if (S.fall_cd <= 0)
            spawn_fall();
    }
    static const float PITCH[3] = {1.2f, 0.85f, 1.5f};
    static const u32 COL[3] = {RGBA(170, 110, 60, 255), RGBA(200, 90, 70, 255), RGBA(255, 230, 120, 255)};
    for (int i = 0; i < NFALL; i++) {
        Fall *f = &S.fall[i];
        if (!f->on)
            continue;
        f->t += dt;
        if (f->st == FS_WARN) {   /* waits just above the screen */
            f->Y = S.cam + 178;
            f->sup = support_below(f->u, f->Y);
            if (f->t >= f->warn) {
                f->st = FS_FALL;
                f->t = 0;
            }
            continue;
        }
        f->sup = support_below(f->u, f->Y);
        if (f->kind != F_STAR)
            f->vy = fmaxf(f->vy - (f->kind == F_ACORN ? 520 : 480) * dt, -380);
        if (f->kind == F_TILE)
            f->u = wrapu(f->u + sinf(f->t * 4) * 25 * dt);
        f->Y += f->vy * dt;
        if (S.st == ST_PLAY && fabsf(wrapd(f->u - S.u)) < 8 && f->Y < S.Y + AH && f->Y + 6 > S.Y) {
            mg_sfx_pitch("tower_falling_hit", PITCH[f->kind]);
            burst(f->u, f->Y, false, 8, COL[f->kind], 70);
            hurt(0);
            f->on = false;
            continue;
        }
        if (f->Y <= f->sup) {
            mg_sfx_pitch("tower_falling_hit", PITCH[f->kind]);
            burst(f->u, f->sup + 2, false, 8, COL[f->kind], 70);
            f->on = false;
            continue;
        }
        if (f->Y < S.cam - 130)
            f->on = false;
    }
}

static bool update_top(float dt)
{
    float prev = S.st_t;
    S.st_t += dt;
    S.cam += (TOP_Y + 40 - S.cam) * clampf(dt * 4, 0, 1);
#define CROSS(T) (prev < (T) && S.st_t >= (T))
    if (CROSS(0.02f))
        mg_sfx("tower_jump");
    if (CROSS(0.8f))
        mg_sfx("tower_enter_hole");
    if (CROSS(1.1f))
        S.flash = 0.5f;
    if (CROSS(1.5f)) {
        mg_sfx("tower_pop_out");
        S.face = 1;
    }
    if (CROSS(2.5f)) {
        mg_sfx("tower_win");
        burst(290, 200, true, 50, 0, 170);
        popup("Top of the Tower!", CX, 34, 0.95f, MG_GOLD, -0.4f, 2.6f);
    }
    if (CROSS(3.3f) || CROSS(4.1f)) {
        mg_sfx("tower_cheer");
        burst(290, 190, true, 18, 0, 120);
    }
#undef CROSS
    return S.st_t < TOP_END;
}

static void update_camera(float dt)
{
    S.floor = fmaxf(S.floor, S.best - 140);
    if (S.t > 6 && S.st == ST_PLAY)   /* the mist rises */
        S.floor = fminf(S.floor + (3 + 2.5f * S.tier) * dt, fmaxf(S.floor, S.best + 150));
    float tgt = S.Y + 22 + clampf(S.vy * 0.06f, -10, 26);
    if (tgt < S.floor)
        tgt = S.floor;
    if (tgt > TOP_Y + 60)
        tgt = TOP_Y + 60;
    S.cam += (tgt - S.cam) * clampf(dt * (S.st == ST_GUST || S.vy < -250 ? 8.0f : 4.5f), 0, 1);
    float lead = clampf(S.vx * 0.22f, -28, 28);
    S.camu = wrapu(S.camu + wrapd(S.u + lead - S.camu) * clampf(dt * 5, 0, 1));
}

static bool update(const Input *in, float dt, bool cheat)
{
    if (dt > 0.05f)
        dt = 0.05f;
    S.anim += dt;
    S.flash = S.flash > 0 ? S.flash - dt : 0;
    for (int i = 0; i < NPART; i++) {
        Part *p = &S.p[i];
        if (p->life <= 0)
            continue;
        p->life -= dt;
        p->vy += p->g * dt;
        p->x += p->vx * dt;
        p->y += p->vy * dt;
    }
    for (int i = 0; i < NPOP; i++)
        S.pop[i].t -= dt;
    if (S.invuln > 0)
        S.invuln -= dt;

    if (S.st == ST_TOP)
        return update_top(dt);
    if (S.st == ST_OVER) {
        S.st_t += dt;
        S.vy = fmaxf(S.vy - G_FALL * dt, -VTERM);
        S.Y += S.vy * dt;
        S.u = wrapu(S.u + S.vx * dt);
        update_plats(dt);
        update_enemies(dt);
        return S.st_t < OVER_T;
    }

    S.t += dt;
    if (cheat)
        do_gust();
    if (S.t >= TIME_CAP && S.st == ST_PLAY) {
        game_over(2);
        return true;
    }
    update_plats(dt);
    gen_ahead(S.cam + 430);
    if (S.st == ST_GUST)
        update_gust(dt);
    else
        update_aron(in, dt);
    if (S.st == ST_TOP)
        return true;
    update_enemies(dt);
    update_falls(dt);
    if (S.st == ST_OVER)
        return true;

    int t = tier_at(S.best);
    if (t > S.tier)
        set_tier(t);
    int m = (int)(S.best / 500);
    if (m > S.milestone) {
        S.milestone = m;
        char buf[16];
        snprintf(buf, sizeof(buf), "%d m", m * 50);
        popup(buf, CX, 100, 0.7f, MG_WHITE, -0.3f, 1.2f);
        mg_sfx("tower_milestone");
    }
    update_camera(dt);
    if (S.st == ST_PLAY && S.Y < S.cam - 110 && S.Y < S.floor - 110)
        game_over(0);
    return true;
}

/* ---- drawing: shapes ----------------------------------------------------------- */

static void quad(int eye, float x0, float y0, float x1, float y1, float x2, float y2, float x3, float y3,
                 float d, u32 c)
{
    mg_tri(eye, x0, y0, x1, y1, x2, y2, d, c);
    mg_tri(eye, x0, y0, x2, y2, x3, y3, d, c);
}

static void fill_ellipse(int eye, float x, float y, float rx, float ry, int n, float depth, u32 c)
{
    float px = x + rx, py = y;
    for (int i = 1; i <= n; i++) {
        float a = 6.2832f * i / n;
        float qx = x + rx * cosf(a), qy = y + ry * sinf(a);
        mg_tri(eye, x, y, px, py, qx, qy, depth, c);
        px = qx;
        py = qy;
    }
}

/* A pointed oval, leaf-like, in four triangles. */
static void leafhex(int eye, float x, float y, float rx, float ry, float d, u32 c)
{
    float k = rx * 0.45f;
    mg_tri(eye, x - rx, y, x - k, y - ry, x - k, y + ry, d, c);
    mg_tri(eye, x - k, y - ry, x + k, y - ry, x + k, y + ry, d, c);
    mg_tri(eye, x - k, y - ry, x + k, y + ry, x - k, y + ry, d, c);
    mg_tri(eye, x + k, y - ry, x + rx, y, x + k, y + ry, d, c);
}

static void heart_mg(int eye, float x, float y, float s, float d, u32 c)
{
    mg_circle(eye, x - s * 0.5f, y, s * 0.58f, d, c);
    mg_circle(eye, x + s * 0.5f, y, s * 0.58f, d, c);
    mg_tri(eye, x - s * 1.05f, y + s * 0.15f, x + s * 1.05f, y + s * 0.15f, x, y + s * 1.25f, d, c);
}

/* Tiny Aron. pose: 0 stand/walk, 1 air, 2 hurt, 3 cheer */
static void draw_aron(int eye, float x, float y, float depth, float s, float alpha, int pose)
{
    u32 jeans = rgba_alpha(RGBA(46, 56, 100, 255), alpha);
    u32 shirt = rgba_alpha(RGBA(58, 156, 170, 255), alpha);
    u32 skin = rgba_alpha(RGBA(246, 206, 172, 255), alpha);
    u32 hair = rgba_alpha(RGBA(78, 50, 34, 255), alpha);
    float f = (float)S.face;
    float sw = pose == 0 ? sinf(S.walk) * 2.2f * s : 0;
    if (pose == 1) {   /* tucked legs */
        mg_line(eye, x - 1.6f * s, y - 7 * s, x - 2.8f * s, y - 2 * s, 2.0f * s, depth, jeans);
        mg_line(eye, x + 1.6f * s, y - 7 * s, x + 2.6f * s, y - 3 * s, 2.0f * s, depth, jeans);
    } else {
        mg_line(eye, x - 1.5f * s, y - 7 * s, x - 1.5f * s - sw, y, 2.0f * s, depth, jeans);
        mg_line(eye, x + 1.5f * s, y - 7 * s, x + 1.5f * s + sw, y, 2.0f * s, depth, jeans);
    }
    mg_rect(eye, x - 3.2f * s, y - 13 * s, 6.4f * s, 7 * s, depth, shirt);
    if (pose == 1 || pose == 3) {   /* arms up */
        float w = pose == 3 ? sinf(S.anim * 14) * 1.5f * s : 0;
        mg_line(eye, x - 3 * s, y - 12 * s, x - 5.5f * s + w, y - 17 * s, 1.6f * s, depth, skin);
        mg_line(eye, x + 3 * s, y - 12 * s, x + 5.5f * s - w, y - 17 * s, 1.6f * s, depth, skin);
    } else {
        mg_line(eye, x - 3 * s, y - 12 * s, x - 4 * s - sw * 0.5f, y - 7 * s, 1.6f * s, depth, shirt);
        mg_line(eye, x + 3 * s, y - 12 * s, x + 4 * s + sw * 0.5f, y - 7 * s, 1.6f * s, depth, shirt);
    }
    mg_circle(eye, x, y - 16.5f * s, 3.7f * s, depth, skin);
    mg_circle(eye, x - f * 0.8f * s, y - 18.4f * s, 3.0f * s, depth, hair);
    mg_rect(eye, x + f * 1.6f * s - 0.6f * s, y - 16.6f * s, 1.2f * s, 1.3f * s, depth,
            rgba_alpha(MG_INK, alpha));
    if (pose == 2) {   /* dizzy stars */
        for (int i = 0; i < 3; i++) {
            float a = S.anim * 8 + i * 2.1f;
            mg_rect(eye, x + cosf(a) * 6 * s - 1, y - 23 * s + sinf(a) * 2, 2, 2, depth - 0.05f,
                    rgba_alpha(MG_GOLD, alpha));
        }
    }
}

static void draw_cat(int eye, float x, float y, float depth)
{
    u32 c = RGBA(60, 54, 64, 255);
    mg_circle(eye, x, y - 5, 5.5f, depth, c);
    mg_circle(eye, x + 4, y - 12, 4, depth, c);
    mg_tri(eye, x + 1, y - 14, x + 2.5f, y - 19, x + 4.5f, y - 15, depth, c);
    mg_tri(eye, x + 4, y - 15, x + 6.5f, y - 19, x + 7.5f, y - 13, depth, c);
    mg_line(eye, x - 5, y - 2, x - 10, y - 8 + sinf(S.anim * 2) * 2, 1.8f, depth, c);
    mg_rect(eye, x + 5, y - 13, 1.2f, 1.2f, depth - 0.01f, RGBA(240, 220, 120, 255));
}

static void draw_beetle(int eye, float x, float y, float d, float f, float sq, float al, int seed)
{
    u32 shell = rgba_alpha(RGBA(104, 64, 170, 255), al), dark = rgba_alpha(RGBA(40, 24, 70, 255), al);
    float leg = sinf(S.anim * 18 + seed) * 1.5f;
    mg_line(eye, x - 5, y - 2, x - 7 - leg, y, 1.4f, d + 0.01f, dark);
    mg_line(eye, x + 5, y - 2, x + 7 + leg, y, 1.4f, d + 0.01f, dark);
    if (sq < 1) {
        mg_rect(eye, x - 7, y - 5 * sq - 1, 14, 5 * sq + 1, d, shell);
        return;
    }
    mg_circle(eye, x, y - 5, 6.5f, d, shell);
    mg_line(eye, x - f * 1, y - 11, x - f * 1, y - 1, 1, d - 0.01f, dark);
    mg_circle(eye, x + f * 6, y - 4, 3.2f, d - 0.005f, dark);
    mg_rect(eye, x + f * 7 - 0.8f, y - 5.5f, 1.6f, 1.6f, d - 0.02f, rgba_alpha(RGBA(255, 70, 90, 255), al));
    int g = ((int)(S.anim * 14) + seed * 7) % 5;   /* glitch slices */
    if (g < 2)
        mg_rect(eye, x - 7 + g * 3, y - 8 + g * 3, 9, 2, d - 0.02f,
                rgba_alpha(g ? RGBA(80, 255, 230, 200) : RGBA(255, 60, 220, 200), al));
}

static void draw_crow(int eye, float x, float y, float d, float f, float sq, float al, bool fly)
{
    u32 body = rgba_alpha(RGBA(40, 38, 52, 255), al), beak = rgba_alpha(RGBA(250, 170, 60, 255), al);
    if (sq < 1) {
        mg_rect(eye, x - 8, y - 5 * sq - 1, 16, 5 * sq + 1, d, body);
        return;
    }
    mg_circle(eye, x, y - 6, 6.5f, d, body);
    mg_tri(eye, x - f * 5, y - 7, x - f * 12, y - 10, x - f * 11, y - 4, d + 0.005f, body);
    mg_circle(eye, x + f * 5, y - 12, 4.3f, d - 0.005f, body);
    mg_tri(eye, x + f * 8.5f, y - 13.5f, x + f * 8.5f, y - 10.5f, x + f * 13, y - 12, d - 0.01f, beak);
    mg_rect(eye, x + f * 6 - 0.8f, y - 13.5f, 1.8f, 1.8f, d - 0.015f, rgba_alpha(MG_WHITE, al));
    mg_line(eye, x + f * 4, y - 16, x + f * 8.5f, y - 14.2f, 1.3f, d - 0.02f, rgba_alpha(RGBA(20, 16, 24, 255), al));
    float fl = fly ? sinf(S.anim * 16) * 6 : 1.5f;
    mg_tri(eye, x - 3, y - 8, x + 4, y - 8, x - f * 2, y - 12 - fl, d - 0.01f, rgba_alpha(RGBA(70, 66, 88, 255), al));
}

/* ---- drawing: the world ------------------------------------------------------------ */

static void draw_bg(int eye)
{
    static const u32 TOPC[4] = {RGBA(96, 160, 226, 255), RGBA(104, 128, 206, 255), RGBA(60, 50, 120, 255),
                                RGBA(16, 16, 44, 255)};
    static const u32 BOTC[4] = {RGBA(200, 228, 246, 255), RGBA(250, 212, 172, 255), RGBA(236, 140, 120, 255),
                                RGBA(62, 44, 104, 255)};
    float h = clampf(S.cam / TOP_Y, 0, 1) * 3;
    int i = (int)h;
    if (i > 2)
        i = 2;
    float f = h - i;
    u32 top = mix(TOPC[i], TOPC[i + 1], f);
    mg_sky(eye, top, mix(BOTC[i], BOTC[i + 1], f));
    float rot = S.camu / RA;   /* the camera turns around the tower: far things slide the other way */
    float night = clampf(h - 1.6f, 0, 1);
    if (night > 0)
        for (int s = 0; s < 24; s++) {
            float x = fmodf(S.star[s][0] + rot * 60 + 4200, 420) - 10;
            float y = fmodf(S.star[s][1] + S.cam * 0.05f, 250) - 5;
            float tw = 0.6f + 0.4f * sinf(S.anim * 2 + s);
            mg_rect(eye, x, y, 1.5f, 1.5f, 1.0f, rgba_alpha(MG_WHITE, night * tw));
        }
    float sx = fmodf(310 + rot * 55 + 4800, 480) - 40, syy = 46 + h * 10;
    if (night < 0.5f) {
        mg_circle(eye, sx, syy, 26, 0.98f, RGBA(255, 236, 170, 60));
        mg_circle(eye, sx, syy, 18, 0.98f, RGBA(255, 236, 170, 255));
    } else {
        mg_circle(eye, sx, syy, 14, 0.98f, RGBA(240, 236, 210, 255));
        mg_circle(eye, sx + 6, syy - 4, 12, 0.98f, top);
    }
    /* far mountains and near hills sink as Aron climbs */
    float base = 215 + S.cam * 0.12f;
    if (base < TOP_H + 70) {
        u32 mc = mix(RGBA(120, 150, 190, 255), top, 0.3f);
        for (int k = 0; k < 5; k++) {
            float x = fmodf(k * 110 + rot * 45 + 5500, 550) - 75, ph = 55.0f + 22 * (k % 3);
            mg_tri(eye, x - 75, base, x, base - ph, x + 75, base, 0.92f, mc);
            mg_tri(eye, x - 15, base - ph + 15, x, base - ph, x + 15, base - ph + 15, 0.92f, RGBA(240, 244, 255, 255));
        }
    }
    float hb = 228 + S.cam * 0.3f;
    if (hb < TOP_H + 100)
        for (int k = 0; k < 3; k++)
            mg_circle(eye, fmodf(k * 160 + rot * 35 + 4800, 480) - 40, hb + 70, 100.0f + 15 * k, 0.72f,
                      k & 1 ? RGBA(110, 160, 140, 255) : RGBA(120, 170, 150, 255));
    u32 cc = rgba_alpha(mix(MG_WHITE, RGBA(150, 120, 190, 255), h / 3), 0.55f);
    for (int c = 0; c < 10; c++) {
        bool near = c >= 6;
        float x = fmodf(S.cloud[c][0] + rot * (near ? 28 : 16) + S.anim * 3 + 4800, 480) - 40;
        float y = fmodf(S.cloud[c][1] + S.cam * (near ? 0.55f : 0.3f), 330) - 45;
        float r = S.cloud[c][2] * (near ? 1.4f : 1), d = near ? 0.55f : 0.82f;
        mg_circle(eye, x, y, r, d, cc);
        mg_circle(eye, x + r, y + 2, r * 0.8f, d, cc);
        mg_circle(eye, x - r, y + 3, r * 0.7f, d, cc);
    }
}

static void draw_ground(int eye)
{
    float y0 = sy(0);
    if (y0 > TOP_H + 70)
        return;
    float tl = tilt(0);
    mg_rect(eye, -20, y0 - 10, TOP_W + 40, TOP_H - y0 + 14, 0.16f, RGBA(92, 150, 84, 255));
    mg_rect(eye, -20, y0 - 10, TOP_W + 40, 3, 0.15f, RGBA(130, 190, 110, 255));
    fill_ellipse(eye, CX, y0, RO + 10, tl * (RO + 10) + 1, 16, 0.05f, RGBA(176, 168, 150, 255));
}

#define NSTRIP 10

static void draw_tower(int eye)
{
    float rot = S.camu / RA;
    for (int i = 0; i < NSTRIP; i++) {
        float a0 = -1.5708f + 3.14159f * i / NSTRIP, a1 = -1.5708f + 3.14159f * (i + 1) / NSTRIP;
        float am = (a0 + a1) * 0.5f, x0 = scx(TR, a0), x1 = scx(TR, a1);
        float yt = fmaxf(scy(TOP_Y, TR, am), -10), yb = fminf(scy(0, TR, am), TOP_H + 10);
        if (yb <= yt)
            continue;
        mg_rect(eye, x0 - 0.5f, yt, x1 - x0 + 1, yb - yt, dep(TR, am),
                mix(RGBA(70, 64, 92, 255), RGBA(196, 188, 214, 255), shade(am)));
    }
    /* stone courses, with joints and windows that turn with the tower */
    int k0 = (int)floorf((S.cam - 130) / BRICK), k1 = (int)ceilf((S.cam + 190) / BRICK);
    int kmax = (int)(TOP_Y / BRICK) - 1;
    if (k0 < 0)
        k0 = 0;
    if (k1 > kmax)
        k1 = kmax;
    float night = clampf(S.cam / TOP_Y * 3 - 1.6f, 0, 1);
    const float JA = 6.2831853f / 12;
    u32 seamc = RGBA(60, 54, 80, 170);
    for (int k = k0; k <= k1; k++) {
        float Y = k * BRICK;
        float pa = -1.45f, pxx = scx(TR, pa), pyy = scy(Y, TR, pa);
        for (int s = 1; s <= 3; s++) {
            float a = -1.45f + 2.9f * s / 3, qx = scx(TR, a), qy = scy(Y, TR, a);
            mg_line(eye, pxx, pyy, qx, qy, 1.3f, dep(TR, (a + pa) * 0.5f) - 0.01f, seamc);
            pa = a;
            pxx = qx;
            pyy = qy;
        }
        float off = (k & 1) ? JA * 0.5f : 0;
        for (int j = 0; j < 12; j++) {
            float a = wrapa(j * JA + off - rot);
            if (cosf(a) < 0.25f)
                continue;
            float x = scx(TR, a);
            mg_line(eye, x, scy(Y, TR, a), x, scy(Y + BRICK, TR, a), 1.1f, dep(TR, a) - 0.01f, seamc);
        }
        if (k % 5 == 2) {
            u32 hsh = (u32)k * 2654435761u;
            float a = wrapa((float)((hsh >> 8) % 1000) / 1000.0f * 6.2832f - rot), ca = cosf(a);
            if (ca > 0.3f) {
                float ww = 9 * ca, x = scx(TR, a), y = scy(Y + BRICK * 0.5f, TR, a), d = dep(TR, a) - 0.015f;
                u32 wc = mix(RGBA(44, 36, 64, 255), RGBA(255, 210, 120, 255), night * 0.8f);
                mg_rect(eye, x - ww / 2, y - 5, ww, 13, d, wc);
                mg_circle(eye, x, y - 5, ww / 2, d, wc);
            }
        }
    }
}

static void merlon(int eye, float a)
{
    float x = scx(TR - 2, a), yb = scy(TOP_Y, TR - 2, a), w = 12 * fabsf(cosf(a)) + 3;
    mg_rect(eye, x - w / 2, yb - 11, w, 11, dep(TR, a) - 0.01f,
            mix(RGBA(80, 72, 104, 255), RGBA(196, 188, 214, 255), shade(a)));
}

/* The top: a walkway ring, a parapet, the hatch and a flag. */
static void draw_crown(int eye)
{
    float y0 = sy(TOP_Y);
    if (y0 > TOP_H + 60 || y0 < -50)
        return;
    float tl = tilt(TOP_Y), rot = S.camu / RA;
    fill_ellipse(eye, CX, y0, RO, fabsf(tl) * RO + 0.5f, 16, 0.2f,
                 tl > 0 ? RGBA(176, 168, 196, 255) : RGBA(96, 88, 116, 255));
    if (tl > 0)
        fill_ellipse(eye, CX, y0, TR - 4, tl * (TR - 4), 14, 0.21f, RGBA(124, 116, 146, 255));
    for (int m = 0; m < 12; m++) {
        float a = wrapa(m * 0.5236f - rot);
        if (cosf(a) < 0)
            merlon(eye, a);
    }
    if (tl > 0) {
        bool open = S.st == ST_TOP;
        fill_ellipse(eye, CX, y0, 20, tl * 20 + 1, 10, 0.2f, RGBA(110, 76, 48, 255));
        fill_ellipse(eye, CX, y0, 15, tl * 15 + 0.6f, 10, 0.19f, open ? RGBA(20, 14, 30, 255) : RGBA(150, 104, 64, 255));
    }
    if (S.st != ST_TOP) {   /* the flag at the back */
        float fx = CX, fy = y0 - tl * TR * 0.6f;
        mg_line(eye, fx, fy, fx, fy - 30, 1.5f, 0.24f, RGBA(80, 70, 60, 255));
        float wv = sinf(S.anim * 4) * 2;
        mg_tri(eye, fx, fy - 30, fx + 14, fy - 26 + wv, fx, fy - 21, 0.24f, RGBA(240, 90, 90, 255));
    }
    for (int m = 0; m < 12; m++) {
        float a = wrapa(m * 0.5236f - rot);
        if (cosf(a) >= 0)
            merlon(eye, a);
    }
    for (int i = 0; i < 8; i++) {   /* the walkway's front face */
        float a0 = -1.5708f + 3.14159f * i / 8, a1 = -1.5708f + 3.14159f * (i + 1) / 8, am = (a0 + a1) * 0.5f;
        quad(eye, scx(RO, a0), scy(TOP_Y, RO, a0), scx(RO, a1), scy(TOP_Y, RO, a1), scx(RO, a1),
             scy(TOP_Y - 10, RO, a1), scx(RO, a0), scy(TOP_Y - 10, RO, a0), dep(RO, am),
             mix(RGBA(70, 64, 92, 255), RGBA(170, 162, 192, 255), shade(am)));
    }
}

static const u32 LOOK_TOP[6] = {RGBA(126, 204, 100, 255), RGBA(214, 196, 160, 255), 0,
                                RGBA(204, 160, 104, 255), RGBA(170, 150, 140, 255), RGBA(240, 96, 96, 255)};
static const u32 LOOK_FRONT[6] = {RGBA(66, 128, 62, 255), RGBA(150, 128, 100, 255), 0,
                                  RGBA(142, 98, 62, 255), RGBA(116, 98, 92, 255), RGBA(200, 62, 72, 255)};
static const u32 LOOK_UNDER[6] = {RGBA(52, 88, 52, 255), RGBA(104, 90, 74, 255), 0,
                                  RGBA(96, 66, 44, 255), RGBA(84, 72, 70, 255), RGBA(236, 218, 196, 255)};

static void draw_disc(int eye, const Plat *p, float Y, bool back, float alpha)
{
    float a = phi(p->u), sa = sinf(a), ca = cosf(a);
    if ((ca < 0) != back || (ca < 0 && fabsf(sa) * RA < TR - 4))
        return;
    float x = scx(RA, a), y = scy(Y, RA, a), d = dep(RA, a), tl = tilt(Y);
    float dim = ca < 0 ? 0.45f : 1.0f;
    float rx = p->hw * 1.08f, ry = 2.5f + fabsf(tl) * p->hw * 1.2f, dir = sa >= 0 ? 1.0f : -1.0f;
    u32 dark = rgba_alpha(mix(RGBA(20, 30, 40, 255), RGBA(46, 110, 60, 255), dim), alpha);
    u32 light = rgba_alpha(mix(RGBA(30, 40, 50, 255), RGBA(108, 196, 104, 255), dim), alpha);
    mg_line(eye, scx(TR, a), scy(Y, TR, a) + 2, x - dir * rx * 0.6f, y + 2, 3, d + 0.02f,
            rgba_alpha(RGBA(70, 120, 60, 255), alpha * dim));
    leafhex(eye, x, y + 3, rx, ry, d + 0.01f, dark);
    mg_tri(eye, x + dir * rx * 0.8f, y + 3 - ry * 0.5f, x + dir * rx * 0.8f, y + 3 + ry * 0.5f, x + dir * (rx + 7),
           y + 3, d + 0.01f, dark);
    leafhex(eye, x, y, rx, ry, d, light);
    mg_tri(eye, x + dir * rx * 0.8f, y - ry * 0.5f, x + dir * rx * 0.8f, y + ry * 0.5f, x + dir * (rx + 7), y, d,
           light);
    mg_line(eye, x - dir * rx * 0.7f, y, x + dir * (rx + 5), y, 1, d - 0.01f,
            rgba_alpha(RGBA(176, 236, 150, 255), alpha * dim));
}

static void draw_rail(int eye, const Row *r, const Plat *p)
{
    float span = (p->amp + p->hw) / RA, c0 = wrapd(p->u0 - S.camu) / RA, Y = r->Y - 3;
    for (int i = 0; i < 4; i++) {
        float pa = c0 - span + 2 * span * i / 4, pb = c0 - span + 2 * span * (i + 1) / 4, m = (pa + pb) * 0.5f;
        if (cosf(m) < 0.1f)
            continue;
        mg_line(eye, scx(TR, pa), scy(Y, TR, pa), scx(TR, pb), scy(Y, TR, pb), 2, dep(TR, m) - 0.012f,
                RGBA(60, 50, 50, 200));
    }
}

static void draw_plat(int eye, const Row *r, const Plat *p, bool back)
{
    if (p->kind == K_NONE || p->kind == K_FULL)
        return;
    float Y = r->Y, alpha = 1, jx = 0;
    if (p->kind == K_CRUMBLE) {
        if (p->gone > 0) {
            float since = GONE_T - p->gone;
            if (since < 0.7f) {   /* falling away */
                Y -= since * since * 260;
                alpha = 1 - since / 0.7f;
            } else if (p->gone < 0.6f) {   /* growing back */
                alpha = (0.6f - p->gone) / 0.6f * 0.6f;
            } else {
                return;
            }
        } else if (p->crack > 0) {
            jx = sinf(S.anim * 75) * 1.6f;
        }
    }
    if (p->look == L_DISC) {
        draw_disc(eye, p, Y, back, alpha);
        return;
    }
    int lk = p->look;
    float sq = p->kind == K_BOUNCE && p->squash > 0 ? p->squash / 0.3f : 0;
    float th = lk == L_LEAF ? 6 : lk == L_SHROOM ? 8 - 4 * sq : 8;
    Y -= 3 * sq;
    float a = p->hw / RA, c0 = phi(p->u), ri = TR - 2, ro = RO + (lk == L_SHROOM ? 2 + 3 * sq : 0);
    int n = p->hw > 36 ? 3 : 2;
    float tl = tilt(Y), tl1 = tilt(Y - th), y0 = sy(Y), y1 = sy(Y - th);
    float tf = tl * FACE_K, tf1 = tl1 * FACE_K;   /* the top face, deeper than true, to read better */
    u32 dark = RGBA(30, 24, 44, 255);
    for (int i = 0; i < n; i++) {
        float pa = c0 - a + 2 * a * i / n, pb = c0 - a + 2 * a * (i + 1) / n, m = (pa + pb) * 0.5f, cm = cosf(m);
        if ((cm < 0) != back || (cm < 0 && fabsf(sinf(m)) * ro < TR - 6))
            continue;
        float sa = sinf(pa), sb = sinf(pb), ca = cosf(pa), cb = cosf(pb);
        float xoa = CX + ro * sa + jx, xob = CX + ro * sb + jx, xia = CX + ri * sa + jx, xib = CX + ri * sb + jx;
        float sh = shade(m) * (back ? 0.6f : 1.0f), d = dep(ro, m), di = dep((ro + ri) * 0.5f, m);
        float yoa = y0 + tl * ro * ca, yob = y0 + tl * ro * cb, yoa1 = y1 + tl1 * ro * ca, yob1 = y1 + tl1 * ro * cb;
        if (fabsf(tf) * (ro - ri) * fmaxf(fabsf(ca), fabsf(cb)) < 0.7f)
            ;   /* edge-on: nothing to see */
        else if (tl > 0)
            quad(eye, xoa, yoa, xob, yob, xib, yob - tf * (ro - ri) * cb, xia, yoa - tf * (ro - ri) * ca, di,
                 rgba_alpha(mix(dark, LOOK_TOP[lk], 0.35f + 0.65f * sh), alpha));
        else
            quad(eye, xoa, yoa1, xob, yob1, xib, yob1 - tf1 * (ro - ri) * cb, xia, yoa1 - tf1 * (ro - ri) * ca, di,
                 rgba_alpha(mix(dark, LOOK_UNDER[lk], 0.4f + 0.6f * sh), alpha));
        if (cm <= 0)
            continue;
        quad(eye, xoa, yoa, xob, yob, xob, yob1, xoa, yoa1, d, rgba_alpha(mix(dark, LOOK_FRONT[lk], 0.3f + 0.7f * sh), alpha));
        float xm = (xoa + xob) * 0.5f, ym = (yoa + yob) * 0.5f, ymb = (yoa1 + yob1) * 0.5f;
        if (cm < 0.45f)
            continue;
        if (lk == L_LEAF)   /* leaves hanging off the edge */
            mg_tri(eye, xm - 4, ymb - 1, xm + 4, ymb - 1, xm + (i & 1 ? 3.0f : -3.0f), ymb + 5, d - 0.005f,
                   rgba_alpha(RGBA(50, 110, 52, 255), alpha));
        else if (lk == L_CRACK)
            mg_line(eye, xm - 3, ym, xm + 2, ymb, 1, d - 0.01f, rgba_alpha(RGBA(40, 30, 30, 255), alpha));
        else if (lk == L_WOOD && i > 0)
            mg_line(eye, xoa, yoa, xoa, yoa1, 1.2f, d - 0.01f, rgba_alpha(RGBA(90, 60, 40, 255), alpha));
        else if (lk == L_SHROOM)
            mg_circle(eye, xm, (ym + ymb) * 0.5f, 2.2f, d - 0.01f, rgba_alpha(RGBA(255, 245, 235, 255), alpha));
    }
}

static void draw_world(int eye, bool back)
{
    for (int i = first_row(); i < S.nrows; i++) {
        const Row *r = &S.rows[i % RING];
        float yy = sy(r->Y);
        if (yy < -90 || yy > TOP_H + 90)
            continue;
        for (int s = 0; s < r->n; s++) {
            const Plat *p = &r->p[s];
            if (p->kind == K_SLIDE && !back)
                draw_rail(eye, r, p);
            draw_plat(eye, r, p, back);
            if (p->heart && solid(p)) {
                float a = phi(p->u);
                if ((cosf(a) < 0) == back) {
                    float bob = sinf(S.anim * 3 + i) * 2;
                    heart_mg(eye, scx(RA, a), scy(r->Y, RA, a) - 14 + bob, 4.5f, dep(RA, a) - 0.04f,
                             RGBA(240, 80, 110, 255));
                }
            }
        }
    }
    if (!back) {
        if (sy(0) < TOP_H + 40) {   /* the tower cat, who waits at the bottom */
            float a = phi(60);
            if (cosf(a) > 0.2f)
                draw_cat(eye, scx(RA + 8, a), scy(0, RA + 8, a), dep(RA + 8, a));
        }
        for (int i = 0; i < NFALL; i++) {   /* shadows where things will land */
            const Fall *f = &S.fall[i];
            if (!f->on || f->sup < -1e8f)
                continue;
            float a = phi(f->u);
            if (cosf(a) < 0.05f)
                continue;
            float ys = scy(f->sup, RA, a);
            if (ys > TOP_H + 10 || ys < -10)
                continue;
            float k = f->st == FS_WARN ? clampf(f->t / f->warn, 0, 1) * 0.5f
                                       : 0.5f + 0.5f * clampf(1 - (f->Y - f->sup) / 150, 0, 1);
            leafhex(eye, scx(RA, a), ys + 1, 5 + 7 * k, 1.5f + 2.5f * k, dep(RA, a) - 0.005f,
                    RGBA(20, 10, 30, (u32)(70 + 110 * k)));
        }
    }
    for (int i = 0; i < NEN; i++) {
        const Enemy *e = &S.en[i];
        if (!e->on)
            continue;
        float a = phi(e->u), ca = cosf(a);
        if ((ca < 0) != back || (ca < 0 && fabsf(sinf(a)) * RA < TR))
            continue;
        float x = scx(RA, a), y = scy(e->Y, RA, a), d = dep(RA, a) - 0.02f;
        if (y < -30 || y > TOP_H + 30)
            continue;
        float sq = 1, al = ca < 0 ? 0.6f : 1.0f;
        if (e->dying) {
            float k = clampf(e->t / 0.45f, 0, 1);
            sq = e->blown ? 1 : 1 - 0.75f * k;
            al *= 1 - k;
        }
        if (e->kind == E_BEETLE)
            draw_beetle(eye, x, y, d, e->dir, sq, al, i);
        else
            draw_crow(eye, x, y, d, e->dir, sq, al, e->kind == E_FLYER);
    }
}

static void draw_hero(int eye)
{
    if (S.st == ST_TOP) {   /* the hop into the hatch */
        float tt = S.st_t;
        if (tt >= 1.1f)
            return;
        float a0 = phi(S.hop_u), x0 = scx(RA, a0), y0 = scy(S.hop_Y, RA, a0), yh = sy(TOP_Y);
        float p = clampf(tt / 0.8f, 0, 1);
        float x = lerpf(x0, CX, p), y = lerpf(y0, yh, p) - sinf(p * 3.14159f) * 40;
        float s = tt < 0.8f ? 1 : clampf(1 - (tt - 0.8f) / 0.3f, 0, 1);
        if (tt > 0.8f)
            y += (tt - 0.8f) * 30;
        if (s > 0.05f)
            draw_aron(eye, x, y, 0.15f, s * ASC, 1, 1);
        return;
    }
    float a = phi(S.u), x = scx(RA, a), y = scy(S.Y, RA, a), d = dep(RA, a) - 0.03f;
    float alpha = S.invuln > 0 && S.st == ST_PLAY && fmodf(S.anim * 12, 2) < 1 ? 0.35f : 1;
    int pose = (S.st == ST_OVER && S.reason == 1) || S.knock > 0 ? 2 : S.ground ? 0 : 1;
    if (S.st == ST_GUST) {
        for (int i = 0; i < 3; i++) {   /* the swirl carrying him */
            float w = S.anim * 9 + i * 2.1f, r = 12 + i * 2;
            mg_line(eye, x + cosf(w) * r, y - 10 + sinf(w) * 4, x + cosf(w + 0.8f) * r, y - 10 + sinf(w + 0.8f) * 4,
                    1.5f, d - 0.02f, RGBA(220, 240, 255, 200));
        }
    }
    draw_aron(eye, x, y, d, ASC, alpha, pose);
}

static void draw_falls(int eye)
{
    for (int i = 0; i < NFALL; i++) {
        const Fall *f = &S.fall[i];
        if (!f->on)
            continue;
        float a = phi(f->u);
        if (cosf(a) < 0.05f)
            continue;
        float x = scx(RA, a), d = dep(RA, a) - 0.04f;
        if (f->st == FS_WARN) {
            if (fmodf(S.anim * 8, 2) < 1.3f) {
                mg_tri(eye, x - 7, 3, x + 7, 3, x, 17, d - 0.05f, RGBA(255, 80, 70, 230));
                mg_rect(eye, x - 1, 5, 2, 5, d - 0.06f, MG_WHITE);
                mg_rect(eye, x - 1, 11, 2, 2, d - 0.06f, MG_WHITE);
            }
            continue;
        }
        float y = scy(f->Y, RA, a);
        if (y < -20 || y > TOP_H + 20)
            continue;
        if (f->kind == F_ACORN) {
            mg_circle(eye, x, y - 4, 4, d, RGBA(160, 100, 52, 255));
            mg_rect(eye, x - 4.5f, y - 10, 9, 4, d - 0.01f, RGBA(100, 66, 40, 255));
            mg_line(eye, x, y - 10, x + 1, y - 13, 1.2f, d - 0.01f, RGBA(100, 66, 40, 255));
        } else if (f->kind == F_TILE) {
            float r = f->t * 7, c = cosf(r), s = sinf(r), hx = 7, hy = 3.5f;
            quad(eye, x + c * hx - s * hy, y + s * hx + c * hy, x - c * hx - s * hy, y - s * hx + c * hy,
                 x - c * hx + s * hy, y - s * hx - c * hy, x + c * hx + s * hy, y + s * hx - c * hy, d,
                 RGBA(196, 86, 64, 255));
            mg_line(eye, x - c * hx, y - s * hx, x + c * hx, y + s * hx, 1, d - 0.01f, RGBA(120, 50, 40, 255));
        } else {
            mg_rect(eye, x - 1.5f, y - 30, 3, 22, d + 0.01f, RGBA(255, 240, 180, 90));
            mg_circle(eye, x, y - 4, 8, d + 0.005f, RGBA(255, 236, 140, 70));
            float r = 6.5f, sp = S.anim * 5;
            mg_tri(eye, x + r * sinf(sp), y - 4 - r * cosf(sp), x + r * sinf(sp + 2.094f), y - 4 - r * cosf(sp + 2.094f),
                   x + r * sinf(sp + 4.189f), y - 4 - r * cosf(sp + 4.189f), d, RGBA(255, 226, 90, 255));
            mg_tri(eye, x - r * sinf(sp), y - 4 + r * cosf(sp), x - r * sinf(sp + 2.094f), y - 4 + r * cosf(sp + 2.094f),
                   x - r * sinf(sp + 4.189f), y - 4 + r * cosf(sp + 4.189f), d, RGBA(255, 226, 90, 255));
        }
    }
}

static void draw_effects(int eye, bool scene)
{
    for (int i = 0; i < NPART; i++) {
        const Part *p = &S.p[i];
        if (p->life <= 0 || p->scr != scene)
            continue;
        float x = p->x, y = p->y, d = -0.1f;
        if (!p->scr) {
            float a = phi(p->x);
            if (cosf(a) < 0)
                continue;
            x = scx(RA, a);
            y = scy(p->y, RA, a);
            d = dep(RA, a) - 0.04f;
        }
        float al = clampf(p->life / p->max * 1.5f, 0, 1);
        mg_rect(eye, x - p->size / 2, y - p->size / 2, p->size, p->size, d, rgba_alpha(p->c, al));
    }
    for (int i = 0; i < NPOP; i++) {
        const Pop *p = &S.pop[i];
        if (p->t <= 0)
            continue;
        float age = p->max - p->t, k = clampf(age / 0.15f, 0, 1);
        float a = clampf(p->t / 0.3f, 0, 1);
        float sc = p->scale * (0.6f + 0.4f * k), yy = p->y - fminf(age, 0.6f) * 12;
        mg_text_centered(eye, p->txt, p->x + 1.5f, yy + 1.5f, sc, p->depth + 0.02f, rgba_alpha(RGBA(20, 16, 30, 255), a));
        mg_text_centered(eye, p->txt, p->x, yy, sc, p->depth, rgba_alpha(p->c, a));
    }
}

static void draw_mist(int eye)
{
    float danger = clampf(1 - (S.Y - (S.cam - 110)) / 140, 0, 1);
    float a = 0.3f + 0.6f * danger;
    for (int i = 0; i < 3; i++)
        mg_rect(eye, -20, TOP_H - 28 + i * 9, TOP_W + 40, 30, -0.22f, RGBA(150, 110, 190, (u32)(a * 70)));
    for (int i = 0; i < 6; i++)
        mg_circle(eye, fmodf(i * 80 + S.anim * 12 + 4800, 480) - 40, TOP_H - 4 + sinf(S.anim * 1.5f + i) * 3, 22,
                  -0.23f, RGBA(170, 130, 210, (u32)(a * 60)));
}

static void draw_hud(int eye)
{
    char buf[24];
    snprintf(buf, sizeof(buf), "%d m", (int)(fmaxf(S.Y, 0) / PX_M));
    mg_text(eye, buf, 9, 7, 0.55f, -0.14f, RGBA(20, 16, 30, 200));
    mg_text(eye, buf, 8, 6, 0.55f, -0.15f, MG_WHITE);
    for (int i = 0; i < 3; i++)
        heart_mg(eye, 354 + i * 15, 11, 5, -0.15f, i < S.hearts ? RGBA(240, 80, 110, 255) : RGBA(255, 255, 255, 60));
    for (int t = 0; t < 4; t++)
        mg_rect(eye, 348 + t * 11, 24, 8, 4, -0.15f, t <= S.tier ? RGBA(255, 190, 90, 255) : RGBA(255, 255, 255, 60));
}

/* ---- drawing: the top ------------------------------------------------------------ */

static void draw_scene(int eye)
{
    float tm = S.anim;
    switch (S.scene) {
    case 0:   /* flower meadow */
        mg_sky(eye, RGBA(110, 180, 240, 255), RGBA(220, 240, 250, 255));
        mg_circle(eye, 330, 50, 22, 0.95f, RGBA(255, 236, 150, 255));
        mg_circle(eye, 330, 50, 30, 0.95f, RGBA(255, 236, 150, 70));
        mg_circle(eye, 70, 290, 150, 0.8f, RGBA(150, 205, 140, 255));
        mg_circle(eye, 330, 300, 170, 0.8f, RGBA(140, 196, 132, 255));
        mg_circle(eye, 200, 330, 170, 0.45f, RGBA(112, 182, 100, 255));
        mg_rect(eye, -20, 205, TOP_W + 40, 40, 0.1f, RGBA(96, 168, 86, 255));
        for (int i = 0; i < 22; i++) {
            float x = S.sc[i][0] * 420 - 10, y = 160 + S.sc[i][1] * 80, d = 0.5f - (y - 160) / 80 * 0.75f;
            float sw = sinf(tm * 2 + i) * 2;
            static const u32 PET[4] = {RGBA(255, 120, 150, 255), RGBA(255, 220, 90, 255),
                                       RGBA(200, 140, 255, 255), RGBA(255, 255, 255, 255)};
            float r = 2 + S.sc[i][2] * 3 * (y - 140) / 100;
            mg_line(eye, x, y, x + sw, y - r * 3, 1.2f, d, RGBA(60, 130, 60, 255));
            mg_circle(eye, x + sw, y - r * 3, r, d, PET[i & 3]);
            mg_circle(eye, x + sw, y - r * 3, r * 0.4f, d - 0.01f, RGBA(250, 200, 60, 255));
        }
        break;
    case 1:   /* city at night */
        mg_sky(eye, RGBA(10, 10, 36, 255), RGBA(70, 40, 96, 255));
        for (int i = 0; i < 24; i++)
            mg_rect(eye, S.sc[i][0] * TOP_W, S.sc[i][1] * 90, 1.5f, 1.5f, 1.0f,
                    rgba_alpha(MG_WHITE, 0.5f + 0.5f * sinf(tm * 3 + i)));
        mg_circle(eye, 80, 46, 14, 0.95f, RGBA(240, 236, 210, 255));
        mg_circle(eye, 86, 42, 12, 0.95f, RGBA(10, 10, 36, 255));
        for (int i = 0; i < 12; i++) {   /* far skyline */
            float x = i * 36 - 10, h = 60 + S.sc[i][2] * 70;
            mg_rect(eye, x, 205 - h, 32, h, 0.7f, RGBA(34, 30, 70, 255));
        }
        for (int i = 0; i < 8; i++) {    /* near blocks with windows */
            float x = i * 54 - 14 + S.sc[i][3] * 10, h = 50 + S.sc[i + 8][2] * 60;
            mg_rect(eye, x, 205 - h, 44, h, 0.35f, RGBA(52, 44, 90, 255));
            for (int w = 0; w < 6; w++) {
                bool on = sinf(tm * 0.7f + i * 3 + w * 1.7f) > -0.3f;
                if (on)
                    mg_rect(eye, x + 6 + (w % 3) * 12, 205 - h + 8 + (w / 3) * 14, 6, 6, 0.34f,
                            RGBA(255, 214, 120, 230));
            }
        }
        mg_rect(eye, -20, 205, TOP_W + 40, 40, 0.1f, RGBA(30, 28, 44, 255));
        for (int i = 0; i < 8; i++)   /* road marks */
            mg_rect(eye, fmodf(i * 60 - tm * 40 + 600, 480) - 40, 222, 22, 2, 0.05f, RGBA(220, 220, 180, 160));
        for (int i = 0; i < 4; i++) { /* cars */
            float dir = i & 1 ? 1.0f : -1.0f;
            float x = fmodf(S.sc[i][0] * 480 + dir * tm * (70 + i * 15) + 4800, 480) - 40, y = 214 + (i & 1) * 12;
            static const u32 CAR[4] = {RGBA(220, 70, 70, 255), RGBA(80, 160, 240, 255), RGBA(240, 200, 70, 255),
                                       RGBA(200, 200, 210, 255)};
            mg_rect(eye, x, y - 5, 22, 6, -0.05f, CAR[i]);
            mg_rect(eye, x + 5, y - 9, 11, 4, -0.05f, CAR[i]);
            mg_circle(eye, x + (dir > 0 ? 23 : -1), y - 3, 2, -0.06f, RGBA(255, 250, 200, 255));
        }
        break;
    case 2:   /* the Purgatorium's little lights */
        mg_sky(eye, RGBA(18, 10, 46, 255), RGBA(84, 50, 120, 255));
        for (int i = 0; i < 28; i++)
            mg_rect(eye, S.sc[i][0] * TOP_W, S.sc[i][1] * 200, 1.5f, 1.5f, 1.0f,
                    rgba_alpha(MG_WHITE, 0.4f + 0.6f * fabsf(sinf(tm * 1.5f + i))));
        for (int i = 0; i < 16; i++) {   /* drifting lights */
            float d = 0.8f - S.sc[i][2] * 1.0f;
            float x = S.sc[i][0] * TOP_W + sinf(tm * 0.8f + i) * 10;
            float y = fmodf(S.sc[i][1] * 260 - tm * (8 + S.sc[i][3] * 10) + 2600, 260) - 10;
            float r = 2 + (0.8f - d) * 2.5f;
            mg_circle(eye, x, y, r * 2.4f, d, RGBA(255, 200, 120, 50));
            mg_circle(eye, x, y, r, d, RGBA(255, 236, 180, 255));
        }
        for (int i = 0; i < 6; i++)      /* cloud floor */
            mg_circle(eye, i * 80, 238, 46, 0.15f, RGBA(200, 180, 236, 255));
        {   /* Pim and Dross */
            float bob = sinf(tm * 2) * 3;
            mg_circle(eye, 90, 120 + bob, 9, 0.2f, RGBA(220, 240, 255, 220));
            mg_tri(eye, 81, 121 + bob, 99, 121 + bob, 90, 138 + bob, 0.2f, RGBA(220, 240, 255, 220));
            mg_rect(eye, 86, 117 + bob, 2, 3, 0.19f, MG_INK);
            mg_rect(eye, 92, 117 + bob, 2, 3, 0.19f, MG_INK);
            mg_circle(eye, 330, 110 - bob, 13, 0.3f, RGBA(150, 130, 170, 220));
            mg_tri(eye, 317, 112 - bob, 343, 112 - bob, 334, 138 - bob, 0.3f, RGBA(150, 130, 170, 220));
            mg_rect(eye, 323, 106 - bob, 3, 2, 0.29f, MG_INK);
            mg_rect(eye, 333, 106 - bob, 3, 2, 0.29f, MG_INK);
        }
        break;
    case 3:   /* seaside */
        mg_sky(eye, RGBA(250, 150, 120, 255), RGBA(255, 222, 170, 255));
        mg_circle(eye, 300, 150, 30, 0.95f, RGBA(255, 240, 180, 255));
        mg_rect(eye, -20, 150, TOP_W + 40, 60, 0.6f, RGBA(60, 110, 170, 255));
        mg_rect(eye, -20, 172, TOP_W + 40, 40, 0.35f, RGBA(50, 96, 156, 255));
        for (int i = 0; i < 10; i++) {
            float y = 156 + i * 5, x = fmodf(S.sc[i][0] * 400 + tm * (10 + i * 3), 440) - 20;
            mg_line(eye, x, y, x + 18 + i * 2, y, 1.2f, 0.6f - i * 0.05f, RGBA(255, 230, 200, 150));
        }
        mg_rect(eye, 300 - 30, 150, 60, 3, 0.58f, RGBA(255, 240, 180, 150));
        mg_rect(eye, -20, 204, TOP_W + 40, 40, 0.08f, RGBA(240, 210, 150, 255));
        for (int i = 0; i < 3; i++) {   /* gulls */
            float x = fmodf(S.sc[i][1] * 400 + tm * 20, 440) - 20, y = 60 + i * 18 + sinf(tm * 3 + i) * 3;
            float f = sinf(tm * 8 + i) * 3;
            mg_line(eye, x - 6, y - f, x, y, 1.2f, 0.5f, MG_INK);
            mg_line(eye, x, y, x + 6, y - f, 1.2f, 0.5f, MG_INK);
        }
        mg_line(eye, 90, 224, 96, 176, 2, -0.05f, RGBA(120, 90, 60, 255));   /* a beach umbrella */
        mg_tri(eye, 66, 186, 126, 174, 94, 166, -0.06f, RGBA(240, 90, 90, 255));
        break;
    default:  /* the angels' clouds */
        mg_sky(eye, RGBA(250, 230, 170, 255), RGBA(255, 250, 235, 255));
        for (int i = 0; i < 7; i++) {   /* light rays */
            float x = 40 + i * 55;
            mg_tri(eye, 200, -20, x - 14, 240, x + 14, 240, 0.9f, RGBA(255, 255, 255, 50));
        }
        mg_rect(eye, 168, 92, 64, 80, 0.7f, RGBA(255, 214, 110, 255));   /* golden gate */
        mg_circle(eye, 200, 92, 32, 0.7f, RGBA(255, 214, 110, 255));
        mg_rect(eye, 176, 96, 48, 76, 0.69f, RGBA(255, 246, 220, 255));
        mg_circle(eye, 200, 96, 24, 0.69f, RGBA(255, 246, 220, 255));
        for (int b = 0; b < 4; b++)
            mg_rect(eye, 183 + b * 11, 80, 2, 92, 0.68f, RGBA(230, 180, 80, 255));
        for (int i = 0; i < 8; i++)
            mg_circle(eye, i * 60 - 10 + S.sc[i][0] * 20, 186 + S.sc[i][1] * 14, 34 + S.sc[i][2] * 14, 0.35f,
                      RGBA(255, 255, 255, 255));
        for (int i = 0; i < 6; i++)
            mg_circle(eye, i * 80 + 10, 236, 44, 0.1f, RGBA(246, 244, 255, 255));
        for (int i = 0; i < 8; i++) {   /* drifting feathers */
            float x = S.sc[i + 10][0] * TOP_W + sinf(tm * 1.3f + i) * 14;
            float y = fmodf(S.sc[i + 10][1] * 240 + tm * 18, 250) - 10, d = 0.5f - S.sc[i + 10][2] * 0.8f;
            mg_line(eye, x - 4, y + 2, x + 4, y - 2, 2.5f, d, RGBA(255, 255, 255, 240));
            mg_line(eye, x - 5, y + 3, x + 5, y - 3, 0.8f, d - 0.01f, RGBA(220, 200, 160, 255));
        }
        break;
    }
    /* the tower's top, with its hatch */
    mg_rect(eye, 160, 200, 80, 44, 0.0f, RGBA(150, 142, 172, 255));
    mg_rect(eye, 160, 200, 12, 44, 0.02f, RGBA(110, 102, 134, 255));
    mg_rect(eye, 228, 200, 12, 44, 0.02f, RGBA(110, 102, 134, 255));
    fill_ellipse(eye, 200, 200, 40, 8, 14, -0.01f, RGBA(190, 182, 210, 255));
    fill_ellipse(eye, 200, 200, 26, 5, 14, -0.02f, RGBA(20, 14, 30, 255));

    /* Aron pops out and celebrates */
    float tt = S.st_t;
    if (tt >= 1.5f) {
        float x, y;
        int pose = 3;
        if (tt < 2.5f) {
            float p = (tt - 1.5f) / 1.0f;
            x = lerpf(200, 290, p);
            y = lerpf(200, 214, p) - sinf(p * 3.14159f) * 150;
            pose = 1;
        } else {
            x = 290;
            y = 214 - fabsf(sinf((tt - 2.5f) * 5)) * 12;
        }
        draw_aron(eye, x, y, -0.12f, 1.6f, 1, pose);
    }
    mg_text_centered(eye, SCENE_NAME[S.scene], CX, 6, 0.45f, -0.15f, MG_WHITE);
}

static void draw_top(int eye)
{
    if (S.st == ST_TOP && S.st_t >= 1.3f) {
        draw_scene(eye);
        draw_effects(eye, true);
    } else {
        draw_bg(eye);
        draw_ground(eye);
        draw_world(eye, true);
        draw_tower(eye);
        draw_crown(eye);
        draw_world(eye, false);
        draw_hero(eye);
        draw_falls(eye);
        draw_effects(eye, false);
        if (S.st == ST_GUST)
            for (int i = 0; i < 8; i++) {   /* wind streaks */
                float x = 30 + i * 47 + sinf(i * 2.3f) * 14, y = fmodf(i * 53 + S.anim * 520, 280) - 30;
                mg_line(eye, x, y, x, y + 22, 1.5f, -0.1f - (i & 1) * 0.1f, RGBA(220, 240, 255, 120));
            }
        if (S.st != ST_TOP) {
            draw_mist(eye);
            draw_hud(eye);
        }
    }
    if (S.flash > 0) {
        float a = 1 - fabsf(S.flash - 0.25f) / 0.25f;
        gfx_rect(0, 0, TOP_W, TOP_H, RGBA(255, 255, 255, (u32)(255 * clampf(a, 0, 1))));
    }
}

/* ---- bottom screen: altimeter, map from above, hearts ------------------------------ */

static void heart_gfx(float x, float y, float s, u32 c)
{
    gfx_circle(x - s * 0.5f, y, s * 0.58f, c);
    gfx_circle(x + s * 0.5f, y, s * 0.58f, c);
    gfx_triangle(x - s * 1.05f, y + s * 0.15f, x + s * 1.05f, y + s * 0.15f, x, y + s * 1.25f, c);
}

static void draw_bottom(void)
{
    static const u32 TC[4] = {RGBA(110, 200, 120, 255), RGBA(230, 210, 90, 255), RGBA(240, 150, 80, 255),
                              RGBA(230, 90, 100, 255)};
    static const u32 LOOKC[6] = {RGBA(120, 210, 110, 255), RGBA(214, 196, 160, 255), RGBA(150, 230, 150, 255),
                                 RGBA(210, 160, 100, 255), RGBA(190, 160, 140, 255), RGBA(240, 100, 100, 255)};
    const u32 dim = RGBA(152, 152, 159, 255);
    char buf[64];
    gfx_text("The Tower", 12, 6, 0.55f, MG_GOLD);
    for (int i = 0; i < 3; i++)
        heart_gfx(246 + i * 26, 16, 8, i < S.hearts ? RGBA(240, 80, 110, 255) : RGBA(255, 255, 255, 40));

    /* altimeter */
    float ax = 18, aw = 12, ab = 200, at = 44, sc = (ab - at) / TOP_Y;
    for (int t = 0; t < 4; t++) {
        float y0 = ab - (t + 1) * TIER_Y * sc;
        gfx_rect(ax, y0, aw, TIER_Y * sc, rgba_alpha(TC[t], S.best >= t * TIER_Y ? 0.9f : 0.25f));
    }
    for (int m = 50; m <= 300; m += 50) {
        float y = ab - m * PX_M * sc;
        gfx_line(ax + aw, y, ax + aw + 4, y, 1, dim);
        snprintf(buf, sizeof(buf), "%d", m);
        gfx_text(buf, ax + aw + 6, y - 6, 0.36f, dim);
    }
    for (int m = 0; m < 3; m++)   /* the crown */
        gfx_rect(ax - 2 + m * 6, at - 7, 4, 5, S.done ? MG_GOLD : RGBA(180, 172, 200, 255));
    float kill = S.cam - 110;
    if (kill > 0 && S.st != ST_TOP)
        gfx_rect(ax - 3, ab - fminf(kill, TOP_Y) * sc, aw + 6, fminf(kill, TOP_Y) * sc, RGBA(170, 120, 210, 110));
    gfx_line(ax - 4, ab - S.best * sc, ax + aw + 2, ab - S.best * sc, 1.5f, MG_GOLD);
    float ay = ab - clampf(S.Y, 0, TOP_Y) * sc;
    gfx_triangle(ax - 9, ay - 4, ax - 9, ay + 4, ax - 2, ay, MG_WHITE);
    gfx_rect(ax - 6, ab, aw + 12, 3, RGBA(110, 170, 100, 255));

    /* the tower seen from above; you look from the bottom */
    float ox = 146, oy = 114, R0 = 30;
    gfx_circle(ox, oy, 66, RGBA(255, 255, 255, 12));
    gfx_circle(ox, oy, R0, RGBA(150, 142, 172, 255));
    if (S.st != ST_TOP) {
        for (int i = first_row(); i < S.nrows; i++) {
            const Row *r = &S.rows[i % RING];
            float dy = r->Y - S.Y;
            if (dy < -60 || dy > 150)
                continue;
            float k = clampf((dy + 60) / 210, 0, 1), rr = R0 + 5 + k * 30;
            for (int s = 0; s < r->n; s++) {
                const Plat *p = &r->p[s];
                if (!solid(p))
                    continue;
                u32 c = p->kind == K_FULL ? RGBA(130, 190, 110, 255) : LOOKC[p->look];
                c = rgba_alpha(c, dy < -8 ? 0.3f : 1 - k * 0.55f);
                float a0 = phi(p->u) - fminf(p->hw / RA, 3.1f), a1 = phi(p->u) + fminf(p->hw / RA, 3.1f);
                int n = p->kind == K_FULL ? 16 : 3;
                for (int q = 0; q < n; q++) {
                    float b0 = a0 + (a1 - a0) * q / n, b1 = a0 + (a1 - a0) * (q + 1) / n;
                    gfx_line(ox + rr * sinf(b0), oy + rr * cosf(b0), ox + rr * sinf(b1), oy + rr * cosf(b1), 3.5f, c);
                }
                if (p->heart)
                    gfx_circle(ox + rr * sinf(phi(p->u)), oy + rr * cosf(phi(p->u)), 2.5f, RGBA(255, 120, 150, 255));
            }
        }
        for (int i = 0; i < NEN; i++) {
            const Enemy *e = &S.en[i];
            float dy = e->Y - S.Y;
            if (!e->on || e->dying || dy < -60 || dy > 150)
                continue;
            float rr = R0 + 5 + clampf((dy + 60) / 210, 0, 1) * 30, a = phi(e->u);
            gfx_circle(ox + rr * sinf(a), oy + rr * cosf(a), 2.6f, RGBA(255, 70, 90, 255));
        }
        for (int i = 0; i < NFALL; i++)
            if (S.fall[i].on) {
                float a = phi(S.fall[i].u);
                gfx_circle(ox + 64 * sinf(a), oy + 64 * cosf(a), 2.5f, RGBA(255, 220, 90, 255));
            }
        float rr = R0 + 5 + (60.0f / 210) * 30, a = phi(S.u);
        gfx_circle(ox + rr * sinf(a), oy + rr * cosf(a), 4, RGBA(70, 170, 240, 255));
        gfx_circle(ox + rr * sinf(a), oy + rr * cosf(a), 2, MG_WHITE);
    }
    gfx_text("you", ox - 9, oy + 70, 0.38f, dim);

    /* numbers */
    float tx = 228, t = S.done || S.st == ST_OVER ? S.end_t : S.t;
    snprintf(buf, sizeof(buf), "%d m", (int)(fmaxf(S.done ? TOP_Y : S.Y, 0) / PX_M));
    gfx_text(buf, tx, 40, 0.75f, MG_WHITE);
    snprintf(buf, sizeof(buf), "best %d of 300 m", (int)(S.best / PX_M));
    gfx_text(buf, tx, 68, 0.4f, dim);
    snprintf(buf, sizeof(buf), "Tier %d of 4", S.tier + 1);
    gfx_text(buf, tx, 90, 0.48f, TC[S.tier]);
    snprintf(buf, sizeof(buf), "Stomps %d", S.stomps);
    gfx_text(buf, tx, 112, 0.48f, MG_WHITE);
    snprintf(buf, sizeof(buf), "Time %d:%02d", (int)t / 60, (int)t % 60);
    gfx_text(buf, tx, 134, 0.48f, MG_WHITE);
    if (S.st == ST_GUST)
        gfx_text("Updraft!", tx, 160, 0.48f, RGBA(200, 230, 255, 255));
    gfx_text("A: jump (hold: higher)\nD-pad / Circle Pad: run", 12, 206, 0.4f, dim);
}

/* ---- score ------------------------------------------------------------------------- */

static int score(void)
{
    float h = clampf(S.best / TOP_Y, 0, 1);
    float s = 62 * h + 3.0f * (S.hearts > 0 ? S.hearts : 0) * h + 0.75f * (S.stomps < 12 ? S.stomps : 12);
    if (S.done)
        s += 10 + 10 * clampf((200 - S.end_t) / 125, 0, 1);
    return (int)clampf(s + 0.5f, 0, 100);
}

static const char *verdict(void)
{
    static char buf[128];
    int m = (int)(S.best / PX_M);
    if (S.done)
        snprintf(buf, sizeof(buf), "Top in %d:%02d, %d stomp%s. Aron found %s.", (int)S.end_t / 60,
                 (int)S.end_t % 60, S.stomps, S.stomps == 1 ? "" : "s", SCENE_FOUND[S.scene]);
    else if (S.st == ST_OVER && S.reason == 1)
        snprintf(buf, sizeof(buf), "Out of hearts at %d m of 300.", m);
    else if (S.st == ST_OVER && S.reason == 2)
        snprintf(buf, sizeof(buf), "Time ran out at %d m of 300.", m);
    else if (S.st == ST_OVER)
        snprintf(buf, sizeof(buf), "Fell from %d m of 300. The tower keeps its secret.", m);
    else
        snprintf(buf, sizeof(buf), "Stopped at %d m of 300.", m);
    return buf;
}

/* ---- bot: aims for the best reachable ledge above, stomps what it meets ------------- */

enum { BM_NONE, BM_NOW, BM_WALK, BM_WAIT };

/* Furthest you get sideways in T seconds starting at speed v (toward the target). */
static float max_disp(float v, float T)
{
    if (T <= 0)
        return 0;
    if (v >= VMAX)
        return v * T;
    float tv = (VMAX - v) / ACC_AIR;
    if (tv >= T)
        return v * T + 0.5f * ACC_AIR * T * T;
    return v * tv + 0.5f * ACC_AIR * tv * tv + VMAX * (T - tv);
}

static float bot_pu(const Plat *p, float T) { return p->kind == K_FULL ? S.u : plat_u_at(p, S.pt + T); }

static int bot_eval(int i, int s, float vy, bool hold, bool grounded, float *score_out, float *tu)
{
    const Row *r = row_at(i);
    const Plat *p = &r->p[s];
    const Row *cr = row_at(S.on_row);
    const Plat *cp = cr ? &cr->p[S.on_slot] : NULL;
    if (grounded && cp && r->Y < S.Y && (cp->kind == K_FULL || fabsf(wrapd(p->u - cp->u)) < cp->hw + p->hw))
        return BM_NONE;   /* right under our own ledge: we'd land back on it */
    float T = fly_time(S.Y, vy, r->Y, hold);
    if (T < 0.05f || fly_time(S.Y, vy, r->Y + 10, hold) < 0)   /* clear it with some room */
        return BM_NONE;
    float dy = r->Y - S.Y;
    float sc = (dy < 0 ? dy * 1.5f : dy) + (s == r->path ? 70 : 0) + (p->kind == K_BOUNCE && dy > -5 ? 30 : 0) +
               (p->kind == K_FULL && i > 0 ? 200 : 0) + (p->heart && S.hearts < 3 ? 25 : 0);
    for (int k = 0; k < 4; k++)   /* break loops between the same few ledges */
        if (B.vrow[k] == i && B.vslot[k] == s && S.t - B.vt[k] < 8)
            sc -= 45;
    float pu = bot_pu(p, T), du = wrapd(pu - S.u);
    float need = fmaxf(fabsf(du) - p->hw * 0.45f, 0);
    if (p->kind == K_FULL || need <= max_disp(S.vx * (du >= 0 ? 1 : -1), T) * 0.84f) {
        *score_out = sc - fabsf(du) * 0.1f;
        *tu = pu;
        return BM_NOW;
    }
    if (!grounded)
        return BM_NONE;
    bool free_walk = !cp || cp->kind == K_FULL;
    if (p->kind == K_SLIDE || p->kind == K_ORBIT) {   /* wait for it to come by (not on a crumbling ledge) */
        if (cp && cp->kind == K_CRUMBLE)
            return BM_NONE;
        for (float w = 0.2f; w <= 7.01f; w += 0.2f) {
            float pw = plat_u_at(p, S.pt + w + T), t2 = pw;
            if (!free_walk)
                t2 = wrapu(cp->u + clampf(wrapd(pw - cp->u), -(cp->hw - 4), cp->hw - 4));
            if (fabsf(wrapd(t2 - S.u)) > VMAX * w * 0.7f)
                continue;
            if (fmaxf(fabsf(wrapd(pw - t2)) - p->hw * 0.45f, 0) <= max_disp(0, T) * 0.78f) {
                *score_out = sc - w * 4;
                *tu = t2;
                return BM_WAIT;
            }
        }
        return BM_NONE;
    }
    /* static target: run to the best takeoff point on our ledge (a run-up gives full speed) */
    float t2 = free_walk ? pu : wrapu(cp->u + clampf(wrapd(pu - cp->u), -(cp->hw - 5), cp->hw - 5));
    if (fmaxf(fabsf(wrapd(pu - t2)) - p->hw * 0.45f, 0) <= max_disp(VMAX * 0.9f, T) * 0.88f) {
        *score_out = sc - 2 - fabsf(wrapd(t2 - S.u)) * 0.05f;
        *tu = t2;
        return BM_WALK;
    }
    return BM_NONE;
}

static int bot_pick(float vy, bool hold, bool grounded, int *bi, int *bs, float *btu)
{
    int mode = BM_NONE;
    float best = -1e9f;
    for (int i = first_row(); i < S.nrows; i++) {
        const Row *r = &S.rows[i % RING];
        float dy = r->Y - S.Y;
        if (dy < (grounded ? -120 : -160) || dy > (grounded ? 68 : 190))
            continue;
        for (int s = 0; s < r->n; s++) {
            const Plat *p = &r->p[s];
            if (!solid(p) || (p->kind == K_CRUMBLE && p->crack > 0) ||
                ((grounded || S.vy > 0) && i == S.on_row && s == S.on_slot))
                continue;
            float sc, tu;
            int m = bot_eval(i, s, vy, hold, grounded, &sc, &tu);
            if (m != BM_NONE && sc > best) {
                best = sc;
                mode = m;
                *bi = i;
                *bs = s;
                *btu = tu;
            }
        }
    }
    return mode;
}

static void bot(Input *in, float t)
{
    float dt = clampf(t - B.lt, 0, 0.05f);
    B.lt = t;
    if (S.st != ST_PLAY) {
        B.has = false;
        B.te = -1;
        return;
    }
    if (S.best > B.best) {
        B.best = S.best;
        B.prog_t = t;
    }
    /* the updraft: on the way up from 125 m, or to get unstuck */
    if (!B.cheated && ((S.best >= 1250 && !S.ground && S.vy > 100) || t - B.prog_t > 8)) {
        in->down |= KEY_L_;
        B.cheated = true;
        return;
    }
    float mv = 0;
    bool holdnow = (B.hold && S.vy > 0) || S.boost;
    if (S.knock > 0) {   /* knocked back: plan again once we can */
        B.has = false;
        B.te = -1;
    }
    if (S.ground) {
        B.has = false;
        B.te = -1;
        B.hop = 0;
        if (S.on_row != B.lrow || S.on_slot != B.lslot) {   /* remember where we've been */
            B.lrow = S.on_row;
            B.lslot = S.on_slot;
            B.vrow[B.vn] = S.on_row;
            B.vslot[B.vn] = S.on_slot;
            B.vt[B.vn] = S.t;
            B.vn = (B.vn + 1) % 4;
        }
        /* a walker on our ledge: hop on it before it reaches us */
        for (int i = 0; i < NEN; i++) {
            const Enemy *e = &S.en[i];
            if (!e->on || e->dying || e->kind == E_FLYER || e->row != S.on_row || e->slot != S.on_slot)
                continue;
            float d = wrapd(e->u - S.u);
            if (fabsf(d) < 44 && fabsf(d) > 9 && (d * e->dir < 0 || fabsf(d) < 28)) {
                in->down |= KEY_A_;
                B.te = i;
                B.hold = false;
                B.hop = 0.1f;
                in->cx = d > 0 ? 0.6f : -0.6f;
                return;
            }
        }
        int bi = -1, bs = -1;
        float tu = S.u;
        int mode = bot_pick(V0, true, true, &bi, &bs, &tu);
        float want = wrapd(tu - S.u);
        bool blocked = false;
        if (mode == BM_NOW) {   /* unless something sits right above the jump */
            for (int i = 0; i < NEN; i++) {
                const Enemy *e = &S.en[i];
                float d = wrapd(e->u - S.u), ey = e->Y - S.Y;
                if (e->on && !e->dying && ey > 6 && ey < 85 && d * want >= -100 && fabsf(d) < fabsf(want) + 18 &&
                    !(e->row == bi && e->kind != E_FLYER))
                    blocked = true;
            }
        }
        const Row *cr0 = row_at(S.on_row);
        if (blocked && B.wait < 1.5f && !(cr0 && cr0->p[S.on_slot].kind == K_CRUMBLE)) {   /* let it move on first */
            B.wait += dt;
        } else if (mode == BM_NOW) {
            in->down |= KEY_A_;
            B.has = true;
            B.tr = bi;
            B.ts = bs;
            B.hold = true;
            B.wait = 0;
            mv = fabsf(want) > 4 ? (want > 0 ? 1.0f : -1.0f) : 0;
        } else if (mode == BM_WAIT) {   /* stand where it will come by */
            mv = fabsf(want) < 2 ? 0 : clampf(want / 14, -1, 1);
            B.wait = 0;
        } else if (mode == BM_WALK) {   /* to the takeoff point, the last bit as a run-up */
            const Row *r = row_at(bi);
            float dir = wrapd(r->p[bs].u - S.u) >= 0 ? 1.0f : -1.0f;
            mv = fabsf(want) > 20 ? clampf(want / 14, -1, 1) : dir;
            if (fabsf(want) < 2.5f) {
                in->down |= KEY_A_;
                B.has = true;
                B.tr = bi;
                B.ts = bs;
                B.hold = true;
                B.wait = 0;
            }
        } else {   /* nothing in reach: go to the edge nearest the next row's path ledge and leap */
            const Row *r = row_at(S.on_row + 1);
            const Row *cr = row_at(S.on_row);
            const Plat *cp = cr ? &cr->p[S.on_slot] : NULL;
            if (r) {
                float d = wrapd(r->p[r->path].u - S.u);
                if (cp && cp->kind != K_FULL) {
                    float rel = wrapd(S.u - cp->u);
                    d = clampf(rel + d, -(cp->hw - 4), cp->hw - 4) - rel;
                }
                mv = fabsf(d) < 3 ? 0 : clampf(d / 14, -1, 1);
                B.wait += dt;
                if (B.wait > 1.5f) {   /* leap out toward it */
                    in->down |= KEY_A_;
                    B.hold = true;
                    B.wait = 0;
                    mv = wrapd(r->p[r->path].u - S.u) > 0 ? 1.0f : -1.0f;
                }
            }
        }
        /* step out from under something about to land on us */
        const Row *cr = row_at(S.on_row);
        const Plat *cp = cr ? &cr->p[S.on_slot] : NULL;
        if (!(in->down & KEY_A_) && cp)
            for (int i = 0; i < NFALL; i++) {
                const Fall *f = &S.fall[i];
                float d = wrapd(f->u - S.u), away = d > 0 ? -1.0f : 1.0f;
                if (f->on && fabsf(f->sup - S.Y) < 2 && fabsf(d) < 14 &&
                    (cp->kind == K_FULL || fabsf(wrapd(S.u - cp->u) + away * 16) < cp->hw - 3))
                    mv = away;
            }
    } else {
        B.hop -= dt;
        float T = -1, pu = 0;
        if (B.te >= 0) {
            const Enemy *e = &S.en[B.te];
            if (!e->on || e->dying) {
                B.te = -1;
                B.hold = true;   /* a stomp: keep holding for the big bounce */
            } else {
                T = fly_time(S.Y, S.vy, e->Y + 6, holdnow || B.hop > 0);
                pu = e->u + (e->kind != E_FLYER && T > 0 ? e->dir * e->spd * T : 0);
                if (T < 0)
                    B.te = -1;
            }
        }
        if (B.te < 0 && B.has) {
            const Row *r = row_at(B.tr);
            if (!r || !solid(&r->p[B.ts]) || (S.vy > 0 && B.tr == S.on_row && B.ts == S.on_slot)) {
                B.has = false;
            } else {
                T = fly_time(S.Y, S.vy, r->Y, holdnow);
                if (T < 0)
                    B.has = false;
                else
                    pu = bot_pu(&r->p[B.ts], T);
            }
        }
        if (B.te < 0 && !B.has) {
            int bi, bs;
            float tu;
            if (bot_pick(S.vy, holdnow, false, &bi, &bs, &tu) == BM_NOW) {
                B.has = true;
                B.tr = bi;
                B.ts = bs;
                T = fly_time(S.Y, S.vy, row_at(bi)->Y, holdnow);
                pu = tu;
            }
        }
        if (T > 0) {
            float du = wrapd(pu - S.u);
            mv = fabsf(du) < 1.5f ? 0 : clampf(du / fmaxf(T, 0.06f) / VMAX, -1, 1);
        }
        if ((B.hold && S.vy > 0) || B.hop > 0 || (B.te >= 0 && S.vy < 0))
            in->held |= KEY_A_;
    }
    if (mv != 0 && fabsf(mv) < 0.3f)
        mv = mv > 0 ? 0.3f : -0.3f;
    in->cx = mv;
}

/* the cheat can't help once the run is wrapping up (or mid-updraft) */
static bool can_cheat(void) { return S.st == ST_PLAY; }

const MiniGame MG_TOWER = {
    .id = "tower",
    .title = "The Tower",
    .rules = "Help tiny Aron climb 300 m up the tower.\n"
             "Run around it and jump from ledge to ledge:\n"
             "some slide, some orbit, cracked ones crumble\n"
             "and mushrooms bounce you high.\n"
             "Jump on beetles and crows; touching them\n"
             "costs a heart. Dodge what falls from the sky:\n"
             "watch for the marker and the shadow.\n"
             "Don't drop below the screen: the mist rises!",
    .controls = "D-pad / Circle Pad: run around the tower\n"
                "A (or B): jump - hold for a higher jump\n"
                "Land on enemies to stomp them (hold A\n"
                "for a big bounce)\n"
                "START: pause",
    .cheat = "An updraft lifts Aron one whole tier (75 m)",
    .music = "tower_1",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .verdict = verdict,
    .can_cheat = can_cheat,
    .bot = bot,
};
