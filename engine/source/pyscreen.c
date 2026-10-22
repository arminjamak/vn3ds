/* A game's own screens, run by its own Python (a ported mechanic, see
 * minigame.h): vnpack translates the game's screen language and init
 * python into one program (game.bin's PYSC section, built by
 * tools/vnpack/pyscreens.py with the runtime tools/vnpack/vn3ds_rt.py),
 * which runs here in pocketpy (third_party/pocketpy).
 *
 *   call screen x        a PORT entry "pyscreen" (screen=x, args=...): the
 *                        screen runs until it returns or jumps; a Jump
 *                        leaves its label in the story variable _vn3ds_jump
 *   show screen x        the story dict _vn3ds_screens (screen -> its
 *                        arguments): drawn over the story every frame; when
 *                        one has buttons, a button on the touch screen
 *                        (PORT entry "pyscreen", mode=overlay) opens it
 *
 * The program builds a display list per frame in the game's coordinates
 * (e.g. 1920x1080); it is drawn at the story's scale on the top screen,
 * each item at its own depth (nested boxes nearer, the focused button
 * nearest), and once more, flat and small, on the touch screen to tap.
 *
 * Controls in a run: D-pad = the screen's keys (a snake's WASD / arrows)
 * or moving the focus; Circle Pad = focus; A = press; B = the game's
 * "back"; taps on the touch screen's copy; START = the pause menu (quit
 * back to the story). */

#include "minigame.h"
#include "pocketpy.h"

#include <math.h>
#include <stdio.h>

static struct {
    bool on;          /* pocketpy is up with the program loaded */
    bool broken;      /* the program failed to load: don't try again */
    u32 crc;          /* of the game it was loaded for */
    py_GlobalRef mod; /* vn3ds_rt */
    int hud_entry;    /* PORT entry for the overlay button, -1 if none */
    char hud_label[48];
    float hud_t;      /* seconds since hud_label was asked */
    bool ran;         /* a run is on (MG mechanic) */
    bool overlay;     /* the run was opened from the overlays' button */
    char status[96];
    char jump[96];    /* an overlay's Jump, taken on the story's next frame */
} P;

/* image name -> texture, for this frame's draws */
#define TEX_CACHE 64
static struct {
    char name[40];
    s32 image;
} tcache[TEX_CACHE];
static int tcache_n;

/* ---- the _vn3ds module -------------------------------------------------- */

static bool to_value(py_Ref v, Value *out)
{
    value_free(out);
    if (py_isnone(v)) {
        out->type = VAL_NONE;
    } else if (py_isbool(v)) {
        out->type = VAL_BOOL;
        out->num = py_tobool(v) ? 1 : 0;
    } else if (py_isint(v)) {
        out->type = VAL_NUM;
        out->num = (double)py_toint(v);
    } else if (py_isfloat(v)) {
        out->type = VAL_NUM;
        out->num = py_tofloat(v);
    } else if (py_isstr(v)) {
        value_set_str(out, py_tostr(v));
    } else {
        return false;
    }
    return true;
}

static bool f_has(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(1);
    PY_CHECK_ARG_TYPE(0, tp_str);
    py_newbool(py_retval(), mg_var(py_tostr(py_arg(0))) != NULL);
    return true;
}

static bool f_get(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(1);
    PY_CHECK_ARG_TYPE(0, tp_str);
    Value *v = mg_var(py_tostr(py_arg(0)));
    if (!v || v->type == VAL_NONE) {
        py_newnone(py_retval());
    } else if (v->type == VAL_BOOL) {
        py_newbool(py_retval(), v->num != 0);
    } else if (v->type == VAL_NUM) {
        if (v->num == (double)(py_i64)v->num && v->num > -9e15 && v->num < 9e15)
            py_newint(py_retval(), (py_i64)v->num);
        else
            py_newfloat(py_retval(), v->num);
    } else {
        py_newstr(py_retval(), v->str ? v->str : "");
    }
    return true;
}

