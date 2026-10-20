/* Instrument (a ported mechanic, see minigame.h): a picture with playable
 * hotspots, one per string or key. Each pluck plays its note, may change the
 * picture and updates the story's variables the way the original screen's
 * buttons did (a counter, the sequence played so far); a Stop hotspot ends
 * the performance. The story then reacts to what was played.
 *
 * Parameters (PORT entry):
 *   background_var  the variable holding the picture's image (the original
 *                   screen showed whatever it named); background: its
 *                   default; bg_alias "VALUE\tSPEC" maps a value (e.g. a
 *                   file path) to a packed image
 *   overlay         image drawn over the picture (the hotspot art)
 *   string          one per hotspot, tab-separated:
 *                   "x y w h \t label \t sound \t hover image \t op \t op ..."
 *                   rect in the story's virtual px; sound plays by name;
 *                   ops: "set VAR=TEXT", "add VAR=NUMBER", "cat VAR=TEXT"
 *   stop            "x y w h \t label \t hover image" of the Stop hotspot
 *
 * Controls: D-pad / Circle Pad pick a string (B jumps to Stop), A plays it;
 * or tap the big buttons on the touch screen. */

#include "minigame.h"

#define MAX_STRINGS 16
#define MAX_OPS 6

typedef struct {
    float x, y, w, h;
    char label[16];
    char sound[32];
    char hover[64];
    char ops[MAX_OPS][96];
    int nops;
    float flash_t;   /* when it was last played */
} Str;

static struct {
    Str s[MAX_STRINGS + 1];   /* the last one is Stop */
    int n;                    /* strings, not counting Stop */
    bool has_stop;
    int sel;
    int touch;                /* button under the finger, -1 none */
    float t;
    bool done;
    float done_t;
    const char *bg_var;
    int played;
    float axis_t;             /* Circle Pad repeat */
} I;

static char *field(char **p)
{
    char *s = *p;
    if (!s)
        return "";
    char *tab = strchr(s, '\t');
    if (tab) {
        *tab = 0;
        *p = tab + 1;
    } else {
        *p = NULL;
    }
    return s;
}

static void parse(Str *st, const char *src, bool is_stop)
{
    char buf[700];
    snprintf(buf, sizeof(buf), "%s", src);
    char *p = buf;
    sscanf(field(&p), "%f %f %f %f", &st->x, &st->y, &st->w, &st->h);
    snprintf(st->label, sizeof(st->label), "%s", field(&p));
    if (!is_stop)
        snprintf(st->sound, sizeof(st->sound), "%s", field(&p));
    snprintf(st->hover, sizeof(st->hover), "%s", field(&p));
    while (!is_stop && p && st->nops < MAX_OPS)
        snprintf(st->ops[st->nops++], sizeof(st->ops[0]), "%s", field(&p));
    st->flash_t = -10;
}

/* The image the background variable names now. */
static const char *bg_spec(void)
{
    const char *v = mg_var_str(I.bg_var);
    if (!v)
        v = mg_param("background");   /* the variable's default */
    if (!v)
        return NULL;
    const char *alias[64];
    int n = mg_param_all("bg_alias", alias, 64);
    size_t len = strlen(v);
    for (int i = 0; i < n; i++)
        if (!strncmp(alias[i], v, len) && alias[i][len] == '\t')
            return alias[i] + len + 1;
    return v;
}

static void start(u32 seed)
{
    (void)seed;
    memset(&I, 0, sizeof(I));
    const char *src[MAX_STRINGS];
    I.n = mg_param_all("string", src, MAX_STRINGS);
    for (int i = 0; i < I.n; i++)
        parse(&I.s[i], src[i], false);
    const char *stop = mg_param("stop");
    if (stop) {
        parse(&I.s[I.n], stop, true);
        I.has_stop = true;
    }
    I.bg_var = mg_param("background_var");
    I.touch = -1;
    /* load the art now rather than on the first pluck */
    mg_image(mg_param("overlay"), NULL, NULL);
    mg_image(bg_spec(), NULL, NULL);
    for (int i = 0; i < I.n + (I.has_stop ? 1 : 0); i++)
        mg_image(I.s[i].hover, NULL, NULL);
}

