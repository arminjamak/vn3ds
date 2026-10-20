/* The Tower: tiny Aron climbs a stone tower, one segment at a time. Every
 * segment has one leaf-shaped platform with a hole in it; all leaves orbit
 * the tower together. Aron rides his leaf, walks along it to line up under
 * the next leaf's ring and jumps up through it. Rings behind the tower are
 * out of reach. Every four segments the orbit speeds up (and the music
 * changes). After the 16th leaf Aron hops into the hole at the top and pops
 * out into a scenery picked at random for the run.
 *
 * The cheat skips one whole speed tier, instantly, even mid-jump.
 *
 * Score: each jump is weighted by its tier (1..4, 39 in all), P = weighted
 * progress / 39.
 *     score = 55 P + 15 (top reached) + P (18 / (1 + falls / 4) + 12 tq)
 * where tq is 1 at 45 s or less and 0 at 150 s or more. The run ends after
 * 3 minutes with whatever was climbed. */

#include "minigame.h"

#define SEGS 16
#define SEG 56.0f           /* world height of a segment */
#define CX 200.0f           /* tower axis on screen */
#define TR 46.0f            /* tower half-width */
#define ORBIT 92.0f         /* leaf orbit radius */
#define LRX 24.0f           /* leaf half-width */
#define HOLE 13.0f          /* pass if within this of the ring's centre */
#define BASE 174.0f         /* screen y of the camera's world height */
#define ARON_H 16.0f        /* feet to head, for passing a ring */
#define JUMP_V 340.0f
#define GRAV 800.0f
#define WALK 75.0f
#define AIR 45.0f
#define UMAX 20.0f
#define TIME_CAP 180.0f
#define REACH_COS -0.3f     /* rings further behind than this are dim and unreachable */
#define Y_TOP (15 * SEG + 36)
#define NPART 80
#define NPOP 4
#define NSCENE 5
#define TOP_END 5.2f

static const float SPEED[4] = {1.0f, 1.3f, 1.65f, 2.0f};
static const char *const MUSIC[4] = {"tower_1", "tower_2", "tower_3", "tower_4"};
static const char *const SCENE_NAME[NSCENE] = {
    "A flower meadow", "The city at night", "The Purgatorium's little lights", "The seaside",
    "The angels' clouds",
};
static const char *const SCENE_FOUND[NSCENE] = {
    "a flower meadow", "a bustling city", "the Purgatorium's lights", "the seaside", "the angels' clouds",
};

enum { ST_STAND, ST_JUMP, ST_TOP, ST_TIMEUP };

typedef struct {
    float x, y, vx, vy, g, life, max, size, depth;
    u32 c;
    bool world;   /* y is world height (up) instead of screen y (down) */
} Part;

typedef struct {
    char txt[32];
    float t, max, x, y, scale, depth;
    u32 c;
} Pop;

static struct {
    int st;
    float t, end_t, anim, st_t;
    float rot;
    float phase[SEGS];
    float win[SEGS][2];       /* window angles per segment */
    int level, tier;
    float u, Y, vy, stun;
    bool missed;
    int falls;
    float progress;
    bool done, cheated_top;
    float cam;
    float fill[SEGS];
    float step_t, walk, align_cool;
    int face;
    bool aligned;
    int scene;
    float flash, warp;
    float x0, Y0;             /* start of the hop into the hole */
    Part p[NPART];
    Pop pop[NPOP];
    float cloud[10][3];       /* x, world y, size */
    float star[32][2];
    float sc[28][4];          /* scenery bits: x, y, size, extra */
} S;

static struct {
    bool cheated, missed_once;
} B;

/* ---- helpers ------------------------------------------------------------- */

static float ang(int k) { return S.phase[k] + S.rot; }
static float leaf_x(int k) { return CX + ORBIT * sinf(ang(k)); }
static float leaf_c(int k) { return cosf(ang(k)); }
static float aron_x(void) { return leaf_x(S.level) + S.u; }
static float sy(float Y) { return BASE - (Y - S.cam); }
static float eye_y(void) { return S.cam + 26; }
static int tier_of(int k) { return k / 4; }
static float pitch(int n) { return powf(2.0f, (float)n / 12.0f); }

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

