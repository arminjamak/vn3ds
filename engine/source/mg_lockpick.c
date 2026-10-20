/* Lockpick (a ported mechanic, see minigame.h): turn the pick to the hidden
 * sweet spot, then apply tension to turn the cylinder. Away from the spot
 * the cylinder only turns part of the way and jams; holding tension on a
 * jammed lock wears the pick down until it snaps. Each pick is an attempt.
 *
 * Rules follow the original screen, tick for tick (60 ticks a second):
 *   pick angle 0..180 (90 = straight up), sweet spot random in 0..180;
 *   the cylinder turns 1 degree a tick towards its limit while tensioned,
 *   1.5 back when released; its limit is 90 (open) within `sweet_angle` of
 *   the spot, else 90 - distance * (30 / sweet_angle), at least 0;
 *   jammed at the limit, the pick loses `pick_dmg` of 100 health a tick;
 *   a broken pick is replaced after 0.5 s (one attempt fewer; none left
 *   fails); the lock opens 0.5 s after the cylinder reaches 90.
 *
 * Parameters (PORT entry): sweet_angle, pick_dmg, attempts; resize (the
 * size the original drew the square lock art at, in the story's virtual
 * pixels; default: the game's width); result = the variable that gets
 * True / False (default _return); images plate, cylinder, tension, pick,
 * pick_broken (image names) with box_<name> = "x0 y0 x1 y1 W H": the part
 * of the W x H original picture the packed image holds. Sounds: unlock,
 * pick_break (one-shot) and loop_moving, loop_jiggling, loop_moving_back.
 *
 * Controls: D-pad / Circle Pad left and right move the pick, hold A to turn
 * the cylinder. Touch: hold the big arrows to move the pick, hold Turn. */

#include "minigame.h"

#define TICK (1.0f / 60.0f)
#define CYL_TARGET 90.0f
#define PICK_MAX 180.0f
#define SWEET_MAX 30.0f
#define MOVE_SPEED 1.0f
#define RESET_SPEED 1.5f
#define BROKEN_DELAY 0.5f
#define OPENED_DELAY 0.5f

/* Bottom screen buttons. */
#define BTN_Y 92
#define BTN_H 104
#define LEFT_X 6
#define LEFT_W 90
#define TURN_X 102
#define TURN_W 116
#define RIGHT_X 224
#define RIGHT_W 90

enum { IMG_PLATE, IMG_CYL, IMG_TENSION, IMG_PICK, IMG_BROKEN, NIMG };
static const char *const IMG_KEY[NIMG] = {"plate", "cylinder", "tension", "pick", "pick_broken"};

typedef struct {
    GfxTex *tex;
    float w, h;          /* drawn size, top-screen px */
    float cx, cy;        /* centre in lock space (the original's px) */
} Piece;

static struct {
    float sweet_angle, pick_dmg;
    int attempts_left;
    float sweet_spot;
    float cyl_pos, cyl_max;
    bool try_rotate, can_rotate, released;
    float pick_pos;
    bool pick_can_rotate, pick_broke, disabled;
    float health;
    float jiggle1, jiggle2;     /* this tick's shake of cylinder and tension, degrees */
    float repair_t, open_t;     /* countdowns, -1 = not running */
    bool done, opened;
    bool want_prev;             /* A or Turn held last tick */
    float hold_t;               /* how long the pick has been pushed one way */
    float acc;                  /* time not yet run as ticks */
    const char *loop;           /* the clip on the looping sound channel, or NULL */
    float t;
    /* layout */
    Piece pc[NIMG];
    float R;                    /* lock square in the story's virtual px */
    float ox, oy, k;            /* lock space -> top screen: x = ox + lx * k */
    const char *result_var;
    float fade_in;              /* the screen's transition, seconds */
    /* touch, for the bottom screen */
    int touch_dir;
    bool touch_turn;
} L;

static void loop_play(const char *clip)
{
    L.loop = clip;
    mg_sound_loop(clip);
}

static void loop_stop(void)
{
    if (L.loop)
        mg_sound_loop(NULL);
    L.loop = NULL;
}

static void load_piece(int i)
{
    Piece *p = &L.pc[i];
    char key[32];
    float w = 0, h = 0;
    const char *name = mg_param(IMG_KEY[i]);
    p->tex = mg_image(name, &w, &h);
    snprintf(key, sizeof(key), "box_%s", IMG_KEY[i]);
    float x0 = 0, y0 = 0, x1 = L.R, y1 = L.R, W = L.R, H = L.R;
    const char *box = mg_param(key);
    if (box)
        sscanf(box, "%f %f %f %f %f %f", &x0, &y0, &x1, &y1, &W, &H);
    if (W <= 0)
        W = L.R;
    if (H <= 0)
        H = L.R;
    /* the original stretched each W x H picture over the R x R square */
    float sx = L.R / W, sy = L.R / H;
    p->cx = (x0 + x1) / 2 * sx;
    p->cy = (y0 + y1) / 2 * sy;
    p->w = (x1 - x0) * sx * L.k;
    p->h = (y1 - y0) * sy * L.k;
}

