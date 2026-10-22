#include "app.h"
#include "link.h"
#include "export.h"
#include "vfs.h"
#include "minigame.h"
#include "leaderboard.h"
#include "fetch.h"
#include "relay.h"
#include "update.h"
#include "net.h"
#include "video.h"
#include "bg.h"
#include "predict.h"

#include <dirent.h>
#ifdef __3DS__
#include <3ds.h>
#endif
#include <sys/stat.h>
#include <unistd.h>

bool app_start_receiving;
bool app_single_game;

Engine E;
FramePerf FP;

/* characters per second; 0 = instant */
const float TEXT_SPEEDS[] = {15, 25, 35, 50, 70, 110, 0};
const int NUM_TEXT_SPEEDS = (int)ARRAY_LEN(TEXT_SPEEDS);

#define BOX_TEXT_W 372.0f
#define BOX_TEXT_H 62.0f
#define CENTER_TEXT_W 340.0f

static void run_vm(void);
static void touch_buttons(const Input *in);
/* `stop music fadeout N` with a new track coming before the next line: the
 * stop waits, and the play that follows becomes a musical change (see
 * audio_music_change). Without a play, it happens at the next line. */
static struct {
    bool on;
    float fade, t;
} mstop;


/* ---- autoplay (testing in emulators) ------------------------------------
 * If <root>/autoplay.cfg exists the engine plays by itself:
 *     game = <folder name>      which game to open
 *     choices = 0,1,0           menu picks in order (0 once they run out)
 *     delay = 1.5               seconds to linger on each line
 * Each line's text also goes to the log. */
static struct {
    bool on;
    char game[64];
    int choices[64], nchoices, next;
    float delay, timer;
} AP;

static void autoplay_load(void)
{
    char path[300];
    snprintf(path, sizeof(path), "%s/autoplay.cfg", E.root);
    FILE *f = fopen(path, "r");
    if (!f)
        return;
    AP.on = true;
    AP.delay = 1.5f;
    char line[512];
    while (fgets(line, sizeof(line), f)) {
        char key[32], val[400];
        if (sscanf(line, " %31[a-z_] = %399[^\n]", key, val) != 2)
            continue;
        if (!strcmp(key, "game"))
            snprintf(AP.game, sizeof(AP.game), "%s", val);
        else if (!strcmp(key, "delay"))
            AP.delay = (float)atof(val);
        else if (!strcmp(key, "receive"))
            app_start_receiving = atoi(val) != 0;
        else if (!strcmp(key, "choices"))
            for (char *t = strtok(val, ", "); t && AP.nchoices < 64; t = strtok(NULL, ", "))
                AP.choices[AP.nchoices++] = atoi(t);
    }
    fclose(f);
    LOG("autoplay on: game=%s, %d choices, delay %.1f", AP.game, AP.nchoices, AP.delay);
}

/* Adds synthetic key presses to `in`. */
static void autoplay_input(Input *in, float dt)
{
    if (!AP.on)
        return;
    AP.timer += dt;
    if (E.screen == SCR_GAMELIST && E.ngames > 0) {
        for (int i = 0; i < E.ngames; i++)
            if (!strcmp(E.games[i], AP.game))
                E.game_sel = i;
        in->down |= KEY_A_;
    } else if (E.screen == SCR_TITLE && E.overlay == OV_NONE && AP.timer > 2.0f) {
        E.title_sel = 0;
        in->down |= KEY_A_;
        AP.timer = 0;
    } else if (E.screen == SCR_GAME && E.overlay == OV_NONE && !E.tr.active) {
        if (E.vm.state == VM_SAY && E.text_done && AP.timer > AP.delay) {
            in->down |= KEY_A_;
            AP.timer = 0;
        } else if (E.vm.state == VM_MENU && AP.timer > AP.delay) {
            int pick = AP.next < AP.nchoices ? AP.choices[AP.next] : 0;
            AP.next++;
            if (pick >= E.vm.nchoices)
                pick = E.vm.nchoices - 1;
            LOG("autoplay: choice %d '%s'", pick, E.vm.choices[pick].text);
            app_choose(pick);
            AP.timer = 0;
        } else if (E.vm.state == VM_PAUSE && E.pause_left < 0 && AP.timer > AP.delay) {
            in->down |= KEY_A_; /* a pause that waits for a click */
            AP.timer = 0;
        } else if (E.vm.state != VM_SAY && E.vm.state != VM_MENU && E.vm.state != VM_PAUSE) {
            AP.timer = 0;
        }
    } else if (E.screen == SCR_ERROR && AP.timer > 5.0f) {
        AP.on = false; /* leave the error on screen */
    }
}

void app_toast(const char *msg)
{
    snprintf(E.toast, sizeof(E.toast), "%s", msg);
    E.toast_t = 2.0f;
}

float app_strength(void)
{
    float shift = E.loaded ? E.game.max_shift : 6.0f;
    return gfx_slider() * shift * E.set.depth_mult;
}

void app_error(const char *msg)
{
    snprintf(E.error, sizeof(E.error), "%s", msg);
    LOG("error: %s", msg);
    E.screen = SCR_ERROR;
    E.overlay = OV_NONE;
}

/* ---- game list ----------------------------------------------------------- */

static void add_game(const char *name, void *ud)
{
    if (E.ngames < MAX_GAMES)
        E.game_app[E.ngames][0] = E.game_app_dir[E.ngames][0] = 0;
    (void)ud;
    if (E.ngames >= MAX_GAMES)
        return;
    char dir[400];
    snprintf(dir, sizeof(dir), "%s/games/%s", E.root, name);
    char title[96];
    if (!game_peek_title(dir, title, sizeof(title)))
        return;
    snprintf(E.games[E.ngames], sizeof(E.games[0]), "%s", name);
    snprintf(E.game_titles[E.ngames], sizeof(E.game_titles[0]), "%s", title);
    E.ngames++;
}

/* A novel exported as its own app (link.h): a card that starts that app. */
static void add_app(const char *id, const char *title, const char *app, const char *dir, void *ud)
{
    (void)ud;
    if (E.ngames >= MAX_GAMES)
        return;
    for (int i = 0; i < E.ngames; i++)
        if (!strcmp(E.games[i], id))
            return;   /* also in the library: that one opens here */
    int i = E.ngames++;
    snprintf(E.games[i], sizeof(E.games[0]), "%s", id);
    snprintf(E.game_titles[i], sizeof(E.game_titles[0]), "%s", title[0] ? title : id);
    snprintf(E.game_app[i], sizeof(E.game_app[0]), "%s", app);
    snprintf(E.game_app_dir[i], sizeof(E.game_app_dir[0]), "%s", dir);
}

/* Starts game i's own app (straight at its resume point with --continue);
 * where that can't be done, says which app to open. */
static void start_app(int i, bool resume)
{
    if (link_launch(E.game_app[i], resume ? "--continue" : NULL, NULL)) {
        E.quit = true;
        return;
    }
    char msg[200];
    snprintf(msg, sizeof(msg), "Open %s from the Homebrew Launcher or your emulator's games: "
             "it carries on where you left off.", E.game_titles[i]);
    app_error(msg);
}

static void unload_game(void)
{
    if (!E.loaded)
        return;
    app_autosave();
    for (int ch = 0; ch < CH_COUNT; ch++)
        audio_stop(ch, 0);
    talk_end();
    audio_vox_free();
    video_close_all();
    texcache_clear();
    pys_unload();
    vm_free(&E.vm);
    game_free(&E.game);
    E.loaded = false;
    net_set_live_game(NULL);
    if (!E.quit)
        sync_event(SYNC_LIBRARY);   /* back in the library: a computer may take the saves */
}

/* Opening a game can take a while on a 3DS card (an update to apply, the
 * script, the voices, the title art): each step is timed in the log, and once
 * the whole thing has taken longer than a moment a "Preparing" card is drawn
 * between steps, so the console never just sits on a still screen. */
static u64 opening_t0, opening_last, opening_drawn;

