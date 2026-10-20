/* Wi-Fi receiver: lets `vn3ds-port --3ds <ip>` push games (and engine
 * updates) straight onto the SD card.
 *
 * Protocol (TCP, little-endian), one connection per transfer:
 *   client: "VN3D" u32 version(1) u32 file_count u64 total_bytes
 *   per file: u16 path_len, path (relative to the vn3ds root, '/'
 *             separated), u64 size, data
 *   server, after each file: u8 status (0 ok, 1 refused, 2 write error)
 *   server, at the end:      "DONE"
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

enum { ST_HEADER, ST_PATHLEN, ST_PATH, ST_SIZE, ST_DATA };

static int listen_fd = -1, conn_fd = -1;
static int state;
static u8 hdr[20];
static size_t got, need;
static char path[300];
static u16 path_len;
static u64 file_size, file_done;
static FILE *out;
static char tmp_path[400], final_path[400];

static void set_status(const char *fmt, const char *arg)
{
    snprintf(NET.message, sizeof(NET.message), fmt, arg ? arg : "");
}

static void close_conn(void)
{
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

bool net_start(int port)
{
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
    if (!strcmp(path, "vn3ds.3dsx")) {
        /* the engine lives beside its folder: sdmc:/3ds/vn3ds.3dsx */
        const char *slash = strrchr(E.root, '/');
        int n = slash ? (int)(slash - E.root) : (int)strlen(E.root);
        snprintf(final_path, sizeof(final_path), "%.*s/vn3ds.3dsx", n, E.root);
    } else
        snprintf(final_path, sizeof(final_path), "%s/%s", E.root, path);
    snprintf(tmp_path, sizeof(tmp_path), "%s.part", final_path);
    make_dirs(final_path);
    out = fopen(tmp_path, "wb");
    if (out)
        setvbuf(out, NULL, _IONBF, 0);   /* our own buffer does the batching */
    wlen = 0;
    write_failed = !out;
    snprintf(NET.current, sizeof(NET.current), "%s", path);
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
            if (!strcmp(path, "vn3ds.3dsx"))
                NET.engine_updated = true;
            else if (!strncmp(path, "games/", 6)) {
                const char *id = path + 6;
                size_t n = strcspn(id, "/");
                snprintf(NET.last_game, sizeof(NET.last_game), "%.*s", (int)n, id);
            }
        }
    } else {
        code = write_failed ? 2 : 1;
    }
    reply(code);
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
                if (memcmp(hdr, "VN3D", 4) != 0 || rd_u32(hdr + 4) != 1) {
                    set_status("Unknown sender (update vn3ds-port?)", NULL);
                    close_conn();
                    return;
                }
                NET.files_total = rd_u32(hdr + 8);
                memcpy(&NET.bytes_total, hdr + 12, 8);
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
            } else {
                memcpy(&file_size, hdr, 8);
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
            need = 8;
            break;
        }
        case ST_DATA: {
            u64 left = file_size - file_done;
            size_t take = (u64)n < left ? n : (size_t)left;
            write_data(p, take);
            file_done += take;
            NET.bytes_done += take;
            p += take;
            n -= take;
            if (file_done == file_size) {
                end_file();
                state = ST_PATHLEN;
                need = 2;
                if (NET.files_done + NET.refused >= NET.files_total) {
                    send(conn_fd, "DONE", 4, 0);
                    set_status("Done: %s", NET.last_game[0] ? NET.last_game : "vn3ds updated");
                    NET.receiving = false;
                    NET.completed++;
                }
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
    NET.files_done = NET.refused = 0;
    NET.bytes_done = 0;
    NET.last_game[0] = 0;
    set_status("Connected", NULL);
    rx_quit = false;
    rx_active = true;
#ifdef __3DS__
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    rx_thread = threadCreate(rx_main, NULL, 32 * 1024, prio > 0x18 ? prio - 1 : prio, -2, false);
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
