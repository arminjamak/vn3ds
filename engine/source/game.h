#pragma once
#include "common.h"

#define MAX_ATTRS 8

enum { IMG_SOLID = 1, IMG_FULLSCREEN = 2, IMG_VIDEO = 4 };
enum { CHR_ADV = 0, CHR_NVL = 1, CHR_CENTERED = 2 };
enum { TR_DISSOLVE = 1, TR_FADE, TR_MOVE, TR_MOVEIN, TR_MOVEOUT, TR_PUNCH };
enum { DIR_LEFT, DIR_RIGHT, DIR_TOP, DIR_BOTTOM };
enum { STEP_SET, STEP_INTERP, STEP_PAUSE, STEP_REPEAT };
enum {
    P_XPOS, P_YPOS, P_XANCHOR, P_YANCHOR, P_XOFFSET, P_YOFFSET,
    P_XZOOM, P_YZOOM, P_ZOOM, P_ALPHA, P_ROTATE, P_ZPOS,
    P_XROTATE, P_YROTATE, /* camera: tilt (pitch) and orbit (yaw), degrees */
    P_COUNT
};

/* One depth layer of a layered illustration; x/y/w/h are in the image's
 * logical 3DS pixels, depth is absolute (positive = behind the screen). */
enum { ANIM_NONE, ANIM_SWAY, ANIM_PULSE, ANIM_BREATHE, ANIM_FALL, ANIM_RISE, ANIM_STARS,
       ANIM_PATCH /* a = x, b = y in texels: see ImageDef.patch_res */ };

typedef struct {
    s32 res;
    float depth, x, y, w, h;
    u32 anim;          /* ANIM_* */
    float a, b, period;
} ImageLayer;

typedef struct {
    const char *name;
    s32 res;
    u32 color;
    float w, h;
    u32 flags;
    float depth;
    ImageLayer *layers; /* NULL for ordinary images */
    int nlayers;
    /* An image stored as an earlier picture (res) plus an opaque JPEG patch
     * at texel (patch_x, patch_y), both JPEG .ctex; the two are put together
     * into one texture when loaded (texcache_image), so it draws exactly
     * like an ordinary image. -1 when not patched. */
    s32 patch_res;
    int patch_x, patch_y;
    /* name split into words */
    char *words;
    const char *tag;
    const char *attrs[MAX_ATTRS];
    int nattrs;
} ImageDef;

typedef struct {
    const char *name;
    const char *image_tag;
    u32 name_color, text_color;
    const char *prefix, *suffix;
    u8 kind;
} CharDef;

typedef struct {
    u8 type, warper, dir;
    float a, b, c;
    u32 color;
} TransDef;

typedef struct {
    u8 prop, abs;
    float value;
} AtlProp;

typedef struct {
    u8 kind, warper, nprops;
    float dur;
    u16 target, count;
    const u8 *props; /* nprops * 8 bytes, see FORMAT.md */
} AtlStep;

typedef struct {
    u16 nsteps;
    AtlStep *steps;
} AtlProg;

typedef struct {
    char id[64];
    char dir[256];
    u8 *data;
    u32 size;
    u32 crc;

    const char **strings;
    u32 nstrings;

    const char *title, *version;
    u16 game_w, game_h;
    float scale, view_x, view_y, view_w, view_h;
    u32 init_addr, nvars;
    float depth_bg, depth_sprite, depth_ui, max_shift;
    s32 title_image;

    const char **var_names;
    const char **res;
    u32 nres;
    ImageDef *images;
    u32 nimages;
    CharDef *chars;
    u32 nchars;
    TransDef *trans;
    u32 ntrans;
    AtlProg *atl;
    u32 natl;
    const u8 *code;
    u32 code_size;
    const u8 *labels; /* LABL: u32 count, {u32 name, u32 addr} (optional) */

    const char *speaking_attr; /* config.speaking_attribute, or NULL */
    float cam_drift, cam_period, cam_zoom; /* slow camera drift (vn3ds.json "camera") */
    s32 vox_res[32];           /* machine-voice syllable bank */
    int nvox;
    float vox_volume, vox_duck;
    float *vox_pitch;          /* per character; 0 = silent */
    const char *minigames[16]; /* MINI: minigame ids the script uses */
    int nminigames;
    const u8 *audio_names;     /* AUDN: u32 count, {u32 name, s32 res} (optional) */
} Game;

bool game_load(Game *g, const char *dir, const char *id, char *err, size_t errlen);
void game_free(Game *g);
const char *game_str(const Game *g, u32 idx);
/* Code address of a label, or -1. */
s32 game_label(const Game *g, const char *name);
/* Resource of a named audio file ("minigame/tower_1"), or -1. */
s32 game_audio_named(const Game *g, const char *name);
void game_res_path(const Game *g, s32 res, char *out, size_t len);
/* Reads just the title of a game folder for the game list. */
bool game_peek_title(const char *dir, char *out, size_t len);