static bool f_set(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(2);
    PY_CHECK_ARG_TYPE(0, tp_str);
    Value *v = mg_var(py_tostr(py_arg(0)));
    if (v)
        to_value(py_arg(1), v);
    py_newnone(py_retval());
    return true;
}

static s32 audio_res(const char *name)
{
    return name && *name ? game_audio_named(&E.game, name) : -1;
}

/* play(channel, name, loop, fade) */
static bool f_play(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(4);
    int ch = (int)py_toint(py_arg(0));
    s32 res = audio_res(py_isstr(py_arg(1)) ? py_tostr(py_arg(1)) : NULL);
    float fade = py_isfloat(py_arg(3)) ? (float)py_tofloat(py_arg(3))
                 : py_isint(py_arg(3)) ? (float)py_toint(py_arg(3)) : 0;
    if (res >= 0 && ch >= 0 && ch < CH_COUNT)
        eng_play((u8)ch, res, py_tobool(py_arg(2)) ? 1 : 0, fade, 0);
    py_newnone(py_retval());
    return true;
}

static bool f_queue(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(3);
    int ch = (int)py_toint(py_arg(0));
    s32 res = audio_res(py_isstr(py_arg(1)) ? py_tostr(py_arg(1)) : NULL);
    if (res >= 0 && ch >= 0 && ch < CH_COUNT)
        eng_play((u8)ch, res, (py_tobool(py_arg(2)) ? 1 : 0) | 2, 0, 0);
    py_newnone(py_retval());
    return true;
}

static bool f_stop(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(2);
    int ch = (int)py_toint(py_arg(0));
    float fade = py_isfloat(py_arg(1)) ? (float)py_tofloat(py_arg(1)) : 0;
    if (ch >= 0 && ch < CH_COUNT)
        eng_stop((u8)ch, fade);
    py_newnone(py_retval());
    return true;
}

/* The audio name of what plays on a channel ("" if nothing or unnamed). */
static bool f_playing(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(1);
    const char *out = "";
    if (py_toint(py_arg(0)) == CH_MUSIC && E.music_res >= 0 && audio_playing(CH_MUSIC) &&
        E.game.audio_names) {
        u32 n = rd_u32(E.game.audio_names);
        for (u32 i = 0; i < n; i++)
            if (rd_s32(E.game.audio_names + 8 + 8 * i) == E.music_res) {
                const char *an = game_str(&E.game, rd_u32(E.game.audio_names + 4 + 8 * i));
                out = an ? an : "";
            }
    }
    py_newstr(py_retval(), out);
    return true;
}

/* Text: a game's font size in game pixels, drawn with the system font at
 * the story's scale but never smaller than is readable on the 3DS. */
#define MIN_TEXT_PX 8.5f

static float game_scale(void) { return E.game.scale > 0 ? E.game.scale : 1.0f; }

static float font_scale(float size)
{
    float px = size * game_scale();
    if (px < MIN_TEXT_PX)
        px = MIN_TEXT_PX;
    float base = gfx_line_height(1.0f) / 1.2f;   /* the font's em at scale 1 */
    return px / (base > 0 ? base : 20.0f);
}

static float num_arg(py_Ref v)
{
    return py_isfloat(v) ? (float)py_tofloat(v) : py_isint(v) ? (float)py_toint(v) : 0;
}

static bool f_text_width(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(2);
    const char *s = py_isstr(py_arg(0)) ? py_tostr(py_arg(0)) : "";
    py_newfloat(py_retval(), gfx_text_width(s, font_scale(num_arg(py_arg(1)))) / game_scale());
    return true;
}

static bool f_line_height(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(1);
    py_newfloat(py_retval(), gfx_line_height(font_scale(num_arg(py_arg(0)))) / game_scale());
    return true;
}

static bool f_log(int argc, py_StackRef argv)
{
    PY_CHECK_ARGC(1);
    if (py_isstr(py_arg(0)))
        fprintf(stderr, "[pyscreen] %s\n", py_tostr(py_arg(0)));
    py_newnone(py_retval());
    return true;
}

static bool f_seen_label(int argc, py_StackRef argv)
{
    py_newbool(py_retval(), true);
    return true;
}

