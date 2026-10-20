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
/* The log is written from the main thread and the background thread. */
static LightLock log_lock;
static bool log_lock_ready;

const char *platform_root(void) { return ROOT; }
bool platform_mkdir(const char *path) { return mkdir(path, 0777) == 0; }
u32 platform_time(void) { return (u32)time(NULL); }
u64 platform_ms(void) { return osGetTime(); }
u64 platform_us(void) { return svcGetSystemTick() * 1000u / (SYSCLOCK_ARM11 / 1000u); }

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

static void log_open(void)
{
    if (!log_file) {
        /* keep the previous run's log: after a freeze it says where it stopped */
        remove(ROOT "/log.old.txt");
        rename(ROOT "/log.txt", ROOT "/log.old.txt");
        log_file = fopen(ROOT "/log.txt", "w");
    }
}

static void log_lock_take(void)
{
    if (!log_lock_ready) {
        LightLock_Init(&log_lock);
        log_lock_ready = true;
    }
    LightLock_Lock(&log_lock);
}

/* perf lines wait here until the background thread writes them out */
static char perf_buf[24 * 1024];
static size_t perf_len;
static u32 perf_dropped;

static void perf_write_locked(void)
{
    log_open();
    if (log_file && perf_len) {
        fwrite(perf_buf, 1, perf_len, log_file);
        if (perf_dropped)
            fprintf(log_file, "perf: (%u lines dropped, the buffer was full)\n", (unsigned)perf_dropped);
        fflush(log_file);
    }
    perf_len = 0;
    perf_dropped = 0;
}

void platform_log(const char *fmt, ...)
{
    log_lock_take();
    perf_write_locked();   /* keep the lines in order */
    if (log_file) {
        va_list ap;
        va_start(ap, fmt);
        vfprintf(log_file, fmt, ap);
        va_end(ap);
        fputc('\n', log_file);
        fflush(log_file);
    }
    LightLock_Unlock(&log_lock);
}

void platform_perf(const char *fmt, ...)
{
    char line[256];
    int n = snprintf(line, sizeof(line), "perf %.3f: ", (double)osGetTime() / 1000.0);
    va_list ap;
    va_start(ap, fmt);
    n += vsnprintf(line + n, sizeof(line) - (size_t)n - 1, fmt, ap);
    va_end(ap);
    if (n > (int)sizeof(line) - 2)
        n = (int)sizeof(line) - 2;
    line[n++] = '\n';
    log_lock_take();
    if (perf_len + (size_t)n <= sizeof(perf_buf)) {
        memcpy(perf_buf + perf_len, line, (size_t)n);
        perf_len += (size_t)n;
    } else {
        perf_dropped++;
    }
    LightLock_Unlock(&log_lock);
}

/* Called by the background thread now and then (and at exit). */
void platform_perf_flush(void)
{
    if (!perf_len)
        return;
    log_lock_take();
    perf_write_locked();
    LightLock_Unlock(&log_lock);
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
    platform_perf_flush();
    if (log_file)
        fclose(log_file);
    return 0;
}
