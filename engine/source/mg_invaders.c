/* The Hungry Sky: a stereoscopic vertical scrolling shooter. Aron's small
 * lantern-ship of light flies up through the heavens while the world
 * scrolls past underneath: the Cloud Sea, the halls of Seraphiel's
 * celestial architecture, the Purgatorium's glowing pools and the star
 * lanes. Purgatorium spirits and Seraphiel's angels come in waves (sweeping
 * formations, drifters, swooping divers, rammers and halo turrets), shoot
 * aimed bolts and spreads or fly into the ship. Some drop pickups: weapon
 * upgrades (spread shot, piercing beam, homing sparks, rapid fire) that
 * level up when the same type is picked up again and lose a level on every
 * hit, and, rarely, a heart.
 *
 * After about two and a quarter minutes comes Lord Ashveil, a childlike
 * cosmic being who is hungry, not evil. He has eight moves over three
 * phases, each with a tell: fan volleys, a spiral of light, the inhale
 * (hold Down), spat-out homing spirits, a cape-beam sweep, a starfield cape
 * of slow stars, a dash across the screen and, near the end, a hungry
 * tantrum. Beaten, he shrinks into a small, sated, sleepy creature.
 *
 * Depth: the world is layered behind the screen (far stars at +1, clouds and
 * halls and pools at +0.9 .. +0.3, mist and star streaks popping out at
 * -0.4), each layer scrolling at its own speed. The play field takes its
 * depth from its height (depth_at): things high up are far away, and come
 * toward you as they fall, so the ship flies "into" the screen.
 *
 * Score (0..100):
 *   25 * min(1, kills / (0.85 * stage enemies))     (cheat-cleared don't count)
 * + 20 * max(0, 1 - hits taken / 6)
 * + boss beaten: 35 + 20 * time bonus (full under 200 s, none after 320 s)
 *   boss not beaten: 15 * damage dealt to the boss
 * so anything above 60 requires beating the boss. */

#include "minigame.h"

#define MAXE 20   /* enemies at once */
#define MAXPS 36  /* player shots */
#define MAXES 84  /* enemy shots */
#define MAXM 8    /* Ashveil's spat-out spirits */
#define MAXI 6    /* pickups */
#define MAXP 56   /* particles */

#define V_SCROLL 55.0f      /* world scroll, pixels per second at depth 0 */
#define SEG_LEN 30.0f       /* seconds per area */
#define SHIP_SPEED 150.0f
#define SHIP_R 4.0f         /* the ship's hitbox: its glowing core */
#define X_MIN 12.0f
#define X_MAX 388.0f
#define Y_MIN 22.0f
#define Y_MAX 226.0f
#define HEARTS_START 4
#define HEARTS_MAX 5
#define WLV_MAX 4
#define BOSS_HP 900.0f
#define BOSS_Y 72.0f
#define D_FAR 0.28f
#define D_NEAR (-0.22f)

enum { W_LANTERN, W_SPREAD, W_BEAM, W_HOMING, W_RAPID, W_COUNT };
#define PK_HEART 9
enum { K_SPIRIT, K_ANGEL, K_CAPTAIN, K_TURRET, K_RAMMER };
enum { MV_SWEEP, MV_DRIFT, MV_COLUMN, MV_DIVE, MV_VFORM, MV_HOLD, MV_RAM };
enum { S_WISP, S_BOLT, S_ORB, S_STAR, S_SPARK };
enum { PS_BOLT, PS_PELLET, PS_SPARK };
enum { ST_STAGE, ST_WARN, ST_BOSS_IN, ST_BOSS, ST_BOSS_DOWN, ST_OVER };
enum { BM_IDLE, BM_FAN, BM_SPIRAL, BM_INHALE, BM_SPIT, BM_SWEEP, BM_STARS, BM_DASH, BM_TANTRUM, BM_COUNT };
enum { SEG_CLOUDS, SEG_HALLS, SEG_POOLS, SEG_LANES, SEG_VOID };
enum { P_SWEEP_L, P_SWEEP_R, P_DRIFT, P_COLUMN, P_DIVERS, P_VFORM, P_TURRET, P_RAMMERS };

/* ---- the stage: a timeline of waves ---------------------------------------- */

typedef struct {
    float t;
    u8 p, n;
    s16 x;
} Ev;

static const Ev EVS[] = {
    /* The Cloud Sea */
    {2, P_SWEEP_L, 6, 0},    {5.5f, P_SWEEP_R, 6, 0}, {9, P_DRIFT, 4, 0},     {12, P_COLUMN, 5, 120},
    {14, P_COLUMN, 5, 280},  {17, P_DIVERS, 2, 0},    {20, P_SWEEP_L, 7, 0},  {21, P_DRIFT, 3, 0},
    {24, P_TURRET, 1, 200},  {28, P_SWEEP_R, 7, 0},   {30.5f, P_DIVERS, 3, 0},
    /* Halls of Seraphiel */
    {35, P_VFORM, 5, 200},   {39, P_DRIFT, 5, 0},     {42, P_TURRET, 2, 0},   {46, P_RAMMERS, 2, 0},
    {49, P_SWEEP_L, 6, 0},   {51, P_SWEEP_R, 6, 0},   {54, P_VFORM, 5, 140},  {57, P_DIVERS, 3, 0},
    {60, P_TURRET, 1, 260},  {61, P_DRIFT, 4, 0},     {64.5f, P_RAMMERS, 3, 0},
    /* The Purgatorium Pools */
    {69, P_COLUMN, 6, 100},  {70, P_COLUMN, 6, 300},  {73.5f, P_DRIFT, 6, 0}, {76.5f, P_TURRET, 2, 0},
    {80, P_SWEEP_L, 8, 0},   {82.5f, P_RAMMERS, 2, 0}, {85, P_VFORM, 7, 200}, {89, P_DIVERS, 4, 0},
    {92, P_TURRET, 1, 140},  {93, P_DRIFT, 4, 0},     {96, P_SWEEP_R, 8, 0},  {98, P_SWEEP_L, 6, 0},
    /* The Star Lanes */
    {103, P_RAMMERS, 3, 0},  {106, P_VFORM, 7, 230},  {109.5f, P_TURRET, 2, 0}, {113, P_COLUMN, 6, 90},
    {113.5f, P_COLUMN, 6, 310}, {116.5f, P_DIVERS, 4, 0}, {119.5f, P_SWEEP_L, 8, 0}, {120.5f, P_SWEEP_R, 8, 0},
    {123.5f, P_TURRET, 3, 0}, {128.5f, P_RAMMERS, 4, 0}, {131, P_DRIFT, 6, 0},
};
#define NEV ((int)ARRAY_LEN(EVS))
#define TL_SCALE (SEG_LEN / 34.0f)   /* the timeline is written for 34 s areas */
#define STAGE_END (134.0f * TL_SCALE)

/* ---- state -------------------------------------------------------------------- */

typedef struct {
    bool alive;
    u8 kind, mv, idx, stage;
    bool fired;
    float x, y;           /* position */
    float vx, vy;         /* measured velocity (for the bot) */
    float mvx, mvy;       /* motion velocity (divers, rammers) */
    float x0, y0;         /* path origin / hold point */
    float t, s_t;         /* seconds alive (negative: waiting to enter), in stage */
    float hp;
    float fire_t, phase, hurt;
} Enemy;

typedef struct {
    bool alive;
    u8 kind;
    float x, y, vx, vy, life;
} PShot;

typedef struct {
    bool alive;
    u8 kind;
    float x, y, vx, vy, phase;
} EShot;

typedef struct {
    bool alive;
    float x, y, vx, vy, phase, t, hp, hurt;
} Minion;

typedef struct {
    bool alive;
    u8 kind;   /* W_SPREAD..W_RAPID or PK_HEART */
    float x, y, t;
} Pickup;

typedef struct {
    float x, y, vx, vy, life, max, size, depth;
    u32 color;
} Particle;

static struct {
    int st;
    float st_t, t;
    float dist, vscroll;  /* scrolled distance (pixels at depth 0) and speed */
    int seg;
    float seg_t;          /* seconds since the area changed */
    int ev;               /* next timeline event */

    /* the ship */
    float sx, sy;
    float fire_cd, invuln;
    int hearts, hits_taken;
    float heart_lost_t;
    int weapon, wlv;
    bool beam_on;
    float beam_snd_t, hit_snd_t;
    float wflash;         /* weapon changed / levelled: HUD and ship glow */
    float toast_t, toast_x, toast_y;
    int toast_kind, toast_lv;

    Enemy e[MAXE];
    PShot ps[MAXPS];
    EShot es[MAXES];
    Minion m[MAXM];
    Pickup pk[MAXI];
    Particle p[MAXP];

    /* Ashveil */
    float bx, by, bscale, bhp, bt;
    int bphase;           /* 1..3 */
    float bphase_t;       /* > 0: between phases (invulnerable) */
    int bmove, bm_stage, bm_k, bm_n, last_move, bm_gap;
    float bm_t, bm_acc, bm_a, bm_a0, bm_a1, bm_dir, bm_lane;
    bool pull, tantrum_done;
    float bhurt, mouth_kick, boss_snd_t;

    /* scoring */
    int points, kills, spawned_total, skipped, kills_since_drop;
    bool reached_boss, boss_beaten;
    float end_t, boss_dmg_frac;

    /* golden light */
    float flash, flash_x, flash_y;
} G;

#ifdef INV_DEBUG
static int dc;
#define mg_rect(...) (dc++, mg_rect(__VA_ARGS__))
#define mg_circle(...) (dc++, mg_circle(__VA_ARGS__))
#define mg_tri(...) (dc++, mg_tri(__VA_ARGS__))
#define mg_line(...) (dc++, mg_line(__VA_ARGS__))
#define mg_text(...) (dc++, mg_text(__VA_ARGS__))
#define mg_text_centered(...) (dc++, mg_text_centered(__VA_ARGS__))
#endif

/* ---- small helpers ------------------------------------------------------- */

static float randr(float lo, float hi) { return lo + (hi - lo) * mg_randf(); }
static void sfx(const char *name) { mg_sfx_pitch(name, randr(0.95f, 1.05f)); }
static float ease(float t)
{
    t = clampf(t, 0, 1);
    return 1 - (1 - t) * (1 - t);
}
static float dist2(float ax, float ay, float bx, float by) { return (ax - bx) * (ax - bx) + (ay - by) * (ay - by); }

static u32 mixc(u32 a, u32 b, float t)
{
    u32 out = 0;
    for (int s = 0; s < 32; s += 8) {
        float ca = (float)((a >> s) & 0xFF), cb = (float)((b >> s) & 0xFF);
        out |= (u32)(ca + (cb - ca) * t + 0.5f) << s;
    }
    return out;
}

static u32 hsh(u32 a, u32 b)
{
    u32 h = a * 0x9E3779B1u ^ (b + 0x7F4A7C15u) * 0x85EBCA77u;
    h ^= h >> 15;
    h *= 0x2C1B3C6Du;
    h ^= h >> 12;
    h *= 0x297A2D39u;
    h ^= h >> 15;
    return h;
}
static float hf(u32 h, int k) { return (float)((h >> (k * 8)) & 0xFF) / 255.0f; }

/* Stereo depth of the play field at height y: far at the top, near at the bottom. */
static float depth_at(float y) { return lerpf(D_FAR, D_NEAR, clampf((y - 30) / 195.0f, 0, 1)); }
static float depth_scale(float d) { return 1.0f - 0.3f * d; }

static int seg_at(float dist)
{
    int s = (int)(dist / (SEG_LEN * V_SCROLL));
    return s < 0 ? 0 : s > SEG_VOID ? SEG_VOID : s;
}

static void burst(float x, float y, int n, u32 color, float speed)
{
    float d = depth_at(y);
    for (int k = 0; k < n; k++)
        for (int i = 0; i < MAXP; i++)
            if (G.p[i].life <= 0) {
                Particle *p = &G.p[i];
                float a = randr(0, 6.2832f), s = randr(0.3f, 1.0f) * speed;
                p->x = x;
                p->y = y;
                p->vx = cosf(a) * s;
                p->vy = sinf(a) * s;
                p->max = p->life = randr(0.3f, 0.7f);
                p->size = randr(1.2f, 2.8f);
                p->depth = d;
                p->color = color;
                break;
            }
}

static const u32 WCOL[W_COUNT] = {RGBA(255, 214, 120, 255), RGBA(120, 255, 170, 255), RGBA(255, 246, 200, 255),
                                  RGBA(255, 140, 220, 255), RGBA(255, 160, 70, 255)};
static const char *const WNAME[W_COUNT] = {"Lantern shot", "Spread shot", "Piercing beam", "Homing sparks",
                                           "Rapid fire"};
static const char *const WLETTER[W_COUNT] = {"L", "S", "B", "H", "R"};
static const char *const SEG_NAME[] = {"The Cloud Sea", "Halls of Seraphiel", "The Purgatorium Pools",
                                       "The Star Lanes", "The Hungry Void"};

/* ---- shots --------------------------------------------------------------- */

static void fire_es(int kind, float x, float y, float vx, float vy)
{
    for (int i = 0; i < MAXES; i++)
        if (!G.es[i].alive) {
            EShot *s = &G.es[i];
            s->alive = true;
            s->kind = (u8)kind;
            s->x = x;
            s->y = y;
            s->vx = vx;
            s->vy = vy;
            s->phase = randr(0, 6.28f);
            return;
        }
}

static void aim_es(int kind, float x, float y, float speed, float off)
{
    float a = atan2f(G.sy - y, G.sx - x) + off;
    fire_es(kind, x, y, cosf(a) * speed, sinf(a) * speed);
}

static float es_r(int kind) { return kind == S_ORB ? 4.5f : kind == S_SPARK ? 3.0f : 3.5f; }

static void fire_ps(int kind, float x, float y, float vx, float vy)
{
    for (int i = 0; i < MAXPS; i++)
        if (!G.ps[i].alive) {
            PShot *s = &G.ps[i];
            s->alive = true;
            s->kind = (u8)kind;
            s->x = x;
            s->y = y;
            s->vx = vx;
            s->vy = vy;
            s->life = kind == PS_SPARK ? 1.8f : 1.2f;
            return;
        }
}

/* ---- enemies --------------------------------------------------------------- */

static const float EHP[] = {2, 4, 8, 16, 3};
static float e_r(const Enemy *e)
{
    return e->kind == K_SPIRIT ? 9.0f : e->kind == K_TURRET ? 15.0f : e->kind == K_CAPTAIN ? 12.0f : 11.0f;
}
static bool e_visible(const Enemy *e) { return e->alive && e->t >= 0; }

static Enemy *spawn(int kind, int mv, float x0, float y0, int idx, float delay, float hp)
{
    for (int i = 0; i < MAXE; i++)
        if (!G.e[i].alive) {
            Enemy *e = &G.e[i];
            memset(e, 0, sizeof(*e));
            e->alive = true;
            e->kind = (u8)kind;
            e->mv = (u8)mv;
            e->idx = (u8)idx;
            e->x = e->x0 = x0;
            e->y0 = y0;
            e->y = -40;
            e->t = -delay;
            e->hp = hp > 0 ? hp : EHP[kind];
            e->phase = randr(0, 6.2832f);
            e->fire_t = randr(0.8f, 2.0f);
            return e;
        }
    G.skipped++;
    return NULL;
}

