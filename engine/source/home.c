/* The home screen: the game library, in three views.
 *
 *   carousel  Top: the games' covers in a coverflow. Bottom: where you left
 *             each one (its resume snapshot) in a sliding carousel, the round
 *             red A to carry on, X for its title screen, Y to receive games.
 *   grid      (double tap) Bottom: the whole library, three across. Top: the
 *             same grid of covers, big, the chosen one sliding to the middle.
 *   timeline  (long press) Bottom: the chosen game's story points (story.c)
 *             in a vertical strip; A starts there. Top: a vine round the edge
 *             of the screen with Polaroids of points further back and ahead.
 *
 * A double tap goes to the grid and back, a long press to the timeline and
 * back; B goes back to the carousel. Drag the carousel or the strip. */

#include "app.h"
#include "fetch.h"
#include "net.h"

#define WHITE 0xFFFFFFFFu
#define BLACK 0x000000FFu
#define INK2 RGBA(152, 152, 159, 255)
#define INK3 RGBA(99, 99, 104, 255)
#define FILL1 RGBA(28, 28, 30, 255)
#define FILL2 RGBA(44, 44, 46, 255)
#define FILL3 RGBA(64, 64, 68, 255)
#define RED RGBA(228, 45, 50, 255)
#define VINE RGBA(150, 186, 132, 235)
#define LISTEN_GREEN RGBA(70, 205, 110, 255)
#define HOME_TOP RGBA(30, 30, 32, 255)
#define HOME_BOTTOM RGBA(0, 0, 0, 255)
#define BOT_TOP RGBA(14, 14, 16, 255)   /* ui_draw_bottom's backdrop */

/* Every picture is 5:3 like the top screen, its corners rounded the same. */
#define CORNER(w) ((w) * 0.055f)

/* bottom carousel: the middle tile, its neighbours mostly off the screen */
#define CT_W 196.0f
#define CT_H 118.0f
#define CT_Y 22.0f
#define CT_STEP 204.0f
#define A_X 160.0f
#define A_Y 172.0f
#define A_R 19.0f
#define PILL_Y 205.0f
#define PILL_H 28.0f
/* bottom grid */
#define G_W 96.0f
#define G_H 58.0f
#define G_STEPX 104.0f
#define G_STEPY 66.0f
/* top grid */
#define TG_W 236.0f
#define TG_H 142.0f
#define TG_STEPX 248.0f
#define TG_STEPY 154.0f
/* bottom strip (timeline) */
#define ST_X 146.0f
#define ST_W 200.0f
#define ST_H 120.0f
#define ST_STEP 128.0f
#define TA_X 288.0f
#define TA_Y 120.0f

#define THUMB_CACHE 12
#define LONG_PRESS 0.5f
#define DOUBLE_TAP 0.35f

enum { HM_CAROUSEL, HM_GRID, HM_TIMELINE };

/* A timeline entry: a story point, or where you are now (the resume save). */
typedef struct {
    int k;   /* story point slot, or -1 for now */
    u32 time;
    const char *preview;
} Entry;

static struct {
    int mode;
    float mode_t;   /* time in this view: fades, the vine growing */
    u32 updated_frame;   /* the last frame home_update ran */
    /* the finger */
    bool touching, dragging, long_fired;
    float touch_t, drag_from;
    int tx0, ty0, tx, ty;
    float last_tap_t;
    int last_tap_x, last_tap_y;
    /* grid */
    float gcol, grow, gscroll;
    /* timeline */
    int tl_game;
    StoryPoint pts[STORY_MAX];
    Entry ent[STORY_MAX + 1];
    int count, sel, now_at;
    float pos, sel_t;
    struct {
        int k;
        GfxTex *tex;
        u32 used;
    } cache[THUMB_CACHE];
    int loads;   /* pictures read this frame */
} H = {.tl_game = -1, .last_tap_t = -10};

static inline float sh(int eye, float depth)
{
    return (eye == EYE_LEFT ? -1.0f : 1.0f) * depth * app_strength();
}
static u32 top_bg_at(float y) { return ui_mix(HOME_TOP, HOME_BOTTOM, y / TOP_H); }
static u32 bot_bg_at(float y) { return ui_mix(BOT_TOP, BLACK, y / BOT_H); }
static u32 white_bg(float y) { return WHITE; }   /* (under a chosen picture's white edge) */
static float smooth(float t)
{
    t = clampf(t, 0, 1);
    return t * t * (3 - 2 * t);
}

static const char *title_of(int i) { return i < E.ngames ? E.game_titles[i] : E.rx_new_title; }
static bool arriving(int i) { return i >= E.ngames ? E.rx_new : app_rx_busy(E.games[i]); }
static GfxTex *cover_of(int i) { return i < E.ngames ? E.game_cover[i] : E.rx_new_cover; }

/* A picture (or, without one, a grey card with the game's name) with
 * rounded corners over the backdrop. */
static void picture(GfxTex *t, const char *name, float x, float y, float w, float h, u32 (*bg)(float),
                    float alpha)
{
    float r = CORNER(w);
    if (t) {
        gfx_image(t, x, y, w, h, 0, alpha);
        ui_round_corners(x, y, w, h, r, bg(y), bg(y + h));
    } else {
        ui_rrect(x, y, w, h, r, rgba_alpha(FILL2, alpha));
        if (name)
            ui_text_centered(name, x + w / 2, y + h / 2 - gfx_line_height(0.5f * w / 200) / 2,
                             ui_fit_scale(name, 0.55f * w / 200, w - 16), rgba_alpha(WHITE, alpha));
    }
}

