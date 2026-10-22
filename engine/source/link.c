/* App linking between vn3ds and standalone novels; see link.h. */

#include "link.h"

#include <sys/stat.h>

#include "app.h"
#include "bg.h"
#include "platform.h"

bool link_continue;
char link_from[64];

static void path_of(char *out, size_t len, const char *rel)
{
    snprintf(out, len, "%s/3ds/%s", platform_sdmc(), rel);
}

static bool exists(const char *path)
{
    struct stat st;
    return stat(path, &st) == 0;
}

/* key=value lines into r (unknown keys are skipped) */
static bool read_cfg(const char *path, Reading *r)
{
    memset(r, 0, sizeof(*r));
    FILE *f = fopen(path, "r");
    if (!f)
        return false;
    char line[400];
    while (fgets(line, sizeof(line), f)) {
        line[strcspn(line, "\r\n")] = 0;
        char *eq = strchr(line, '=');
        if (!eq)
            continue;
        *eq = 0;
        const char *v = eq + 1;
        if (!strcmp(line, "id"))
            snprintf(r->id, sizeof(r->id), "%s", v);
        else if (!strcmp(line, "title"))
            snprintf(r->title, sizeof(r->title), "%s", v);
        else if (!strcmp(line, "app"))
            snprintf(r->app, sizeof(r->app), "%s", v);
        else if (!strcmp(line, "slot"))
            r->slot = atoi(v);
        else if (!strcmp(line, "time"))
            r->time = (u32)strtoul(v, NULL, 10);
    }
    fclose(f);
    return r->id[0] != 0;
}

static void write_cfg(const char *path, const Reading *r, bool background)
{
    char text[600];
    int n = snprintf(text, sizeof(text), "id=%s\ntitle=%s\napp=%s\nslot=%d\ntime=%u\n", r->id,
                     r->title, r->app, r->slot, (unsigned)r->time);
    if (n <= 0 || n >= (int)sizeof(text))
        return;
    if (background) {
        u8 *buf = malloc((size_t)n);
        if (buf) {
            memcpy(buf, text, (size_t)n);
            bg_write_file(path, buf, (size_t)n);   /* (takes the buffer) */
        }
        return;
    }
    FILE *f = fopen(path, "w");
    if (f) {
        fwrite(text, 1, (size_t)n, f);
        fclose(f);
    }
}

bool link_read(Reading *r)
{
    char path[300];
    path_of(path, sizeof(path), "vn3ds/reading.cfg");
    return read_cfg(path, r);
}

void link_note_reading(bool background)
{
    if (!E.loaded)
        return;
    Reading r;
    memset(&r, 0, sizeof(r));
    snprintf(r.id, sizeof(r.id), "%s", E.game.id);
    snprintf(r.title, sizeof(r.title), "%s", E.game.title ? E.game.title : E.game.id);
    if (app_single_game)
        snprintf(r.app, sizeof(r.app), "%s", platform_self_path());
    r.slot = RESUME_SLOT;
    r.time = platform_time();
    char dir[300], path[300];
    snprintf(dir, sizeof(dir), "%s/3ds", platform_sdmc());
    platform_mkdir(dir);
    path_of(dir, sizeof(dir), "vn3ds");
    platform_mkdir(dir);   /* (a standalone app on a card without vn3ds) */
    path_of(path, sizeof(path), "vn3ds/reading.cfg");
    write_cfg(path, &r, background);
}

const char *link_vn3ds_path(void)
{
    static char path[300];
    path_of(path, sizeof(path), "vn3ds.3dsx");
    if (exists(path))
        return path;
    path_of(path, sizeof(path), "vn3ds/vn3ds.3dsx");
    return exists(path) ? path : NULL;
}

void link_register_app(void)
{
    if (!app_single_game || !E.loaded)
        return;
    char src[600];
    snprintf(src, sizeof(src), "%s/cover.thm", E.game.dir);
    link_register(E.game.id, E.game.title ? E.game.title : E.game.id, platform_self_path(), src);
}

void link_register(const char *id, const char *title, const char *app, const char *src)
{
    Reading r;
    memset(&r, 0, sizeof(r));
    snprintf(r.id, sizeof(r.id), "%s", id);
    snprintf(r.title, sizeof(r.title), "%s", title);
    snprintf(r.app, sizeof(r.app), "%s", app);
    char dir[300], path[400];
    snprintf(dir, sizeof(dir), "%s/3ds/%s", platform_sdmc(), id);
    platform_mkdir(dir);
    snprintf(path, sizeof(path), "%s/app.cfg", dir);
    Reading old;
    /* (an app started by an emulator doesn't know its file: keep a known one) */
    if (!r.app[0] && read_cfg(path, &old) && old.app[0])
        snprintf(r.app, sizeof(r.app), "%s", old.app);
    if (!read_cfg(path, &old) || strcmp(old.app, r.app) || strcmp(old.title, r.title))
        write_cfg(path, &r, false);
    /* the game's card art, for vn3ds's library */
    char cover[400];
    snprintf(cover, sizeof(cover), "%s/cover.thm", dir);
    if (!exists(cover)) {
        FILE *in = fopen(src, "rb"), *out = in ? fopen(cover, "wb") : NULL;
        char buf[4096];
        size_t n;
        while (out && (n = fread(buf, 1, sizeof(buf), in)) > 0)
            fwrite(buf, 1, n, out);
        if (out)
            fclose(out);
        if (in)
            fclose(in);
    }
}

typedef struct {
    void (*cb)(const char *, const char *, const char *, const char *, void *);
    void *ud;
} ScanCtx;

static void scan_dir(const char *name, void *ud)
{
    ScanCtx *c = ud;
    char dir[300], cfg[400];
    path_of(dir, sizeof(dir), name);
    snprintf(cfg, sizeof(cfg), "%s/app.cfg", dir);
    Reading r;
    /* (an app an emulator started doesn't know its own file: listed all the same) */
    if (read_cfg(cfg, &r) && (!r.app[0] || exists(r.app)))
        c->cb(r.id, r.title, r.app, dir, c->ud);
}

void link_scan_apps(void (*cb)(const char *, const char *, const char *, const char *, void *),
                    void *ud)
{
    char dir[300];
    snprintf(dir, sizeof(dir), "%s/3ds", platform_sdmc());
    ScanCtx c = {cb, ud};
    platform_list_dirs(dir, scan_dir, &c);
}

bool link_launch(const char *app, const char *arg1, const char *arg2)
{
    const char *args[3] = {app, arg1, arg2};
    int n = 1 + (arg1 != NULL) + (arg1 && arg2);
    LOG("link: start %s%s%s%s%s", app, arg1 ? " " : "", arg1 ? arg1 : "", arg2 ? " " : "",
        arg2 ? arg2 : "");
    return platform_launch(n, args);
}

void link_take_args(int argc, char **argv)
{
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--continue"))
            link_continue = true;
        else if (!strcmp(argv[i], "--from") && i + 1 < argc)
            snprintf(link_from, sizeof(link_from), "%s", argv[++i]);
    }
}