/* ---- loading ------------------------------------------------------------ */

/* A display-list item: a tuple (or a list) of fields. */
static int seq_len(py_Ref it)
{
    return py_istuple(it) ? py_tuple_len(it) : py_islist(it) ? py_list_len(it) : 0;
}

static py_Ref seq_at(py_Ref it, int i)
{
    return py_istuple(it) ? py_tuple_getitem(it, i) : py_list_getitem(it, i);
}


static bool call(const char *fn, int argc);

static void report(const char *what)
{
    char *msg = py_formatexc();
    fprintf(stderr, "[pyscreen] %s: %s\n", what, msg ? msg : "?");
    if (msg)
        py_free(msg);
    py_clearexc(NULL);
}

void pys_unload(void)
{
    if (P.on)
        py_finalize();
    memset(&P, 0, sizeof(P));
    P.hud_entry = -1;
    tcache_n = 0;
}

static bool ensure(void)
{
    if (!E.loaded || !E.game.pysc)
        return false;
    if (P.on && P.crc == E.game.crc)
        return true;
    if (P.broken && P.crc == E.game.crc)
        return false;
    pys_unload();
    P.crc = E.game.crc;
    u64 t0 = platform_us();
    py_initialize();
    P.on = true;
    py_GlobalRef m = py_newmodule("_vn3ds");
    py_bindfunc(m, "has", f_has);
    py_bindfunc(m, "get", f_get);
    py_bindfunc(m, "set", f_set);
    py_bindfunc(m, "play", f_play);
    py_bindfunc(m, "queue", f_queue);
    py_bindfunc(m, "stop", f_stop);
    py_bindfunc(m, "playing", f_playing);
    py_bindfunc(m, "text_width", f_text_width);
    py_bindfunc(m, "line_height", f_line_height);
    py_bindfunc(m, "log", f_log);
    py_bindfunc(m, "seen_label", f_seen_label);
    P.mod = py_newmodule("vn3ds_rt");
    char *src = malloc(E.game.pysc_size + 1);
    if (!src) {
        P.broken = true;
        pys_unload();
        P.crc = E.game.crc;
        P.broken = true;
        return false;
    }
    memcpy(src, E.game.pysc, E.game.pysc_size);
    src[E.game.pysc_size] = 0;
    bool ok = py_exec(src, "vn3ds_rt", EXEC_MODE, P.mod);
    free(src);
    if (!ok) {
        report("loading the game's screens");
        py_finalize();
        P.on = false;
        P.broken = true;
        return false;
    }
    /* the game's own code, a statement at a time (see _load_chunks) */
    py_ItemRef chunks = py_getdict(P.mod, py_name("_CHUNKS"));
    int nchunks = chunks && py_islist(chunks) ? py_list_len(chunks) : 0, failed = 0;
    for (int i = 0; i < nchunks; i++) {
        py_Ref it = py_list_getitem(chunks, i);
        if (seq_len(it) < 2)
            continue;
        const char *where = py_tostr(seq_at(it, 0));
        const char *code = py_tostr(seq_at(it, 1));
        if (!py_exec(code, where, EXEC_MODE, P.mod)) {
            char *msg = py_formatexc();
            const char *last = msg ? strrchr(msg, '\n') : NULL;
            fprintf(stderr, "[pyscreen] %s: %s\n", where, last ? last + 1 : msg ? msg : "?");
            if (msg)
                py_free(msg);
            py_clearexc(NULL);
            failed++;
        }
    }
    if (chunks)
        py_list_clear(chunks);
    call("_finish_load", 0);
    fprintf(stderr, "[pyscreen] %d statements, %d left out\n", nchunks, failed);
    P.hud_entry = mg_port_find("pyscreen", "mode", "overlay");
    fprintf(stderr, "[pyscreen] loaded in %.0f ms\n", (platform_us() - t0) / 1000.0);
    return true;
}