static void burst(float x, float y, bool world, int n, u32 c, float speed, float depth)
{
    for (int i = 0, k = 0; i < NPART && k < n; i++) {
        Part *p = &S.p[i];
        if (p->life > 0)
            continue;
        float a = mg_randf() * 6.2832f, v = speed * (0.4f + 0.6f * mg_randf());
        p->x = x;
        p->y = y;
        p->vx = cosf(a) * v;
        p->vy = sinf(a) * v * (world ? 1 : -1) + (world ? speed * 0.5f : -speed * 0.5f);
        p->g = world ? -260 : 260;
        p->max = p->life = 0.5f + 0.6f * mg_randf();
        p->size = 1.5f + 2.0f * mg_randf();
        p->depth = depth + (mg_randf() - 0.5f) * 0.3f;
        p->c = c;
        if (c == 0) {   /* confetti */
            static const u32 CONF[5] = {RGBA(255, 120, 120, 255), RGBA(255, 220, 110, 255),
                                         RGBA(120, 220, 255, 255), RGBA(170, 255, 140, 255),
                                         RGBA(240, 150, 255, 255)};
            p->c = CONF[mg_randi(0, 4)];
            p->max = p->life = 1.4f + mg_randf();
        }
        p->world = world;
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
    p->x = x;
    p->y = y;
    p->scale = scale;
    p->c = c;
    p->depth = depth;
}

/* ---- run ----------------------------------------------------------------- */

static void start(u32 seed)
{
    (void)seed;
    memset(&S, 0, sizeof(S));
    memset(&B, 0, sizeof(B));
    S.face = 1;
    for (int k = 1; k < SEGS; k++) {
        float mag = 0.45f + 0.7f * mg_randf();
        S.phase[k] = S.phase[k - 1] + (mg_rand() & 1 ? mag : -mag);
    }
    for (int k = 0; k < SEGS; k++) {
        S.win[k][0] = -1.1f + mg_randf() * 0.9f;
        S.win[k][1] = 0.2f + mg_randf() * 0.9f;
    }
    S.fill[0] = 1;
    for (int i = 0; i < 10; i++) {
        S.cloud[i][0] = mg_randf() * 440 - 20;
        S.cloud[i][1] = -40 + i * 55 + mg_randf() * 30;
        S.cloud[i][2] = 8 + mg_randf() * 8;
    }
    for (int i = 0; i < 32; i++) {
        S.star[i][0] = mg_randf() * TOP_W;
        S.star[i][1] = mg_randf() * 900;
    }
    for (int i = 0; i < 28; i++) {
        S.sc[i][0] = mg_randf();
        S.sc[i][1] = mg_randf();
        S.sc[i][2] = mg_randf();
        S.sc[i][3] = mg_randf();
    }
    S.scene = mg_randi(0, NSCENE - 1);
}

static void set_tier(int t)
{
    if (t <= S.tier)
        return;
    S.tier = t;
    mg_music(MUSIC[t]);
    mg_sfx("tower_faster");
    popup("Faster!", CX, 64, 1.1f, RGBA(255, 190, 90, 255), -0.45f, 1.3f);
}

static void credit(int from, int to)   /* jumps landing on leaves from..to */
{
    for (int j = from; j <= to && j < SEGS; j++) {
        S.progress += (float)(tier_of(j) + 1);
        S.fill[j] = 1;
    }
}

static void start_top(void)
{
    S.st = ST_TOP;
    S.st_t = 0;
    S.done = true;
    S.end_t = S.t;
    S.x0 = aron_x();
    S.Y0 = S.Y;
    mg_sfx("tower_summit");
}

static void do_cheat(void)
{
    if (S.st != ST_STAND && S.st != ST_JUMP)
        return;
    int nt = S.tier + 1;
    burst(aron_x(), S.Y + 8, true, 18, RGBA(200, 180, 255, 255), 90, -0.1f);
    mg_sfx("tower_warp");
    S.warp = 0.6f;
    if (nt >= 4) {
        credit(S.level + 1, SEGS - 1);
        S.level = SEGS - 1;
        S.Y = S.level * SEG;
        S.u = 0;
        S.cheated_top = true;
        start_top();
        return;
    }
    int dest = nt * 4;
    credit(S.level + 1, dest);
    S.level = dest;
    S.Y = dest * SEG;
    S.vy = 0;
    S.u = 0;
    S.st = ST_STAND;
    S.stun = 0;
    S.missed = false;
    set_tier(nt);
    popup("Tier skip!", CX, 100, 0.7f, RGBA(220, 200, 255, 255), -0.3f, 1.2f);
    burst(aron_x(), S.Y + 8, true, 18, RGBA(200, 180, 255, 255), 90, -0.1f);
}

static void land(void)
{
    S.Y = S.level * SEG;
    S.vy = 0;
    S.st = ST_STAND;
    if (S.missed) {
        S.stun = 0.45f;
        S.u = clampf(S.u, -UMAX, UMAX);
        mg_sfx("tower_thud");
        return;
    }
    mg_sfx_pitch("tower_land", pitch(S.level));
    S.progress += (float)(tier_of(S.level) + 1);
    S.u = clampf(S.u, -UMAX, UMAX);
    burst(aron_x(), S.Y, true, 8, RGBA(170, 240, 150, 255), 50, -0.1f);
    if (tier_of(S.level) > S.tier)
        set_tier(tier_of(S.level));
    if (S.level == SEGS - 1)
        start_top();
}

static bool update_top(float dt)
{
    float prev = S.st_t;
    S.st_t += dt;
    S.cam += (Y_TOP - 60 - S.cam) * clampf(dt * 4, 0, 1);
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
        burst(290, 200, false, 50, 0, 170, -0.2f);
        popup("Top of the Tower!", CX, 34, 0.95f, MG_GOLD, -0.4f, 2.6f);
    }
    if (CROSS(3.3f) || CROSS(4.1f)) {
        mg_sfx("tower_cheer");
        burst(290, 190, false, 18, 0, 120, -0.2f);
    }
#undef CROSS
    return S.st_t < TOP_END;
}

