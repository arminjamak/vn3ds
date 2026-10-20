/* Desktop test runner: plays a packed game without a 3DS.
 *
 *   vn3ds-host build/<id> [--out frames] [--choices 0,1] [--slider 1.0]
 *              [--every N] [--test-save] [--root dir]
 *              [--record frames.rgb --audio-log audio.txt --pace --stop-label L]
 *              [--minigame id [--every N]]   (plays a minigame with its bot)
 *              [--leaderboard id]   (renders the Minigames menu's online top 10)
 *
 * It presses A through dialogue, picks menu choices from --choices (0 when
 * the list runs out), prints a transcript, and writes one PNG per line of
 * dialogue: both eyes side by side, a red/cyan anaglyph and the bottom screen.
 *
 * Recording (used by tools/vn3ds-record): --record writes the top screen's
 * left eye and the bottom screen side by side as raw RGB24 at 30 fps, --audio-log the timestamped audio calls,
 * --pace holds each line and menu long enough to read, and --stop-label ends
 * the run when the script reaches that label.
 */

#include "../source/app.h"
#include "../source/leaderboard.h"
#include "../source/minigame.h"
#include "host.h"
#include "../source/net.h"
#include <unistd.h>

#include <dirent.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <time.h>
#include <zlib.h>

static char root_dir[512] = "host_root";
extern FILE *host_audio_log;
extern double host_now;

/* How long a line stays up once it has finished typing: a reader takes
 * about a second plus 20 characters a second, and has been reading while it
 * typed out at the default 50 characters a second. */
static int read_frames(const char *text)
{
    float n = (float)strlen(text);
    float sec = 1.0f + n / 20.0f - n / 50.0f;
    return (int)(fminf(fmaxf(sec, 0.9f), 7.0f) * 60.0f);
}

/* One recorded frame: the top screen's left eye and the bottom screen side
 * by side, (TOP_W + BOT_W) x TOP_H, RGB24. */
static void record_frame(FILE *f)
{
    enum { RW = TOP_W + BOT_W };
    static u8 rgb[RW * TOP_H * 3];
    int w, h;
    const u8 *l = host_surface(0, &w, &h);
    const u8 *b = host_surface(2, &w, &h);
    for (int y = 0; y < TOP_H; y++) {
        for (int x = 0; x < TOP_W; x++)
            memcpy(rgb + (y * RW + x) * 3, l + (y * TOP_W + x) * 4, 3);
        for (int x = 0; x < BOT_W; x++)
            memcpy(rgb + (y * RW + TOP_W + x) * 3, b + (y * BOT_W + x) * 4, 3);
    }
    fwrite(rgb, 1, sizeof(rgb), f);
}

const char *platform_root(void) { return root_dir; }
bool platform_mkdir(const char *path) { return mkdir(path, 0755) == 0; }
u32 platform_time(void) { return (u32)time(NULL); }

void platform_list_dirs(const char *path, void (*cb)(const char *, void *), void *ud)
{
    DIR *d = opendir(path);
    if (!d)
        return;
    struct dirent *e;
    while ((e = readdir(d)))
        if (e->d_name[0] != '.')
            cb(e->d_name, ud);
    closedir(d);
}

void platform_log(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "    [log] ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
}

/* ---- PNG output ---------------------------------------------------------- */

static void put32(FILE *f, u32 v)
{
    u8 b[4] = {(u8)(v >> 24), (u8)(v >> 16), (u8)(v >> 8), (u8)v};
    fwrite(b, 1, 4, f);
}

static void chunk(FILE *f, const char *type, const u8 *data, u32 len)
{
    put32(f, len);
    fwrite(type, 1, 4, f);
    if (len)
        fwrite(data, 1, len, f);
    uLong crc = crc32(0, (const Bytef *)type, 4);
    if (len)
        crc = crc32(crc, data, len);
    put32(f, (u32)crc);
}

