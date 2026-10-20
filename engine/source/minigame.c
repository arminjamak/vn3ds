/* Minigame framework: intro card, play, pause, one cheat, result, high
 * scores. The games themselves live in mg_*.c; see minigame.h. */

#include "minigame.h"

#include <stdio.h>

extern const MiniGame MG_QUIZ, MG_DRAW, MG_INVADERS, MG_TOWER, MG_SNAKE, MG_MISO, MG_LANTERN;

/* Menu order. */
static const MiniGame *const GAMES[] = {
    &MG_QUIZ, &MG_MISO, &MG_DRAW, &MG_LANTERN, &MG_SNAKE, &MG_TOWER, &MG_INVADERS,
};

MgRun MG;

const MiniGame *mg_find(const char *id)
{
    for (unsigned i = 0; i < ARRAY_LEN(GAMES); i++)
        if (!strcmp(GAMES[i]->id, id))
            return GAMES[i];
    return NULL;
}

int mg_count(void) { return (int)ARRAY_LEN(GAMES); }
const MiniGame *mg_at(int i) { return i >= 0 && i < mg_count() ? GAMES[i] : NULL; }

/* ---- high scores ------------------------------------------------------- */

static void best_path(char *out, size_t len)
{
    snprintf(out, len, "%s/saves/%s/minigames.cfg", E.root, E.loaded ? E.game.id : "_");
}