static bool update(const Input *in, float dt, bool cheat)
{
    if (dt > 0.05f)
        dt = 0.05f;
    S.anim += dt;
    S.flash = S.flash > 0 ? S.flash - dt : 0;
    S.warp = S.warp > 0 ? S.warp - dt : 0;
    S.align_cool -= dt;
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
    for (int k = 0; k < SEGS; k++)
        if (k <= S.level && S.fill[k] < 1)
            S.fill[k] = clampf(S.fill[k] + dt * 5, 0, 1);

    if (S.st == ST_TOP) {
        S.rot += SPEED[S.tier] * 0.5f * dt;
        return update_top(dt);
    }
    if (S.st == ST_TIMEUP) {
        S.st_t += dt;
        return S.st_t < 2.4f;
    }

    S.t += dt;
    S.rot += SPEED[S.tier] * dt;
    S.cam += (S.level * SEG - S.cam) * clampf(dt * 6, 0, 1);
    if (cheat) {
        do_cheat();
        if (S.st == ST_TOP)
            return true;
    }
    if (S.t >= TIME_CAP) {
        S.st = ST_TIMEUP;
        S.st_t = 0;
        mg_sfx("tower_timeout");
        popup("Time's up!", CX, 80, 1.0f, RGBA(255, 150, 130, 255), -0.4f, 2.4f);
        return true;
    }

    float mv = in->cx;
    if (in->held & KEY_LEFT_)
        mv = -1;
    if (in->held & KEY_RIGHT_)
        mv = 1;
    if (fabsf(mv) < 0.25f)
        mv = 0;
    if (mv)
        S.face = mv > 0 ? 1 : -1;
    bool jump = (in->down & (KEY_A_ | KEY_B_)) != 0;
    int k = S.level + 1;

    if (S.st == ST_STAND) {
        if (S.stun > 0) {
            S.stun -= dt;
            mv = 0;
            jump = false;
        }
        float before = S.u;
        S.u = clampf(S.u + mv * WALK * dt, -UMAX, UMAX);
        if (S.u != before) {
            S.walk += dt * 14;
            S.step_t -= dt;
            if (S.step_t <= 0) {
                mg_sfx("tower_step");
                S.step_t = 0.22f;
            }
        } else {
            S.step_t = 0;
        }
        bool al = k < SEGS && leaf_c(k) > REACH_COS && fabsf(aron_x() - leaf_x(k)) < HOLE - 2;
        if (al && !S.aligned && S.align_cool <= 0) {
            mg_sfx("tower_aligned");
            S.align_cool = 0.6f;
        }
        S.aligned = al;
        if (jump && k < SEGS) {
            S.st = ST_JUMP;
            S.vy = JUMP_V;
            S.missed = false;
            S.aligned = false;
            mg_sfx("tower_jump");
        }
        return true;
    }

    /* in the air */
    S.u = clampf(S.u + mv * AIR * dt, -30, 30);
    float head0 = S.Y + ARON_H;
    S.vy -= GRAV * dt;
    S.Y += S.vy * dt;
    float ring = k * SEG;
    if (!S.missed && k < SEGS && S.vy > 0 && head0 < ring && S.Y + ARON_H >= ring) {
        float dx = aron_x() - leaf_x(k);
        bool reach = leaf_c(k) > REACH_COS;
        if (reach && fabsf(dx) < HOLE) {
            S.u = aron_x() - leaf_x(k);
            S.level = k;
            S.fill[k] = 0.01f;
            mg_sfx_pitch("tower_through_hoop", pitch(k - 1));
            burst(aron_x(), ring, true, 10, RGBA(255, 240, 170, 255), 70, -0.15f);
        } else {
            S.missed = true;
            S.falls++;
            if (reach && fabsf(dx) < LRX + 4) {
                S.vy = S.vy < -40 ? S.vy : -40;
                mg_sfx("tower_bonk");
                popup("Bonk!", aron_x(), sy(S.Y + 26), 0.55f, RGBA(255, 160, 140, 255), -0.3f, 0.8f);
            } else {
                mg_sfx("tower_miss");
                popup("Miss!", aron_x(), sy(S.Y + 30), 0.55f, RGBA(255, 160, 140, 255), -0.3f, 0.8f);
            }
        }
    }
    if (S.vy < 0 && S.Y <= S.level * SEG)
        land();
    return true;
}

/* ---- drawing: shapes ------------------------------------------------------- */

/* Half an ellipse (near half when `near`), seen from above when ns = 1. */
static void half_ellipse(int eye, float x, float y, float rx, float ry, float ns, bool near, float th,
                         float depth, u32 c)
{
    const int N = 8;
    float a0 = near ? 0 : 3.14159f;
    float px = x + rx * cosf(a0), py = y + ns * ry * sinf(a0);
    for (int i = 1; i <= N; i++) {
        float a = a0 + 3.14159f * i / N;
        float qx = x + rx * cosf(a), qy = y + ns * ry * sinf(a);
        mg_line(eye, px, py, qx, qy, th, depth, c);
        px = qx;
        py = qy;
    }
}

static void fill_ellipse(int eye, float x, float y, float rx, float ry, float depth, u32 c)
{
    const int N = 14;
    float px = x + rx, py = y;
    for (int i = 1; i <= N; i++) {
        float a = 6.2832f * i / N;
        float qx = x + rx * cosf(a), qy = y + ry * sinf(a);
        mg_tri(eye, x, y, px, py, qx, qy, depth, c);
        px = qx;
        py = qy;
    }
}

/* Tiny Aron. pose: 0 stand/walk, 1 air, 2 stunned, 3 cheer */
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

/* ---- drawing: the climb ---------------------------------------------------- */