/* Calls vn3ds_rt.<fn>(args in r0..) and leaves its result in py_retval(). */
static bool call(const char *fn, int argc)
{
    py_ItemRef f = py_getdict(P.mod, py_name(fn));
    if (!f)
        return false;
    if (!py_call(f, argc, argc ? py_r0() : NULL)) {
        report(fn);
        return false;
    }
    return true;
}

/* ---- drawing the display list ------------------------------------------- */

static s32 image_index(const char *name)
{
    for (int i = 0; i < tcache_n; i++)
        if (!strcmp(tcache[i].name, name))
            return tcache[i].image;
    s32 im = stage_resolve(&E.game, name, NULL);
    if (strlen(name) < sizeof(tcache[0].name)) {
        int k = tcache_n < TEX_CACHE ? tcache_n++ : (int)(platform_us() % TEX_CACHE);
        snprintf(tcache[k].name, sizeof(tcache[k].name), "%s", name);
        tcache[k].image = im;
    }
    return im;
}

static float fnum(py_Ref v) { return num_arg(v); }

typedef struct {
    float ox, oy, k;   /* game px -> screen px */
    int eye;           /* -1: the touch screen, flat */
} View;

static float shift_of(const View *vw, float depth)
{
    return vw->eye < 0 ? 0 : mg_shift(vw->eye, depth);
}

static void draw_item(const View *vw, py_Ref it)
{
    int len = seq_len(it);
    if (len < 2)
        return;
    const char *kind = py_tostr(seq_at(it, 0));
    if (!strcmp(kind, "img") && len >= 12) {
        const char *name = py_tostr(seq_at(it, 1));
        s32 i = image_index(name);
        if (i < 0 || (u32)i >= E.game.nimages)
            return;
        const ImageDef *im = &E.game.images[i];
        if (im->res < 0) {
            if (im->flags & IMG_SOLID) {
                float x = fnum(seq_at(it, 2)), y = fnum(seq_at(it, 3));
                float w = fnum(seq_at(it, 4)), h = fnum(seq_at(it, 5));
                gfx_rect(vw->ox + x * vw->k + shift_of(vw, fnum(seq_at(it, 7))),
                         vw->oy + y * vw->k, w * vw->k, h * vw->k, im->color);
            }
            return;
        }
        GfxTex *t = texcache_image(im);
        if (!t)
            return;
        float x = fnum(seq_at(it, 2)), y = fnum(seq_at(it, 3));
        float w = fnum(seq_at(it, 4)), h = fnum(seq_at(it, 5));
        float a = fnum(seq_at(it, 6)), depth = fnum(seq_at(it, 7));
        float cx = fnum(seq_at(it, 8)), cy = fnum(seq_at(it, 9));
        float cw = fnum(seq_at(it, 10)), ch = fnum(seq_at(it, 11));
        int iw, ih;
        gfx_tex_size(t, &iw, &ih);
        bool crop = cw > 0 && ch > 0;
        if (crop)   /* the window, as fractions of the image */
            gfx_tex_window(t, (int)(cx * iw + 0.5f), (int)(cy * ih + 0.5f),
                           (int)(cw * iw + 0.5f), (int)(ch * ih + 0.5f));
        gfx_image(t, vw->ox + x * vw->k + shift_of(vw, depth), vw->oy + y * vw->k, w * vw->k,
                  h * vw->k, 0, a);
        if (crop)
            gfx_tex_window(t, 0, 0, iw, ih);
    } else if (!strcmp(kind, "rect") && len >= 7) {
        u32 c = (u32)py_toint(seq_at(it, 1));
        if ((c & 0xFF) == 0)
            return;
        float x = fnum(seq_at(it, 2)), y = fnum(seq_at(it, 3));
        float w = fnum(seq_at(it, 4)), h = fnum(seq_at(it, 5));
        gfx_rect(vw->ox + x * vw->k + shift_of(vw, fnum(seq_at(it, 6))),
                 vw->oy + y * vw->k, w * vw->k, h * vw->k, c);
    } else if (!strcmp(kind, "text") && len >= 8) {
        const char *s = py_tostr(seq_at(it, 1));
        float x = fnum(seq_at(it, 2)), y = fnum(seq_at(it, 3));
        float size = fnum(seq_at(it, 4));
        u32 c = (u32)py_toint(seq_at(it, 5));
        u32 outl = (u32)py_toint(seq_at(it, 7));
        float sc = font_scale(size);
        if (vw->eye < 0)   /* the touch screen's copy is smaller */
            sc *= vw->k / game_scale();
        float sx = vw->ox + x * vw->k + shift_of(vw, fnum(seq_at(it, 6)));
        float sy = vw->oy + y * vw->k;
        if (outl & 0xFF) {
            gfx_text(s, sx - 1, sy, sc, outl);
            gfx_text(s, sx + 1, sy, sc, outl);
            gfx_text(s, sx, sy - 1, sc, outl);
            gfx_text(s, sx, sy + 1, sc, outl);
        }
        gfx_text(s, sx, sy, sc, c);
    }
}