static void spawn_pattern(const Ev *ev)
{
    int n = ev->n;
    switch (ev->p) {
    case P_SWEEP_L:
    case P_SWEEP_R: {
        float y0 = randr(22, 44);
        for (int k = 0; k < n; k++)
            spawn(K_SPIRIT, MV_SWEEP, ev->p == P_SWEEP_L ? -24 : 424, y0, k, k * 0.3f, 1);
        break;
    }
    case P_DRIFT:
        for (int k = 0; k < n; k++)
            spawn(K_SPIRIT, MV_DRIFT, 40 + 320 * (k + 0.5f) / n + randr(-14, 14), -16 - randr(0, 50), k, 0, 3);
        break;
    case P_COLUMN:
        for (int k = 0; k < n; k++)
            spawn(K_SPIRIT, MV_COLUMN, ev->x, 0, k, k * 0.36f, 2);
        break;
    case P_DIVERS:
        for (int k = 0; k < n; k++)
            spawn(K_ANGEL, MV_DIVE, 60 + 280 * (k + 0.5f) / n + randr(-20, 20), randr(46, 80), k, k * 0.7f, 3);
        break;
    case P_VFORM:
        for (int k = 0; k < n; k++)
            spawn(k == 0 ? K_CAPTAIN : K_ANGEL, MV_VFORM, ev->x, 0, k, 0, 0);
        break;
    case P_TURRET:
        for (int k = 0; k < n; k++) {
            float x = n == 1 ? ev->x : 80 + 240.0f * k / (n - 1);
            spawn(K_TURRET, MV_HOLD, x, 56 + (k % 2) * 14, k, k * 0.4f, 0);
        }
        break;
    case P_RAMMERS:
        for (int k = 0; k < n; k++)
            spawn(K_RAMMER, MV_RAM, randr(50, 350), randr(38, 62), k, k * 0.8f, 0);
        break;
    }
}

/* ---- the player ------------------------------------------------------------ */

static void toast(int kind, int lv)
{
    G.toast_t = 1.2f;
    G.toast_x = G.sx;
    G.toast_y = G.sy - 18;
    G.toast_kind = kind;
    G.toast_lv = lv;
}

static void hit_player(const char *why)
{
    (void)why;
    if (G.invuln > 0 || G.hearts <= 0 || G.st == ST_BOSS_DOWN || G.st == ST_OVER)
        return;
    G.hearts--;
    G.hits_taken++;
#ifdef INV_DEBUG
    printf("invaders: hit (%s) at %.1f s, state %d move %d ship %.0f,%.0f\n", why, G.t, G.st, G.bmove, G.sx, G.sy);
#endif
    G.invuln = 1.8f;
    burst(G.sx, G.sy, 14, RGBA(255, 220, 150, 255), 90);
    sfx("invaders_player_hit");
    if (G.wlv > 0) {   /* a hit costs a weapon level */
        G.wlv--;
        if (G.wlv == 0)
            G.weapon = W_LANTERN;
        G.wflash = 0.8f;
        toast(G.weapon, -G.wlv - 1);
        mg_sfx("invaders_weapon_down");
    }
    if (G.hearts <= 0) {
        mg_sfx("invaders_game_over");
        G.st = ST_OVER;
        G.st_t = 0;
        G.pull = false;
    } else {
        G.heart_lost_t = 0.35f;
    }
}

static void drop(float x, float y, int kind)
{
    for (int i = 0; i < MAXI; i++)
        if (!G.pk[i].alive) {
            Pickup *p = &G.pk[i];
            p->alive = true;
            p->kind = (u8)kind;
            p->x = clampf(x, 20, TOP_W - 20);
            p->y = y;
            p->t = 0;
            sfx("invaders_drop");
            return;
        }
}

static int random_weapon(void)
{
    if (G.weapon != W_LANTERN && mg_randf() < 0.45f)
        return G.weapon;
    return mg_randi(W_SPREAD, W_RAPID);
}

static void maybe_drop(float x, float y, int kind)
{
    float pw = kind == K_TURRET ? 1.0f : kind == K_CAPTAIN ? 0.5f : kind == K_SPIRIT ? 0.025f : 0.07f;
    float ph = kind == K_TURRET ? 0.22f : 0.012f;
    if (G.hearts < HEARTS_MAX && mg_randf() < ph) {
        drop(x, y, PK_HEART);
    } else if (mg_randf() < pw || G.kills_since_drop >= 18) {
        drop(x, y, random_weapon());
        G.kills_since_drop = 0;
    }
}

static void kill_enemy(Enemy *e, bool credit)
{
    e->alive = false;
    if (credit) {
        static const int PTS[] = {100, 200, 400, 600, 250};
        G.kills++;
        G.kills_since_drop++;
        G.points += PTS[e->kind];
        maybe_drop(e->x, e->y, e->kind);
    }
    if (e->kind == K_SPIRIT) {
        burst(e->x, e->y, 8, RGBA(150, 240, 255, 255), 60);
        sfx("invaders_hit_spirit");
    } else {
        burst(e->x, e->y, e->kind == K_TURRET ? 16 : 10, RGBA(255, 220, 120, 255), 70);
        burst(e->x, e->y, 4, MG_WHITE, 40);
        sfx("invaders_hit_angel");
    }
}

static void damage_enemy(Enemy *e, float dmg)
{
    e->hp -= dmg;
    if (e->hp <= 0) {
        kill_enemy(e, true);
        return;
    }
    e->hurt = 0.1f;
    if (e->kind != K_SPIRIT && G.hit_snd_t <= 0) {
        sfx("invaders_angel_armor");
        G.hit_snd_t = 0.09f;
    }
}

static void boss_phase_check(void);

static void damage_boss(float dmg, bool mouth)
{
    if (G.st != ST_BOSS)
        return;
    if (G.bphase_t > 0) {   /* between phases he shrugs it off */
        return;
    }
    G.bhp -= mouth ? dmg * 2 : dmg;
    G.points += mouth ? 20 : 10;
    G.bhurt = 0.1f;
    if (G.boss_snd_t <= 0) {
        sfx(mouth ? "invaders_boss_gulp" : "invaders_boss_hit");
        G.boss_snd_t = 0.11f;
    }
    boss_phase_check();
}

static void damage_minion(Minion *m, float dmg)
{
    m->hp -= dmg;
    m->hurt = 0.1f;
    if (m->hp <= 0) {
        m->alive = false;
        G.points += 150;
        burst(m->x, m->y, 6, RGBA(200, 160, 255, 255), 50);
        sfx("invaders_hit_spirit");
        if (mg_randf() < 0.08f)
            drop(m->x, m->y, G.hearts < 3 && mg_randf() < 0.3f ? PK_HEART : random_weapon());
    }
}

static void fire_weapon(void)
{
    float x = G.sx, y = G.sy - 12;
    int lv = G.wlv;
    switch (G.weapon) {
    case W_LANTERN:
        fire_ps(PS_BOLT, x, y, 0, -380);
        G.fire_cd = 0.2f;
        sfx("invaders_shoot");
        break;
    case W_RAPID: {
        static const float CD[4] = {0.125f, 0.17f, 0.135f, 0.16f};
        if (lv == 1) {
            fire_ps(PS_BOLT, x, y, 0, -430);
        } else {
            fire_ps(PS_BOLT, x - 5, y, 0, -430);
            fire_ps(PS_BOLT, x + 5, y, 0, -430);
            if (lv >= 4) {
                fire_ps(PS_BOLT, x - 9, y + 2, -40, -425);
                fire_ps(PS_BOLT, x + 9, y + 2, 40, -425);
            }
        }
        G.fire_cd = CD[lv - 1];
        mg_sfx_pitch("invaders_rapid", randr(0.92f, 1.1f));
        break;
    }
    case W_SPREAD: {
        static const int N[4] = {3, 5, 5, 7};
        static const float SPAN[4] = {0.42f, 0.62f, 0.7f, 0.95f}, CD[4] = {0.3f, 0.34f, 0.28f, 0.3f};
        int n = N[lv - 1];
        for (int i = 0; i < n; i++) {
            float a = -1.5708f + (i - (n - 1) * 0.5f) * SPAN[lv - 1] / (n - 1);
            fire_ps(PS_PELLET, x, y, cosf(a) * 330, sinf(a) * 330);
        }
        G.fire_cd = CD[lv - 1];
        sfx("invaders_spread");
        break;
    }
    case W_HOMING: {
        int n = lv + 1;
        for (int i = 0; i < n; i++) {
            float a = -1.5708f + (i - (n - 1) * 0.5f) * 0.45f;
            fire_ps(PS_SPARK, x, y, cosf(a) * 240, sinf(a) * 240);
        }
        G.fire_cd = lv == 2 ? 0.32f : 0.3f;
        sfx("invaders_homing");
        break;
    }
    }
}

static void update_ship(const Input *in, float dt)
{
    float mx = in->cx, my = in->cy;
    if (in->held & KEY_LEFT_)
        mx = -1;
    if (in->held & KEY_RIGHT_)
        mx = 1;
    if (in->held & KEY_UP_)
        my = 1;
    if (in->held & KEY_DOWN_)
        my = -1;
    if (fabsf(mx) < 0.15f)
        mx = 0;
    if (fabsf(my) < 0.15f)
        my = 0;
    float len = sqrtf(mx * mx + my * my);
    if (len > 1) {
        mx /= len;
        my /= len;
    }
    G.sx += mx * SHIP_SPEED * dt;
    G.sy -= my * SHIP_SPEED * dt;

    /* Ashveil's inhale drags the ship toward his mouth */
    if (G.pull) {
        float mxp = G.bx, myp = G.by + 24;
        float dx = mxp - G.sx, dy = myp - G.sy, d = sqrtf(dx * dx + dy * dy) + 1;
        G.sx += dx / d * 95.0f * dt;
        G.sy += dy / d * 95.0f * dt;
        if (d < 22) {
            hit_player("inhale");
            G.sy = Y_MAX - 4;
            sfx("invaders_boss_gulp");
        }
    }
    G.sx = clampf(G.sx, X_MIN, X_MAX);
    G.sy = clampf(G.sy, Y_MIN, Y_MAX);

    /* fire: a tap fires at once, holding A auto-fires */
    G.fire_cd -= dt;
    bool can = G.st == ST_STAGE || G.st == ST_WARN || G.st == ST_BOSS_IN || G.st == ST_BOSS;
    bool held = (in->held | in->down) & KEY_A_;
    bool beam = can && held && G.weapon == W_BEAM;
    if (beam && !G.beam_on) {
        mg_sfx_pitch("invaders_beam", 0.9f + 0.06f * G.wlv);
        G.beam_snd_t = 0.6f;
    } else if (beam && (G.beam_snd_t -= dt) <= 0) {
        mg_sfx_pitch("invaders_beam", 0.88f + 0.06f * G.wlv);
        G.beam_snd_t = 0.6f;
    }
    G.beam_on = beam;
    if (!can || G.weapon == W_BEAM)
        return;
    if (((in->down & KEY_A_) && G.fire_cd <= 0.05f) || (held && G.fire_cd <= 0))
        fire_weapon();
}

static float beam_w(void) { return 2.0f + 3.0f * G.wlv; }

static void update_beam(float dt)
{
    if (!G.beam_on)
        return;
    static const float DPS[4] = {8, 11, 14, 17};
    float dps = DPS[G.wlv - 1], hw = beam_w() * 0.5f;
    for (int i = 0; i < MAXE; i++) {
        Enemy *e = &G.e[i];
        if (e_visible(e) && e->y < G.sy && e->y > -10 && fabsf(e->x - G.sx) < hw + e_r(e))
            damage_enemy(e, dps * dt);
    }
    for (int i = 0; i < MAXM; i++) {
        Minion *m = &G.m[i];
        if (m->alive && m->y < G.sy && fabsf(m->x - G.sx) < hw + 8)
            damage_minion(m, dps * dt);
    }
    if (G.st == ST_BOSS && G.by < G.sy && G.by > -40 && fabsf(G.bx - G.sx) < hw + 40) {
        bool mouth = G.pull && fabsf(G.bx - G.sx) < 16;
        damage_boss(dps * dt, mouth);
    }
}

/* The nearest thing a homing spark can chase. */
static bool homing_target(float x, float y, float *tx, float *ty)
{
    float best = 1e9f;
    bool found = false;
    for (int i = 0; i < MAXE; i++) {
        const Enemy *e = &G.e[i];
        if (!e_visible(e) || e->y < -10 || e->y > y + 30)
            continue;
        float d = dist2(x, y, e->x, e->y);
        if (d < best)
            best = d, *tx = e->x, *ty = e->y, found = true;
    }
    for (int i = 0; i < MAXM; i++) {
        const Minion *m = &G.m[i];
        if (!m->alive || m->y > y + 30)
            continue;
        float d = dist2(x, y, m->x, m->y);
        if (d < best)
            best = d, *tx = m->x, *ty = m->y, found = true;
    }
    if (G.st == ST_BOSS && G.bphase_t <= 0 && G.by > -30) {
        float d = dist2(x, y, G.bx, G.by) * 1.3f;
        if (d < best)
            *tx = G.bx, *ty = G.by, found = true;
    }
    return found;
}

static void update_player_shots(float dt)
{
    for (int i = 0; i < MAXPS; i++) {
        PShot *s = &G.ps[i];
        if (!s->alive)
            continue;
        s->life -= dt;
        if (s->kind == PS_SPARK) {
            float tx, ty;
            if (homing_target(s->x, s->y, &tx, &ty)) {
                float want = atan2f(ty - s->y, tx - s->x), cur = atan2f(s->vy, s->vx);
                float da = want - cur;
                while (da > 3.14159f)
                    da -= 6.28318f;
                while (da < -3.14159f)
                    da += 6.28318f;
                float turn = 7.0f * dt;
                cur += clampf(da, -turn, turn);
                s->vx = cosf(cur) * 250;
                s->vy = sinf(cur) * 250;
            }
        }
        s->x += s->vx * dt;
        s->y += s->vy * dt;
        if (s->y < -12 || s->y > TOP_H + 10 || s->x < -12 || s->x > TOP_W + 12 || s->life <= 0) {
            s->alive = false;
            continue;
        }
        for (int k = 0; k < MAXE && s->alive; k++) {
            Enemy *e = &G.e[k];
            if (!e_visible(e))
                continue;
            float r = e_r(e) * depth_scale(depth_at(e->y)) + 2;
            if (dist2(s->x, s->y, e->x, e->y) < r * r) {
                s->alive = false;
                burst(s->x, s->y, 2, MG_WHITE, 40);
                damage_enemy(e, 1);
            }
        }
        for (int k = 0; k < MAXM && s->alive; k++) {
            Minion *m = &G.m[k];
            if (m->alive && dist2(s->x, s->y, m->x, m->y) < 10 * 10) {
                s->alive = false;
                damage_minion(m, 1);
            }
        }
        if (s->alive && G.st == ST_BOSS) {
            float dx = s->x - G.bx, dy = s->y - G.by;
            if (dx * dx + dy * dy < 44.0f * 44.0f) {
                bool mouth = G.pull && fabsf(dx) < 16 && fabsf(dy - 24) < 16;
                s->alive = false;
                burst(s->x, s->y, mouth ? 4 : 2, mouth ? MG_GOLD : RGBA(220, 200, 255, 255), 45);
                damage_boss(1, mouth);
            }
        }
    }
}

static void update_enemy_shots(float dt)
{
    float mx = G.bx, my = G.by + 24;
    for (int i = 0; i < MAXES; i++) {
        EShot *s = &G.es[i];
        if (!s->alive)
            continue;
        s->phase += dt;
        if (G.pull) {   /* the inhale swallows his own light too */
            float dx = mx - s->x, dy = my - s->y, d = sqrtf(dx * dx + dy * dy) + 1;
            float k = clampf(2.5f * dt, 0, 1);
            s->vx += (dx / d * 140 - s->vx) * k;
            s->vy += (dy / d * 140 - s->vy) * k;
            if (d < 14) {
                s->alive = false;
                continue;
            }
        }
        float wob = s->kind == S_WISP ? cosf(s->phase * 5) * 20 : s->kind == S_STAR ? cosf(s->phase * 1.6f) * 12 : 0;
        s->x += (s->vx + wob) * dt;
        s->y += s->vy * dt;
        if (s->y > TOP_H + 10 || s->y < -20 || s->x < -20 || s->x > TOP_W + 20) {
            s->alive = false;
            continue;
        }
        float r = es_r(s->kind) + SHIP_R;
        if (dist2(s->x, s->y, G.sx, G.sy) < r * r && G.invuln <= 0) {
            s->alive = false;
            static const char *const SN[] = {"wisp", "bolt", "orb", "star", "spark"};
            hit_player(SN[s->kind]);
        }
    }
}

static void update_particles(float dt)
{
    for (int i = 0; i < MAXP; i++) {
        Particle *p = &G.p[i];
        if (p->life <= 0)
            continue;
        p->life -= dt;
        p->x += p->vx * dt;
        p->y += p->vy * dt;
        p->vx *= 1 - 2.0f * dt;
        p->vy *= 1 - 2.0f * dt;
    }
}