static void apply(const char *op)
{
    char var[64];
    const char *eq = strchr(op, '=');
    if (strlen(op) < 5 || !eq || eq - (op + 4) >= (int)sizeof(var))
        return;
    memcpy(var, op + 4, eq - (op + 4));
    var[eq - (op + 4)] = 0;
    const char *val = eq + 1;
    if (!strncmp(op, "set ", 4)) {
        mg_var_set_str(var, val);
    } else if (!strncmp(op, "add ", 4)) {
        mg_var_set_num(var, mg_var_num(var, 0) + atof(val));
    } else if (!strncmp(op, "cat ", 4)) {
        const char *cur = mg_var_str(var);
        char buf[1024];
        snprintf(buf, sizeof(buf), "%s%s", cur ? cur : "", val);
        mg_var_set_str(var, buf);
    }
}

static void pluck(int i)
{
    if (i == I.n) {   /* Stop */
        I.done = true;
        I.done_t = I.t;
        I.s[i].flash_t = I.t;
        return;
    }
    Str *st = &I.s[i];
    st->flash_t = I.t;
    mg_sfx(st->sound);
    for (int k = 0; k < st->nops; k++)
        apply(st->ops[k]);
    I.played++;
}

/* Bottom screen buttons: two rows. */
static void button_rect(int i, float *x, float *y, float *w, float *h)
{
    int total = I.n + (I.has_stop ? 1 : 0);
    int per_row = (total + 1) / 2;
    int row = i < per_row ? 0 : 1, col = row ? i - per_row : i;
    int in_row = row ? total - per_row : per_row;
    float bw = (BOT_W - 12 - 6 * (per_row - 1)) / (float)per_row;
    float rw = in_row * bw + (in_row - 1) * 6;
    *w = bw;
    *h = 74;
    *x = (BOT_W - rw) / 2 + col * (bw + 6);
    *y = 36 + row * 82;
}

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    I.t += dt;
    if (I.done)
        return I.t - I.done_t < 0.3f;
    int total = I.n + (I.has_stop ? 1 : 0);
    if (total == 0)
        return false;
    int step = 0;
    if (in->down & (KEY_RIGHT_ | KEY_DOWN_))
        step = 1;
    if (in->down & (KEY_LEFT_ | KEY_UP_))
        step = -1;
    float ax = fabsf(in->cx) > fabsf(in->cy) ? in->cx : -in->cy;
    if (fabsf(ax) > 0.5f) {
        if (I.axis_t <= 0) {
            step = ax > 0 ? 1 : -1;
            I.axis_t = 0.22f;
        }
        I.axis_t -= dt;
    } else {
        I.axis_t = 0;
    }
    if (step)
        I.sel = (I.sel + step + total) % total;
    if ((in->down & KEY_B_) && I.has_stop)
        I.sel = I.n;
    if (in->down & KEY_A_)
        pluck(I.sel);
    I.touch = -1;
    if (in->held & KEY_TOUCH_)
        for (int i = 0; i < total; i++) {
            float x, y, w, h;
            button_rect(i, &x, &y, &w, &h);
            if (in->tx >= x && in->tx < x + w && in->ty >= y && in->ty < y + h) {
                I.touch = i;
                if (in->down & KEY_TOUCH_) {
                    I.sel = i;
                    pluck(i);
                }
            }
        }
    return true;
}

static void draw_virtual(int eye, const char *spec, float x, float y, float depth, float alpha)
{
    float w, h;
    GfxTex *t = mg_image(spec, &w, &h);
    if (!t)
        return;
    const Game *g = &E.game;
    gfx_image(t, g->view_x + x * g->scale + mg_shift(eye, depth), g->view_y + y * g->scale, w, h, 0,
              alpha);
}