static float leaf_depth(int k)
{
    float d = -0.22f * leaf_c(k);
    if (k > S.level)
        d += (k - S.level) * 0.16f;
    return clampf(d, -0.35f, 0.9f);
}

static float leaf_ry(float Y) { return clampf(3.5f + fabsf(Y - eye_y()) * 0.08f, 4.0f, 9.0f); }

/* Part 0: stalk and the far side; part 1: the near side of an outline. */
static void draw_leaf(int eye, int k, int part)
{
    float Y = k * SEG, y = sy(Y);
    if (y < -16 || y > TOP_H + 16)
        return;
    float a = ang(k), sn = sinf(a), c = cosf(a);
    float x = CX + ORBIT * sn, d = leaf_depth(k);
    float ns = Y < eye_y() ? 1.0f : -1.0f, ry = leaf_ry(Y);
    float fl = k <= S.level ? S.fill[k] : 0;
    bool reach = c > REACH_COS;
    float up = (float)(k - S.level);
    float fade = up > 1 ? clampf(1.25f - up * 0.2f, 0.3f, 1) : 1;
    float dim = reach ? 1.0f : 0.4f;
    float tx = x + sn * (LRX + 7), ty = y + c * ns * (ry + 3);   /* leaf tip */
    if (part == 0) {
        float s0 = x - sn * (LRX - 3);
        mg_line(eye, CX + TR * sn, y + 1, s0, y + 1, 3, d + 0.02f,
                rgba_alpha(RGBA(70, 120, 60, 255), dim * fade));
        if (fl > 0) {
            float e = fl;
            fill_ellipse(eye, x, y + 2.5f, LRX, ry, d + 0.01f, rgba_alpha(RGBA(46, 110, 60, 255), e * dim));
            mg_tri(eye, x + sn * (LRX - 4), y - ry * 0.6f, x + sn * (LRX - 4), y + ry * 0.6f, tx, ty + 2,
                   d + 0.01f, rgba_alpha(RGBA(46, 110, 60, 255), e * dim));
            fill_ellipse(eye, x, y, LRX, ry, d, rgba_alpha(RGBA(108, 196, 104, 255), e * dim));
            mg_tri(eye, x + sn * (LRX - 4), y - ry * 0.6f, x + sn * (LRX - 4), y + ry * 0.6f, tx, ty,
                   d, rgba_alpha(RGBA(108, 196, 104, 255), e * dim));
            mg_line(eye, x - sn * LRX * 0.7f, y, tx, ty, 1, d - 0.01f,
                    rgba_alpha(RGBA(176, 236, 150, 255), e * dim));
            mg_line(eye, x, y, x - 8, y - ry * 0.5f, 1, d - 0.01f, rgba_alpha(RGBA(176, 236, 150, 255), e * dim));
            mg_line(eye, x, y, x + 8, y - ry * 0.5f, 1, d - 0.01f, rgba_alpha(RGBA(176, 236, 150, 255), e * dim));
            if (fl >= 1)
                return;
        }
    }
    if (fl >= 1)
        return;
    bool next = k == S.level + 1 && S.st != ST_TOP;
    u32 col = RGBA(160, 245, 200, 255);
    if (next && reach && fabsf(aron_x() - x) < HOLE)
        col = RGBA(255, 214, 96, 255);
    else if (!reach)
        col = RGBA(120, 140, 170, 255);
    col = rgba_alpha(col, fade * (reach ? 1.0f : 0.45f));
    float th = next ? 2.4f : 1.8f;
    u32 under = rgba_alpha(RGBA(20, 30, 40, 255), fade * (reach ? 0.55f : 0.2f));
    half_ellipse(eye, x, y + 1, LRX, ry, ns, part == 1, th + 1.4f, d + 0.01f, under);
    half_ellipse(eye, x, y, LRX, ry, ns, part == 1, th, d, col);
    if (part == 1) {
        mg_line(eye, x + sn * (LRX - 2), y - ry * 0.55f, tx, ty, th, d, col);
        mg_line(eye, x + sn * (LRX - 2), y + ry * 0.55f, tx, ty, th, d, col);
    }
}

static void draw_sky(int eye)
{
    static const u32 TOPC[4] = {RGBA(96, 160, 226, 255), RGBA(104, 128, 206, 255), RGBA(60, 50, 120, 255),
                                RGBA(16, 16, 44, 255)};
    static const u32 BOTC[4] = {RGBA(200, 228, 246, 255), RGBA(250, 212, 172, 255), RGBA(236, 140, 120, 255),
                                RGBA(62, 44, 104, 255)};
    float h = clampf(S.cam / (15 * SEG), 0, 1) * 3;
    int i = (int)h;
    if (i > 2)
        i = 2;
    float f = h - i;
    mg_sky(eye, mix(TOPC[i], TOPC[i + 1], f), mix(BOTC[i], BOTC[i + 1], f));
    float night = clampf(h - 1.6f, 0, 1);
    if (night > 0)
        for (int s = 0; s < 32; s++) {
            float y = S.star[s][1] - 500 + S.cam * 0.25f;
            y = fmodf(y + 2000, 260) - 10;
            float tw = 0.6f + 0.4f * sinf(S.anim * 2 + s);
            mg_rect(eye, S.star[s][0], y, 1.5f, 1.5f, 1.0f, rgba_alpha(MG_WHITE, night * tw));
        }
    /* far hills near the ground */
    float gy = BASE + 20 + S.cam * 0.5f;
    if (gy < TOP_H + 60) {
        mg_circle(eye, 60, gy + 40, 90, 0.75f, RGBA(120, 170, 150, 255));
        mg_circle(eye, 330, gy + 50, 110, 0.75f, RGBA(110, 160, 145, 255));
    }
    u32 cc = rgba_alpha(mix(RGBA(255, 255, 255, 255), RGBA(150, 120, 190, 255), h / 3), 0.5f);
    for (int c = 0; c < 10; c++) {
        float x = S.cloud[c][0] + sinf(S.anim * 0.1f + c) * 10, r = S.cloud[c][2];
        float y = BASE - (S.cloud[c][1] - S.cam * 0.35f);
        if (y < -30 || y > TOP_H + 30)
            continue;
        mg_circle(eye, x, y, r, 0.85f, cc);
        mg_circle(eye, x + r, y + 2, r * 0.8f, 0.85f, cc);
        mg_circle(eye, x - r, y + 3, r * 0.7f, 0.85f, cc);
    }
}