static void update_pickups(float dt)
{
    for (int i = 0; i < MAXI; i++) {
        Pickup *p = &G.pk[i];
        if (!p->alive)
            continue;
        p->t += dt;
        p->y += (p->t < 0.4f ? -40.0f : 30.0f) * dt;
        p->x += sinf(p->t * 2.2f) * 12 * dt;
        float d = sqrtf(dist2(p->x, p->y, G.sx, G.sy));
        if (d < 36 && G.st != ST_OVER) {   /* a gentle magnet */
            p->x += (G.sx - p->x) / (d + 1) * 170 * dt;
            p->y += (G.sy - p->y) / (d + 1) * 170 * dt;
        }
        if (d < 14 && G.st != ST_OVER && G.st != ST_BOSS_DOWN) {
            p->alive = false;
            if (p->kind == PK_HEART) {
                if (G.hearts < HEARTS_MAX)
                    G.hearts++;
                else
                    G.points += 500;
                toast(PK_HEART, 0);
                burst(p->x, p->y, 10, RGBA(255, 120, 150, 255), 60);
                mg_sfx("invaders_pickup_heart");
            } else if (p->kind == G.weapon) {
                if (G.wlv < WLV_MAX) {
                    G.wlv++;
                    mg_sfx_pitch("invaders_weapon_up", 0.9f + 0.08f * G.wlv);
                } else {
                    G.points += 500;
                    mg_sfx_pitch("invaders_weapon_up", 1.3f);
                }
                toast(G.weapon, G.wlv);
                G.wflash = 1.0f;
                burst(p->x, p->y, 10, WCOL[G.weapon], 60);
            } else {
                G.weapon = p->kind;
                if (G.wlv < 1)
                    G.wlv = 1;
                toast(G.weapon, G.wlv);
                G.wflash = 1.0f;
                burst(p->x, p->y, 10, WCOL[G.weapon], 60);
                mg_sfx("invaders_pickup_weapon");
            }
            continue;
        }
        if (p->y > TOP_H + 14)
            p->alive = false;
    }
}

/* ---- update: the stage ----------------------------------------------------- */

static void update_enemies(float dt)
{
    int seg = G.seg > SEG_LANES ? SEG_LANES : G.seg;
    for (int i = 0; i < MAXE; i++) {
        Enemy *e = &G.e[i];
        if (!e->alive)
            continue;
        float px = e->x, py = e->y;
        e->t += dt;
        e->s_t += dt;
        if (e->hurt > 0)
            e->hurt -= dt;
        if (e->t < 0) {
            e->vx = e->vy = 0;
            continue;
        }
        float u = e->t;
        bool on = e->y > 8 && e->y < 180;   /* close enough to shoot */
        switch (e->mv) {
        case MV_SWEEP: {
            float dir = e->x0 < 200 ? 1.0f : -1.0f;
            e->x = e->x0 + dir * 128 * u;
            e->y = e->y0 + 100 * sinf(3.14159f * clampf(u / 3.5f, 0, 1));
            if (!e->fired && u > 1.3f && seg >= SEG_HALLS && e->idx % 2 == 0) {
                e->fired = true;
                aim_es(S_WISP, e->x, e->y + 5, 66 + 6 * seg, 0);
                sfx("invaders_wisp");
            }
            if (u > 3.7f)
                e->alive = false;
            break;
        }
        case MV_DRIFT:
            e->y = e->y0 + 32 * u;
            e->x = e->x0 + 26 * sinf(1.3f * u + e->phase);
            e->fire_t -= dt;
            if (e->fire_t <= 0 && on) {
                e->fire_t = randr(2.0f, 3.0f) - 0.2f * seg;
                aim_es(S_WISP, e->x, e->y + 5, 60 + 8 * seg, 0);
                sfx("invaders_wisp");
            }
            if (e->y > 260)
                e->alive = false;
            break;
        case MV_COLUMN:
            e->y = -16 + 56 * u;
            e->x = e->x0 + 52 * sinf(1.7f * u);
            if (!e->fired && e->y > 70 && e->idx % 3 == 1) {
                e->fired = true;
                aim_es(S_WISP, e->x, e->y + 5, 62 + 8 * seg, 0);
                sfx("invaders_wisp");
            }
            if (e->y > 260)
                e->alive = false;
            break;
        case MV_DIVE:
            if (e->stage == 0) {
                e->y = lerpf(-20, e->y0, ease(u / 0.8f));
                if (u >= 0.8f)
                    e->stage = 1, e->s_t = 0;
            } else if (e->stage == 1) {
                if (e->s_t >= 0.45f) {
                    aim_es(S_BOLT, e->x, e->y + 8, 120 + 6 * seg, 0);
                    sfx("invaders_enemy_shot");
                    sfx("invaders_dive");
                    e->stage = 2;
                    e->mvx = 0;
                    e->mvy = 30;
                }
            } else {
                float want = clampf((G.sx - e->x) * 1.4f, -110, 110);
                e->mvx += (want - e->mvx) * clampf(2.5f * dt, 0, 1);
                e->mvy = fminf(e->mvy + 260 * dt, 210);
                e->x += e->mvx * dt;
                e->y += e->mvy * dt;
                if (e->y > 262)
                    e->alive = false;
            }
            break;
        case MV_VFORM: {
            int k = (e->idx + 1) / 2;
            float side = e->idx % 2 ? -1.0f : 1.0f;
            float cy = u < 2.5f ? lerpf(-40, 66, ease(u / 2.5f)) : u < 7.5f ? 66 + 3 * sinf(u * 2) : 66 + (u - 7.5f) * 70;
            e->x = e->x0 + side * k * 34 + 10 * sinf(G.t * 1.1f);
            e->y = cy - k * 16;
            e->fire_t -= dt;
            if (e->fire_t <= 0 && on && u > 2) {
                e->fire_t = randr(1.8f, 3.2f);
                aim_es(S_BOLT, e->x, e->y + 8, 92 + 8 * seg, 0);
                sfx("invaders_enemy_shot");
            }
            if (e->y > 270)
                e->alive = false;
            break;
        }
        case MV_HOLD:
            if (u < 1.8f) {
                e->y = lerpf(-34, e->y0, ease(u / 1.8f));
            } else if (u < 10.5f) {
                e->y = e->y0 + 3 * sinf(u * 2);
                e->x = e->x0 + 20 * sinf(0.7f * (u - 1.8f));
                e->fire_t -= dt;
                e->stage = e->fire_t < 0.45f;   /* the halo charges: a tell */
                if (e->fire_t <= 0) {
                    int n = seg >= SEG_POOLS ? 5 : 3;
                    for (int s = 0; s < n; s++)
                        aim_es(S_BOLT, e->x, e->y + 10, 95 + 5 * seg, (s - (n - 1) * 0.5f) * 0.24f);
                    sfx("invaders_turret_shot");
                    e->fire_t = 1.6f - 0.1f * seg;
                }
            } else {
                e->stage = 0;
                e->y -= 80 * dt;
                if (e->y < -50)
                    e->alive = false;
            }
            break;
        case MV_RAM:
            if (e->stage == 0) {
                e->y = lerpf(-24, e->y0, ease(u));
                e->x += (G.sx - e->x) * clampf(1.5f * dt, 0, 1);
                if (u >= 1.0f) {
                    e->stage = 1;
                    e->s_t = 0;
                    float dx = G.sx - e->x, dy = G.sy - e->y, d = sqrtf(dx * dx + dy * dy) + 0.01f;
                    e->mvx = dx / d;
                    e->mvy = dy / d;
                    sfx("invaders_ram_charge");
                }
            } else if (e->stage == 1) {
                if (e->s_t >= 0.7f) {
                    e->stage = 2;
                    sfx("invaders_ram");
                }
            } else {
                e->x += e->mvx * 280 * dt;
                e->y += e->mvy * 280 * dt;
                if (e->x < -40 || e->x > TOP_W + 40 || e->y > TOP_H + 30 || e->y < -60)
                    e->alive = false;
            }
            break;
        }
        e->vx = (e->x - px) / dt;
        e->vy = (e->y - py) / dt;
        if (!e->alive)
            continue;
        /* flying into the ship */
        float r = e_r(e) * 0.8f + SHIP_R;
        if (G.invuln <= 0 && dist2(e->x, e->y, G.sx, G.sy) < r * r) {
            hit_player("ram");
            sfx("invaders_ram_hit");
            if (e->kind == K_TURRET)
                damage_enemy(e, 3);
            else
                kill_enemy(e, false);
        }
    }
}

/* ---- update: Ashveil ------------------------------------------------------- */

static const float TELL[BM_COUNT] = {0, 0.55f, 0.8f, 1.0f, 0.6f, 1.0f, 0.9f, 0.55f, 1.0f};

static void clear_enemy_shots(void)
{
    for (int i = 0; i < MAXES; i++)
        if (G.es[i].alive) {
            if (i % 3 == 0)
                burst(G.es[i].x, G.es[i].y, 1, MG_GOLD, 30);
            G.es[i].alive = false;
        }
}

static void boss_begin(int m)
{
    G.bmove = m;
    G.bm_stage = 0;
    G.bm_t = 0;
    G.bm_k = 0;
    G.bm_acc = 0;
    if (m == BM_IDLE)
        return;
    G.last_move = m;
#ifdef INV_DEBUG
    printf("invaders: boss move %d at %.1f s (hp %.0f, phase %d)\n", m, G.t, G.bhp, G.bphase);
#endif
    mg_sfx_pitch("invaders_boss_tell", 0.8f + 0.06f * m);
    switch (m) {
    case BM_SWEEP:
        G.bm_dir = G.sx < 200 ? 1.0f : -1.0f;   /* start on the far side */
        G.bm_a0 = G.bm_dir > 0 ? 0.35f : 2.79f;
        G.bm_a1 = G.bm_dir > 0 ? 2.79f : 0.35f;
        break;
    case BM_DASH:
        G.bm_n = G.bphase >= 3 ? 2 : 1;
        break;
    case BM_STARS:
        G.bm_gap = mg_randi(2, 6);
        break;
    case BM_SPIRAL:
        G.bm_a = randr(0, 6.28f);
        G.bm_dir = mg_randf() < 0.5f ? 1.0f : -1.0f;
        break;
    case BM_TANTRUM:
        G.tantrum_done = true;
        break;
    }
}

static int boss_pick(void)
{
    static const u8 L1[] = {BM_FAN, BM_SPIRAL, BM_SPIT, BM_FAN};
    static const u8 L2[] = {BM_FAN, BM_INHALE, BM_SPIRAL, BM_SWEEP, BM_STARS};
    static const u8 L3[] = {BM_DASH, BM_SPIRAL, BM_INHALE, BM_SPIT, BM_SWEEP, BM_FAN, BM_STARS, BM_DASH};
    bool low = G.bhp < BOSS_HP * 0.2f;
    if (G.bphase >= 3 && low && !G.tantrum_done)
        return BM_TANTRUM;
    const u8 *l = G.bphase == 1 ? L1 : G.bphase == 2 ? L2 : L3;
    int n = G.bphase == 1 ? (int)ARRAY_LEN(L1) : G.bphase == 2 ? (int)ARRAY_LEN(L2) : (int)ARRAY_LEN(L3);
    if (G.bphase >= 3 && low && mg_randf() < 0.3f && G.last_move != BM_TANTRUM)
        return BM_TANTRUM;
    for (int tries = 0; tries < 8; tries++) {
        int m = l[mg_randi(0, n - 1)];
        if (m != G.last_move)
            return m;
    }
    return l[0];
}

static void boss_phase_check(void)
{
    if (G.bhp <= 0)
        return;   /* defeat is handled in update_boss */
    int phase = G.bhp > BOSS_HP * 2 / 3 ? 1 : G.bhp > BOSS_HP / 3 ? 2 : 3;
    if (phase <= G.bphase)
        return;
    G.bphase = phase;
    G.bphase_t = 2.4f;
    G.pull = false;
    boss_begin(BM_IDLE);
    clear_enemy_shots();
    for (int i = 0; i < MAXM; i++)
        if (G.m[i].alive) {
            burst(G.m[i].x, G.m[i].y, 3, MG_GOLD, 50);
            G.m[i].alive = false;
        }
    mg_sfx("invaders_boss_phase");
    /* he spills a little of the light he ate */
    drop(G.bx - 30, G.by + 30, random_weapon());
    if (G.hearts < HEARTS_MAX)
        drop(G.bx + 30, G.by + 30, PK_HEART);
}

static void boss_fan(void)
{
    int n = G.bphase == 1 ? 5 : G.bphase == 2 ? 7 : 9;
    float span = G.bphase == 1 ? 1.0f : G.bphase == 2 ? 1.3f : 1.6f;
    float aim = atan2f(G.sy - (G.by + 24), G.sx - G.bx) + ((G.bm_k & 1) ? span / (n - 1) * 0.5f : 0);
    for (int i = 0; i < n; i++) {
        float a = aim + (i - (n - 1) * 0.5f) * span / (n - 1);
        float sp = 82.0f + 9.0f * G.bphase;
        fire_es(S_ORB, G.bx, G.by + 24, cosf(a) * sp, sinf(a) * sp);
    }
    G.mouth_kick = 0.4f;
    sfx("invaders_boss_spread");
}

static void boss_spit(void)
{
    int n = G.bphase == 1 ? 2 : G.bphase == 2 ? 3 : 4;
    for (int k = 0; k < n; k++)
        for (int i = 0; i < MAXM; i++)
            if (!G.m[i].alive) {
                Minion *m = &G.m[i];
                memset(m, 0, sizeof(*m));
                m->alive = true;
                m->x = G.bx;
                m->y = G.by + 26;
                float a = 3.14159f * (0.15f + 0.7f * (k + 0.5f) / n);
                m->vx = cosf(a) * 80;
                m->vy = sinf(a) * 60;
                m->hp = 2;
                m->phase = randr(0, 6.28f);
                break;
            }
    G.mouth_kick = 0.5f;
    sfx("invaders_boss_spit");
}

static void star_row(void)
{
    const int slots = 10;
    const float w = TOP_W / (float)slots;
    G.bm_gap = mg_randi(G.bm_gap - 1 < 0 ? 0 : G.bm_gap - 1, G.bm_gap + 1 > slots - 2 ? slots - 2 : G.bm_gap + 1);
    float off = (G.bm_k & 1) ? w * 0.25f : -w * 0.25f;
    for (int k = 0; k < slots; k++) {
        if (k == G.bm_gap || k == G.bm_gap + 1)
            continue;
        fire_es(S_STAR, w * (k + 0.5f) + off, G.by + 30 + randr(-6, 6), 0, 46);
    }
}

static void boss_hover(float dt, bool center)
{
    float tx = center ? 200 : 200 + sinf(G.bt * 0.5f) * 70;
    float ty = BOSS_Y + sinf(G.bt * 0.9f) * 5;
    G.bx += (tx - G.bx) * clampf(2.5f * dt, 0, 1);
    G.by += (ty - G.by) * clampf(2.5f * dt, 0, 1);
}

/* Is the sweep beam (from the cape at angle a) touching (x, y)? */
static bool sweep_hits(float a, float x, float y, float r)
{
    float ox = G.bx, oy = G.by + 28, dx = cosf(a), dy = sinf(a);
    float vx = x - ox, vy = y - oy, t = vx * dx + vy * dy;
    return t > 0 && fabsf(vx * dy - vy * dx) < r;
}

static float sweep_angle(void) { return lerpf(G.bm_a0, G.bm_a1, clampf(G.bm_t / 2.2f, 0, 1)); }

