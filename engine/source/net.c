/* Wi-Fi receiver: lets `vn3ds-port --3ds <ip>` push games (and engine
 * updates) straight onto the SD card.
 *
 * Protocol (TCP, little-endian), one connection per transfer:
 *   client: "VN3D" u32 version(1 or 2) u32 file_count u64 total_bytes
 *   per file: u16 path_len, path (relative to the vn3ds root, '/'
 *             separated), u64 size, [v2: u32 crc32], data
 *   server, after each file: u8 status (0 ok, 1 refused, 2 write error)
 *   server, at the end:      "DONE"
 * Version 2 lets updates skip what the card already has: after a file's
 * size and CRC the server answers 3 ("have it": no data follows, and that 3
 * is the file's status) or 4 ("send it": data follows, then the status).
 * Version 3 avoids a round trip per file, which on a slow Wi-Fi link costs
 * far more than the data: the client sends the whole manifest first (every
 * entry as in version 2: path, size, CRC), the server answers once with a
 * bitmap of the files it needs (bit i = entry i, LSB first), then the client
 * streams those files back to back as u32 index + data, with no replies in
 * between. At the end the server sends "DONE" u32 failed. A dropped
 * connection just means sending the manifest again: finished files are on
 * the card and get skipped, so transfers resume by themselves.
 *
 * Paths are restricted to games/<id>/... and the engine file itself, so a
 * client can't write anywhere else on the card. The main loop only accepts
 * connections; each transfer runs on its own thread with blocking recv()
 * calls, which is what makes the 3DS's network service deliver data at
 * full speed (polling a non-blocking socket once per frame managed ~20 KB/s).
 * The UI just reads the NET counters.
 *
 * File data is collected in a large buffer and written in big blocks: on the
 * 3DS every SD-card write is slow (it is flushed), so writing each network
 * packet on its own runs at a few KB/s. */

#include "app.h"
#include "net.h"

#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <zlib.h>

#ifdef __3DS__
#include <3ds.h>
#include <arpa/inet.h>
static Thread rx_thread;
#include <malloc.h>
#include <netinet/in.h>
#include <sys/socket.h>
#define SOC_ALIGN 0x1000
#define SOC_BUFFERSIZE 0x100000
static u32 *soc_buf;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sys/socket.h>
static pthread_t rx_thread;
#endif

static volatile bool rx_active, rx_quit;
static bool rx_started;
static void rx_join(void);

NetStatus NET;

#define WBUF_SIZE (512 * 1024)
static u8 *wbuf;
static size_t wlen;
static bool write_failed;
static void widen_window(int fd);

enum { ST_HEADER, ST_PATHLEN, ST_PATH, ST_SIZE, ST_DATA, ST_INDEX };

/* version 3: the manifest */
#define MF_MAX 40000
static char *mf_paths;     /* NUL-separated */
static u32 *mf_off, *mf_crc, mf_n, mf_bytes, mf_cap, mf_failed;
static u64 *mf_size;

static int listen_fd = -1, conn_fd = -1;
static int state;
static u8 hdr[20];
static size_t got, need;
static char path[300];
static u16 path_len;
static u64 file_size, file_done;
static u32 proto, file_crc;
/* Protocol 4: each file comes as raw bytes or a raw-deflate stream that is
 * unpacked as it arrives, and its CRC is checked before it is kept. */
static u8 file_method;          /* 0 raw, 1 deflate */
static u64 wire_left;           /* bytes of this file still to come */
static uLong out_crc;
static z_stream zs;
static bool zs_ready, zs_ended;
static void target_path(const char *rel, char *out, size_t len);
static void live_path(const char *rel, char *out, size_t len);
static FILE *out;
static char tmp_path[400], final_path[400];

static void set_status(const char *fmt, const char *arg)
{
    snprintf(NET.message, sizeof(NET.message), fmt, arg ? arg : "");
}

