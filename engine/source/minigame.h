#pragma once
#include "app.h"

/* Minigames: small native games a script starts with
 *
 *     $ score = vn3ds_minigame("snake")
 *
 * vnpack compiles that call; on PC, Ren'Py runs a vn3ds_minigame() the game
 * defines itself. The same games can be played from the title screen's
 * Minigames menu to chase high scores.
 *
 * A game only implements the MiniGame callbacks. The framework (minigame.c)
 * shows the intro card (title, rules, controls, cheat), runs the game,
 * pauses with START, offers the cheat (L, R, SELECT or the Cheat button on
 * the touch screen; at most one per run), then shows the result and keeps
 * the best score. A game must not use L, R, SELECT or START itself.
 *
 * Cheats in the story come from a pool: the script variable `vn3ds_cheats`
 * (the game hands them out at milestones, e.g. `$ vn3ds_cheats += 1`); using
 * one spends it. Free play from the Minigames menu allows one per run.
 *
 * Coordinates: the top screen is 400x240, the bottom 320x240. Use the mg_*
 * drawing helpers on the top screen so everything gets stereo depth:
 * depth 0 is the screen surface, positive is behind it (+1 is far), negative
 * pops out (-0.5 is about as near as is comfortable). */

typedef struct {
    const char *id;       /* "snake": the name scripts use */
    const char *title;    /* shown on the intro card and in menus */
    const char *rules;    /* a few short lines, '\n' separated */
    const char *controls; /* e.g. "D-pad / Circle Pad: steer\nA: dash" */
    const char *cheat;    /* what the one cheat does, e.g. "Skip a question" */
    const char *music;    /* loop in game/audio/minigame/ (no extension), or NULL */

    void (*start)(u32 seed);
    /* One step of play. `cheat` is true on the single frame the player uses
     * the cheat (at most once per run). Return false when the run is over. */
    bool (*update)(const Input *in, float dt, bool cheat);
    void (*draw_top)(int eye);
    void (*draw_bottom)(void); /* may be NULL: the framework draws a HUD */
    /* Optional: called before draw_top with the eye's off-screen capture
     * (400x240) as the target. Draw there, then in draw_top show pieces of it
     * with gfx_draw_capture_part() for split views and distortions. */
    void (*draw_offscreen)(int eye);
    int (*score)(void);        /* 0..100 once update() returned false */
    /* Optional: one line under the score, e.g. "Crowned in 112% of the
     * shortest route". NULL or "" for none. */
    const char *(*verdict)(void);
    /* Optional: return false while the cheat can't help (e.g. during a
     * death or victory animation) so it isn't spent for nothing. */
    bool (*can_cheat)(void);
    /* Optional: plausible input for automated tests and recordings
     * (vn3ds-host --minigame <id>). `t` is seconds since the run started. */
    void (*bot)(Input *in, float t);
} MiniGame;

/* ---- registry ------------------------------------------------------------- */

const MiniGame *mg_find(const char *id);
int mg_count(void);
const MiniGame *mg_at(int i);

/* ---- running (app.c / ui.c) --------------------------------------------- */

typedef enum { MG_INTRO, MG_PLAY, MG_PAUSED, MG_RESULT } MgPhase;

typedef struct {
    const MiniGame *game;
    MgPhase phase;
    bool from_story;      /* started by the script (score goes back to it) */
    bool cheat_used;      /* at most one cheat per run */
    int cheats_left;      /* story: the script's vn3ds_cheats pool; free play: 1 */
    float t;              /* seconds in MG_PLAY */
    int score;
    int best_before;
    char verdict[128];
    float rt;             /* seconds on the result screen */
    float board_t0;       /* when the online board started scrolling (-1: not yet) */
    float scroll;         /* board scroll position, in rows */
    int scroll_ticks;
    bool landed;
    s32 music_before;     /* story music to restore afterwards */
    bool music_loop_before;
    int pause_sel;
    bool posted;          /* the score went to the online leaderboard (leaderboard.h) */
    int port;             /* PORT entry of a ported game (see below), -1 for the others */
    bool hud;             /* started from the story's on-screen overlay button, not the script */
} MgRun;

extern MgRun MG;

/* Begin a run; `from_story` returns the score to the VM when it ends. */
void mg_begin(const MiniGame *g, bool from_story);
void mg_update(const Input *in, float dt);
void mg_draw_top(int eye);
void mg_draw_bottom(void);
/* Best score for a game in the loaded game's save folder, -1 if none. */
int mg_best(const char *id);
/* Your own scores for a game: the first story run (-1 if not played yet)
 * and the best free-play runs, best first (returns how many). */
int mg_scores(const char *id, int *story, int *runs, int max);

/* ---- helpers for games ---------------------------------------------------- */