static void update_minions(float dt)
{
    for (int i = 0; i < MAXM; i++) {
        Minion *m = &G.m[i];
        if (!m->alive)
            continue;
        m->t += dt;
        m->phase += dt;
        if (m->hurt > 0)
            m->hurt -= dt;
        if (m->t > 0.5f && m->t < 4.0f) {   /* they home in on the ship for a while */
            float dx = G.sx - m->x, dy = G.sy - m->y, d = sqrtf(dx * dx + dy * dy) + 1;
            float k = clampf(1.4f * dt, 0, 1);
            m->vx += (dx / d * 72 - m->vx) * k;
            m->vy += (dy / d * 72 - m->vy) * k;
        } else if (m->t >= 4.0f) {
            m->vy = fminf(m->vy + 50 * dt, 90);
        } else {
            m->vx *= 1 - 1.5f * dt;
            m->vy *= 1 - 1.5f * dt;
        }
        m->x += (m->vx + cosf(m->phase * 4) * 18) * dt;
        m->y += m->vy * dt;
        if (m->y > TOP_H + 12 || m->x < -20 || m->x > TOP_W + 20 || m->t > 9) {
            m->alive = false;
        } else if (G.invuln <= 0 && dist2(m->x, m->y, G.sx, G.sy) < 11 * 11) {
            m->alive = false;
            burst(m->x, m->y, 6, RGBA(200, 160, 255, 255), 50);
            hit_player("minion");
        }
    }
}

static void update_boss(float dt)
{
    if (G.bhurt > 0)
        G.bhurt -= dt;
    if (G.mouth_kick > 0)
        G.mouth_kick -= dt;
    G.bt += dt;

    if (G.st == ST_BOSS_IN) {
        G.bx = 200;
        G.by = lerpf(-90, BOSS_Y, ease(G.st_t / 3.0f));
        if (G.st_t >= 3.0f) {
            G.st = ST_BOSS;
            G.st_t = 0;
            G.bt = 0;
            boss_begin(BM_IDLE);
            G.bm_t = 0.4f;
        }
        return;
    }

    if (G.bphase_t > 0) {   /* between phases: he shudders, hungrier */
        G.bphase_t -= dt;
        boss_hover(dt, true);
        G.bx += sinf(G.t * 40) * 1.2f;
        if (G.bphase_t <= 0)
            boss_begin(BM_IDLE);
        return;
    }

    G.bm_t += dt;
    float idle = G.bphase == 1 ? 1.2f : G.bphase == 2 ? 0.95f : 0.75f;
    bool tell = G.bm_stage == 0;
    if (tell && G.bmove != BM_IDLE && G.bmove != BM_DASH && G.bm_t >= TELL[G.bmove]) {
        G.bm_stage = 1;
        G.bm_t = 0;
        switch (G.bmove) {
        case BM_SPIRAL: sfx("invaders_boss_spiral"); break;
        case BM_INHALE: G.pull = true; sfx("invaders_boss_pull"); break;
        case BM_SWEEP: sfx("invaders_boss_sweep"); break;
        case BM_STARS: sfx("invaders_boss_stars"); break;
        case BM_TANTRUM: mg_sfx("invaders_boss_tantrum"); break;
        }
    }

    switch (G.bmove) {
    case BM_IDLE:
        boss_hover(dt, false);
        if (G.bm_t >= idle)
            boss_begin(boss_pick());
        break;
    case BM_FAN:
        boss_hover(dt, false);
        if (G.bm_stage == 1) {
            if (G.bm_k < 3 && G.bm_t >= G.bm_k * 0.45f) {
                boss_fan();
                G.bm_k++;
            }
            if (G.bm_t >= 1.5f)
                boss_begin(BM_IDLE);
        }
        break;
    case BM_SPIRAL: {
        boss_hover(dt, true);
        if (G.bm_stage == 1) {
            int arms = G.bphase + 1;
            float iv = G.bphase == 1 ? 0.12f : G.bphase == 2 ? 0.15f : 0.18f;
            float rate = 2.2f * G.bm_dir * (G.bphase == 3 && G.bm_t > 1.5f ? -1 : 1);
            G.bm_a += rate * dt;
            G.bm_acc += dt;
            while (G.bm_acc >= iv) {
                G.bm_acc -= iv;
                for (int k = 0; k < arms; k++) {
                    float a = G.bm_a + k * 6.2832f / arms;
                    fire_es(S_SPARK, G.bx + cosf(a) * 14, G.by + 6 + sinf(a) * 14, cosf(a) * 78, sinf(a) * 78);
                }
            }
            if (G.bm_t >= 3.0f)
                boss_begin(BM_IDLE);
        }
        break;
    }
    case BM_INHALE:
        boss_hover(dt, true);
        if (G.bm_stage == 1 && G.bm_t >= 2.6f) {
            G.pull = false;
            sfx("invaders_boss_pull_end");
            boss_begin(BM_IDLE);
        }
        break;
    case BM_SPIT:
        boss_hover(dt, false);
        if (G.bm_stage == 1) {
            if (G.bm_k == 0) {
                boss_spit();
                G.bm_k = 1;
            }
            if (G.bm_t >= 0.7f)
                boss_begin(BM_IDLE);
        }
        break;
    case BM_SWEEP:
        boss_hover(dt, true);
        if (G.bm_stage == 1) {
            if (G.invuln <= 0 && sweep_hits(sweep_angle(), G.sx, G.sy, 6 + SHIP_R))
                hit_player("sweep");
            if (G.bm_t >= 2.2f) {
                boss_begin(BM_IDLE);
                G.bm_t = -0.2f;
            }
        }
        break;
    case BM_STARS:
        boss_hover(dt, true);
        if (G.bm_stage == 1) {
            if (G.bm_k < 5 && G.bm_t >= G.bm_k * 0.75f) {
                star_row();
                G.bm_k++;
            }
            if (G.bm_t >= 3.4f) {
                boss_begin(BM_IDLE);
                G.bm_t = -1.0f;   /* let the stars fall */
            }
        }
        break;
    case BM_DASH:
        /* 0: rise out of the top, 1: the lane warning, 2: the dash, 3: back */
        if (G.bm_stage == 0) {
            G.by += (-100 - G.by) * clampf(4.0f * dt, 0, 1);
            if (G.bm_t >= 0.55f) {
                G.bm_stage = 1;
                G.bm_t = 0;
                G.bm_lane = clampf(G.sy, 112, 196);
                G.bm_dir = G.sx < 200 ? -1.0f : 1.0f;   /* come from the ship's side */
                if (mg_randf() < 0.35f)
                    G.bm_dir = -G.bm_dir;
                G.bx = G.bm_dir > 0 ? -110 : 510;
                G.by = G.bm_lane;
                sfx("invaders_boss_dash_warn");
            }
        } else if (G.bm_stage == 1) {
            if (G.bm_t >= 0.95f) {
                G.bm_stage = 2;
                G.bm_t = 0;
                sfx("invaders_boss_dash");
            }
        } else if (G.bm_stage == 2) {
            G.bx += G.bm_dir * 560 * dt;
            if (G.invuln <= 0 && fabsf(G.sx - G.bx) < 62 && fabsf(G.sy - G.by) < 44)
                hit_player("dash");
            if ((G.bm_dir > 0 && G.bx > 510) || (G.bm_dir < 0 && G.bx < -110)) {
                if (--G.bm_n > 0) {
                    G.bm_stage = 1;
                    G.bm_t = 0;
                    G.bm_lane = clampf(G.sy, 112, 196);
                    G.bm_dir = -G.bm_dir;
                    G.by = G.bm_lane;
                    sfx("invaders_boss_dash_warn");
                } else {
                    G.bm_stage = 3;
                    G.bm_t = 0;
                    G.bx = 200;
                    G.by = -100;
                }
            }
        } else {
            G.by = lerpf(-100, BOSS_Y, ease(G.bm_t / 1.0f));
            if (G.bm_t >= 1.0f)
                boss_begin(BM_IDLE);
        }
        break;
    case BM_TANTRUM:
        boss_hover(dt, true);
        G.bx += sinf(G.t * 47) * 1.6f;
        if (G.bm_stage == 1) {
            G.bm_acc += dt;
            while (G.bm_acc >= 0.16f) {
                G.bm_acc -= 0.16f;
                for (int k = 0; k < 2; k++) {
                    float a = randr(-0.3f, 3.44f), sp = randr(55, 100);
                    fire_es(S_ORB, G.bx, G.by + 20, cosf(a) * sp, sinf(a) * sp);
                }
            }
            if (G.bm_t >= G.bm_k * 1.1f) {
                G.bm_k++;
                float base = randr(0, 1);
                for (int k = 0; k < 8; k++) {
                    float a = base + k * 0.785f;
                    fire_es(S_STAR, G.bx, G.by, cosf(a) * 50, sinf(a) * 50);
                }
                G.mouth_kick = 0.4f;
                sfx("invaders_boss_spread");
            }
            if (G.bm_t >= 4.5f) {
                boss_begin(BM_IDLE);
                G.bm_t = -0.6f;
            }
        }
        break;
    }

    /* touching his face hurts (and bumps the ship away) */
    if (G.bmove != BM_DASH && G.invuln <= 0 && dist2(G.sx, G.sy, G.bx, G.by) < 40 * 40) {
        hit_player("face");
        G.sy = fminf(Y_MAX, G.by + 80);
    }

    if (G.bhp <= 0) {
        G.bhp = 0;
        G.boss_beaten = true;
        G.points += 5000 + 1000 * G.hearts;
        G.st = ST_BOSS_DOWN;
        G.st_t = 0;
        G.pull = false;
        if (G.by < 0 || G.bx < 0 || G.bx > TOP_W) {   /* defeated mid-dash */
            G.bx = clampf(G.bx, 60, 340);
            G.by = clampf(G.by, 40, 150);
        }
        clear_enemy_shots();
        for (int i = 0; i < MAXM; i++)
            G.m[i].alive = false;
        burst(G.bx, G.by, 20, MG_GOLD, 140);
        burst(G.bx, G.by, 14, MG_WHITE, 90);
        mg_sfx("invaders_boss_defeat");
    }
}

/* ---- golden light ------------------------------------------------------------ */

static void golden_light(void)
{
    G.flash = 1.2f;
    G.flash_x = G.sx;
    G.flash_y = G.sy;
    mg_sfx("invaders_golden_light");
    clear_enemy_shots();
    for (int i = 0; i < MAXM; i++)
        if (G.m[i].alive) {
            burst(G.m[i].x, G.m[i].y, 3, MG_GOLD, 50);
            G.m[i].alive = false;
        }
    if (G.st == ST_STAGE || G.st == ST_WARN) {
        for (int i = 0; i < MAXE; i++)
            if (G.e[i].alive) {
                if (G.e[i].t >= 0)
                    burst(G.e[i].x, G.e[i].y, 3, MG_GOLD, 60);
                G.e[i].alive = false;
            }
    } else if (G.st == ST_BOSS) {
        G.bhp -= BOSS_HP * 0.3f;
        G.bhurt = 0.6f;
        G.pull = false;
        burst(G.bx, G.by, 12, MG_GOLD, 120);
        boss_phase_check();
    }
}

/* ---- start / update ---------------------------------------------------------- */

static void start(u32 seed)
{
    (void)seed;
    memset(&G, 0, sizeof(G));
    G.sx = 200;
    G.sy = 200;
    G.hearts = HEARTS_START;
    G.weapon = W_LANTERN;
    G.bscale = 1;
    G.bphase = 1;
    G.vscroll = V_SCROLL;
    G.seg = -1;
    for (int i = 0; i < NEV; i++)
        G.spawned_total += EVS[i].n;
}

static bool update(const Input *in, float dt, bool cheat)
{
    G.t += dt;
    G.st_t += dt;
    G.seg_t += dt;
    if (G.flash > 0)
        G.flash -= dt;
    if (G.invuln > 0)
        G.invuln -= dt;
    if (G.wflash > 0)
        G.wflash -= dt;
    if (G.toast_t > 0)
        G.toast_t -= dt;
    if (G.hit_snd_t > 0)
        G.hit_snd_t -= dt;
    if (G.boss_snd_t > 0)
        G.boss_snd_t -= dt;
    if (G.heart_lost_t > 0) {
        G.heart_lost_t -= dt;
        if (G.heart_lost_t <= 0)
            mg_sfx("invaders_life_lost");
    }

    /* the world scrolls on; Ashveil slows the sky */
    float want = G.st >= ST_WARN ? 26.0f : V_SCROLL;
    G.vscroll += (want - G.vscroll) * clampf(0.8f * dt, 0, 1);
    G.dist += G.vscroll * dt;
    int seg = seg_at(G.dist);
    if (G.st == ST_STAGE && seg >= SEG_VOID)
        seg = SEG_LANES;
    if (seg != G.seg) {
        G.seg = seg;
        G.seg_t = 0;
        if (seg > 0 && seg < SEG_VOID)
            sfx("invaders_wave_start");
    }

    if (cheat)
        golden_light();

    if (G.st != ST_OVER && G.st != ST_BOSS_DOWN)
        update_ship(in, dt);
    else
        G.beam_on = false;
    update_beam(dt);
    update_player_shots(dt);
    update_enemies(dt);
    update_enemy_shots(dt);
    update_minions(dt);
    update_pickups(dt);
    update_particles(dt);

    switch (G.st) {
    case ST_STAGE: {
        while (G.ev < NEV && EVS[G.ev].t * TL_SCALE <= G.st_t)
            spawn_pattern(&EVS[G.ev++]);
        bool any = false;
        for (int i = 0; i < MAXE; i++)
            any |= G.e[i].alive;
        if (G.ev >= NEV && (!any || G.st_t > STAGE_END + 8)) {
            G.st = ST_WARN;
            G.st_t = 0;
            sfx("invaders_wave_clear");
            mg_sfx("invaders_boss_warning");
        }
        break;
    }
    case ST_WARN:
        if (G.st_t >= 3.5f) {
            G.st = ST_BOSS_IN;
            G.st_t = 0;
            G.reached_boss = true;
            G.bhp = BOSS_HP;
            G.bphase = 1;
            G.bx = 200;
            G.by = -90;
            mg_music("invaders_boss");
            mg_sfx("invaders_boss_roar");
        }
        break;
    case ST_BOSS_IN:
    case ST_BOSS:
        update_boss(dt);
        break;
    case ST_BOSS_DOWN:
        G.bscale = lerpf(1.0f, 0.28f, clampf(G.st_t / 2.5f, 0, 1));
        G.bx = lerpf(G.bx, 200, clampf(dt * 1.5f, 0, 1));
        G.by = lerpf(G.by, 112, clampf(dt * 1.5f, 0, 1));
        if (G.st_t > 2.6f && G.st_t - dt <= 2.6f)
            sfx("invaders_boss_sleep");
        if (G.st_t >= 5.5f) {
            G.end_t = G.t;
            return false;
        }
        break;
    case ST_OVER:
        if (G.st_t >= 2.8f) {
            G.end_t = G.t;
            return false;
        }
        break;
    }
    if (G.reached_boss)
        G.boss_dmg_frac = clampf(1.0f - G.bhp / BOSS_HP, 0, 1);
    return true;
}

/* ---- drawing: the world -------------------------------------------------------- */

typedef struct {
    float speed, depth, spacing, margin;
} Layer;

static const Layer LAYERS[4] = {
    {0.22f, 0.92f, 40, 40},  /* far */
    {0.5f, 0.7f, 62, 60},    /* middle */
    {1.0f, 0.48f, 96, 90},   /* near ground */
    {2.1f, -0.4f, 230, 90},  /* in front of the screen */
};

static const u32 GROUND[5][2] = {
    {RGBA(52, 70, 140, 255), RGBA(150, 122, 178, 255)},   /* clouds: dusk blue to lavender */
    {RGBA(46, 36, 84, 255), RGBA(128, 94, 98, 255)},     /* halls: violet to warm gold */
    {RGBA(20, 56, 66, 255), RGBA(34, 86, 90, 255)},       /* pools: misty teal */
    {RGBA(6, 8, 30, 255), RGBA(26, 16, 60, 255)},         /* star lanes */
    {RGBA(4, 2, 16, 255), RGBA(30, 10, 44, 255)},         /* the void */
};