static void draw_top(int eye)
{
    const char *bg = bg_spec();
    float w, h;
    if (bg && mg_image(bg, &w, &h))
        draw_virtual(eye, bg, 0, 0, E.game.depth_bg, 1);
    else
        render_scene(eye);
    float fade = mg_paramf("fade_in", 0) > 0 ? clampf(I.t / mg_paramf("fade_in", 0), 0, 1) : 1;
    draw_virtual(eye, mg_param("overlay"), 0, 0, -0.1f, fade);
    int total = I.n + (I.has_stop ? 1 : 0);
    for (int i = 0; i < total; i++) {
        const Str *st = &I.s[i];
        float flash = clampf(1 - (I.t - st->flash_t) / 0.6f, 0, 1);
        float a = i == I.sel ? 1.0f : flash;
        if (a <= 0)
            continue;
        if (mg_image(st->hover, NULL, NULL)) {
            draw_virtual(eye, st->hover, st->x, st->y, -0.18f - 0.1f * flash, a);
        } else {
            const Game *g = &E.game;
            mg_circle(eye, g->view_x + (st->x + st->w / 2) * g->scale,
                      g->view_y + (st->y + st->h / 2) * g->scale, 12 + 6 * flash, -0.18f,
                      RGBA(255, 220, 140, (int)(90 * a)));
        }
    }
}

static void draw_bottom(void)
{
    const u32 dim = RGBA(152, 152, 159, 255);
    char buf[48];
    gfx_text("Play", 12, 10, 0.6f, MG_WHITE);
    snprintf(buf, sizeof(buf), "Notes played: %d", I.played);
    gfx_text(buf, BOT_W - 12 - gfx_text_width(buf, 0.45f), 13, 0.45f, MG_GOLD);
    int total = I.n + (I.has_stop ? 1 : 0);
    for (int i = 0; i < total; i++) {
        float x, y, w, h;
        button_rect(i, &x, &y, &w, &h);
        float flash = clampf(1 - (I.t - I.s[i].flash_t) / 0.3f, 0, 1);
        bool on = I.touch == i || flash > 0;
        bool stop = i == I.n;
        u32 bg = on ? RGBA(255, 255, 255, 235) : stop ? RGBA(90, 40, 40, 255) : RGBA(52, 52, 56, 255);
        ui_rrect(x, y, w, h, 12, bg);
        if (i == I.sel)
            ui_rrect(x + 3, y + h - 8, w - 6, 4, 2, MG_GOLD);
        const char *lab = I.s[i].label[0] ? I.s[i].label : (stop ? "Stop" : "?");
        float sc = stop ? 0.5f : 0.75f;
        gfx_text(lab, x + (w - gfx_text_width(lab, sc)) / 2, y + (h - gfx_line_height(sc)) / 2, sc,
                 on ? RGBA(0, 0, 0, 255) : MG_WHITE);
    }
    gfx_text("D-pad: choose   A: play   B: go to Stop", 12, 206, 0.42f, dim);
}

static int score(void) { return I.played > 100 ? 100 : I.played; }

/* Plays a short tune up the strings, then Stop. */
static void bot(Input *in, float t)
{
    static float last = 1e9f, next;
    static int k;
    if (t < last) {
        k = 0;
        next = 0.6f;
    }
    last = t;
    if (t < next || I.done)
        return;
    int tune[] = {0, 1, 2, 3, 4, 3, 2, 1};
    int len = (int)ARRAY_LEN(tune);
    int want = k < len ? tune[k] % (I.n ? I.n : 1) : I.n;
    if (I.sel != want) {
        in->down |= I.sel < want ? KEY_RIGHT_ : KEY_LEFT_;
        next = t + 0.08f;
        return;
    }
    in->down |= KEY_A_;
    k++;
    next = t + 0.35f;
}

const MiniGame MG_INSTRUMENT = {
    .id = "instrument",
    .title = "Instrument",
    .rules = "Play the strings; Stop ends the performance.",
    .controls = "D-pad / Circle Pad: choose a string\nA: play it\nB: go to Stop",
    .cheat = "",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .bot = bot,
};
