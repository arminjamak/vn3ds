/* The download page: the one-command converter for Mac and Windows. */
#define VN3DS_SITE "arminjamak.github.io/vn3ds"

#include "app.h"
#include "leaderboard.h"
#include "minigame.h"
#include "net.h"

#include <time.h>

enum {
    B_TITLE_START = 1, B_TITLE_LOAD = 2, B_TITLE_GAMES = 3, B_TITLE_QUIT = 4, B_TITLE_MINI = 5,
    B_TITLE_CONTINUE = 6, B_HOME_PLAY = 50, B_HOME_PREV, B_HOME_NEXT, B_HOME_TITLE,
    B_MG = 60, B_MG_BACK = 90, B_MG_BOARD = 91,
    B_LOG = 10, B_AUTO, B_SKIP, B_SAVE, B_LOAD, B_MENU,
    B_BACK = 20, B_PAGE_PREV, B_PAGE_NEXT, B_LOG_UP, B_LOG_DOWN,
    B_TO_TITLE = 30,
    B_RECEIVE = 40, B_RECEIVE_DONE,
    B_CHOICE = 100, B_SLOT = 200, B_PREF_DEC = 300, B_PREF_INC = 320, B_GAME = 400,
};

/* ---- style: black and white, rounded ------------------------------------ */

#define WHITE 0xFFFFFFFFu
#define BLACK 0x000000FFu
#define INK2 RGBA(152, 152, 159, 255)   /* secondary text */
#define INK3 RGBA(99, 99, 104, 255)     /* tertiary text, empty things */
#define FILL1 RGBA(28, 28, 30, 255)     /* cards and grouped lists */
#define FILL2 RGBA(44, 44, 46, 255)     /* buttons */
#define FILL3 RGBA(64, 64, 68, 255)     /* tracks, toggles that are on */
#define HAIRLINE RGBA(255, 255, 255, 24)
/* the translucent "glass" laid over the scene on the top screen */
#define PANEL(a) RGBA(14, 14, 16, (u32)((a) * 255))
#define R_BUTTON 10.0f   /* corner radius of buttons and cards */

static inline float eye_sign(int eye) { return eye == EYE_LEFT ? -1.0f : 1.0f; }
/* Horizontal shift for something at `depth` seen by `eye`. */
static inline float shift(int eye, float depth) { return eye_sign(eye) * depth * app_strength(); }

static float ui_depth(void) { return E.loaded ? E.game.depth_ui : -0.35f; }

/* A filled rounded rectangle, drawn as one triangle fan so that translucent
 * fills never blend twice where pieces would overlap. */
void ui_rrect(float x, float y, float w, float h, float r, u32 c)
{
    if (w <= 0 || h <= 0 || !(c & 0xFF))
        return;
    r = fminf(r, fminf(w, h) / 2);
    if (r < 1) {
        gfx_rect(x, y, w, h, c);
        return;
    }
    int seg = r < 5 ? 3 : r < 12 ? 5 : 7;
    const float cxs[4] = {x + w - r, x + w - r, x + r, x + r}, cys[4] = {y + r, y + h - r, y + h - r, y + r};
    float mx = x + w / 2, my = y + h / 2, px = 0, py = 0, fx = 0, fy = 0;
    for (int k = 0; k < 4; k++)
        for (int j = 0; j <= seg; j++) {
            float a = ((float)k - 1 + (float)j / (float)seg) * (float)M_PI / 2;   /* from -90 degrees */
            float vx = cxs[k] + r * cosf(a), vy = cys[k] + r * sinf(a);
            if (k == 0 && j == 0) {
                fx = vx;
                fy = vy;
            } else {
                gfx_triangle(mx, my, px, py, vx, vy, c);
            }
            px = vx;
            py = vy;
        }
    gfx_triangle(mx, my, px, py, fx, fy, c);
}

/* Fills the outside of each rounded corner: laid over a picture's square
 * corners it rounds them (pictures can't be clipped), in the colour of
 * what is behind (`top` for the upper corners, `bottom` for the lower). */