static void draw_item(int eye, int seg, int l, float x, float y, u32 h)
{
    float d = LAYERS[l].depth;
    float a = hf(h, 2), b = hf(h, 3);
    u32 h2 = hsh(h, 77);
    switch (seg) {
    case SEG_CLOUDS:
        if (l == 0) {
            float r = 9 + 9 * a;
            mg_circle(eye, x, y, r, d, RGBA(205, 195, 240, 60));
            mg_circle(eye, x + r * 0.9f, y + 3, r * 0.7f, d, RGBA(205, 195, 240, 60));
            mg_circle(eye, x - r * 0.8f, y + 2, r * 0.6f, d, RGBA(205, 195, 240, 60));
        } else if (l == 1) {
            float r = 15 + 12 * a;
            mg_circle(eye, x + 4, y + 6, r * 1.1f, d + 0.02f, RGBA(120, 100, 170, 60));
            mg_circle(eye, x, y, r, d, RGBA(236, 230, 255, 84));
            mg_circle(eye, x + r, y + 4, r * 0.75f, d, RGBA(236, 230, 255, 84));
            mg_circle(eye, x - r, y + 3, r * 0.7f, d, RGBA(236, 230, 255, 84));
        } else if (l == 2) {
            float r = 24 + 16 * a;
            mg_circle(eye, x + 6, y + 10, r * 1.2f, d + 0.03f, RGBA(110, 90, 160, 70));
            mg_circle(eye, x, y, r, d, RGBA(250, 245, 255, 112));
            mg_circle(eye, x + r * 1.0f, y + 6, r * 0.8f, d, RGBA(250, 245, 255, 112));
            mg_circle(eye, x - r * 0.95f, y + 5, r * 0.75f, d, RGBA(250, 245, 255, 112));
            mg_circle(eye, x - r * 0.2f, y - r * 0.4f, r * 0.6f, d - 0.01f, RGBA(255, 255, 255, 120));
        } else if (b > 0.35f) {
            float r = 50 + 30 * a;
            mg_circle(eye, x, y, r, d, RGBA(255, 255, 255, 26));
            mg_circle(eye, x + r * 0.7f, y + 10, r * 0.7f, d, RGBA(255, 255, 255, 22));
        }
        break;
    case SEG_HALLS:
        if (l == 0) {   /* a distant spire */
            float r = 5 + 5 * a;
            mg_line(eye, x, y, x, y + 26 + 20 * b, 2, d + 0.02f, RGBA(220, 190, 150, 80));
            mg_circle(eye, x, y, r, d, RGBA(230, 200, 140, 130));
            mg_circle(eye, x, y, r * 0.5f, d, RGBA(255, 240, 200, 170));
        } else if (l == 1) {   /* a floating marble platform */
            float w = 56 + 50 * a, hgt = 20 + 14 * b;
            mg_rect(eye, x - w / 2 + 6, y + 8, w, hgt, d + 0.06f, RGBA(40, 26, 70, 80));
            mg_rect(eye, x - w / 2, y, w, hgt, d, RGBA(222, 214, 236, 150));
            mg_rect(eye, x - w / 2, y, w, 4, d - 0.005f, RGBA(255, 255, 255, 150));
            mg_rect(eye, x - w / 2, y + hgt - 2, w, 2, d - 0.005f, RGBA(240, 200, 110, 230));
            mg_circle(eye, x - w / 2 + 7, y + hgt / 2, 4.5f, d - 0.03f, RGBA(255, 250, 240, 200));
            mg_circle(eye, x + w / 2 - 7, y + hgt / 2, 4.5f, d - 0.03f, RGBA(255, 250, 240, 200));
        } else if (l == 2) {   /* a bridge of light between pillars */
            float w = 150 + 80 * a;
            mg_rect(eye, x - w / 2 + 8, y + 10, w, 12, d + 0.07f, RGBA(40, 26, 70, 70));
            mg_rect(eye, x - w / 2, y, w, 12, d, RGBA(236, 228, 248, 150));
            mg_rect(eye, x - w / 2, y, w, 2, d - 0.005f, RGBA(255, 214, 120, 240));
            mg_rect(eye, x - w / 2, y + 10, w, 2, d - 0.005f, RGBA(255, 214, 120, 240));
            for (int k = 0; k < 3; k++)
                mg_circle(eye, x + (k - 1) * w * 0.42f, y + 6, 8, d - 0.04f, RGBA(255, 246, 225, 190));
        } else {
            mg_circle(eye, x, y, 2 + 2 * a, d, RGBA(255, 220, 140, 120));
            mg_circle(eye, x + 30 * b - 15, y + 40, 1.5f + a, d, RGBA(255, 230, 160, 100));
        }
        break;
    case SEG_POOLS:
        if (l == 0) {
            float r = 12 + 12 * a;
            mg_circle(eye, x, y, r, d, RGBA(40, 110, 120, 110));
            mg_circle(eye, x, y, r * 0.75f, d, RGBA(6, 26, 40, 190));
        } else if (l == 1) {
            float r = 18 + 12 * a;
            mg_circle(eye, x, y, r + 3, d, RGBA(90, 230, 230, 110));
            mg_circle(eye, x, y, r, d, RGBA(6, 24, 40, 240));
            mg_circle(eye, x - r * 0.3f, y - r * 0.35f, r * 0.3f, d - 0.005f, RGBA(160, 255, 250, 60));
            float lx = x + (b - 0.5f) * r, ly = y + (hf(h2, 0) - 0.5f) * r;
            mg_circle(eye, lx, ly, 5, d - 0.06f, RGBA(255, 190, 100, 90));
            mg_circle(eye, lx, ly, 2, d - 0.06f, RGBA(255, 232, 170, 255));
        } else if (l == 2) {
            float r = 30 + 16 * a, ox = (b - 0.5f) * 40;
            mg_circle(eye, x, y, r + 4, d, RGBA(110, 240, 230, 120));
            mg_circle(eye, x + ox + r * 0.6f, y + 14, r * 0.7f + 4, d, RGBA(110, 240, 230, 120));
            mg_circle(eye, x, y, r, d, RGBA(6, 24, 40, 245));
            mg_circle(eye, x + ox + r * 0.6f, y + 14, r * 0.7f, d, RGBA(6, 24, 40, 245));
            mg_circle(eye, x - r * 0.4f, y - r * 0.3f, r * 0.25f, d - 0.005f, RGBA(170, 255, 250, 50));
            float lx = x + (hf(h2, 1) - 0.5f) * r, ly = y + (hf(h2, 2) - 0.5f) * r * 0.6f;
            mg_circle(eye, lx, ly, 7, d - 0.1f, RGBA(255, 190, 100, 90));
            mg_circle(eye, lx, ly, 2.6f, d - 0.1f, RGBA(255, 236, 180, 255));
        } else {
            float r = 46 + 30 * a;
            mg_circle(eye, x, y, r, d, RGBA(120, 230, 220, 20));
        }
        break;
    case SEG_LANES:
        if (l == 0) {   /* a distant planet */
            static const u32 PL[4] = {RGBA(150, 110, 220, 150), RGBA(90, 160, 220, 150), RGBA(220, 130, 150, 140),
                                      RGBA(230, 190, 120, 140)};
            float r = 6 + 14 * a * a;
            u32 c = PL[h2 % 4];
            mg_circle(eye, x, y, r, d, c);
            mg_circle(eye, x - r * 0.3f, y - r * 0.3f, r * 0.6f, d, rgba_alpha(MG_WHITE, 0.25f));
        } else if (l == 1) {   /* a lane of light */
            float len = 90 + 80 * a;
            mg_line(eye, x, y - len / 2, x, y + len / 2, 3, d, RGBA(140, 170, 255, 50));
            mg_line(eye, x, y - len / 2, x, y + len / 2, 1, d - 0.01f, RGBA(220, 230, 255, 110));
            mg_rect(eye, x - 1.5f, y - len * 0.2f, 3, 3, d - 0.02f, RGBA(255, 255, 255, 230));
        } else if (l == 2) {
            float len = 30 + 40 * a;
            mg_line(eye, x, y, x, y + len, 1.5f, d, RGBA(200, 220, 255, 120));
            mg_line(eye, x + 40 * b - 20, y + 30, x + 40 * b - 20, y + 30 + len * 0.7f, 1.2f, d,
                    RGBA(200, 220, 255, 90));
        } else {
            mg_line(eye, x, y, x, y + 70 + 40 * a, 2, d, RGBA(255, 255, 255, 46));
        }
        break;
    default:   /* the void around Ashveil */
        if (l == 0) {
            static const u32 NEB[3] = {RGBA(120, 60, 170, 28), RGBA(40, 120, 160, 24), RGBA(170, 70, 120, 22)};
            float r = 40 + 30 * a;
            mg_circle(eye, x, y, r, d, NEB[h2 % 3]);
        } else if (l == 1) {
            mg_rect(eye, x, y, 2, 2, d, RGBA(230, 230, 255, 200));
            mg_rect(eye, x + 30 * b, y + 20, 1, 1, d, RGBA(230, 230, 255, 160));
        } else if (l == 2) {
            mg_line(eye, x, y, x, y + 24, 1, d, RGBA(200, 200, 255, 50));
        }
        break;
    }
}

static void draw_layer(int eye, int l)
{
    const Layer *L = &LAYERS[l];
    float w = G.dist * L->speed;
    int i0 = (int)floorf((w - TOP_H - L->margin) / L->spacing), i1 = (int)floorf((w + L->margin) / L->spacing);
    for (int i = i0; i <= i1; i++) {
        u32 h = hsh((u32)i, (u32)l);
        float y = w - i * L->spacing + (hf(h, 1) - 0.5f) * L->spacing * 0.5f;
        float x = 10 + hf(h, 0) * 380;
        int seg = seg_at((i * L->spacing + 120) / L->speed);
        if (G.st == ST_STAGE && seg == SEG_VOID)
            seg = SEG_LANES;
        draw_item(eye, seg, l, x, y, h);
    }
}

static void draw_background(int eye)
{
    /* the ground colours cross-fade between areas */
    float f = G.dist / (SEG_LEN * V_SCROLL);
    int s0 = (int)f;
    float k = clampf((f - s0 - 0.94f) / 0.12f, 0, 1);
    if (f - s0 < 0.06f && s0 > 0) {
        s0--;
        k = clampf((f - s0 - 0.94f) / 0.12f, 0, 1);
    }
    int s1 = s0 + 1;
    if (s0 > SEG_VOID)
        s0 = SEG_VOID;
    if (s1 > SEG_VOID)
        s1 = SEG_VOID;
    if (G.st == ST_STAGE && s1 == SEG_VOID)
        s1 = SEG_LANES;
    mg_sky(eye, mixc(GROUND[s0][0], GROUND[s1][0], k), mixc(GROUND[s0][1], GROUND[s1][1], k));

    /* far stars, faint where the sky is bright */
    static const float SA[5] = {0.2f, 0.3f, 0.55f, 1.0f, 1.0f};
    float sa = lerpf(SA[s0], SA[s1], k);
    for (int i = 0; i < 26; i++) {
        float x = (float)((i * 73 + 17) % TOP_W);
        float y = fmodf((float)((i * 131 + 29) % TOP_H) + G.dist * 0.1f, (float)TOP_H);
        float tw = 0.6f + 0.4f * sinf(G.t * 1.7f + i);
        mg_rect(eye, x, y, 1 + (i % 2), 1 + (i % 2), 1.0f, rgba_alpha(RGBA(230, 230, 255, 220), tw * sa));
    }
    for (int l = 0; l < 3; l++)
        draw_layer(eye, l);
}

/* ---- drawing: the actors -------------------------------------------------------- */

static void draw_ship(int eye)
{
    if (G.st == ST_OVER)
        return;
    if (G.invuln > 0 && fmodf(G.invuln, 0.2f) < 0.08f)
        return;
    float x = G.sx, y = G.sy, d = depth_at(y);
    float fl = 0.85f + 0.15f * sinf(G.t * 23.0f);
    u32 wc = WCOL[G.weapon];
    mg_circle(eye, x, y, 14 + (G.wflash > 0 ? 6 * G.wflash : 0), d + 0.02f, rgba_alpha(wc, 0.16f + 0.3f * fmaxf(0, G.wflash)));
    mg_tri(eye, x - 4, y - 1, x - 14, y + 8, x - 4, y + 6, d, RGBA(220, 160, 70, 255));
    mg_tri(eye, x + 4, y - 1, x + 14, y + 8, x + 4, y + 6, d, RGBA(220, 160, 70, 255));
    mg_tri(eye, x - 3, y + 6, x + 3, y + 6, x, y + 10 + 5 * fl, d, RGBA(255, 150, 60, 200));
    mg_rect(eye, x - 5.5f, y - 7, 11, 14, d, RGBA(190, 130, 50, 255));
    mg_rect(eye, x - 3.5f, y - 5, 7, 10, d - 0.01f, rgba_alpha(mixc(RGBA(255, 238, 180, 255), wc, 0.4f), fl));
    mg_tri(eye, x - 6.5f, y - 7, x + 6.5f, y - 7, x, y - 13, d, RGBA(160, 100, 40, 255));
    mg_circle(eye, x, y, 2.4f, d - 0.02f, MG_WHITE);   /* the core is the hitbox */
}

static void draw_spirit(int eye, float x, float y, float d, float s, float ph, int tint, bool hurt)
{
    static const u32 COL[3] = {RGBA(120, 230, 255, 255), RGBA(190, 160, 255, 255), RGBA(255, 240, 160, 255)};
    u32 c = hurt ? RGBA(255, 255, 255, 255) : COL[tint % 3];
    float blink = 0.55f + 0.45f * sinf(G.t * 4.0f + ph);
    if (fmodf(G.t + ph, 3.1f) < 0.12f)
        blink = 0.2f;
    mg_circle(eye, x, y, 12 * s, d + 0.01f, rgba_alpha(c, 0.22f * blink + 0.05f));
    mg_circle(eye, x, y, 7.5f * s, d, rgba_alpha(c, 0.55f + 0.45f * blink));
    mg_circle(eye, x, y - 0.5f * s, 4.8f * s, d - 0.005f, rgba_alpha(MG_WHITE, 0.5f + 0.4f * blink));
    u32 ink = RGBA(30, 40, 70, 255);
    mg_circle(eye, x - 2.3f * s, y - 1.2f * s, 1.1f * s, d - 0.01f, ink);
    mg_circle(eye, x + 2.3f * s, y - 1.2f * s, 1.1f * s, d - 0.01f, ink);
    mg_circle(eye, x, y + 2.0f * s, 1.0f * s, d - 0.01f, ink);
}