static void opening_step(const char *step, float frac)
{
    if (!E.opening)
        return;
    u64 now = platform_ms();
    if (strcmp(step, E.opening_step) != 0) {
        LOG("open %s: %s after %u ms", E.opening_title, step, (unsigned)(now - opening_t0));
        snprintf(E.opening_step, sizeof(E.opening_step), "%s", step);
    }
    E.opening_frac = frac;
    opening_last = now;
    if (now - opening_t0 > 150 && now - opening_drawn > 100) {   /* ~10 fps is plenty */
        opening_drawn = now;
        app_render();
    }
}

/* Moves everything under `src` into `dst` (same card), replacing files. */
static void move_tree(const char *src, const char *dst)
{
    /* The names first, then the moves: renaming entries out of a folder
     * while reading it makes the 3DS's SD card listing skip some, and the
     * skipped files would stay behind in updates/ (their game can't read
     * them there, and the next transfer counts them as already sent). */
    DIR *d = opendir(src);
    if (!d)
        return;
    mkdir(dst, 0755);
    char (*names)[256] = NULL;
    size_t n = 0, cap = 0;
    struct dirent *e;
    while ((e = readdir(d))) {
        if (e->d_name[0] == '.')
            continue;
        if (n == cap) {
            size_t nc = cap ? cap * 2 : 64;
            char (*nn)[256] = realloc(names, nc * sizeof(*names));
            if (!nn)
                break;
            names = nn;
            cap = nc;
        }
        snprintf(names[n++], sizeof(names[0]), "%s", e->d_name);
    }
    closedir(d);
    char from[512], to[512];
    for (size_t i = 0; i < n; i++) {
        snprintf(from, sizeof(from), "%s/%s", src, names[i]);
        snprintf(to, sizeof(to), "%s/%s", dst, names[i]);
        struct stat st;
        if (stat(from, &st) != 0)
            continue;
        if (S_ISDIR(st.st_mode)) {
            move_tree(from, to);
        } else if (strstr(names[i], ".part")) {
            remove(from);   /* a transfer that never finished: nothing will complete it */
        } else {
            remove(to);
            if (rename(from, to) != 0)
                LOG("update: cannot move %s", from);
            opening_step("Applying the update", -1);
        }
    }
    free(names);
    rmdir(src);
}

/* An update received while the game was open waits in updates/<id>/. */
static void apply_staged_update(const char *id)
{
    char staged[400], live[400];
    snprintf(staged, sizeof(staged), "%s/updates/%s", E.root, id);
    struct stat st;
    if (stat(staged, &st) != 0)
        return;
    snprintf(live, sizeof(live), "%s/games/%s", E.root, id);
    LOG("applying the update received for %s", id);
    move_tree(staged, live);
}

/* After an update (see flag_prune in net.c), deletes packed files in img/,
 * snd/ and pk/ that game.bin no longer names: files are named by their
 * contents, so changed ones arrive under new names and the old ones stay
 * behind. A game with pack files names only its packs, so the loose files of
 * an older version go too. On a 3DS card deleting a thousand files takes
 * minutes, so it runs in a low-priority thread while the game plays; the
 * flag goes only when done. */
enum { PRUNE_NAME = 64 };
typedef struct {
    char dir[400];
    char *names;   /* n names of PRUNE_NAME bytes, sorted */
    u32 n;
} PruneJob;
static volatile bool prune_busy;

static int cmp_name(const void *a, const void *b)
{
    return strcmp((const char *)a, (const char *)b);
}

static void prune_run(void *arg)
{
    PruneJob *job = arg;
    char *doomed = NULL;
    u32 ndoomed = 0, cap = 0;
    /* list first, delete after: removing while reading a folder can skip entries */
    static const char *subs[] = {"img", "snd", "pk"};
    for (int k = 0; k < 3; k++) {
        char path[460];
        snprintf(path, sizeof(path), "%s/%s", job->dir, subs[k]);
        DIR *d = opendir(path);
        if (!d)
            continue;
        struct dirent *e;
        while ((e = readdir(d))) {
            const char *ext = strrchr(e->d_name, '.');
            if (!ext || (strcmp(ext, ".ctex") && strcmp(ext, ".ogg") && strcmp(ext, ".cvid") &&
                         strcmp(ext, ".cvh") && strcmp(ext, ".pak")) ||
                strlen(e->d_name) >= PRUNE_NAME - 5)
                continue;
            char rel[PRUNE_NAME];
            snprintf(rel, sizeof(rel), "%s/%s", subs[k], e->d_name);
            if (bsearch(rel, job->names, job->n, PRUNE_NAME, cmp_name))
                continue;
            if (ndoomed == cap) {
                cap = cap ? cap * 2 : 64;
                char *grown = realloc(doomed, (size_t)cap * PRUNE_NAME);
                if (!grown)
                    break;
                doomed = grown;
            }
            memcpy(doomed + (size_t)ndoomed++ * PRUNE_NAME, rel, PRUNE_NAME);
        }
        closedir(d);
    }
    for (u32 i = 0; i < ndoomed; i++) {
        char path[460];
        snprintf(path, sizeof(path), "%s/%s", job->dir, doomed + (size_t)i * PRUNE_NAME);
        remove(path);
        /* each delete holds the card for a moment: space them out so a game
         * reading its pictures and music never waits behind a queue of them */
#ifdef __3DS__
        svcSleepThread(40 * 1000000LL);
#else
        usleep(1000);
#endif
    }
    char flag[460];
    snprintf(flag, sizeof(flag), "%s/prune.flag", job->dir);
    remove(flag);
    if (ndoomed)
        LOG("removed %u files the update replaced", (unsigned)ndoomed);
    free(doomed);
    free(job->names);
    free(job);
    prune_busy = false;
}

#ifndef __3DS__
#include <pthread.h>
static void *prune_run_host(void *arg)
{
    prune_run(arg);
    return NULL;
}
#endif

static void prune_game(const char *dir, const Game *g)
{
    char flag[400];
    snprintf(flag, sizeof(flag), "%s/prune.flag", dir);
    struct stat st;
    if (prune_busy || stat(flag, &st) != 0)
        return;
    PruneJob *job = calloc(1, sizeof(PruneJob));
    /* every referenced path, plus the poster beside each .cvh video */
    char *names = job ? malloc((size_t)(g->nres * 2 + vfs_packs() + 1) * PRUNE_NAME) : NULL;
    if (!names) {
        free(job);
        return;
    }
    u32 n = 0;
    /* a packed game reads only its packs: loose files of an older version go too */
    for (int i = 0; g->packed && i < vfs_packs(); i++)
        snprintf(names + (size_t)n++ * PRUNE_NAME, PRUNE_NAME, "%s", vfs_pack_name(i));
    for (u32 i = 0; !g->packed && i < g->nres; i++) {
        const char *r = g->res[i];
        if (!r)
            continue;
        size_t len = strlen(r);
        if (len >= PRUNE_NAME - 2) {   /* not a name this scheme makes: leave the folder alone */
            free(names);
            free(job);
            return;
        }
        snprintf(names + (size_t)n++ * PRUNE_NAME, PRUNE_NAME, "%s", r);
        if (len > 4 && !strcmp(r + len - 4, ".cvh"))
            snprintf(names + (size_t)n++ * PRUNE_NAME, PRUNE_NAME, "%.*s.ctex", (int)(len - 4), r);
    }
    qsort(names, n, PRUNE_NAME, cmp_name);
    snprintf(job->dir, sizeof(job->dir), "%s", dir);
    job->names = names;
    job->n = n;
    prune_busy = true;
#ifdef __3DS__
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    Thread t = threadCreate(prune_run, job, 128 * 1024, prio < 0x3E ? prio + 2 : 0x3F, -2, true);
    if (!t)
        prune_run(job);
#else
    pthread_t t;
    if (pthread_create(&t, NULL, prune_run_host, job) == 0)
        pthread_detach(t);
    else
        prune_run(job);
#endif
}