static void round_corners(float x, float y, float w, float h, float r, u32 top, u32 bottom)
{
    const float px[4] = {x, x + w, x + w, x}, py[4] = {y, y, y + h, y + h};
    const float cx[4] = {x + r, x + w - r, x + w - r, x + r}, cy[4] = {y + r, y + r, y + h - r, y + h - r};
    for (int k = 0; k < 4; k++) {
        u32 c = k < 2 ? top : bottom;
        float a0 = (float)M_PI * (k == 0 ? 1.0f : k == 1 ? 1.5f : k == 2 ? 0.0f : 0.5f);
        float lx = cx[k] + r * cosf(a0), ly = cy[k] + r * sinf(a0);
        for (int j = 1; j <= 5; j++) {
            float a = a0 + (float)M_PI / 2 * (float)j / 5;
            float vx = cx[k] + r * cosf(a), vy = cy[k] + r * sinf(a);
            gfx_triangle(px[k], py[k], lx, ly, vx, vy, c);
            lx = vx;
            ly = vy;
        }
    }
}

/* A thin horizontal bar with round ends: progress, the 3D meter. */
static void progress_bar(float x, float y, float w, float h, float p, u32 track, u32 fill)
{
    ui_rrect(x, y, w, h, h / 2, track);
    if (p > 0)
        ui_rrect(x, y, fmaxf(h, w * clampf(p, 0, 1)), h, h / 2, fill);
}

static u32 mix(u32 a, u32 b, float t)
{
    t = clampf(t, 0, 1);
    u32 out = 0;
    for (int sh = 0; sh < 32; sh += 8) {
        float ca = (float)((a >> sh) & 0xFF), cb = (float)((b >> sh) & 0xFF);
        out |= (u32)(ca + (cb - ca) * t + 0.5f) << sh;
    }
    return out;
}

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
    if (app_has_resume())
        ids[n++] = B_TITLE_CONTINUE;
    ids[n++] = B_TITLE_START;
    ids[n++] = B_TITLE_LOAD;
    if (E.loaded && E.game.nminigames > 0)
        ids[n++] = B_TITLE_MINI;
    ids[n++] = B_TITLE_GAMES;
    ids[n++] = B_TITLE_QUIT;
    return n;
}

/* The game shown on home card `i` (a new one may still be arriving). */
static const char *home_title(int i)
{
    return i < E.ngames ? E.game_titles[i] : E.rx_new_title;
}

