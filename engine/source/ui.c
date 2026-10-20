#include "app.h"
#include "leaderboard.h"
#include "minigame.h"
#include "net.h"

#include <time.h>

enum {
    B_TITLE_START = 1, B_TITLE_LOAD = 2, B_TITLE_GAMES = 3, B_TITLE_QUIT = 4, B_TITLE_MINI = 5,
    B_MG = 60, B_MG_BACK = 90, B_MG_BOARD = 91,
    B_LOG = 10, B_AUTO, B_SKIP, B_SAVE, B_LOAD, B_MENU,
    B_BACK = 20, B_PAGE_PREV, B_PAGE_NEXT, B_LOG_UP, B_LOG_DOWN,
    B_TO_TITLE = 30,
    B_RECEIVE = 40, B_RECEIVE_DONE,
    B_CHOICE = 100, B_SLOT = 200, B_PREF_DEC = 300, B_PREF_INC = 320, B_GAME = 400,
};

#define WHITE 0xFFFFFFFFu
#define BLACK 0x000000FFu
#define PANEL(a) RGBA(12, 12, 22, (u32)((a) * 255))

static inline float eye_sign(int eye) { return eye == EYE_LEFT ? -1.0f : 1.0f; }
/* Horizontal shift for something at `depth` seen by `eye`. */
static inline float shift(int eye, float depth) { return eye_sign(eye) * depth * app_strength(); }

static float ui_depth(void) { return E.loaded ? E.game.depth_ui : -0.35f; }

/* ---- text helpers ------------------------------------------------------- */

void ui_wrap(const char *src, float width, float scale, char *out, size_t len)
{
    size_t o = 0, last_space = (size_t)-1;
    float line_w = 0, w_at_space = 0;
    u32 cp;
    int k;
    while ((k = utf8_decode(src, &cp)) > 0 && o + (size_t)k + 1 < len) {
        if (cp == '\n') {
            out[o++] = '\n';
            line_w = 0;
            last_space = (size_t)-1;
            src += k;
            continue;
        }
        float adv = gfx_glyph_advance(cp, scale);
        if (line_w + adv > width && line_w > 0) {
            if (cp == ' ') {
                out[o++] = '\n';
                line_w = 0;
                last_space = (size_t)-1;
                src += k;
                continue;
            }
            if (last_space != (size_t)-1) {
                out[last_space] = '\n';
                line_w -= w_at_space;
            } else {
                out[o++] = '\n';
                line_w = 0;
            }
            last_space = (size_t)-1;
        }
        if (cp == ' ') {
            last_space = o;
            w_at_space = line_w + adv;
        }
        memcpy(out + o, src, (size_t)k);
        o += (size_t)k;
        line_w += adv;
        src += k;
    }
    out[o] = 0;
}

int ui_count_lines(const char *s)
{
    if (!*s)
        return 0;
    int n = 1;
    for (; *s; s++)
        if (*s == '\n')
            n++;
    return n;
}


/* Draw text, each line centred on cx. */
static void text_centered(const char *s, float cx, float y, float scale, u32 color)
{
    char line[512];
    float lh = gfx_line_height(scale);
    while (*s) {
        size_t n = strcspn(s, "\n");
        size_t c = n < sizeof(line) - 1 ? n : sizeof(line) - 1;
        memcpy(line, s, c);
        line[c] = 0;
        gfx_text(line, cx - gfx_text_width(line, scale) / 2, y, scale, color);
        y += lh;
        s += n;
        if (*s == '\n')
            s++;
    }
}

static float fit_scale(const char *s, float scale, float width)
{
    float w = gfx_text_width(s, scale);
    if (w > width && w > 0)
        scale *= width / w;
    return scale;
}

void ui_hist_add(const char *who, u32 color, const char *text, bool extend)
{
    HistEntry *h;
    if (extend && E.hist_n > 0) {
        h = &E.hist[E.hist_n - 1];
    } else {
        if (E.hist_n == HIST_MAX) {
            memmove(&E.hist[0], &E.hist[1], sizeof(HistEntry) * (HIST_MAX - 1));
            E.hist_n--;
        }
        h = &E.hist[E.hist_n++];
        snprintf(h->who, sizeof(h->who), "%s", who ? who : "");
        h->who_color = color;
    }
    snprintf(h->text, sizeof(h->text), "%s", text);
}

/* ---- buttons -------------------------------------------------------------- */

static int add(Button *b, int n, int max, float x, float y, float w, float h, const char *label,
               int id)
{
    if (n >= max)
        return n;
    Button *o = &b[n];
    memset(o, 0, sizeof(*o));
    o->x = x;
    o->y = y;
    o->w = w;
    o->h = h;
    o->label = label;
    o->id = id;
    return n + 1;
}

static int list_window(int sel, int count, int visible)
{
    int first = sel - visible / 2;
    if (first > count - visible)
        first = count - visible;
    return first < 0 ? 0 : first;
}

static const char *PREF_NAMES[NUM_PREFS] = {
    "Text speed", "Auto-forward", "3D depth", "Textbox", "Music", "Sound",
    "Return to title", "Close",
};