static bool load_game_dir(const char *dir, const char *id)
{
    E.opening = true;
    opening_t0 = opening_drawn = platform_ms();
    if (!E.opening_title[0])
        snprintf(E.opening_title, sizeof(E.opening_title), "%.63s", id);
    E.opening_step[0] = 0;
    opening_step("Closing the last game", -1);
    unload_game();
    opening_step("Applying the update", -1);
    apply_staged_update(id);
    opening_step("Reading the story", 0.2f);
    char err[256];
    if (!game_load(&E.game, dir, id, err, sizeof(err))) {
        E.opening = false;
        app_error(err);
        return false;
    }
    E.loaded = true;
    link_note_reading(false);
    link_register_app();
    story_game_opened();
    prune_game(dir, &E.game);
    net_set_live_game(id);
    opening_step("Looking for your saves", 0.45f);
    {
        SlotInfo info;
        E.has_resume = save_peek(id, RESUME_SLOT, &info);
    }
    vm_init(&E.vm, &E.game);
    opening_step("Tuning the voices", 0.6f);
    talk_load_bank();
    E.music_res = -1;
    opening_step("Setting the stage", 0.85f);
    app_to_title();
    LOG("open %s: ready after %u ms", E.opening_title, (unsigned)(platform_ms() - opening_t0));
    E.opening = false;
    E.opening_title[0] = 0;
    return true;
}

static void rx_wait_toast(const char *title)
{
    char eta[48], msg[96];
    app_rx_eta_text(eta, sizeof(eta));
    if (eta[0])
        snprintf(msg, sizeof(msg), "%s is still arriving: %s", title, eta);
    else
        snprintf(msg, sizeof(msg), "%s is still arriving", title);
    app_toast(msg);
}

bool app_load_game(int index)
{
    if (index == E.ngames && E.rx_new) {
        rx_wait_toast(E.rx_new_title);
        return false;
    }
    if (index < 0 || index >= E.ngames)
        return false;
    if (E.game_app_dir[index][0]) {   /* its own app: to its title screen */
        start_app(index, false);
        return false;
    }
    if (app_rx_busy(E.games[index])) {
        rx_wait_toast(E.game_titles[index]);
        return false;
    }
    char dir[400];
    snprintf(dir, sizeof(dir), "%s/games/%s", E.root, E.games[index]);
    snprintf(E.opening_title, sizeof(E.opening_title), "%.63s",
             E.game_titles[index][0] ? E.game_titles[index] : E.games[index]);
    return load_game_dir(dir, E.games[index]);
}

/* ---- resume: autosave and snapshots ------------------------------------------ */

static u16 thumb[THUMB_W * THUMB_H];
static bool thumb_valid, snap_pending;
static u32 snapped_serial;

static void thumb_path(const char *id, char *out, size_t len)
{
    snprintf(out, len, "%s/saves/%s/slot%02d.thm", E.root, id, RESUME_SLOT);
}

/* The saves of home card i: the library's, or a standalone app's own. */
static const char *card_root(int i) { return E.game_app_dir[i][0] ? E.game_app_dir[i] : E.root; }

static void autosave(bool background)
{
    if (!E.loaded || E.screen != SCR_GAME)
        return;
    E.autosave_t = E.time;
    if (!save_write_ex(RESUME_SLOT, background))
        return;
    E.has_resume = true;
    link_note_reading(background);
    if (!thumb_valid)
        return;
    char path[400];
    thumb_path(E.game.id, path, sizeof(path));
    size_t n = 8 + sizeof(thumb);
    u8 *buf = malloc(n);
    if (!buf)
        return;
    u16 wh[2] = {THUMB_W, THUMB_H};
    memcpy(buf, "THM1", 4);
    memcpy(buf + 4, wh, 4);
    memcpy(buf + 8, thumb, sizeof(thumb));
    if (background) {
        bg_write_file(path, buf, n);
        return;
    }
    FILE *f = fopen(path, "wb");
    if (f) {
        fwrite(buf, 1, n, f);
        fclose(f);
    }
    free(buf);
}

void app_autosave(void)
{
    autosave(false);
    bg_flush_files();
}

bool app_has_resume(void) { return E.loaded && E.has_resume; }

/* The story reached its end: next time, Play starts at the title. */
static void drop_resume(void)
{
    char path[400];
    snprintf(path, sizeof(path), "%s/saves/%s/slot%02d.sav", E.root, E.game.id, RESUME_SLOT);
    remove(path);
    thumb_path(E.game.id, path, sizeof(path));
    remove(path);
    E.has_resume = false;
}

/* A picture of at most THUMB_W x THUMB_H in a .thm file (a resume
 * snapshot, a story point's or a game's cover.thm), or NULL. */
GfxTex *app_load_thm(const char *path)
{
    static u16 buf[THUMB_W * THUMB_H];
    FILE *f = fopen(path, "rb");
    if (!f)
        return NULL;
    char magic[4];
    u16 wh[2];
    GfxTex *t = NULL;
    if (fread(magic, 1, 4, f) == 4 && !memcmp(magic, "THM1", 4) && fread(wh, 2, 2, f) == 2 &&
        wh[0] > 0 && wh[1] > 0 && wh[0] <= THUMB_W && wh[1] <= THUMB_H &&
        fread(buf, 2, (size_t)wh[0] * wh[1], f) == (size_t)wh[0] * wh[1])
        t = gfx_tex_from_rgb565(buf, wh[0], wh[1]);
    fclose(f);
    return t;
}

static void cover_path(const char *id, char *out, size_t len)
{
    snprintf(out, len, "%s/games/%s/cover.thm", E.root, id);
}

/* Where game i was left: its resume line and snapshot. */
static void home_resume(int i)
{
    gfx_tex_free(E.game_thumb[i]);
    save_peek_at(card_root(i), E.games[i], RESUME_SLOT, &E.game_resume[i]);
    char path[400];
    snprintf(path, sizeof(path), "%s/saves/%s/slot%02d.thm", card_root(i), E.games[i], RESUME_SLOT);
    E.game_thumb[i] = app_load_thm(path);
}

/* Back on the home screen from a game: where that one was left now. */
void app_home_refresh_loaded(void)
{
    for (int i = 0; i < E.ngames && E.loaded; i++)
        if (!strcmp(E.games[i], E.game.id))
            home_resume(i);
}

/* The home screen's cards: each game's cover, resume snapshot and line. */
static void home_refresh(void)
{
    for (int i = 0; i < MAX_GAMES; i++) {
        gfx_tex_free(E.game_thumb[i]);
        gfx_tex_free(E.game_cover[i]);
        E.game_thumb[i] = E.game_cover[i] = NULL;
    }
    for (int i = 0; i < E.ngames; i++) {
        home_resume(i);
        char path[400];
        if (E.game_app_dir[i][0])
            snprintf(path, sizeof(path), "%s/cover.thm", E.game_app_dir[i]);
        else
            cover_path(E.games[i], path, sizeof(path));
        E.game_cover[i] = app_load_thm(path);
    }
    home_reset();
}

/* Quitting a novel inside vn3ds: save, close it and go back to the library
 * with its card selected (the app itself quits from the library). */
void app_to_library(void)
{
    char id[sizeof(E.games[0])];
    snprintf(id, sizeof(id), "%s", E.loaded ? E.game.id : "");
    unload_game();
    E.overlay = OV_NONE;
    E.screen = SCR_GAMELIST;
    for (int i = 0; id[0] && i < E.ngames; i++)
        if (!strcmp(E.games[i], id)) {
            E.game_sel = i;
            home_reset();
        }
}

/* ---- Export as app ---------------------------------------------------- */

/* The .3dsx to build apps from: this program's own, else vn3ds.3dsx on the
 * card (vn3ds started as a CIA, or by an emulator). */