static bool home_arriving(int i)
{
    return i >= E.ngames ? E.rx_new : app_rx_busy(E.games[i]);
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
        n = add(b, n, max, 12, 206, 120, 30, E.mg_board ? "B  Close" : "B  Back", B_MG_BACK);
        n = add(b, n, max, 188, 206, 120, 30, E.mg_board ? "X  Refresh" : "X  Leaderboard",
                B_MG_BOARD);
        break;
    }
    case SCR_RECEIVE:
        n = add(b, n, max, 60, 196, 200, 36, "Done", B_RECEIVE_DONE);
        break;
    case SCR_MINIGAME:   /* minigame.c handles its own touch areas */
        break;
    case SCR_GAMELIST: {
        int count = app_home_count();
        if (count > 0) {
            static char play[48];
            int sel = E.game_sel;
            bool arriving = home_arriving(sel);
            bool resume = sel < E.ngames && E.game_resume[sel].used;
            if (arriving)
                snprintf(play, sizeof(play), "Arriving  %d%%", (int)(app_rx_progress() * 100));
            else
                snprintf(play, sizeof(play), resume ? "A  Continue" : "A  Play");
            n = add(b, n, max, 70, 84, 180, 48, play, B_HOME_PLAY);
            b[n - 1].hot = !arriving;
            b[n - 1].disabled = arriving;
            n = add(b, n, max, 14, 90, 48, 36, "<", B_HOME_PREV);
            b[n - 1].disabled = sel == 0;
            n = add(b, n, max, 258, 90, 48, 36, ">", B_HOME_NEXT);
            b[n - 1].disabled = sel >= count - 1;
            n = add(b, n, max, 10, 200, 146, 34, "X  Title screen", B_HOME_TITLE);
            b[n - 1].disabled = arriving;
        }
        n = add(b, n, max, 164, 200, 146, 34, "Y  Receive", B_RECEIVE);
        break;
    }
    case SCR_TITLE:
        if (E.overlay == OV_LOAD)
            return slot_buttons(b, n, max);
        {
            int ids[6], cnt = ui_title_items(ids);
            float step = cnt > 5 ? 30 : cnt > 4 ? 36 : 44;
            for (int i = 0; i < cnt; i++) {
                const char *label = ids[i] == B_TITLE_CONTINUE ? "Continue" : ids[i] == B_TITLE_START ? "Start" : ids[i] == B_TITLE_LOAD ? "Load"
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
    case B_TITLE_CONTINUE: app_load_slot(RESUME_SLOT); break;
    case B_HOME_PLAY: app_play_game(E.game_sel); break;
    case B_HOME_TITLE: app_load_game(E.game_sel); break;
    case B_HOME_PREV: if (E.game_sel > 0) E.game_sel--; break;
    case B_HOME_NEXT: if (E.game_sel < app_home_count() - 1) E.game_sel++; break;
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
    float sc = fit_scale(E.toast, 0.5f, 330);
    float w = gfx_text_width(E.toast, sc) + 28;
    ui_rrect(200 - w / 2 + dx, 8, w, 24, 12, rgba_alpha(RGBA(44, 44, 46, 242), a));
    gfx_text(E.toast, 214 - w / 2 + dx, 8 + (24 - gfx_line_height(sc)) / 2, sc, rgba_alpha(WHITE, a));
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
        ui_rrect(50 + dx, y, 300, h, h / 2, sel ? RGBA(255, 255, 255, 242) : PANEL(0.78f));
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
        ui_rrect(6 + dx, 164, 388, 72, 12, PANEL(E.set.box_alpha));
        if (has_text) {
            if (vm->say_who[0]) {
                /* the name in a white pill, with the character's colour as a dot */
                float nd = shift(eye, d - 0.08f);
                float sc = 0.5f;
                float nw = gfx_text_width(vm->say_who, sc) + 30;
                ui_rrect(12 + nd, 143, nw, 19, 9.5f, RGBA(255, 255, 255, 242));
                gfx_circle(22 + nd, 152.5f, 3.5f, c->name_color | 0xFF);
                gfx_text(vm->say_who, 30 + nd, 143 + (19 - gfx_line_height(sc)) / 2, sc, BLACK);
            }
            gfx_text(vis, 16 + dx, 170, E.text_scale, c->text_color);
            if (say && E.text_done) {
                float a = 0.55f + 0.45f * sinf(E.time * 6);
                gfx_triangle(379 + dx, 224, 389 + dx, 224, 384 + dx, 230, rgba_alpha(WHITE, a));
            }
        }
    }
    if (menu)
        draw_choices_top(eye, has_text);

    const char *mode = E.skip ? "Skip" : (E.auto_mode ? "Auto" : NULL);
    if (mode) {
        float dx = shift(eye, d) - (NET.receiving ? 32 : 0);   /* room for the download icon */
        float w = gfx_text_width(mode, 0.45f) + 20;
        ui_rrect(394 - w + dx, 7, w, 20, 10, PANEL(0.75f));
        gfx_text(mode, 404 - w + dx, 7 + (20 - gfx_line_height(0.45f)) / 2, 0.45f, WHITE);
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
/* The player's own scores for a game, in a panel: the first story run pinned
 * on top, then the best free-play runs. */
static void draw_my_scores(int eye, const MiniGame *g, float x, float y, float w, float h)
{
    const u32 GOLD = WHITE, DIM = INK2;
    float px = x + shift(eye, -0.25f);
    char buf[64];
    int story, runs[5];
    int n = mg_scores(g->id, &story, runs, 5);
    ui_rrect(px, y, w, h, R_BUTTON, RGBA(255, 255, 255, 22));
    gfx_text("Your scores", px + 10, y + 7, 0.45f, GOLD);
    float ly = y + 28;
    ui_rrect(px + 4, ly - 2, w - 8, 20, 7, RGBA(255, 255, 255, 30));
    gfx_text("Story", px + 10, ly, 0.45f, DIM);
    snprintf(buf, sizeof(buf), story >= 0 ? "%d%%" : "not yet", story);
    gfx_text(buf, px + w - 10 - gfx_text_width(buf, 0.45f), ly, 0.45f, story >= 0 ? WHITE : DIM);
    ly += 24;
    if (n == 0) {
        gfx_text("Free play:\nno runs yet", px + 10, ly, 0.42f, DIM);
        return;
    }
    for (int i = 0; i < n && ly < y + h - 16; i++, ly += 18) {
        snprintf(buf, sizeof(buf), "%d.", i + 1);
        gfx_text(buf, px + 10, ly, 0.45f, DIM);
        snprintf(buf, sizeof(buf), "%d%%", runs[i]);
        gfx_text(buf, px + w - 10 - gfx_text_width(buf, 0.45f), ly, 0.45f, i == 0 ? GOLD : WHITE);
    }
}

static void draw_board_top(int eye)
{
    const MiniGame *g = mg_at(E.mg_sel);
    const u32 GOLD = WHITE, DIM = INK2;
    char buf[300];
    if (!g)
        return;
    gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(30, 30, 32, 255), BLACK);
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
            u32 c = WHITE;
            if (!strcmp(e->name, lb_name()))
                ui_rrect(14 + dx, y - 1, 258, 18, 9, RGBA(255, 255, 255, 40));
            else if (i % 2 == 0)
                ui_rrect(14 + dx, y - 1, 258, 18, 9, RGBA(255, 255, 255, 14));
            snprintf(buf, sizeof(buf), "%d", e->rank);
            gfx_text(buf, 44 - gfx_text_width(buf, 0.5f) + dx, y, 0.5f, DIM);
            gfx_text(e->name, 58 + dx, y, fit_scale(e->name, 0.5f, 160), c);
            snprintf(buf, sizeof(buf), "%d%%", e->score);
            gfx_text(buf, 264 - gfx_text_width(buf, 0.5f) + dx, y, 0.5f, c);
        }
    }

    /* you */
    draw_my_scores(eye, g, 284, 42, 106, 170);
    if (lb_online() && LB_POST.state == LB_DONE && !strcmp(LB_POST.game, g->id)) {
        snprintf(buf, sizeof(buf), "Online #%d of %d", LB_POST.rank, LB_POST.total);
        gfx_text(buf, 290 + shift(eye, -0.25f), 218, fit_scale(buf, 0.42f, 96), DIM);
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
        gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(36, 36, 38, 255), BLACK);
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