static void start(u32 seed)
{
    (void)seed;
    memset(&L, 0, sizeof(L));
    L.sweet_angle = clampf(mg_paramf("sweet_angle", 10), 1, SWEET_MAX);
    L.pick_dmg = mg_paramf("pick_dmg", 1.5f);
    L.attempts_left = (int)mg_paramf("attempts", 3);
    if (L.attempts_left < 1)
        L.attempts_left = 1;
    L.result_var = mg_param("result") ? mg_param("result") : "_return";
    L.fade_in = mg_paramf("fade_in", 0);
    L.sweet_spot = (float)mg_randi(0, (int)PICK_MAX);
    L.pick_pos = 90;
    L.pick_can_rotate = true;
    L.health = 100;
    L.repair_t = L.open_t = -1;
    L.want_prev = true;   /* a press already held when the game opens does not count */
    /* The original centred the R x R lock on the virtual screen; keep its
     * framing, at the story's scale, on the top screen. */
    const Game *g = &E.game;
    float gw = g->game_w ? g->game_w : 1280, gh = g->game_h ? g->game_h : 720;
    L.R = mg_paramf("resize", gw);
    L.k = g->scale > 0 ? g->scale : TOP_W / gw;
    L.ox = g->view_x + (gw - L.R) / 2 * L.k;
    L.oy = g->view_y + (gh - L.R) / 2 * L.k;
    for (int i = 0; i < NIMG; i++)
        load_piece(i);
}

/* Released: the cylinder springs back (also the original's mouse-up). */
static void release(void)
{
    loop_stop();
    L.try_rotate = false;
    L.released = true;
    L.pick_can_rotate = true;
    L.pick_broke = false;
}

static void disable(void)
{
    L.pick_can_rotate = false;
    L.can_rotate = false;
    L.try_rotate = false;
    L.disabled = true;
}

static void tick(float pick_delta, bool want)
{
    /* timers (the original's pygame events) */
    if (L.open_t >= 0 && (L.open_t -= TICK) < 0) {
        L.done = L.opened = true;
        return;
    }
    if (L.repair_t >= 0 && (L.repair_t -= TICK) < 0) {
        L.pick_broke = false;
        L.pick_can_rotate = true;
        L.disabled = false;
        L.released = true;
        L.attempts_left--;
        L.health = 100;
        if (L.attempts_left <= 0) {
            L.done = true;
            return;
        }
    }
    /* press and release */
    if (!L.disabled) {
        if (want && !L.want_prev) {
            L.try_rotate = true;
            L.released = false;
        } else if (!want && L.want_prev) {
            release();
        }
    }
    L.want_prev = want;

    if (L.pick_can_rotate && !L.disabled) {
        L.pick_pos = clampf(L.pick_pos + pick_delta, 0, PICK_MAX);
        L.can_rotate = true;
        float off = fabsf(L.pick_pos - L.sweet_spot);
        L.cyl_max = off < L.sweet_angle ? CYL_TARGET : CYL_TARGET - off * (SWEET_MAX / L.sweet_angle);
        if (L.cyl_max < 0)
            L.cyl_max = 0;
    }
    L.jiggle1 = L.jiggle2 = 0;
    if (L.try_rotate && !L.disabled) {
        if (L.can_rotate) {
            L.cyl_pos += MOVE_SPEED;
            if (L.cyl_pos > L.cyl_max) {
                L.cyl_pos = L.cyl_max;
                if (L.cyl_pos == CYL_TARGET) {
                    loop_stop();
                    mg_sfx("unlock");
                    disable();
                    L.open_t = OPENED_DELAY;
                } else {   /* jammed */
                    L.pick_can_rotate = false;
                    if (!L.loop)
                        loop_play("jiggling");
                    L.jiggle1 = (float)mg_randi(-2, 2);
                    L.jiggle2 = (float)mg_randi(-4, 4);
                    L.health -= L.pick_dmg;
                    if (L.health < 0) {
                        loop_stop();
                        mg_sfx("pick_break");
                        L.pick_broke = true;
                        disable();
                        L.repair_t = BROKEN_DELAY;
                    }
                }
            } else if (!L.loop) {
                loop_play("moving");
            }
        }
    } else if (L.released) {
        if (L.cyl_pos > 15 && !L.loop)
            loop_play("moving_back");
        L.pick_can_rotate = true;
        L.cyl_pos -= RESET_SPEED;
        if (L.cyl_pos < 0) {
            L.cyl_pos = 0;
            L.released = false;
            loop_stop();
        }
    }
}

