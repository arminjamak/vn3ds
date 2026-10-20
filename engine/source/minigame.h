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
 * pauses with START, gives one cheat per run (L, R, SELECT or the Cheat
 * button on the touch screen), then shows the result and keeps the best
 * score. A game must not use L, R, SELECT or START itself.
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
    bool cheat_used;
    float t;              /* seconds in MG_PLAY */
    int score;
    int best_before;
    char verdict[128];
    s32 music_before;     /* story music to restore afterwards */
    bool music_loop_before;
    int pause_sel;
} MgRun;

extern MgRun MG;

/* Begin a run; `from_story` returns the score to the VM when it ends. */
void mg_begin(const MiniGame *g, bool from_story);
void mg_update(const Input *in, float dt);
void mg_draw_top(int eye);
void mg_draw_bottom(void);
/* Best score for a game in the loaded game's save folder, -1 if none. */
int mg_best(const char *id);

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

/* Deterministic random numbers, reseeded by mg_begin(). */
u32 mg_rand(void);
float mg_randf(void);                 /* 0..1 */
int mg_randi(int lo, int hi);         /* lo..hi inclusive */

/* Sound: files in game/audio/minigame/ by name without extension. */
void mg_sfx(const char *name);        /* one-shot on the sound channel */
void mg_music(const char *name);      /* switch the music loop (e.g. per level) */

/* Common colours. */
#define MG_WHITE RGBA(255, 255, 255, 255)
#define MG_INK RGBA(30, 28, 40, 255)
#define MG_GOLD RGBA(255, 210, 110, 255)
