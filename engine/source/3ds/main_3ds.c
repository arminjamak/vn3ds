/* 3DS entry point: input mapping, platform helpers and the main loop. */

#include <3ds.h>
#include <dirent.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <time.h>

#include "../app.h"

#define ROOT "sdmc:/3ds/vn3ds"

/* Main thread stack (libctru's default is 32 KiB). The Opus decoder keeps
 * its scratch arrays on the stack, about 16 KiB per call for stereo, and
 * it runs at the bottom of the frame's call chain. */
u32 __stacksize__ = 96 * 1024;

static FILE *log_file;

const char *platform_root(void) { return ROOT; }
bool platform_mkdir(const char *path) { return mkdir(path, 0777) == 0; }
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
    if (!log_file) {
        /* keep the previous run's log: after a freeze it says where it stopped */
        remove(ROOT "/log.old.txt");
        rename(ROOT "/log.txt", ROOT "/log.old.txt");
        log_file = fopen(ROOT "/log.txt", "w");
    }
    if (!log_file)
        return;
    va_list ap;
    va_start(ap, fmt);
    vfprintf(log_file, fmt, ap);
    va_end(ap);
    fputc('\n', log_file);
    fflush(log_file);
}

static u32 map_keys(u32 k)
{
    u32 o = 0;
    if (k & KEY_A) o |= KEY_A_;
    if (k & KEY_B) o |= KEY_B_;
    if (k & KEY_X) o |= KEY_X_;
    if (k & KEY_Y) o |= KEY_Y_;
    if (k & KEY_L) o |= KEY_L_;
    if (k & KEY_R) o |= KEY_R_;
    if (k & KEY_ZL) o |= KEY_ZL_;
    if (k & KEY_ZR) o |= KEY_ZR_;
    if (k & KEY_START) o |= KEY_START_;
    if (k & KEY_SELECT) o |= KEY_SELECT_;
    if (k & KEY_DUP) o |= KEY_UP_;
    if (k & KEY_DDOWN) o |= KEY_DOWN_;
    if (k & KEY_DLEFT) o |= KEY_LEFT_;
    if (k & KEY_DRIGHT) o |= KEY_RIGHT_;
    if (k & KEY_TOUCH) o |= KEY_TOUCH_;
    return o;
}

void platform_keep_awake(bool on)
{
    aptSetSleepAllowed(!on);
}

void platform_screens(bool on)
{
    static bool off;
    if (on == !off)
        return;
    if (R_SUCCEEDED(gspLcdInit())) {
        if (on)
            GSPLCD_PowerOnAllBacklights();
        else
            GSPLCD_PowerOffAllBacklights();
        gspLcdExit();
        off = !on;
    }
}

/* HOME, sleep (closing the lid) or the power menu: save where we are first,
 * so the home screen can carry on from exactly here. */
static aptHookCookie apt_cookie;

static void on_apt(APT_HookType type, void *param)
{
    (void)param;
    static const char *names[] = {"suspend", "restore", "sleep", "wakeup", "exit"};
    LOG("apt: %s", type < 5 ? names[type] : "?");
    if (type == APTHOOK_ONSUSPEND || type == APTHOOK_ONSLEEP || type == APTHOOK_ONEXIT)
        app_autosave();
}

int main(int argc, char **argv)
{
    /* Started over Wi-Fi from the Homebrew Launcher (3dslink): go straight to
     * the receive screen so `vn3ds-port --install` can save us to the card. */
    if (argc > 0 && argv[0] && strncmp(argv[0], "3dslink:", 8) == 0)
        app_start_receiving = true;
    osSetSpeedupEnable(true); /* 804 MHz on New 3DS */
    gfx_init();
    mkdir("sdmc:/3ds", 0777);
    mkdir(ROOT, 0777);
    mkdir(ROOT "/games", 0777);
    audio_init();
    srand((unsigned)time(NULL));
    app_init(NULL);
    aptHook(&apt_cookie, on_apt, NULL);

    u64 last = osGetTime();
    while (aptMainLoop()) {
        hidScanInput();
        Input in;
        memset(&in, 0, sizeof(in));
        in.down = map_keys(hidKeysDown());
        in.held = map_keys(hidKeysHeld());
        in.up = map_keys(hidKeysUp());
        if (hidKeysHeld() & KEY_TOUCH) {
            touchPosition tp;
            hidTouchRead(&tp);
            in.tx = tp.px;
            in.ty = tp.py;
        }
        circlePosition cp;
        hidCircleRead(&cp);
        in.cx = clampf(cp.dx / 156.0f, -1, 1);
        in.cy = clampf(cp.dy / 156.0f, -1, 1);

        u64 now = osGetTime();
        float dt = clampf((float)(now - last) / 1000.0f, 0.0f, 0.1f);
        last = now;

        app_update(&in, dt);
        if (E.quit)
            break;
        app_render();
    }

    aptUnhook(&apt_cookie);
    platform_screens(true);
    platform_keep_awake(false);
    app_shutdown();
    audio_exit();
    gfx_exit();
    if (log_file)
        fclose(log_file);
    return 0;
}