static int slot_buttons(Button *b, int n, int max)
{
    static char labels[SLOTS_PER_PAGE][8];
    for (int i = 0; i < SLOTS_PER_PAGE; i++) {
        int c = i % 2, r = i / 2;
        snprintf(labels[i], sizeof(labels[i]), "%d", E.slot_page * SLOTS_PER_PAGE + i + 1);
        n = add(b, n, max, 4 + c * 158, 26 + r * 56, 154, 52, labels[i], B_SLOT + i);
        b[n - 1].hot = i == E.slot_sel;
    }
    n = add(b, n, max, 4, 200, 100, 36, "Back", B_BACK);
    n = add(b, n, max, 166, 200, 72, 36, "<", B_PAGE_PREV);
    n = add(b, n, max, 244, 200, 72, 36, ">", B_PAGE_NEXT);
    return n;
}

int ui_title_items(int *ids)
{
    int n = 0;
    ids[n++] = B_TITLE_START;
    ids[n++] = B_TITLE_LOAD;
    if (E.loaded && E.game.nminigames > 0)
        ids[n++] = B_TITLE_MINI;
    ids[n++] = B_TITLE_GAMES;
    ids[n++] = B_TITLE_QUIT;
    return n;
}

int ui_buttons(Button *b, int max)
{
    int n = 0;
    switch (E.screen) {
    case SCR_MGMENU: {
        static char labels[16][96];
        int cnt = mg_count();
        for (int i = 0; i < cnt && i < 16; i++) {
            int best = mg_best(mg_at(i)->id);
            if (best >= 0)
                snprintf(labels[i], sizeof(labels[i]), "%s   %d%%", mg_at(i)->title, best);
            else
                snprintf(labels[i], sizeof(labels[i]), "%s", mg_at(i)->title);
            n = add(b, n, max, 12, 26 + i * 25, 296, 23, labels[i], B_MG + i);
            b[n - 1].hot = i == E.mg_sel;
        }
        n = add(b, n, max, 12, 206, 120, 30, E.mg_board ? "B: Close" : "B: Back", B_MG_BACK);
        n = add(b, n, max, 188, 206, 120, 30, E.mg_board ? "X: Refresh" : "X: Leaderboard",
                B_MG_BOARD);
        break;
    }
    case SCR_RECEIVE:
        n = add(b, n, max, 60, 196, 200, 36, "Done", B_RECEIVE_DONE);
        break;
    case SCR_MINIGAME:   /* minigame.c handles its own touch areas */
        break;
    case SCR_GAMELIST: {
        n = add(b, n, max, 170, 200, 146, 34, "Receive (Y)", B_RECEIVE);
        int vis = E.ngames < 4 ? E.ngames : 4;
        int first = list_window(E.game_sel, E.ngames, vis);
        for (int i = first; i < first + vis; i++) {
            n = add(b, n, max, 20, 40 + (i - first) * 36, 280, 32, E.game_titles[i], B_GAME + i);
            b[n - 1].hot = i == E.game_sel;
        }
        break;
    }
    case SCR_TITLE:
        if (E.overlay == OV_LOAD)
            return slot_buttons(b, n, max);
        {
            int ids[6], cnt = ui_title_items(ids);
            float step = cnt > 4 ? 36 : 44;
            for (int i = 0; i < cnt; i++) {
                const char *label = ids[i] == B_TITLE_START ? "Start" : ids[i] == B_TITLE_LOAD ? "Load"
                                  : ids[i] == B_TITLE_MINI ? "Minigames" : ids[i] == B_TITLE_GAMES
                                  ? "Game list" : "Quit";
                n = add(b, n, max, 60, 32 + i * step, 200, step - 6, label, ids[i]);
                b[n - 1].hot = i == E.title_sel;
            }
        }
        break;
    case SCR_GAME:
        switch (E.overlay) {
        case OV_NONE:
            if (E.vm.state == VM_MENU) {
                int cnt = E.vm.nchoices, vis = cnt < 5 ? cnt : 5;
                int first = list_window(E.menu_sel, cnt, vis);
                for (int i = first; i < first + vis; i++) {
                    n = add(b, n, max, 10, 28 + (i - first) * 34, 300, 30, E.vm.choices[i].text,
                            B_CHOICE + i);
                    b[n - 1].hot = i == E.menu_sel;
                }
            } else {
                static const char *labels[] = {"Log", "Auto", "Skip", "Save", "Load", "Menu"};
                bool can_save = E.vm.state == VM_SAY || E.vm.state == VM_PAUSE;
                for (int i = 0; i < 6; i++) {
                    n = add(b, n, max, 4 + i * 52.6f, 202, 48.6f, 34, labels[i], B_LOG + i);
                    if (i == 1)
                        b[n - 1].on = E.auto_mode;
                    if (i == 2)
                        b[n - 1].on = E.skip_toggle;
                    if (i == 3)
                        b[n - 1].disabled = !can_save;
                }
            }
            break;
        case OV_LOG:
            n = add(b, n, max, 4, 204, 120, 32, "Back", B_BACK);
            n = add(b, n, max, 190, 204, 60, 32, "Older", B_LOG_UP);
            n = add(b, n, max, 256, 204, 60, 32, "Newer", B_LOG_DOWN);
            break;
        case OV_SAVE:
        case OV_LOAD:
            return slot_buttons(b, n, max);
        case OV_PREFS:
            for (int r = 0; r < 6; r++) {
                n = add(b, n, max, 222, 26 + r * 26, 40, 24, "-", B_PREF_DEC + r);
                n = add(b, n, max, 270, 26 + r * 26, 40, 24, "+", B_PREF_INC + r);
            }
            n = add(b, n, max, 10, 186, 300, 24, PREF_NAMES[6], B_TO_TITLE);
            b[n - 1].hot = E.prefs_sel == 6;
            n = add(b, n, max, 10, 212, 300, 24, PREF_NAMES[7], B_BACK);
            b[n - 1].hot = E.prefs_sel == 7;
            break;
        }
        break;
    case SCR_ERROR:
        n = add(b, n, max, 110, 196, 100, 36, "OK", B_BACK);
        break;
    }
    return n;
}