static void header(const char *title);

/* ---- home screen: coverflow of where each game was left -------------------- */

/* The home screen's backdrop: a quiet fall from dark grey to black. */
#define HOME_TOP RGBA(30, 30, 32, 255)
#define HOME_BOTTOM RGBA(0, 0, 0, 255)
static u32 home_bg_at(float y) { return mix(HOME_TOP, HOME_BOTTOM, y / TOP_H); }

/* A small download glyph: an arrow into a tray. */
static void download_glyph(float cx, float cy, float s, u32 c)
{
    gfx_line(cx, cy - 6 * s, cx, cy + 1.5f * s, 2.0f * s, c);
    gfx_triangle(cx - 4.5f * s, cy + 0.5f * s, cx + 4.5f * s, cy + 0.5f * s, cx, cy + 5.5f * s, c);
    gfx_rect(cx - 5.5f * s, cy + 7 * s, 11 * s, 1.8f * s, c);
}

static void draw_card(int eye, int i, float o)
{
    float a = fabsf(o);
    float side = o < 0 ? -1.0f : 1.0f;
    float x = 200 + side * (fminf(a, 1.0f) * 128 + fmaxf(a - 1.0f, 0) * 58);
    float k = a < 1 ? 1.0f - 0.4f * a : 0.6f - 0.08f * fminf(a - 1.0f, 2.0f);
    float depth = -0.28f + 0.55f * fminf(a, 1.6f);
    float w = THUMB_W * k, h = THUMB_H * k, r = 9 * k + 2;
    float cx = x + shift(eye, depth), cy = 98 - (1 - fminf(a, 1)) * 6;
    float fade = clampf(1.6f - (a - 1.0f), 0, 1);
    float x0 = cx - w / 2, y0 = cy - h / 2;
    bool chosen = a < 0.5f;
    GfxTex *thumb = i < E.ngames ? E.game_thumb[i] : NULL;
    if (chosen)   /* a white edge around the chosen card */
        ui_rrect(x0 - 2.5f, y0 - 2.5f, w + 5, h + 5, r + 2.5f, rgba_alpha(WHITE, fade));
    if (thumb) {
        gfx_image(thumb, x0, y0, w, h, 0, fade);
        if (chosen)
            round_corners(x0, y0, w, h, r, WHITE, WHITE);
        else
            round_corners(x0, y0, w, h, r, home_bg_at(y0), home_bg_at(y0 + h));
    } else {
        ui_rrect(x0, y0, w, h, r, rgba_alpha(FILL2, fade));
        text_centered(home_title(i), cx, cy - (home_arriving(i) ? 2 : 10) * k,
                      fit_scale(home_title(i), 0.55f * k, w - 16), rgba_alpha(WHITE, fade));
    }
    if (home_arriving(i)) {   /* still on its way: a glyph and how far along it is */
        if (thumb)
            ui_rrect(x0, y0, w, h, r, RGBA(0, 0, 0, (u8)(120 * fade)));
        download_glyph(cx, cy - (thumb ? 6 : 24) * k, k, rgba_alpha(WHITE, fade));
        progress_bar(x0 + 14 * k, y0 + h - 16 * k, w - 28 * k, 4, app_rx_progress(),
                     RGBA(255, 255, 255, (u8)(60 * fade)), rgba_alpha(WHITE, fade));
    }
    if (a > 0.5f)   /* side cards sit back and darker */
        ui_rrect(x0, y0, w, h, r, RGBA(0, 0, 0, (u8)(120 * fminf(a, 1) * fade)));
}

