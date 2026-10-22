#pragma once
#include "audio.h"
#include "game.h"
#include "gfx.h"
#include "platform.h"
#include "stage.h"
#include "vm.h"

#define MAX_GAMES 32
#define HIST_MAX 100
#define SLOTS_PER_PAGE 6
#define SLOT_PAGES 5
#define NUM_PREFS 8

typedef enum {
    SCR_GAMELIST, SCR_TITLE, SCR_GAME, SCR_ERROR, SCR_RECEIVE,
    SCR_MINIGAME, /* a minigame is running (minigame.c) */
    SCR_MGMENU,   /* the title screen's Minigames list */
} Screen;
typedef enum { OV_NONE, OV_LOG, OV_SAVE, OV_LOAD, OV_PREFS } Overlay;
enum { WIN_AUTO = 0, WIN_SHOW = 1, WIN_HIDE = 2 };

typedef struct {
    char who[64];
    u32 who_color;
    char text[512];
} HistEntry;

typedef struct {
    int text_speed; /* index into TEXT_SPEEDS */
    float auto_delay;
    float depth_mult;
    float box_alpha;
    float music_vol, sound_vol;
} Settings;

typedef struct {
    bool used;
    u32 time;
    char preview[96];
} SlotInfo;

typedef struct {
    bool active;
    const TransDef *def;
    float t, dur;
    Stage old;
    bool need_capture;
    float off[MAX_SPRITES][2];   /* MOVE: start offset of each new-stage sprite */
    int leaving[MAX_SPRITES];    /* MOVEOUT: old-stage sprites that leave */
    float loff[MAX_SPRITES][2];
    int nleaving;
} Transition;

typedef struct {
    float x, y, w, h;
    const char *label;
    int id;
    bool hot, on, disabled;
} Button;

typedef struct {
    Screen screen;
    Overlay overlay;
    char root[256];

    char games[MAX_GAMES][64];
    char game_titles[MAX_GAMES][96];
    /* a novel exported as its own app (link.h): its .3dsx and the folder with
     * its saves and cover; "" for a game in games/ */
    char game_app[MAX_GAMES][200];
    char game_app_dir[MAX_GAMES][200];
    int ngames, game_sel;
    /* the home screen's coverflow: where each game was left */
    float cf_pos;
    GfxTex *game_thumb[MAX_GAMES];   /* the resume snapshot */
    GfxTex *game_cover[MAX_GAMES];   /* the game's own cover (cover.thm, made by vnpack) */
    SlotInfo game_resume[MAX_GAMES];
    float autosave_t;
    u32 story_step;       /* lines read since the story began (story.c) */
    bool has_resume;      /* the loaded game has a resume save (title: Continue) */
    /* opening a game: a "Preparing ..." card once it takes longer than a moment */
    bool opening;
    char opening_title[64], opening_step[64];
    float opening_frac;   /* 0..1, or < 0 when unknown */

    Game game;
    bool loaded;
    VM vm;
    Stage stage, committed;
    Transition tr;
    Settings set;

    /* dialogue being shown */
    char wrapped[VM_TEXT * 2];
    float text_scale;
    size_t text_cps_len;
    float text_shown;
    bool text_done;
    float auto_timer;
    bool skip, skip_toggle, auto_mode, hide_ui;
    u8 window_mode;
    float pause_left;
    int menu_sel;
    float punch_x, punch_y;

    HistEntry hist[HIST_MAX];
    int hist_n;
    int log_scroll;

    s32 music_res;
    bool music_loop;
    bool voice_pending;

    int slot_page, slot_sel;
    SlotInfo slots[SLOTS_PER_PAGE];
    int prefs_sel;
    int title_sel;
    int mg_sel;

    /* Wi-Fi transfers run in the background while you play: a corner icon
     * shows one is going, and the home screen lists the arriving game with
     * its progress. A game that isn't in the list yet gets an extra card at
     * the end (index ngames). */
    bool rx_new;              /* the arriving game is new: show its card */
    char rx_new_id[64];
    char rx_new_title[96];
    GfxTex *rx_new_cover;     /* its cover, once that file is in */
    float rx_rate;            /* bytes per second, smoothed; 0 until known */
    bool mg_board;   /* Minigames menu: the online leaderboard is showing */
    char toast[96];
    float toast_t;
    char error[300];

    float time;
    u32 frame;
    u32 say_serial; /* bumps on every new line of dialogue */
    bool quit;
} Engine;

extern Engine E;

/* What the current frame cost the main thread, for the timing log: textures
 * loaded on the spot (not preloaded), and the music calls. */
typedef struct {
    u32 tex_sync;       /* textures read and decoded on the main thread */
    u32 tex_sync_bytes; /* their file sizes */
    u64 tex_sync_us;
    u32 tex_ready;      /* preloaded textures that were used for the first time */
    u64 music_us;       /* time in audio_play / audio_stop / the music changes */
    u64 save_us;        /* autosave */
    bool advanced;      /* the story moved on this frame (A, auto, skip...) */
} FramePerf;
extern FramePerf FP;
extern const float TEXT_SPEEDS[];
extern const int NUM_TEXT_SPEEDS;

void app_init(const char *game_dir);
/* Wi-Fi receive screen (games and engine updates from vn3ds-port --3ds). */
void app_receive_open(void);
void app_receive_close(void);
/* Quitting a novel inside vn3ds: back to the library with its card selected. */
void app_to_library(void);
/* Resume: slot 0 is the automatic save (on HOME, quitting, leaving a game,
 * and every two minutes), with a snapshot of the screen for the home menu. */