static const char *export_engine(void)
{
    const char *self = platform_self_path();
    size_t n = strlen(self);
    struct stat st;
    if (n > 5 && !strcmp(self + n - 5, ".3dsx") && stat(self, &st) == 0)
        return self;
    return link_vn3ds_path();
}

bool app_can_export(void)
{
    return !app_single_game && E.loaded && export_engine() != NULL;
}

static void export_progress(u64 done, u64 total, void *ud)
{
    (void)ud;
    opening_step("Writing the app", total ? (float)done / (float)total : -1.0f);
}

void app_export_game(void)
{
    const char *engine = export_engine();
    if (!E.loaded || !engine) {
        app_toast("vn3ds.3dsx isn't on the SD card to build the app from");
        return;
    }
    char out[300], err[256];
    snprintf(out, sizeof(out), "%s/3ds/%s.3dsx", platform_sdmc(), E.game.id);
    const char *title = E.game.title && E.game.title[0] ? E.game.title : E.game.id;
    E.opening = true;
    opening_t0 = opening_drawn = platform_ms() - 1000;   /* the card from the start */
    snprintf(E.opening_title, sizeof(E.opening_title), "%.63s", title);
    E.opening_step[0] = 0;
    opening_step("Writing the app", 0);
    bool ok = export_app(engine, E.game.dir, E.game.id, title, "vn3ds", out, export_progress,
                         NULL, err, sizeof(err));
    LOG("export %s -> %s: %s", E.game.id, out, ok ? "done" : err);
    E.opening = false;
    E.opening_title[0] = 0;
    if (!ok) {
        app_toast(err);
        return;
    }
    char cover[400];
    snprintf(cover, sizeof(cover), "%s/cover.thm", E.game.dir);
    link_register(E.game.id, title, out, cover);
    char msg[200];
    snprintf(msg, sizeof(msg), "Saved %s.3dsx beside vn3ds: start it from the Homebrew Launcher",
             E.game.id);
    app_toast(msg);
}

void app_play_game(int index)
{
    bool resume = index >= 0 && index < E.ngames && E.game_resume[index].used;
    if (index >= 0 && index < E.ngames && E.game_app_dir[index][0]) {
        start_app(index, resume);
        return;
    }
    if (app_load_game(index) && resume && E.loaded)
        app_load_slot(RESUME_SLOT);
}

void app_init(const char *game_dir)
{
    memset(&E, 0, sizeof(E));
    snprintf(E.root, sizeof(E.root), "%s", platform_root());
    texcache_init();
    bg_start();
    settings_load();
    lb_init();
    audio_set_volume(CH_MUSIC, E.set.music_vol);
    audio_set_volume(CH_SOUND, E.set.sound_vol);
    audio_set_volume(CH_VOICE, E.set.sound_vol);
    E.screen = SCR_GAMELIST;
    autoplay_load();
    if (game_dir) {
        const char *slash = strrchr(game_dir, '/');
        load_game_dir(game_dir, slash ? slash + 1 : game_dir);
        if (link_continue && E.loaded && E.has_resume)   /* started from vn3ds's Continue */
            app_load_slot(RESUME_SLOT);
        if (!app_start_receiving && app_listen_background && !app_single_game)
            net_start(NET_PORT);
        return;
    }
    app_rescan_games();
    for (int i = 0; link_from[0] && i < E.ngames; i++)   /* back from that game's own app */
        if (!strcmp(E.games[i], link_from)) {
            E.game_sel = i;
            home_reset();
        }
    if (app_start_receiving)
        app_receive_open();
    else {
        if (app_listen_background)
            net_start(NET_PORT);   /* listen in the background: games can arrive any time */
    }
}

void app_rescan_games(void)
{
    /* stay on the same card, including a new game whose card was arriving */
    char keep[64] = "";
    if (E.game_sel < E.ngames)
        snprintf(keep, sizeof(keep), "%s", E.games[E.game_sel]);
    else if (E.rx_new)
        snprintf(keep, sizeof(keep), "%s", E.rx_new_id);
    char games[300];
    E.ngames = 0;
    snprintf(games, sizeof(games), "%s/games", E.root);
    platform_list_dirs(games, add_game, NULL);
    link_scan_apps(add_app, NULL);
    for (int i = 0; i < E.ngames; i++)
        if (!strcmp(E.games[i], keep))
            E.game_sel = i;
    if (E.game_sel >= app_home_count())
        E.game_sel = 0;
    home_refresh();
}

void app_receive_open(void)
{
    if (E.loaded)
        app_to_title();
    E.screen = SCR_RECEIVE;
    net_start(NET_PORT);
}

void app_receive_close(void)
{
    /* keep listening in the background */
    app_rescan_games();
    E.screen = SCR_GAMELIST;
}

void app_shutdown(void)
{
    app_autosave();
    bg_flush_files();
    sync_event(SYNC_EXIT);   /* (waits a moment for a computer that should get new saves) */
    fetch_stop();
    update_stop();
    lb_shutdown();
    settings_save();
    unload_game();
    bg_stop();
}

void app_to_title(void)
{
    app_autosave();   /* only does something when leaving a running story */
    talk_end();
    /* with title music the music channel isn't stopped: the title loop takes
     * over from the story's music on the beat (eng_play below) */
    bool title_music = E.game.title_music >= 0;
    for (int ch = 0; ch < CH_COUNT; ch++)
        if (ch != CH_MUSIC || !title_music)
            audio_stop(ch, 0.5f);
    mstop.on = false;
    E.music_res = -1;
    stage_clear(&E.stage);
    stage_clear(&E.committed);
    E.stage.has_camera = E.committed.has_camera = 0;
    E.tr.active = false;
    E.overlay = OV_NONE;
    E.screen = SCR_TITLE;
    E.title_sel = 0;
    E.skip = E.skip_toggle = E.auto_mode = E.hide_ui = false;
    if (title_music)
        eng_play(CH_MUSIC, E.game.title_music, 1, 1.5f, 0.0f);
}

static void reset_presentation(void)
{
    mstop.on = false;
    stage_clear(&E.stage);
    stage_clear(&E.committed);
    E.stage.has_camera = E.committed.has_camera = 0;
    E.tr.active = false;
    E.window_mode = WIN_AUTO;
    E.hist_n = 0;
    E.skip = E.skip_toggle = E.auto_mode = E.hide_ui = false;
    E.overlay = OV_NONE;
    E.screen = SCR_GAME;
}

void app_new_game(void)
{
    reset_presentation();
    E.story_step = 0;
    vm_new_game(&E.vm);
    run_vm();
}

bool app_new_game_at(const char *label)
{
    s32 addr = game_label(&E.game, label);
    if (addr < 0)
        return false;
    reset_presentation();
    E.story_step = 0;
    if (!vm_new_game_at(&E.vm, (u32)addr))
        return false;
    run_vm();
    return true;
}

/* The story goes on at `label` (a game's own screen jumped there from an
 * overlay, see pyscreen.c), as Ren'Py's Jump() ends the interaction. */
bool app_story_jump(const char *label)
{
    s32 addr = game_label(&E.game, label);
    if (addr < 0 || !E.loaded)
        return false;
    E.screen = SCR_GAME;
    E.vm.pc = (u32)addr;
    E.vm.state = VM_RUNNING;
    run_vm();
    return true;
}

bool app_load_slot(int slot)
{
    reset_presentation();
    if (!save_read(slot)) {
        app_to_title();
        app_toast("Could not load that save");
        return false;
    }
    E.vm.state = VM_RUNNING;
    run_vm();
    return true;
}

/* ---- looking ahead: preloads and the music ---------------------------------
 * After the story moves on (on the next frame, to keep the frame A was
 * pressed on light), predict.c looks a few lines ahead: the pictures there
 * are preloaded and the next music is opened and decoded in advance. */

#define PREDICT_LINES 6   /* how far ahead the scan looks (lines, menus) */
#define PRELOAD_LINES 3   /* pictures this close are preloaded */

static bool predict_due;