static void draw_coverflow(int eye)
{
    gfx_gradient(0, 0, TOP_W, TOP_H, HOME_TOP, HOME_BOTTOM);
    int n = app_home_count();
    if (n == 0) {
        text_centered("vn3ds", 200 + shift(eye, -0.4f), 66, 1.2f, WHITE);
        text_centered("No games yet. Send one from your computer:\nvn3ds is listening for it.",
                      200 + shift(eye, -0.2f), 132, 0.5f, INK2);
        return;
    }
    /* far cards first, the chosen one last (nearest) */
    int order[MAX_GAMES + 1];
    for (int i = 0; i < n; i++)
        order[i] = i;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (fabsf(order[j] - E.cf_pos) > fabsf(order[i] - E.cf_pos)) {
                int t = order[i];
                order[i] = order[j];
                order[j] = t;
            }
    for (int k = 0; k < n; k++)
        if (fabsf(order[k] - E.cf_pos) < 3.2f)
            draw_card(eye, order[k], (float)order[k] - E.cf_pos);
    /* the chosen game: its name and where you are (or how far it has come) */
    int sel = E.game_sel;
    float dx = shift(eye, -0.2f);
    const char *t = home_title(sel);
    text_centered(t, 200 + dx, 174, fit_scale(t, 0.62f, 360), WHITE);
    char line[160];
    if (home_arriving(sel)) {
        char eta[48];
        app_rx_eta_text(eta, sizeof(eta));
        if (eta[0])
            snprintf(line, sizeof(line), "Arriving  %d%%  ·  %s", (int)(app_rx_progress() * 100), eta);
        else
            snprintf(line, sizeof(line), "Arriving  %d%%", (int)(app_rx_progress() * 100));
    } else if (sel < E.ngames && E.game_resume[sel].used) {
        snprintf(line, sizeof(line), "%.80s", E.game_resume[sel].preview);
    } else {
        snprintf(line, sizeof(line), "Not started yet");
    }
    text_centered(line, 200 + shift(eye, -0.1f), 199, fit_scale(line, 0.45f, 370), INK2);
}

/* ---- the download icon ------------------------------------------------------ */

/* While a transfer runs in the background: a download glyph in the top
 * right corner, with a spinner going round behind it. */