static void mf_free(void)
{
    free(mf_paths);
    free(mf_off);
    free(mf_crc);
    free(mf_size);
    mf_paths = NULL;
    mf_off = mf_crc = NULL;
    mf_size = NULL;
    mf_n = mf_bytes = mf_cap = mf_failed = 0;
}

static void inflate_stop(void);

static void close_conn(void)
{
    inflate_stop();
    mf_free();
    if (out) {
        fclose(out);
        out = NULL;
        remove(tmp_path);
    }
    if (conn_fd >= 0)
        close(conn_fd);
    conn_fd = -1;
}

/* The 3DS socket service, shared by the receiver and the leaderboard: it is
 * started by the first user and stopped when the last one lets go. Only
 * called from the main thread. */
static int soc_users;
static bool rx_soc;   /* net_start() holds a reference */

bool net_soc_acquire(void)
{
#ifdef __3DS__
    if (soc_users == 0) {
        soc_buf = memalign(SOC_ALIGN, SOC_BUFFERSIZE);
        if (!soc_buf || R_FAILED(socInit(soc_buf, SOC_BUFFERSIZE))) {
            free(soc_buf);
            soc_buf = NULL;
            return false;
        }
    }
#endif
    soc_users++;
    return true;
}

void net_soc_release(void)
{
    if (soc_users <= 0)
        return;
    soc_users--;
#ifdef __3DS__
    if (soc_users == 0 && soc_buf) {
        socExit();
        free(soc_buf);
        soc_buf = NULL;
    }
#endif
}

/* The game that is open right now: files for it are staged in
 * updates/<id>/ instead of overwriting what it is reading. */
static char live_game[64];
/* Odd while the main thread is changing live_game; the receiver thread
 * retries its copy until it reads the same even value before and after. */
static volatile u32 live_seq;

void net_set_live_game(const char *id)
{
    live_seq++;
    __sync_synchronize();
    snprintf(live_game, sizeof(live_game), "%s", id ? id : "");
    __sync_synchronize();
    live_seq++;
}

static void copy_live_game(char *out, size_t len)
{
    for (;;) {
        u32 seq = live_seq;
        __sync_synchronize();
        if (!(seq & 1)) {
            snprintf(out, len, "%s", live_game);
            __sync_synchronize();
            if (live_seq == seq)
                return;
        }
#ifdef __3DS__
        svcSleepThread(100000LL);
#else
        usleep(100);
#endif
    }
}

/* Remembers which game an incoming path belongs to (for the home screen). */
static void note_game(const char *rel)
{
    if (strncmp(rel, "games/", 6) != 0)
        return;
    const char *id = rel + 6;
    size_t n = strcspn(id, "/");
    if (n == 0 || n >= sizeof(NET.game) || (strlen(NET.game) == n && !strncmp(NET.game, id, n)))
        return;
    memcpy(NET.game, id, n);
    NET.game[n] = 0;
}

bool net_start(int port)
{
    if (listen_fd >= 0)
        return true;   /* already listening (in the background) */
    memset(&NET, 0, sizeof(NET));
    NET.port = port;
    if (!rx_soc) {
        if (!net_soc_acquire()) {
            set_status("Wi-Fi is not available (is it switched on?)", NULL);
            return false;
        }
        rx_soc = true;
    }
#ifdef __3DS__
    struct in_addr a = {(in_addr_t)gethostid()};
    snprintf(NET.address, sizeof(NET.address), "%s", inet_ntoa(a));
#else
    snprintf(NET.address, sizeof(NET.address), "127.0.0.1");
#endif
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) {
        set_status("cannot open a socket", NULL);
        return false;
    }
#ifndef __3DS__
    int yes = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