bool app_music_meta(const char *path, MusicMeta *out)
{
    memset(out, 0, sizeof(*out));
    if (!E.loaded || !E.game.music_meta)
        return false;
    for (u32 i = 0; i < E.game.nmusic_meta; i++) {
        const u8 *m = E.game.music_meta + 12 * i;
        char p[400];
        game_res_path(&E.game, rd_s32(m), p, sizeof(p));
        if (strcmp(p, path) != 0)
            continue;
        out->bpm = rd_f32(m + 4);
        out->beats_per_bar = m[8];
        out->phrase_bars = m[9];
        out->bars = rd_u16(m + 10);
        return out->bpm > 0;
    }
    return false;
}

static void run_prediction(void)
{
    if (!E.loaded || E.screen != SCR_GAME)
        return;
    u64 t0 = platform_us();
    Prediction pr;
    predict_scan(&E.vm, &E.stage, PREDICT_LINES, &pr);
    texcache_want_begin();
    int n = 0;
    for (int i = 0; i < pr.nimages; i++)
        if (pr.image_dist[i] <= PRELOAD_LINES && (u32)pr.images[i] < E.game.nimages) {
            texcache_want(&E.game.images[pr.images[i]]);
            n++;
        }
    texcache_want_end();
    if (pr.music_res >= 0 && !(pr.music_flags & 2) && pr.music_res != E.music_res) {
        char path[400];
        game_res_path(&E.game, pr.music_res, path, sizeof(path));
        audio_music_prefetch(path, pr.music_flags & 1);
    }
    PERF("predict: %d pictures within %d lines, next music res %d (%d lines on); %.2f ms", n,
         PRELOAD_LINES, (int)pr.music_res, pr.music_dist, (platform_us() - t0) / 1000.0);
}

/* Does a music PLAY come before the player is next asked for anything? */
static bool music_follows(void)
{
    Prediction pr;
    predict_scan(&E.vm, &E.stage, 0, &pr);
    return pr.music_res >= 0 && !(pr.music_flags & 2);
}

static void music_stop_now(void)
{
    if (!mstop.on)
        return;
    mstop.on = false;
    PERF("music: the deferred stop happens now (fade %.1f s): no new music came", mstop.fade);
    audio_stop(CH_MUSIC, mstop.fade);
}

/* ---- VM hooks ------------------------------------------------------------ */

static void preload(const Stage *st, const char *tag)
{
    int i = stage_find(st, tag);
    if (i < 0)
        return;
    const ImageDef *im = &E.game.images[st->s[i].image];
    if (!(im->flags & IMG_VIDEO))
        texcache_image(im);
    for (int k = 0; k < im->nlayers; k++)
        if (im->layers[k].anim != ANIM_VIDEO)
            texcache_get(im->layers[k].res);
}

static void sprite_key(const char *spec, const char *as_tag, char *key, size_t len)
{
    if (as_tag) {
        snprintf(key, len, "%s", as_tag);
        return;
    }
    size_t n = strcspn(spec, " ");
    if (n >= len)
        n = len - 1;
    memcpy(key, spec, n);
    key[n] = 0;
}

void eng_scene(const char *spec, const char *as_tag, s32 zorder, const char *behind,
               const s32 *atl, int natl)
{
    stage_clear(&E.stage);
    story_scene();
    if (!spec)
        return;
    stage_show(&E.stage, &E.game, spec, as_tag, zorder, behind, atl, natl, false, true);
    char key[32];
    sprite_key(spec, as_tag, key, sizeof(key));
    preload(&E.stage, key);
}

void eng_show(const char *spec, const char *as_tag, s32 zorder, const char *behind,
              const s32 *atl, int natl, bool only_if_shown)
{
    if (as_tag && !strcmp(as_tag, "@camera")) {
        stage_camera(&E.stage, &E.game, atl, natl);
        return;
    }
    stage_show(&E.stage, &E.game, spec, as_tag, zorder, behind, atl, natl, only_if_shown, false);
    char key[32];
    sprite_key(spec, as_tag, key, sizeof(key));
    preload(&E.stage, key);
}

void eng_hide(const char *tag)
{
    if (tag)
        stage_hide(&E.stage, tag);
}

static float trans_duration(const TransDef *t)
{
    switch (t->type) {
    case TR_FADE: return t->a + t->b + t->c;
    default: return t->a;
    }
}

static void edge_offset(int dir, const SpriteRect *r, float *dx, float *dy)
{
    float w = fabsf(r->w), h = fabsf(r->h);
    *dx = *dy = 0;
    switch (dir) {
    case DIR_LEFT: *dx = -(r->x + w); break;
    case DIR_RIGHT: *dx = TOP_W - r->x; break;
    case DIR_TOP: *dy = -(r->y + h); break;
    default: *dy = TOP_H - r->y; break;
    }
}

bool eng_with(s32 t)
{
    if (t < 0 || (u32)t >= E.game.ntrans || E.skip) {
        E.committed = E.stage;
        return false;
    }
    Transition *tr = &E.tr;
    const TransDef *def = &E.game.trans[t];
    tr->def = def;
    tr->t = 0;
    tr->dur = trans_duration(def);
    if (tr->dur <= 0) {
        E.committed = E.stage;
        return false;
    }
    tr->old = E.committed;
    tr->need_capture = def->type == TR_DISSOLVE;
    tr->nleaving = 0;
    memset(tr->off, 0, sizeof(tr->off));
    if (def->type == TR_MOVE || def->type == TR_MOVEIN || def->type == TR_MOVEOUT) {
        for (int i = 0; i < E.stage.n; i++) {
            const Sprite *s = &E.stage.s[i];
            SpriteRect nr, orr;
            sprite_rect(&E.game, s, &nr);
            int j = stage_find(&tr->old, s->tag);
            if (j >= 0) {
                sprite_rect(&E.game, &tr->old.s[j], &orr);
                tr->off[i][0] = orr.x - nr.x;
                tr->off[i][1] = orr.y - nr.y;
            } else if (def->type == TR_MOVEIN) {
                edge_offset(def->dir, &nr, &tr->off[i][0], &tr->off[i][1]);
            }
        }
        if (def->type == TR_MOVEOUT) {
            for (int j = 0; j < tr->old.n; j++) {
                if (stage_find(&E.stage, tr->old.s[j].tag) >= 0)
                    continue;
                SpriteRect orr;
                sprite_rect(&E.game, &tr->old.s[j], &orr);
                int k = tr->nleaving++;
                tr->leaving[k] = j;
                edge_offset(def->dir, &orr, &tr->loff[k][0], &tr->loff[k][1]);
            }
        }
    }
    tr->active = true;
    return true;
}

static void finish_transition(void)
{
    E.tr.active = false;
    E.punch_x = E.punch_y = 0;
    E.committed = E.stage;
    if (E.vm.state == VM_WITH) {
        vm_resume(&E.vm);
        run_vm();
    }
}

void eng_play(u8 channel, s32 res, u8 flags, float fadein, float fadeout)
{
    (void)fadeout;
    if (channel >= CH_COUNT || res < 0)
        return;
    if (channel == CH_MUSIC && (flags & 4) && E.music_res == res && audio_playing(CH_MUSIC) && !mstop.on)
        return;
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    bool loop = flags & 1, queue = flags & 2;
    u64 t0 = platform_us();
    if (channel == CH_MUSIC && !queue) {
        /* one continuous score: the new track comes in on the beat */
        if (mstop.on)
            PERF("music: the deferred stop becomes a change to %s", path);
        mstop.on = false;
        audio_music_change(path, loop, fadein);
    } else {
        audio_play(channel, path, loop, fadein, queue);
    }
    u64 us = platform_us() - t0;
    FP.music_us += us;
    if (channel == CH_MUSIC) {
        PERF("music: play %s took %.2f ms", path, us / 1000.0);
        E.music_res = res;
        E.music_loop = loop;
    }
    if (channel == CH_VOICE)
        E.voice_pending = true;
}