static void draw_angel(int eye, const Enemy *e, float d, float s)
{
    float x = e->x, y = e->y;
    if (e->kind == K_TURRET)
        s *= 1.35f;
    if (e->kind == K_RAMMER && e->stage == 1)
        x += sinf(G.t * 60) * 1.5f;   /* trembling before the charge */
    float flap = sinf(G.t * (e->kind == K_RAMMER && e->stage == 2 ? 14.0f : 6.0f) + e->phase) * 3.0f * s;
    bool diving = (e->mv == MV_DIVE && e->stage >= 1) || (e->kind == K_RAMMER && e->stage >= 1);
    u32 wing = e->hurt > 0 ? RGBA(255, 190, 170, 255) : e->kind == K_RAMMER ? RGBA(255, 222, 205, 255) : RGBA(244, 244, 255, 255);
    u32 wing2 = e->kind == K_RAMMER ? RGBA(235, 180, 170, 255) : RGBA(214, 218, 240, 255);
    u32 gold = RGBA(255, 205, 90, 255);
    if (diving)
        mg_circle(eye, x, y, 16 * s, d + 0.01f,
                  e->kind == K_RAMMER ? RGBA(255, 120, 90, 70 + (int)(40 * sinf(G.t * 20))) : RGBA(255, 210, 110, 50));
    if (e->kind == K_TURRET)
        mg_circle(eye, x, y - 12.5f * s, (e->stage ? 11 : 8) * s, d + 0.005f,
                  e->stage ? RGBA(255, 230, 140, 120) : RGBA(255, 220, 120, 40));
    for (int side = -1; side <= 1; side += 2) {
        float tipx = x + side * 17 * s, tipy = y - 9 * s - flap;
        mg_tri(eye, x + side * 2 * s, y - 3 * s, tipx, tipy, x + side * 13 * s, y + 4 * s, d + 0.005f, wing);
        mg_tri(eye, x + side * 2 * s, y, x + side * 13 * s, y + 4 * s, x + side * 8 * s, y + 9 * s, d + 0.005f, wing2);
        mg_line(eye, x + side * 2 * s, y - 3 * s, tipx, tipy, 1.2f, d, gold);
    }
    mg_tri(eye, x, y - 5 * s, x - 5 * s, y + 11 * s, x + 5 * s, y + 11 * s, d, e->hurt > 0 ? MG_WHITE : RGBA(250, 250, 255, 255));
    mg_line(eye, x - 5 * s, y + 10.5f * s, x + 5 * s, y + 10.5f * s, 1.4f, d - 0.005f, gold);
    mg_circle(eye, x, y - 6 * s, 3.4f * s, d - 0.005f, RGBA(255, 232, 200, 255));
    /* halo: a flat golden ring floating above the head */
    float hy = y - 12.5f * s, hw = (e->kind == K_CAPTAIN || e->kind == K_TURRET ? 6.5f : 5.0f) * s, hh = 1.8f * s;
    u32 halo = e->kind == K_TURRET && e->stage ? MG_WHITE : e->kind == K_CAPTAIN ? RGBA(255, 225, 120, 255) : gold;
    if (e->kind == K_TURRET && e->hp < EHP[K_TURRET] * 0.4f)
        halo = rgba_alpha(halo, 0.45f + 0.3f * sinf(G.t * 12));   /* cracked */
    mg_line(eye, x - hw, hy, x, hy - hh, 1.3f, d - 0.01f, halo);
    mg_line(eye, x, hy - hh, x + hw, hy, 1.3f, d - 0.01f, halo);
    mg_line(eye, x - hw, hy, x, hy + hh, 1.3f, d - 0.01f, halo);
    mg_line(eye, x, hy + hh, x + hw, hy, 1.3f, d - 0.01f, halo);
    if (e->kind == K_CAPTAIN || e->kind == K_TURRET)
        mg_rect(eye, x - 1.5f * s, y - 1 * s, 3 * s, 7 * s, d - 0.006f, gold);
}

static void draw_enemies(int eye)
{
    for (int i = 0; i < MAXE; i++) {
        const Enemy *e = &G.e[i];
        if (!e_visible(e) || e->y < -30 || e->y > TOP_H + 30)
            continue;
        float d = depth_at(e->y), s = depth_scale(d);
        if (e->kind == K_SPIRIT)
            draw_spirit(eye, e->x, e->y, d, s, e->phase, e->mv == MV_SWEEP ? 0 : e->mv == MV_DRIFT ? 1 : 2, e->hurt > 0);
        else
            draw_angel(eye, e, d, s);
        /* a rammer's aim line during its tell */
        if (e->kind == K_RAMMER && e->stage == 1) {
            float a = 0.25f + 0.25f * sinf(G.t * 25);
            mg_line(eye, e->x, e->y, e->x + e->mvx * 120, e->y + e->mvy * 120, 1.2f, d, RGBA(255, 120, 90, (int)(255 * a)));
        }
    }
}

static void draw_player_shots(int eye)
{
    for (int i = 0; i < MAXPS; i++) {
        const PShot *p = &G.ps[i];
        if (!p->alive)
            continue;
        float d = depth_at(p->y), s = depth_scale(d);
        if (p->kind == PS_BOLT) {
            u32 c = G.weapon == W_RAPID ? RGBA(255, 190, 110, 255) : RGBA(255, 250, 220, 255);
            mg_circle(eye, p->x, p->y + 3, 4.0f * s, d + 0.01f, RGBA(255, 230, 150, 60));
            mg_line(eye, p->x, p->y, p->x - p->vx * 0.02f, p->y + 8 * s, 2.4f * s, d, c);
        } else if (p->kind == PS_PELLET) {
            mg_circle(eye, p->x, p->y, 4.2f * s, d + 0.01f, RGBA(120, 255, 170, 70));
            mg_circle(eye, p->x, p->y, 2.2f * s, d, RGBA(220, 255, 230, 255));
        } else {
            mg_circle(eye, p->x - p->vx * 0.02f, p->y - p->vy * 0.02f, 3.2f * s, d + 0.01f, RGBA(255, 140, 220, 90));
            mg_circle(eye, p->x, p->y, 2.2f * s, d, RGBA(255, 220, 245, 255));
        }
    }
    if (G.beam_on) {   /* the piercing beam, in four slices so it reaches into the screen */
        float w = beam_w(), y0 = G.sy - 12;
        float fl = 0.8f + 0.2f * sinf(G.t * 40);
        for (int k = 0; k < 4; k++) {
            float ya = y0 * (1 - k / 4.0f), yb = y0 * (1 - (k + 1) / 4.0f);
            float d = depth_at((ya + yb) * 0.5f);
            mg_rect(eye, G.sx - w / 2 - 3, yb, w + 6, ya - yb, d + 0.01f, RGBA(255, 230, 160, (int)(70 * fl)));
            mg_rect(eye, G.sx - w / 2, yb, w, ya - yb, d, RGBA(255, 252, 235, (int)(230 * fl)));
        }
        mg_circle(eye, G.sx, y0, w * 0.8f + 2, depth_at(y0) - 0.01f, RGBA(255, 255, 240, 200));
    }
}

static void draw_enemy_shots(int eye)
{
    for (int i = 0; i < MAXES; i++) {
        const EShot *p = &G.es[i];
        if (!p->alive)
            continue;
        float d = depth_at(p->y), s = depth_scale(d);
        switch (p->kind) {
        case S_WISP:
            mg_circle(eye, p->x, p->y, 5 * s, d + 0.01f, RGBA(140, 230, 255, 70));
            mg_circle(eye, p->x, p->y, 2.6f * s, d, RGBA(210, 250, 255, 240));
            break;
        case S_BOLT:
            mg_circle(eye, p->x, p->y, 5.5f * s, d + 0.01f, RGBA(255, 200, 80, 70));
            mg_tri(eye, p->x, p->y - 5 * s, p->x - 3.2f * s, p->y, p->x + 3.2f * s, p->y, d, RGBA(255, 215, 100, 255));
            mg_tri(eye, p->x - 3.2f * s, p->y, p->x + 3.2f * s, p->y, p->x, p->y + 5 * s, d, RGBA(255, 240, 180, 255));
            break;
        case S_ORB: {
            float pulse = 0.8f + 0.2f * sinf(p->phase * 10);
            mg_circle(eye, p->x, p->y, 7 * s * pulse, d + 0.01f, RGBA(200, 150, 255, 80));
            mg_circle(eye, p->x, p->y, 3.6f * s, d, RGBA(245, 230, 255, 255));
            break;
        }
        case S_STAR: {
            float tw = 0.7f + 0.3f * sinf(p->phase * 6 + i);
            mg_circle(eye, p->x, p->y, 5.5f * s, d + 0.01f, RGBA(180, 190, 255, (int)(80 * tw)));
            mg_rect(eye, p->x - 2.2f * s, p->y - 2.2f * s, 4.4f * s, 4.4f * s, d, rgba_alpha(RGBA(240, 240, 255, 255), tw));
            break;
        }
        default:
            mg_circle(eye, p->x, p->y, 4.5f * s, d + 0.01f, RGBA(255, 240, 170, 80));
            mg_circle(eye, p->x, p->y, 2.4f * s, d, RGBA(255, 255, 230, 255));
            break;
        }
    }
    for (int i = 0; i < MAXM; i++) {
        const Minion *m = &G.m[i];
        if (!m->alive)
            continue;
        float d = depth_at(m->y), s = depth_scale(d) * 0.85f;
        draw_spirit(eye, m->x, m->y, d, s, m->phase, 1, m->hurt > 0);
    }
}

static void draw_heart(int eye, float x, float y, float r, float d, u32 c)
{
    mg_circle(eye, x - r * 0.5f, y - r * 0.2f, r * 0.58f, d, c);
    mg_circle(eye, x + r * 0.5f, y - r * 0.2f, r * 0.58f, d, c);
    mg_tri(eye, x - r * 1.05f, y + r * 0.05f, x + r * 1.05f, y + r * 0.05f, x, y + r * 1.1f, d, c);
}

static void draw_pickups(int eye)
{
    for (int i = 0; i < MAXI; i++) {
        const Pickup *p = &G.pk[i];
        if (!p->alive)
            continue;
        float d = depth_at(p->y) - 0.03f, pulse = 0.85f + 0.15f * sinf(p->t * 7);
        if (p->kind == PK_HEART) {
            mg_circle(eye, p->x, p->y, 12 * pulse, d + 0.01f, RGBA(255, 120, 150, 70));
            draw_heart(eye, p->x, p->y - 1, 7, d, RGBA(255, 90, 120, 255));
        } else {
            u32 c = WCOL[p->kind];
            mg_circle(eye, p->x, p->y, 12 * pulse, d + 0.01f, rgba_alpha(c, 0.3f));
            mg_circle(eye, p->x, p->y, 8.5f, d, c);
            mg_circle(eye, p->x - 2.5f, p->y - 3, 3, d - 0.005f, RGBA(255, 255, 255, 150));
            mg_text_centered(eye, WLETTER[p->kind], p->x, p->y - 7, 0.42f, d - 0.01f, RGBA(40, 30, 50, 255));
        }
    }
}

static void draw_particles(int eye)
{
    for (int i = 0; i < MAXP; i++) {
        const Particle *p = &G.p[i];
        if (p->life <= 0)
            continue;
        float f = p->life / p->max;
        mg_circle(eye, p->x, p->y, p->size * (0.4f + 0.6f * f), p->depth, rgba_alpha(p->color, f));
    }
}

/* Lord Ashveil: a pale round childlike face, big curious eyes, a cape that
 * is a starfield and a mouth that pulls light in. */
static void draw_boss(int eye)
{
    if (G.by < -95 || G.bx < -200 || G.bx > TOP_W + 200)
        return;
    float x = G.bx, y = G.by, s = G.bscale, d = clampf(depth_at(y), -0.1f, 0.3f);
    bool down = G.st == ST_BOSS_DOWN;
    bool acting = G.st == ST_BOSS && G.bphase_t <= 0;
    int mv = acting ? G.bmove : BM_IDLE;
    bool tell = acting && G.bm_stage == 0 && mv != BM_IDLE;
    bool tantrum = mv == BM_TANTRUM;
    bool inhale = mv == BM_INHALE;
    float sleep = down ? clampf((G.st_t - 1.5f) / 1.0f, 0, 1) : 0;
    if (tantrum || G.bphase_t > 0)
        x += sinf(G.t * 53) * 1.5f;

    /* the cape is a starfield: a hood behind the head and a cloak whose
     * scalloped hem drapes down to both sides */
    u32 rim = RGBA(110, 80, 190, 235), cape = RGBA(14, 10, 46, 250);
    if (mv == BM_SWEEP)
        rim = mixc(rim, RGBA(255, 220, 140, 255), tell ? 0.5f + 0.5f * sinf(G.t * 20) : 1.0f);
    float cw = (down ? lerpf(1.0f, 0.55f, sleep) : mv == BM_STARS ? 1.15f : 1.0f) * s;
    float lift = mv == BM_SWEEP ? -18 * s : 0;   /* the cape lifts to sweep */
    float ax = x, ay = y + 4 * s;
    float hx[8], hy[8];
    for (int i = 0; i < 8; i++) {
        float u = i / 7.0f * 2 - 1;
        hx[i] = x + u * 138 * cw;
        hy[i] = y + (34 + 52 * (1 - u * u)) * s + sinf(G.t * 1.4f + i * 1.1f) * 4 * s + (i & 1) * 7 * s + lift * u * u;
    }
    mg_circle(eye, x, y - 3 * s, 61 * s, d + 0.1f, rim);
    for (int i = 0; i < 7; i++)
        mg_tri(eye, ax, ay - 10 * s, hx[i] + (i == 0 ? -5 * s : 0), hy[i] + 4 * s, hx[i + 1] + (i == 6 ? 5 * s : 0),
               hy[i + 1] + 4 * s, d + 0.1f, rim);
    mg_circle(eye, x, y - 3 * s, 57 * s, d + 0.09f, cape);
    for (int i = 0; i < 7; i++)
        mg_tri(eye, ax, ay, hx[i], hy[i], hx[i + 1], hy[i + 1], d + 0.09f, cape);
    float starb = mv == BM_STARS ? (tell ? 1.6f + 0.6f * sinf(G.t * 18) : 1.4f) : 1.0f;
    for (int i = 0; i < 18; i++) {   /* stars inside the cape */
        float u = (float)((i * 37 + 11) % 100) / 100.0f * 1.7f - 0.85f;
        float v = 0.3f + (float)((i * 61 + 7) % 100) / 100.0f * 0.6f;
        float sx = ax + u * 138 * cw * v, sy = ay + v * (34 + 52 * (1 - u * u)) * s;
        float tw = 0.5f + 0.5f * sinf(G.t * 2.0f + i * 1.3f);
        float sz = (i % 4 == 0 ? 2.2f : 1.3f) * (s < 0.5f ? 0.7f : 1.0f) * starb;
        mg_rect(eye, sx, sy, sz, sz, d + 0.08f, rgba_alpha(RGBA(230, 230, 255, 255), 0.4f + 0.6f * tw));
    }
    float gx = x + 78 * cw, gy = y + 48 * s;   /* a little galaxy on the hem */
    mg_circle(eye, gx, gy, 6 * s, d + 0.08f, RGBA(170, 140, 255, 80));
    mg_circle(eye, gx, gy, 2.2f * s, d + 0.08f, RGBA(255, 240, 255, 210));

    /* face: pale, round, childlike (flushed in a tantrum) */
    u32 face = G.bhurt > 0 ? RGBA(255, 232, 238, 255) : RGBA(240, 236, 247, 255);
    if (tantrum)
        face = RGBA(255, 214, 226, 255);
    mg_circle(eye, x, y, 46 * s, d, face);
    mg_circle(eye, x - 9 * s, y - 10 * s, 30 * s, d - 0.005f, RGBA(255, 255, 255, 50));
    float puff = mv == BM_SPIT && tell ? 1.6f : 1.0f;   /* cheeks puff before he spits */
    u32 blush = tantrum || puff > 1 ? RGBA(255, 140, 170, 150) : RGBA(255, 160, 185, 80);
    mg_circle(eye, x - 28 * s, y + 12 * s, 7 * s * puff, d - 0.01f, blush);
    mg_circle(eye, x + 28 * s, y + 12 * s, 7 * s * puff, d - 0.01f, blush);
    mg_line(eye, x - 2 * s, y - 44 * s, x + 3 * s, y - 53 * s, 2.2f * s + 0.4f, d - 0.01f, face);
    mg_line(eye, x + 3 * s, y - 53 * s, x + 10 * s, y - 51 * s, 2.2f * s + 0.4f, d - 0.01f, face);
    mg_circle(eye, x - 22 * s, y + 43 * s, 5.5f * s, d - 0.02f, RGBA(226, 220, 240, 255));
    mg_circle(eye, x + 22 * s, y + 43 * s, 5.5f * s, d - 0.02f, RGBA(226, 220, 240, 255));

    /* eyes: big, glossy and curious, following the ship */
    u32 ink = RGBA(30, 20, 52, 255);
    float lookx = clampf((G.sx - x) / 120.0f, -1, 1) * 3 * s, looky = clampf((G.sy - y) / 120.0f, -1, 1) * 2.5f * s;
    if (mv == BM_SPIRAL && tell) {   /* eyes swirl as the spiral gathers */
        lookx = cosf(G.t * 14) * 3 * s;
        looky = sinf(G.t * 14) * 3 * s;
    }
    bool blink = !down && fmodf(G.t, 4.3f) < 0.13f;
    float wide = inhale ? 1.12f : 1.0f;
    bool narrow = mv == BM_DASH;
    for (int side = -1; side <= 1; side += 2) {
        float ex = x + side * 18 * s, ey = y - 5 * s;
        float bt = narrow || tantrum ? 4 * s : 0;   /* brows tilt in: determined (or sulky) */
        mg_line(eye, ex - 7 * s, ey - 16 * s - (side < 0) * 2 * s + (side > 0 ? bt : 0),
                ex + 6 * s, ey - 17 * s - (side > 0) * 2 * s + (side < 0 ? bt : 0), 1.6f * s + 0.4f, d - 0.015f,
                RGBA(170, 150, 200, 255));
        if (sleep > 0.5f || blink) {
            mg_line(eye, ex - 8 * s, ey, ex, ey + 3 * s, 2.2f * s + 0.5f, d - 0.02f, ink);
            mg_line(eye, ex, ey + 3 * s, ex + 8 * s, ey, 2.2f * s + 0.5f, d - 0.02f, ink);
        } else {
            float ew = 12 * s * wide * (narrow ? 0.85f : 1.0f);
            mg_circle(eye, ex, ey, ew, d - 0.02f, ink);
            mg_circle(eye, ex + lookx * 0.5f, ey + looky * 0.5f, ew * 0.79f, d - 0.025f,
                      mv == BM_SPIRAL && tell ? RGBA(200, 170, 255, 255) : RGBA(112, 74, 196, 255));
            mg_circle(eye, ex + lookx, ey + looky, 5.5f * s, d - 0.03f, RGBA(16, 8, 36, 255));
            mg_circle(eye, ex - 3.5f * s, ey - 4.5f * s, 3.8f * s, d - 0.035f, MG_WHITE);
            mg_circle(eye, ex + 3.5f * s, ey + 3.5f * s, 1.6f * s, d - 0.035f, RGBA(220, 220, 255, 230));
            if (tantrum)   /* hungry tears */
                mg_circle(eye, ex + side * 6 * s, ey + 12 * s + fmodf(G.t * 30, 10) * s, 2 * s, d - 0.03f,
                          RGBA(160, 220, 255, 220));
        }
    }

    /* mouth: a small "o" that opens wide and pulls light in */
    float mx = x, my = y + 24 * s;
    if (down) {
        mg_line(eye, mx - 5 * s, my - 1 * s, mx, my + 2 * s, 1.6f, d - 0.02f, ink);
        mg_line(eye, mx, my + 2 * s, mx + 5 * s, my - 1 * s, 1.6f, d - 0.02f, ink);
    } else if (mv == BM_SPIT && tell) {   /* lips pressed shut, cheeks full */
        mg_line(eye, mx - 6 * s, my, mx + 6 * s, my, 2.2f, d - 0.02f, ink);
    } else {
        float open = 4;
        if (inhale && tell)
            open = lerpf(6, 16, clampf(G.bm_t / TELL[BM_INHALE], 0, 1));
        else if (inhale)
            open = 16 + sinf(G.t * 9) * 1.5f;
        else if (tantrum)
            open = 9 + sinf(G.t * 17) * 3;
        else if (G.mouth_kick > 0)
            open = 4 + 7 * clampf(G.mouth_kick / 0.4f, 0, 1);
        else if (mv == BM_FAN && tell)
            open = 7;
        if (open > 6)
            mg_circle(eye, mx, my, (open + 2) * s, d - 0.01f, RGBA(150, 100, 200, 180));
        mg_circle(eye, mx, my, open * s, d - 0.015f, RGBA(8, 4, 20, 255));
        if (mv == BM_FAN && tell)   /* golden light gathering in his mouth */
            mg_circle(eye, mx, my, 4 * s * (0.6f + 0.4f * sinf(G.t * 25)), d - 0.02f, RGBA(255, 220, 140, 230));
        if (inhale && !tell)
            for (int i = 0; i < 3; i++) {   /* swallowed light circling inside */
                float a = G.t * 7 + i * 2.094f, r = open * 0.55f * s;
                mg_circle(eye, mx + cosf(a) * r, my + sinf(a) * r, 1.6f * s, d - 0.02f, RGBA(255, 235, 200, 220));
            }
    }

    /* tells around him */
    if (mv == BM_SPIRAL && tell) {   /* a ring of light gathers inward */
        float f = clampf(G.bm_t / TELL[BM_SPIRAL], 0, 1), r = lerpf(90, 20, f);
        for (int i = 0; i < 8; i++) {
            float a = i * 0.785f + G.t * 3;
            mg_circle(eye, x + cosf(a) * r, y + 6 + sinf(a) * r, 2.5f, d - 0.05f, RGBA(255, 245, 190, (int)(120 + 120 * f)));
        }
    }
    if (mv == BM_FAN && tell) {
        float f = clampf(G.bm_t / TELL[BM_FAN], 0, 1);
        for (int i = 0; i < 5; i++) {
            float a = 0.6f + i * 0.48f, r = lerpf(60, 6, f);
            mg_circle(eye, mx + cosf(a) * r, my + sinf(a) * r, 2, d - 0.04f, RGBA(255, 220, 140, 200));
        }
    }

    /* light pulled in: streaks flowing into the mouth */
    if (inhale && !tell && !down) {
        for (int i = 0; i < 12; i++) {
            float a = i * 0.5236f + 0.2f;
            float ph = fmodf(G.t * 1.4f + i * 0.37f, 1.0f);
            float r0 = 20 + 190 * (1 - ph), r1 = r0 + 16 + 20 * (1 - ph);
            float x0 = mx + cosf(a) * r0, y0 = my + sinf(a) * r0 * 0.75f;
            float x1 = mx + cosf(a) * r1, y1 = my + sinf(a) * r1 * 0.75f;
            mg_line(eye, x0, y0, x1, y1, 1.6f, d - 0.05f, rgba_alpha(RGBA(255, 240, 210, 255), 0.25f + 0.6f * ph));
        }
        mg_line(eye, G.sx, G.sy - 8, mx, my, 1.0f, (depth_at(G.sy) + d) * 0.5f, RGBA(255, 220, 160, 70));
    }

    /* sleepy z's */
    if (sleep > 0)
        for (int i = 0; i < 3; i++) {
            float ph = fmodf(G.t * 0.5f + i * 0.33f, 1.0f);
            mg_text(eye, "z", x + 14 + ph * 22, y - 14 - ph * 40, 0.4f + 0.25f * ph, d - 0.08f - ph * 0.1f,
                    rgba_alpha(RGBA(220, 220, 255, 255), sleep * (1 - ph)));
        }
}