int mg_best(const char *id)
{
    char path[400], line[128];
    best_path(path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (!f)
        return -1;
    int best = -1;
    while (fgets(line, sizeof(line), f)) {
        char key[64];
        int v;
        if (sscanf(line, " %63[^ =] = %d", key, &v) == 2 && !strcmp(key, id))
            best = v;
    }
    fclose(f);
    return best;
}

static void save_best(const char *id, int score)
{
    char path[400], dir[400];
    int vals[32];
    const MiniGame *g;
    for (int i = 0; i < mg_count() && i < 32; i++)
        vals[i] = mg_best(mg_at(i)->id);
    for (int i = 0; i < mg_count() && i < 32; i++)
        if (!strcmp(mg_at(i)->id, id) && score > vals[i])
            vals[i] = score;
    snprintf(dir, sizeof(dir), "%s/saves", E.root);
    platform_mkdir(dir);
    snprintf(dir, sizeof(dir), "%s/saves/%s", E.root, E.loaded ? E.game.id : "_");
    platform_mkdir(dir);
    best_path(path, sizeof(path));
    FILE *f = fopen(path, "w");
    if (!f)
        return;
    for (int i = 0; i < mg_count() && i < 32; i++)
        if ((g = mg_at(i)) && vals[i] >= 0)
            fprintf(f, "%s = %d\n", g->id, vals[i]);
    fclose(f);
}

/* ---- random ------------------------------------------------------------------ */

static u32 rng = 0x9E3779B9u;

u32 mg_rand(void)
{
    rng ^= rng << 13;
    rng ^= rng >> 17;
    rng ^= rng << 5;
    return rng;
}

float mg_randf(void) { return (float)(mg_rand() >> 8) / 16777216.0f; }

int mg_randi(int lo, int hi)
{
    if (hi <= lo)
        return lo;
    return lo + (int)(mg_rand() % (u32)(hi - lo + 1));
}

/* ---- sound -------------------------------------------------------------------- */

static void play_named(int ch, const char *name, bool loop)
{
    if (!E.loaded || !name)
        return;
    char full[96], path[400];
    snprintf(full, sizeof(full), "minigame/%s", name);
    s32 res = game_audio_named(&E.game, full);
    if (res < 0)
        return;
    game_res_path(&E.game, res, path, sizeof(path));
    audio_play(ch, path, loop, ch == CH_MUSIC ? 0.4f : 0.0f, false);
}

void mg_sfx(const char *name) { play_named(CH_SOUND, name, false); }
void mg_music(const char *name) { play_named(CH_MUSIC, name, true); }

/* ---- drawing helpers ---------------------------------------------------------- */

float mg_shift(int eye, float depth)
{
    return (eye == EYE_LEFT ? -1.0f : 1.0f) * depth * app_strength();
}

void mg_rect(int eye, float x, float y, float w, float h, float depth, u32 c)
{
    gfx_rect(x + mg_shift(eye, depth), y, w, h, c);
}

void mg_circle(int eye, float x, float y, float r, float depth, u32 c)
{
    gfx_circle(x + mg_shift(eye, depth), y, r, c);
}

void mg_tri(int eye, float x0, float y0, float x1, float y1, float x2, float y2, float depth, u32 c)
{
    float s = mg_shift(eye, depth);
    gfx_triangle(x0 + s, y0, x1 + s, y1, x2 + s, y2, c);
}

void mg_line(int eye, float x0, float y0, float x1, float y1, float thick, float depth, u32 c)
{
    float s = mg_shift(eye, depth);
    gfx_line(x0 + s, y0, x1 + s, y1, thick, c);
}

void mg_text(int eye, const char *s, float x, float y, float scale, float depth, u32 c)
{
    gfx_text(s, x + mg_shift(eye, depth), y, scale, c);
}

void mg_text_centered(int eye, const char *s, float cx, float y, float scale, float depth, u32 c)
{
    char line[256];
    float lh = gfx_line_height(scale), sh = mg_shift(eye, depth);
    while (*s) {
        size_t n = strcspn(s, "\n");
        size_t k = n < sizeof(line) - 1 ? n : sizeof(line) - 1;
        memcpy(line, s, k);
        line[k] = 0;
        gfx_text(line, cx - gfx_text_width(line, scale) / 2 + sh, y, scale, c);
        y += lh;
        s += n;
        if (*s == '\n')
            s++;
    }
}

void mg_sky(int eye, u32 top, u32 bottom)
{
    (void)eye;   /* a flat fill has no visible disparity */
    gfx_gradient(0, 0, TOP_W, TOP_H, top, bottom);
}

/* ---- the run ---------------------------------------------------------------------- */

/* Touch areas on the bottom screen. */
#define CHEAT_X 236
#define CHEAT_Y 206
#define CHEAT_W 78
#define CHEAT_H 28

static bool touched(const Input *in, float x, float y, float w, float h)
{
    return (in->down & KEY_TOUCH_) && in->tx >= x && in->tx < x + w && in->ty >= y && in->ty < y + h;
}

void mg_begin(const MiniGame *g, bool from_story)
{
    memset(&MG, 0, sizeof(MG));
    MG.game = g;
    MG.from_story = from_story;
    MG.phase = MG_INTRO;
    MG.best_before = mg_best(g->id);
    MG.music_before = E.music_res;
    MG.music_loop_before = E.music_loop;
    E.screen = SCR_MINIGAME;
    talk_end();
}

static void start_play(void)
{
    rng = (platform_time() * 2654435761u) ^ (E.frame * 40503u) ^ 0x51ED270Bu;
    if (!rng)
        rng = 1;
    MG.phase = MG_PLAY;
    MG.t = 0;
    MG.cheat_used = false;
    MG.verdict[0] = 0;
    if (MG.game->music)
        mg_music(MG.game->music);
    MG.game->start(mg_rand());
}

static void finish(void)
{
    MG.score = MG.game->score ? MG.game->score() : 0;
    MG.score = MG.score < 0 ? 0 : (MG.score > 100 ? 100 : MG.score);
    const char *v = MG.game->verdict ? MG.game->verdict() : NULL;
    snprintf(MG.verdict, sizeof(MG.verdict), "%s", v ? v : "");
    save_best(MG.game->id, MG.score);
    MG.phase = MG_RESULT;
    mg_sfx("result");
}

static void leave(void)
{
    /* restore the story's music */
    audio_stop(CH_SOUND, 0);
    if (MG.from_story) {
        if (MG.music_before >= 0) {
            char path[400];
            game_res_path(&E.game, MG.music_before, path, sizeof(path));
            audio_play(CH_MUSIC, path, MG.music_loop_before, 1.0f, false);
        } else {
            audio_stop(CH_MUSIC, 0.5f);
        }
        app_minigame_done(MG.score);
    } else {
        audio_stop(CH_MUSIC, 0.5f);
        E.music_res = -1;
        E.screen = SCR_MGMENU;
    }
}

void mg_update(const Input *in, float dt)
{
    const MiniGame *g = MG.game;
    switch (MG.phase) {
    case MG_INTRO:
        if ((in->down & KEY_A_) || touched(in, 170, 196, 140, 36))
            start_play();
        else if (!MG.from_story && ((in->down & KEY_B_) || touched(in, 10, 196, 140, 36)))
            leave();
        break;
    case MG_PLAY: {
        if (in->down & KEY_START_) {
            MG.phase = MG_PAUSED;
            MG.pause_sel = 0;
            break;
        }
        bool cheat = false;
        if (!MG.cheat_used && ((in->down & (KEY_L_ | KEY_R_ | KEY_SELECT_)) ||
                               touched(in, CHEAT_X, CHEAT_Y, CHEAT_W, CHEAT_H))) {
            cheat = MG.cheat_used = true;
            mg_sfx("cheat");
        }
        MG.t += dt;
        if (!g->update(in, dt, cheat))
            finish();
        break;
    }
    case MG_PAUSED: {
        int n = MG.from_story ? 2 : 3;   /* Resume, Restart, (Quit) */
        if (in->down & KEY_UP_)
            MG.pause_sel = (MG.pause_sel + n - 1) % n;
        if (in->down & KEY_DOWN_)
            MG.pause_sel = (MG.pause_sel + 1) % n;
        int pick = -1;
        if (in->down & KEY_A_)
            pick = MG.pause_sel;
        for (int i = 0; i < n; i++)
            if (touched(in, 60, 50 + i * 50, 200, 40))
                pick = i;
        if ((in->down & (KEY_START_ | KEY_B_)) || pick == 0)
            MG.phase = MG_PLAY;
        else if (pick == 1)
            start_play();
        else if (pick == 2)
            finish();
        break;
    }
    case MG_RESULT:
        if ((in->down & (KEY_A_ | KEY_B_)) || touched(in, 90, 196, 140, 36))
            leave();
        break;
    }
}

/* ---- drawing ---------------------------------------------------------------- */

static void card(int eye, const char *title, const char *body)
{
    gfx_gradient(0, 0, TOP_W, TOP_H, RGBA(24, 20, 44, 255), RGBA(70, 40, 90, 255));
    for (int i = 0; i < 24; i++) {   /* a few stars far behind */
        float x = (float)((i * 97 + 31) % TOP_W), y = (float)((i * 57 + 11) % TOP_H);
        gfx_rect(x + mg_shift(eye, 1.0f), y, 2, 2, RGBA(255, 255, 255, 90));
    }
    mg_text_centered(eye, title, TOP_W / 2, 26, 0.9f, -0.15f, MG_GOLD);
    mg_text_centered(eye, body, TOP_W / 2, 80, 0.5f, -0.05f, MG_WHITE);
}

void mg_draw_top(int eye)
{
    const MiniGame *g = MG.game;
    char buf[400];
    switch (MG.phase) {
    case MG_INTRO:
        card(eye, g->title, g->rules);
        break;
    case MG_PLAY:
    case MG_PAUSED:
        g->draw_top(eye);
        if (MG.phase == MG_PAUSED) {
            gfx_rect(0, 0, TOP_W, TOP_H, RGBA(0, 0, 0, 150));
            mg_text_centered(eye, "Paused", TOP_W / 2, 100, 0.9f, -0.2f, MG_WHITE);
        }
        break;
    case MG_RESULT: {
        snprintf(buf, sizeof(buf), "%s", g->title);
        card(eye, buf, "");
        snprintf(buf, sizeof(buf), "%d%%", MG.score);
        mg_text_centered(eye, buf, TOP_W / 2, 74, 1.6f, -0.35f, MG_WHITE);
        if (MG.verdict[0])
            mg_text_centered(eye, MG.verdict, TOP_W / 2, 140, 0.5f, -0.1f, RGBA(220, 220, 255, 255));
        if (MG.score > MG.best_before && MG.best_before >= 0)
            snprintf(buf, sizeof(buf), "New best! (was %d%%)", MG.best_before);
        else if (MG.best_before < 0)
            snprintf(buf, sizeof(buf), "First score on the board");
        else
            snprintf(buf, sizeof(buf), "Best: %d%%", MG.best_before);
        mg_text_centered(eye, buf, TOP_W / 2, 176, 0.55f, -0.1f, MG_GOLD);
        if (MG.cheat_used)
            mg_text_centered(eye, "(one cheat used)", TOP_W / 2, 204, 0.45f, 0, RGBA(200, 200, 200, 255));
        break;
    }
    }
}

static void bottom_button(float x, float y, float w, float h, const char *label, bool on)
{
    gfx_rect(x, y, w, h, on ? RGBA(255, 255, 255, 235) : RGBA(255, 255, 255, 40));
    float sc = 0.5f, lh = gfx_line_height(sc);
    gfx_text(label, x + (w - gfx_text_width(label, sc)) / 2, y + (h - lh) / 2, sc,
             on ? RGBA(20, 20, 30, 255) : MG_WHITE);
}

static void bottom_text(const char *s, float x, float y, float scale, u32 c)
{
    char line[256];
    float lh = gfx_line_height(scale);
    while (*s) {
        size_t n = strcspn(s, "\n");
        size_t k = n < sizeof(line) - 1 ? n : sizeof(line) - 1;
        memcpy(line, s, k);
        line[k] = 0;
        gfx_text(line, x, y, scale, c);
        y += lh;
        s += n;
        if (*s == '\n')
            s++;
    }
}

void mg_draw_bottom(void)
{
    const MiniGame *g = MG.game;
    char buf[200];
    gfx_gradient(0, 0, BOT_W, BOT_H, RGBA(20, 18, 34, 255), RGBA(36, 30, 56, 255));
    switch (MG.phase) {
    case MG_INTRO:
        gfx_text("Controls", 14, 10, 0.55f, MG_GOLD);
        bottom_text(g->controls, 14, 34, 0.45f, MG_WHITE);
        snprintf(buf, sizeof(buf), "Cheat (once): %s\nL, R, SELECT or tap Cheat", g->cheat);
        bottom_text(buf, 14, 132, 0.45f, RGBA(255, 200, 150, 255));
        if (!MG.from_story)
            bottom_button(10, 196, 140, 36, "B: Back", false);
        bottom_button(170, 196, 140, 36, "A: Start", true);
        break;
    case MG_PLAY:
        if (g->draw_bottom) {
            g->draw_bottom();
        } else {
            gfx_text(g->title, 14, 12, 0.55f, MG_GOLD);
            snprintf(buf, sizeof(buf), "%d:%02d", (int)MG.t / 60, (int)MG.t % 60);
            gfx_text(buf, 14, 40, 0.5f, MG_WHITE);
            gfx_text("START: pause", 14, 180, 0.45f, RGBA(180, 180, 200, 255));
        }
        if (!MG.cheat_used)
            bottom_button(CHEAT_X, CHEAT_Y, CHEAT_W, CHEAT_H, "Cheat", false);
        break;
    case MG_PAUSED: {
        static const char *items[] = {"Resume", "Restart", "Quit (score so far)"};
        int n = MG.from_story ? 2 : 3;
        for (int i = 0; i < n; i++)
            bottom_button(60, 50 + i * 50, 200, 40, items[i], i == MG.pause_sel);
        break;
    }
    case MG_RESULT:
        gfx_text(g->title, 14, 12, 0.55f, MG_GOLD);
        snprintf(buf, sizeof(buf), "Score %d%%", MG.score);
        gfx_text(buf, 14, 44, 0.6f, MG_WHITE);
        bottom_button(90, 196, 140, 36, "A: Continue", true);
        break;
    }
}
