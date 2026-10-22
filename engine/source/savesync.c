/* Save sync with a computer: the receiver's "VN3S" request (net.c hands the
 * connection over) and the nudges that tell the computer when to come.
 *
 * The computer (tools/vnpack/savesync.py, the Mac app's sync agent) does all
 * the deciding: which side changed, which is newer, converting between
 * vn3ds and Ren'Py saves. The 3DS only lists its saves and reads or writes
 * the ones it is asked for, so a request costs a few hundred bytes plus the
 * saves that actually changed (the Wi-Fi can be slow: 10-200 KB/s).
 *
 * Protocol (TCP, little-endian), on the receiver's port:
 *   client: "VN3S" u32 version(1) u32 udp_port u64 0
 *   server: "VN3S" u32 version u32 now (the 3DS clock) u32 count,
 *           count x {u16 len, path "saves/<id>/slotNN.sav", u32 size, u32 time}
 *           (time is the save's own, from its header; slots 0-30 only)
 *   then commands until 'Q':
 *     'G' u16 len path            -> u32 size (0xFFFFFFFF: none) + the file
 *     'P' u16 len path u32 size + data -> u8 status (0 ok, 1 refused, 2 failed);
 *                                  the file it replaces is kept as <path>.bak
 *     'D' u16 len path            -> u8 status; the file becomes <path>.bak
 *     'Q'                         -> "DONE"
 * After 'Q' the 3DS remembers the computer (sync.cfg: its address and
 * udp_port) and from then on sends it a UDP nudge, "VN3N" u32 reason
 * u32 unsynced, when vn3ds opens, after a save (at most every
 * NUDGE_GAP seconds), when a game is closed and when vn3ds exits. On exit,
 * with saves the computer hasn't had yet, vn3ds waits a few seconds for it.
 * vn3ds can't run while it's closed, so saves made then wait on the SD card
 * until the computer and vn3ds are both there. */

#include "app.h"
#include "net.h"

#include <dirent.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

#ifdef __3DS__
#include <3ds.h>
#endif
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>

#define SYNC_VERSION 1
#define MAX_SLOT 30
#define MAX_SAVE (4u << 20)
#define NUDGE_GAP 20000   /* ms between nudges for saves made while playing */
#define EXIT_WAIT 4000    /* ms vn3ds waits on exit for the computer to take its saves */

static char mac_host[64];
static u16 mac_port;
static bool cfg_read;
static volatile bool unsynced;          /* a save was written since the last sync */
static volatile u32 sessions;           /* completed sync sessions */
static volatile bool in_session;
static volatile bool cfg_dirty;         /* a session learnt a (new) computer */
static volatile bool saves_changed;     /* a session wrote or removed saves */
static u64 nudge_due;                   /* 0: none pending */
static u32 nudge_reason;

static void cfg_path(char *out, size_t len)
{
    snprintf(out, len, "%s/sync.cfg", E.root);
}