static void draw_list(const View *vw)
{
    if (!call("draw_list", 0))
        return;
    py_Ref lst = py_retval();
    if (!py_islist(lst))
        return;
    /* the list stays alive in the module while we read it */
    int n = py_list_len(lst);
    if (getenv("VN3DS_PYS_DEBUG"))
        fprintf(stderr, "[pyscreen] draw %d items (eye %d)\n", n, vw->eye);
    py_StackRef keep = py_pushtmp();
    py_assign(keep, lst);
    for (int i = 0; i < n; i++) {
        if (getenv("VN3DS_PYS_DEBUG") && vw->eye == 0) {
            py_Ref it = py_list_getitem(keep, i);
            if (py_repr(it))
                fprintf(stderr, "    %s\n", py_tostr(py_retval()));
        }
        draw_item(vw, py_list_getitem(keep, i));
    }
    py_pop();
}

static View top_view(int eye)
{
    View v = {E.game.view_x, E.game.view_y, game_scale(), eye};
    return v;
}

/* The touch screen's copy: the whole game area, letterboxed. */
static View bottom_view(void)
{
    float gw = E.game.game_w ? E.game.game_w : 1920, gh = E.game.game_h ? E.game.game_h : 1080;
    float k = fminf(BOT_W / gw, (BOT_H - 22) / gh);
    View v = {(BOT_W - gw * k) / 2, 22 + (BOT_H - 22 - gh * k) / 2, k, -1};
    return v;
}

/* ---- the story's overlays ------------------------------------------------ */

static bool overlays_shown(void)
{
    const char *v = E.loaded && E.game.pysc ? mg_var_str("_vn3ds_screens") : NULL;
    return v && *v;
}

void pys_story_update(float dt)
{
    if (P.jump[0]) {
        char label[96];
        snprintf(label, sizeof(label), "%s", P.jump);
        P.jump[0] = 0;
        if (!app_story_jump(label))
            fprintf(stderr, "[pyscreen] no label '%s' to jump to\n", label);
        return;
    }
    if (!overlays_shown() || !ensure())
        return;
    py_newfloat(py_r0(), dt);
    py_newint(py_r1(), (py_i64)E.say_serial);
    call("story_frame", 2);
    P.hud_t += dt;
}

void pys_story_draw(int eye)
{
    if (!overlays_shown() || !P.on)
        return;
    View v = top_view(eye);
    draw_list(&v);
}

const char *pys_hud_label(void)
{
    if (!overlays_shown() || !P.on || P.hud_entry < 0)
        return NULL;
    if (!call("hud_label", 0) || !py_isstr(py_retval()))
        return NULL;
    snprintf(P.hud_label, sizeof(P.hud_label), "%s", py_tostr(py_retval()));
    return P.hud_label[0] ? P.hud_label : NULL;
}

void pys_hud_open(void)
{
    if (P.hud_entry >= 0)
        mg_begin_port(P.hud_entry);
}

/* ---- the mechanic --------------------------------------------------------- */

