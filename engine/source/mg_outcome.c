/* The outcome card (a ported mechanic, see minigame.h): stands in for a
 * game's own minigame that vn3ds can't play and no adapter rebuilds. It
 * says so, and the player picks how it went; the story carries on down that
 * branch. vnpack works out the choices from the screen (what it returns,
 * the jumps it can take) and compiles the call so the chosen option's index,
 * returned as the score, sets the variables or takes the jump the original
 * would have (tools/vnpack/ported.py, outcome_entry()).
 *
 * Parameters (PORT entry):
 *   title     the minigame's name (from the screen's name)
 *   text      what the card says
 *   option    one per choice, in order: its label
 *
 * Controls: D-pad / Circle Pad to pick, A or a tap to choose. */

#include "minigame.h"

#define MAX_OPTIONS 6

static struct {
    const char *title;
    char text_top[1024], text_bot[1024];
    const char *opt[MAX_OPTIONS];
    int n, sel, chosen;
    float t;
} O;

#define TOP_SCALE 0.55f
#define BOT_SCALE 0.5f
#define BTN_H 30.0f
#define BTN_GAP 8.0f

static float btn_y(int i)
{
    float total = O.n * BTN_H + (O.n - 1) * BTN_GAP;
    return 236 - 8 - total + i * (BTN_H + BTN_GAP);
}

static void start(u32 seed)
{
    (void)seed;
    memset(&O, 0, sizeof(O));
    O.title = mg_param("title");
    if (!O.title || !*O.title)
        O.title = "A minigame";
    const char *text = mg_param("text");
    if (!text)
        text = "This minigame can't be played on the 3DS. How did it go?";
    ui_wrap(text, TOP_W - 60, TOP_SCALE, O.text_top, sizeof(O.text_top));
    ui_wrap(text, BOT_W - 28, BOT_SCALE, O.text_bot, sizeof(O.text_bot));
    O.n = mg_param_all("option", O.opt, MAX_OPTIONS);
    if (O.n == 0) {
        O.opt[0] = "Continue";
        O.n = 1;
    }
    O.chosen = -1;
}

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    O.t += dt;
    if (O.t < 0.3f)   /* the A that started the line doesn't choose */
        return true;
    if (in->down & KEY_UP_)
        O.sel = (O.sel + O.n - 1) % O.n;
    if (in->down & KEY_DOWN_)
        O.sel = (O.sel + 1) % O.n;
    if (in->down & KEY_TOUCH_)
        for (int i = 0; i < O.n; i++)
            if (in->tx >= 14 && in->tx < BOT_W - 14 && in->ty >= btn_y(i) &&
                in->ty < btn_y(i) + BTN_H) {
                O.sel = O.chosen = i;
            }
    if (in->down & KEY_A_)
        O.chosen = O.sel;
    return O.chosen < 0;
}

static void draw_top(int eye)
{
    render_scene(eye);
    gfx_rect(0, 0, TOP_W, TOP_H, RGBA(0, 0, 0, 140));
    float x = 30, y = 60;
    mg_rect(eye, x - 12, y - 14, TOP_W - 36, 120, -0.25f, RGBA(28, 28, 34, 230));
    mg_text(eye, O.title, x, y, 0.7f, -0.3f, MG_GOLD);
    mg_text(eye, O.text_top, x, y + 30, TOP_SCALE, -0.3f, MG_WHITE);
}

static void draw_bottom(void)
{
    gfx_text(O.text_bot, 14, 12, BOT_SCALE, RGBA(200, 200, 208, 255));
    for (int i = 0; i < O.n; i++) {
        float y = btn_y(i);
        bool on = i == O.sel;
        ui_rrect(14, y, BOT_W - 28, BTN_H, 10, on ? RGBA(90, 120, 200, 255) : RGBA(52, 52, 58, 255));
        float s = 0.5f;
        gfx_text(O.opt[i], BOT_W / 2 - gfx_text_width(O.opt[i], s) / 2,
                 y + (BTN_H - gfx_line_height(s)) / 2, s, MG_WHITE);
    }
}

/* The option's index (vnpack maps it back to the original's results). */
static int score(void) { return O.chosen < 0 ? 0 : O.chosen; }

/* Tests take the first option unless scripted input picks another. */
static void bot(Input *in, float t)
{
    if (t > 0.5f && t < 0.52f)
        in->down |= KEY_A_;
}

const MiniGame MG_OUTCOME = {
    .id = "outcome",
    .title = "Minigame",
    .rules = "",
    .controls = "D-pad: pick\nA: choose",
    .cheat = "",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .bot = bot,
};