static void open_slots(Overlay ov)
{
    E.overlay = ov;
    E.slot_sel = 0;
    save_scan(E.slot_page, E.slots);
}

static void pref_change(int row, int dir)
{
    Settings *s = &E.set;
    switch (row) {
    case 0: s->text_speed = (int)clampf((float)(s->text_speed + dir), 0, (float)(NUM_TEXT_SPEEDS - 1)); break;
    case 1: s->auto_delay = clampf(s->auto_delay + 0.5f * (float)dir, 0.5f, 5.0f); break;
    case 2: s->depth_mult = clampf(s->depth_mult + 0.25f * (float)dir, 0.0f, 2.0f); break;
    case 3: s->box_alpha = clampf(s->box_alpha + 0.1f * (float)dir, 0.2f, 1.0f); break;
    case 4:
        s->music_vol = clampf(s->music_vol + 0.1f * (float)dir, 0, 1);
        audio_set_volume(CH_MUSIC, s->music_vol);
        break;
    case 5:
        s->sound_vol = clampf(s->sound_vol + 0.1f * (float)dir, 0, 1);
        audio_set_volume(CH_SOUND, s->sound_vol);
        audio_set_volume(CH_VOICE, s->sound_vol);
        break;
    }
}

static void close_overlay(void)
{
    if (E.overlay == OV_PREFS)
        settings_save();
    E.overlay = OV_NONE;
}

void ui_activate(int id)
{
    char msg[64];
    if (id >= B_MG && id < B_MG + 16 && E.screen == SCR_MGMENU) {
        E.mg_sel = id - B_MG;
        if (E.mg_board)
            ui_mg_board();   /* with the leaderboard up, a tap just switches games */
        else if (mg_at(E.mg_sel))
            mg_begin(mg_at(E.mg_sel), false);
        return;
    }
    if (id >= B_GAME) {
        app_load_game(id - B_GAME);
        return;
    }
    if (id >= B_PREF_INC) {
        E.prefs_sel = id - B_PREF_INC;
        pref_change(id - B_PREF_INC, 1);
        return;
    }
    if (id >= B_PREF_DEC) {
        E.prefs_sel = id - B_PREF_DEC;
        pref_change(id - B_PREF_DEC, -1);
        return;
    }
    if (id >= B_SLOT) {
        int i = id - B_SLOT;
        int slot = E.slot_page * SLOTS_PER_PAGE + i + 1;
        E.slot_sel = i;
        if (E.overlay == OV_SAVE) {
            bool ok = save_write(slot);
            snprintf(msg, sizeof(msg), ok ? "Saved to slot %d" : "Could not save to slot %d", slot);
            app_toast(msg);
            save_scan(E.slot_page, E.slots);
        } else if (E.overlay == OV_LOAD) {
            if (E.slots[i].used)
                app_load_slot(slot);
            else
                app_toast("That slot is empty");
        }
        return;
    }
    if (id >= B_CHOICE) {
        app_choose(id - B_CHOICE);
        return;
    }
    switch (id) {
    case B_RECEIVE: app_receive_open(); break;
    case B_RECEIVE_DONE: app_receive_close(); break;
    case B_TITLE_START: app_new_game(); break;
    case B_TITLE_LOAD: E.slot_page = 0; open_slots(OV_LOAD); break;
    case B_TITLE_GAMES:   /* always available: the list is where Receive lives */
        E.screen = SCR_GAMELIST;
        break;
    case B_TITLE_QUIT: E.quit = true; break;
    case B_TITLE_MINI: E.screen = SCR_MGMENU; break;
    case B_MG_BACK:
        if (E.mg_board)
            E.mg_board = false;
        else
            E.screen = SCR_TITLE;
        break;
    case B_MG_BOARD: ui_mg_board(); break;
    case B_LOG: E.overlay = OV_LOG; E.log_scroll = 0; break;
    case B_AUTO: E.auto_mode = !E.auto_mode; break;
    case B_SKIP: E.skip_toggle = !E.skip_toggle; break;
    case B_SAVE: open_slots(OV_SAVE); break;
    case B_LOAD: open_slots(OV_LOAD); break;
    case B_MENU: E.overlay = OV_PREFS; E.prefs_sel = 0; break;
    case B_BACK:
        if (E.screen == SCR_ERROR)
            E.screen = E.loaded ? SCR_TITLE : SCR_GAMELIST;
        else
            close_overlay();
        break;
    case B_PAGE_PREV:
        E.slot_page = (E.slot_page + SLOT_PAGES - 1) % SLOT_PAGES;
        save_scan(E.slot_page, E.slots);
        break;
    case B_PAGE_NEXT:
        E.slot_page = (E.slot_page + 1) % SLOT_PAGES;
        save_scan(E.slot_page, E.slots);
        break;
    case B_LOG_UP:
        if (E.log_scroll < E.hist_n - 1)
            E.log_scroll++;
        break;
    case B_LOG_DOWN:
        if (E.log_scroll > 0)
            E.log_scroll--;
        break;
    case B_TO_TITLE:
        settings_save();
        app_to_title();
        break;
    }
}