void eng_stop(u8 channel, float fadeout)
{
    if (channel >= CH_COUNT)
        return;
    u64 t0 = platform_us();
    if (channel == CH_MUSIC && fadeout > 0 && audio_playing(CH_MUSIC) && !E.skip && music_follows()) {
        mstop.on = true;
        mstop.fade = fadeout;
        mstop.t = 0;
        PERF("music: stop (fade %.1f s) deferred: new music follows", fadeout);
    } else {
        if (channel == CH_MUSIC)
            mstop.on = false;
        audio_stop(channel, fadeout);
    }
    FP.music_us += platform_us() - t0;
    if (channel == CH_MUSIC)
        E.music_res = -1;
}

void eng_window(u8 mode)
{
    E.window_mode = mode;
}

void eng_say_begin(void)
{
    E.committed = E.stage;
    if (!E.voice_pending)
        audio_stop(CH_VOICE, 0);
    E.voice_pending = false;
}

/* ---- dialogue ------------------------------------------------------------ */

static void prepare_text(void)
{
    const VM *vm = &E.vm;
    const CharDef *c = &E.game.chars[vm->say_char];
    bool centered = c->kind == CHR_CENTERED;
    float width = centered ? CENTER_TEXT_W : BOX_TEXT_W;
    static const float scales[] = {0.5f, 0.46f, 0.42f, 0.38f, 0.34f};
    for (size_t i = 0; i < ARRAY_LEN(scales); i++) {
        E.text_scale = scales[i];
        ui_wrap(vm->say_text, width, E.text_scale, E.wrapped, sizeof(E.wrapped));
        if (centered || ui_count_lines(E.wrapped) * gfx_line_height(E.text_scale) <= BOX_TEXT_H)
            break;
    }
    E.text_cps_len = utf8_len(E.wrapped);
    E.text_shown = 0;
    E.text_done = false;
    E.auto_timer = 0;
    if (vm->say_flags & SAY_EXTEND) {
        /* the part shown before `extend` appears at once */
        char prev[VM_TEXT];
        size_t n = vm->extend_from < sizeof(prev) ? vm->extend_from : sizeof(prev) - 1;
        memcpy(prev, vm->say_text, n);
        prev[n] = 0;
        E.text_shown = (float)utf8_len(prev);
    }
}

static void run_vm(void)
{
    VM *vm = &E.vm;
    FP.advanced = true;
    predict_due = true;
    talk_end();
    vm_run(vm);
    /* the player is asked for something: a deferred stop of the music is real */
    if (mstop.on && vm->state != VM_WITH && !(vm->state == VM_PAUSE && vm->pause_time >= 0))
        music_stop_now();
    switch (vm->state) {
    case VM_SAY: {
        E.say_serial++;
        if (!(vm->say_flags & SAY_EXTEND))
            E.story_step++;
        if (E.time - E.autosave_t > 120.0f) {
            u64 t0 = platform_us();
            autosave(true);   /* written by the background thread */
            FP.save_us += platform_us() - t0;
        }
        if (AP.on)
            LOG("say: %s%s%s", vm->say_who, vm->say_who[0] ? ": " : "", vm->say_text);
        prepare_text();
        talk_begin();
        const CharDef *c = &E.game.chars[vm->say_char];
        ui_hist_add(vm->say_who, c->name_color, vm->say_text, vm->say_flags & SAY_EXTEND);
        break;
    }
    case VM_MENU:
        E.menu_sel = 0;
        E.skip = false;
        if (vm->say_text[0]) {
            prepare_text();
            E.text_shown = (float)E.text_cps_len;
            E.text_done = true;
            const CharDef *c = &E.game.chars[vm->say_char];
            ui_hist_add(vm->say_who, c->name_color, vm->say_text, false);
        }
        E.committed = E.stage;
        break;
    case VM_PAUSE:
        E.pause_left = vm->pause_time;
        E.committed = E.stage;
        break;
    case VM_GAME: {
        E.committed = E.stage;
        const MiniGame *g = mg_find(vm->mg_id);
        if (g) {
            mg_begin(g, true);
        } else {   /* unknown game: carry on with an average score */
            LOG("unknown minigame '%s'", vm->mg_id);
            vm_minigame_done(vm, 50);
            run_vm();
        }
        break;
    }
    case VM_ENDED:
        drop_resume();
        E.screen = SCR_TITLE;   /* (so app_to_title doesn't autosave the ending) */
        app_to_title();
        break;
    case VM_ERROR: {
        char msg[300];
        snprintf(msg, sizeof(msg), "Script error: %s", vm->error);
        app_error(msg);
        break;
    }
    default:
        break;
    }
}

void app_choose(int i)
{
    if (E.vm.state != VM_MENU || i < 0 || i >= E.vm.nchoices)
        return;
    char line[300];
    snprintf(line, sizeof(line), "> %s", E.vm.choices[i].text);
    ui_hist_add("", 0xAAAAAAFF, line, false);
    vm_choose(&E.vm, i);
    run_vm();
}

/* ---- per-frame update ---------------------------------------------------- */

static void update_transition(float dt, bool click)
{
    Transition *tr = &E.tr;
    if (!tr->active)
        return;
    tr->t += dt;
    if (tr->def->type == TR_PUNCH) {
        float amp = 10.0f * E.game.scale * (1.0f - clampf(tr->t / tr->dur, 0, 1));
        float wave = sinf(tr->t / 0.1f * 3.14159265f);
        E.punch_x = tr->def->dir ? amp * wave : 0;
        E.punch_y = tr->def->dir ? 0 : amp * wave;
    }
    if (tr->t >= tr->dur || click || E.skip)
        finish_transition();
}

static void game_update(const Input *in, float dt)
{
    VM *vm = &E.vm;
    if (E.overlay != OV_NONE) {
        ui_overlay_input(in);
        return;
    }
    if (in->down & KEY_START_) {
        E.overlay = OV_PREFS;
        E.prefs_sel = 0;
        return;
    }
    if (E.hide_ui) {
        if (in->down & (KEY_A_ | KEY_B_ | KEY_SELECT_ | KEY_TOUCH_))
            E.hide_ui = false;
        stage_update(&E.stage, &E.game, dt);
        return;
    }
    if (in->down & KEY_SELECT_) {
        E.hide_ui = true;
        return;
    }
    bool interacting = vm->state == VM_SAY || vm->state == VM_MENU || vm->state == VM_PAUSE;
    if (interacting && (in->down & KEY_Y_ || (vm->state == VM_SAY && in->down & KEY_UP_))) {
        E.overlay = OV_LOG;
        E.log_scroll = 0;
        return;
    }
    if (interacting && (in->down & KEY_X_)) {
        E.overlay = OV_SAVE;
        E.slot_sel = 0;
        save_scan(E.slot_page, E.slots);
        return;
    }
    if (in->down & KEY_L_)
        E.auto_mode = !E.auto_mode;
    E.skip = E.skip_toggle || (in->held & KEY_R_);
    if (vm->state == VM_MENU)
        E.skip = E.skip_toggle = false;

    stage_update(&E.stage, &E.game, dt);
    pys_story_update(dt);
    bool click = (in->down & KEY_A_) != 0;
    if (E.tr.active) {
        update_transition(dt, click);
        return;
    }

    switch (vm->state) {
    case VM_SAY: {
        float cps = TEXT_SPEEDS[E.set.text_speed];
        if (!E.text_done) {
            if (cps <= 0 || E.skip || click) {
                E.text_shown = (float)E.text_cps_len;
                click = false;
            } else {
                E.text_shown += cps * dt;
            }
            if (E.text_shown >= (float)E.text_cps_len) {
                E.text_shown = (float)E.text_cps_len;
                E.text_done = true;
                E.auto_timer = 0;
            }
        }
        talk_update(dt);
        if (E.text_done) {
            E.auto_timer += dt;
            float wait = E.set.auto_delay + 0.02f * (float)E.text_cps_len;
            bool advance = click || E.skip || (vm->say_flags & SAY_NOWAIT) ||
                           (E.auto_mode && E.auto_timer >= wait && !audio_playing(CH_VOICE));
            if (advance) {
                vm_resume(vm);
                run_vm();
            }
        }
        break;
    }
    case VM_MENU:
        if (in->down & KEY_UP_)
            E.menu_sel = (E.menu_sel + vm->nchoices - 1) % vm->nchoices;
        if (in->down & KEY_DOWN_)
            E.menu_sel = (E.menu_sel + 1) % vm->nchoices;
        if (click)
            app_choose(E.menu_sel);
        break;
    case VM_PAUSE:
        if (E.pause_left >= 0) {
            E.pause_left -= dt;
            if (E.pause_left <= 0 || click || E.skip) {
                vm_resume(vm);
                run_vm();
            }
        } else if (click || E.skip) {
            vm_resume(vm);
            run_vm();
        }
        break;
    case VM_GAME: {
        E.committed = E.stage;
        const MiniGame *g = mg_find(vm->mg_id);
        if (g) {
            mg_begin(g, true);
        } else {   /* unknown game: carry on with an average score */
            LOG("unknown minigame '%s'", vm->mg_id);
            vm_minigame_done(vm, 50);
            run_vm();
        }
        break;
    }
    case VM_ENDED:
        drop_resume();
        E.screen = SCR_TITLE;   /* (so app_to_title doesn't autosave the ending) */
        app_to_title();
        break;
    default:
        break;
    }
}

