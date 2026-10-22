/* 3DS entry point: input mapping, platform helpers and the main loop. */

#include <3ds.h>
#include <dirent.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <time.h>

#include "../app.h"
#include "../link.h"

/* The library's folder; a standalone app (one game in its romfs, see
 * appfs_open) keeps its saves and settings in sdmc:/3ds/<game id> instead. */
static char ROOT[96] = "sdmc:/3ds/vn3ds";

/* Main thread stack (libctru's default is 32 KiB). The Opus decoder keeps
 * its scratch arrays on the stack, about 16 KiB per call for stereo, and
 * it runs at the bottom of the frame's call chain. */
u32 __stacksize__ = 96 * 1024;

static FILE *log_file;
/* The log is written from the main thread and the background thread. */
static LightLock log_lock;
static bool log_lock_ready;

const char *platform_root(void) { return ROOT; }
const char *platform_sdmc(void) { return "sdmc:"; }

static char self_path[256];
const char *platform_self_path(void) { return self_path; }

/* Luma3DS's homebrew loader (Rosalina's hb:ldr port, what the Homebrew
 * Launcher uses): the next .3dsx to start and its arguments. Every .3dsx it
 * starts chainloads to itself on exit (RUNFLAG_APTCHAINLOAD), which is when
 * the target is loaded; after that it falls back to boot.3dsx again. */
bool platform_launch(int argc, const char **argv)
{
    if (!envIsHomebrew() || argc < 1 || strncmp(argv[0], "sdmc:/", 6) != 0)
        return false;   /* a CIA title: exiting goes to the HOME Menu, not to hb:ldr */
    Handle h;
    if (R_FAILED(svcConnectToPort(&h, "hb:ldr")))
        return false;
    static u32 args[0x400 / 4];   /* u32 argc, then the strings one after another */
    memset(args, 0, sizeof(args));
    char *dst = (char *)&args[1], *end = (char *)args + sizeof(args);
    for (int i = 0; i < argc; i++) {
        size_t n = strlen(argv[i]) + 1;
        if (dst + n > end)
            break;
        memcpy(dst, argv[i], n);
        dst += n;
        args[0]++;
    }
    const char *path = argv[0] + 5;   /* without "sdmc:" */
    u32 *cmd = getThreadCommandBuffer();
    cmd[0] = IPC_MakeHeader(2, 0, 2);   /* SetTarget */
    cmd[1] = IPC_Desc_StaticBuffer(strlen(path) + 1, 0);
    cmd[2] = (u32)path;
    Result rc = svcSendSyncRequest(h);
    if (R_SUCCEEDED(rc))
        rc = cmd[1];
    if (R_SUCCEEDED(rc)) {
        cmd[0] = IPC_MakeHeader(3, 0, 2);   /* SetArgv */
        cmd[1] = IPC_Desc_StaticBuffer(sizeof(args), 1);
        cmd[2] = (u32)args;
        rc = svcSendSyncRequest(h);
        if (R_SUCCEEDED(rc))
            rc = cmd[1];
    }
    svcCloseHandle(h);
    LOG("link: hb:ldr %s -> %08lx", argv[0], (unsigned long)rc);
    return R_SUCCEEDED(rc);
}
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
        char now[128], old[128];
        snprintf(now, sizeof(now), "%s/log.txt", ROOT);
        snprintf(old, sizeof(old), "%s/log.old.txt", ROOT);
        remove(old);
        rename(now, old);
        log_file = fopen(now, "w");
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

/* ---- standalone apps: a game in the .3dsx's romfs ----------------------
 *
 * vn3ds-port --app appends a romfs holding games/<id>/ to vn3ds.3dsx. It is
 * mounted as romfs:/ for the game's loose files; the pack files are read
 * straight from the .3dsx through one shared handle (appfs_locate), so the
 * engine needs no handle per pack. */

static Handle appfs_file;
static u64 appfs_base;     /* where the romfs starts in the .3dsx */
static u32 appfs_hdr[10];  /* romfs_header, see <3ds/romfs.h> */
static u8 *appfs_dirs, *appfs_files;

static bool appfs_read(u64 off, void *dst, u32 n)
{
    u32 got = 0;
    return R_SUCCEEDED(FSFILE_Read(appfs_file, &got, appfs_base + off, dst, n)) && got == n;
}

/* Does the UTF-16 name of a romfs entry equal name[0..len)? */
static bool appfs_name_is(const u8 *e, u32 hdr, const char *name, u32 len)
{
    u32 n = *(const u32 *)(e + hdr - 4) / 2;
    if (n != len)
        return false;
    for (u32 i = 0; i < n; i++)
        if (e[hdr + i * 2] != (u8)name[i] || e[hdr + i * 2 + 1])
            return false;
    return true;
}

/* A handle on the file holding this app's romfs and where the romfs starts:
 * the .3dsx at `self` (argv[0], as the Homebrew Launcher starts it), else the
 * process's own RomFS archive (an emulator starting the .3dsx directly hands
 * it over that way, at 0x1000 as libctru's romfsMountFromCurrentProcess reads
 * it). */