void ui_overlay_input(const Input *in)
{
    u32 d = in->down;
    static float cpad_acc;
    switch (E.overlay) {
    case OV_LOG:
        cpad_acc += in->cy * 0.25f;
        if (d & KEY_UP_ || cpad_acc > 1) {
            ui_activate(B_LOG_UP);
            cpad_acc = 0;
        }
        if (d & KEY_DOWN_ || cpad_acc < -1) {
            ui_activate(B_LOG_DOWN);
            cpad_acc = 0;
        }
        if (d & (KEY_B_ | KEY_Y_))
            close_overlay();
        break;
    case OV_SAVE:
    case OV_LOAD:
        if (d & KEY_LEFT_ || d & KEY_RIGHT_)
            E.slot_sel ^= 1;
        if (d & KEY_UP_)
            E.slot_sel = (E.slot_sel + SLOTS_PER_PAGE - 2) % SLOTS_PER_PAGE;
        if (d & KEY_DOWN_)
            E.slot_sel = (E.slot_sel + 2) % SLOTS_PER_PAGE;
        if (d & KEY_L_)
            ui_activate(B_PAGE_PREV);
        if (d & KEY_R_)
            ui_activate(B_PAGE_NEXT);
        if (d & KEY_A_)
            ui_activate(B_SLOT + E.slot_sel);
        else if (d & (KEY_B_ | KEY_X_))
            close_overlay();
        break;
    case OV_PREFS:
        if (d & KEY_UP_)
            E.prefs_sel = (E.prefs_sel + NUM_PREFS - 1) % NUM_PREFS;
        if (d & KEY_DOWN_)
            E.prefs_sel = (E.prefs_sel + 1) % NUM_PREFS;
        if (E.prefs_sel < 6) {
            if (d & KEY_LEFT_)
                pref_change(E.prefs_sel, -1);
            if (d & KEY_RIGHT_)
                pref_change(E.prefs_sel, 1);
        }
        if (d & KEY_A_) {
            if (E.prefs_sel == 6)
                ui_activate(B_TO_TITLE);
            else if (E.prefs_sel == 7)
                close_overlay();
        }
        if (d & (KEY_B_ | KEY_START_))
            close_overlay();
        break;
    default:
        break;
    }
}

/* ---- top screen -------------------------------------------------------- */

static void draw_toast(int eye)
{
    if (E.toast_t <= 0)
        return;
    float a = clampf(E.toast_t / 0.3f, 0, 1);
    float dx = shift(eye, ui_depth() - 0.1f);
    float w = gfx_text_width(E.toast, 0.5f) + 20;
    gfx_rect(200 - w / 2 + dx, 8, w, 22, rgba_alpha(PANEL(0.85f), a));
    gfx_text(E.toast, 210 - w / 2 + dx, 11, 0.5f, rgba_alpha(WHITE, a));
}

static void draw_choices_top(int eye, bool caption)
{
    const VM *vm = &E.vm;
    float top = 10, bottom = caption ? 140 : 230;
    float h = 22, gap = 5;
    int n = vm->nchoices;
    int vis = (int)((bottom - top + gap) / (h + gap));
    if (vis > n)
        vis = n;
    int first = list_window(E.menu_sel, n, vis);
    float total = vis * (h + gap) - gap;
    float y = top + (bottom - top - total) / 2;
    float dx = shift(eye, ui_depth() - 0.15f);
    for (int i = first; i < first + vis; i++, y += h + gap) {
        bool sel = i == E.menu_sel;
        gfx_rect(50 + dx, y, 300, h, sel ? RGBA(255, 255, 255, 235) : PANEL(0.8f));
        const char *t = vm->choices[i].text;
        float sc = fit_scale(t, 0.5f, 288);
        gfx_text(t, 200 - gfx_text_width(t, sc) / 2 + dx, y + (h - gfx_line_height(sc)) / 2, sc,
                 sel ? BLACK : WHITE);
    }
}