static void touch_buttons(const Input *in)
{
    if (!(in->down & KEY_TOUCH_))
        return;
    Button b[48];
    int n = ui_buttons(b, 48);
    for (int i = 0; i < n; i++) {
        if (b[i].disabled)
            continue;
        if (in->tx >= b[i].x && in->tx < b[i].x + b[i].w && in->ty >= b[i].y &&
            in->ty < b[i].y + b[i].h) {
            ui_activate(b[i].id);
            return;
        }
    }
}

/* ---- receiving while playing ------------------------------------------------ */

#ifdef __3DS__
bool app_listen_background = true;
#else
bool app_listen_background = false;   /* desktop tests opt in with --listen */
#endif

static u32 rx_seen;
static bool rx_was_receiving;

static int game_index(const char *id)
{
    for (int i = 0; i < E.ngames; i++)
        if (!strcmp(E.games[i], id))
            return i;
    return -1;
}

int app_home_count(void)
{
    return E.ngames + (E.rx_new ? 1 : 0);
}

bool app_rx_busy(const char *id)
{
    if (!NET.receiving || !id || !id[0])
        return false;
    char cur[64];
    snprintf(cur, sizeof(cur), "%s", NET.game);
    return !strcmp(cur, id);
}

float app_rx_progress(void)
{
    if (!NET.bytes_total)
        return 0;
    return clampf((float)((double)NET.bytes_done / (double)NET.bytes_total), 0, 1);
}

void app_rx_eta_text(char *out, size_t len)
{
    out[0] = 0;
    if (!NET.receiving || E.rx_rate <= 0)
        return;
    u64 done = NET.bytes_done, total = NET.bytes_total;
    double left = done < total ? (double)(total - done) / E.rx_rate : 0;
    if (left < 60)
        snprintf(out, len, "less than a minute left");
    else if (left < 3600)
        snprintf(out, len, "about %d min left", (int)(left / 60 + 0.5));
    else
        snprintf(out, len, "about %d h %d min left", (int)(left / 3600), (int)(left / 60) % 60);
}

/* Bytes per second actually sent (files already on the card don't count),
 * smoothed over a few seconds. */
static void rx_measure(void)
{
    static float t0;
    static u64 sent0;
    u64 sent = NET.bytes_done - NET.bytes_skipped;
    if (!rx_was_receiving) {
        t0 = E.time;
        sent0 = sent;
        E.rx_rate = 0;
        return;
    }
    if (E.time - t0 < 1.0f)
        return;
    float r = sent > sent0 ? (float)((double)(sent - sent0) / (E.time - t0)) : 0;
    E.rx_rate = E.rx_rate > 0 ? E.rx_rate * 0.8f + r * 0.2f : r;
    t0 = E.time;
    sent0 = sent;
}

/* A game that isn't in the list yet gets its own card while it arrives. */
static void rx_track_new_game(void)
{
    static float looked_up;
    char id[64];
    snprintf(id, sizeof(id), "%s", NET.receiving ? NET.game : "");
    if (!id[0] || game_index(id) >= 0) {
        if (E.rx_new) {
            E.rx_new = false;
            gfx_tex_free(E.rx_new_cover);
            E.rx_new_cover = NULL;
            if (E.game_sel >= E.ngames)
                E.game_sel = E.ngames > 0 ? E.ngames - 1 : 0;
        }
        return;
    }
    if (!E.rx_new || strcmp(E.rx_new_id, id)) {
        E.rx_new = true;
        snprintf(E.rx_new_id, sizeof(E.rx_new_id), "%s", id);
        snprintf(E.rx_new_title, sizeof(E.rx_new_title), "%s", id);
        gfx_tex_free(E.rx_new_cover);
        E.rx_new_cover = NULL;
        looked_up = -10;
    }
    if (E.time - looked_up > 1.0f) {   /* its real title, once game.bin is in */
        looked_up = E.time;
        char dir[400], title[96];
        snprintf(dir, sizeof(dir), "%s/games/%s", E.root, id);
        if (game_peek_title(dir, title, sizeof(title)))
            snprintf(E.rx_new_title, sizeof(E.rx_new_title), "%s", title);
        if (!E.rx_new_cover) {   /* and its cover, once that is in */
            char path[400];
            cover_path(id, path, sizeof(path));
            E.rx_new_cover = app_load_thm(path);
        }
    }
}

static void rx_done_toast(void)
{
    char id[64], msg[96];
    snprintf(id, sizeof(id), "%s", NET.last_game);
    int i = game_index(id);
    const char *title = i >= 0 ? E.game_titles[i] : id;
    if (id[0] && NET.staged && E.loaded && !strcmp(id, E.game.id))
        snprintf(msg, sizeof(msg), "Update for %s: applies next time", title);
    else if (id[0] && NET.engine_updated)
        snprintf(msg, sizeof(msg), "%s is ready. Restart vn3ds to update it", title);
    else if (id[0])
        snprintf(msg, sizeof(msg), "%s is ready", title);
    else if (NET.engine_updated)
        snprintf(msg, sizeof(msg), "vn3ds updated: restart it to use it");
    else
        return;
    app_toast(msg);
    E.toast_t = 3.5f;
}

/* Called every frame: keeps the background receiver going. Nothing stops
 * for a transfer: a corner icon shows it, and the home screen its card. */
static void rx_update(Input *in)
{
    net_poll();
    update_poll();  /* a newer vn3ds release (update.h) */
    if (sync_poll()) {   /* a computer synced saves: what the screens show may have changed */
        app_toast("Saves updated from your computer");
        if (E.loaded) {
            SlotInfo info;
            E.has_resume = save_peek(E.game.id, RESUME_SLOT, &info);
        }
        home_refresh();
    }
    fetch_poll();
    rx_measure();
    /* overnight transfers: stay awake. (The screens stay on: switching the
     * backlights off during a transfer froze vn3ds on a real New 3DS.) */
    static bool awake_held;
    if (NET.receiving != awake_held) {
        awake_held = NET.receiving;
        platform_keep_awake(awake_held);
    }
    static float beat;
    if (NET.receiving && (beat += 1.0f / 60.0f) > 5.0f) {   /* for log.txt after a freeze */
        beat = 0;
        LOG("rx: %s | %u of %u files, %.1f MB", NET.message, (unsigned)NET.files_done,
            (unsigned)NET.files_total, NET.bytes_done / 1048576.0);
    }
    bool finished = NET.completed != rx_seen;
    if (finished || (rx_was_receiving && !NET.receiving)) {
        app_rescan_games();
        if (finished && E.screen != SCR_RECEIVE)
            rx_done_toast();
        rx_seen = NET.completed;
    }
    rx_track_new_game();
    rx_was_receiving = NET.receiving;
}