/* A white edge round a chosen picture. */
static void ring(float x, float y, float w, float h, float a)
{
    float r = CORNER(w);
    ui_rrect(x - 2.5f, y - 2.5f, w + 5, h + 5, r + 2.5f, rgba_alpha(WHITE, a));
}

/* Still arriving: a dark veil, a download glyph and how far along it is. */
static void arriving_veil(float x, float y, float w, float h)
{
    float k = w / 200;
    ui_rrect(x, y, w, h, CORNER(w), RGBA(0, 0, 0, 130));
    ui_download_glyph(x + w / 2, y + h / 2 - 8 * k, k, WHITE);
    ui_progress_bar(x + 14 * k, y + h - 16 * k, w - 28 * k, 4, app_rx_progress(), RGBA(255, 255, 255, 60),
                    WHITE);
}

static void ago(u32 t, char *out, size_t len)
{
    u32 now = platform_time(), d = now > t ? now - t : 0;
    if (!t)
        out[0] = 0;
    else if (d < 90)
        snprintf(out, len, "just now");
    else if (d < 3600)
        snprintf(out, len, "%u min ago", (unsigned)(d / 60));
    else if (d < 86400 * 2)
        snprintf(out, len, "%u h ago", (unsigned)(d / 3600));
    else
        snprintf(out, len, "%u days ago", (unsigned)(d / 86400));
}

/* ---- timeline data --------------------------------------------------------- */

static void cache_clear(void)
{
    for (int i = 0; i < THUMB_CACHE; i++) {
        gfx_tex_free(H.cache[i].tex);
        H.cache[i].tex = NULL;
        H.cache[i].k = -1;
    }
}

/* Entry i's snapshot, read when first needed (one file a frame at most). */
static GfxTex *entry_tex(int i)
{
    if (i < 0 || i >= H.count)
        return NULL;
    int k = H.ent[i].k;
    if (k < 0)
        return H.tl_game < E.ngames ? E.game_thumb[H.tl_game] : NULL;
    int lru = 0;
    for (int c = 0; c < THUMB_CACHE; c++) {
        if (H.cache[c].tex && H.cache[c].k == k) {
            H.cache[c].used = E.frame;
            return H.cache[c].tex;
        }
        if (!H.cache[c].tex || (H.cache[lru].tex && H.cache[c].used < H.cache[lru].used))
            lru = c;
    }
    if (H.loads >= 1)
        return NULL;
    H.loads++;
    char path[400];
    story_thumb_path(E.games[H.tl_game], k, path, sizeof(path));
    gfx_tex_free(H.cache[lru].tex);
    H.cache[lru].tex = app_load_thm(path);
    H.cache[lru].k = k;
    H.cache[lru].used = E.frame;
    return H.cache[lru].tex;
}

/* The story points of game `g`, with now (the resume save) after the
 * latest one. */
static void timeline_open(int g)
{
    cache_clear();
    H.tl_game = g;
    H.count = 0;
    H.now_at = -1;
    if (g < 0 || g >= E.ngames)
        return;
    int n = story_read(E.games[g], H.pts, STORY_MAX), latest = -1;
    for (int i = 0; i < n; i++)
        if (latest < 0 || H.pts[i].time >= H.pts[latest].time)
            latest = i;
    bool resume = E.game_resume[g].used;
    for (int i = 0; i < n; i++) {
        H.ent[H.count++] = (Entry){H.pts[i].k, H.pts[i].time, H.pts[i].preview};
        if (i == latest && resume) {
            H.now_at = H.count;
            H.ent[H.count++] = (Entry){-1, E.game_resume[g].time, E.game_resume[g].preview};
        }
    }
    if (resume && H.now_at < 0) {   /* (no points yet) */
        H.now_at = H.count;
        H.ent[H.count++] = (Entry){-1, E.game_resume[g].time, E.game_resume[g].preview};
    }
    H.sel = H.now_at >= 0 ? H.now_at : H.count - 1;
    if (H.sel < 0)
        H.sel = 0;
    H.pos = (float)H.sel;
}

/* "Now", "3 back", "2 ahead": an entry's place relative to now. */
static void entry_label(int i, char *out, size_t len)
{
    int ref = H.now_at >= 0 ? H.now_at : H.count - 1, d = i - ref;
    if (d == 0)
        snprintf(out, len, H.now_at >= 0 ? "Now" : "Latest");
    else if (d < 0)
        snprintf(out, len, "%d back", -d);
    else
        snprintf(out, len, "%d ahead", d);
}

static void timeline_start(void)
{
    if (H.count == 0 || H.tl_game < 0)
        return;
    const Entry *e = &H.ent[H.sel];
    if (e->k < 0) {
        app_play_game(H.tl_game);
        return;
    }
    if (app_load_game(H.tl_game) && E.loaded)
        app_load_slot(STORY_SLOT0 + e->k);
}

/* ---- input ------------------------------------------------------------------ */

static void set_mode(int m)
{
    if (m == HM_TIMELINE)
        timeline_open(E.game_sel);
    else
        cache_clear();
    if (m == HM_GRID) {
        H.gcol = (float)(E.game_sel % 3);
        H.grow = (float)(E.game_sel / 3);
    }
    H.mode = m;
    H.mode_t = 0;
}

void home_reset(void)
{
    H.updated_frame = E.frame;   /* (back from Receive: stay in the same view) */
    if (E.game_sel >= app_home_count())
        E.game_sel = app_home_count() > 0 ? app_home_count() - 1 : 0;
    if (H.mode == HM_TIMELINE) {   /* the points may have changed: stay where you were */
        int sel = H.sel;
        timeline_open(E.game_sel);
        H.sel = sel < H.count ? sel : H.sel;
    }
}