#endif
    widen_window(listen_fd);   /* before listen(), so the handshake advertises it */
    struct sockaddr_in sa;
    memset(&sa, 0, sizeof(sa));
    sa.sin_family = AF_INET;
    sa.sin_port = htons((u16)port);
    sa.sin_addr.s_addr = htonl(INADDR_ANY);
    if (bind(listen_fd, (struct sockaddr *)&sa, sizeof(sa)) < 0 || listen(listen_fd, 1) < 0) {
        set_status("cannot listen on the port", NULL);
        close(listen_fd);
        listen_fd = -1;
        return false;
    }
    fcntl(listen_fd, F_SETFL, fcntl(listen_fd, F_GETFL, 0) | O_NONBLOCK);
    NET.listening = true;
    set_status("Waiting for your computer...", NULL);
    return true;
}

void net_stop(void)
{
    if (rx_started) {
        rx_quit = true;
        if (conn_fd >= 0)
            shutdown(conn_fd, SHUT_RDWR);   /* wakes a blocked recv() */
        rx_join();
        rx_active = false;
    }
    close_conn();
    if (listen_fd >= 0)
        close(listen_fd);
    listen_fd = -1;
    NET.listening = false;
    if (rx_soc)
        net_soc_release();
    rx_soc = false;
}

static void reply(u8 code)
{
    if (conn_fd >= 0)
        send(conn_fd, (const char *)&code, 1, 0);
}

/* Only games/<id>/<file> (no "..", no absolute paths) and the engine itself. */
static bool path_allowed(const char *p)
{
    if (!strcmp(p, "vn3ds.3dsx"))
        return true;
    if (strncmp(p, "games/", 6) != 0 || strstr(p, "..") || strchr(p, '\\') || strchr(p, ':'))
        return false;
    return strlen(p) > 7;
}

static void make_dirs(const char *full)
{
    char d[400];
    snprintf(d, sizeof(d), "%s", full);
    for (char *c = d + 1; *c; c++) {
        if (*c == '/') {
            *c = 0;
            platform_mkdir(d);
            *c = '/';
        }
    }
}

static void begin_file(void)
{
    path[path_len] = 0;
    file_done = 0;
    write_failed = false;
    if (!path_allowed(path)) {
        LOG("net: refused path %s", path);
        out = NULL;
        NET.refused++;
        return;
    }
    note_game(path);
    target_path(path, final_path, sizeof(final_path));
    snprintf(tmp_path, sizeof(tmp_path), "%s.part", final_path);
    make_dirs(final_path);
    out = fopen(tmp_path, "wb");
    if (out)
        setvbuf(out, NULL, _IONBF, 0);   /* our own buffer does the batching */
    wlen = 0;
    write_failed = !out;
    snprintf(NET.current, sizeof(NET.current), "%s", path);
    LOG("net: receiving %s", path);
}

/* A large receive window: with the console's default one the sender can
 * only have a few KB in flight, and the 3DS's delayed ACKs then limit a
 * transfer to ~20 KB/s. (ftpd does the same.) */
static void widen_window(int fd)
{
    static const int sizes[] = {0x40000, 0x20000, 0x10000, 0x8000};
    for (unsigned i = 0; i < sizeof(sizes) / sizeof(sizes[0]); i++) {
        int v = sizes[i];
        if (setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &v, sizeof(v)) == 0) {
            LOG("net: receive window %d KB", v / 1024);
            return;
        }
    }
}

static void drop_file(void)
{
    write_failed = true;
    fclose(out);
    out = NULL;
    remove(tmp_path);
}

static bool flush_buf(void)
{
    if (out && wlen > 0 && fwrite(wbuf, 1, wlen, out) != wlen) {
        drop_file();
        wlen = 0;
        return false;
    }
    wlen = 0;
    return true;
}

static void write_data(const u8 *p, size_t n)
{
    if (!out)
        return;
    if (!wbuf && !(wbuf = malloc(WBUF_SIZE))) {
        if (fwrite(p, 1, n, out) != n)
            drop_file();
        return;
    }
    while (n > 0 && out) {
        size_t take = WBUF_SIZE - wlen < n ? WBUF_SIZE - wlen : n;
        memcpy(wbuf + wlen, p, take);
        wlen += take;
        p += take;
        n -= take;
        if (wlen == WBUF_SIZE)
            flush_buf();
    }
}