static void draw_dialogue(int eye)
{
    const VM *vm = &E.vm;
    bool say = vm->state == VM_SAY && !E.tr.active;
    bool menu = vm->state == VM_MENU;
    bool has_text = say || (menu && vm->say_text[0]);
    const CharDef *c = &E.game.chars[vm->say_char];
    float d = ui_depth();

    char vis[VM_TEXT * 2];
    size_t off = utf8_offset(E.wrapped, (size_t)E.text_shown);
    if (off >= sizeof(vis))
        off = sizeof(vis) - 1;
    memcpy(vis, E.wrapped, off);
    vis[off] = 0;

    if (has_text && c->kind == CHR_CENTERED) {
        float lh = gfx_line_height(E.text_scale);
        float y = (TOP_H - ui_count_lines(E.wrapped) * lh) / 2;
        float dx = shift(eye, d * 0.6f);
        text_centered(vis, 201 + dx, y + 1, E.text_scale, BLACK);
        text_centered(vis, 200 + dx, y, E.text_scale, c->text_color);
    } else if (has_text || (E.window_mode == WIN_SHOW && !E.tr.active)) {
        float dx = shift(eye, d);
        gfx_rect(6 + dx, 164, 388, 72, PANEL(E.set.box_alpha));
        gfx_rect(6 + dx, 164, 388, 1, RGBA(255, 255, 255, 70));
        if (has_text) {
            if (vm->say_who[0]) {
                float nd = shift(eye, d - 0.08f);
                float sc = 0.55f;
                float nw = gfx_text_width(vm->say_who, sc) + 14;
                gfx_rect(12 + nd, 144, nw, 20, PANEL(fminf(1, E.set.box_alpha + 0.1f)));
                gfx_text(vm->say_who, 19 + nd, 144 + (20 - gfx_line_height(sc)) / 2, sc,
                         c->name_color);
            }
            gfx_text(vis, 14 + dx, 169, E.text_scale, c->text_color);
            if (say && E.text_done) {
                float a = 0.55f + 0.45f * sinf(E.time * 6);
                gfx_rect(381 + dx, 225, 6, 6, rgba_alpha(WHITE, a));
            }
        }
    }
    if (menu)
        draw_choices_top(eye, has_text);

    const char *mode = E.skip ? "Skip >>" : (E.auto_mode ? "Auto" : NULL);
    if (mode) {
        float dx = shift(eye, d);
        float w = gfx_text_width(mode, 0.45f) + 12;
        gfx_rect(394 - w + dx, 6, w, 18, PANEL(0.7f));
        gfx_text(mode, 400 - w + dx, 8, 0.45f, WHITE);
    }
}

/* ---- minigame leaderboard ------------------------------------------------ */

void ui_mg_board(void)
{
    const MiniGame *g = mg_at(E.mg_sel);
    E.mg_board = true;
    if (g)
        lb_fetch_top(g->id);
}

/* The selected game's online top 10 on the left, the player's own name and
 * local best on the right. */
static void draw_board_top(int eye)
{
    const MiniGame *g = mg_at(E.mg_sel);
    const u32 GOLD = RGBA(255, 210, 110, 255), DIM = RGBA(190, 190, 215, 255);
    char buf[300];
    if (!g)
        return;
    gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(24, 20, 44, 255), RGBA(70, 40, 90, 255));
    snprintf(buf, sizeof(buf), "%s: online top %d", g->title, LB_TOP_MAX);
    float sc = fit_scale(buf, 0.62f, 380);
    gfx_text(buf, 200 - gfx_text_width(buf, sc) / 2 + shift(eye, -0.3f), 10, sc, GOLD);

    /* the list, or what is going on instead */
    float dx = shift(eye, -0.15f);
    const char *msg = NULL;
    if (!lb_online())
        msg = "The online leaderboard is off.\nTo turn it on, add the line\nurl = http://<server>\n"
              "to leaderboard.cfg in the\nvn3ds folder.";
    else if (!lb_top_is(g->id) || LB_TOP.state == LB_BUSY || LB_TOP.state == LB_IDLE)
        msg = "Loading...";
    else if (LB_TOP.state == LB_FAILED) {
        char why[200];
        ui_wrap(LB_TOP.error, 240, 0.45f, why, sizeof(why));
        snprintf(buf, sizeof(buf), "Could not load the leaderboard.\n\n%s", why);
        msg = buf;
    } else if (LB_TOP.ntop == 0)
        msg = "No scores yet.\nBe the first!";
    if (msg) {
        text_centered(msg, 145 + dx, 90, 0.45f, WHITE);
    } else {
        for (int i = 0; i < LB_TOP.ntop; i++) {
            const LbEntry *e = &LB_TOP.top[i];
            float y = 42 + i * 18;
            u32 c = !strcmp(e->name, lb_name()) ? GOLD : WHITE;
            if (i % 2 == 0)
                gfx_rect(14 + dx, y - 1, 258, 18, RGBA(255, 255, 255, 18));
            snprintf(buf, sizeof(buf), "%d", e->rank);
            gfx_text(buf, 44 - gfx_text_width(buf, 0.5f) + dx, y, 0.5f, DIM);
            gfx_text(e->name, 58 + dx, y, fit_scale(e->name, 0.5f, 160), c);
            snprintf(buf, sizeof(buf), "%d%%", e->score);
            gfx_text(buf, 264 - gfx_text_width(buf, 0.5f) + dx, y, 0.5f, c);
        }
    }

    /* you */
    float px = 284 + shift(eye, -0.25f);
    gfx_rect(px, 42, 104, 150, RGBA(255, 255, 255, 30));
    gfx_text("Playing as", px + 8, 50, 0.42f, DIM);
    gfx_text(lb_name(), px + 8, 66, fit_scale(lb_name(), 0.52f, 90), WHITE);
    gfx_text("Your best", px + 8, 104, 0.42f, DIM);
    int best = mg_best(g->id);
    if (best >= 0)
        snprintf(buf, sizeof(buf), "%d%%", best);
    else
        snprintf(buf, sizeof(buf), "-");
    gfx_text(buf, px + 8, 120, 0.9f, GOLD);
    if (lb_online() && LB_POST.state == LB_DONE && !strcmp(LB_POST.game, g->id)) {
        snprintf(buf, sizeof(buf), "Online #%d of %d", LB_POST.rank, LB_POST.total);
        gfx_text(buf, px + 8, 166, fit_scale(buf, 0.42f, 90), DIM);
    }
}

