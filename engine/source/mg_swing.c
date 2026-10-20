/* Swing timing (a ported mechanic, see minigame.h): a marker swings to and
 * fro along an arc; press once to stop it. Inside the window around the
 * middle of the arc adds a point to the score variable, outside takes one.
 *
 * As the original screen: the rotation runs from -90 to 90 degrees and back,
 * `speed` degrees a tick (60 ticks a second) while the variable `speed_if`
 * is true, else `speed_alt`; a hit is |rotation| <= `window`. The rotation
 * and direction start from, and are written back to, the variables
 * `rotation_var` and `clockwise_var` (the original kept them in the store).
 *
 * Parameters (PORT entry): window, speed, speed_alt, speed_if, score (the
 * variable), hit, miss (what a hit / miss adds, default 1 / -1),
 * rotation_var, clockwise_var; layout in the story's virtual px: box
 * "x y w h" (the arc's frame), center "x y" (inside the box), radius,
 * angle_offset (degrees added to the rotation; 0 points up, clockwise
 * positive); images bar (fills the box) and ball, ball_size "w h".
 *
 * fade_in: seconds of the screen's transition, when it can't be pressed yet.
 *
 * Controls: A (or B, X, Y) or a tap anywhere on the touch screen. */

#include "minigame.h"

#define TICK (1.0f / 60.0f)

static struct {
    float rot, speed, window;
    bool clockwise, pressed, hit;
    float acc, t, end_t, fade_in;
    const char *score_var;
    GfxTex *bar, *ball;
    float bx, by, bw, bh;      /* the frame, virtual px */
    float cx, cy, radius, offset, ball_w, ball_h;
} W;

static void start(u32 seed)
{
    (void)seed;
    memset(&W, 0, sizeof(W));
    W.window = mg_paramf("window", 10);
    W.fade_in = mg_paramf("fade_in", 0);
    const char *cond = mg_param("speed_if");
    bool fast = cond && *cond ? mg_var_num(cond, 0) != 0 : true;
    W.speed = fast ? mg_paramf("speed", 3.1f) : mg_paramf("speed_alt", mg_paramf("speed", 3.1f));
    W.score_var = mg_param("score") ? mg_param("score") : "score";
    W.rot = clampf((float)mg_var_num(mg_param("rotation_var"), 0), -90, 90);
    W.clockwise = mg_var_num(mg_param("clockwise_var"), 1) != 0;
    float tw, th;
    W.bar = mg_image(mg_param("bar"), &tw, &th);
    W.ball = mg_image(mg_param("ball"), &tw, &th);
    const Game *g = &E.game;
    W.bw = 350;
    W.bh = 700;
    W.bx = (g->game_w - W.bw) * 0.21f;
    W.by = (g->game_h - W.bh) * 0.5f;
    const char *v;
    if ((v = mg_param("box")))
        sscanf(v, "%f %f %f %f", &W.bx, &W.by, &W.bw, &W.bh);
    W.cx = W.bw;
    W.cy = W.bh / 2;
    if ((v = mg_param("center")))
        sscanf(v, "%f %f", &W.cx, &W.cy);
    W.radius = mg_paramf("radius", W.bw - 13);
    W.offset = mg_paramf("angle_offset", -90);
    W.ball_w = W.ball_h = 24;
    if ((v = mg_param("ball_size")))
        sscanf(v, "%f %f", &W.ball_w, &W.ball_h);
}

static void tick(void)
{
    if (W.clockwise) {
        if (W.rot < 90)
            W.rot += W.speed;
        else
            W.clockwise = false;
    } else {
        if (W.rot > -90)
            W.rot -= W.speed;
        else
            W.clockwise = true;
    }
    W.rot = clampf(W.rot, -90, 90);
}

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    W.t += dt;
    if (W.pressed) {   /* a moment to see where it stopped */
        return W.t < W.end_t;
    }
    /* While the screen's transition plays it can't be pressed yet (the
     * marker already swings, as in the original). */
    if (W.t >= W.fade_in && (in->down & (KEY_A_ | KEY_B_ | KEY_X_ | KEY_Y_ | KEY_TOUCH_))) {
        W.pressed = true;
        W.hit = W.rot >= -W.window && W.rot <= W.window;
        double s = mg_var_num(W.score_var, 0);
        mg_var_set_num(W.score_var, s + (W.hit ? mg_paramf("hit", 1) : mg_paramf("miss", -1)));
        mg_var_set_num(mg_param("rotation_var"), W.rot);
        mg_var_set_bool(mg_param("clockwise_var"), W.clockwise);
        W.end_t = W.t + 0.35f;
        return true;
    }
    W.acc += dt;
    while (W.acc >= TICK) {
        W.acc -= TICK;
        tick();
    }
    return true;
}

static void to_screen(float vx, float vy, float *sx, float *sy)
{
    const Game *g = &E.game;
    *sx = g->view_x + vx * g->scale;
    *sy = g->view_y + vy * g->scale;
}

static void draw_top(int eye)
{
    render_scene(eye);
    const Game *g = &E.game;
    float x, y, fade = W.fade_in > 0 ? clampf(W.t / W.fade_in, 0, 1) : 1;
    to_screen(W.bx, W.by, &x, &y);
    if (W.bar)
        gfx_image(W.bar, x + mg_shift(eye, -0.12f), y, W.bw * g->scale, W.bh * g->scale, 0, fade);
    float a = (W.rot + W.offset) * (float)M_PI / 180.0f;
    float px = W.bx + W.cx + W.radius * sinf(a), py = W.by + W.cy - W.radius * cosf(a);
    to_screen(px, py, &x, &y);
    float w = W.ball_w * g->scale, h = W.ball_h * g->scale;
    if (W.pressed)
        mg_circle(eye, x, y, w * 0.9f, -0.22f, W.hit ? RGBA(120, 255, 160, 110) : RGBA(255, 90, 80, 110));
    if (W.ball)
        gfx_image(W.ball, x - w / 2 + mg_shift(eye, -0.22f), y - h / 2, w, h, 0, fade);
    else
        mg_circle(eye, x, y, w / 2, -0.22f, RGBA(80, 255, 200, 255));
}

static void draw_bottom(void)
{
    const u32 dim = RGBA(152, 152, 159, 255);
    bool on = W.pressed;
    ui_rrect(16, 40, 288, 150, 24, on ? RGBA(255, 255, 255, 235) : RGBA(52, 52, 56, 255));
    const char *t = "Release!";
    gfx_text(t, 160 - gfx_text_width(t, 0.9f) / 2, 92, 0.9f, on ? RGBA(0, 0, 0, 255) : MG_WHITE);
    gfx_text("Stop the light on the green mark.", 160 - gfx_text_width("Stop the light on the green mark.", 0.45f) / 2,
             12, 0.45f, dim);
    gfx_text("A, or tap anywhere", 160 - gfx_text_width("A, or tap anywhere", 0.45f) / 2, 206, 0.45f, dim);
}

static int score(void) { return W.hit ? 100 : 0; }

/* Waits for the marker to swing into the window, heading for its middle. */
static void bot(Input *in, float t)
{
    (void)t;
    if (!W.pressed && W.t >= W.fade_in && fabsf(W.rot) <= W.window * 0.5f)
        in->down |= KEY_A_;
}

const MiniGame MG_SWING = {
    .id = "swing_timing",
    .title = "Timing",
    .rules = "Stop the swinging marker in the window.",
    .controls = "A or a tap: stop it",
    .cheat = "",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .bot = bot,
};