/* The Homebrew Launcher lists sdmc:/3ds/vn3ds.3dsx and, from older installs,
 * sdmc:/3ds/vn3ds/vn3ds.3dsx: when the engine updates, refresh both so it
 * doesn't matter which one is started. */
static void also_update_engine_copy(const char *fresh)
{
    char other[400];
    snprintf(other, sizeof(other), "%s/vn3ds.3dsx", E.root);
    struct stat st;
    if (!strcmp(other, fresh) || stat(other, &st) != 0)
        return;
    FILE *in = fopen(fresh, "rb"), *out_f = fopen(other, "wb");
    static u8 chunk[16 * 1024];
    size_t r;
    bool ok = in && out_f;
    while (ok && (r = fread(chunk, 1, sizeof(chunk), in)) > 0)
        ok = fwrite(chunk, 1, r, out_f) == r;
    if (in)
        fclose(in);
    if (out_f)
        fclose(out_f);
    LOG("net: %s %s too", ok ? "updated" : "could not update", other);
}

static void end_file(void)
{
    u8 code = 0;
    if (out)
        flush_buf();
    if (out) {
        bool ok = fclose(out) == 0;
        out = NULL;
        remove(final_path);
        ok = ok && rename(tmp_path, final_path) == 0;
        code = ok ? 0 : 2;
        if (ok) {
            NET.files_done++;
            if (!strcmp(path, "vn3ds.3dsx")) {
                NET.engine_updated = true;
                also_update_engine_copy(final_path);
            }
            else if (!strncmp(path, "games/", 6)) {
                const char *id = path + 6;
                size_t n = strcspn(id, "/");
                snprintf(NET.last_game, sizeof(NET.last_game), "%.*s", (int)n, id);
            }
        }
    } else {
        code = write_failed ? 2 : 1;
    }
    if (proto >= 3) {
        if (code)
            mf_failed++;
    } else {
        reply(code);
    }
}

/* After a complete protocol-3 transfer, each game in the manifest gets a
 * prune.flag: the next time it loads, files its game.bin no longer names are
 * deleted (packed files are named by their contents, so an update leaves the
 * old ones behind). For the game being played the flag is staged with the
 * rest of the update. */
static void flag_prune(void)
{
    if (proto < 3 || mf_failed || !mf_n)
        return;
    char last[64] = "", rel[128], full[400];
    for (u32 i = 0; i < mf_n; i++) {
        const char *p = mf_paths + mf_off[i];
        if (strncmp(p, "games/", 6) != 0)
            continue;
        size_t n = strcspn(p + 6, "/");
        if (!p[6 + n] || n >= sizeof(last) || (!strncmp(last, p + 6, n) && !last[n]))
            continue;
        snprintf(last, sizeof(last), "%.*s", (int)n, p + 6);
        snprintf(rel, sizeof(rel), "games/%s/prune.flag", last);
        target_path(rel, full, sizeof(full));
        make_dirs(full);
        FILE *f = fopen(full, "wb");
        if (f)
            fclose(f);
    }
}

static void finish_transfer(void)
{
    flag_prune();
    send(conn_fd, "DONE", 4, 0);
    if (proto >= 3)
        send(conn_fd, (const char *)&mf_failed, 4, 0);
    set_status("Done: %s", NET.last_game[0] ? NET.last_game : "vn3ds updated");
    NET.receiving = false;
    NET.completed++;
}

/* Where an incoming path ends up on the card. */
static void live_path(const char *rel, char *out, size_t len);

/* Where an incoming file is written: like live_path(), except that files of
 * the game being played go to updates/<id>/ until it is restarted. */
static void target_path(const char *rel, char *out, size_t len)
{
    char live[64];
    copy_live_game(live, sizeof(live));
    size_t n = strlen(live);
    if (n && !strncmp(rel, "games/", 6) && !strncmp(rel + 6, live, n) && rel[6 + n] == '/') {
        snprintf(out, len, "%s/updates/%s/%s", E.root, live, rel + 7 + n);
        NET.staged = true;
        return;
    }
    live_path(rel, out, len);
}