/* Horizontal shift of something at `depth` for the eye being drawn. */
float mg_shift(int eye, float depth);
void mg_rect(int eye, float x, float y, float w, float h, float depth, u32 rgba);
void mg_circle(int eye, float x, float y, float r, float depth, u32 rgba);
void mg_tri(int eye, float x0, float y0, float x1, float y1, float x2, float y2, float depth,
            u32 rgba);
void mg_line(int eye, float x0, float y0, float x1, float y1, float thick, float depth, u32 rgba);
void mg_text(int eye, const char *s, float x, float y, float scale, float depth, u32 rgba);
void mg_text_centered(int eye, const char *s, float cx, float y, float scale, float depth, u32 rgba);
/* Background helpers (no depth argument: drawn far behind, at +1). */
void mg_sky(int eye, u32 top, u32 bottom);

/* Desktop test hook: when non-zero, every run's random numbers start from
 * this seed instead of the clock (vn3ds-host --mg-seed). */
extern u32 mg_test_seed;

/* Deterministic random numbers, reseeded by mg_begin(). */
u32 mg_rand(void);
float mg_randf(void);                 /* 0..1 */
int mg_randi(int lo, int hi);         /* lo..hi inclusive */

/* Sound: files in game/audio/minigame/ by name without extension. */
void mg_sfx(const char *name);        /* one-shot; several can overlap */
void mg_sfx_pitch(const char *name, float rate);   /* rate 1 = as recorded */
void mg_music(const char *name);      /* switch the music loop (e.g. per level) */

/* ---- ported minigames ---------------------------------------------------
 *
 * Games rebuilt from a ported game's own custom screens (a lockpick, an
 * instrument, ...). vnpack compiles `call screen <name>` into
 * vn3ds_minigame("@i"), where i is an entry of the game's PORT table: the
 * mechanic (a MiniGame id from the ported list in minigame.c) and its
 * parameters, art and sounds, all from the game's own files (see
 * tools/vnpack/ported.py). A ported game starts straight away and ends
 * straight back in the story: no intro or result card, no cheats, no
 * scores, no Minigames menu entry. Its result goes back to the story
 * through the script's variables, the way the original screen set them.
 *
 * Sounds: the entry's sounds are its named audio "minigame/@i_<name>", so
 * mg_sfx("<name>") plays them like any minigame's own clips; clips named
 * "loop_<name>" are streamed instead (mg_sound_loop). */

/* Overlays: a game's persistent on-screen button (Ren'Py `show screen X`
 * where X is a launcher an adapter names, e.g. Eternum's audio logs). The
 * script keeps the shown overlay's PORT entry in the story variable
 * _vn3ds_hud ("@i", "" when hidden), so it is saved with the game. Its
 * entry (mechanic "loglist") gives the button's label and the list it
 * opens: each item a ported entry (e.g. captions over a recording) played
 * on demand, which sets the variables its original screen set when it is
 * played to the end ("set" parameters, "var=value"). The story waits on its
 * current line meanwhile and carries on from there afterwards. */
int mg_hud_entry(void);            /* the shown overlay's entry, or -1 */
const char *mg_hud_label(void);    /* its button's label */
void mg_hud_open(void);            /* the button was pressed */
/* Starts PORT entry `index` from the overlay (not the script). */
bool mg_begin_port(int index);

/* The entry's parameters: the first value of `key`, or NULL / `def`. */
const char *mg_param(const char *key);
float mg_paramf(const char *key, float def);
/* Every value of a repeated key, in order; returns how many. */
int mg_param_all(const char *key, const char **out, int max);
/* Story variables by name (NULL / `def` when the script has no such variable). */
Value *mg_var(const char *name);
double mg_var_num(const char *name, double def);
const char *mg_var_str(const char *name);
void mg_var_set_num(const char *name, double v);
void mg_var_set_bool(const char *name, bool v);
void mg_var_set_str(const char *name, const char *v);
/* One of the game's images by the name the script shows it by ("bg room"),
 * loaded through the texture cache; *w, *h get its size in top-screen px
 * (the story's scale). NULL if the game has no such image. */
GfxTex *mg_image(const char *spec, float *w, float *h);
/* A looping clip "loop_<name>" of the entry, streamed on the story's sound
 * channel (one at a time; not in the decoded bank). NULL stops it. */
void mg_sound_loop(const char *name);

/* The framework's Cheat button on the bottom screen: keep touch areas clear
 * of it (taps there are the cheat, not your game's input). */
#define MG_CHEAT_X 236
#define MG_CHEAT_Y 206
#define MG_CHEAT_W 78
#define MG_CHEAT_H 28

/* Common colours. */
#define MG_WHITE RGBA(255, 255, 255, 255)
#define MG_INK RGBA(30, 28, 40, 255)
#define MG_GOLD RGBA(255, 210, 110, 255)
