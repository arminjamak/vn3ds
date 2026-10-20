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
    int ngames, game_sel;

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
extern const float TEXT_SPEEDS[];
extern const int NUM_TEXT_SPEEDS;

void app_init(const char *game_dir);
/* Wi-Fi receive screen (games and engine updates from vn3ds-port --3ds). */
void app_receive_open(void);
void app_receive_close(void);
void app_rescan_games(void);
extern bool app_start_receiving; /* set before app_init, e.g. when launched via 3dslink */
void app_update(const Input *in, float dt);
void app_render(void);
void app_shutdown(void);

/* app.c */
void app_toast(const char *msg);
void app_load_game(int index);
void app_to_title(void);
void app_new_game(void);
bool app_new_game_at(const char *label); /* debugging: skip to a label */
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
void ui_draw_bottom(void);
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
void texcache_clear(void);

/* save.c */
bool save_write(int slot);
bool save_read(int slot);
void save_scan(int page, SlotInfo out[SLOTS_PER_PAGE]);
void settings_load(void);
void settings_save(void);