/* Where a file lives on the card. */
static void live_path(const char *rel, char *out, size_t len)
{
    if (!strcmp(rel, "vn3ds.3dsx")) {
        /* the engine lives beside its folder: sdmc:/3ds/vn3ds.3dsx */
        const char *slash = strrchr(E.root, '/');
        int n = slash ? (int)(slash - E.root) : (int)strlen(E.root);
        snprintf(out, len, "%.*s/vn3ds.3dsx", n, E.root);
    } else {
        snprintf(out, len, "%s/%s", E.root, rel);
    }
}

/* True if the card already holds this exact file (same size and CRC-32). */
static bool file_matches(const char *full)
{
    struct stat st;
    if (stat(full, &st) != 0 || (u64)st.st_size != file_size)
        return false;   /* missing or a different size: no need to read it */
    FILE *f = fopen(full, "rb");
    if (!f)
        return false;
    static u8 buf[32 * 1024];
    uLong crc = crc32(0L, Z_NULL, 0);
    u64 total = 0;
    size_t r;
    while ((r = fread(buf, 1, sizeof(buf), f)) > 0) {
        crc = crc32(crc, buf, (uInt)r);
        total += r;
    }
    fclose(f);
    return total == file_size && (u32)crc == file_crc;
}

static bool have_file(void)
{
    if (!path_allowed(path))
        return false;
    note_game(path);
    char live[400], target[400];
    live_path(path, live, sizeof(live));
    bool staged_before = NET.staged;
    target_path(path, target, sizeof(target));
    NET.staged = staged_before;   /* only asking where it would go */
    if (strcmp(live, target) != 0) {
        /* the game is open: an update for it may already be waiting */
        if (file_matches(target))
            return true;
        remove(target);   /* stale: it would overwrite the live file on the next load */
    }
    return file_matches(live);
}

/* Every file has arrived, been refused or failed (protocol 3+ counts
 * refusals among the failures). */
static bool all_files_in(void)
{
    return proto >= 3 ? NET.files_done + mf_failed >= NET.files_total
                      : NET.files_done + NET.refused >= NET.files_total;
}

static void inflate_stop(void)
{
    if (zs_ready)
        inflateEnd(&zs);
    zs_ready = false;
}

static bool inflate_start(void)
{
    inflate_stop();
    memset(&zs, 0, sizeof(zs));
    zs_ended = false;
    zs_ready = inflateInit2(&zs, -15) == Z_OK;
    return zs_ready;
}

static void keep(const u8 *p, size_t n)
{
    if (file_done + n > file_size) {   /* more than the manifest said: damaged */
        write_failed = true;
        n = (size_t)(file_size - file_done);
    }
    out_crc = crc32(out_crc, p, (uInt)n);
    write_data(p, n);
    file_done += n;
    NET.bytes_done += n;
}

/* Protocol 4 file data: raw, or deflate unpacked as it arrives. */
static bool data_v4(const u8 *p, size_t n)
{
    if (file_method == 0) {
        keep(p, n);
        return true;
    }
    static u8 inflated[32 * 1024];
    zs.next_in = (Bytef *)p;
    zs.avail_in = (uInt)n;
    while (zs.avail_in > 0 && !zs_ended) {
        zs.next_out = inflated;
        zs.avail_out = sizeof(inflated);
        int r = inflate(&zs, Z_NO_FLUSH);
        keep(inflated, sizeof(inflated) - zs.avail_out);
        if (r == Z_STREAM_END)
            zs_ended = true;
        else if (r != Z_OK && r != Z_BUF_ERROR)
            return false;   /* not deflate: the stream can't be trusted any more */
        else if (r == Z_BUF_ERROR && zs.avail_out != 0)
            break;
    }
    /* output still waiting inside zlib once all input is in */
    while (!zs_ended) {
        zs.next_out = inflated;
        zs.avail_out = sizeof(inflated);
        int r = inflate(&zs, Z_NO_FLUSH);
        size_t got = sizeof(inflated) - zs.avail_out;
        keep(inflated, got);
        if (r == Z_STREAM_END)
            zs_ended = true;
        if (got == 0 || (r != Z_OK && r != Z_STREAM_END))
            break;
    }
    return true;
}