static void cfg_load(void)
{
    if (cfg_read)
        return;
    cfg_read = true;
    char path[320], line[128];
    cfg_path(path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (!f)
        return;
    while (fgets(line, sizeof(line), f)) {
        char host[64];
        unsigned port;
        if (sscanf(line, "host = %63s", host) == 1)
            snprintf(mac_host, sizeof(mac_host), "%s", host);
        else if (sscanf(line, "port = %u", &port) == 1)
            mac_port = (u16)port;
        else if (!strncmp(line, "unsynced = 1", 12))
            unsynced = true;
    }
    fclose(f);
}

/* Main thread only (the receiver thread just sets cfg_dirty). */
static void cfg_save(void)
{
    char path[320];
    cfg_path(path, sizeof(path));
    FILE *f = fopen(path, "w");
    if (!f)
        return;
    fprintf(f, "host = %s\nport = %u\nunsynced = %d\n", mac_host, (unsigned)mac_port,
            unsynced ? 1 : 0);
    fclose(f);
}

/* ---- the session (receiver thread, blocking socket) --------------------- */

static bool rx_all(int fd, void *p, size_t n)
{
    u8 *b = p;
    while (n > 0) {
        ssize_t r = recv(fd, (char *)b, n, 0);
        if (r > 0) {
            b += r;
            n -= (size_t)r;
        } else if (r < 0 && (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)) {
#ifdef __3DS__
            svcSleepThread(1000000LL);
#else
            usleep(1000);
#endif
        } else {
            return false;
        }
    }
    return true;
}

static bool tx_all(int fd, const void *p, size_t n)
{
    const u8 *b = p;
    while (n > 0) {
        ssize_t r = send(fd, (const char *)b, n, 0);
        if (r > 0) {
            b += r;
            n -= (size_t)r;
        } else if (r < 0 && (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)) {
#ifdef __3DS__
            svcSleepThread(1000000LL);
#else
            usleep(1000);
#endif
        } else {
            return false;
        }
    }
    return true;
}

/* A growing reply, sent in one go. */
typedef struct {
    u8 *p;
    size_t n, cap;
} Out;

static void put(Out *o, const void *p, size_t n)
{
    if (o->n + n > o->cap) {
        size_t cap = o->cap ? o->cap * 2 : 4096;
        while (cap < o->n + n)
            cap *= 2;
        u8 *g = realloc(o->p, cap);
        if (!g)
            return;
        o->p = g;
        o->cap = cap;
    }
    memcpy(o->p + o->n, p, n);
    o->n += n;
}

/* "saves/<id>/slotNN.sav", NN 00-30, id without '/' or "..". */
static bool sync_path_ok(const char *p)
{
    if (strncmp(p, "saves/", 6) != 0)
        return false;
    const char *id = p + 6, *slash = strchr(id, '/');
    if (!slash || slash == id || slash - id >= 64)
        return false;
    for (const char *c = id; c < slash; c++)
        if (!((*c >= 'a' && *c <= 'z') || (*c >= 'A' && *c <= 'Z') || (*c >= '0' && *c <= '9') ||
              *c == '-' || *c == '_' || (*c == '.' && c != id)))
            return false;
    if (strstr(id, ".."))
        return false;
    const char *f = slash + 1;   /* slotNN.sav */
    if (strlen(f) != 10 || strncmp(f, "slot", 4) != 0 || strcmp(f + 6, ".sav") != 0 ||
        f[4] < '0' || f[4] > '9' || f[5] < '0' || f[5] > '9')
        return false;
    return (f[4] - '0') * 10 + (f[5] - '0') <= MAX_SLOT;
}

static void list_game(Out *o, u32 *count, const char *id)
{
    for (int slot = 0; slot <= MAX_SLOT; slot++) {
        char rel[128], full[400];
        snprintf(rel, sizeof(rel), "saves/%s/slot%02d.sav", id, slot);
        if (!sync_path_ok(rel))
            return;
        snprintf(full, sizeof(full), "%s/%s", E.root, rel);
        struct stat st;
        if (stat(full, &st) != 0)
            continue;
        u8 head[16] = {0};
        FILE *f = fopen(full, "rb");
        if (!f)
            continue;
        size_t got = fread(head, 1, sizeof(head), f);
        fclose(f);
        u32 size = (u32)st.st_size, time = got == 16 && !memcmp(head, "VNSV", 4) ? rd_u32(head + 12) : 0;
        u16 len = (u16)strlen(rel);
        put(o, &len, 2);
        put(o, rel, len);
        put(o, &size, 4);
        put(o, &time, 4);
        (*count)++;
    }
}

static bool send_listing(int fd)
{
    Out o = {0};
    u32 version = SYNC_VERSION, now = platform_time(), count = 0;
    put(&o, "VN3S", 4);
    put(&o, &version, 4);
    put(&o, &now, 4);
    put(&o, &count, 4);
    char dir[320];
    snprintf(dir, sizeof(dir), "%s/saves", E.root);
    DIR *d = opendir(dir);
    struct dirent *e;
    while (d && (e = readdir(d)))
        if (e->d_name[0] != '.')
            list_game(&o, &count, e->d_name);
    if (d)
        closedir(d);
    bool ok = o.p && o.n >= 16;
    if (ok) {
        memcpy(o.p + 12, &count, 4);
        ok = tx_all(fd, o.p, o.n);
    }
    free(o.p);
    return ok;
}

static bool read_path(int fd, char *path, size_t cap)
{
    u16 len = 0;
    if (!rx_all(fd, &len, 2) || len == 0 || len >= cap)
        return false;
    if (!rx_all(fd, path, len))
        return false;
    path[len] = 0;
    return true;
}

static void make_dirs_for(const char *full)
{
    char d[400];
    snprintf(d, sizeof(d), "%s", full);
    for (char *c = d + 1; *c; c++)
        if (*c == '/') {
            *c = 0;
            platform_mkdir(d);
            *c = '/';
        }
}

static void keep_backup(const char *full)
{
    char bak[420];
    snprintf(bak, sizeof(bak), "%s.bak", full);
    remove(bak);
    rename(full, bak);
}

static bool do_get(int fd)
{
    char rel[300], full[400];
    if (!read_path(fd, rel, sizeof(rel)))
        return false;
    u32 none = 0xFFFFFFFF;
    if (!sync_path_ok(rel))
        return tx_all(fd, &none, 4);
    snprintf(full, sizeof(full), "%s/%s", E.root, rel);
    FILE *f = fopen(full, "rb");
    u8 *data = NULL;
    long size = -1;
    if (f && fseek(f, 0, SEEK_END) == 0 && (size = ftell(f)) >= 0 && size <= (long)MAX_SAVE &&
        fseek(f, 0, SEEK_SET) == 0 && (data = malloc(size ? (size_t)size : 1)) &&
        fread(data, 1, (size_t)size, f) == (size_t)size) {
        fclose(f);
        u32 n = (u32)size;
        bool ok = tx_all(fd, &n, 4) && tx_all(fd, data, n);
        free(data);
        return ok;
    }
    if (f)
        fclose(f);
    free(data);
    return tx_all(fd, &none, 4);
}

static bool do_put(int fd)
{
    char rel[300], full[400], part[420];
    u32 size = 0;
    if (!read_path(fd, rel, sizeof(rel)) || !rx_all(fd, &size, 4) || size > MAX_SAVE)
        return false;
    u8 *data = malloc(size ? size : 1);
    if (!data || !rx_all(fd, data, size)) {
        free(data);
        return false;
    }
    u8 status = 1;
    if (sync_path_ok(rel) && size >= 16 && !memcmp(data, "VNSV", 4)) {
        snprintf(full, sizeof(full), "%s/%s", E.root, rel);
        snprintf(part, sizeof(part), "%s.part", full);
        make_dirs_for(full);
        FILE *f = fopen(part, "wb");
        bool ok = f && fwrite(data, 1, size, f) == size;
        if (f)
            ok = fclose(f) == 0 && ok;
        if (ok) {
            keep_backup(full);
            ok = rename(part, full) == 0;
        } else {
            remove(part);
        }
        status = ok ? 0 : 2;
        if (ok) {
            saves_changed = true;
            LOG("sync: received %s", rel);
        }
    }
    free(data);
    return tx_all(fd, &status, 1);
}

static bool do_delete(int fd)
{
    char rel[300], full[400];
    if (!read_path(fd, rel, sizeof(rel)))
        return false;
    u8 status = 1;
    if (sync_path_ok(rel)) {
        snprintf(full, sizeof(full), "%s/%s", E.root, rel);
        struct stat st;
        status = stat(full, &st) == 0 ? 0 : 1;
        if (!status) {
            keep_backup(full);
            saves_changed = true;
        }
    }
    return tx_all(fd, &status, 1);
}

void sync_session(int fd, const u8 header[20])
{
    in_session = true;
    u16 port = (u16)rd_u32(header + 8);
    char before[sizeof(NET.message)];   /* (the receive screen's line comes back after) */
    snprintf(before, sizeof(before), "%s", NET.message);
    snprintf(NET.message, sizeof(NET.message), "Syncing saves...");
    bool ok = send_listing(fd);
    while (ok) {
        u8 cmd = 0;
        if (!rx_all(fd, &cmd, 1))
            break;
        if (cmd == 'G')
            ok = do_get(fd);
        else if (cmd == 'P')
            ok = do_put(fd);
        else if (cmd == 'D')
            ok = do_delete(fd);
        else if (cmd == 'Q') {
            struct sockaddr_in peer;
            socklen_t pl = sizeof(peer);
            if (getpeername(fd, (struct sockaddr *)&peer, &pl) == 0) {
                snprintf(mac_host, sizeof(mac_host), "%s", inet_ntoa(peer.sin_addr));
                if (port)
                    mac_port = port;
            }
            unsynced = false;
            cfg_dirty = true;
            sessions++;
            tx_all(fd, "DONE", 4);
            break;
        } else {
            break;
        }
    }
    snprintf(NET.message, sizeof(NET.message), "%s", before);
    in_session = false;
}

/* ---- nudges (main thread) ----------------------------------------------- */

static void send_nudge(u32 reason)
{
    cfg_load();
    if (!mac_host[0] || !mac_port || !NET.listening)
        return;
    int s = socket(AF_INET, SOCK_DGRAM, 0);
    if (s < 0)
        return;
    struct sockaddr_in to;
    memset(&to, 0, sizeof(to));
    to.sin_family = AF_INET;
    to.sin_port = htons(mac_port);
    to.sin_addr.s_addr = inet_addr(mac_host);
    u8 msg[76];
    u32 flag = unsynced ? 1 : 0;
    memcpy(msg, "VN3N", 4);
    memcpy(msg + 4, &reason, 4);
    memcpy(msg + 8, &flag, 4);
    snprintf((char *)msg + 12, 64, "%s", E.loaded ? E.game.id : "");
    sendto(s, (const char *)msg, sizeof(msg), 0, (struct sockaddr *)&to, sizeof(to));
    close(s);
    LOG("sync: nudged %s:%u (%u)", mac_host, (unsigned)mac_port, (unsigned)reason);
}

void sync_note_saved(int slot)
{
    if (slot < 0 || slot > MAX_SLOT)
        return;   /* (story points stay on the 3DS) */
    cfg_load();
    bool was = unsynced;
    unsynced = true;
    if (!was)
        cfg_dirty = true;   /* remembered across a restart: the computer still wants it */
    if (!nudge_due) {
        /* a slot the player picked goes soon; autosaves at most every NUDGE_GAP */
        nudge_due = platform_ms() + (slot == 0 ? NUDGE_GAP : 1500);
        nudge_reason = SYNC_SAVED;
    }
}

void sync_event(u32 reason)
{
    cfg_load();
    send_nudge(reason);
    nudge_due = 0;
    if (reason != SYNC_EXIT || !unsynced || !mac_host[0])
        return;
    /* give the computer a moment to take the new saves */
    u32 before = sessions;
    u64 until = platform_ms() + EXIT_WAIT;
    while (platform_ms() < until && (sessions == before || in_session)) {
        net_poll();
#ifdef __3DS__
        svcSleepThread(20000000LL);
#else
        usleep(20000);
#endif
    }
    if (cfg_dirty)
        cfg_save();
}

bool sync_poll(void)
{
    if (cfg_dirty && !in_session) {
        cfg_dirty = false;
        cfg_save();
    }
    if (nudge_due && platform_ms() >= nudge_due && !in_session) {
        nudge_due = 0;
        send_nudge(nudge_reason);
    }
    bool changed = saves_changed && !in_session;
    if (changed)
        saves_changed = false;
    return changed;
}

u32 sync_sessions(void) { return sessions; }
