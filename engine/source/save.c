#include "app.h"
#include "bg.h"

/* Save files hold the VM (resume point, call stack, variables), the scene
 * that was on screen and the music. Sprites are written as raw structs, so
 * the save version must change whenever Sprite changes layout. */

#define SAVE_MAGIC "VNSV"
#define SAVE_VERSION 2

static void slot_path(int slot, char *out, size_t len)
{
    snprintf(out, len, "%s/saves/%s/slot%02d.sav", E.root, E.game.id, slot);
}

/* A save is put together in memory, then written in one go (on the
 * background thread for autosaves, so the frame that makes one doesn't
 * wait for the SD card). */
typedef struct {
    u8 *p;
    size_t n, cap;
} Buf;

static bool wr(Buf *b, const void *p, size_t n)
{
    if (b->n + n > b->cap) {
        size_t cap = b->cap ? b->cap * 2 : 4096;
        while (cap < b->n + n)
            cap *= 2;
        u8 *grown = realloc(b->p, cap);
        if (!grown)
            return false;
        b->p = grown;
        b->cap = cap;
    }
    memcpy(b->p + b->n, p, n);
    b->n += n;
    return true;
}
static bool rdf(FILE *f, void *p, size_t n) { return fread(p, 1, n, f) == n; }

static void preview_text(char *out, size_t len)
{
    if (E.vm.say_who[0])
        snprintf(out, len, "%s: %s", E.vm.say_who, E.vm.say_text);
    else
        snprintf(out, len, "%s", E.vm.say_text);
    for (char *c = out; *c; c++)
        if (*c == '\n')
            *c = ' ';
}

bool save_write(int slot) { return save_write_ex(slot, false); }

bool save_write_ex(int slot, bool background)
{
    VM *vm = &E.vm;
    if (vm->state != VM_SAY && vm->state != VM_MENU && vm->state != VM_PAUSE)
        return false;
    talk_end(); /* never save a sprite with its mouth open */
    char dir[300], path[320];
    static char dirs_for[64];   /* the folders are made once per game */
    if (strcmp(dirs_for, E.game.id) != 0) {
        snprintf(dir, sizeof(dir), "%s/saves", E.root);
        platform_mkdir(dir);
        snprintf(dir, sizeof(dir), "%s/saves/%s", E.root, E.game.id);
        platform_mkdir(dir);
        snprintf(dirs_for, sizeof(dirs_for), "%s", E.game.id);
    }
    slot_path(slot, path, sizeof(path));
    Buf buf = {0}, *f = &buf;

    bool ok = true;
    u32 version = SAVE_VERSION, crc = E.game.crc, t = platform_time();
    char preview[96] = "";
    preview_text(preview, sizeof(preview));
    ok &= wr(f, SAVE_MAGIC, 4) && wr(f, &version, 4) && wr(f, &crc, 4) && wr(f, &t, 4);
    ok &= wr(f, preview, sizeof(preview));

    u32 n = (u32)vm->ncalls;
    ok &= wr(f, &vm->resume_pc, 4) && wr(f, &n, 4) && wr(f, vm->calls, 4 * n);
    n = E.game.nvars;
    ok &= wr(f, &n, 4);
    for (u32 i = 0; i < n && ok; i++) {
        const Value *v = &vm->vars[i];
        ok &= wr(f, &v->type, 1);
        if (v->type == VAL_NUM || v->type == VAL_BOOL) {
            ok &= wr(f, &v->num, 8);
        } else if (v->type == VAL_STR) {
            u32 len = (u32)strlen(v->str);
            ok &= wr(f, &len, 4) && wr(f, v->str, len);
        }
    }
    ok &= wr(f, &vm->last_char, 4) && wr(f, vm->last_text, sizeof(vm->last_text));

    const Stage *st = &E.stage;
    n = (u32)st->n;
    ok &= wr(f, &n, 4) && wr(f, &st->next_order, 4) && wr(f, st->s, sizeof(Sprite) * n);
    u8 loop = E.music_loop, win = E.window_mode;
    ok &= wr(f, &E.music_res, 4) && wr(f, &loop, 1) && wr(f, &win, 1);
    ok &= wr(f, &st->has_camera, 1) && wr(f, &st->camera, sizeof(Sprite));
    if (!ok) {
        free(buf.p);
        return false;
    }
    if (background) {
        bg_write_file(path, buf.p, buf.n);
        return true;
    }
    bg_flush_files();   /* (an older autosave of this slot must not land after it) */
    FILE *out = fopen(path, "wb");
    ok = out && fwrite(buf.p, 1, buf.n, out) == buf.n;
    if (out)
        ok = (fclose(out) == 0) && ok;
    free(buf.p);
    return ok;
}