#define NSTRIP 9

static float strip_depth(float th) { return 0.06f + (1 - cosf(th)) * 0.3f; }

static void seam(int eye, float Y, float thick, float dd, u32 c)
{
    float y0 = sy(Y), cur = clampf((Y - eye_y()) * 0.05f, -5, 5);
    float px = 0, py = 0;
    for (int i = 0; i <= 6; i++) {
        float th = -1.5708f + 3.14159f * i / 6;
        float x = CX + TR * sinf(th), y = y0 - cur * cosf(th);
        if (i) {
            float tm = th - 3.14159f / 12;
            mg_line(eye, px, py, x, y, thick, strip_depth(tm) + dd, c);
        }
        px = x;
        py = y;
    }
}

static void draw_tower(int eye)
{
    float ytop = sy(Y_TOP), ybot = sy(-22);
    float y0 = clampf(ytop, -10, TOP_H + 10), y1 = clampf(ybot, -10, TOP_H + 10);
    /* ground */
    if (ybot < TOP_H) {
        mg_rect(eye, -20, ybot, TOP_W + 40, TOP_H - ybot + 4, 0.12f, RGBA(92, 150, 84, 255));
        mg_rect(eye, -20, ybot, TOP_W + 40, 3, 0.1f, RGBA(130, 190, 110, 255));
        draw_cat(eye, 128, ybot + 12, 0.0f);
    }
    if (y1 > y0)
        for (int i = 0; i < NSTRIP; i++) {
            float a0 = -1.5708f + 3.14159f * i / NSTRIP, a1 = -1.5708f + 3.14159f * (i + 1) / NSTRIP;
            float x0 = CX + TR * sinf(a0), x1 = CX + TR * sinf(a1), am = (a0 + a1) / 2;
            float sh = 0.5f + 0.5f * clampf(cosf(am + 0.45f), 0, 1);
            u32 c = mix(RGBA(70, 64, 92, 255), RGBA(196, 188, 214, 255), sh);
            mg_rect(eye, x0 - 1, y0, x1 - x0 + 2, y1 - y0, strip_depth(am), c);
        }
    int lo = (int)floorf((S.cam - 90) / SEG), hi = (int)ceilf((S.cam + 200) / SEG);
    if (lo < 0)
        lo = 0;
    if (hi > SEGS - 1)
        hi = SEGS - 1;
    for (int k = lo; k <= hi; k++) {
        float yb = k * SEG - 20, ym = sy(yb + SEG * 0.5f);
        seam(eye, yb, 1.5f, -0.01f, RGBA(60, 54, 80, 200));
        for (int w = 0; w < 2; w++) {
            float wa = S.win[k][w], wc = cosf(wa);
            if (wc < 0.25f)
                continue;
            float wx = CX + TR * sinf(wa), ww = 7 * wc;
            mg_rect(eye, wx - ww / 2, ym - 4, ww, 11, strip_depth(wa) - 0.01f, RGBA(44, 36, 64, 255));
            mg_circle(eye, wx, ym - 4, ww / 2, strip_depth(wa) - 0.01f, RGBA(44, 36, 64, 255));
        }
    }
    /* the current segment's outline */
    if (S.st != ST_TOP) {
        float yb = S.level * SEG - 20;
        float pulse = 0.7f + 0.3f * sinf(S.anim * 5);
        u32 hc = rgba_alpha(RGBA(255, 200, 70, 255), pulse);
        float ta = sy(yb + SEG), tb = sy(yb);
        mg_rect(eye, CX - TR, ta, TR * 2, tb - ta, 0.04f, RGBA(255, 236, 170, (u32)(30 + 25 * pulse)));
        seam(eye, yb, 4.0f, -0.025f, RGBA(60, 40, 20, 120));
        seam(eye, yb + SEG, 4.0f, -0.025f, RGBA(60, 40, 20, 120));
        seam(eye, yb, 2.4f, -0.03f, hc);
        seam(eye, yb + SEG, 2.4f, -0.03f, hc);
        float a = sy(yb), b = sy(yb + SEG);
        mg_line(eye, CX - TR, a, CX - TR, b, 2.6f, strip_depth(1.5708f) - 0.03f, hc);
        mg_line(eye, CX + TR, a, CX + TR, b, 2.6f, strip_depth(1.5708f) - 0.03f, hc);
        char buf[8];
        snprintf(buf, sizeof(buf), "%d", S.level + 1);
        mg_text_centered(eye, buf, CX, sy(yb + SEG) + 4, 0.42f, 0.02f, rgba_alpha(MG_GOLD, 0.85f));
    }
    /* crown */
    if (ytop > -20 && ytop < TOP_H + 20) {
        mg_rect(eye, CX - TR - 4, ytop - 2, TR * 2 + 8, 6, 0.05f, RGBA(150, 142, 172, 255));
        for (int m = 0; m < 5; m++) {
            float a = -1.2f + 0.6f * m, w = 11 * cosf(a);
            float mx = CX + (TR + 2) * sinf(a);
            mg_rect(eye, mx - w / 2, ytop - 12, w, 10, strip_depth(a) - 0.02f,
                    mix(RGBA(90, 82, 112, 255), RGBA(190, 182, 210, 255), 0.5f + 0.5f * cosf(a + 0.45f)));
        }
        if (S.st == ST_TOP) {   /* from up here you can see the hole */
            fill_ellipse(eye, CX, ytop - 2, TR + 4, 7, 0.03f, RGBA(170, 162, 192, 255));
            fill_ellipse(eye, CX, ytop - 2, TR - 14, 4.5f, 0.02f, RGBA(20, 14, 30, 255));
        } else {
            mg_line(eye, CX, ytop - 12, CX, ytop - 34, 1.5f, 0.05f, RGBA(80, 70, 60, 255));
            float wv = sinf(S.anim * 4) * 2;
            mg_tri(eye, CX, ytop - 34, CX + 14, ytop - 30 + wv, CX, ytop - 25, 0.04f, RGBA(240, 90, 90, 255));
        }
    }
}