static bool in_box(const Input *in, float x, float y, float w, float h)
{
    return in->tx >= x && in->tx < x + w && in->ty >= y && in->ty < y + h;
}

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    L.t += dt;
    bool touching = (in->held & KEY_TOUCH_) != 0;
    L.touch_dir = 0;
    L.touch_turn = false;
    if (touching) {
        if (in_box(in, LEFT_X, BTN_Y, LEFT_W, BTN_H))
            L.touch_dir = -1;
        else if (in_box(in, RIGHT_X, BTN_Y, RIGHT_W, BTN_H))
            L.touch_dir = 1;
        else if (in_box(in, TURN_X, BTN_Y, TURN_W, BTN_H))
            L.touch_turn = true;
    }
    /* pick speed in degrees a second: a tap nudges, holding speeds up */
    float dir = 0;
    if ((in->held & KEY_LEFT_) || L.touch_dir < 0)
        dir = -1;
    else if ((in->held & KEY_RIGHT_) || L.touch_dir > 0)
        dir = 1;
    float speed = 0;
    if (dir != 0) {
        L.hold_t += dt;
        speed = dir * (L.hold_t < 0.4f ? 24.0f : fminf(24.0f + (L.hold_t - 0.4f) * 120.0f, 110.0f));
    } else {
        L.hold_t = 0;
        if (fabsf(in->cx) > 0.15f)   /* the Circle Pad: proportional */
            speed = in->cx * fabsf(in->cx) * 110.0f;
    }
    float nudge = 0;
    if (in->down & KEY_LEFT_)
        nudge = -1;
    else if (in->down & KEY_RIGHT_)
        nudge = 1;
    bool want = (in->held & KEY_A_) || L.touch_turn;
    L.acc += dt;
    bool first = true;
    while (L.acc >= TICK && !L.done) {
        L.acc -= TICK;
        tick(speed * TICK + (first ? nudge : 0), want);
        first = false;
    }
    if (L.done) {
        loop_stop();
        mg_var_set_bool(L.result_var, L.opened);
        return false;
    }
    return true;
}

/* ---- drawing ------------------------------------------------------------- */

static void draw_piece(int eye, const Piece *p, float deg, float depth)
{
    if (!p->tex)
        return;
    /* rotate about the lock's centre (the keyhole) */
    float a = deg * (float)M_PI / 180.0f, c = cosf(a), s = sinf(a);
    float px = L.R / 2, py = L.R / 2, dx = p->cx - px, dy = p->cy - py;
    float cx = px + c * dx - s * dy, cy = py + s * dx + c * dy;
    float sx = L.ox + cx * L.k + mg_shift(eye, depth), sy = L.oy + cy * L.k;
    float fade = L.fade_in > 0 ? clampf(L.t / L.fade_in, 0, 1) : 1;
    gfx_image(p->tex, sx - p->w / 2, sy - p->h / 2, p->w, p->h, a, fade);
}

static void draw_top(int eye)
{
    render_scene(eye);   /* the story's scene, as behind the original screen */
    draw_piece(eye, &L.pc[IMG_PLATE], 0, 0.1f);
    draw_piece(eye, &L.pc[IMG_CYL], L.cyl_pos + L.jiggle1, 0.05f);
    draw_piece(eye, &L.pc[IMG_TENSION], L.cyl_pos + L.jiggle2, -0.05f);
    draw_piece(eye, &L.pc[L.pick_broke && L.pc[IMG_BROKEN].tex ? IMG_BROKEN : IMG_PICK], L.pick_pos,
               -0.15f);
    char buf[48];
    snprintf(buf, sizeof(buf), "Attempts: %d", L.attempts_left);
    float w = gfx_text_width(buf, 0.6f) + 20;
    ui_rrect(TOP_W / 2 - w / 2 + mg_shift(eye, -0.25f), 8, w, 26, 13, RGBA(0, 0, 0, 150));
    mg_text_centered(eye, buf, TOP_W / 2, 11, 0.6f, -0.25f, MG_WHITE);
}

static void button(float x, float y, float w, float h, bool on)
{
    ui_rrect(x, y, w, h, 14, on ? RGBA(255, 255, 255, 235) : RGBA(52, 52, 56, 255));
}