static void write_png(const char *path, const u8 *rgb, int w, int h)
{
    size_t raw_len = (size_t)(w * 3 + 1) * h;
    u8 *raw = malloc(raw_len);
    for (int y = 0; y < h; y++) {
        raw[y * (w * 3 + 1)] = 0;
        memcpy(raw + y * (w * 3 + 1) + 1, rgb + y * w * 3, (size_t)w * 3);
    }
    uLongf zlen = compressBound(raw_len);
    u8 *z = malloc(zlen);
    compress2(z, &zlen, raw, raw_len, 6);
    FILE *f = fopen(path, "wb");
    if (f) {
        fwrite("\x89PNG\r\n\x1a\n", 1, 8, f);
        u8 ihdr[13] = {0};
        ihdr[0] = (u8)(w >> 24); ihdr[1] = (u8)(w >> 16); ihdr[2] = (u8)(w >> 8); ihdr[3] = (u8)w;
        ihdr[4] = (u8)(h >> 24); ihdr[5] = (u8)(h >> 16); ihdr[6] = (u8)(h >> 8); ihdr[7] = (u8)h;
        ihdr[8] = 8;
        ihdr[9] = 2;
        chunk(f, "IHDR", ihdr, 13);
        chunk(f, "IDAT", z, (u32)zlen);
        chunk(f, "IEND", NULL, 0);
        fclose(f);
    }
    free(raw);
    free(z);
}

/* Layout: [left eye | right eye] over [anaglyph | bottom screen]. */
static void dump(const char *dir, int index, const char *tag)
{
    int W = TOP_W * 2 + 8, H = TOP_H * 2 + 8;
    u8 *img = calloc((size_t)(W * H), 3);
    memset(img, 40, (size_t)(W * H * 3));
    int w, h;
    const u8 *l = host_surface(0, &w, &h);
    const u8 *r = host_surface(1, &w, &h);
    for (int y = 0; y < TOP_H; y++) {
        for (int x = 0; x < TOP_W; x++) {
            const u8 *pl = l + (y * TOP_W + x) * 4, *pr = r + (y * TOP_W + x) * 4;
            u8 *dl = img + (y * W + x) * 3, *dr = img + (y * W + x + TOP_W + 8) * 3;
            u8 *da = img + ((y + TOP_H + 8) * W + x) * 3;
            memcpy(dl, pl, 3);
            memcpy(dr, pr, 3);
            da[0] = pl[0];
            da[1] = pr[1];
            da[2] = pr[2];
        }
    }
    const u8 *b = host_surface(2, &w, &h);
    for (int y = 0; y < BOT_H; y++)
        for (int x = 0; x < BOT_W; x++)
            memcpy(img + ((y + TOP_H + 8) * W + x + TOP_W + 8 + 40) * 3, b + (y * BOT_W + x) * 4, 3);
    char path[700];
    snprintf(path, sizeof(path), "%s/%04d_%s.png", dir, index, tag);
    write_png(path, img, W, H);
    free(img);
}

static void record_frame(FILE *f);