static bool read_header(FILE *f, SlotInfo *info)
{
    char magic[4];
    u32 version, crc;
    if (!rdf(f, magic, 4) || memcmp(magic, SAVE_MAGIC, 4) != 0)
        return false;
    if (!rdf(f, &version, 4) || version != SAVE_VERSION)
        return false;
    if (!rdf(f, &crc, 4) || crc != E.game.crc)
        return false;
    if (!rdf(f, &info->time, 4) || !rdf(f, info->preview, sizeof(info->preview)))
        return false;
    info->preview[sizeof(info->preview) - 1] = 0;
    info->used = true;
    return true;
}

/* A slot's header for any game folder, without loading that game (the
 * game's CRC isn't checked here; loading still checks it). */
bool save_peek(const char *game_id, int slot, SlotInfo *info)
{
    bg_flush_files();
    char path[400];
    snprintf(path, sizeof(path), "%s/saves/%s/slot%02d.sav", E.root, game_id, slot);
    memset(info, 0, sizeof(*info));
    FILE *f = fopen(path, "rb");
    if (!f)
        return false;
    char magic[4];
    u32 version, crc;
    bool ok = rdf(f, magic, 4) && !memcmp(magic, SAVE_MAGIC, 4) && rdf(f, &version, 4) &&
              version == SAVE_VERSION && rdf(f, &crc, 4) && rdf(f, &info->time, 4) &&
              rdf(f, info->preview, sizeof(info->preview));
    fclose(f);
    info->preview[sizeof(info->preview) - 1] = 0;
    info->used = ok;
    return ok;
}

void save_scan(int page, SlotInfo out[SLOTS_PER_PAGE])
{
    for (int i = 0; i < SLOTS_PER_PAGE; i++) {
        char path[320];
        memset(&out[i], 0, sizeof(out[i]));
        slot_path(page * SLOTS_PER_PAGE + i + 1, path, sizeof(path));
        FILE *f = fopen(path, "rb");
        if (!f)
            continue;
        if (!read_header(f, &out[i])) {
            memset(&out[i], 0, sizeof(out[i]));
            snprintf(out[i].preview, sizeof(out[i].preview), "(from another version of the game)");
        }
        fclose(f);
    }
}