static void draw_title_top(int eye)
{
    const Game *g = &E.game;
    if (g->title_image >= 0 && (u32)g->title_image < g->nimages) {
        Sprite s;
        memset(&s, 0, sizeof(s));
        xform_default(&s.xf);
        s.xf.v[P_XPOS] = s.xf.v[P_XANCHOR] = 0.5f;
        s.xf.v[P_YPOS] = s.xf.v[P_YANCHOR] = 0.5f;
        s.image = g->title_image;
        s.from_scene = 1;
        render_sprite(&s, eye, 0, 0, 0);
    } else {
        gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(40, 30, 80, 255), RGBA(150, 80, 120, 255));
    }
    float dx = shift(eye, -0.5f);
    float sc = fit_scale(g->title, 1.0f, 360);
    float y = 70;
    gfx_text(g->title, 202 - gfx_text_width(g->title, sc) / 2 + dx, y + 2, sc, RGBA(0, 0, 0, 160));
    gfx_text(g->title, 200 - gfx_text_width(g->title, sc) / 2 + dx, y, sc, WHITE);
    if (g->version && g->version[0]) {
        float w = gfx_text_width(g->version, 0.4f);
        gfx_text(g->version, 394 - w + shift(eye, -0.2f), 222, 0.4f, RGBA(255, 255, 255, 180));
    }
}

void ui_draw_top(int eye)
{
    switch (E.screen) {
    case SCR_GAMELIST: {
        gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(25, 30, 60, 255), RGBA(70, 40, 90, 255));
        for (int i = 0; i < 6; i++) {
            float dx = shift(eye, 1.0f - i * 0.3f);
            gfx_rect(40 + i * 56 + dx, 150 - i * 12, 40, 40, RGBA(255, 255, 255, 30 + i * 20));
        }
        float dx = shift(eye, -0.5f);
        text_centered("vn3ds", 200 + dx, 50, 1.2f, WHITE);
        const char *sub = E.ngames ? E.game_titles[E.game_sel] : "No games found";
        text_centered(sub, 200 + shift(eye, -0.25f), 110, fit_scale(sub, 0.6f, 360), RGBA(255, 230, 200, 255));
        break;
    }
    case SCR_TITLE:
        draw_title_top(eye);
        break;
    case SCR_MINIGAME:
        mg_draw_top(eye);
        break;
    case SCR_MGMENU: {
        if (E.mg_board) {
            draw_board_top(eye);
            break;
        }
        gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(24, 20, 44, 255), RGBA(70, 40, 90, 255));
        const MiniGame *g = mg_at(E.mg_sel);
        text_centered("Minigames", 200 + shift(eye, -0.3f), 20, 0.8f, RGBA(255, 210, 110, 255));
        if (g) {
            text_centered(g->title, 200 + shift(eye, -0.2f), 70, 0.7f, WHITE);
            char wrapped[600];
            ui_wrap(g->rules, 360, 0.45f, wrapped, sizeof(wrapped));
            text_centered(wrapped, 200 + shift(eye, -0.05f), 110, 0.45f, RGBA(220, 220, 255, 255));
        }
        break;
    }
    case SCR_GAME:
        render_scene(eye);
        if (!E.hide_ui)
            draw_dialogue(eye);
        break;
    case SCR_RECEIVE: {
        gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(15, 30, 55, 255), RGBA(40, 60, 100, 255));
        float dx = shift(eye, -0.3f);
        text_centered("Receive over Wi-Fi", 200 + dx, 22, 0.8f, WHITE);
        char line[200];
        if (NET.listening) {
            snprintf(line, sizeof(line), "On your computer:\nvn3ds-port <game> --3ds %s", NET.address);
            text_centered(line, 200 + shift(eye, -0.15f), 70, 0.5f, RGBA(200, 230, 255, 255));
        }
        text_centered(NET.message, 200 + dx, 128, 0.5f, RGBA(255, 230, 180, 255));
        if (NET.bytes_total > 0) {
            float p = (float)((double)NET.bytes_done / (double)NET.bytes_total);
            float bx = 50 + shift(eye, -0.2f);
            gfx_rect(bx, 160, 300, 12, RGBA(255, 255, 255, 50));
            gfx_rect(bx, 160, 300 * clampf(p, 0, 1), 12, RGBA(120, 200, 255, 255));
            snprintf(line, sizeof(line), "%u / %u files  -  %.1f / %.1f MB", (unsigned)NET.files_done,
                     (unsigned)NET.files_total, NET.bytes_done / 1048576.0, NET.bytes_total / 1048576.0);
            text_centered(line, 200 + dx, 180, 0.45f, WHITE);
        }
        if (NET.engine_updated)
            text_centered("vn3ds was updated - restart it to use the new version", 200 + dx, 205, 0.42f,
                          RGBA(255, 210, 120, 255));
        break;
    }
    case SCR_ERROR: {
        gfx_rect(0, 0, TOP_W, TOP_H, RGBA(40, 10, 10, 255));
        char wrapped[600];
        ui_wrap(E.error, 360, 0.5f, wrapped, sizeof(wrapped));
        gfx_text("Something went wrong", 20, 20, 0.7f, RGBA(255, 160, 160, 255));
        gfx_text(wrapped, 20, 60, 0.5f, WHITE);
        break;
    }
    }
    draw_toast(eye);
}