static void draw_layer(int eye, bool front)
{
    int lo = S.level - 1 < 0 ? 0 : S.level - 1, hi = S.level + 4 >= SEGS ? SEGS - 1 : S.level + 4;
    for (int k = lo; k <= hi; k++)
        if ((leaf_c(k) >= 0) == front)
            draw_leaf(eye, k, 0);
    bool aron_front = S.st == ST_TOP || leaf_c(S.level) >= 0;
    if (aron_front == front) {
        if (S.st == ST_TOP) {
            float tt = S.st_t;
            if (tt < 1.1f) {
                float p = clampf(tt / 0.8f, 0, 1);
                float x = lerpf(S.x0, CX, p), Y = lerpf(S.Y0, Y_TOP + 4, p) + sinf(p * 3.14159f) * 40;
                float s = tt < 0.8f ? 1 : clampf(1 - (tt - 0.8f) / 0.3f, 0, 1);
                if (tt > 0.8f)
                    Y -= (tt - 0.8f) * 30;
                if (s > 0.05f)
                    draw_aron(eye, x, sy(Y), -0.05f, s * 1.15f, 1, 1);
            }
        } else {
            int pose = S.st == ST_JUMP ? 1 : S.stun > 0 ? 2 : 0;
            draw_aron(eye, aron_x(), sy(S.Y), leaf_depth(S.level) - 0.03f, 1.15f, 1, pose);
        }
    }
    for (int k = lo; k <= hi; k++)
        if ((leaf_c(k) >= 0) == front)
            draw_leaf(eye, k, 1);
}