void ui_draw_rx_icon(int eye)
{
    if (!NET.receiving || E.screen == SCR_RECEIVE)
        return;
    float cx = TOP_W - 20 + shift(eye, ui_depth() - 0.15f), cy = 20, r = 10.5f;
    gfx_circle(cx, cy, 14, PANEL(0.62f));
    for (int i = 0; i < 24; i++) {   /* the faint ring */
        float a = (float)i / 24 * 2 * (float)M_PI, b = (float)(i + 1) / 24 * 2 * (float)M_PI;
        gfx_line(cx + r * cosf(a), cy + r * sinf(a), cx + r * cosf(b), cy + r * sinf(b), 1.6f,
                 RGBA(255, 255, 255, 40));
    }
    float head = E.time * 5.5f;   /* the spinner: a short comet */
    for (int i = 0; i < 10; i++) {
        float a = head - (float)i * 0.2f, b = a - 0.2f;
        gfx_line(cx + r * cosf(a), cy + r * sinf(a), cx + r * cosf(b), cy + r * sinf(b), 2.0f,
                 rgba_alpha(WHITE, 1.0f - (float)i / 10));
    }
    download_glyph(cx, cy - 0.5f, 0.75f, WHITE);
}

void ui_draw_opening(int eye)
{
    if (!E.opening)
        return;
    if (eye < 0) {   /* bottom screen: just dim it */
        gfx_rect(0, 0, 320, 240, RGBA(0, 0, 0, 170));
        return;
    }
    gfx_rect(0, 0, TOP_W, TOP_H, RGBA(0, 0, 0, 190));
    float dx = shift(eye, ui_depth() - 0.15f);
    ui_rrect(70 + dx, 78, 260, 84, 14, FILL1);
    char line[96];
    snprintf(line, sizeof(line), "Preparing %s", E.opening_title);
    text_centered(line, 200 + dx, 90, fit_scale(line, 0.6f, 240), WHITE);
    text_centered(E.opening_step, 200 + dx, 116, fit_scale(E.opening_step, 0.45f, 240), INK2);
    float bx = 95 + dx, by = 144, bw = 210;
    if (E.opening_frac >= 0) {
        progress_bar(bx, by, bw, 5, E.opening_frac, FILL3, WHITE);
    } else {   /* unknown length: a sliding segment */
        float p = fmodf((float)(platform_ms() % 100000) / 900.0f, 1.0f);
        gfx_rect(bx, by, bw, 5, FILL3);
        gfx_rect(bx + p * (bw - 50), by, 50, 5, WHITE);
    }
}

void ui_draw_top(int eye)
{
    switch (E.screen) {
    case SCR_GAMELIST:
        draw_coverflow(eye);
        break;
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
        gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(30, 30, 32, 255), BLACK);
        const MiniGame *g = mg_at(E.mg_sel);
        text_centered("Minigames", 200 + shift(eye, -0.3f), 18, 0.8f, WHITE);
        if (g) {
            text_centered(g->title, 140 + shift(eye, -0.2f), 62, fit_scale(g->title, 0.65f, 260), WHITE);
            char wrapped[600];
            ui_wrap(g->rules, 250, 0.42f, wrapped, sizeof(wrapped));
            text_centered(wrapped, 140 + shift(eye, -0.05f), 96, 0.42f, INK2);
            draw_my_scores(eye, g, 284, 52, 106, 170);
        }
        break;
    }
    case SCR_GAME:
        render_scene(eye);
        if (!E.hide_ui)
            draw_dialogue(eye);
        break;
    case SCR_RECEIVE: {
        gfx_gradient(0, 0, TOP_W, TOP_H, HOME_TOP, HOME_BOTTOM);
        float dx = shift(eye, -0.3f);
        text_centered("Receive over Wi-Fi", 200 + dx, 18, 0.8f, WHITE);
        char line[200];
        if (NET.listening) {   /* the command to type, in a card */
            float cd = shift(eye, -0.15f);
            ui_rrect(40 + cd, 56, 320, 52, 12, FILL1);
            text_centered("On your computer, open", 200 + cd, 62, 0.42f, INK2);
            text_centered(VN3DS_SITE, 200 + cd, 80, fit_scale(VN3DS_SITE, 0.6f, 300), WHITE);
        }
        text_centered(NET.message, 200 + dx, 124, fit_scale(NET.message, 0.5f, 370), INK2);
        if (NET.bytes_total > 0) {
            float bx = 50 + shift(eye, -0.2f);
            progress_bar(bx, 152, 300, 6, app_rx_progress(), FILL3, WHITE);
            char eta[48];
            app_rx_eta_text(eta, sizeof(eta));
            snprintf(line, sizeof(line), "%u of %u files  ·  %.1f of %.1f MB%s%s", (unsigned)NET.files_done,
                     (unsigned)NET.files_total, NET.bytes_done / 1048576.0, NET.bytes_total / 1048576.0,
                     eta[0] ? "\n" : "", eta);
            text_centered(line, 200 + dx, 168, 0.45f, WHITE);
        }
        if (NET.engine_updated)
            text_centered("vn3ds was updated: restart it to use the new version", 200 + dx, 214, 0.42f, INK2);
        break;
    }
    case SCR_ERROR: {
        gfx_gradient(0, 0, TOP_W, TOP_H, HOME_TOP, HOME_BOTTOM);
        char wrapped[600];
        ui_wrap(E.error, 344, 0.5f, wrapped, sizeof(wrapped));
        gfx_circle(34, 32, 11, RGBA(255, 69, 58, 255));
        gfx_rect(32.8f, 25, 2.4f, 9, WHITE);
        gfx_rect(32.8f, 36, 2.4f, 2.4f, WHITE);
        gfx_text("Something went wrong", 54, 22, 0.7f, WHITE);
        ui_rrect(16, 54, 368, 170, 12, FILL1);
        gfx_text(wrapped, 28, 64, 0.5f, INK2);
        break;
    }
    }
    draw_toast(eye);
}