bool save_read(int slot)
{
    bg_flush_files();
    char path[320];
    slot_path(slot, path, sizeof(path));
    FILE *f = fopen(path, "rb");
    if (!f)
        return false;
    SlotInfo info;
    VM *vm = &E.vm;
    bool ok = read_header(f, &info);
    u32 pc = 0, ncalls = 0, nvars = 0;
    u32 calls[VM_CALLS];
    ok = ok && rdf(f, &pc, 4) && rdf(f, &ncalls, 4) && ncalls <= VM_CALLS &&
         rdf(f, calls, 4 * ncalls) && rdf(f, &nvars, 4) && nvars == E.game.nvars;
    if (!ok) {
        fclose(f);
        return false;
    }
    vm_new_game(vm);
    for (u32 i = 0; i < nvars && ok; i++) {
        Value *v = &vm->vars[i];
        u8 type = 0;
        ok &= rdf(f, &type, 1);
        if (type == VAL_NUM || type == VAL_BOOL) {
            v->type = type;
            ok &= rdf(f, &v->num, 8);
        } else if (type == VAL_STR) {
            u32 len = 0;
            ok &= rdf(f, &len, 4) && len < 65536;
            if (ok) {
                char *s = malloc(len + 1);
                ok &= rdf(f, s, len);
                s[len] = 0;
                v->type = VAL_STR;
                v->str = s;
            }
        }
    }
    ok = ok && rdf(f, &vm->last_char, 4) && rdf(f, vm->last_text, sizeof(vm->last_text));
    vm->last_text[sizeof(vm->last_text) - 1] = 0;
    u32 n = 0;
    Stage st;
    memset(&st, 0, sizeof(st));
    ok = ok && rdf(f, &n, 4) && n <= MAX_SPRITES && rdf(f, &st.next_order, 4) &&
         rdf(f, st.s, sizeof(Sprite) * n);
    st.n = (int)n;
    s32 music = -1;
    u8 loop = 0, win = 0;
    ok = ok && rdf(f, &music, 4) && rdf(f, &loop, 1) && rdf(f, &win, 1);
    if (ok && rdf(f, &st.has_camera, 1) && !rdf(f, &st.camera, sizeof(Sprite)))
        st.has_camera = 0;   /* (older saves end before the camera) */
    fclose(f);
    if (!ok || pc >= E.game.code_size)
        return false;
    for (int i = 0; i < st.n; i++)
        if (st.s[i].image < 0 || (u32)st.s[i].image >= E.game.nimages)
            return false;

    memcpy(vm->calls, calls, 4 * ncalls);
    vm->ncalls = (int)ncalls;
    vm->pc = pc;
    E.stage = st;
    E.committed = st;
    E.tr.active = false;
    E.window_mode = win;
    for (int ch = 0; ch < CH_COUNT; ch++)
        audio_stop(ch, 0);
    E.music_res = -1;
    if (music >= 0)
        eng_play(CH_MUSIC, music, loop ? 1 : 0, 0.5f, 0);
    return true;
}

/* ---- settings ---------------------------------------------------------- */

void settings_load(void)
{
    Settings *s = &E.set;
    s->text_speed = 3;
    s->auto_delay = 1.5f;
    s->depth_mult = 1.0f;
    s->box_alpha = 0.75f;
    s->music_vol = 0.8f;
    s->sound_vol = 1.0f;
    char path[300];
    snprintf(path, sizeof(path), "%s/settings.cfg", E.root);
    FILE *f = fopen(path, "r");
    if (!f)
        return;
    char line[128];
    while (fgets(line, sizeof(line), f)) {
        char key[32];
        float v;
        if (sscanf(line, "%31[a-z_] = %f", key, &v) != 2)
            continue;
        if (!strcmp(key, "text_speed"))
            s->text_speed = (int)clampf(v, 0, (float)(NUM_TEXT_SPEEDS - 1));
        else if (!strcmp(key, "auto_delay"))
            s->auto_delay = clampf(v, 0.5f, 5.0f);
        else if (!strcmp(key, "depth"))
            s->depth_mult = clampf(v, 0.0f, 2.0f);
        else if (!strcmp(key, "box_alpha"))
            s->box_alpha = clampf(v, 0.2f, 1.0f);
        else if (!strcmp(key, "music_volume"))
            s->music_vol = clampf(v, 0, 1);
        else if (!strcmp(key, "sound_volume"))
            s->sound_vol = clampf(v, 0, 1);
    }
    fclose(f);
}

void settings_save(void)
{
    char path[300];
    snprintf(path, sizeof(path), "%s/settings.cfg", E.root);
    FILE *f = fopen(path, "w");
    if (!f)
        return;
    const Settings *s = &E.set;
    fprintf(f, "text_speed = %d\nauto_delay = %.2f\ndepth = %.2f\nbox_alpha = %.2f\n"
               "music_volume = %.2f\nsound_volume = %.2f\n",
            s->text_speed, s->auto_delay, s->depth_mult, s->box_alpha, s->music_vol, s->sound_vol);
    fclose(f);
}
