/* The Hungry Sky: a stereoscopic space-invaders game. The player flies a
 * small lantern-ship of light near the bottom of the top screen and shoots
 * up into a swaying, stepping formation whose rows hang at different stereo
 * depths: Purgatorium spirits (wave 1), Seraphiel's angels (wave 2), then
 * both together with angels that dive (wave 3). Last comes Lord Ashveil, a
 * childlike energy-vampire being who is hungry, not evil: light spreads, a
 * pull toward his mouth, and spirits he spits out. Beaten, he shrinks into
 * a small, sated, sleepy creature.
 *
 * Depth: everything in the play field takes its stereo depth from its
 * height (depth_at): the ship pops out at SHIP_D, each formation row sits
 * at its own depth behind the screen, so shots visibly fly into the screen.
 *
 * Score (0..100):
 *   30 * kills / regular enemies             (cheat-cleared ones don't count)
 * + 15 * min(1, accuracy / 0.8)
 * + boss beaten: 30 + 15 * lives left / 3 + 10 * time bonus (full under 120 s,
 *                none after 300 s)
 *   boss not beaten: 15 * damage dealt to the boss
 * so anything above 60 requires beating the boss. */

#include "minigame.h"

#define MAXE 32   /* enemies in a wave */
#define MAXPS 4   /* player shots in flight */
#define MAXES 48  /* enemy shots */
#define MAXM 10   /* boss minions */
#define MAXP 64   /* particles */

#define SHIP_D (-0.25f)
#define SHIP_Y0 210.0f
#define SHIP_YMIN 190.0f
#define SHIP_YMAX 224.0f
#define BOSS_D 0.32f
#define BOSS_HP 140
#define WAVES 3

enum { K_SPIRIT, K_ANGEL, K_CAPTAIN };
enum { E_FORM, E_DIVE, E_RETURN };
enum { S_WISP, S_BOLT, S_ORB };
enum { ST_WAVE_IN, ST_WAVE, ST_CLEAR, ST_BOSS_IN, ST_BOSS, ST_BOSS_DOWN, ST_OVER };

typedef struct {
    bool alive;
    u8 kind, hp, row, col, state;
    bool fired;           /* diver already dropped its bolt */
    float x, y;           /* current position */
    float vx, vy, dt;     /* dive motion */
    float phase;          /* blink / flap offset */
    float hurt;           /* flash after a non-lethal hit */
} Enemy;

typedef struct {
    bool alive;
    float x, y;
} PShot;

typedef struct {
    bool alive;
    u8 kind;
    float x, y, vx, vy, phase;
} EShot;

typedef struct {
    bool alive;
    float x, y, vx, vy, phase;
} Minion;

typedef struct {
    float x, y, vx, vy, life, max, size, depth;
    u32 color;
} Particle;

static struct {
    int st;
    float st_t;           /* seconds in the current state */
    float t;              /* seconds since start */
    int wave;             /* 0..WAVES-1 */

    /* the ship */
    float sx, sy;
    float fire_cd;
    float invuln;
    int lives;
    float life_lost_t;    /* > 0: counting down to the life_lost chime */
    int hits_taken;

    /* formation */
    Enemy e[MAXE];
    int ne, nrows;
    int row_n[4];
    float row_sp[4];
    float fx, fy, fdir, fspeed;
    float fvel;           /* current sideways speed (for the bot) */
    float fire_t, dive_t;

    PShot ps[MAXPS];
    EShot es[MAXES];
    Minion m[MAXM];
    Particle p[MAXP];

    /* the boss */
    float bx, by, bscale;
    int bhp;
    int bphase;           /* 1..3 */
    float spread_t, spit_t, pull_cycle, pull_t;
    int pull_state;       /* 0 idle, 1 opening (warning), 2 pulling */
    float bhurt, mouth_kick;
    float boss_dmg_frac;

    /* scoring */
    int points, kills, total_regular, shots, hits;
    bool reached_boss, boss_beaten;
    float end_t;

    /* golden light */
    float flash;
    float flash_x, flash_y;
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

static float row_depth(int r)
{
    if (G.nrows <= 1)
        return 0.2f;
    return 0.42f - r * (0.36f / (G.nrows - 1));
}

static float row_y(int r) { return G.fy + r * 24.0f; }

/* Stereo depth of the play field at height y. */
static float depth_at(float y)
{
    if (G.st >= ST_BOSS_IN) {
        float by = G.by + 20;
        if (y <= by)
            return BOSS_D;
        return lerpf(BOSS_D, SHIP_D, clampf((y - by) / (SHIP_Y0 - by), 0, 1));
    }
    float top = row_y(0), bot = row_y(G.nrows - 1);
    if (y <= top)
        return row_depth(0);
    if (y >= bot) {
        float span = SHIP_Y0 - bot;
        if (span < 20)
            span = 20;
        return lerpf(row_depth(G.nrows - 1), SHIP_D, clampf((y - bot) / span, 0, 1.15f));
    }
    float f = (y - top) / 24.0f;
    int r = (int)f;
    if (r >= G.nrows - 1)
        return row_depth(G.nrows - 1);
    return lerpf(row_depth(r), row_depth(r + 1), f - r);
}

/* Things further behind the screen are drawn a little smaller. */
static float depth_scale(float d) { return 1.0f - 0.3f * d; }

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
                p->max = p->life = randr(0.35f, 0.8f);
                p->size = randr(1.2f, 2.8f);
                p->depth = d;
                p->color = color;
                break;
            }
}

/* ---- waves --------------------------------------------------------------- */

static void slot_pos(const Enemy *e, float *x, float *y)
{
    float sway = sinf(G.t * 0.9f) * 6.0f;
    *x = G.fx + (e->col - (G.row_n[e->row] - 1) * 0.5f) * G.row_sp[e->row] + sway;
    *y = row_y(e->row) + sinf(G.t * 2.2f + e->col * 0.7f) * 2.0f;
}

static void add_row(int kind, int count)
{
    int r = G.nrows++;
    G.row_n[r] = count;
    G.row_sp[r] = kind == K_SPIRIT ? 36.0f : 42.0f;
    for (int c = 0; c < count && G.ne < MAXE; c++) {
        Enemy *e = &G.e[G.ne++];
        memset(e, 0, sizeof(*e));
        e->alive = true;
        e->kind = (u8)kind;
        e->hp = kind == K_CAPTAIN ? 2 : 1;
        e->row = (u8)r;
        e->col = (u8)c;
        e->phase = randr(0, 6.2832f);
    }
}

static void setup_wave(int w)
{
    G.wave = w;
    G.ne = G.nrows = 0;
    memset(G.e, 0, sizeof(G.e));
    if (w == 0) {
        add_row(K_SPIRIT, 8);
        add_row(K_SPIRIT, 8);
        add_row(K_SPIRIT, 8);
    } else if (w == 1) {
        add_row(K_CAPTAIN, 6);
        add_row(K_ANGEL, 7);
        add_row(K_ANGEL, 7);
    } else {
        add_row(K_CAPTAIN, 6);
        add_row(K_ANGEL, 7);
        add_row(K_SPIRIT, 8);
        add_row(K_SPIRIT, 8);
    }
    G.fx = 200;
    G.fy = -110;
    G.fdir = (w & 1) ? -1 : 1;
    G.fspeed = 20.0f + 4.0f * w;
    G.fire_t = 2.0f;
    G.dive_t = 3.0f;
    G.st = ST_WAVE_IN;
    G.st_t = 0;
    for (int i = 0; i < G.ne; i++)
        slot_pos(&G.e[i], &G.e[i].x, &G.e[i].y);
}