/* ---- drawing: the top -------------------------------------------------------- */

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
        /* Pim and Dross */
        {
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
        /* a beach umbrella */
        mg_line(eye, 90, 224, 96, 176, 2, -0.05f, RGBA(120, 90, 60, 255));
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
    /* the tower's top, with its hole */
    mg_rect(eye, 160, 200, 80, 44, 0.0f, RGBA(150, 142, 172, 255));
    mg_rect(eye, 160, 200, 12, 44, 0.02f, RGBA(110, 102, 134, 255));
    mg_rect(eye, 228, 200, 12, 44, 0.02f, RGBA(110, 102, 134, 255));
    fill_ellipse(eye, 200, 200, 40, 8, -0.01f, RGBA(190, 182, 210, 255));
    fill_ellipse(eye, 200, 200, 26, 5, -0.02f, RGBA(20, 14, 30, 255));

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

static void draw_effects(int eye, bool scene)
{
    for (int i = 0; i < NPART; i++) {
        Part *p = &S.p[i];
        if (p->life <= 0 || p->world == scene)
            continue;
        float y = p->world ? sy(p->y) : p->y;
        float a = clampf(p->life / p->max * 1.5f, 0, 1);
        mg_rect(eye, p->x - p->size / 2, y - p->size / 2, p->size, p->size, p->depth, rgba_alpha(p->c, a));
    }
    for (int i = 0; i < NPOP; i++) {
        Pop *p = &S.pop[i];
        if (p->t <= 0)
            continue;
        float age = p->max - p->t, k = clampf(age / 0.15f, 0, 1);
        float a = clampf(p->t / 0.3f, 0, 1);
        float sc = p->scale * (0.6f + 0.4f * k);
        for (int o = 0; o < 2; o++)
            mg_text_centered(eye, p->txt, p->x + (o ? 1.5f : -1), p->y - fminf(age, 0.6f) * 12 + 1.5f, sc, p->depth + 0.02f,
                             rgba_alpha(RGBA(20, 16, 30, 255), a));
        mg_text_centered(eye, p->txt, p->x, p->y - fminf(age, 0.6f) * 12, sc, p->depth, rgba_alpha(p->c, a));
    }
}

static void draw_top(int eye)
{
    if (S.st == ST_TOP && S.st_t >= 1.3f) {
        draw_scene(eye);
        draw_effects(eye, true);
    } else {
        draw_sky(eye);
        draw_layer(eye, false);
        draw_tower(eye);
        draw_layer(eye, true);
        /* a ghost of Aron when the tower hides him */
        if (S.st != ST_TOP && leaf_c(S.level) < 0 && fabsf(aron_x() - CX) < TR + 4)
            draw_aron(eye, aron_x(), sy(S.Y), 0.0f, 1.15f, 0.4f, S.st == ST_JUMP ? 1 : 0);
        draw_effects(eye, false);
        if (S.warp > 0)
            mg_circle(eye, aron_x(), sy(S.Y + 8), 30 * (1 - S.warp / 0.6f) + 4, -0.1f,
                      RGBA(210, 190, 255, (u32)(160 * S.warp / 0.6f)));
        if (S.st != ST_TOP) {
            char buf[32];
            snprintf(buf, sizeof(buf), "%d/16", S.level + 1);
            mg_text(eye, buf, 8, 6, 0.5f, -0.15f, MG_WHITE);
            for (int t = 0; t < 4; t++)
                mg_rect(eye, 352 + t * 11, 10, 8, 8, -0.15f,
                        t <= S.tier ? RGBA(255, 190, 90, 255) : RGBA(255, 255, 255, 60));
        }
    }
    if (S.flash > 0) {
        float a = 1 - fabsf(S.flash - 0.25f) / 0.25f;
        gfx_rect(0, 0, TOP_W, TOP_H, RGBA(255, 255, 255, (u32)(255 * clampf(a, 0, 1))));
    }
}

/* ---- bottom screen: minimap -------------------------------------------------- */

static void draw_bottom(void)
{
    static const u32 TC[4] = {RGBA(110, 200, 120, 255), RGBA(230, 210, 90, 255), RGBA(240, 150, 80, 255),
                              RGBA(230, 90, 100, 255)};
    char buf[64];
    gfx_text("The Tower", 100, 6, 0.55f, MG_GOLD);
    /* tower minimap */
    float bx = 18, bw = 50, sh = 12;
    for (int k = 0; k < SEGS; k++) {
        float y = 222 - (k + 1) * sh;
        bool reached = k <= S.level;
        u32 c = reached ? TC[tier_of(k)] : rgba_alpha(TC[tier_of(k)], 0.25f);
        gfx_rect(bx, y + 1, bw, sh - 2, c);
        if (k == S.level && S.st != ST_TOP) {
            gfx_line(bx - 3, y - 1, bx + bw + 3, y - 1, 2, MG_WHITE);
            gfx_line(bx - 3, y + sh + 1, bx + bw + 3, y + sh + 1, 2, MG_WHITE);
            gfx_line(bx - 3, y - 1, bx - 3, y + sh + 1, 2, MG_WHITE);
            gfx_line(bx + bw + 3, y - 1, bx + bw + 3, y + sh + 1, 2, MG_WHITE);
            gfx_circle(bx + bw + 10, y + sh / 2, 3.5f, MG_WHITE);
        }
    }
    for (int m = 0; m < 4; m++)
        gfx_rect(bx + m * 14, 222 - SEGS * sh - 7, 8, 6, S.done ? MG_GOLD : RGBA(180, 172, 200, 255));
    if (S.done)
        gfx_circle(bx + bw / 2, 222 - SEGS * sh - 14, 4, MG_GOLD);
    gfx_rect(bx - 6, 222, bw + 12, 3, RGBA(110, 170, 100, 255));

    /* the orbit seen from above (you look from the bottom) */
    float ox = 150, oy = 96, orr = 46;
    for (int i = 0; i < 12; i++) {   /* the unreachable side, behind the tower */
        float a0 = 1.875f + 2.533f * i / 12, a1 = 1.875f + 2.533f * (i + 1) / 12;
        gfx_triangle(ox, oy, ox + (orr + 10) * sinf(a0), oy + (orr + 10) * cosf(a0), ox + (orr + 10) * sinf(a1),
                     oy + (orr + 10) * cosf(a1), RGBA(0, 0, 0, 70));
    }
    for (int i = 0; i < 24; i++) {
        float a0 = 6.2832f * i / 24, a1 = 6.2832f * (i + 1) / 24;
        gfx_line(ox + orr * sinf(a0), oy + orr * cosf(a0), ox + orr * sinf(a1), oy + orr * cosf(a1), 1,
                 RGBA(255, 255, 255, 60));
    }
    gfx_circle(ox, oy, 22, RGBA(150, 142, 172, 255));
    gfx_text("you", ox - 9, oy + orr + 14, 0.4f, RGBA(180, 180, 200, 255));
    if (S.st != ST_TOP && S.st != ST_TIMEUP) {
        int k = S.level + 1;
        if (k < SEGS) {
            float a = ang(k);
            bool reach = cosf(a) > REACH_COS;
            float x = ox + orr * sinf(a), y = oy + orr * cosf(a);
            u32 c = !reach ? RGBA(120, 140, 170, 255)
                  : fabsf(aron_x() - leaf_x(k)) < HOLE ? RGBA(255, 214, 96, 255) : RGBA(160, 245, 200, 255);
            gfx_circle(x, y, 8, c);
            gfx_circle(x, y, 5, RGBA(28, 24, 44, 255));
        }
        float a = ang(S.level);
        gfx_circle(ox + orr * sinf(a), oy + orr * cosf(a), 7, RGBA(108, 196, 104, 255));
        float aa = a + S.u / ORBIT;
        gfx_circle(ox + orr * sinf(aa), oy + orr * cosf(aa), 2.5f, RGBA(58, 156, 230, 255));
    }

    /* numbers */
    float tx = 220;
    snprintf(buf, sizeof(buf), "Segment %d/16", S.level + 1);
    gfx_text(buf, tx, 34, 0.48f, MG_WHITE);
    snprintf(buf, sizeof(buf), "Tier %d of 4", S.tier + 1);
    gfx_text(buf, tx, 58, 0.48f, TC[S.tier]);
    snprintf(buf, sizeof(buf), "Falls %d", S.falls);
    gfx_text(buf, tx, 82, 0.48f, S.falls ? RGBA(255, 170, 150, 255) : MG_WHITE);
    float t = S.done ? S.end_t : S.t;
    snprintf(buf, sizeof(buf), "Time %d:%02d", (int)t / 60, (int)t % 60);
    gfx_text(buf, tx, 106, 0.48f, MG_WHITE);
    float left = TIME_CAP - S.t;
    if (!S.done && left < 30) {
        snprintf(buf, sizeof(buf), "%d s left!", (int)left + 1);
        gfx_text(buf, tx, 130, 0.45f, RGBA(255, 150, 130, 255));
    }
    gfx_text("A: jump\nD-pad: walk", 96, 176, 0.42f, RGBA(180, 180, 200, 255));
}

/* ---- score ------------------------------------------------------------------- */

static int score(void)
{
    float p = clampf(S.progress / 39.0f, 0, 1);
    float t = S.done ? S.end_t : TIME_CAP;
    float tq = clampf((150 - t) / 105, 0, 1);
    float fq = 1.0f / (1.0f + S.falls * 0.25f);
    float s = 55 * p + (S.done ? 15 : 0) + p * (18 * fq + 12 * tq);
    return (int)clampf(s + 0.5f, 0, 100);
}

static const char *verdict(void)
{
    static char buf[128];
    if (S.done)
        snprintf(buf, sizeof(buf), "Top in %d:%02d, %d fall%s. Aron found %s.", (int)S.end_t / 60,
                 (int)S.end_t % 60, S.falls, S.falls == 1 ? "" : "s", SCENE_FOUND[S.scene]);
    else
        snprintf(buf, sizeof(buf), "Reached segment %d of 16. The tower keeps its secret.", S.level + 1);
    return buf;
}

/* ---- bot ------------------------------------------------------------------------- */

static void bot(Input *in, float t)
{
    if (S.st == ST_TOP || S.st == ST_TIMEUP)
        return;
    int k = S.level + 1;
    if (k >= SEGS)
        return;
    if (!B.cheated && S.level == 5 && S.st == ST_JUMP && S.vy < 250) {
        in->down |= KEY_L_;
        B.cheated = true;
        return;
    }
    const float T = 0.14f;   /* until the head reaches the ring */
    float w = SPEED[S.tier];
    float own = CX + ORBIT * sinf(ang(S.level) + w * T);
    float tgt = CX + ORBIT * sinf(ang(k) + w * T);
    bool reach = cosf(ang(k) + w * T) > REACH_COS + 0.1f;
    float want = clampf(tgt - own, -UMAX, UMAX), diff = want - S.u;
    in->cx = fabsf(diff) < 1.5f ? 0 : clampf(diff / 6.0f, -1, 1);
    if (S.st != ST_STAND || S.stun > 0)
        return;
    if (!B.missed_once && S.level == 1 && t > 1.5f && fabsf(own + S.u - tgt) > 30) {
        in->down |= KEY_A_;   /* one deliberate miss to show the penalty */
        B.missed_once = true;
        return;
    }
    if (reach && fabsf(own + S.u - tgt) < 5)
        in->down |= KEY_A_;
}

/* the cheat can't help once the run is wrapping up */
static bool can_cheat(void) { return S.st == ST_STAND || S.st == ST_JUMP; }

const MiniGame MG_TOWER = {
    .id = "tower",
    .title = "The Tower",
    .rules = "Help tiny Aron climb the tower, one segment\n"
             "at a time. One leaf grows from each segment\n"
             "and all leaves circle the tower together.\n"
             "Stand right under the next leaf's ring and\n"
             "jump up through it to land on it. Dim rings\n"
             "behind the tower are out of reach.\n"
             "Every 4 segments the spin gets faster.\n"
             "Falls and slow climbing cost points.",
    .controls = "D-pad / Circle Pad: walk along your leaf\n"
                "A (or B): jump - you can steer a little\n"
                "The ring turns gold when you're lined up\n"
                "START: pause",
    .cheat = "Skip ahead one speed tier, even mid-jump",
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