/* The cape sweep beam and the dash lane: drawn over the world, under the ship. */
static void draw_boss_attacks(int eye)
{
    if (G.st != ST_BOSS || G.bphase_t > 0)
        return;
    if (G.bmove == BM_SWEEP) {
        float ox = G.bx, oy = G.by + 28;
        if (G.bm_stage == 0) {   /* ghost lines: where it starts and where it ends */
            float p = 0.4f + 0.4f * sinf(G.t * 16);
            for (int k = 0; k < 2; k++) {
                float a = k ? G.bm_a1 : G.bm_a0;
                float d = depth_at(oy + sinf(a) * 120);
                if (!k)
                    mg_line(eye, ox, oy, ox + cosf(a) * 420, oy + sinf(a) * 420, 9, d + 0.01f,
                            RGBA(255, 200, 120, (int)(60 * p)));
                mg_line(eye, ox, oy, ox + cosf(a) * 420, oy + sinf(a) * 420, k ? 1.5f : 3.0f, d,
                        RGBA(255, 226, 150, (int)(255 * p * (k ? 0.5f : 1.0f))));
            }
        } else {
            float a = sweep_angle(), c = cosf(a), sn = sinf(a);
            for (int k = 0; k < 3; k++) {   /* three slices, reaching out of the screen */
                float r0 = k * 140.0f, r1 = r0 + 140;
                float d = depth_at(oy + sn * (r0 + r1) * 0.5f);
                mg_line(eye, ox + c * r0, oy + sn * r0, ox + c * r1, oy + sn * r1, 16, d + 0.01f, RGBA(255, 200, 120, 70));
                mg_line(eye, ox + c * r0, oy + sn * r0, ox + c * r1, oy + sn * r1, 6, d, RGBA(255, 250, 225, 240));
            }
        }
    } else if (G.bmove == BM_DASH && (G.bm_stage == 1 || G.bm_stage == 2)) {
        float p = G.bm_stage == 1 ? 0.5f + 0.5f * sinf(G.t * 18) : 0.3f;
        float d = depth_at(G.bm_lane);
        mg_rect(eye, 0, G.bm_lane - 44, TOP_W, 88, d + 0.02f, RGBA(255, 120, 160, (int)(40 * p + 14)));
        mg_rect(eye, 0, G.bm_lane - 45, TOP_W, 2, d, RGBA(255, 150, 180, (int)(200 * p)));
        mg_rect(eye, 0, G.bm_lane + 43, TOP_W, 2, d, RGBA(255, 150, 180, (int)(200 * p)));
        if (G.bm_stage == 1) {   /* an arrow showing where he comes from */
            float ax = G.bm_dir > 0 ? 24 : TOP_W - 24, dir = G.bm_dir;
            mg_tri(eye, ax + dir * 14, G.bm_lane, ax - dir * 6, G.bm_lane - 12, ax - dir * 6, G.bm_lane + 12, d - 0.05f,
                   RGBA(255, 200, 220, (int)(255 * p)));
        }
    }
}

static void draw_hud(int eye)
{
    for (int i = 0; i < HEARTS_MAX; i++) {
        u32 c = i < G.hearts ? RGBA(255, 100, 130, 255) : RGBA(255, 255, 255, 40);
        if (i == G.hearts && G.heart_lost_t > 0)
            c = rgba_alpha(RGBA(255, 100, 130, 255), G.heart_lost_t / 0.35f + 0.2f);
        if (i >= HEARTS_START && i >= G.hearts && !(i == G.hearts && G.heart_lost_t > 0))
            continue;   /* the fifth heart only shows once you have it */
        draw_heart(eye, 12 + i * 15, 12, 5, -0.12f, c);
    }
    if (G.st == ST_BOSS || G.st == ST_BOSS_IN) {
        float f = G.st == ST_BOSS_IN ? clampf(G.st_t / 3.0f, 0, 1) : G.bhp / BOSS_HP;
        mg_rect(eye, 100, 6, 200, 5, -0.12f, RGBA(255, 255, 255, 40));
        mg_rect(eye, 100, 6, 200 * f, 5, -0.12f, G.bphase_t > 0 ? RGBA(255, 255, 255, 255) : RGBA(220, 150, 255, 255));
        mg_rect(eye, 100 + 200.0f / 3, 5, 1, 7, -0.13f, RGBA(255, 255, 255, 120));
        mg_rect(eye, 100 + 400.0f / 3, 5, 1, 7, -0.13f, RGBA(255, 255, 255, 120));
    }
}

/* Banner text with a soft dark shadow so it reads over bright clouds. */
static void say(int eye, const char *s, float cx, float y, float scale, float depth, u32 c)
{
    mg_text_centered(eye, s, cx + 1, y + 1, scale, depth + 0.02f, RGBA(20, 10, 40, (int)((c & 0xFF) * 0.6f)));
    mg_text_centered(eye, s, cx, y, scale, depth, c);
}

static void draw_banner(int eye)
{
    char buf[48];
    if (G.st == ST_STAGE && G.seg_t < 2.8f && G.seg >= 0 && G.seg < SEG_VOID) {
        float a = clampf(G.seg_t < 2.2f ? G.seg_t / 0.3f : (2.8f - G.seg_t) / 0.6f, 0, 1);
        say(eye, SEG_NAME[G.seg], 200, 96, 0.8f, -0.3f, rgba_alpha(MG_GOLD, a));
        if (G.seg == 0)
            say(eye, "Fly up. Hold A to fire.", 200, 126, 0.48f, -0.2f, rgba_alpha(MG_WHITE, a));
    } else if (G.st == ST_WARN) {
        say(eye, "Something hungry is coming...", 200, 100, 0.6f, -0.25f, RGBA(220, 190, 255, 255));
    } else if (G.st == ST_BOSS_IN && G.st_t < 2.6f) {
        say(eye, "Lord Ashveil", 200, 150, 0.8f, -0.3f, RGBA(230, 210, 255, 255));
        say(eye, "hungry, not evil", 200, 178, 0.45f, -0.2f, RGBA(200, 190, 230, 255));
    } else if (G.st == ST_BOSS && G.bphase_t > 0) {
        say(eye, G.bphase == 2 ? "Ashveil grows hungrier" : "Ashveil is starving!", 200, 196, 0.6f, -0.3f,
                         RGBA(255, 210, 240, 255));
    } else if (G.st == ST_BOSS) {
        const char *s = NULL;
        bool tell = G.bm_stage == 0;
        if (G.bmove == BM_INHALE)
            s = "He's inhaling - hold Down!";
        else if (G.bmove == BM_SWEEP && tell)
            s = "Cape sweep - fly up beside him!";
        else if (G.bmove == BM_DASH && G.bm_stage == 1)
            s = "Out of his lane!";
        else if (G.bmove == BM_STARS && tell)
            s = "Weave between the stars";
        else if (G.bmove == BM_TANTRUM && tell)
            s = "Hungry tantrum!";
        if (s)
            say(eye, s, 200, G.bmove == BM_SWEEP ? 196 : 204, 0.5f, -0.3f, RGBA(255, 214, 232, 255));
    } else if (G.st == ST_BOSS_DOWN && G.st_t > 2.6f) {
        say(eye, "Sated. Sleepy. Quiet.", 200, 170, 0.6f, -0.25f, MG_GOLD);
    } else if (G.st == ST_OVER) {
        say(eye, "The lantern goes out", 200, 100, 0.7f, -0.25f, RGBA(255, 200, 180, 255));
    }
    if (G.toast_t > 0) {   /* what you just picked up (or lost) */
        float a = clampf(G.toast_t / 0.4f, 0, 1), rise = (1.2f - G.toast_t) * 20;
        if (G.toast_kind == PK_HEART)
            snprintf(buf, sizeof(buf), "+1 heart");
        else if (G.toast_lv < 0)
            snprintf(buf, sizeof(buf), G.toast_lv == -1 ? "Weapon lost" : "Weapon down: Lv %d", -G.toast_lv - 1);
        else if (G.toast_lv >= WLV_MAX)
            snprintf(buf, sizeof(buf), "%s MAX", WNAME[G.toast_kind]);
        else
            snprintf(buf, sizeof(buf), "%s Lv %d", WNAME[G.toast_kind], G.toast_lv);
        u32 c = G.toast_kind == PK_HEART ? RGBA(255, 150, 170, 255) : G.toast_lv < 0 ? RGBA(255, 170, 150, 255) : WCOL[G.toast_kind];
        float ty = G.toast_y - rise;
        say(eye, buf, clampf(G.toast_x, 70, 330), ty < 20 ? 20 : ty, 0.42f, -0.3f, rgba_alpha(c, a));
    }
}

static void draw_flash(int eye)
{
    if (G.flash <= 0)
        return;
    float f = G.flash / 1.2f, r = (1 - f) * 420;
    gfx_rect(0, 0, TOP_W, TOP_H, rgba_alpha(RGBA(255, 230, 150, 255), f * f * 0.6f));
    mg_circle(eye, G.flash_x, G.flash_y, r, -0.1f, rgba_alpha(RGBA(255, 220, 120, 255), f * 0.22f));
    for (int i = 0; i < 16; i++) {
        float a = i * 0.3927f + G.flash * 0.3f, c = cosf(a), sn = sinf(a);
        mg_line(eye, G.flash_x + c * r * 0.55f, G.flash_y + sn * r * 0.55f, G.flash_x + c * r, G.flash_y + sn * r, 3,
                -0.15f, rgba_alpha(RGBA(255, 240, 190, 255), f));
    }
    if (f > 0.3f) {
        float a = (f - 0.3f) / 0.7f;
        mg_text_centered(eye, "Golden light!", 201, 151, 0.8f, -0.4f, rgba_alpha(RGBA(60, 30, 0, 255), a * 0.7f));
        mg_text_centered(eye, "Golden light!", 200, 150, 0.8f, -0.4f, rgba_alpha(MG_WHITE, a));
    }
}