/* ---- bottom screen ------------------------------------------------------- */

/* Buttons: dark grey and rounded; the focused one white with black text;
 * a toggle that is on a lighter grey with a dot. */
static void draw_button(const Button *b)
{
    u32 bg = b->hot ? WHITE : (b->on ? FILL3 : FILL2);
    u32 fg = b->hot ? BLACK : WHITE;
    float a = b->disabled ? 0.4f : 1.0f;
    ui_rrect(b->x, b->y, b->w, b->h, fminf(R_BUTTON, b->h / 2), rgba_alpha(bg, a));
    float sc = fit_scale(b->label, 0.5f, b->w - (b->on ? 18 : 10));
    float lh = gfx_line_height(sc);
    float tw = gfx_text_width(b->label, sc);
    float tx = b->x + (b->w - tw) / 2 + (b->on ? 4 : 0);
    if (b->on)
        gfx_circle(tx - 7, b->y + b->h / 2, 2.5f, rgba_alpha(WHITE, a));
    gfx_text(b->label, tx, b->y + (b->h - lh) / 2, sc, rgba_alpha(fg, a));
}

static void header(const char *text)
{
    gfx_text(text, 10, 4, fit_scale(text, 0.5f, 230), WHITE);
    float s = gfx_slider();
    gfx_text("3D", 262, 5, 0.42f, INK2);
    progress_bar(282, 9, 30, 5, s * fminf(1, E.set.depth_mult), FILL3, WHITE);
    gfx_rect(0, 22, BOT_W, 1, HAIRLINE);
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
            if (ty >= top) {
                gfx_circle(14, ty + lh / 2, 2.5f, rgba_alpha(h->who_color | 0xFF, a));
                gfx_text(h->who, 21, ty, sc, rgba_alpha(WHITE, a));
            }
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
                gfx_text(line, 14, ty, sc, rgba_alpha(RGBA(210, 210, 215, 255), a));
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
    snprintf(head, sizeof(head), "%s  ·  page %d of %d", title, E.slot_page + 1, SLOT_PAGES);
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
        ui_rrect(b[i].x, b[i].y, b[i].w, b[i].h, R_BUTTON, hot ? WHITE : FILL1);
        u32 fg = hot ? BLACK : WHITE;
        gfx_text(b[i].label, b[i].x + 7, b[i].y + 4, 0.45f, fg);
        if (s->used) {
            char when[32];
            time_t t = (time_t)s->time;
            struct tm *tm = localtime(&t);
            if (tm)
                strftime(when, sizeof(when), "%Y-%m-%d %H:%M", tm);
            else
                snprintf(when, sizeof(when), "?");
            gfx_text(when, b[i].x + 28, b[i].y + 5, 0.38f, hot ? RGBA(90, 90, 95, 255) : INK2);
            char wrapped[200];
            ui_wrap(s->preview, b[i].w - 10, 0.36f, wrapped, sizeof(wrapped));
            /* first two lines only */
            char *nl = strchr(wrapped, '\n');
            if (nl && (nl = strchr(nl + 1, '\n')))
                *nl = 0;
            gfx_text(wrapped, b[i].x + 7, b[i].y + 20, 0.36f, fg);
        } else {
            gfx_text(s->preview[0] ? s->preview : "Empty", b[i].x + 28, b[i].y + 5, 0.38f,
                     hot ? RGBA(110, 110, 115, 255) : INK3);
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
    gfx_gradient(0, 0, BOT_W, BOT_H, RGBA(14, 14, 16, 255), BLACK);
    Button b[48];
    int n;
    switch (E.screen) {
    case SCR_RECEIVE:
        header("Wi-Fi");
        {
            char msg[400], wrapped[500];
            snprintf(msg, sizeof(msg), "Copy the one command from " VN3DS_SITE ", drag your game into "
                     "the terminal and press Enter. It finds this 3DS by itself.\n\n"
                     "Same Wi-Fi network needed. Games also arrive while you play.\n\n"
                     "This 3DS: %s  (port %d)", NET.address, NET.port);
            ui_rrect(8, 32, 304, 132, 12, FILL1);
            ui_wrap(msg, 280, 0.45f, wrapped, sizeof(wrapped));
            gfx_text(wrapped, 20, 42, 0.45f, INK2);
        }
        break;
    case SCR_GAMELIST:
        header("vn3ds");
        if (app_home_count() > 0) {   /* page dots */
            int cnt = app_home_count();
            float step = cnt > 16 ? 300.0f / cnt : 12, x0 = 160 - step * (cnt - 1) / 2;
            for (int i = 0; i < cnt; i++)
                gfx_circle(x0 + step * i, 52, i == E.game_sel ? 3.0f : 2.2f, i == E.game_sel ? WHITE : INK3);
        }
        if (NET.receiving) {   /* what is arriving, and how long it will take */
            char msg[160], eta[48];
            const char *who = NET.game[0] && E.rx_new ? E.rx_new_title : "";
            for (int i = 0; i < E.ngames && !who[0]; i++)
                if (app_rx_busy(E.games[i]))
                    who = E.game_titles[i];
            app_rx_eta_text(eta, sizeof(eta));
            snprintf(msg, sizeof(msg), "Receiving%s%s  %d%%%s%s", who[0] ? " " : "", who,
                     (int)(app_rx_progress() * 100), eta[0] ? "  ·  " : "", eta);
            float sc = fit_scale(msg, 0.42f, 290);
            gfx_text(msg, 160 - gfx_text_width(msg, sc) / 2, 148, sc, INK2);
            progress_bar(60, 168, 200, 4, app_rx_progress(), FILL3, WHITE);
        } else if (NET.listening) {
            char msg[96];
            snprintf(msg, sizeof(msg), "Listening for games on %s", NET.address);
            gfx_text(msg, 160 - gfx_text_width(msg, 0.4f) / 2, 160, 0.4f, INK3);
        }
        if (app_home_count() == 0) {
            char msg[400], wrapped[500];
            snprintf(msg, sizeof(msg),
                     "No games yet. Press Y to receive one over Wi-Fi, or copy games made with "
                     "vn3ds-port to\n%s/games/\n\nSTART: exit", E.root);
            ui_wrap(msg, 296, 0.48f, wrapped, sizeof(wrapped));
            gfx_text(wrapped, 12, 36, 0.48f, INK2);
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
            ui_rrect(4, 25, 312, 6 * 26 - 1, R_BUTTON, FILL1);   /* a grouped list */
            for (int r = 0; r < 6; r++) {
                float y = 26 + r * 26;
                if (r == E.prefs_sel)
                    ui_rrect(6, y, 308, 23, 8, FILL2);
                else if (r > 0 && r - 1 != E.prefs_sel)
                    gfx_rect(12, y - 1.5f, 296, 1, HAIRLINE);
                char v[32];
                pref_value(r, v, sizeof(v));
                gfx_text(PREF_NAMES[r], 14, y + 4, 0.48f, WHITE);
                gfx_text(v, 212 - gfx_text_width(v, 0.48f), y + 4, 0.48f, INK2);
            }
            break;
        }
        break;
    case SCR_ERROR:
        header("Error");
        gfx_text("Press A to continue.", 12, 36, 0.5f, INK2);
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