#define RESUME_SLOT 0
#define THUMB_W 200
#define THUMB_H 120
void app_autosave(void);
void app_play_game(int index);   /* carry on where you left off */
bool app_has_resume(void);       /* for the loaded game */
/* Cards on the home screen: the games, plus one for a new game arriving. */
int app_home_count(void);
/* True while a transfer is writing this game's files (it can't be opened yet). */
bool app_rx_busy(const char *id);
float app_rx_progress(void);      /* 0..1 of the current transfer */
/* "about 3 min left" and the like; "" while the speed isn't known yet. */
void app_rx_eta_text(char *out, size_t len);
void app_rescan_games(void);
extern bool app_start_receiving; /* set before app_init, e.g. when launched via 3dslink */
extern bool app_listen_background; /* accept transfers at any time (3DS default) */
/* A standalone app (vn3ds-port --app), set before app_init: the one game it
 * carries is opened at once, and there is no library, home or receive screen. */
extern bool app_single_game;
/* "Export as app" (export.h): the open library game as sdmc:/3ds/<id>.3dsx. */
bool app_can_export(void);
void app_export_game(void);
void app_update(const Input *in, float dt);
void app_render(void);
void app_frame_done_without_drawing(void);   /* (desktop tests: instead of app_render) */
void app_shutdown(void);

/* app.c */
void app_toast(const char *msg);
bool app_load_game(int index);
void app_to_title(void);
void app_new_game(void);
bool app_new_game_at(const char *label); /* debugging: skip to a label */
bool app_story_jump(const char *label);
bool app_load_slot(int slot);
void app_choose(int choice);
void app_error(const char *msg);
/* A minigame started by the script ended: hand its score to the VM. */
void app_minigame_done(int score);
float app_strength(void);

/* ui.c */
int ui_buttons(Button *out, int max);
/* The title screen's entries (button ids) in order; returns how many. */
int ui_title_items(int *ids);
void ui_activate(int id);
/* Minigames menu: show (or refresh) the selected game's online leaderboard. */
void ui_mg_board(void);
void ui_overlay_input(const Input *in);
void ui_draw_top(int eye);
void ui_draw_rx_icon(int eye);   /* corner icon while a transfer runs */
void ui_draw_opening(int eye);   /* "Preparing ..." while a game opens (eye -1: bottom) */
/* A filled rounded rectangle (buttons, cards, panels). */
void ui_rrect(float x, float y, float w, float h, float r, u32 c);
void ui_draw_bottom(void);
/* Drawing helpers for home.c. */
void ui_round_corners(float x, float y, float w, float h, float r, u32 top, u32 bottom);
void ui_text_centered(const char *s, float cx, float y, float scale, u32 color);
float ui_fit_scale(const char *s, float scale, float width);
u32 ui_mix(u32 a, u32 b, float t);
void ui_progress_bar(float x, float y, float w, float h, float p, u32 track, u32 fill);
void ui_download_glyph(float cx, float cy, float s, u32 c);
void ui_wrap(const char *src, float width, float scale, char *out, size_t len);
int ui_count_lines(const char *s);
void ui_hist_add(const char *who, u32 color, const char *text, bool extend);

/* render.c */
void render_stage(const Stage *st, int eye, const float (*off)[2], float offk);
void render_sprite(const Sprite *s, int eye, int rank, float dx, float dy);
void render_scene(int eye);

/* talk.c */
void talk_begin(void);
void talk_update(float dt);
void talk_end(void);
void talk_load_bank(void);

/* texcache.c */
GfxTex *texcache_get(s32 res);
/* An image's texture (its base picture with its patch put in, if any). */
GfxTex *texcache_image(const ImageDef *im);
void texcache_clear(void);
void texcache_init(void);
/* Once a frame: hands preloads their memory, caches finished ones. */
void texcache_pump(void);
/* Preloading (see texcache.c): a prediction pass is want_begin, want for
 * each picture in the order it may be needed, want_end. */
void texcache_want_begin(void);
void texcache_want(const ImageDef *im);
void texcache_want_end(void);

/* save.c */
bool save_write(int slot);
/* background: the file is written by the background thread (autosaves). */
bool save_write_ex(int slot, bool background);
bool save_peek(const char *game_id, int slot, SlotInfo *info);
bool save_peek_at(const char *root, const char *game_id, int slot, SlotInfo *info);
bool save_read(int slot);
void save_scan(int page, SlotInfo out[SLOTS_PER_PAGE]);
void settings_load(void);
void settings_save(void);

/* story.c: story points, the home screen's timeline. Each is a save in slot
 * STORY_SLOT0 + k with a STORY_W x STORY_H snapshot. */
#define STORY_SLOT0 100
#define STORY_MAX 40
#define STORY_W 160
#define STORY_H 96
typedef struct {
    u16 k, pad;   /* its slot: STORY_SLOT0 + k */
    u32 pc;       /* where in the script (the line's address) */
    u32 step;     /* E.story_step there */
    u32 time;
    char preview[96];
} StoryPoint;
/* Any game's points, in story order; returns how many. */
int story_read(const char *game_id, StoryPoint *out, int max);
void story_thumb_path(const char *id, int k, char *out, size_t len);
void story_game_opened(void);
u32 story_latest_step(void);   /* for saves from before story steps */
void story_scene(void);        /* a `scene` ran */
void story_snapshot(void);     /* a line's snapshot is being taken */
void story_thumb(const u16 *px, int w, int h);   /* ...and here it is */

/* home.c: the home screen (SCR_GAMELIST). */
void home_update(const Input *in, float dt);
void home_draw_top(int eye);
void home_draw_bottom(void);
void home_reset(void);   /* the game list changed */
void app_home_refresh_loaded(void);   /* re-reads where the open game was left */
/* A picture in a .thm file (snapshots, covers), or NULL. */
GfxTex *app_load_thm(const char *path);
