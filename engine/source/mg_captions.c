/* Timed captions (a ported mechanic, see minigame.h): a recording plays (the
 * story started it) while its lines fade in and out on cue over the scene,
 * with a spinning record icon, until the original screen's timer runs out.
 *
 * Parameters (PORT entry):
 *   duration      seconds until it ends (the original's timer)
 *   caption       one per line: "in0 in1 out0 out1 \t x y \t text": fades in
 *                 from in0 to in1 and out from out0 to out1 (seconds; out0 < 0:
 *                 stays), at x, y in the story's virtual px
 *   spinner       image of the icon, spinner_box "x y w h" (virtual px),
 *                 spinner_period (seconds a turn)
 *
 * Controls: none needed; B skips to the end (and stops the recording). */

#include "minigame.h"

#define MAX_CAPTIONS 32

typedef struct {
    float in0, in1, out0, out1;
    float x, y;
    const char *text;
    char wrapped_top[1024];
    char wrapped_bot[1024];
} Cap;

static struct {
    Cap c[MAX_CAPTIONS];
    int n;
    float t, duration;
    float sx, sy, sw, sh, period;
    bool skipped;
    float skip_hold;
} C;

#define TOP_SCALE 0.42f
#define BOT_SCALE 0.55f

static void start(u32 seed)
{
    (void)seed;
    memset(&C, 0, sizeof(C));
    C.duration = mg_paramf("duration", 10);
    const char *src[MAX_CAPTIONS];
    C.n = mg_param_all("caption", src, MAX_CAPTIONS);
    const Game *g = &E.game;
    for (int i = 0; i < C.n; i++) {
        Cap *c = &C.c[i];
        c->out0 = c->out1 = -1;
        sscanf(src[i], "%f %f %f %f", &c->in0, &c->in1, &c->out0, &c->out1);
        const char *p = strchr(src[i], '\t');
        c->x = g->game_w * 0.2f;
        c->y = g->game_h * 0.04f;
        if (p) {
            sscanf(p + 1, "%f %f", &c->x, &c->y);
            p = strchr(p + 1, '\t');
        }
        c->text = p ? p + 1 : "";
        float x = g->view_x + c->x * g->scale;
        ui_wrap(c->text, TOP_W - x - 10, TOP_SCALE, c->wrapped_top, sizeof(c->wrapped_top));
        ui_wrap(c->text, BOT_W - 28, BOT_SCALE, c->wrapped_bot, sizeof(c->wrapped_bot));
    }
    C.sw = C.sh = 114;
    C.sx = g->game_w * 0.1f;
    C.sy = 20;
    const char *v = mg_param("spinner_box");
    if (v)
        sscanf(v, "%f %f %f %f", &C.sx, &C.sy, &C.sw, &C.sh);
    C.period = mg_paramf("spinner_period", 2);
    mg_image(mg_param("spinner"), NULL, NULL);
}

static float alpha_of(const Cap *c, float t)
{
    float a;
    if (t < c->in0)
        return 0;
    a = c->in1 > c->in0 ? clampf((t - c->in0) / (c->in1 - c->in0), 0, 1) : 1;
    if (c->out0 >= 0 && t >= c->out0)
        a *= c->out1 > c->out0 ? clampf(1 - (t - c->out0) / (c->out1 - c->out0), 0, 1) : 0;
    return a;
}

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    C.t += dt;
    if (in->held & KEY_B_) {
        C.skip_hold += dt;
    } else {
        C.skip_hold = 0;
    }
    bool tap_skip = (in->down & KEY_TOUCH_) && in->ty >= 200 && in->tx >= 200;
    if (C.skip_hold >= 0.6f || tap_skip) {
        C.skipped = true;
        audio_stop(CH_SOUND, 0.5f);   /* the recording the story started */
        return false;
    }
    return C.t < C.duration;
}

static void draw_top(int eye)
{
    render_scene(eye);
    const Game *g = &E.game;
    float vis = 0;
    for (int i = 0; i < C.n; i++)
        vis = fmaxf(vis, alpha_of(&C.c[i], C.t));
    if (vis > 0)   /* a soft band so the lines read over any picture */
        gfx_gradient(0, 0, TOP_W, 96, RGBA(0, 0, 0, (int)(150 * vis)), RGBA(0, 0, 0, 0));
    float w, h;
    GfxTex *sp = mg_image(mg_param("spinner"), &w, &h);
    if (sp) {
        float sw = C.sw * g->scale, sh = C.sh * g->scale;
        float ang = C.period > 0 ? fmodf(C.t / C.period, 1) * 2 * (float)M_PI : 0;
        gfx_image(sp, g->view_x + C.sx * g->scale + mg_shift(eye, -0.2f), g->view_y + C.sy * g->scale,
                  sw, sh, ang, 1);
    }
    for (int i = 0; i < C.n; i++) {
        float a = alpha_of(&C.c[i], C.t);
        if (a <= 0)
            continue;
        float x = g->view_x + C.c[i].x * g->scale, y = g->view_y + C.c[i].y * g->scale;
        u32 col = rgba_alpha(MG_WHITE, a), sh = RGBA(0, 0, 0, (int)(200 * a));
        mg_text(eye, C.c[i].wrapped_top, x + 1, y + 1, TOP_SCALE, -0.15f, sh);
        mg_text(eye, C.c[i].wrapped_top, x, y, TOP_SCALE, -0.15f, col);
    }
}

static void draw_bottom(void)
{
    const u32 dim = RGBA(152, 152, 159, 255);
    float y = 14;
    for (int i = 0; i < C.n; i++) {
        float a = alpha_of(&C.c[i], C.t);
        if (a <= 0)
            continue;
        gfx_text(C.c[i].wrapped_bot, 14, y, BOT_SCALE, rgba_alpha(MG_WHITE, a));
        y += gfx_line_height(BOT_SCALE) * (ui_count_lines(C.c[i].wrapped_bot) + 0.5f);
    }
    float p = C.duration > 0 ? clampf(C.t / C.duration, 0, 1) : 1;
    gfx_rect(14, 192, 292, 4, RGBA(52, 52, 56, 255));
    gfx_rect(14, 192, 292 * p, 4, MG_WHITE);
    char buf[32];
    int left = (int)ceilf(C.duration - C.t);
    snprintf(buf, sizeof(buf), "%d:%02d", left / 60, left % 60);
    gfx_text(buf, 14, 206, 0.45f, dim);
    ui_rrect(200, 202, 106, 30, 12, RGBA(52, 52, 56, 255));
    const char *s = "Hold B: skip";
    gfx_text(s, 253 - gfx_text_width(s, 0.42f) / 2, 208, 0.42f, MG_WHITE);
}

static int score(void) { return C.skipped ? 0 : 100; }

/* Listens to the end. */
static void bot(Input *in, float t)
{
    (void)in;
    (void)t;
}

const MiniGame MG_CAPTIONS = {
    .id = "captions",
    .title = "Recording",
    .rules = "",
    .controls = "Hold B: skip",
    .cheat = "",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .bot = bot,
};
