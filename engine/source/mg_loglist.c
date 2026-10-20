/* An overlay's list (a ported mechanic, see minigame.h "Overlays"): the
 * page a game's persistent on-screen button opens, e.g. Eternum's list of
 * audio logs. Each item is another PORT entry (a captions recording) that
 * plays when picked; items appear once their condition variable is true.
 *
 * Parameters (PORT entry):
 *   button    the overlay button's label ("Audio logs")
 *   title     the list's heading
 *   item      one per entry, in order: "entry \t condition \t label"
 *             (condition: a story variable, or empty for always)
 *
 * Controls: D-pad to pick, A to play, B or the Close button to go back.
 * Score: 1 + the picked item's position among all items, 0 for none. */

#include "minigame.h"

#define MAX_ITEMS 24

static struct {
    int idx[MAX_ITEMS];       /* position in the entry's item list */
    char label[MAX_ITEMS][64];
    int n, sel, chosen;
    float t;
    const char *title;
} L;

#define ROW_H 26.0f

static void start(u32 seed)
{
    (void)seed;
    memset(&L, 0, sizeof(L));
    const char *items[MAX_ITEMS];
    int n = mg_param_all("item", items, MAX_ITEMS);
    for (int i = 0; i < n && L.n < MAX_ITEMS; i++) {
        const char *cond = strchr(items[i], '\t');
        const char *label = cond ? strchr(cond + 1, '\t') : NULL;
        char var[64] = "";
        if (cond && label && label - cond - 1 > 0 && (size_t)(label - cond - 1) < sizeof(var)) {
            memcpy(var, cond + 1, (size_t)(label - cond - 1));
            var[label - cond - 1] = 0;
        }
        if (var[0]) {
            Value *v = mg_var(var);
            bool on = v && (v->type == VAL_STR ? (v->str && v->str[0])
                                               : (v->type == VAL_NUM || v->type == VAL_BOOL) && v->num != 0);
            if (!on)
                continue;
        }
        L.idx[L.n] = i;
        snprintf(L.label[L.n], sizeof(L.label[0]), "%s", label ? label + 1 : "Play");
        L.n++;
    }
    L.title = mg_param("title");
    if (!L.title)
        L.title = mg_param("button");
    L.chosen = -1;
}

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    L.t += dt;
    if (L.t < 0.2f)
        return true;
    int rows = L.n + 1;   /* the last row is Close */
    if (in->down & KEY_UP_)
        L.sel = (L.sel + rows - 1) % rows;
    if (in->down & KEY_DOWN_)
        L.sel = (L.sel + 1) % rows;
    if (in->down & KEY_B_)
        L.chosen = L.n;
    if (in->down & KEY_A_)
        L.chosen = L.sel;
    if (in->down & KEY_TOUCH_)
        for (int i = 0; i < rows; i++) {
            float y = 30 + i * (ROW_H + 4);
            if (in->ty >= y && in->ty < y + ROW_H && in->tx >= 10 && in->tx < BOT_W - 10)
                L.sel = L.chosen = i;
        }
    return L.chosen < 0;
}

static void draw_top(int eye) { render_scene(eye); }

static void draw_bottom(void)
{
    gfx_text(L.title ? L.title : "", 10, 6, 0.5f, MG_WHITE);
    for (int i = 0; i <= L.n; i++) {
        float y = 30 + i * (ROW_H + 4);
        const char *s = i < L.n ? L.label[i] : "Close";
        ui_rrect(10, y, BOT_W - 20, ROW_H, 9, i == L.sel ? RGBA(90, 120, 200, 255) : RGBA(52, 52, 58, 255));
        gfx_text(s, 22, y + (ROW_H - gfx_line_height(0.48f)) / 2, 0.48f, MG_WHITE);
    }
}

static int score(void) { return L.chosen >= 0 && L.chosen < L.n ? L.idx[L.chosen] + 1 : 0; }

/* Tests open the first log. */
static void bot(Input *in, float t)
{
    if (t > 0.5f && t < 0.52f)
        in->down |= KEY_A_;
}

const MiniGame MG_LOGLIST = {
    .id = "loglist",
    .title = "List",
    .rules = "",
    .controls = "D-pad: pick\nA: play\nB: close",
    .cheat = "",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .bot = bot,
};