/* Plays one minigame start to finish with its bot: intro, play, result. */
static int run_minigame(const char *id, const char *out, int every, FILE *rec)
{
    const MiniGame *g = mg_find(id);
    if (!g) {
        printf("ERROR: no minigame '%s'\n", id);
        return 1;
    }
    mg_begin(g, false);
    const float dt = 1.0f / 60.0f;
    int shots = 0;
    for (int frame = 0; frame < 60 * 60 * 10; frame++) {
        Input in;
        memset(&in, 0, sizeof(in));
        host_now = frame * (double)dt;
        if (MG.phase == MG_INTRO && frame == 90)
            in.down = KEY_A_;
        else if (MG.phase == MG_PLAY && g->bot)
            g->bot(&in, MG.t);
        else if (MG.phase == MG_PLAY && !g->bot && frame % 30 == 0)
            in.down = KEY_A_;
        else if (MG.phase == MG_RESULT && MG.t >= 0) {
            static int result_frames, post_wait;
            /* give the online post (up to 15 s) time to land before the screenshot */
            if (MG.posted && LB_POST.state == LB_BUSY && post_wait++ < 1500) {
                usleep(10000);
            } else if (++result_frames == 2 && out) {
                app_render();
                dump(out, shots++, "result");
            }
            /* stay long enough for the online board to scroll to you */
            if (result_frames > (MG.posted ? 480 : 120))
                in.down = KEY_A_;
        }
        in.held |= in.down;   /* the bot may also hold keys (e.g. a stylus) */
        app_update(&in, dt);
        app_render();
        if (rec && frame % 2 == 0)
            record_frame(rec);
        if (out && frame % every == 0 && E.screen == SCR_MINIGAME)
            dump(out, shots++, MG.phase == MG_INTRO ? "intro" : MG.phase == MG_RESULT ? "result" : "play");
        if (E.screen != SCR_MINIGAME)
            break;
    }
    if (host_audio_log) {
        fprintf(host_audio_log, "%.4f end\n", host_now);
        fclose(host_audio_log);
        host_audio_log = NULL;
    }
    printf("== minigame %s: score %d%%%s%s, %.1f s, cheat %s ==\n", id, MG.score,
           MG.verdict[0] ? " - " : "", MG.verdict, MG.t, MG.cheat_used ? "used" : "unused");
    if (!MG.posted)
        printf("== leaderboard: %s ==\n", lb_online() ? "not posted" : "offline");
    else if (LB_POST.state == LB_DONE)
        printf("== leaderboard: posted as %s: #%d of %d ==\n", lb_name(), LB_POST.rank, LB_POST.total);
    else
        printf("== leaderboard: post failed: %s ==\n",
               LB_POST.state == LB_FAILED ? LB_POST.error : "timed out");
    if (rec)
        fclose(rec);
    return 0;
}

/* Opens the Minigames menu's online leaderboard for one game (as the X button
 * does), waits for the list and writes <out>/0000_leaderboard.png. */
static int run_leaderboard(const char *id, const char *out)
{
    int idx = -1;
    for (int i = 0; i < mg_count(); i++)
        if (!strcmp(mg_at(i)->id, id))
            idx = i;
    if (idx < 0) {
        printf("ERROR: no minigame '%s'\n", id);
        return 1;
    }
    const float dt = 1.0f / 60.0f;
    Input in;
    memset(&in, 0, sizeof(in));
    E.screen = SCR_MGMENU;
    E.mg_sel = idx;
    in.down = KEY_X_;
    app_update(&in, dt);
    memset(&in, 0, sizeof(in));
    for (int i = 0; i < 1500 && lb_online() && (!lb_top_is(id) || LB_TOP.state == LB_BUSY); i++) {
        app_update(&in, dt);
        usleep(10000);
    }
    app_update(&in, dt);
    app_render();
    dump(out ? out : ".", 0, "leaderboard");
    if (!lb_online()) {
        printf("== leaderboard %s: offline ==\n", id);
        return 0;
    }
    if (LB_TOP.state != LB_DONE) {
        printf("== leaderboard %s: failed: %s ==\n", id, LB_TOP.error);
        return 1;
    }
    printf("== leaderboard %s: %d entries ==\n", id, LB_TOP.ntop);
    for (int i = 0; i < LB_TOP.ntop; i++)
        printf("%d\t%s\t%d\n", LB_TOP.top[i].rank, LB_TOP.top[i].name, LB_TOP.top[i].score);
    return 0;
}

/* ---- driver ------------------------------------------------------------- */