/* ---- bottom screen ------------------------------------------------------- */

static void draw_button(const Button *b)
{
    u32 bg = b->hot ? RGBA(255, 255, 255, 235) : (b->on ? RGBA(80, 130, 220, 255) : RGBA(255, 255, 255, 34));
    u32 fg = b->hot ? BLACK : WHITE;
    float a = b->disabled ? 0.35f : 1.0f;
    gfx_rect(b->x, b->y, b->w, b->h, rgba_alpha(bg, a * (float)(bg & 0xFF) / 255.0f));
    gfx_rect(b->x, b->y + b->h - 1, b->w, 1, RGBA(0, 0, 0, 90));
    float sc = fit_scale(b->label, 0.5f, b->w - 8);
    float lh = gfx_line_height(sc);
    gfx_text(b->label, b->x + (b->w - gfx_text_width(b->label, sc)) / 2, b->y + (b->h - lh) / 2,
             sc, rgba_alpha(fg, a));
}

static void header(const char *text)
{
    gfx_rect(0, 0, BOT_W, 22, RGBA(0, 0, 0, 110));
    gfx_text(text, 6, 3, fit_scale(text, 0.48f, 240), RGBA(220, 220, 235, 255));
    float s = gfx_slider();
    gfx_text("3D", 262, 4, 0.42f, RGBA(200, 200, 210, 255));
    gfx_rect(282, 8, 32, 6, RGBA(255, 255, 255, 40));
    gfx_rect(282, 8, 32 * s * fminf(1, E.set.depth_mult), 6, RGBA(120, 200, 255, 255));
}

/* History, newest at the bottom of [top, bottom). */
static void draw_history(float top, float bottom, int skip, bool fade)
{
    float sc = 0.44f;
    float lh = gfx_line_height(sc);
    float y = bottom;
    char wrapped[700];
    for (int i = E.hist_n - 1 - skip; i >= 0 && y > top; i--) {
        const HistEntry *h = &E.hist[i];
        ui_wrap(h->text, 300, sc, wrapped, sizeof(wrapped));
        int lines = ui_count_lines(wrapped) + (h->who[0] ? 1 : 0);
        y -= lines * lh + 6;
        float age = (float)(E.hist_n - 1 - skip - i);
        float a = fade ? clampf(1.0f - age * 0.25f, 0.25f, 1.0f) : 1.0f;
        float ty = y;
        if (ty + lines * lh < top)
            break;
        if (h->who[0]) {
            if (ty >= top)
                gfx_text(h->who, 10, ty, sc, rgba_alpha(h->who_color, a));
            ty += lh;
        }
        /* draw line by line so partially visible entries clip cleanly */
        const char *p = wrapped;
        char line[512];
        while (*p) {
            size_t n = strcspn(p, "\n");
            size_t c = n < sizeof(line) - 1 ? n : sizeof(line) - 1;
            memcpy(line, p, c);
            line[c] = 0;
            if (ty >= top)
                gfx_text(line, 14, ty, sc, rgba_alpha(RGBA(235, 235, 240, 255), a));
            ty += lh;
            p += n;
            if (*p == '\n')
                p++;
        }
    }
}