static void arrow(float cx, float cy, float dir, bool on)
{
    u32 c = on ? RGBA(0, 0, 0, 255) : MG_WHITE;
    gfx_triangle(cx + dir * 18, cy, cx - dir * 14, cy - 22, cx - dir * 14, cy + 22, c);
}

static void draw_bottom(void)
{
    const u32 dim = RGBA(152, 152, 159, 255);
    gfx_text("Pick the lock", 12, 10, 0.6f, MG_WHITE);
    char buf[48];
    snprintf(buf, sizeof(buf), "Attempts: %d", L.attempts_left);
    gfx_text(buf, BOT_W - 12 - gfx_text_width(buf, 0.5f), 12, 0.5f, MG_GOLD);
    /* pick health */
    gfx_rect(12, 40, 296, 8, RGBA(40, 40, 44, 255));
    gfx_rect(12, 40, 296 * clampf(L.health / 100, 0, 1), 8,
             L.health > 35 ? RGBA(200, 200, 210, 255) : RGBA(230, 90, 70, 255));
    gfx_text("Find the spot where the cylinder turns all\nthe way. Don't force it: the pick wears out.",
             12, 54, 0.42f, dim);
    bool left = L.touch_dir < 0, right = L.touch_dir > 0, turn = L.touch_turn || L.try_rotate;
    button(LEFT_X, BTN_Y, LEFT_W, BTN_H, left);
    arrow(LEFT_X + LEFT_W / 2, BTN_Y + BTN_H / 2, -1, left);
    button(RIGHT_X, BTN_Y, RIGHT_W, BTN_H, right);
    arrow(RIGHT_X + RIGHT_W / 2, BTN_Y + BTN_H / 2, 1, right);
    button(TURN_X, BTN_Y, TURN_W, BTN_H, turn);
    const char *t = "Turn";
    gfx_text(t, TURN_X + (TURN_W - gfx_text_width(t, 0.7f)) / 2, BTN_Y + 30, 0.7f,
             turn ? RGBA(0, 0, 0, 255) : MG_WHITE);
    t = "(hold)";
    gfx_text(t, TURN_X + (TURN_W - gfx_text_width(t, 0.45f)) / 2, BTN_Y + 62, 0.45f,
             turn ? RGBA(60, 60, 60, 255) : dim);
    gfx_text("D-pad / Circle Pad: move the pick\nHold A: turn the cylinder", 12, 204, 0.42f, dim);
}

static int score(void) { return L.opened ? 100 : 0; }

/* Finds the spot the way a player would: probe every few degrees, testing
 * how far the cylinder turns before it jams, then search around the best
 * probe in shrinking steps. */
static void bot(Input *in, float t)
{
    static float last = 1e9f, best_pos, best_turn, step, target, coarse, phase_t;
    static int phase, tried, beat;   /* phase 0: move the pick, 1: turn, 2: let go */
    if (t < last) {
        best_turn = -1;
        coarse = target = 4;
        step = 4;
        phase = tried = 0;
    }
    last = t;
    if (L.disabled) {
        phase = 0;
        return;
    }
    float d = target - L.pick_pos;
    switch (phase) {
    case 0:
        if (fabsf(d) > 3) {
            in->held |= d > 0 ? KEY_RIGHT_ : KEY_LEFT_;
        } else if (fabsf(d) > 1) {
            if (++beat % 4 == 0)
                in->down |= d > 0 ? KEY_RIGHT_ : KEY_LEFT_;
        } else {
            phase = 1;
            phase_t = t;
        }
        break;
    case 1:
        in->held |= KEY_A_;
        if (t - phase_t > 0.1f && !L.pick_can_rotate) {   /* jammed: how far did it turn? */
            float m = L.cyl_pos, p = L.pick_pos;
            if (m > best_turn + 0.01f) {
                best_turn = m;
                best_pos = p;
                tried = 0;
            } else {
                tried++;
            }
            if (best_turn <= 0) {
                coarse += 8;
                if (coarse > PICK_MAX)
                    coarse = 4;
                target = coarse;
            } else {
                if (tried >= 2) {
                    step = fmaxf(step * 0.5f, 1.0f);
                    tried = 0;
                }
                target = clampf(best_pos + (tried == 0 ? step : -step), 0, PICK_MAX);
            }
            phase = 2;
        }
        break;
    default:
        if (L.cyl_pos <= 0)
            phase = 0;
        break;
    }
}

const MiniGame MG_LOCKPICK = {
    .id = "lockpick",
    .title = "Lockpick",
    .rules = "Find the sweet spot with the pick, then turn.",
    .controls = "D-pad / Circle Pad: move the pick\nA (hold): turn the cylinder\nSTART: pause",
    .cheat = "",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .bot = bot,
};