int main(int argc, char **argv)
{
    const char *game = NULL, *out = NULL, *choices = "", *label = NULL;
    bool receive = false;
    int every = 0, max_lines = 0;
    bool talk_frames = false;
    u32 talk_serial = 0;
    setvbuf(stdout, NULL, _IOLBF, 0);
    bool test_save = false, pace = false;
    FILE *rec = NULL;
    const char *stop_label = NULL, *minigame = NULL, *board = NULL;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--out") && i + 1 < argc)
            out = argv[++i];
        else if (!strcmp(argv[i], "--choices") && i + 1 < argc)
            choices = argv[++i];
        else if (!strcmp(argv[i], "--slider") && i + 1 < argc)
            host_slider_value = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--every") && i + 1 < argc)
            every = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--root") && i + 1 < argc)
            snprintf(root_dir, sizeof(root_dir), "%s", argv[++i]);
        else if (!strcmp(argv[i], "--max-lines") && i + 1 < argc)
            max_lines = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--label") && i + 1 < argc)
            label = argv[++i];
        else if (!strcmp(argv[i], "--receive"))
            receive = true;
        else if (!strcmp(argv[i], "--talk-frames"))
            talk_frames = true;
        else if (!strcmp(argv[i], "--test-save"))
            test_save = true;
        else if (!strcmp(argv[i], "--minigame") && i + 1 < argc)
            minigame = argv[++i];
        else if (!strcmp(argv[i], "--leaderboard") && i + 1 < argc)
            board = argv[++i];
        else if (!strcmp(argv[i], "--pace"))
            pace = true;
        else if (!strcmp(argv[i], "--stop-label") && i + 1 < argc)
            stop_label = argv[++i];
        else if (!strcmp(argv[i], "--record") && i + 1 < argc) {
            rec = fopen(argv[++i], "wb");
            if (!rec) {
                perror(argv[i]);
                return 2;
            }
        } else if (!strcmp(argv[i], "--audio-log") && i + 1 < argc) {
            host_audio_log = fopen(argv[++i], "w");
            if (!host_audio_log) {
                perror(argv[i]);
                return 2;
            }
        }
        else
            game = argv[i];
    }
    if (receive) {
        /* Desktop test of the Wi-Fi receiver: wait for one transfer, then exit. */
        mkdir(root_dir, 0755);
        gfx_init();
        audio_init();
        app_start_receiving = true;
        app_init(NULL);
        printf("receiving on port %d into %s\n", NET_PORT, root_dir);
        Input none;
        memset(&none, 0, sizeof(none));
        int after = 0;   /* a few frames after completion, so the app rescans */
        for (int frame = 0; frame < 60 * 600 && (NET.completed == 0 || after++ < 5); frame++) {
            app_update(&none, 1.0f / 60.0f);
            if (frame % 2 == 0)
                app_render();
            usleep(4000);
        }
        printf("%s\nfiles %u, refused %u, %.1f MB, games now: %d\n", NET.message, (unsigned)NET.files_done,
               (unsigned)NET.refused, NET.bytes_done / 1048576.0, E.ngames);
        app_render();
        dump(".", 0, "receive");
        return NET.completed ? 0 : 1;
    }
    if (!game) {
        fprintf(stderr, "usage: %s <game folder> [--out dir] [--choices 0,1,...] [--slider 0..1] "
                        "[--every N] [--test-save] [--root dir] [--label name]\n", argv[0]);
        return 2;
    }
    srand(1);
    mkdir(root_dir, 0755);
    if (host_audio_log)
        fprintf(host_audio_log, "0.0000 root %s\n", game);
    if (out)
        mkdir(out, 0755);
    gfx_init();
    audio_init();
    app_init(game);
    if (E.screen == SCR_ERROR) {
        fprintf(stderr, "%s\n", E.error);
        return 1;
    }
    printf("== %s ==\n", E.game.title);
    if (board)
        return run_leaderboard(board, out);
    if (minigame)
        return run_minigame(minigame, out, every > 0 ? every : 30, rec);

    const float dt = 1.0f / 60.0f;
    int shots = 0, lines = 0, wait = 0, menu_presses = -1;
    int saved_at = -1;
    char saved_text[VM_TEXT] = "";
    const char *cp = choices;
    bool started = false, failed = false;
    Input in;
    u32 last_serial = 0;
    s32 stop_addr = stop_label ? game_label(&E.game, stop_label) : -1;
    if (stop_label && stop_addr < 0)
        printf("    [warn] no label '%s' to stop at\n", stop_label);
    vm_watch_addr = stop_addr;
    int title_frames = pace ? 240 : 10, menu_wait = 0, pick_beat = 0;

    for (int frame = 0; frame < 60 * 60 * 60 * 12; frame++) { /* up to 12 hours of game time */
        memset(&in, 0, sizeof(in));
        host_now = frame * (double)dt;
        if (E.rx_overlay) {
            /* a transfer arrived mid-story: watch the overlay, then carry on */
            static int rxf;
            rxf++;
            if (out && rxf % 30 == 1) {
                app_render();
                dump(out, shots++, "rx");
            }
            if (E.rx_overlay >= 2 && rxf > 150) {
                printf("    [rx] received %s%s; continuing\n", E.rx_game, E.rx_staged ? " (staged update)" : "");
                in.down = KEY_B_;
                rxf = 0;
            }
            app_update(&in, dt);
            app_render();
            continue;
        }
        if (stop_addr >= 0 && vm_watch_hit) {
            printf("== reached %s ==\n", stop_label);
            break;
        }
        if (E.screen == SCR_TITLE) {
            if (started)
                break; /* the game returned to the title: done */
            if (frame == 5) {
                app_render();
                if (out)
                    dump(out, shots++, "title");
            }
            if (frame == title_frames) {
                started = true;
                if (label) {
                    if (!app_new_game_at(label)) {
                        printf("ERROR: no label '%s'\n", label);
                        failed = true;
                        break;
                    }
                } else {
                    in.down = KEY_A_;
                }
            }
        } else if (E.screen == SCR_ERROR) {
            printf("ERROR: %s\n", E.error);
            failed = true;
            break;
        } else if (E.screen == SCR_GAME && !E.tr.active) {
            VM *vm = &E.vm;
            if (talk_frames && out && vm->state == VM_SAY && !E.text_done &&
                E.text_shown > E.text_cps_len * 0.5f && talk_serial != E.say_serial) {
                talk_serial = E.say_serial;
                app_render();
                dump(out, shots++, "talking");
            }
            if (vm->state == VM_SAY && E.text_done) {
                if (wait == 0) {
                    lines++;
                    if (max_lines && lines > max_lines)
                        break;
                    if (E.say_serial != last_serial) {
                        printf("%s%s%s\n", vm->say_who[0] ? vm->say_who : "",
                               vm->say_who[0] ? ": " : "", vm->say_text);
                        if (host_audio_log)
                            fprintf(host_audio_log, "%.4f line %s%s%s\n", host_now, vm->say_who,
                                    vm->say_who[0] ? ": " : "", vm->say_text);
                        last_serial = E.say_serial;
                    }
                    if (out) {
                        app_render();
                        dump(out, shots++, "say");
                    }
                    if (test_save && saved_at < 0 && lines == 3) {
                        saved_at = lines;
                        snprintf(saved_text, sizeof(saved_text), "%s", vm->say_text);
                        printf("    [test] saved to slot 1: %s\n", save_write(1) ? "ok" : "FAILED");
                    } else if (test_save && saved_at > 0 && lines == saved_at + 3) {
                        saved_at = 0;
                        bool ok = app_load_slot(1) && E.vm.state == VM_SAY &&
                                  !strcmp(E.vm.say_text, saved_text);
                        printf("    [test] loaded slot 1: %s (%s)\n", ok ? "PASS" : "FAIL", E.vm.say_text);
                        if (!ok)
                            failed = true;
                        last_serial = E.say_serial;
                        wait = 0;
                        lines++;
                        continue;
                    }
                }
                if (++wait > (pace ? read_frames(vm->say_text) : 3)) {
                    in.down = KEY_A_;
                    wait = 0;
                }
            } else if (vm->state == VM_MENU) {
                if (pace && menu_presses < 0 && menu_wait == 0) {
                    /* time to read the choices before the cursor moves */
                    size_t chars = strlen(vm->say_text);
                    for (int i = 0; i < vm->nchoices; i++)
                        chars += strlen(vm->choices[i].text);
                    menu_wait = (int)(fminf(2.0f + chars / 22.0f, 8.0f) * 60.0f);
                }
                if (pace && menu_wait > 1) {
                    menu_wait--;
                } else if (menu_presses < 0) {
                    int pick = 0;
                    if (*cp) {
                        pick = atoi(cp);
                        while (*cp && *cp != ',')
                            cp++;
                        if (*cp == ',')
                            cp++;
                    }
                    if (pick >= vm->nchoices)
                        pick = vm->nchoices - 1;
                    if (vm->say_text[0])
                        printf("%s%s%s\n", vm->say_who[0] ? vm->say_who : "",
                               vm->say_who[0] ? ": " : "", vm->say_text);
                    for (int i = 0; i < vm->nchoices; i++)
                        printf("    %s %s\n", i == pick ? "->" : "  ", vm->choices[i].text);
                    menu_presses = pick;
                    if (out) {
                        app_render();
                        dump(out, shots++, "menu");
                    }
                }
                /* paced: one cursor step every 0.4 s, a beat on the pick */
                int step = pace ? 24 : 2;
                if (!(pace && menu_wait > 1) && frame % step == 0) {
                    if (menu_presses > 0) {
                        in.down = KEY_DOWN_;
                        menu_presses--;
                    } else if (!pace || ++pick_beat > 2) {
                        in.down = KEY_A_;
                        menu_presses = -1;
                        menu_wait = pick_beat = 0;
                    }
                }
            } else if (vm->state == VM_PAUSE && E.pause_left < 0) {
                if (++wait > (pace ? 90 : 10)) {
                    in.down = KEY_A_;
                    wait = 0;
                }
            } else {
                wait = 0;
            }
        } else if (E.screen == SCR_MINIGAME) {
            /* a minigame started by the script: play it with its bot */
            static int mg_frames;
            mg_frames++;
            if (MG.phase == MG_INTRO) {
                if (mg_frames % 90 == 0)
                    in.down = KEY_A_;
            } else if (MG.phase == MG_PLAY) {
                if (MG.game->bot)
                    MG.game->bot(&in, MG.t);
                else if (mg_frames % 30 == 0)
                    in.down = KEY_A_;
                in.held |= in.down;
            } else if (MG.phase == MG_RESULT) {
                if (mg_frames % 120 == 0) {
                    printf("    [minigame] %s: %d%%%s%s\n", MG.game->id, MG.score,
                           MG.verdict[0] ? " - " : "", MG.verdict);
                    if (out) {
                        app_render();
                        dump(out, shots++, "minigame");
                    }
                    in.down = KEY_A_;
                }
            }
        } else if (E.screen == SCR_GAME && E.tr.active && every > 0 && out &&
                   (int)(E.tr.t * 60) % every == every / 2) {
            app_render();
            dump(out, shots++, "trans");
        }
        if (E.screen == SCR_GAME && every > 0 && out && E.vm.state == VM_PAUSE &&
            E.pause_left > 0 && frame % (every * 4) == 0) {
            app_render();
            dump(out, shots++, "pause");
        }
        app_update(&in, dt);
        app_render();
        if (rec && frame % 2 == 0)
            record_frame(rec);
        if (E.quit)
            break;
    }
    extern int host_vox_count;
    printf("== %d lines, %d images written, %d voice syllables ==\n", lines, shots, host_vox_count);
    if (rec)
        fclose(rec);
    if (host_audio_log) {
        fprintf(host_audio_log, "%.4f end\n", host_now);
        fclose(host_audio_log);
    }
    app_shutdown();
    return failed ? 1 : 0;
}