static void update_frame(const Input *in_real, float dt);
static u64 perf_update_us;
static u32 perf_report_frames;   /* frames after an advance still being reported */
static bool perf_a;

void app_update(const Input *in_real, float dt)
{
    memset(&FP, 0, sizeof(FP));
    u64 t0 = platform_us();
    update_frame(in_real, dt);
    perf_update_us = platform_us() - t0;
    perf_a = (in_real->down & KEY_A_) != 0;
}

/* The timing line for a frame (see app_render): every frame on which the
 * story moved on and the two after it, and any slow frame. */
static void perf_frame(u64 render_us)
{
    if (FP.advanced)
        perf_report_frames = 3;
#ifdef __3DS__
    u64 total = perf_update_us + render_us;
#else
    u64 total = perf_update_us;   /* (the desktop's software renderer is no guide) */
#endif
    if (perf_report_frames == 0 && total < 20000 && !FP.tex_sync)
        return;
    const char *what = FP.advanced ? "advance" : perf_report_frames > 0 ? "after" : "slow";
    if (perf_report_frames > 0)
        perf_report_frames--;
    PERF("frame %u %s%s: update %.2f ms, render %.2f ms; sync textures %u (%u KB, %.2f ms), "
         "preloaded %u; music %.2f ms; save %.2f ms",
         (unsigned)E.frame, what, perf_a ? " (A)" : "", perf_update_us / 1000.0, render_us / 1000.0,
         (unsigned)FP.tex_sync, (unsigned)(FP.tex_sync_bytes >> 10), FP.tex_sync_us / 1000.0,
         (unsigned)FP.tex_ready, FP.music_us / 1000.0, FP.save_us / 1000.0);
}

/* Desktop test runs that skip drawing still get their timing lines. */
void app_frame_done_without_drawing(void) { perf_frame(0); }

static void update_frame(const Input *in_real, float dt)
{
    Input in_copy = *in_real;
    Input *in = &in_copy;
    autoplay_input(in, dt);
    E.time += dt;
    E.frame++;
    texcache_pump();
    if (predict_due) {   /* (the frame after the story moved on) */
        predict_due = false;
        run_prediction();
    }
    if (mstop.on && (mstop.t += dt) > 10.0f)
        music_stop_now();
    video_update(dt);
    if (E.toast_t > 0)
        E.toast_t -= dt;
    audio_update(dt);
    lb_poll();
    rx_update(in);

    E.cf_pos += ((float)E.game_sel - E.cf_pos) * fminf(1.0f, dt * 9.0f);

    Screen before = E.screen;
    Overlay ov_before = E.overlay;
    touch_buttons(in);
    if (E.screen != before || E.overlay != ov_before)
        return;

    switch (E.screen) {
    case SCR_RECEIVE: {
        if (in->down & (KEY_B_ | KEY_START_))
            app_receive_close();
        break;
    }
    case SCR_GAMELIST:
        home_update(in, dt);   /* home.c */
        break;
    case SCR_TITLE:
        if (E.overlay != OV_NONE) {
            ui_overlay_input(in);
            break;
        }
        {
            int ids[8], cnt = ui_title_items(ids);
            if (in->down & KEY_UP_)
                E.title_sel = (E.title_sel + cnt - 1) % cnt;
            if (in->down & KEY_DOWN_)
                E.title_sel = (E.title_sel + 1) % cnt;
            if (E.title_sel >= cnt)
                E.title_sel = 0;
            if (in->down & KEY_A_)
                ui_activate(ids[E.title_sel]);
        }
        if ((in->down & KEY_B_) && !app_single_game)
            app_to_library();
        if ((in->down & KEY_Y_) && !app_single_game)
            app_receive_open();
        if (in->down & KEY_START_) {
            if (app_single_game)
                E.quit = true;
            else
                app_to_library();
        }
        break;
    case SCR_GAME:
        game_update(in, dt);
        break;
    case SCR_MINIGAME:
        mg_update(in, dt);
        break;
    case SCR_MGMENU: {
        int cnt = mg_count(), was = E.mg_sel;
        if (in->down & KEY_UP_)
            E.mg_sel = (E.mg_sel + cnt - 1) % cnt;
        if (in->down & KEY_DOWN_)
            E.mg_sel = (E.mg_sel + 1) % cnt;
        if (E.mg_board && E.mg_sel != was)
            ui_mg_board();   /* follow the selection */
        if (in->down & KEY_A_) {
            E.mg_board = false;
            mg_begin(mg_at(E.mg_sel), false);
        } else if (in->down & KEY_X_) {
            ui_mg_board();
        } else if (in->down & KEY_B_) {
            if (E.mg_board)
                E.mg_board = false;
            else
                E.screen = SCR_TITLE;
        }
        break;
    }
    case SCR_ERROR:
        if (in->down & (KEY_A_ | KEY_START_)) {
            if (E.loaded)
                app_to_title();
            else if (app_single_game)
                E.quit = true;   /* the game didn't open: nothing else to show */
            else
                E.screen = SCR_GAMELIST;
        }
        break;
    }
}

void app_minigame_done(int score)
{
    E.screen = SCR_GAME;
    vm_minigame_done(&E.vm, score);
    run_vm();
}

void app_render(void)
{
    u64 r0 = platform_us();
    float strength = app_strength();
    gfx_frame_begin();   /* (waits for the previous frame's GPU work) */
    u64 r1 = platform_us();
    if (snap_pending) {
        thumb_valid = gfx_snapshot_read(thumb, THUMB_W, THUMB_H);
        snap_pending = false;
        if (thumb_valid)
            story_thumb(thumb, THUMB_W, THUMB_H);
    }
    /* keep a snapshot of each new line (or choice) for the home screen. Like the
     * captures below it is drawn before the screens: drawn after the bottom
     * screen it could flash the top picture onto the bottom on a real 3DS. */
    if (!E.opening && E.screen == SCR_GAME && E.overlay == OV_NONE && E.say_serial != snapped_serial &&
        ((E.vm.state == VM_SAY && E.text_done) || E.vm.state == VM_MENU)) {
        snapped_serial = E.say_serial;
        story_snapshot();
        gfx_target_snapshot(0x000000FF);
        ui_draw_top(EYE_LEFT);
        snap_pending = true;
    }
    if (E.screen == SCR_GAME && E.tr.active && E.tr.need_capture) {
        for (int eye = 0; eye < 2; eye++) {
            gfx_target_capture(eye, 0x000000FF);
            render_stage(&E.tr.old, eye, NULL, 0);
        }
        E.tr.need_capture = false;
    }
    if (E.screen == SCR_MINIGAME && (MG.phase == MG_PLAY || MG.phase == MG_PAUSED) &&
        MG.game->draw_offscreen) {
        for (int eye = 0; eye < (strength > 0 ? 2 : 1); eye++) {
            gfx_target_capture(eye, 0x000000FF);
            MG.game->draw_offscreen(eye);
        }
    }
    gfx_target_top(EYE_LEFT, 0x000000FF);
    ui_draw_top(EYE_LEFT);
    ui_draw_rx_icon(EYE_LEFT);
    ui_draw_opening(EYE_LEFT);
    if (strength > 0) {
        gfx_target_top(EYE_RIGHT, 0x000000FF);
        ui_draw_top(EYE_RIGHT);
        ui_draw_rx_icon(EYE_RIGHT);
        ui_draw_opening(EYE_RIGHT);
    }
    gfx_target_bottom(0x1A1A24FF);
    ui_draw_bottom();
    ui_draw_opening(-1);
    u64 r2 = platform_us();
    gfx_frame_end();
    /* the time spent drawing, without the waits for the GPU and the screen */
    perf_frame((r2 - r1) + (r1 - r0 > 2000 ? 0 : r1 - r0));
}