static int alive_count(void)
{
    int n = 0;
    for (int i = 0; i < G.ne; i++)
        n += G.e[i].alive;
    return n;
}

static void clear_shots(void)
{
    memset(G.es, 0, sizeof(G.es));
    memset(G.m, 0, sizeof(G.m));
}

/* ---- start --------------------------------------------------------------- */

static void start(u32 seed)
{
    (void)seed;
    memset(&G, 0, sizeof(G));
    G.sx = 200;
    G.sy = SHIP_Y0;
    G.lives = 3;
    G.total_regular = 24 + 20 + 29;
    G.bscale = 1;
    setup_wave(0);
}

/* ---- hits ---------------------------------------------------------------- */

static void hit_player(void)
{
    if (G.invuln > 0 || G.lives <= 0 || G.st == ST_BOSS_DOWN || G.st == ST_OVER)
        return;
    G.lives--;
    G.hits_taken++;
#ifdef INV_DEBUG
    printf("invaders: hit at %.1f s, state %d wave %d pull %d ship %.0f,%.0f\n", G.t, G.st, G.wave, G.pull_state, G.sx, G.sy);
#endif
    G.invuln = 2.0f;
    burst(G.sx, G.sy, 14, RGBA(255, 220, 150, 255), 90);
    sfx("invaders_player_hit");
    if (G.lives <= 0) {
        mg_sfx("invaders_game_over");
        G.st = ST_OVER;
        G.st_t = 0;
    } else {
        G.life_lost_t = 0.35f;
    }
}

static void kill_enemy(Enemy *e, bool by_shot)
{
    e->alive = false;
    if (by_shot) {
        G.kills++;
        int pts = e->kind == K_SPIRIT ? 10 : e->kind == K_ANGEL ? 20 : 40;
        G.points += e->state == E_DIVE ? pts * 2 : pts;
    }
    if (e->kind == K_SPIRIT) {
        burst(e->x, e->y, 8, RGBA(150, 240, 255, 255), 60);
        sfx("invaders_hit_spirit");
    } else {
        burst(e->x, e->y, 10, RGBA(255, 220, 120, 255), 70);
        burst(e->x, e->y, 4, RGBA(255, 255, 255, 255), 40);
        sfx("invaders_hit_angel");
    }
}

static void golden_light(void)
{
    G.flash = 1.2f;
    G.flash_x = G.sx;
    G.flash_y = G.sy;
    mg_sfx("invaders_golden_light");
    for (int i = 0; i < MAXES; i++)
        if (G.es[i].alive)
            burst(G.es[i].x, G.es[i].y, 1, MG_GOLD, 30);
    for (int i = 0; i < MAXM; i++)
        if (G.m[i].alive)
            burst(G.m[i].x, G.m[i].y, 3, MG_GOLD, 50);
    clear_shots();
    if (G.st == ST_WAVE || G.st == ST_WAVE_IN) {
        for (int i = 0; i < G.ne; i++)
            if (G.e[i].alive) {
                G.e[i].alive = false;
                burst(G.e[i].x, G.e[i].y, 3, MG_GOLD, 60);
            }
    } else if (G.st == ST_BOSS || G.st == ST_BOSS_IN) {
        G.bhp -= (BOSS_HP * 35 + 99) / 100;
        G.bhurt = 0.6f;
        burst(G.bx, G.by, 12, MG_GOLD, 120);
    }
}

/* ---- update: ship and shots ---------------------------------------------- */

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
    G.sx += mx * 160.0f * dt;
    G.sy -= my * 80.0f * dt;

    /* Ashveil's pull drags the ship toward his mouth */
    float ymin = SHIP_YMIN;
    if (G.st == ST_BOSS && G.pull_state == 2) {
        float mxp = G.bx, myp = G.by + 24;
        float dx = mxp - G.sx, dy = myp - G.sy, d = sqrtf(dx * dx + dy * dy) + 1;
        G.sx += dx / d * 70.0f * dt;
        G.sy += dy / d * 52.0f * dt;
        ymin = 140;
    } else if (G.sy < SHIP_YMIN) {
        G.sy += 60.0f * dt;   /* drift back down after a pull */
        ymin = G.sy;
    }
    G.sx = clampf(G.sx, 14, TOP_W - 14);
    G.sy = clampf(G.sy, ymin, SHIP_YMAX);
    if (G.st == ST_BOSS && G.pull_state == 2 && G.sy < 160) {
        hit_player();
        G.sy = SHIP_Y0;
    }

    /* fire: a tap fires at once, holding A auto-fires steadily */
    G.fire_cd -= dt;
    bool want = (in->down & KEY_A_) ? G.fire_cd <= 0.06f : (in->held & KEY_A_) && G.fire_cd <= 0;
    bool can = G.st == ST_WAVE || G.st == ST_WAVE_IN || G.st == ST_BOSS;
    if (want && can)
        for (int i = 0; i < MAXPS; i++)
            if (!G.ps[i].alive) {
                G.ps[i].alive = true;
                G.ps[i].x = G.sx;
                G.ps[i].y = G.sy - 12;
                G.fire_cd = 0.22f;
                G.shots++;
                sfx("invaders_shoot");
                break;
            }
}

static void update_player_shots(float dt)
{
    for (int i = 0; i < MAXPS; i++) {
        PShot *s = &G.ps[i];
        if (!s->alive)
            continue;
        s->y -= 360.0f * dt;
        if (s->y < -10) {
            s->alive = false;
            continue;
        }
        /* enemies */
        for (int k = 0; k < G.ne && s->alive; k++) {
            Enemy *e = &G.e[k];
            if (!e->alive)
                continue;
            float r = 12.0f * depth_scale(depth_at(e->y));
            if (fabsf(s->x - e->x) < r && fabsf(s->y - e->y) < r) {
                s->alive = false;
                G.hits++;
                if (e->hp > 1) {
                    e->hp--;
                    e->hurt = 0.3f;
                    G.points += 5;
                    burst(s->x, s->y, 3, MG_WHITE, 40);
                    sfx("invaders_angel_armor");
                } else {
                    kill_enemy(e, true);
                }
            }
        }
        /* minions */
        for (int k = 0; k < MAXM && s->alive; k++) {
            Minion *m = &G.m[k];
            if (m->alive && fabsf(s->x - m->x) < 9 && fabsf(s->y - m->y) < 9) {
                s->alive = false;
                m->alive = false;
                G.hits++;
                G.points += 15;
                burst(m->x, m->y, 6, RGBA(200, 160, 255, 255), 50);
                sfx("invaders_hit_spirit");
            }
        }
        /* the boss's face */
        if (s->alive && G.st == ST_BOSS) {
            float dx = s->x - G.bx, dy = s->y - G.by;
            if (dx * dx + dy * dy < 46.0f * 46.0f) {
                bool mouth = G.pull_state > 0 && fabsf(dx) < 16 && fabsf(dy - 24) < 16;
                s->alive = false;
                G.hits++;
                G.bhp -= mouth ? 2 : 1;
                G.points += mouth ? 10 : 5;
                G.bhurt = 0.12f;
                burst(s->x, s->y, mouth ? 6 : 3, mouth ? MG_GOLD : RGBA(220, 200, 255, 255), 45);
                sfx(mouth ? "invaders_boss_gulp" : "invaders_boss_hit");
            }
        }
    }
}

static void fire_enemy_shot(int kind, float x, float y, float vx, float vy)
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

