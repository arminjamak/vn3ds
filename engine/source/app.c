#include "app.h"
#include "minigame.h"
#include "leaderboard.h"
#include "net.h"
#include "video.h"

bool app_start_receiving;

Engine E;

/* characters per second; 0 = instant */
const float TEXT_SPEEDS[] = {15, 25, 35, 50, 70, 110, 0};
const int NUM_TEXT_SPEEDS = (int)ARRAY_LEN(TEXT_SPEEDS);

#define BOX_TEXT_W 372.0f
#define BOX_TEXT_H 62.0f
#define CENTER_TEXT_W 340.0f

static void run_vm(void);

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

static void unload_game(void)
{
    if (!E.loaded)
        return;
    for (int ch = 0; ch < CH_COUNT; ch++)
        audio_stop(ch, 0);
    talk_end();
    audio_vox_free();
    video_close_all();
    texcache_clear();
    vm_free(&E.vm);
    game_free(&E.game);
    E.loaded = false;
}

static bool load_game_dir(const char *dir, const char *id)
{
    unload_game();
    char err[256];
    if (!game_load(&E.game, dir, id, err, sizeof(err))) {
        app_error(err);
        return false;
    }
    E.loaded = true;
    vm_init(&E.vm, &E.game);
    talk_load_bank();
    E.music_res = -1;
    app_to_title();
    return true;
}

void app_load_game(int index)
{
    if (index < 0 || index >= E.ngames)
        return;
    char dir[400];
    snprintf(dir, sizeof(dir), "%s/games/%s", E.root, E.games[index]);
    load_game_dir(dir, E.games[index]);
}

void app_init(const char *game_dir)
{
    memset(&E, 0, sizeof(E));
    snprintf(E.root, sizeof(E.root), "%s", platform_root());
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
        return;
    }
    app_rescan_games();
    if (app_start_receiving)
        app_receive_open();
    else if (E.ngames == 1 && !AP.on)
        app_load_game(0);
}

void app_rescan_games(void)
{
    char games[300];
    E.ngames = 0;
    snprintf(games, sizeof(games), "%s/games", E.root);
    platform_list_dirs(games, add_game, NULL);
    if (E.game_sel >= E.ngames)
        E.game_sel = 0;
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
    net_stop();
    app_rescan_games();
    E.screen = SCR_GAMELIST;
}

void app_shutdown(void)
{
    lb_shutdown();
    settings_save();
    unload_game();
}

void app_to_title(void)
{
    talk_end();
    for (int ch = 0; ch < CH_COUNT; ch++)
        audio_stop(ch, 0.5f);
    E.music_res = -1;
    stage_clear(&E.stage);
    stage_clear(&E.committed);
    E.stage.has_camera = E.committed.has_camera = 0;
    E.tr.active = false;
    E.overlay = OV_NONE;
    E.screen = SCR_TITLE;
    E.title_sel = 0;
    E.skip = E.skip_toggle = E.auto_mode = E.hide_ui = false;
}

static void reset_presentation(void)
{
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
    vm_new_game(&E.vm);
    run_vm();
}

bool app_new_game_at(const char *label)
{
    s32 addr = game_label(&E.game, label);
    if (addr < 0)
        return false;
    reset_presentation();
    if (!vm_new_game_at(&E.vm, (u32)addr))
        return false;
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

/* ---- VM hooks ------------------------------------------------------------ */

static void preload(const Stage *st, const char *tag)
{
    int i = stage_find(st, tag);
    if (i < 0)
        return;
    const ImageDef *im = &E.game.images[st->s[i].image];
    if (!(im->flags & IMG_VIDEO))
        texcache_get(im->res);
    for (int k = 0; k < im->nlayers; k++)
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
    if (channel == CH_MUSIC && (flags & 4) && E.music_res == res && audio_playing(CH_MUSIC))
        return;
    char path[400];
    game_res_path(&E.game, res, path, sizeof(path));
    bool loop = flags & 1, queue = flags & 2;
    audio_play(channel, path, loop, fadein, queue);
    if (channel == CH_MUSIC) {
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
    audio_stop(channel, fadeout);
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
    talk_end();
    vm_run(vm);
    switch (vm->state) {
    case VM_SAY: {
        E.say_serial++;
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

void app_update(const Input *in_real, float dt)
{
    Input in_copy = *in_real;
    Input *in = &in_copy;
    autoplay_input(in, dt);
    E.time += dt;
    E.frame++;
    video_update(dt);
    if (E.toast_t > 0)
        E.toast_t -= dt;
    audio_update(dt);
    lb_poll();

    Screen before = E.screen;
    Overlay ov_before = E.overlay;
    touch_buttons(in);
    if (E.screen != before || E.overlay != ov_before)
        return;

    switch (E.screen) {
    case SCR_RECEIVE: {
        static u32 seen;
        net_poll();
        if (NET.completed != seen) {
            seen = NET.completed;
            app_rescan_games();
        }
        if (in->down & (KEY_B_ | KEY_START_))
            app_receive_close();
        break;
    }
    case SCR_GAMELIST:
        if (in->down & KEY_Y_) {
            app_receive_open();
            break;
        }
        if (E.ngames == 0) {
            if (in->down & KEY_START_)
                E.quit = true;
            break;
        }
        if (in->down & KEY_UP_)
            E.game_sel = (E.game_sel + E.ngames - 1) % E.ngames;
        if (in->down & KEY_DOWN_)
            E.game_sel = (E.game_sel + 1) % E.ngames;
        if (in->down & KEY_A_)
            app_load_game(E.game_sel);
        if (in->down & KEY_START_)
            E.quit = true;
        break;
    case SCR_TITLE:
        if (E.overlay != OV_NONE) {
            ui_overlay_input(in);
            break;
        }
        {
            int ids[6], cnt = ui_title_items(ids);
            if (in->down & KEY_UP_)
                E.title_sel = (E.title_sel + cnt - 1) % cnt;
            if (in->down & KEY_DOWN_)
                E.title_sel = (E.title_sel + 1) % cnt;
            if (E.title_sel >= cnt)
                E.title_sel = 0;
            if (in->down & KEY_A_)
                ui_activate(ids[E.title_sel]);
        }
        if (in->down & KEY_B_)
            E.screen = SCR_GAMELIST;
        if (in->down & KEY_Y_)
            app_receive_open();
        if (in->down & KEY_START_)
            E.quit = true;
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
    float strength = app_strength();
    gfx_frame_begin();
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
    if (strength > 0) {
        gfx_target_top(EYE_RIGHT, 0x000000FF);
        ui_draw_top(EYE_RIGHT);
    }
    gfx_target_bottom(0x1A1A24FF);
    ui_draw_bottom();
    gfx_frame_end();
}
