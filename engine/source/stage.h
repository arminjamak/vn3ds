#pragma once
#include "game.h"

#define MAX_SPRITES 32
#define MAX_RUNNERS 8
#define MAX_STEP_PROPS 16

typedef struct {
    float v[P_COUNT];
    u8 abs[4]; /* xpos, ypos, xanchor, yanchor: 1 = virtual pixels */
    u8 zpos_set;
} XForm;

typedef struct {
    s16 prog;
    u16 step;
    float t;
    u8 started, done;
    u16 repeat_left;
    u8 repeat_armed;
    float from[MAX_STEP_PROPS];
} AtlRunner;

typedef struct {
    char tag[32];
    s32 image;
    s32 zorder;
    u32 order;
    XForm xf;
    AtlRunner atl[MAX_RUNNERS];
    u8 natl;
    u8 from_scene;
} Sprite;

typedef struct {
    Sprite s[MAX_SPRITES];
    int n;
    u32 next_order;
    /* Ren'Py's `camera` statement: its ATL moves the whole scene (offsets,
     * zoom, rotate, plus xrotate/yrotate as tilt and orbit). It survives
     * `scene`, like in Ren'Py. */
    Sprite camera;
    u8 has_camera;
} Stage;

/* A sprite's placement on the top screen, before any stereo shift. */
typedef struct {
    float x, y, w, h; /* w/h negative when flipped */
    float angle;      /* radians */
    float alpha;
} SpriteRect;

void xform_default(XForm *xf);
void stage_clear(Stage *st);
int stage_find(const Stage *st, const char *tag);
s32 stage_resolve(const Game *g, const char *spec, const Sprite *current);
/* Returns false (and logs) when the image cannot be resolved. */
bool stage_show(Stage *st, const Game *g, const char *spec, const char *as_tag, s32 zorder,
                const char *behind, const s32 *atl, int natl, bool only_if_shown, bool from_scene);
void stage_hide(Stage *st, const char *tag);
/* `camera` with transforms; natl == 0 resets the camera. */
void stage_camera(Stage *st, const Game *g, const s32 *atl, int natl);
void stage_update(Stage *st, const Game *g, float dt);
/* Sprites in draw order (back to front). Returns count. */
int stage_order(const Stage *st, const Sprite **out);
void sprite_rect(const Game *g, const Sprite *s, SpriteRect *r);
/* Depth of a sprite: >0 behind the screen, <0 in front. `rank` = index among
 * non-fullscreen sprites in draw order. */
float sprite_depth(const Game *g, const Sprite *s, int rank);