static void update_enemy_shots(float dt)
{
    for (int i = 0; i < MAXES; i++) {
        EShot *s = &G.es[i];
        if (!s->alive)
            continue;
        s->phase += dt;
        s->x += s->vx * dt + (s->kind == S_WISP ? cosf(s->phase * 5) * 20 * dt : 0);
        s->y += s->vy * dt;
        if (s->y > TOP_H + 10 || s->y < -20 || s->x < -20 || s->x > TOP_W + 20) {
            s->alive = false;
            continue;
        }
        float r = s->kind == S_ORB ? 7 : 6;
        if (fabsf(s->x - G.sx) < r && fabsf(s->y - G.sy) < r + 2) {
            s->alive = false;
#ifdef INV_DEBUG
            printf("invaders: shot kind %d at %.0f,%.0f v %.0f,%.0f\n", s->kind, s->x, s->y, s->vx, s->vy);
#endif
            hit_player();
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

/* ---- update: formation --------------------------------------------------- */

static void update_formation(float dt)
{
    int alive = alive_count();
    float speed = G.fspeed * (1.0f + 1.6f * (1.0f - (float)alive / (float)(G.ne ? G.ne : 1)));

    if (G.st == ST_WAVE_IN) {
        G.fy = lerpf(-110, 34, clampf(G.st_t / 1.8f, 0, 1));
        if (G.st_t >= 1.8f) {
            G.st = ST_WAVE;
            G.st_t = 0;
        }
    } else {
        G.fx += G.fdir * speed * dt;
        G.fvel = G.fdir * speed;
        float lo = 1e9f, hi = -1e9f, low = -1e9f;
        for (int i = 0; i < G.ne; i++) {
            Enemy *e = &G.e[i];
            if (!e->alive || e->state != E_FORM)
                continue;
            if (e->x < lo)
                lo = e->x;
            if (e->x > hi)
                hi = e->x;
            if (e->y > low)
                low = e->y;
        }
        if ((G.fdir > 0 && hi > TOP_W - 16) || (G.fdir < 0 && lo < 16)) {
            G.fdir = -G.fdir;
            G.fy += 8;
            sfx("invaders_step");
        }
        if (low > 176) {   /* the formation reached the ship's lane */
            G.fy -= 64;
            sfx("invaders_overrun");
            hit_player();
        }
    }

    for (int i = 0; i < G.ne; i++) {
        Enemy *e = &G.e[i];
        if (!e->alive)
            continue;
        if (e->hurt > 0)
            e->hurt -= dt;
        float tx, ty;
        slot_pos(e, &tx, &ty);
        if (e->state == E_FORM) {
            e->x = tx;
            e->y = ty;
        } else if (e->state == E_DIVE) {
            e->dt += dt;
            if (e->dt < 0.5f) {           /* swing up and out */
                e->vy += 260.0f * dt;
            } else {                       /* then swoop at the ship */
                float want = clampf((G.sx - e->x) * 1.6f, -120, 120);
                e->vx += (want - e->vx) * clampf(3.0f * dt, 0, 1);
                e->vy = fminf(e->vy + 240.0f * dt, 150.0f);
            }
            e->x += e->vx * dt;
            e->y += e->vy * dt;
            if (!e->fired && e->y > 100) {
                e->fired = true;
                fire_enemy_shot(S_BOLT, e->x, e->y + 6, (G.sx - e->x) * 0.25f, 120);
                sfx("invaders_enemy_shot");
            }
            if (fabsf(e->x - G.sx) < 12 && fabsf(e->y - G.sy) < 12 && G.invuln <= 0) {
                hit_player();
                kill_enemy(e, false);
                continue;
            }
            if (e->y > TOP_H + 20) {
                e->y = -24;
                e->x = tx;
                e->state = E_RETURN;
            }
        } else {   /* E_RETURN */
            float dx = tx - e->x, dy = ty - e->y, d = sqrtf(dx * dx + dy * dy);
            float step = 150.0f * dt;
            if (d <= step) {
                e->x = tx;
                e->y = ty;
                e->state = E_FORM;
            } else {
                e->x += dx / d * step;
                e->y += dy / d * step;
            }
        }
    }

    if (G.st != ST_WAVE)
        return;

    /* shooting */
    G.fire_t -= dt;
    if (G.fire_t <= 0) {
        static const float RATE[WAVES] = {1.4f, 1.05f, 0.85f};
        G.fire_t = RATE[G.wave] * randr(0.7f, 1.3f);
        for (int tries = 0; tries < 10; tries++) {
            Enemy *e = &G.e[mg_randi(0, G.ne - 1)];
            if (!e->alive || e->state != E_FORM)
                continue;
            if (e->kind == K_SPIRIT) {
                fire_enemy_shot(S_WISP, e->x, e->y + 6, 0, 58);
                sfx("invaders_wisp");
            } else {
                fire_enemy_shot(S_BOLT, e->x, e->y + 8, clampf((G.sx - e->x) * 0.15f, -25, 25), 82);
                sfx("invaders_enemy_shot");
            }
            break;
        }
    }

    /* diving angels (wave 3) */
    if (G.wave == 2) {
        G.dive_t -= dt;
        if (G.dive_t <= 0) {
            G.dive_t = randr(2.6f, 4.0f);
            for (int tries = 0; tries < 12; tries++) {
                Enemy *e = &G.e[mg_randi(0, G.ne - 1)];
                if (!e->alive || e->state != E_FORM || e->kind == K_SPIRIT)
                    continue;
                e->state = E_DIVE;
                e->dt = 0;
                e->fired = false;
                e->vx = e->x < G.sx ? -70.0f : 70.0f;
                e->vy = -110.0f;
                sfx("invaders_dive");
                break;
            }
        }
    }

    if (alive == 0) {
        G.st = ST_CLEAR;
        G.st_t = 0;
        memset(G.es, 0, sizeof(G.es));
        sfx("invaders_wave_clear");
    }
}

/* ---- update: boss -------------------------------------------------------- */

static void boss_spread(void)
{
    int n = G.bphase == 1 ? 5 : 7;
    float aim = atan2f(G.sy - (G.by + 24), G.sx - G.bx);
    float spanw = G.bphase == 1 ? 1.1f : 1.4f;
    for (int i = 0; i < n; i++) {
        float a = aim + (i - (n - 1) * 0.5f) * spanw / (n - 1);
        float sp = 72.0f + 8.0f * G.bphase;
        fire_enemy_shot(S_ORB, G.bx, G.by + 24, cosf(a) * sp, sinf(a) * sp);
    }
    G.mouth_kick = 0.4f;
    sfx("invaders_boss_spread");
}

static void boss_spit(void)
{
    for (int k = 0; k < 2; k++)
        for (int i = 0; i < MAXM; i++)
            if (!G.m[i].alive) {
                Minion *m = &G.m[i];
                m->alive = true;
                m->x = G.bx;
                m->y = G.by + 26;
                m->vx = k ? 55.0f : -55.0f;
                m->vy = 30.0f;
                m->phase = randr(0, 6.28f);
                break;
            }
    G.mouth_kick = 0.5f;
    sfx("invaders_boss_spit");
}

static void update_boss(float dt)
{
    if (G.bhurt > 0)
        G.bhurt -= dt;
    if (G.mouth_kick > 0)
        G.mouth_kick -= dt;

    if (G.st == ST_BOSS_IN) {
        G.bx = 200;
        G.by = lerpf(-90, 80, clampf(G.st_t / 3.0f, 0, 1));
        if (G.st_t >= 3.0f) {
            G.st = ST_BOSS;
            G.st_t = 0;
            G.spread_t = 1.2f;
            G.pull_cycle = 5.0f;
            G.spit_t = 2.0f;
        }
        return;
    }

    G.bx = 200 + sinf(G.st_t * 0.5f) * 70.0f * (G.pull_state ? 0.3f : 1.0f);
    G.by = 80 + sinf(G.st_t * 0.9f) * 5.0f;

    int phase = G.bhp > BOSS_HP * 2 / 3 ? 1 : G.bhp > BOSS_HP / 3 ? 2 : 3;
    if (phase != G.bphase) {
        G.bphase = phase;
        if (phase > 1)
            sfx("invaders_boss_phase");
    }

    /* light spreads */
    G.spread_t -= dt;
    if (G.spread_t <= 0 && G.pull_state != 2) {
        G.spread_t = phase == 1 ? 2.4f : phase == 2 ? 2.1f : 1.8f;
        boss_spread();
    }

    /* the pull */
    if (phase >= 2) {
        if (G.pull_state == 0) {
            G.pull_cycle -= dt;
            if (G.pull_cycle <= 0) {
                G.pull_state = 1;
                G.pull_t = 0.9f;
                sfx("invaders_boss_pull");
            }
        } else {
            G.pull_t -= dt;
            if (G.pull_t <= 0) {
                if (G.pull_state == 1) {
                    G.pull_state = 2;
                    G.pull_t = 2.6f;
                } else {
                    G.pull_state = 0;
                    G.pull_cycle = phase == 2 ? 6.5f : 7.5f;
                    sfx("invaders_boss_pull_end");
                }
            }
        }
    }

    /* spat-out spirits */
    if (phase == 3) {
        G.spit_t -= dt;
        if (G.spit_t <= 0 && G.pull_state == 0) {
            G.spit_t = 3.2f;
            boss_spit();
        }
    }
    for (int i = 0; i < MAXM; i++) {
        Minion *m = &G.m[i];
        if (!m->alive)
            continue;
        m->phase += dt;
        m->vx += (G.sx - m->x) * 0.6f * dt;
        m->vx = clampf(m->vx, -70, 70);
        m->vy = fminf(m->vy + 30.0f * dt, 75.0f);
        m->x += (m->vx + cosf(m->phase * 4) * 30) * dt;
        m->y += m->vy * dt;
        if (m->y > TOP_H + 12)
            m->alive = false;
        else if (fabsf(m->x - G.sx) < 9 && fabsf(m->y - G.sy) < 9) {
            m->alive = false;
            hit_player();
        }
    }

    if (G.bhp <= 0) {
        G.bhp = 0;
        G.boss_beaten = true;
        G.points += 1000;
        G.st = ST_BOSS_DOWN;
        G.st_t = 0;
        G.pull_state = 0;
        clear_shots();
        burst(G.bx, G.by, 20, MG_GOLD, 140);
        burst(G.bx, G.by, 14, MG_WHITE, 90);
        mg_sfx("invaders_boss_defeat");
    }
}

/* ---- update -------------------------------------------------------------- */

static bool update(const Input *in, float dt, bool cheat)
{
    G.t += dt;
    G.st_t += dt;
    if (G.flash > 0)
        G.flash -= dt;
    if (G.invuln > 0)
        G.invuln -= dt;
    if (G.life_lost_t > 0) {
        G.life_lost_t -= dt;
        if (G.life_lost_t <= 0)
            mg_sfx("invaders_life_lost");
    }
    if (cheat)
        golden_light();

    if (G.st != ST_OVER && G.st != ST_BOSS_DOWN)
        update_ship(in, dt);
    update_player_shots(dt);
    update_enemy_shots(dt);
    update_particles(dt);

    switch (G.st) {
    case ST_WAVE_IN:
    case ST_WAVE:
        update_formation(dt);
        break;
    case ST_CLEAR:
        if (G.st_t >= 2.2f) {
            if (G.wave + 1 < WAVES) {
                setup_wave(G.wave + 1);
                sfx("invaders_wave_start");
            } else {
                G.st = ST_BOSS_IN;
                G.st_t = 0;
                G.reached_boss = true;
                G.bhp = BOSS_HP;
                G.bphase = 1;
                G.ne = 0;
                mg_music("invaders_boss");
                mg_sfx("invaders_boss_roar");
            }
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
        if (G.st_t >= 5.0f) {
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
        G.boss_dmg_frac = 1.0f - (float)G.bhp / BOSS_HP;
    return true;
}

/* ---- drawing: pieces ----------------------------------------------------- */

static void draw_background(int eye)
{
    bool boss = G.st >= ST_BOSS_IN;
    mg_sky(eye, boss ? RGBA(4, 2, 16, 255) : RGBA(6, 8, 26, 255), boss ? RGBA(30, 10, 44, 255) : RGBA(26, 16, 52, 255));
    /* nebula, far behind */
    static const u32 NEB[5] = {RGBA(120, 60, 170, 34), RGBA(40, 120, 160, 30), RGBA(170, 70, 120, 26),
                               RGBA(60, 80, 180, 30), RGBA(120, 50, 140, 28)};
    for (int i = 0; i < 5; i++) {
        float x = 40 + i * 80 + sinf(G.t * 0.05f + i * 1.7f) * 24;
        float y = 50 + (i * 53 % 120) + cosf(G.t * 0.04f + i) * 10;
        float r = 55 + (i * 23 % 40);
        mg_circle(eye, x, y, r, 0.95f, rgba_alpha(NEB[i], 0.4f));
        mg_circle(eye, x + 6, y - 4, r * 0.72f, 0.95f, rgba_alpha(NEB[i], 0.4f));
        mg_circle(eye, x + 10, y - 6, r * 0.42f, 0.95f, rgba_alpha(NEB[i], 0.5f));
    }
    /* three layers of stars drifting down */
    for (int i = 0; i < 42; i++) {
        int layer = i % 3;
        float d = 1.0f - layer * 0.15f, sp = 6.0f + layer * 9.0f;
        float x = (float)((i * 73 + 17) % TOP_W);
        float y = fmodf((float)((i * 131 + 29) % TOP_H) + G.t * sp, (float)TOP_H);
        float tw = 0.6f + 0.4f * sinf(G.t * (1.5f + layer) + i);
        float sz = layer == 2 ? 2.0f : 1.0f + (i % 2);
        mg_rect(eye, x, y, sz, sz, d, rgba_alpha(RGBA(230, 230, 255, 220), tw));
    }
}

static void draw_ship(int eye)
{
    if (G.st == ST_OVER)
        return;
    if (G.invuln > 0 && fmodf(G.invuln, 0.2f) < 0.08f)
        return;
    float x = G.sx, y = G.sy, d = SHIP_D;
    float fl = 0.85f + 0.15f * sinf(G.t * 23.0f);
    mg_circle(eye, x, y, 14, d + 0.02f, RGBA(255, 210, 120, 36));
    mg_tri(eye, x - 4, y - 1, x - 14, y + 8, x - 4, y + 6, d, RGBA(220, 160, 70, 255));
    mg_tri(eye, x + 4, y - 1, x + 14, y + 8, x + 4, y + 6, d, RGBA(220, 160, 70, 255));
    mg_tri(eye, x - 3, y + 6, x + 3, y + 6, x, y + 10 + 4 * fl, d, RGBA(255, 150, 60, 200));
    mg_rect(eye, x - 5.5f, y - 7, 11, 14, d, RGBA(190, 130, 50, 255));
    mg_rect(eye, x - 3.5f, y - 5, 7, 10, d - 0.01f, rgba_alpha(RGBA(255, 238, 180, 255), fl));
    mg_tri(eye, x - 6.5f, y - 7, x + 6.5f, y - 7, x, y - 13, d, RGBA(160, 100, 40, 255));
    mg_circle(eye, x, y - 1, 2.2f, d - 0.02f, MG_WHITE);
}

static void draw_spirit(int eye, float x, float y, float d, float s, float ph, int tint, float sleepy)
{
    static const u32 COL[3] = {RGBA(120, 230, 255, 255), RGBA(190, 160, 255, 255), RGBA(255, 240, 160, 255)};
    u32 c = COL[tint % 3];
    float blink = 0.55f + 0.45f * sinf(G.t * 4.0f + ph);
    if (fmodf(G.t + ph, 3.1f) < 0.12f)
        blink = 0.2f;   /* a quick flicker now and then */
    mg_circle(eye, x, y, 12 * s, d + 0.01f, rgba_alpha(c, 0.22f * blink + 0.05f));
    mg_circle(eye, x, y, 7.5f * s, d, rgba_alpha(c, 0.55f + 0.45f * blink));
    mg_circle(eye, x, y - 0.5f * s, 4.8f * s, d - 0.005f, rgba_alpha(MG_WHITE, 0.5f + 0.4f * blink));
    u32 ink = RGBA(30, 40, 70, 255);
    if (sleepy > 0) {
        mg_line(eye, x - 3 * s, y - 1 * s, x - 1 * s, y - 1 * s, 1, d - 0.01f, ink);
        mg_line(eye, x + 1 * s, y - 1 * s, x + 3 * s, y - 1 * s, 1, d - 0.01f, ink);
    } else {
        mg_circle(eye, x - 2.3f * s, y - 1.2f * s, 1.1f * s, d - 0.01f, ink);
        mg_circle(eye, x + 2.3f * s, y - 1.2f * s, 1.1f * s, d - 0.01f, ink);
    }
    mg_circle(eye, x, y + 2.0f * s, 1.0f * s, d - 0.01f, ink);
}

static void draw_angel(int eye, const Enemy *e, float d, float s)
{
    float x = e->x, y = e->y;
    float flap = sinf(G.t * 6.0f + e->phase) * 3.0f * s;
    bool diving = e->state == E_DIVE;
    u32 wing = e->hurt > 0 ? RGBA(255, 190, 170, 255) : RGBA(244, 244, 255, 255);
    u32 wing2 = RGBA(214, 218, 240, 255);
    u32 gold = RGBA(255, 205, 90, 255);
    if (diving)
        mg_circle(eye, x, y, 15 * s, d + 0.01f, RGBA(255, 210, 110, 50));
    for (int side = -1; side <= 1; side += 2) {
        float tipx = x + side * 17 * s, tipy = y - 9 * s - flap;
        mg_tri(eye, x + side * 2 * s, y - 3 * s, tipx, tipy, x + side * 13 * s, y + 4 * s, d + 0.005f, wing);
        mg_tri(eye, x + side * 2 * s, y, x + side * 13 * s, y + 4 * s, x + side * 8 * s, y + 9 * s, d + 0.005f, wing2);
        mg_line(eye, x + side * 2 * s, y - 3 * s, tipx, tipy, 1.2f, d, gold);
    }
    /* robe and head */
    mg_tri(eye, x, y - 5 * s, x - 5 * s, y + 11 * s, x + 5 * s, y + 11 * s, d, RGBA(250, 250, 255, 255));
    mg_line(eye, x - 5 * s, y + 10.5f * s, x + 5 * s, y + 10.5f * s, 1.4f, d - 0.005f, gold);
    mg_circle(eye, x, y - 6 * s, 3.4f * s, d - 0.005f, RGBA(255, 232, 200, 255));
    /* halo: a flat golden ring floating above the head */
    float hy = y - 12.5f * s, hw = (e->kind == K_CAPTAIN ? 6.5f : 5.0f) * s, hh = 1.8f * s;
    u32 halo = e->kind == K_CAPTAIN && e->hp > 1 ? RGBA(255, 225, 120, 255) : gold;
    if (e->kind == K_CAPTAIN && e->hp <= 1)
        halo = rgba_alpha(gold, 0.45f + 0.3f * sinf(G.t * 12));   /* cracked */
    mg_line(eye, x - hw, hy, x, hy - hh, 1.3f, d - 0.01f, halo);
    mg_line(eye, x, hy - hh, x + hw, hy, 1.3f, d - 0.01f, halo);
    mg_line(eye, x - hw, hy, x, hy + hh, 1.3f, d - 0.01f, halo);
    mg_line(eye, x, hy + hh, x + hw, hy, 1.3f, d - 0.01f, halo);
    if (e->kind == K_CAPTAIN)   /* gold trim on the commander's guard */
        mg_rect(eye, x - 1.5f * s, y - 1 * s, 3 * s, 7 * s, d - 0.006f, gold);
}

static void draw_enemies(int eye)
{
    for (int i = 0; i < G.ne; i++) {
        const Enemy *e = &G.e[i];
        if (!e->alive)
            continue;
        float d = depth_at(e->y), s = depth_scale(d);
        if (e->kind == K_SPIRIT)
            draw_spirit(eye, e->x, e->y, d, s, e->phase, e->row + G.wave, 0);
        else
            draw_angel(eye, e, d, s);
    }
}

static void draw_shots(int eye)
{
    for (int i = 0; i < MAXPS; i++) {
        const PShot *p = &G.ps[i];
        if (!p->alive)
            continue;
        float d = depth_at(p->y), s = depth_scale(d);
        mg_circle(eye, p->x, p->y + 3, 4.5f * s, d + 0.01f, RGBA(255, 230, 150, 70));
        mg_line(eye, p->x, p->y, p->x, p->y + 8 * s, 2.4f * s, d, RGBA(255, 250, 220, 255));
    }
    for (int i = 0; i < MAXES; i++) {
        const EShot *p = &G.es[i];
        if (!p->alive)
            continue;
        float d = depth_at(p->y), s = depth_scale(d);
        if (p->kind == S_WISP) {
            mg_circle(eye, p->x, p->y, 4.5f * s, d + 0.01f, RGBA(140, 230, 255, 60));
            mg_circle(eye, p->x, p->y, 2.4f * s, d, RGBA(210, 250, 255, 230));
        } else if (p->kind == S_BOLT) {
            mg_circle(eye, p->x, p->y, 5 * s, d + 0.01f, RGBA(255, 200, 80, 60));
            mg_tri(eye, p->x, p->y - 6 * s, p->x - 3 * s, p->y, p->x + 3 * s, p->y, d, RGBA(255, 215, 100, 255));
            mg_tri(eye, p->x - 3 * s, p->y, p->x + 3 * s, p->y, p->x, p->y + 6 * s, d, RGBA(255, 240, 180, 255));
        } else {
            float pulse = 0.8f + 0.2f * sinf(p->phase * 10);
            mg_circle(eye, p->x, p->y, 6.5f * s * pulse, d + 0.01f, RGBA(200, 150, 255, 70));
            mg_circle(eye, p->x, p->y, 3.4f * s, d, RGBA(245, 230, 255, 255));
        }
    }
    for (int i = 0; i < MAXM; i++) {
        const Minion *m = &G.m[i];
        if (!m->alive)
            continue;
        float d = depth_at(m->y), s = depth_scale(d) * 0.8f;
        draw_spirit(eye, m->x, m->y, d, s, m->phase, 1, 0);
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
    float x = G.bx, y = G.by, s = G.bscale, d = BOSS_D;
    bool down = G.st == ST_BOSS_DOWN;
    float sleep = down ? clampf((G.st_t - 1.5f) / 1.0f, 0, 1) : 0;

    /* the cape is a starfield: a hood behind the head and a cloak whose
     * scalloped hem drapes down to both sides */
    u32 rim = RGBA(110, 80, 190, 235), cape = RGBA(14, 10, 46, 250);
    float cw = (down ? lerpf(1.0f, 0.55f, sleep) : 1.0f) * s;
    float ax = x, ay = y + 4 * s;
    float hx[8], hy[8];
    for (int i = 0; i < 8; i++) {
        float u = i / 7.0f * 2 - 1;
        hx[i] = x + u * 138 * cw;
        hy[i] = y + (34 + 52 * (1 - u * u)) * s + sinf(G.t * 1.4f + i * 1.1f) * 4 * s + (i & 1) * 7 * s;
    }
    mg_circle(eye, x, y - 3 * s, 61 * s, d + 0.1f, rim);
    for (int i = 0; i < 7; i++)
        mg_tri(eye, ax, ay - 10 * s, hx[i] + (i == 0 ? -5 * s : 0), hy[i] + 4 * s, hx[i + 1] + (i == 6 ? 5 * s : 0),
               hy[i + 1] + 4 * s, d + 0.1f, rim);
    mg_circle(eye, x, y - 3 * s, 57 * s, d + 0.09f, cape);
    for (int i = 0; i < 7; i++)
        mg_tri(eye, ax, ay, hx[i], hy[i], hx[i + 1], hy[i + 1], d + 0.09f, cape);
    for (int i = 0; i < 18; i++) {   /* stars inside the cape */
        float u = (float)((i * 37 + 11) % 100) / 100.0f * 1.7f - 0.85f;
        float v = 0.3f + (float)((i * 61 + 7) % 100) / 100.0f * 0.6f;
        float sx = ax + u * 138 * cw * v, sy = ay + v * (34 + 52 * (1 - u * u)) * s;
        float tw = 0.5f + 0.5f * sinf(G.t * 2.0f + i * 1.3f);
        float sz = (i % 4 == 0 ? 2.2f : 1.3f) * (s < 0.5f ? 0.7f : 1.0f);
        mg_rect(eye, sx, sy, sz, sz, d + 0.08f, rgba_alpha(RGBA(230, 230, 255, 255), 0.4f + 0.6f * tw));
    }
    float gx = x + 78 * cw, gy = y + 48 * s;   /* a little galaxy on the hem */
    mg_circle(eye, gx, gy, 6 * s, d + 0.08f, RGBA(170, 140, 255, 80));
    mg_circle(eye, gx, gy, 2.2f * s, d + 0.08f, RGBA(255, 240, 255, 210));

    /* face: pale, round, childlike */
    u32 face = G.bhurt > 0 ? RGBA(255, 232, 238, 255) : RGBA(240, 236, 247, 255);
    mg_circle(eye, x, y, 46 * s, d, face);
    mg_circle(eye, x - 9 * s, y - 10 * s, 30 * s, d - 0.005f, RGBA(255, 255, 255, 50));
    mg_circle(eye, x - 28 * s, y + 12 * s, 7 * s, d - 0.01f, RGBA(255, 160, 185, 80));
    mg_circle(eye, x + 28 * s, y + 12 * s, 7 * s, d - 0.01f, RGBA(255, 160, 185, 80));
    /* a curl of stardust hair */
    mg_line(eye, x - 2 * s, y - 44 * s, x + 3 * s, y - 53 * s, 2.2f * s + 0.4f, d - 0.01f, face);
    mg_line(eye, x + 3 * s, y - 53 * s, x + 10 * s, y - 51 * s, 2.2f * s + 0.4f, d - 0.01f, face);
    /* little hands holding the cape closed */
    mg_circle(eye, x - 22 * s, y + 43 * s, 5.5f * s, d - 0.02f, RGBA(226, 220, 240, 255));
    mg_circle(eye, x + 22 * s, y + 43 * s, 5.5f * s, d - 0.02f, RGBA(226, 220, 240, 255));

    /* eyes: big, glossy and curious, following the ship */
    u32 ink = RGBA(30, 20, 52, 255);
    float lookx = clampf((G.sx - x) / 120.0f, -1, 1) * 3 * s, looky = 2.5f * s;
    bool blink = !down && fmodf(G.t, 4.3f) < 0.13f;
    float wide = G.pull_state ? 1.12f : 1.0f;
    for (int side = -1; side <= 1; side += 2) {
        float ex = x + side * 18 * s, ey = y - 5 * s;
        /* raised, curious brows */
        mg_line(eye, ex - 7 * s, ey - 16 * s - (side < 0) * 2 * s, ex + 6 * s, ey - 17 * s - (side > 0) * 2 * s,
                1.6f * s + 0.4f, d - 0.015f, RGBA(170, 150, 200, 255));
        if (sleep > 0.5f || blink) {
            mg_line(eye, ex - 8 * s, ey, ex, ey + 3 * s, 2.2f * s + 0.5f, d - 0.02f, ink);
            mg_line(eye, ex, ey + 3 * s, ex + 8 * s, ey, 2.2f * s + 0.5f, d - 0.02f, ink);
        } else {
            mg_circle(eye, ex, ey, 12 * s * wide, d - 0.02f, ink);
            mg_circle(eye, ex + lookx * 0.5f, ey + looky * 0.5f, 9.5f * s * wide, d - 0.025f, RGBA(112, 74, 196, 255));
            mg_circle(eye, ex + lookx, ey + looky, 5.5f * s, d - 0.03f, RGBA(16, 8, 36, 255));
            mg_circle(eye, ex - 3.5f * s, ey - 4.5f * s, 3.8f * s, d - 0.035f, MG_WHITE);
            mg_circle(eye, ex + 3.5f * s, ey + 3.5f * s, 1.6f * s, d - 0.035f, RGBA(220, 220, 255, 230));
        }
    }

    /* mouth: a small "o" that opens wide and pulls light in */
    float mx = x, my = y + 24 * s;
    if (down) {
        mg_line(eye, mx - 5 * s, my - 1 * s, mx, my + 2 * s, 1.6f, d - 0.02f, ink);
        mg_line(eye, mx, my + 2 * s, mx + 5 * s, my - 1 * s, 1.6f, d - 0.02f, ink);
    } else {
        float open = 4;
        if (G.pull_state == 1)
            open = lerpf(16, 6, clampf(G.pull_t / 0.9f, 0, 1));
        else if (G.pull_state == 2)
            open = 16 + sinf(G.t * 9) * 1.5f;
        else if (G.mouth_kick > 0)
            open = 4 + 7 * clampf(G.mouth_kick / 0.4f, 0, 1);
        if (open > 6)
            mg_circle(eye, mx, my, (open + 2) * s, d - 0.01f, RGBA(150, 100, 200, 180));
        mg_circle(eye, mx, my, open * s, d - 0.015f, RGBA(8, 4, 20, 255));
        if (G.pull_state == 2)
            for (int i = 0; i < 3; i++) {   /* swallowed light circling inside */
                float a = G.t * 7 + i * 2.094f, r = open * 0.55f * s;
                mg_circle(eye, mx + cosf(a) * r, my + sinf(a) * r, 1.6f * s, d - 0.02f, RGBA(255, 235, 200, 220));
            }
    }

    /* light pulled in: streaks flowing into the mouth */
    if (G.pull_state == 2 && !down) {
        for (int i = 0; i < 12; i++) {
            float a = i * 0.5236f + 0.2f;
            float ph = fmodf(G.t * 1.4f + i * 0.37f, 1.0f);
            float r0 = 20 + 190 * (1 - ph), r1 = r0 + 16 + 20 * (1 - ph);
            float x0 = mx + cosf(a) * r0, y0 = my + sinf(a) * r0 * 0.75f;
            float x1 = mx + cosf(a) * r1, y1 = my + sinf(a) * r1 * 0.75f;
            mg_line(eye, x0, y0, x1, y1, 1.6f, d - 0.05f, rgba_alpha(RGBA(255, 240, 210, 255), 0.25f + 0.6f * ph));
        }
        mg_line(eye, G.sx, G.sy - 8, mx, my, 1.0f, (SHIP_D + d) * 0.5f, RGBA(255, 220, 160, 70));
    }

    /* sleepy z's */
    if (sleep > 0)
        for (int i = 0; i < 3; i++) {
            float ph = fmodf(G.t * 0.5f + i * 0.33f, 1.0f);
            mg_text(eye, "z", x + 14 + ph * 22, y - 14 - ph * 40, 0.4f + 0.25f * ph, d - 0.08f - ph * 0.1f,
                    rgba_alpha(RGBA(220, 220, 255, 255), sleep * (1 - ph)));
        }
}

static void draw_hud(int eye)
{
    /* lives as little lanterns, top left */
    for (int i = 0; i < 3; i++) {
        u32 c = i < G.lives ? MG_GOLD : RGBA(255, 255, 255, 40);
        if (i == G.lives && G.life_lost_t > 0)
            c = rgba_alpha(MG_GOLD, G.life_lost_t / 0.35f);
        mg_rect(eye, 8 + i * 13, 8, 7, 9, -0.12f, c);
    }
    if (G.st == ST_BOSS || G.st == ST_BOSS_IN) {
        float f = (float)G.bhp / BOSS_HP;
        if (G.st == ST_BOSS_IN)
            f = clampf(G.st_t / 3.0f, 0, 1);
        mg_rect(eye, 100, 4, 200, 5, -0.12f, RGBA(255, 255, 255, 40));
        mg_rect(eye, 100, 4, 200 * f, 5, -0.12f, RGBA(220, 150, 255, 255));
    } else if (G.st < ST_BOSS_IN) {
        char buf[24];
        snprintf(buf, sizeof(buf), "Wave %d/3", G.wave + 1);
        mg_text(eye, buf, 340, 6, 0.4f, -0.12f, RGBA(220, 220, 255, 200));
    }
}

static void draw_banner(int eye)
{
    static const char *WAVE_NAMES[WAVES] = {
        "Lights of the Purgatorium",
        "Seraphiel's Corps",
        "The Sky Dives",
    };
    char buf[64];
    if (G.st == ST_WAVE_IN) {
        float a = clampf(G.st_t < 1.4f ? 1 : (1.8f - G.st_t) / 0.4f, 0, 1);
        snprintf(buf, sizeof(buf), "Wave %d", G.wave + 1);
        mg_text_centered(eye, buf, 200, 92, 0.9f, -0.3f, rgba_alpha(MG_GOLD, a));
        mg_text_centered(eye, WAVE_NAMES[G.wave], 200, 124, 0.55f, -0.2f, rgba_alpha(MG_WHITE, a));
    } else if (G.st == ST_CLEAR) {
        mg_text_centered(eye, "Sky cleared", 200, 92, 0.8f, -0.3f, MG_GOLD);
        if (G.wave + 1 >= WAVES && G.st_t > 0.9f)
            mg_text_centered(eye, "Something hungry is coming...", 200, 124, 0.5f, -0.2f, RGBA(220, 190, 255, 255));
    } else if (G.st == ST_BOSS_IN && G.st_t < 2.6f) {
        mg_text_centered(eye, "Lord Ashveil", 200, 150, 0.8f, -0.3f, RGBA(230, 210, 255, 255));
        mg_text_centered(eye, "hungry, not evil", 200, 178, 0.45f, -0.2f, RGBA(200, 190, 230, 255));
    } else if (G.st == ST_BOSS && G.pull_state == 1) {
        mg_text_centered(eye, "He's pulling - hold Down!", 200, 168, 0.5f, -0.3f, RGBA(255, 210, 230, 255));
    } else if (G.st == ST_BOSS_DOWN && G.st_t > 2.6f) {
        mg_text_centered(eye, "Sated. Sleepy. Quiet.", 200, 170, 0.6f, -0.25f, MG_GOLD);
    } else if (G.st == ST_OVER) {
        mg_text_centered(eye, "The lantern goes out", 200, 100, 0.7f, -0.25f, RGBA(255, 200, 180, 255));
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
        mg_line(eye, G.flash_x + c * r * 0.55f, G.flash_y + sn * r * 0.55f, G.flash_x + c * r,
                G.flash_y + sn * r, 3, -0.15f, rgba_alpha(RGBA(255, 240, 190, 255), f));
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
    if (G.st >= ST_BOSS_IN && G.st != ST_OVER)
        draw_boss(eye);
    else if (G.st == ST_OVER && G.reached_boss)
        draw_boss(eye);
    draw_enemies(eye);
    draw_shots(eye);
    draw_particles(eye);
    draw_ship(eye);
    draw_hud(eye);
    draw_banner(eye);
    draw_flash(eye);
#ifdef INV_DEBUG
    if (dc > dc_max) {
        dc_max = dc;
        printf("invaders: %d draw calls (state %d)\n", dc, G.st);
    }
#endif
}

/* ---- bottom screen ------------------------------------------------------- */

static void draw_bottom(void)
{
    char buf[64];
    gfx_text("The Hungry Sky", 14, 8, 0.55f, MG_GOLD);

    gfx_text("Lives", 14, 40, 0.45f, RGBA(200, 200, 230, 255));
    for (int i = 0; i < 3; i++) {
        bool on = i < G.lives;
        float x = 70 + i * 24;
        gfx_circle(x + 6, 48, 9, on ? RGBA(255, 210, 120, 60) : RGBA(0, 0, 0, 0));
        gfx_rect(x, 40, 12, 16, on ? RGBA(200, 140, 60, 255) : RGBA(255, 255, 255, 30));
        gfx_rect(x + 2.5f, 43, 7, 10, on ? RGBA(255, 238, 180, 255) : RGBA(255, 255, 255, 20));
    }

    if (G.st >= ST_BOSS_IN && G.reached_boss) {
        gfx_text("Lord Ashveil", 14, 70, 0.45f, RGBA(220, 200, 255, 255));
        float f = G.st == ST_BOSS_IN ? clampf(G.st_t / 3.0f, 0, 1) : (float)G.bhp / BOSS_HP;
        gfx_rect(110, 72, 196, 12, RGBA(255, 255, 255, 40));
        gfx_rect(110, 72, 196 * f, 12, RGBA(200, 140, 255, 255));
        if (G.boss_beaten)
            snprintf(buf, sizeof(buf), "Asleep, full of light");
        else
            snprintf(buf, sizeof(buf), "Phase %d of 3", G.bphase ? G.bphase : 1);
        gfx_text(buf, 14, 90, 0.42f, RGBA(200, 200, 230, 255));
    } else {
        snprintf(buf, sizeof(buf), "Wave %d of 3", G.wave + 1);
        gfx_text(buf, 14, 70, 0.45f, RGBA(200, 200, 230, 255));
        int alive = alive_count();
        snprintf(buf, sizeof(buf), "%d left", alive);
        gfx_text(buf, 120, 70, 0.45f, MG_WHITE);
    }

    snprintf(buf, sizeof(buf), "Score %d", G.points);
    gfx_text(buf, 14, 112, 0.55f, MG_WHITE);
    snprintf(buf, sizeof(buf), "Accuracy %d%%", G.shots ? G.hits * 100 / G.shots : 0);
    gfx_text(buf, 170, 116, 0.42f, RGBA(200, 200, 230, 255));

    gfx_rect(10, 140, 300, 1, RGBA(255, 255, 255, 40));
    gfx_text("D-pad / Circle Pad: move", 14, 146, 0.42f, RGBA(200, 200, 230, 255));
    gfx_text("A: shoot (hold to auto-fire)", 14, 162, 0.42f, RGBA(200, 200, 230, 255));
    gfx_text("Down: resist Ashveil's pull", 14, 178, 0.42f, RGBA(200, 200, 230, 255));
    gfx_text("START: pause", 14, 212, 0.42f, RGBA(160, 160, 190, 255));
}

/* ---- results ------------------------------------------------------------- */

static int score(void)
{
    float acc = G.shots ? (float)G.hits / G.shots : 0;
    float s = 30.0f * G.kills / G.total_regular + 15.0f * clampf(acc / 0.8f, 0, 1);
    if (G.boss_beaten) {
        float tb = clampf((300.0f - G.end_t) / 180.0f, 0, 1);
        s += 30.0f + 15.0f * G.lives / 3.0f + 10.0f * tb;
    } else if (G.reached_boss) {
        s += 15.0f * G.boss_dmg_frac;
    }
    int v = (int)(s + 0.5f);
#ifdef INV_DEBUG
    printf("invaders: kills %d/%d acc %.2f lives %d hits taken %d t %.1f boss %d\n", G.kills, G.total_regular, acc,
           G.lives, G.hits_taken, G.end_t, G.boss_beaten);
#endif
    return v < 0 ? 0 : v > 100 ? 100 : v;
}

static const char *verdict(void)
{
    if (G.boss_beaten && G.hits_taken == 0)
        return "Ashveil sleeps, full of light. Not a scratch.";
    if (G.boss_beaten)
        return "Lord Ashveil curls up, sated and sleepy.";
    if (G.reached_boss)
        return "The hungry sky is still hungry.";
    return "The formation held. The sky stays dark.";
}

/* The cheat only helps while there is something to fight. */
static bool can_cheat(void)
{
    return G.st == ST_WAVE_IN || G.st == ST_WAVE || G.st == ST_BOSS_IN || G.st == ST_BOSS;
}

/* ---- bot ----------------------------------------------------------------- */

static void bot(Input *in, float t)
{
    static float last_t;
    static bool cheated;
    if (t < last_t)
        cheated = false;
    last_t = t;

    /* fire (the host copies down into held) only with something above */
    bool aligned = G.st >= ST_BOSS_IN && fabsf(G.bx - G.sx) < 36;
    for (int i = 0; i < G.ne; i++) {
        const Enemy *e = &G.e[i];
        float lead = e->state == E_FORM ? G.fvel * (G.sy - e->y) / 360.0f : e->vx * 0.2f;
        if (e->alive && e->y < G.sy && fabsf(e->x + lead - G.sx) < 7)
            aligned = true;
    }
    for (int i = 0; i < MAXM; i++)
        if (G.m[i].alive && G.m[i].y < G.sy && fabsf(G.m[i].x - G.sx) < 7)
            aligned = true;
    if (aligned)
        in->down |= KEY_A_;

    /* pick a target: the lowest enemy, preferring ones near the ship */
    float tx = 200;
    float best = 1e9f;
    for (int i = 0; i < G.ne; i++) {
        const Enemy *e = &G.e[i];
        if (!e->alive)
            continue;
        float px = e->x + (e->state == E_FORM ? G.fvel * (G.sy - e->y) / 360.0f : 0);
        float c = fabsf(px - G.sx) - e->y * 0.6f - (e->state == E_DIVE ? 200 : 0);
        if (c < best)
            best = c, tx = px;
    }
    if (G.st >= ST_BOSS_IN)
        tx = G.bx;
    for (int i = 0; i < MAXM; i++)
        if (G.m[i].alive && G.m[i].y > 100)
            tx = G.m[i].x;

    float mx = clampf((tx - G.sx) / 18.0f, -1, 1);

    /* dodge: score a few spots around the ship by how close the threats
     * will pass, and head for the safest one nearest the target */
    float bestx = G.sx, bestc = 1e9f, here = 0;
    for (int k = -6; k <= 6; k++) {
        float cxp = clampf(G.sx + k * 8.0f, 14, TOP_W - 14), dng = 0;
        /* sample the way there too: running through a shot is no dodge */
        for (int step = 1; step <= 3; step++) {
            float px = lerpf(G.sx, cxp, step / 3.0f);
            for (int i = 0; i < MAXES; i++) {
                const EShot *s = &G.es[i];
                if (!s->alive || s->y > G.sy + 8 || s->y < G.sy - 110)
                    continue;
                float tt = (G.sy - s->y) / (s->vy > 10 ? s->vy : 10);
                float fut = s->x + s->vx * tt;
                dng += fmaxf(0, 20 - fabsf(fut - px)) * fmaxf(0.3f, 2.0f - tt);
            }
            for (int i = 0; i < G.ne; i++) {
                const Enemy *e = &G.e[i];
                if (e->alive && e->state == E_DIVE && e->y > G.sy - 100)
                    dng += fmaxf(0, 30 - fabsf(e->x - px)) * 2;
            }
            for (int i = 0; i < MAXM; i++) {
                const Minion *m = &G.m[i];
                if (m->alive && m->y > G.sy - 50)
                    dng += fmaxf(0, 22 - fabsf(m->x - px)) * 2;
            }
            if (k == 0)
                break;
        }
        if (k == 0)
            here = dng;
        else
            dng /= 3;
        float c = dng * 10 + fabsf(cxp - tx) * 0.3f + abs(k) * 0.5f;
        if (c < bestc)
            bestc = c, bestx = cxp;
    }
#ifdef INV_DEBUG
    if (here > 0)
        printf("bot t %.2f sx %.0f bestx %.0f here %.0f\n", t, G.sx, bestx, here);
#endif
    (void)here;
    mx = clampf((bestx - G.sx) / 6.0f, -1, 1);
    in->cx = mx;
    in->cy = -1;   /* stay low (and resist the pull) */

    /* spend the cheat once the boss is fighting */
    if (!cheated && G.st == ST_BOSS && G.bhp < BOSS_HP * 0.85f) {
        in->down |= KEY_L_;
        cheated = true;
    }
}

const MiniGame MG_INVADERS = {
    .id = "invaders",
    .title = "The Hungry Sky",
    .rules = "Spirits and Seraphiel's angels fill the sky.\n"
             "Clear 3 waves, then face Lord Ashveil,\n"
             "who is hungry, not evil. Dodge golden bolts,\n"
             "diving angels, his light and his spirits.\n"
             "When his mouth opens he pulls you in:\n"
             "hold Down, and shoot into his open mouth\n"
             "for double damage. You have 3 lives.\n"
             "Score: kills, accuracy, lives and time.",
    .controls = "D-pad / Circle Pad: move the lantern\n"
                "  (left and right, a little up and down)\n"
                "A: shoot    Hold A: auto-fire\n"
                "Down: resist Ashveil's pull\n"
                "START: pause",
    .cheat = "Golden light clears all enemies\nand shots, or burns 35% off the boss",
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