static bool in_circle(int x, int y, float cx, float cy, float r)
{
    return (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r;
}

static float pill_w_y(void);
static void y_pill_box(float *x, float *w);

static void tap(int x, int y)
{
    int n = app_home_count();
    float yx, yw;
    y_pill_box(&yx, &yw);
    if (H.mode == HM_CAROUSEL && y >= PILL_Y - 4 && x >= yx && x < yx + yw + 4) {
        app_receive_open();
        return;
    }
    switch (H.mode) {
    case HM_CAROUSEL:
        if (n == 0) {
            if (in_circle(x, y, A_X, A_Y, A_R + 6) || (y >= CT_Y && y < CT_Y + CT_H))
                fetch_start();
            return;
        }
        if (in_circle(x, y, A_X, A_Y, A_R + 6))
            app_play_game(E.game_sel);
        else if (y >= PILL_Y - 4 && x < 8 + pill_w_y() + 4)
            app_load_game(E.game_sel);
        else if (y >= CT_Y && y < CT_Y + CT_H && x < 160 - CT_W / 2 && E.game_sel > 0)
            E.game_sel--;
        else if (y >= CT_Y && y < CT_Y + CT_H && x >= 160 + CT_W / 2 && E.game_sel < n - 1)
            E.game_sel++;
        break;
    case HM_GRID: {
        int c = (int)((x - 4) / G_STEPX), r = (int)((y - 8 + H.gscroll * G_STEPY) / G_STEPY + 1) - 1;
        int i = r * 3 + c;
        if (c >= 0 && c < 3 && r >= 0 && i < n)
            E.game_sel = i;
        break;
    }
    case HM_TIMELINE:
        if (in_circle(x, y, TA_X, TA_Y, A_R + 6))
            timeline_start();
        else if (x < ST_X + ST_W / 2 && y < TA_Y - ST_H / 2 && H.sel > 0)
            H.sel--, H.sel_t = 0;
        else if (x < ST_X + ST_W / 2 && y >= TA_Y + ST_H / 2 && H.sel < H.count - 1)
            H.sel++, H.sel_t = 0;
        break;
    }
}

static void touch(const Input *in, float dt)
{
    if (in->down & KEY_TOUCH_) {
        H.touching = true;
        H.dragging = H.long_fired = false;
        H.touch_t = 0;
        H.tx0 = H.tx = in->tx;
        H.ty0 = H.ty = in->ty;
        H.drag_from = H.mode == HM_TIMELINE ? H.pos : E.cf_pos;
        return;
    }
    if (!H.touching)
        return;
    if (in->held & KEY_TOUCH_) {
        H.touch_t += dt;
        H.tx = in->tx;
        H.ty = in->ty;
        int dx = H.tx - H.tx0, dy = H.ty - H.ty0;
        if (!H.dragging && !H.long_fired && dx * dx + dy * dy > 10 * 10 && H.mode != HM_GRID &&
            app_home_count() > 0)
            H.dragging = true;
        if (H.dragging && H.mode == HM_CAROUSEL)
            E.cf_pos = clampf(H.drag_from - dx / CT_STEP, -0.3f, app_home_count() - 0.7f);
        else if (H.dragging && H.mode == HM_TIMELINE)
            H.pos = clampf(H.drag_from - dy / ST_STEP, -0.3f, H.count - 0.7f);
        if (!H.dragging && !H.long_fired && H.touch_t >= LONG_PRESS && app_home_count() > 0) {
            H.long_fired = true;
            set_mode(H.mode == HM_TIMELINE ? HM_CAROUSEL : HM_TIMELINE);
        }
        return;
    }
    H.touching = false;   /* lifted */
    if (H.dragging) {
        if (H.mode == HM_CAROUSEL) {
            E.game_sel = (int)clampf(floorf(E.cf_pos + 0.5f), 0, app_home_count() - 1);
        } else if (H.count > 0) {
            int s = (int)clampf(floorf(H.pos + 0.5f), 0, H.count - 1);
            if (s != H.sel)
                H.sel_t = 0;
            H.sel = s;
        }
        return;
    }
    if (H.long_fired)
        return;
    int x = H.tx, y = H.ty;
    if (E.time - H.last_tap_t < DOUBLE_TAP && abs(x - H.last_tap_x) < 40 && abs(y - H.last_tap_y) < 40 &&
        app_home_count() > 0) {
        H.last_tap_t = -10;
        set_mode(H.mode == HM_GRID ? HM_CAROUSEL : HM_GRID);
        return;
    }
    H.last_tap_t = E.time;
    H.last_tap_x = x;
    H.last_tap_y = y;
    tap(x, y);
}

void home_update(const Input *in, float dt)
{
    if (E.frame != H.updated_frame + 1 && H.updated_frame) {   /* back on the home screen */
        H.mode = HM_CAROUSEL;
        H.touching = false;
        cache_clear();
        app_home_refresh_loaded();   /* where the game you were playing was left */
    }
    H.updated_frame = E.frame;
    H.mode_t += dt;
    H.sel_t += dt;
    H.loads = 0;
    int n = app_home_count();
    if (E.game_sel >= n)
        E.game_sel = n > 0 ? n - 1 : 0;
    touch(in, dt);
    if (E.screen != SCR_GAMELIST)
        return;
    if (in->down & KEY_Y_) {
        app_receive_open();
        return;
    }
    if (in->down & KEY_START_)
        E.quit = true;
    if (n == 0) {
        if (in->down & KEY_A_)
            fetch_start();   /* the first-run offer: download Snapshot */
        return;
    }
    switch (H.mode) {
    case HM_CAROUSEL:
        if ((in->down & KEY_LEFT_) && E.game_sel > 0)
            E.game_sel--;
        if ((in->down & KEY_RIGHT_) && E.game_sel < n - 1)
            E.game_sel++;
        if (in->down & KEY_A_)
            app_play_game(E.game_sel);   /* carry on where you left off */
        else if (in->down & KEY_X_)
            app_load_game(E.game_sel);   /* its title screen */
        break;
    case HM_GRID:
        if ((in->down & KEY_LEFT_) && E.game_sel > 0)
            E.game_sel--;
        if ((in->down & KEY_RIGHT_) && E.game_sel < n - 1)
            E.game_sel++;
        if ((in->down & KEY_UP_) && E.game_sel >= 3)
            E.game_sel -= 3;
        if ((in->down & KEY_DOWN_) && E.game_sel / 3 < (n - 1) / 3)
            E.game_sel = E.game_sel + 3 < n ? E.game_sel + 3 : n - 1;
        if (in->down & KEY_A_)
            app_play_game(E.game_sel);
        else if (in->down & KEY_X_)
            app_load_game(E.game_sel);
        else if (in->down & KEY_B_)
            set_mode(HM_CAROUSEL);
        break;
    case HM_TIMELINE:
        if ((in->down & KEY_UP_) && H.sel > 0)
            H.sel--, H.sel_t = 0;
        if ((in->down & KEY_DOWN_) && H.sel < H.count - 1)
            H.sel++, H.sel_t = 0;
        if (in->down & KEY_A_)
            timeline_start();
        else if (in->down & KEY_B_)
            set_mode(HM_CAROUSEL);
        break;
    }
    if (E.screen != SCR_GAMELIST)
        return;
    /* the views follow the selection */
    float k = fminf(1.0f, dt * 10.0f);
    if (!(H.touching && H.dragging))
        H.pos += ((float)H.sel - H.pos) * k;
    H.gcol += ((float)(E.game_sel % 3) - H.gcol) * k;
    H.grow += ((float)(E.game_sel / 3) - H.grow) * k;
    int rows = (n + 2) / 3;
    float want = clampf((float)(E.game_sel / 3) - 1, 0, (float)(rows > 3 ? rows - 3 : 0));
    H.gscroll += (want - H.gscroll) * k;
}

/* ---- top screen ---------------------------------------------------------------- */

/* The coverflow: card i at offset o from the chosen one. */
static void draw_card(int eye, int i, float o)
{
    float a = fabsf(o);
    float side = o < 0 ? -1.0f : 1.0f;
    float x = 200 + side * (fminf(a, 1.0f) * 128 + fmaxf(a - 1.0f, 0) * 58);
    float k = a < 1 ? 1.0f - 0.4f * a : 0.6f - 0.08f * fminf(a - 1.0f, 2.0f);
    float depth = -0.28f + 0.55f * fminf(a, 1.6f);
    float w = THUMB_W * k, h = THUMB_H * k, r = CORNER(w);
    float cx = x + sh(eye, depth), cy = 98 - (1 - fminf(a, 1)) * 6;
    float fade = clampf(1.6f - (a - 1.0f), 0, 1);
    float x0 = cx - w / 2, y0 = cy - h / 2;
    if (a < 0.5f)
        ring(x0, y0, w, h, fade);
    picture(cover_of(i), title_of(i), x0, y0, w, h, top_bg_at, fade);
    if (arriving(i))
        arriving_veil(x0, y0, w, h);
    if (a > 0.5f)   /* side cards sit back and darker */
        ui_rrect(x0, y0, w, h, r, RGBA(0, 0, 0, (u8)(120 * fminf(a, 1) * fade)));
}

/* First run, no games yet: a card for Snapshot, the demo, where its card
 * will be while it downloads, and what it is. */
static void draw_offer(int eye)
{
    float cx = 200 + sh(eye, -0.28f), cy = 92, w = THUMB_W, h = THUMB_H, r = CORNER(w);
    float x0 = cx - w / 2, y0 = cy - h / 2;
    ring(x0, y0, w, h, 1);
    ui_rrect(x0, y0, w, h, r, FILL2);
    ui_download_glyph(cx, cy - 14, 1.5f, WHITE);
    ui_text_centered("Snapshot", cx, cy + 18, 0.62f, WHITE);
    float dx = sh(eye, -0.2f);
    ui_text_centered("Try Snapshot, the vn3ds demo", 200 + dx, 168, 0.62f, WHITE);
    const char *l1 = "A short story at the beach, with music,", *l2 = "3D scenes and minigames.  " SNAPSHOT_SIZE_TEXT;
    char e1[128];
    if (FETCH.failed) {
        snprintf(e1, sizeof(e1), "Download stopped: %s", FETCH.error);
        l1 = e1;
        l2 = "Press A to try again.";
    } else if (FETCH.busy) {
        l1 = "Connecting...";
        l2 = "";
    }
    dx = sh(eye, -0.1f);
    ui_text_centered(l1, 200 + dx, 192, ui_fit_scale(l1, 0.45f, 370), INK2);
    ui_text_centered(l2, 200 + dx, 208, 0.45f, INK2);
}

static void draw_coverflow(int eye)
{
    int n = app_home_count();
    if (n == 0) {
        draw_offer(eye);
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
    const char *t = title_of(sel);
    ui_text_centered(t, 200 + sh(eye, -0.2f), 174, ui_fit_scale(t, 0.62f, 360), WHITE);
    char line[160];
    if (arriving(sel)) {
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
    ui_text_centered(line, 200 + sh(eye, -0.1f), 199, ui_fit_scale(line, 0.45f, 370), INK2);
}

/* The library grid, big: the chosen cover in the middle, a third of its
 * neighbours at the sides and a quarter of the rows above and below. */
static void draw_top_grid(int eye)
{
    int n = app_home_count();
    for (int i = 0; i < n; i++) {
        float ox = (float)(i % 3) - H.gcol, oy = (float)(i / 3) - H.grow;
        if (fabsf(ox) > 1.6f || fabsf(oy) > 1.6f)
            continue;
        float d = fminf(1, sqrtf(ox * ox + oy * oy));
        bool chosen = i == E.game_sel;
        float cx = 200 + ox * TG_STEPX + sh(eye, -0.25f + 0.45f * d), cy = 120 + oy * TG_STEPY;
        float x0 = cx - TG_W / 2, y0 = cy - TG_H / 2;
        if (chosen)
            ring(x0, y0, TG_W, TG_H, 1);
        GfxTex *t = cover_of(i);
        if (t) {
            gfx_image(t, x0, y0, TG_W, TG_H, 0, 1);
            if (chosen) {   /* its name on a shade along the bottom */
                gfx_gradient(x0, y0 + TG_H - 40, TG_W, 40, RGBA(0, 0, 0, 0), RGBA(0, 0, 0, 200));
                const char *s = title_of(i);
                gfx_text(s, x0 + 12, y0 + TG_H - 24, ui_fit_scale(s, 0.55f, TG_W - 24), WHITE);
            }
            u32 c = chosen ? WHITE : top_bg_at(y0), c2 = chosen ? WHITE : top_bg_at(y0 + TG_H);
            ui_round_corners(x0, y0, TG_W, TG_H, CORNER(TG_W), c, c2);
        } else {
            picture(NULL, title_of(i), x0, y0, TG_W, TG_H, top_bg_at, 1);
        }
        if (arriving(i))
            arriving_veil(x0, y0, TG_W, TG_H);
        if (!chosen)
            ui_rrect(x0, y0, TG_W, TG_H, CORNER(TG_W), RGBA(0, 0, 0, (u8)(70 + 70 * d)));
    }
}

/* The vine: a rounded rectangle just inside the screen's edge, starting low
 * on the left and going up, along the top, down the right and back along
 * the bottom. */
#define V_X0 12.0f
#define V_Y0 12.0f
#define V_X1 388.0f
#define V_Y1 228.0f
#define V_R 26.0f
#define V_SIDE (V_Y1 - V_Y0 - 2 * V_R)
#define V_TOP (V_X1 - V_X0 - 2 * V_R)
#define V_ARC ((float)M_PI / 2 * V_R)
#define V_LEN (2 * V_SIDE + 2 * V_TOP + 4 * V_ARC)

/* The point s along the vine, and the way it goes (tx, ty). */
static void vine_at(float s, float *x, float *y, float *tx, float *ty)
{
    s = fmodf(s + V_LEN, V_LEN);
    const float len[8] = {V_SIDE, V_ARC, V_TOP, V_ARC, V_SIDE, V_ARC, V_TOP, V_ARC};
    const float cxs[4] = {V_X0 + V_R, V_X1 - V_R, V_X1 - V_R, V_X0 + V_R};
    const float cys[4] = {V_Y0 + V_R, V_Y0 + V_R, V_Y1 - V_R, V_Y1 - V_R};
    int seg = 0;
    while (seg < 7 && s > len[seg]) {
        s -= len[seg];
        seg++;
    }
    float f = s / len[seg];
    switch (seg) {
    case 0: *x = V_X0, *y = V_Y1 - V_R - f * V_SIDE, *tx = 0, *ty = -1; return;
    case 2: *x = V_X0 + V_R + f * V_TOP, *y = V_Y0, *tx = 1, *ty = 0; return;
    case 4: *x = V_X1, *y = V_Y0 + V_R + f * V_SIDE, *tx = 0, *ty = 1; return;
    case 6: *x = V_X1 - V_R - f * V_TOP, *y = V_Y1, *tx = -1, *ty = 0; return;
    }
    int c = seg / 2;   /* the corners: top left, top right, bottom right, bottom left */
    float a = (float)M_PI * (1.0f + 0.5f * (float)c) + f * (float)M_PI / 2;
    *x = cxs[c] + V_R * cosf(a);
    *y = cys[c] + V_R * sinf(a);
    *tx = -sinf(a);
    *ty = cosf(a);
}

static void draw_vine(int eye, float grown)
{
    float dx = sh(eye, 0.12f), end = grown * V_LEN;
    float px = 0, py = 0;
    for (float s = 0; s <= end + 0.01f; s += 6) {
        float x, y, tx, ty;
        vine_at(s, &x, &y, &tx, &ty);
        float wob = 1.6f * sinf(s * 0.085f);   /* a gentle wander */
        x += -ty * wob + dx;
        y += tx * wob;
        if (s > 0)
            gfx_line(px, py, x, y, 1.6f, VINE);
        px = x;
        py = y;
    }
    for (float s = 17; s < end; s += 34) {   /* leaves, unfolding behind the tip */
        float x, y, tx, ty;
        vine_at(s, &x, &y, &tx, &ty);
        float g = clampf((end - s) / 24, 0, 1), side = fmodf(s, 68) < 34 ? 1.0f : -1.0f;
        float lx = tx * 0.6f - ty * 0.8f * side, ly = ty * 0.6f + tx * 0.8f * side;   /* leaning forward */
        float L = 7.5f * g, W = 2.6f * g;
        float bx = x + dx, by = y, mx = bx + lx * L * 0.5f, my = by + ly * L * 0.5f;
        float ex = bx + lx * L, ey = by + ly * L;
        gfx_triangle(bx, by, mx - ly * W, my + lx * W, ex, ey, VINE);
        gfx_triangle(bx, by, mx + ly * W, my - lx * W, ex, ey, VINE);
    }
    if (grown < 1) {   /* the growing tip */
        float x, y, tx, ty;
        vine_at(end, &x, &y, &tx, &ty);
        gfx_circle(x + dx, y, 2.2f, VINE);
    }
}

/* A filled quad rotated by `a` about (cx, cy): w x h, centre offset (ox, oy). */
static void quad(float cx, float cy, float ox, float oy, float w, float h, float a, u32 c)
{
    float ca = cosf(a), sa = sinf(a), xs[4], ys[4];
    const float u[4] = {-0.5f, 0.5f, 0.5f, -0.5f}, v[4] = {-0.5f, -0.5f, 0.5f, 0.5f};
    for (int i = 0; i < 4; i++) {
        float lx = ox + u[i] * w, ly = oy + v[i] * h;
        xs[i] = cx + lx * ca - ly * sa;
        ys[i] = cy + lx * sa + ly * ca;
    }
    gfx_triangle(xs[0], ys[0], xs[1], ys[1], xs[2], ys[2], c);
    gfx_triangle(xs[0], ys[0], xs[2], ys[2], xs[3], ys[3], c);
}

#define PO_W 94.0f
#define PO_H 70.0f
#define PO_PIC_W 84.0f
#define PO_PIC_H 50.0f

/* A Polaroid of entry i hanging from (pin_x, pin_y): below it, or standing
 * above it when `up`. */
static void polaroid(int eye, int i, float pin_x, float pin_y, bool up, float tilt, float alpha)
{
    if (alpha <= 0)
        return;
    float dx = sh(eye, -0.04f);
    float cx = pin_x + dx, cy = up ? pin_y - 6 - PO_H / 2 : pin_y + 6 + PO_H / 2;
    quad(cx + 2, cy + 3, 0, 0, PO_W, PO_H, tilt, RGBA(0, 0, 0, (u8)(110 * alpha)));   /* shadow */
    quad(cx, cy, 0, 0, PO_W, PO_H, tilt, rgba_alpha(RGBA(242, 240, 233, 255), alpha));
    float ox = 0, oy = -PO_H / 2 + 5 + PO_PIC_H / 2, ca = cosf(tilt), sa = sinf(tilt);
    float picx = cx + ox * ca - oy * sa, picy = cy + ox * sa + oy * ca;
    GfxTex *t = entry_tex(i);
    if (t)
        gfx_image(t, picx - PO_PIC_W / 2, picy - PO_PIC_H / 2, PO_PIC_W, PO_PIC_H, tilt, alpha);
    else
        quad(cx, cy, ox, oy, PO_PIC_W, PO_PIC_H, tilt, rgba_alpha(FILL2, alpha));
    char label[24];
    entry_label(i, label, sizeof(label));
    float ly = PO_H / 2 - 8.5f;   /* the caption, in the wide bottom margin */
    float lx = cx - ly * sa, lyy = cy + ly * ca;
    ui_text_centered(label, lx, lyy - gfx_line_height(0.36f) / 2, 0.36f,
                     rgba_alpha(RGBA(70, 68, 64, 255), alpha));
    float pin_dx = pin_x + sh(eye, -0.06f);   /* the pin */
    gfx_circle(pin_dx, pin_y + (up ? -3 : 3), 3.2f, rgba_alpha(RGBA(200, 64, 56, 255), alpha));
    gfx_circle(pin_dx - 0.8f, pin_y + (up ? -3.8f : 2.2f), 1.1f, rgba_alpha(RGBA(255, 190, 180, 255), alpha));
}

static void draw_timeline_top(int eye)
{
    float grown = smooth(H.mode_t / 1.1f);
    draw_vine(eye, grown);
    float end = grown * V_LEN;
    if (H.count == 0) {
        ui_text_centered("No story points yet", 200 + sh(eye, -0.1f), 104, 0.55f, WHITE);
        ui_text_centered("They gather here as you play.", 200 + sh(eye, -0.05f), 124, 0.45f, INK2);
        return;
    }
    /* back along the top (the oldest on the left), ahead along the bottom
     * (the furthest on the left): points spread evenly over each stretch */
    const float xs[3] = {84, 200, 316};
    float fade = smooth(H.sel_t / 0.25f);
    int c = H.sel, back = c, ahead = H.count - 1 - c, last = -1;
    for (int j = 0; j < 3; j++) {
        int i = c - (back * (3 - j) + 2) / 3;
        if (back == 0 || i == last || i >= c)
            continue;
        last = i;
        float s = V_SIDE + V_ARC + (xs[j] - (V_X0 + V_R));
        polaroid(eye, i, xs[j], V_Y0, false, (j - 1) * 0.045f + 0.02f, fade * clampf((end - s) / 40, 0, 1));
    }
    last = -1;
    for (int j = 0; j < 3; j++) {
        int i = c + (ahead * (j + 1) + 2) / 3;
        if (ahead == 0 || i == last || i <= c)
            continue;
        last = i;
        float x = xs[2 - j], s = 2 * V_SIDE + V_TOP + 3 * V_ARC + ((V_X1 - V_R) - x);
        polaroid(eye, i, x, V_Y1, true, (1 - j) * 0.04f - 0.015f, fade * clampf((end - s) / 40, 0, 1));
    }
    /* where the strip below is: a bud on the right */
    if (end > V_SIDE * 1.5f + V_TOP + 2 * V_ARC) {
        float bx = V_X1 + sh(eye, 0.1f), by = 120, p = 0.5f + 0.5f * sinf(E.time * 3);
        gfx_circle(bx, by, 6 + p, RGBA(150, 186, 132, (u8)(60 + 40 * p)));
        gfx_circle(bx, by, 3.5f, WHITE);
    }
    /* the chosen point: what was said there, and when */
    const Entry *e = &H.ent[c];
    const char *game = title_of(H.tl_game);
    ui_text_centered(game, 200 + sh(eye, -0.12f), 91, ui_fit_scale(game, 0.42f, 300), INK2);
    char text[104], wrapped[300];
    snprintf(text, sizeof(text), "%s%s", e->preview[0] ? e->preview : "(a picture without words)",
             strlen(e->preview) >= sizeof(H.pts[0].preview) - 1 ? "..." : "");   /* (cut short) */
    ui_wrap(text, 300, 0.45f, wrapped, sizeof(wrapped));
    char *third = wrapped;   /* two lines at most */
    for (int l = 0; l < 2 && third; l++)
        third = strchr(third + (l ? 1 : 0), '\n');
    if (third)
        strcpy(third, "...");
    ui_text_centered(wrapped, 200 + sh(eye, -0.16f), 106, 0.45f, WHITE);
    char when[48], line[96], label[24];
    ago(e->time, when, sizeof(when));
    entry_label(c, label, sizeof(label));
    snprintf(line, sizeof(line), "%s%s%s", label, when[0] ? "  ·  " : "", when);
    ui_text_centered(line, 200 + sh(eye, -0.1f), 136, 0.38f, INK3);
}

void home_draw_top(int eye)
{
    gfx_gradient(0, 0, TOP_W, TOP_H, HOME_TOP, HOME_BOTTOM);
    switch (H.mode) {
    case HM_CAROUSEL: draw_coverflow(eye); break;
    case HM_GRID: draw_top_grid(eye); break;
    case HM_TIMELINE: draw_timeline_top(eye); break;
    }
    if (H.mode_t < 0.2f && E.screen == SCR_GAMELIST)   /* a view coming in */
        gfx_rect(0, 0, TOP_W, TOP_H, RGBA(0, 0, 0, (u8)(255 * (1 - H.mode_t / 0.2f))));
}

/* ---- bottom screen -------------------------------------------------------------- */

static void a_button(float cx, float cy, float alpha)
{
    gfx_circle(cx, cy + 1.5f, A_R, RGBA(0, 0, 0, (u8)(120 * alpha)));
    gfx_circle(cx, cy, A_R, rgba_alpha(RED, alpha));
    gfx_circle(cx, cy - 1, A_R - 3, rgba_alpha(RGBA(240, 66, 70, 255), alpha));
    float sc = 0.72f;
    gfx_text("A", cx - gfx_text_width("A", sc) / 2, cy - gfx_line_height(sc) / 2, sc, rgba_alpha(WHITE, alpha));
}

/* A rounded corner button: a letter in a circle, then its label. */
static float pill_w(const char *label) { return 34 + gfx_text_width(label, 0.45f) + 12; }
static float pill_w_y(void) { return pill_w("Title screen"); }

static void pill(float x, const char *key, const char *label, float alpha)
{
    float w = pill_w(label);
    ui_rrect(x, PILL_Y, w, PILL_H, PILL_H / 2, rgba_alpha(FILL2, alpha));
    gfx_circle(x + 15, PILL_Y + PILL_H / 2, 9.5f, rgba_alpha(FILL3, alpha));
    gfx_text(key, x + 15 - gfx_text_width(key, 0.42f) / 2, PILL_Y + PILL_H / 2 - gfx_line_height(0.42f) / 2,
             0.42f, rgba_alpha(WHITE, alpha));
    gfx_text(label, x + 31, PILL_Y + PILL_H / 2 - gfx_line_height(0.45f) / 2, 0.45f, rgba_alpha(WHITE, alpha));
}

static void y_pill_box(float *x, float *w)
{
    *w = pill_w("Receive") + 8;
    *x = BOT_W - 8 - *w;
}

/* Y: Receive. It is always listening: a small green dot says so (a progress
 * line under the label while something arrives). */
static void y_pill(void)
{
    float x, w;
    y_pill_box(&x, &w);
    ui_rrect(x, PILL_Y, w, PILL_H, PILL_H / 2, FILL2);
    gfx_circle(x + 15, PILL_Y + PILL_H / 2, 9.5f, FILL3);
    gfx_text("Y", x + 15 - gfx_text_width("Y", 0.42f) / 2, PILL_Y + PILL_H / 2 - gfx_line_height(0.42f) / 2,
             0.42f, WHITE);
    gfx_text("Receive", x + 31, PILL_Y + PILL_H / 2 - gfx_line_height(0.45f) / 2, 0.45f, WHITE);
    float dx = x + w - 12, dy = PILL_Y + PILL_H / 2;
    if (NET.receiving) {
        float lw = gfx_text_width("Receive", 0.45f);
        ui_progress_bar(x + 31, PILL_Y + PILL_H - 6, lw, 2, app_rx_progress(), FILL3, LISTEN_GREEN);
        gfx_circle(dx, dy, 2.6f, rgba_alpha(LISTEN_GREEN, 0.6f + 0.4f * sinf(E.time * 6)));
    } else if (NET.listening) {
        gfx_circle(dx, dy, 2.4f, LISTEN_GREEN);
    }
}

/* Carousel tile i at offset o: where that game was left. */
static void draw_snap_tile(int i, float o)
{
    float x0 = 160 + o * CT_STEP - CT_W / 2, y0 = CT_Y;
    GfxTex *snap = i < E.ngames ? E.game_thumb[i] : NULL;
    bool started = snap && i < E.ngames && E.game_resume[i].used;
    if (fabsf(o) < 0.5f)
        ring(x0, y0, CT_W, CT_H, 1);
    if (started) {
        picture(snap, NULL, x0, y0, CT_W, CT_H, fabsf(o) < 0.5f ? white_bg : bot_bg_at, 1);
    } else {   /* not started: its cover, quietly */
        picture(cover_of(i), title_of(i), x0, y0, CT_W, CT_H, fabsf(o) < 0.5f ? white_bg : bot_bg_at, 1);
        if (!arriving(i)) {
            ui_rrect(x0, y0, CT_W, CT_H, CORNER(CT_W), RGBA(0, 0, 0, 120));
            ui_text_centered("Not started yet", x0 + CT_W / 2, y0 + CT_H / 2 - 7, 0.5f, WHITE);
        }
    }
    if (arriving(i))
        arriving_veil(x0, y0, CT_W, CT_H);
    if (fabsf(o) > 0.5f)
        ui_rrect(x0, y0, CT_W, CT_H, CORNER(CT_W), RGBA(0, 0, 0, (u8)(130 * fminf(fabsf(o), 1))));
}

static void draw_carousel(void)
{
    int n = app_home_count();
    if (n == 0) {   /* first run: the demo's card and A to download it */
        float x0 = 160 - CT_W / 2;
        ui_rrect(x0, CT_Y, CT_W, CT_H, CORNER(CT_W), FILL1);
        ui_text_centered("No games yet", 160, CT_Y + 30, 0.55f, WHITE);
        ui_text_centered(FETCH.busy ? "Connecting..." : "A: download the demo, Snapshot\nY: receive a game over Wi-Fi\n\nMore games: vn3ds.com",
                         160, CT_Y + 56, 0.42f, INK2);
        a_button(A_X, A_Y, FETCH.busy ? 0.4f : 1);
        y_pill();
        return;
    }
    for (int i = 0; i < n; i++) {
        float o = (float)i - E.cf_pos;
        if (fabsf(o) < 1.9f)
            draw_snap_tile(i, o);
    }
    a_button(A_X, A_Y, arriving(E.game_sel) ? 0.4f : 1);
    pill(8, "X", "Title screen", arriving(E.game_sel) ? 0.4f : 1);
    y_pill();
}

static void draw_bottom_grid(void)
{
    int n = app_home_count();
    for (int i = 0; i < n; i++) {
        float x0 = 8 + (float)(i % 3) * G_STEPX, y0 = 8 + ((float)(i / 3) - H.gscroll) * G_STEPY;
        if (y0 > BOT_H || y0 + G_H < 0)
            continue;
        bool chosen = i == E.game_sel;
        if (chosen)
            ring(x0, y0, G_W, G_H, 1);
        picture(cover_of(i), title_of(i), x0, y0, G_W, G_H, chosen ? white_bg : bot_bg_at, 1);
        if (arriving(i))
            ui_rrect(x0, y0, G_W, G_H, CORNER(G_W), RGBA(0, 0, 0, 130));
    }
}

static void draw_strip(void)
{
    if (H.count == 0) {
        ui_rrect(ST_X - ST_W / 2, TA_Y - ST_H / 2, ST_W, ST_H, CORNER(ST_W), FILL1);
        ui_text_centered("Nothing here yet", ST_X, TA_Y - 8, 0.5f, INK2);
        return;
    }
    /* the strip's thread, through every picture */
    gfx_line(ST_X, 0, ST_X, BOT_H, 1.6f, VINE);
    for (int i = 0; i < H.count; i++) {
        float o = (float)i - H.pos;
        if (fabsf(o) > 1.9f)
            continue;
        float x0 = ST_X - ST_W / 2, y0 = TA_Y + o * ST_STEP - ST_H / 2;
        bool chosen = fabsf(o) < 0.5f;
        if (chosen)
            ring(x0, y0, ST_W, ST_H, 1);
        GfxTex *t = entry_tex(i);
        picture(t, t ? NULL : "...", x0, y0, ST_W, ST_H, chosen ? white_bg : bot_bg_at, 1);
        if (!chosen)
            ui_rrect(x0, y0, ST_W, ST_H, CORNER(ST_W), RGBA(0, 0, 0, (u8)(130 * fminf(fabsf(o), 1))));
        char label[24];   /* its place, on a small tag in the corner */
        entry_label(i, label, sizeof(label));
        float lw = gfx_text_width(label, 0.38f) + 14;
        ui_rrect(x0 + 6, y0 + 6, lw, 17, 8.5f, RGBA(0, 0, 0, 160));
        gfx_text(label, x0 + 13, y0 + 6 + (17 - gfx_line_height(0.38f)) / 2, 0.38f, WHITE);
    }
    a_button(TA_X, TA_Y, 1);
}

void home_draw_bottom(void)
{
    switch (H.mode) {
    case HM_CAROUSEL: draw_carousel(); break;
    case HM_GRID: draw_bottom_grid(); break;
    case HM_TIMELINE: draw_strip(); break;
    }
    if (H.mode_t < 0.2f && E.screen == SCR_GAMELIST)
        gfx_rect(0, 0, BOT_W, BOT_H, RGBA(0, 0, 0, (u8)(255 * (1 - H.mode_t / 0.2f))));
}