static void start(u32 seed)
{
    (void)seed;
    P.ran = false;
    P.status[0] = 0;
    if (!ensure())
        return;
    const char *mode = mg_param("mode");
    P.overlay = mode && !strcmp(mode, "overlay");
    py_newstr(py_r0(), mode && *mode ? mode : "call");
    const char *screen = mg_param("screen");
    py_newstr(py_r1(), screen ? screen : "");
    const char *args = mg_param("args");
    py_newstr(py_getreg(2), args ? args : "");
    P.ran = call("begin", 3);
    mg_var_set_str("_vn3ds_jump", "");
}

static void add_event(char *ev, size_t len, const char *what)
{
    size_t n = strlen(ev);
    snprintf(ev + n, len - n, "%s%s", n ? " " : "", what);
}

static float pad_t;

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    if (!P.ran)
        return false;
    char ev[160] = "";
    if (in->down & KEY_UP_)
        add_event(ev, sizeof(ev), "up");
    if (in->down & KEY_DOWN_)
        add_event(ev, sizeof(ev), "down");
    if (in->down & KEY_LEFT_)
        add_event(ev, sizeof(ev), "left");
    if (in->down & KEY_RIGHT_)
        add_event(ev, sizeof(ev), "right");
    if (in->down & KEY_A_)
        add_event(ev, sizeof(ev), "a");
    if (in->down & KEY_B_)
        add_event(ev, sizeof(ev), "b");
    if (in->down & KEY_X_)
        add_event(ev, sizeof(ev), "x");
    if (in->down & KEY_Y_)
        add_event(ev, sizeof(ev), "y");
    /* the circle pad moves the focus, a step at a time */
    pad_t -= dt;
    if (fabsf(in->cx) > 0.6f || fabsf(in->cy) > 0.6f) {
        if (pad_t <= 0) {
            add_event(ev, sizeof(ev), fabsf(in->cx) > fabsf(in->cy)
                                         ? (in->cx > 0 ? "pad_right" : "pad_left")
                                         : (in->cy > 0 ? "pad_up" : "pad_down"));
            pad_t = 0.22f;
        }
    } else {
        pad_t = 0;
    }
    if (in->down & KEY_TOUCH_) {
        View b = bottom_view();
        char t[48];
        snprintf(t, sizeof(t), "tap:%.0f,%.0f", (in->tx - b.ox) / b.k, (in->ty - b.oy) / b.k);
        add_event(ev, sizeof(ev), t);
    }
    py_newfloat(py_r0(), dt);
    py_newstr(py_r1(), ev);
    if (!call("frame", 2))
        return false;
    const char *st = py_isstr(py_retval()) ? py_tostr(py_retval()) : "end";
    if (!*st)
        return true;
    snprintf(P.status, sizeof(P.status), "%s", st);
    if (!strncmp(st, "jump:", 5) || !strncmp(st, "call:", 5)) {
        if (P.overlay)   /* the story isn't waiting on the screen: it goes there */
            snprintf(P.jump, sizeof(P.jump), "%s", st + 5);
        else
            mg_var_set_str("_vn3ds_jump", st + 5);
    }
    call("end_run", 0);
    return false;
}

static void draw_top(int eye)
{
    render_scene(eye);
    if (!P.ran)
        return;
    View v = top_view(eye);
    draw_list(&v);
}

static void draw_bottom(void)
{
    gfx_gradient(0, 0, BOT_W, BOT_H, RGBA(14, 14, 16, 255), RGBA(0, 0, 0, 255));
    if (P.ran) {
        View v = bottom_view();
        gfx_rect(v.ox, v.oy, (E.game.game_w ? E.game.game_w : 1920) * v.k,
                 (E.game.game_h ? E.game.game_h : 1080) * v.k, RGBA(0, 0, 0, 255));
        draw_list(&v);
    }
    gfx_text("Tap or D-pad + A    B: back    START: menu", 6, 4, 0.4f, RGBA(152, 152, 159, 255));
}

static int score(void)
{
    return 0;
}

const MiniGame MG_PYSCREEN = {
    .id = "pyscreen",
    .title = "Screen",
    .rules = "",
    .controls = "D-pad: the screen's keys or focus\nA: press\nB: back\nTouch: tap",
    .cheat = "",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
};