/* "VN3L": sends log.old.txt and log.txt (the last run's and this one's). */
static void send_logs(void)
{
    static const char *names[] = {"log.old.txt", "log.txt"};
    static u8 chunk[4096];
    for (int i = 0; i < 2; i++) {
        char full[400];
        snprintf(full, sizeof(full), "%s/%s", E.root, names[i]);
        int n = snprintf((char *)chunk, sizeof(chunk), "==== %s ====\n", names[i]);
        send(conn_fd, (const char *)chunk, n, 0);
        FILE *f = fopen(full, "rb");
        if (!f)
            continue;
        size_t r;
        while ((r = fread(chunk, 1, sizeof(chunk), f)) > 0)
            send(conn_fd, (const char *)chunk, r, 0);
        fclose(f);
    }
}

/* Has the computer hung up? (Checked during the long comparison, which
 * otherwise only notices when its answer can't be sent.) */
static bool sender_gone(void)
{
    char c;
    ssize_t r = recv(conn_fd, &c, 1, MSG_PEEK | MSG_DONTWAIT);
    return r == 0 || (r < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR);
}

static void feed(const u8 *p, size_t n)
{
    while (n > 0) {
        switch (state) {
        case ST_HEADER:
        case ST_PATHLEN:
        case ST_SIZE: {
            size_t take = need - got < n ? need - got : n;
            memcpy(hdr + got, p, take);
            got += take;
            p += take;
            n -= take;
            if (got < need)
                return;
            got = 0;
            if (state == ST_HEADER) {
                if (memcmp(hdr, "VN3L", 4) == 0) {   /* a computer asks for the logs */
                    send_logs();
                    close_conn();
                    return;
                }
                proto = rd_u32(hdr + 4);
                if (memcmp(hdr, "VN3D", 4) != 0 || proto < 1 || proto > 4) {
                    set_status("Unknown sender (update vn3ds-port?)", NULL);
                    close_conn();
                    return;
                }
                NET.files_total = rd_u32(hdr + 8);
                memcpy(&NET.bytes_total, hdr + 12, 8);
                if (proto >= 3) {
                    mf_free();
                    mf_cap = 64 * 1024;
                    if (NET.files_total > MF_MAX || !(mf_paths = malloc(mf_cap)) ||
                        !(mf_off = malloc(4 * (NET.files_total + 1))) ||
                        !(mf_crc = malloc(4 * (NET.files_total + 1))) ||
                        !(mf_size = malloc(8 * (NET.files_total + 1)))) {
                        set_status("Too many files for one transfer", NULL);
                        close_conn();
                        return;
                    }
                    if (NET.files_total == 0) {
                        finish_transfer();
                        close_conn();
                        return;
                    }
                }
                state = ST_PATHLEN;
                need = 2;
                NET.receiving = true;
                set_status("Receiving...", NULL);
            } else if (state == ST_PATHLEN) {
                path_len = rd_u16(hdr);
                if (path_len == 0 || path_len >= sizeof(path)) {
                    close_conn();
                    return;
                }
                state = ST_PATH;
                need = path_len;
            } else if (proto >= 3) {
                /* one manifest entry */
                if (mf_bytes + path_len + 1 > mf_cap) {
                    char *grown = realloc(mf_paths, mf_cap * 2 + path_len + 1);
                    if (!grown) {
                        close_conn();
                        return;
                    }
                    mf_paths = grown;
                    mf_cap = mf_cap * 2 + path_len + 1;
                }
                memcpy(mf_paths + mf_bytes, path, path_len);
                mf_paths[mf_bytes + path_len] = 0;
                mf_off[mf_n] = mf_bytes;
                mf_bytes += path_len + 1;
                memcpy(&mf_size[mf_n], hdr, 8);
                mf_crc[mf_n] = rd_u32(hdr + 8);
                if (++mf_n < NET.files_total) {
                    state = ST_PATHLEN;
                    need = 2;
                    break;
                }
                /* the whole list is here: answer with what we still need */
                u32 nb = (mf_n + 7) / 8, needed = 0;
                u8 *bits = calloc(1, nb);
                if (!bits) {
                    close_conn();
                    return;
                }
                for (u32 i = 0; i < mf_n; i++) {
                    snprintf(path, sizeof(path), "%s", mf_paths + mf_off[i]);
                    path_len = (u16)strlen(path);
                    file_size = mf_size[i];
                    file_crc = mf_crc[i];
                    if (have_file()) {
                        NET.files_done++;
                        NET.skipped++;
                        NET.bytes_done += file_size;
                        NET.bytes_skipped += file_size;
                    } else {
                        bits[i >> 3] |= (u8)(1u << (i & 7));
                        needed++;
                    }
                    if ((i & 15) == 15 && sender_gone()) {   /* nobody waits for the answer */
                        free(bits);
                        set_status("Connection lost while comparing", NULL);
                        NET.receiving = false;
                        close_conn();
                        return;
                    }
                    if ((i & 63) == 0) {
                        char m[64];
                        snprintf(m, sizeof(m), "%u of %u", (unsigned)i, (unsigned)mf_n);
                        set_status("Comparing with the card: %s", m);
                    }
                }
                send(conn_fd, (const char *)bits, nb, 0);
                free(bits);
                set_status("Receiving...", NULL);
                if (needed == 0) {
                    finish_transfer();
                    return;
                }
                state = ST_INDEX;
                need = proto >= 4 ? 13 : 4;
                break;
            } else {
                memcpy(&file_size, hdr, 8);
                if (proto == 2) {
                    file_crc = rd_u32(hdr + 8);
                    path[path_len] = 0;
                    if (have_file()) {   /* identical file already on the card */
                        reply(3);
                        NET.files_done++;
                        NET.skipped++;
                        NET.bytes_done += file_size;
                        NET.bytes_skipped += file_size;
                        state = ST_PATHLEN;
                        need = 2;
                        if (all_files_in())
                            finish_transfer();
                        break;
                    }
                    reply(4);
                }
                begin_file();
                state = ST_DATA;
                if (file_size == 0) {
                    end_file();
                    state = ST_PATHLEN;
                    need = 2;
                }
            }
            break;
        }
        case ST_PATH: {
            size_t take = need - got < n ? need - got : n;
            memcpy(path + got, p, take);
            got += take;
            p += take;
            n -= take;
            if (got < need)
                return;
            got = 0;
            state = ST_SIZE;
            need = proto >= 2 ? 12 : 8;
            break;
        }
        case ST_DATA: {
            if (proto >= 4) {
                size_t take = (u64)n < wire_left ? n : (size_t)wire_left;
                if (!data_v4(p, take)) {
                    close_conn();
                    return;
                }
                wire_left -= take;
                p += take;
                n -= take;
                if (wire_left > 0)
                    break;
                bool whole = file_method == 0 || zs_ended;
                inflate_stop();
                if (!whole || file_done != file_size || out_crc != file_crc) {
                    LOG("net: %s arrived damaged", path);
                    if (out)
                        drop_file();
                }
            } else {
                u64 left = file_size - file_done;
                size_t take = (u64)n < left ? n : (size_t)left;
                write_data(p, take);
                file_done += take;
                NET.bytes_done += take;
                p += take;
                n -= take;
                if (file_done != file_size)
                    break;
            }
            end_file();
            state = proto >= 3 ? ST_INDEX : ST_PATHLEN;
            need = proto >= 4 ? 13 : proto >= 3 ? 4 : 2;
            if (all_files_in())
                finish_transfer();
            break;
        }
        case ST_INDEX: {   /* version 3: which manifest entry comes next */
            size_t take = need - got < n ? need - got : n;
            memcpy(hdr + got, p, take);
            got += take;
            p += take;
            n -= take;
            if (got < need)
                return;
            got = 0;
            u32 idx = rd_u32(hdr);
            if (idx >= mf_n) {
                close_conn();
                return;
            }
            snprintf(path, sizeof(path), "%s", mf_paths + mf_off[idx]);
            path_len = (u16)strlen(path);
            file_size = mf_size[idx];
            file_crc = mf_crc[idx];
            begin_file();
            state = ST_DATA;
            if (proto >= 4) {
                file_method = hdr[4];
                memcpy(&wire_left, hdr + 5, 8);
                out_crc = crc32(0L, Z_NULL, 0);
                if (file_method > 1 || (file_method == 1 && !inflate_start())) {
                    close_conn();
                    return;
                }
            }
            if (proto >= 4 ? wire_left == 0 && file_size == 0 : file_size == 0) {
                end_file();
                state = ST_INDEX;
                need = proto >= 4 ? 13 : 4;
                if (all_files_in())
                    finish_transfer();
            }
            break;
        }
        }
    }
}