static bool appfs_source(const char *self, Handle *h, u64 *base)
{
    *h = 0;
    if (self && strncmp(self, "sdmc:/", 6) == 0) {
        u32 hdr[11];   /* 3dsx header + extended header (smdh offset, size, romfs offset) */
        u32 got = 0;
        if (R_FAILED(FSUSER_OpenFileDirectly(h, ARCHIVE_SDMC, fsMakePath(PATH_EMPTY, ""),
                                             fsMakePath(PATH_ASCII, self + 5), FS_OPEN_READ, 0)))
            return false;
        if (R_SUCCEEDED(FSFILE_Read(*h, &got, 0, hdr, sizeof(hdr))) && got == sizeof(hdr) &&
            memcmp(hdr, "3DSX", 4) == 0 && (hdr[1] & 0xFFFF) >= sizeof(hdr) && hdr[10]) {
            *base = hdr[10];
            return true;
        }
        FSFILE_Close(*h);
        *h = 0;
        return false;
    }
    static const u32 zeros[3];
    FS_Path path = {PATH_BINARY, sizeof(zeros), zeros};
    if (R_FAILED(FSUSER_OpenFileDirectly(h, ARCHIVE_ROMFS, fsMakePath(PATH_EMPTY, ""), path,
                                         FS_OPEN_READ, 0)))
        return false;
    *base = 0x1000;
    return true;
}

/* Opens this app's romfs and mounts it as romfs:/. Returns the game id when
 * it holds games/<id>/game.bin. */
static bool appfs_open(const char *self, char *id, size_t idlen)
{
    if (!appfs_source(self, &appfs_file, &appfs_base))
        return false;
    if (!appfs_read(0, appfs_hdr, sizeof(appfs_hdr)) || appfs_hdr[0] != sizeof(appfs_hdr) ||
        appfs_hdr[4] > (1u << 20) || appfs_hdr[8] > (4u << 20))
        goto no;
    appfs_dirs = malloc(appfs_hdr[4]);
    appfs_files = malloc(appfs_hdr[8]);
    if (!appfs_dirs || !appfs_files || !appfs_read(appfs_hdr[3], appfs_dirs, appfs_hdr[4]) ||
        !appfs_read(appfs_hdr[7], appfs_files, appfs_hdr[8]))
        goto no;
    Handle mount = 0;   /* libctru's romfs:/ gets a handle of its own */
    u64 mbase;
    if (!appfs_source(self, &mount, &mbase))
        goto no;
    if (R_FAILED(romfsMountFromFile(mount, (u32)mbase, "romfs"))) {
        FSFILE_Close(mount);
        goto no;
    }
    DIR *d = opendir("romfs:/games");
    struct dirent *e;
    char probe[400];
    while (d && (e = readdir(d))) {
        struct stat st;
        snprintf(probe, sizeof(probe), "romfs:/games/%s/game.bin", e->d_name);
        if (e->d_name[0] != '.' && stat(probe, &st) == 0) {
            snprintf(id, idlen, "%s", e->d_name);
            closedir(d);
            return true;
        }
    }
    if (d)
        closedir(d);
    romfsUnmount("romfs");
no:
    free(appfs_dirs);
    free(appfs_files);
    appfs_dirs = appfs_files = NULL;
    FSFILE_Close(appfs_file);
    appfs_file = 0;
    return false;
}

/* Where the bytes of romfs:/<path> sit: the .3dsx's handle (shared: don't
 * close it) and their offset in it. */
bool appfs_locate(const char *path, Handle *h, u64 *off, u64 *size)
{
    if (!appfs_file || strncmp(path, "romfs:/", 7) != 0)
        return false;
    const char *p = path + 7;
    u32 dir = 0;   /* the root */
    while (*p) {
        const char *slash = strchr(p, '/');
        u32 len = slash ? (u32)(slash - p) : (u32)strlen(p);
        if (slash) {   /* a sub-folder: walk the children of dir */
            u32 c = *(const u32 *)(appfs_dirs + dir + 8);
            while (c != 0xFFFFFFFF && c + 24 <= appfs_hdr[4] &&
                   !appfs_name_is(appfs_dirs + c, 24, p, len))
                c = *(const u32 *)(appfs_dirs + c + 4);
            if (c == 0xFFFFFFFF || c + 24 > appfs_hdr[4])
                return false;
            dir = c;
            p = slash + 1;
            continue;
        }
        u32 f = *(const u32 *)(appfs_dirs + dir + 12);
        while (f != 0xFFFFFFFF && f + 32 <= appfs_hdr[8]) {
            const u8 *e = appfs_files + f;
            if (appfs_name_is(e, 32, p, len)) {
                u64 data, len_;   /* (the entries are only 4-aligned) */
                memcpy(&data, e + 8, 8);
                memcpy(&len_, e + 16, 8);
                *h = appfs_file;
                *off = appfs_base + appfs_hdr[9] + data;
                *size = len_;
                return true;
            }
            f = *(const u32 *)(e + 4);
        }
        return false;
    }
    return false;
}

Handle appfs_handle(void) { return appfs_file; }

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
    if (argc > 0 && argv[0])
        snprintf(self_path, sizeof(self_path), "%s", argv[0]);
    link_take_args(argc, argv);
    char game_id[64], game_dir[128];
    app_single_game = appfs_open(argc > 0 ? argv[0] : NULL, game_id, sizeof(game_id));
    if (app_single_game) {
        snprintf(ROOT, sizeof(ROOT), "sdmc:/3ds/%s", game_id);
        snprintf(game_dir, sizeof(game_dir), "romfs:/games/%s", game_id);
    }
    osSetSpeedupEnable(true); /* 804 MHz on New 3DS */
    gfx_init();
    mkdir("sdmc:/3ds", 0777);
    mkdir(ROOT, 0777);
    if (!app_single_game) {
        char games[128];
        snprintf(games, sizeof(games), "%s/games", ROOT);
        mkdir(games, 0777);
    }
    audio_init();
    srand((unsigned)time(NULL));
    app_init(app_single_game ? game_dir : NULL);
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