static void draw_top(int eye)
{
#ifdef INV_DEBUG
    static int dc_max;
    dc = 0;
#endif
    draw_background(eye);
    if (G.reached_boss)
        draw_boss(eye);
    draw_boss_attacks(eye);
    draw_player_shots(eye);
    draw_enemies(eye);
    draw_pickups(eye);
    draw_particles(eye);
    draw_ship(eye);
    draw_enemy_shots(eye);
    draw_layer(eye, 3);   /* mist and streaks in front of everything */
    draw_hud(eye);
    draw_banner(eye);
    draw_flash(eye);
#ifdef INV_DEBUG
    if (dc > dc_max) {
        dc_max = dc;
        printf("invaders: %d draw calls (state %d move %d, t %.1f)\n", dc, G.st, G.bmove, G.t);
    }
#endif
}

/* ---- bottom screen ------------------------------------------------------- */

static void bot_heart(float x, float y, float r, u32 c)
{
    gfx_circle(x - r * 0.5f, y - r * 0.2f, r * 0.58f, c);
    gfx_circle(x + r * 0.5f, y - r * 0.2f, r * 0.58f, c);
    gfx_triangle(x - r * 1.05f, y + r * 0.05f, x + r * 1.05f, y + r * 0.05f, x, y + r * 1.1f, c);
}

static const char *const MOVE_NAME[BM_COUNT] = {"",           "Fan volleys",    "Spiral of light", "The inhale",
                                                "Spat spirits", "Cape sweep",   "Starfield cape",  "Hungry dash",
                                                "Hungry tantrum"};

static void draw_bottom(void)
{
    char buf[64];
    const u32 dim = RGBA(200, 200, 230, 255);
    gfx_text("The Hungry Sky", 14, 8, 0.55f, MG_GOLD);
    snprintf(buf, sizeof(buf), "%d", G.points);
    gfx_text(buf, 306 - gfx_text_width(buf, 0.55f), 8, 0.55f, MG_WHITE);

    /* hearts */
    for (int i = 0; i < HEARTS_MAX; i++)
        bot_heart(22 + i * 24, 42, 8, i < G.hearts ? RGBA(255, 100, 130, 255) : RGBA(255, 255, 255, 30));

    /* the weapon and its level */
    u32 wc = WCOL[G.weapon];
    ui_rrect(10, 60, 300, 58, 10, G.wflash > 0 ? mixc(RGBA(40, 36, 60, 255), wc, G.wflash * 0.35f) : RGBA(40, 36, 60, 255));
    gfx_circle(38, 89, 18, rgba_alpha(wc, 0.3f));
    gfx_circle(38, 89, 13, wc);
    gfx_circle(34, 85, 4, RGBA(255, 255, 255, 150));
    gfx_text(WLETTER[G.weapon], 38 - gfx_text_width(WLETTER[G.weapon], 0.6f) / 2, 79, 0.6f, RGBA(40, 30, 50, 255));
    gfx_text(WNAME[G.weapon], 64, 66, 0.55f, MG_WHITE);
    if (G.weapon == W_LANTERN) {
        gfx_text("Pick up S, B, H or R orbs", 64, 92, 0.42f, dim);
    } else {
        for (int i = 0; i < WLV_MAX; i++)
            gfx_rect(64 + i * 30, 94, 26, 8, i < G.wlv ? wc : RGBA(255, 255, 255, 40));
        snprintf(buf, sizeof(buf), G.wlv >= WLV_MAX ? "Lv MAX" : "Lv %d", G.wlv);
        gfx_text(buf, 190, 90, 0.45f, MG_WHITE);
    }

    /* the stage or the boss */
    if (G.reached_boss) {
        gfx_text("Lord Ashveil", 14, 128, 0.5f, RGBA(220, 200, 255, 255));
        float f = G.st == ST_BOSS_IN ? clampf(G.st_t / 3.0f, 0, 1) : G.bhp / BOSS_HP;
        gfx_rect(120, 132, 190, 10, RGBA(255, 255, 255, 40));
        gfx_rect(120, 132, 190 * f, 10, RGBA(200, 140, 255, 255));
        gfx_rect(120 + 190.0f / 3, 130, 1, 14, RGBA(255, 255, 255, 140));
        gfx_rect(120 + 380.0f / 3, 130, 1, 14, RGBA(255, 255, 255, 140));
        if (G.boss_beaten)
            snprintf(buf, sizeof(buf), "Asleep, full of light");
        else if (G.st == ST_BOSS && G.bphase_t > 0)
            snprintf(buf, sizeof(buf), "Phase %d of 3 - he grows hungrier", G.bphase);
        else if (G.st == ST_BOSS && G.bmove != BM_IDLE)
            snprintf(buf, sizeof(buf), "Phase %d of 3 - %s", G.bphase, MOVE_NAME[G.bmove]);
        else
            snprintf(buf, sizeof(buf), "Phase %d of 3", G.bphase);
        gfx_text(buf, 14, 150, 0.42f, dim);
    } else {
        int seg = G.seg < 0 ? 0 : G.seg > SEG_LANES ? SEG_LANES : G.seg;
        gfx_text(SEG_NAME[seg], 14, 128, 0.5f, RGBA(220, 220, 255, 255));
        float f = clampf(G.dist / (4 * SEG_LEN * V_SCROLL), 0, 1);
        gfx_rect(14, 150, 292, 6, RGBA(255, 255, 255, 40));
        gfx_rect(14, 150, 292 * f, 6, RGBA(255, 214, 120, 255));
        for (int i = 1; i < 4; i++)
            gfx_rect(14 + 73 * i, 148, 1, 10, RGBA(255, 255, 255, 120));
        gfx_circle(306, 153, 5, RGBA(200, 140, 255, 255));   /* Ashveil waits at the end */
    }
    snprintf(buf, sizeof(buf), "Kills %d", G.kills);
    gfx_text(buf, 14, 164, 0.42f, dim);

    gfx_rect(10, 182, 300, 1, RGBA(255, 255, 255, 40));
    gfx_text("Pad: fly    A: fire (hold)", 14, 188, 0.42f, dim);
    gfx_text("Down: resist his inhale", 14, 204, 0.42f, dim);
    gfx_text("START: pause", 14, 220, 0.42f, RGBA(160, 160, 190, 255));
}

/* ---- results ------------------------------------------------------------- */

static int score(void)
{
    int total = G.spawned_total - G.skipped;
    float kf = (float)G.kills / (float)(total > 1 ? total : 1);
    float s = 25.0f * clampf(kf / 0.85f, 0, 1) + 20.0f * fmaxf(0, 1 - G.hits_taken / 6.0f);
    if (G.boss_beaten)
        s += 35.0f + 20.0f * clampf((320.0f - G.end_t) / 120.0f, 0, 1);
    else if (G.reached_boss)
        s += 15.0f * G.boss_dmg_frac;
    int v = (int)(s + 0.5f);
#ifdef INV_DEBUG
    printf("invaders: kills %d/%d hearts %d hits taken %d t %.1f boss %d weapon %d lv %d\n", G.kills, total, G.hearts,
           G.hits_taken, G.end_t, G.boss_beaten, G.weapon, G.wlv);
#endif
    return v < 0 ? 0 : v > 100 ? 100 : v;
}

static const char *verdict(void)
{
    static char buf[96];
    if (G.boss_beaten && G.hits_taken == 0)
        return "Ashveil sleeps, full of light. Not a scratch.";
    if (G.boss_beaten && G.end_t < 200)
        return "Swift as a star lane: Ashveil naps, sated.";
    if (G.boss_beaten)
        return "Lord Ashveil curls up, sated and sleepy.";
    if (G.reached_boss)
        return "The hungry sky is still hungry.";
    int seg = G.seg < 0 ? 0 : G.seg > SEG_LANES ? SEG_LANES : G.seg;
    snprintf(buf, sizeof(buf), "The lantern went out over %s.", seg == 0 ? "the Cloud Sea"
                                                               : seg == 1 ? "Seraphiel's halls"
                                                               : seg == 2 ? "the Purgatorium"
                                                                          : "the star lanes");
    return buf;
}

/* The cheat only helps while there is something to clear or to hurt. */
static bool can_cheat(void)
{
    if (G.st == ST_STAGE || G.st == ST_WARN) {
        for (int i = 0; i < MAXE; i++)
            if (e_visible(&G.e[i]) && G.e[i].y > -10)
                return true;
        for (int i = 0; i < MAXES; i++)
            if (G.es[i].alive)
                return true;
        return false;
    }
    return G.st == ST_BOSS && G.bphase_t <= 0 && G.bhp > 0;
}

/* ---- bot ----------------------------------------------------------------- */

/* How dangerous is (px, py) at tau seconds from now? */
static float bot_danger(float px, float py, float tau)
{
    float dng = 0;
    for (int i = 0; i < MAXES; i++) {
        const EShot *s = &G.es[i];
        if (!s->alive)
            continue;
        float bx = s->x + s->vx * tau, by = s->y + s->vy * tau;
        float r = es_r(s->kind) + SHIP_R + 6;
        float dd = dist2(bx, by, px, py);
        if (dd < r * r) {
            float k = r - sqrtf(dd);
            dng += k * k;
        }
    }
    for (int i = 0; i < MAXE; i++) {
        const Enemy *e = &G.e[i];
        if (!e_visible(e))
            continue;
        float ex = e->x + e->vx * tau, ey = e->y + e->vy * tau;
        if (e->kind == K_RAMMER && e->stage == 1) {   /* about to charge along its line */
            float vx = px - e->x, vy = py - e->y, t = vx * e->mvx + vy * e->mvy;
            if (t > 0 && fabsf(vx * e->mvy - vy * e->mvx) < 24)
                dng += 150;
        }
        float r = e_r(e) + SHIP_R + 10;
        float dd = dist2(ex, ey, px, py);
        if (dd < r * r) {
            float k = r - sqrtf(dd);
            dng += k * k * 1.5f;
        }
    }
    for (int i = 0; i < MAXM; i++) {
        const Minion *m = &G.m[i];
        if (!m->alive)
            continue;
        float r = 22, dd = dist2(m->x + m->vx * tau, m->y + m->vy * tau, px, py);
        if (dd < r * r) {
            float k = r - sqrtf(dd);
            dng += k * k * 1.5f;
        }
    }
    if (G.st == ST_BOSS && G.bphase_t <= 0) {
        if (G.bmove != BM_DASH) {
            float dd = dist2(G.bx, G.by, px, py);
            if (dd < 70 * 70)
                dng += (70 - sqrtf(dd)) * 8;
        }
        if (G.bmove == BM_SWEEP) {
            float a = G.bm_stage == 0 ? -1 : lerpf(G.bm_a0, G.bm_a1, clampf((G.bm_t + tau) / 2.2f, 0, 1));
            if (a >= 0 && sweep_hits(a, px, py, 18))
                dng += 400;
            /* the whole fan below him is unsafe for a while */
            float ang = atan2f(py - (G.by + 28), px - G.bx);
            if (ang > 0.3f && ang < 2.84f)
                dng += 60;
        }
        if (G.bmove == BM_DASH && (G.bm_stage == 1 || G.bm_stage == 2) && fabsf(py - G.bm_lane) < 60)
            dng += 300;
        if (G.pull) {
            float dd = dist2(G.bx, G.by + 24, px, py);
            if (dd < 90 * 90)
                dng += (90 - sqrtf(dd)) * 4;
        }
    }
    return dng;
}

static void bot(Input *in, float t)
{
    static float last_t;
    static bool cheated;
    if (t < last_t)
        cheated = false;
    last_t = t;

    in->held |= KEY_A_;   /* keep firing */

    /* where would we like to be? */
    float gx = 200, gy = 208;
    float best = 1e9f;
    for (int i = 0; i < MAXE; i++) {
        const Enemy *e = &G.e[i];
        if (!e_visible(e) || e->y < -5 || e->y > G.sy - 20)
            continue;
        float lead = e->vx * (G.sy - e->y) / 400.0f;
        float c = fabsf(e->x + lead - G.sx) * 0.5f - e->y * 0.4f - (e->kind == K_TURRET ? 120 : 0);
        if (c < best)
            best = c, gx = e->x + lead;
    }
    for (int i = 0; i < MAXM; i++)
        if (G.m[i].alive && G.m[i].y < G.sy)
            gx = G.m[i].x;
    if (G.st == ST_BOSS || G.st == ST_BOSS_IN) {
        gx = clampf(G.bx, 60, 340);
        gy = 190;
        if (G.st == ST_BOSS && G.bphase_t <= 0) {
            if (G.bmove == BM_SWEEP) {
                gx = G.sx < 200 ? 26 : 374;
                gy = Y_MIN + 4;
            } else if (G.bmove == BM_DASH && G.bm_stage >= 1 && G.bm_stage <= 2) {
                gx = G.sx;
                gy = G.bm_lane > 150 ? G.bm_lane - 80 : G.bm_lane + 75;
            } else if (G.bmove == BM_DASH) {
                gy = 200;
            } else if (G.pull) {
                gy = Y_MAX;
            }
        }
    }
    /* pickups beat everything but real danger */
    float pbest = 1e9f;
    for (int i = 0; i < MAXI; i++) {
        const Pickup *p = &G.pk[i];
        if (!p->alive || p->y < 20)
            continue;
        float c = fabsf(p->x - G.sx) + fabsf(p->y - G.sy) * 0.5f - (p->kind == PK_HEART ? 80 : 0);
        if (c < pbest && !(G.st == ST_BOSS && (G.bmove == BM_SWEEP || G.bmove == BM_DASH || G.pull)))
            pbest = c, gx = p->x, gy = clampf(p->y + 6, 150, Y_MAX);
    }

    /* pick the safest nearby spot on the way there */
    float bx = G.sx, by = G.sy, bc = 1e12f;
    static const float TAU[8] = {0.04f, 0.09f, 0.14f, 0.2f, 0.27f, 0.35f, 0.45f, 0.6f},
                       W[8] = {1.6f, 1.6f, 1.4f, 1.2f, 1.0f, 0.8f, 0.6f, 0.4f};
    for (int ix = -4; ix <= 4; ix++)
        for (int iy = -3; iy <= 3; iy++) {
            float cx = clampf(G.sx + ix * 10.0f, X_MIN, X_MAX), cy = clampf(G.sy + iy * 10.0f, Y_MIN, Y_MAX);
            float dx = cx - G.sx, dy = cy - G.sy, dl = sqrtf(dx * dx + dy * dy);
            float dng = 0;
            for (int k = 0; k < 8; k++) {
                float f = dl > 0 ? fminf(1, SHIP_SPEED * TAU[k] / dl) : 0;
                dng += bot_danger(G.sx + dx * f, G.sy + dy * f, TAU[k]) * W[k];
            }
            float c = dng * 30 + sqrtf(dist2(cx, cy, gx, gy)) * 0.6f + dl * 0.05f;
            if (c < bc)
                bc = c, bx = cx, by = cy;
        }
    in->cx = clampf((bx - G.sx) / 6.0f, -1, 1);
    in->cy = clampf((G.sy - by) / 6.0f, -1, 1);
    if (G.pull)
        in->held |= KEY_DOWN_;

    /* spend the cheat once the boss is fighting */
    if (!cheated && G.st == ST_BOSS && G.bphase_t <= 0 && G.bhp < BOSS_HP * 0.8f) {
        in->down |= KEY_L_;
        cheated = true;
    }
}

const MiniGame MG_INVADERS = {
    .id = "invaders",
    .title = "The Hungry Sky",
    .rules = "Fly Aron's lantern-ship up through the heavens.\n"
             "Spirits and angels swoop, shoot and ram you.\n"
             "Some drop weapon orbs: Spread, Beam, Homing,\n"
             "Rapid. The same orb again powers it up; a hit\n"
             "costs a heart and a weapon level. Hearts heal.\n"
             "At the end waits Lord Ashveil, hungry, not evil:\n"
             "read his tells. When he inhales, hold Down.\n"
             "Score: kills, damage taken, time, the boss.",
    .controls = "D-pad / Circle Pad: fly anywhere\n"
                "A: fire    Hold A: auto-fire\n"
                "Down: resist Ashveil's inhale\n"
                "START: pause",
    .cheat = "Golden light clears every enemy\nand shot, or burns 30% off Ashveil",
    .music = "invaders",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .verdict = verdict,
    .can_cheat = can_cheat,
    .bot = bot,
};