static void draw_slots(const char *title)
{
    char head[64];
    snprintf(head, sizeof(head), "%s  -  page %d/%d", title, E.slot_page + 1, SLOT_PAGES);
    header(head);
    Button b[16];
    int n = ui_buttons(b, 16);
    for (int i = 0; i < n; i++) {
        if (b[i].id < B_SLOT || b[i].id >= B_SLOT + SLOTS_PER_PAGE) {
            draw_button(&b[i]);
            continue;
        }
        const SlotInfo *s = &E.slots[b[i].id - B_SLOT];
        bool hot = b[i].hot;
        gfx_rect(b[i].x, b[i].y, b[i].w, b[i].h, hot ? RGBA(255, 255, 255, 230) : RGBA(255, 255, 255, 30));
        u32 fg = hot ? BLACK : WHITE;
        gfx_text(b[i].label, b[i].x + 5, b[i].y + 3, 0.45f, fg);
        if (s->used) {
            char when[32];
            time_t t = (time_t)s->time;
            struct tm *tm = localtime(&t);
            if (tm)
                strftime(when, sizeof(when), "%Y-%m-%d %H:%M", tm);
            else
                snprintf(when, sizeof(when), "?");
            gfx_text(when, b[i].x + 26, b[i].y + 4, 0.38f, hot ? RGBA(60, 60, 60, 255) : RGBA(180, 180, 190, 255));
            char wrapped[200];
            ui_wrap(s->preview, b[i].w - 10, 0.36f, wrapped, sizeof(wrapped));
            /* first two lines only */
            char *nl = strchr(wrapped, '\n');
            if (nl && (nl = strchr(nl + 1, '\n')))
                *nl = 0;
            gfx_text(wrapped, b[i].x + 5, b[i].y + 20, 0.36f, fg);
        } else {
            gfx_text(s->preview[0] ? s->preview : "empty", b[i].x + 26, b[i].y + 4, 0.38f,
                     hot ? RGBA(90, 90, 90, 255) : RGBA(140, 140, 150, 255));
        }
    }
}

static void pref_value(int row, char *out, size_t len)
{
    const Settings *s = &E.set;
    switch (row) {
    case 0:
        if (TEXT_SPEEDS[s->text_speed] <= 0)
            snprintf(out, len, "Instant");
        else
            snprintf(out, len, "%.0f cps", TEXT_SPEEDS[s->text_speed]);
        break;
    case 1: snprintf(out, len, "%.1f s", s->auto_delay); break;
    case 2: snprintf(out, len, "x%.2f", s->depth_mult); break;
    case 3: snprintf(out, len, "%.0f%%", s->box_alpha * 100); break;
    case 4: snprintf(out, len, "%.0f%%", s->music_vol * 100); break;
    case 5: snprintf(out, len, "%.0f%%", s->sound_vol * 100); break;
    default: out[0] = 0;
    }
}

void ui_draw_bottom(void)
{
    gfx_gradient(0, 0, BOT_W, BOT_H, RGBA(34, 34, 50, 255), RGBA(16, 16, 24, 255));
    Button b[48];
    int n;
    switch (E.screen) {
    case SCR_RECEIVE:
        header("Wi-Fi");
        {
            char msg[400], wrapped[500];
            snprintf(msg, sizeof(msg), "Keep this screen open while your computer sends games. "
                     "Both must be on the same Wi-Fi network.\n\nPort %d", NET.port);
            ui_wrap(msg, 300, 0.45f, wrapped, sizeof(wrapped));
            gfx_text(wrapped, 10, 34, 0.45f, WHITE);
            if (E.ngames)
                gfx_text("Received games appear in the list.", 10, 150, 0.42f, RGBA(180, 220, 255, 255));
        }
        break;
    case SCR_GAMELIST:
        header("vn3ds  -  choose a game");
        if (E.ngames == 0) {
            char msg[400], wrapped[500];
            snprintf(msg, sizeof(msg),
                     "No games yet. Press Y to receive one over Wi-Fi, or copy games made with "
                     "vn3ds-port to\n%s/games/\n\nSTART: exit", E.root);
            ui_wrap(msg, 300, 0.5f, wrapped, sizeof(wrapped));
            gfx_text(wrapped, 10, 40, 0.5f, WHITE);
        }
        break;
    case SCR_TITLE:
        header(E.game.title);
        if (E.overlay == OV_LOAD) {
            draw_slots("Load");
            return;
        }
        break;
    case SCR_GAME:
        switch (E.overlay) {
        case OV_NONE:
            header(E.game.title);
            if (E.vm.state != VM_MENU)
                draw_history(26, 196, 0, true);
            break;
        case OV_LOG: {
            char head[48];
            snprintf(head, sizeof(head), "History (%d)", E.hist_n);
            header(head);
            draw_history(26, 198, E.log_scroll, false);
            break;
        }
        case OV_SAVE: draw_slots("Save"); return;
        case OV_LOAD: draw_slots("Load"); return;
        case OV_PREFS:
            header("Settings");
            for (int r = 0; r < 6; r++) {
                float y = 26 + r * 26;
                if (r == E.prefs_sel)
                    gfx_rect(4, y, 312, 24, RGBA(255, 255, 255, 40));
                char v[32];
                pref_value(r, v, sizeof(v));
                gfx_text(PREF_NAMES[r], 10, y + 4, 0.48f, WHITE);
                gfx_text(v, 140, y + 4, 0.48f, RGBA(180, 220, 255, 255));
            }
            break;
        }
        break;
    case SCR_ERROR:
        header("Error");
        gfx_text("Press A to continue.", 10, 40, 0.5f, WHITE);
        break;
    case SCR_MINIGAME:
        mg_draw_bottom();
        return;
    case SCR_MGMENU:
        header(E.mg_board ? "Online leaderboard" : "Minigames: best scores");
        break;
    }
    n = ui_buttons(b, 48);
    for (int i = 0; i < n; i++)
        draw_button(&b[i]);
}