static void rx_main(void *arg)
{
    (void)arg;
    static u8 buf[64 * 1024];
    while (conn_fd >= 0 && !rx_quit) {
        ssize_t r = recv(conn_fd, (char *)buf, sizeof(buf), 0);
        if (r > 0) {
            feed(buf, (size_t)r);
            continue;
        }
        if (r < 0 && (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)) {
#ifdef __3DS__
            svcSleepThread(1000000LL);
#else
            usleep(1000);
#endif
            continue;
        }
        /* 0: the sender finished (or went away); <0: the connection broke */
        if (NET.receiving)
            set_status("Connection lost during %s", NET.current);
        NET.receiving = false;
        close_conn();
    }
    rx_active = false;
}

#ifndef __3DS__
static void *rx_main_host(void *arg)
{
    rx_main(arg);
    return NULL;
}
#endif

static void rx_join(void)
{
    if (!rx_started)
        return;
#ifdef __3DS__
    threadJoin(rx_thread, U64_MAX);
    threadFree(rx_thread);
#else
    pthread_join(rx_thread, NULL);
#endif
    rx_started = false;
}

void net_poll(void)
{
    if (listen_fd < 0 || rx_active)
        return;   /* the receiver thread owns the connection */
    rx_join();
    struct sockaddr_in ca;
    socklen_t cl = sizeof(ca);
    int fd = accept(listen_fd, (struct sockaddr *)&ca, &cl);
    if (fd < 0)
        return;
    conn_fd = fd;
    widen_window(conn_fd);
    fcntl(conn_fd, F_SETFL, fcntl(conn_fd, F_GETFL, 0) & ~O_NONBLOCK);
    state = ST_HEADER;
    got = 0;
    need = 20;
    NET.files_done = NET.refused = NET.skipped = 0;
    NET.staged = false;
    NET.bytes_done = NET.bytes_skipped = 0;
    NET.last_game[0] = NET.game[0] = 0;
    set_status("Connected", NULL);
    rx_quit = false;
    rx_active = true;
#ifdef __3DS__
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    /* below the main thread, so a transfer while someone plays never costs a frame:
     * the main thread waits for the screen every frame, and the receiver runs then */
    rx_thread = threadCreate(rx_main, NULL, 96 * 1024, prio < 0x3F ? prio + 1 : prio, -2, false);
    rx_started = rx_thread != NULL;
#else
    rx_started = pthread_create(&rx_thread, NULL, rx_main_host, NULL) == 0;
#endif
    if (!rx_started) {
        rx_active = false;
        set_status("cannot start the receiver", NULL);
        close_conn();
    }
}
