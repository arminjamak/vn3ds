#pragma once
#include "game.h"

enum { VAL_NONE, VAL_BOOL, VAL_NUM, VAL_STR };

typedef struct {
    u8 type;
    double num;
    char *str; /* owned, VAL_STR only */
} Value;

typedef enum {
    VM_RUNNING,
    VM_SAY,    /* waiting for the player to read say_text */
    VM_MENU,   /* waiting for a choice */
    VM_PAUSE,  /* waiting for pause_time (or a click if <0) */
    VM_WITH,   /* waiting for a transition */
    VM_GAME,   /* a minigame is running (mg_id); vm_minigame_done() resumes */
    VM_ENDED,
    VM_ERROR,
} VmState;

#define VM_STACK 64
#define VM_CALLS 64
#define VM_CHOICES 16
#define VM_TEXT 1024

enum { SAY_EXTEND = 1, SAY_NOWAIT = 2 };

typedef struct {
    char text[256];
    u32 addr;
} Choice;

typedef struct VM {
    const Game *g;
    u32 pc;
    Value stack[VM_STACK];
    int sp;
    u32 calls[VM_CALLS];
    int ncalls;
    Value *vars;
    VmState state;
    /* Where execution restarts when a save made now is loaded. */
    u32 resume_pc;

    /* current interaction */
    s32 say_char;
    char say_who[128];
    char say_text[VM_TEXT];
    u8 say_flags;
    Choice choices[VM_CHOICES];
    int nchoices;
    u32 menu_begin_pc;
    float pause_time;
    s32 with_trans;
    char mg_id[32];

    s32 last_char;
    char last_text[VM_TEXT];
    size_t extend_from; /* bytes of say_text already shown before `extend` */
    char error[256];
} VM;

void vm_init(VM *vm, const Game *g);
void vm_free(VM *vm);
/* Reset variables and call stack and start a new game. */
void vm_new_game(VM *vm);
void vm_run(VM *vm);
/* Run init code, then continue at `addr` instead of `label start`. */
bool vm_new_game_at(VM *vm, u32 addr);
void vm_choose(VM *vm, int choice);
void vm_resume(VM *vm);
/* The minigame started by vn3ds_minigame() ended: its score becomes the
 * call's value and the script continues (call vm_run afterwards). */
void vm_minigame_done(VM *vm, int score);

void vm_interpolate(const VM *vm, const char *src, char *out, size_t len);
void value_free(Value *v);
void value_set_str(Value *v, const char *s);

/* Engine hooks, implemented in app.c. */
void eng_scene(const char *spec, const char *as_tag, s32 zorder, const char *behind,
               const s32 *atl, int natl);
void eng_show(const char *spec, const char *as_tag, s32 zorder, const char *behind,
              const s32 *atl, int natl, bool only_if_shown);
void eng_hide(const char *tag);
/* -1 commits the scene without a transition; returns true if the VM must wait. */
bool eng_with(s32 trans);
void eng_play(u8 channel, s32 res, u8 flags, float fadein, float fadeout);
void eng_stop(u8 channel, float fadeout);
void eng_window(u8 mode);
void eng_say_begin(void);

/* Desktop test hook: set to a code address; vm_watch_hit becomes true when
 * the VM executes it. */
extern s32 vm_watch_addr;
extern bool vm_watch_hit;
