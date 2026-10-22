/* Web downloads of a game (Snapshot on first run); see fetch.h. A small
 * HTTP/1.0 client on its own thread: HTTP/1.0 so servers answer with a plain
 * body (no chunked encoding), Range requests to resume, redirects followed
 * while they stay on http://. */

#include "fetch.h"
#include "app.h"
#include "net.h"

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <poll.h>
#include <sys/stat.h>
#include <unistd.h>
#include <zlib.h>

#ifdef __3DS__
#include <3ds.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
static Thread thread;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sys/socket.h>
static pthread_t thread;
#endif

#ifndef MSG_NOSIGNAL
#define MSG_NOSIGNAL 0
#endif

#define TIMEOUT_MS 20000
#define MANIFEST_MAX (64 * 1024)
#define WBUF_SIZE (256 * 1024)   /* SD writes are slow one by one: write in big blocks */

FetchStatus FETCH;
const char *fetch_url_override;

static bool running, soc_held;
static volatile bool quit;
static char base_url[256];

typedef struct {
    char host[128], path[256];
    int port;
} Url;

static bool parse_url(const char *u, Url *out)
{
    memset(out, 0, sizeof(*out));
    if (strncmp(u, "http://", 7) != 0)
        return false;
    u += 7;
    size_t hl = strcspn(u, ":/");
    if (hl == 0 || hl >= sizeof(out->host))
        return false;
    memcpy(out->host, u, hl);
    u += hl;
    out->port = 80;
    if (*u == ':') {
        out->port = atoi(u + 1);
        u += 1 + strspn(u + 1, "0123456789");
    }
    if ((*u && *u != '/') || out->port <= 0 || out->port > 65535)
        return false;
    snprintf(out->path, sizeof(out->path), "%s", *u ? u : "/");
    return true;
}

static bool wait_fd(int fd, int events, u64 deadline)
{
    while (!quit && platform_ms() < deadline) {
        struct pollfd p = {fd, (short)events, 0};
        int r = poll(&p, 1, 100);
        if (r > 0)
            return true;
        if (r < 0 && errno != EINTR)
            return false;
    }
    return false;
}

static bool resolve(const char *host, struct in_addr *out)
{
    if (inet_pton(AF_INET, host, out) == 1)
        return true;
    struct addrinfo hints, *res = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(host, NULL, &hints, &res) != 0 || !res)
        return false;
    *out = ((struct sockaddr_in *)res->ai_addr)->sin_addr;
    freeaddrinfo(res);
    return true;
}

/* An open response: the body continues on fd after `extra` bytes already read. */
typedef struct {
    int fd, status;
    s64 length;    /* Content-Length, -1 if not given */
    u8 head[4096];
    size_t extra_at, extra_len;
} Resp;

static void fail(const char *msg)
{
    if (!FETCH.error[0])
        snprintf(FETCH.error, sizeof(FETCH.error), "%s", msg);
}

/* GET url (from byte `from` on). On success the headers are read and r->fd
 * is open on the body. Follows up to four http:// redirects. */
static bool get(const char *url_text, u64 from, Resp *r)
{
    char cur[300];
    snprintf(cur, sizeof(cur), "%s", url_text);
    for (int hop = 0; hop < 5; hop++) {
        Url u;
        if (!parse_url(cur, &u)) {
            fail(strncmp(cur, "https://", 8) ? "Bad download address" : "The server wants HTTPS");
            return false;
        }
        struct sockaddr_in sa;
        memset(&sa, 0, sizeof(sa));
        sa.sin_family = AF_INET;
        sa.sin_port = htons((u16)u.port);
        if (!resolve(u.host, &sa.sin_addr)) {
            fail("No internet connection (is Wi-Fi on?)");
            return false;
        }
        int fd = socket(AF_INET, SOCK_STREAM, 0);
        if (fd < 0) {
            fail("No network");
            return false;
        }
#ifdef SO_NOSIGPIPE
        int one = 1;
        setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &one, sizeof(one));
#endif
        fcntl(fd, F_SETFL, fcntl(fd, F_GETFL, 0) | O_NONBLOCK);
        u64 deadline = platform_ms() + TIMEOUT_MS;
        int soerr = 0;
        socklen_t sl = sizeof(soerr);
        if ((connect(fd, (struct sockaddr *)&sa, sizeof(sa)) < 0 && errno != EINPROGRESS &&
             errno != EWOULDBLOCK && errno != EAGAIN) ||
            !wait_fd(fd, POLLOUT, deadline) ||
            (getsockopt(fd, SOL_SOCKET, SO_ERROR, &soerr, &sl) == 0 && soerr != 0)) {
            close(fd);
            fail("Cannot reach the server");
            return false;
        }
        char req[700], range[64] = "";
        if (from)
            snprintf(range, sizeof(range), "Range: bytes=%llu-\r\n", (unsigned long long)from);
        snprintf(req, sizeof(req),
                 "GET %s HTTP/1.0\r\nHost: %s\r\nUser-Agent: vn3ds\r\nAccept-Encoding: identity\r\n%s\r\n",
                 u.path, u.host, range);
        size_t len = strlen(req), sent = 0;
        while (sent < len) {
            ssize_t n = wait_fd(fd, POLLOUT, deadline) ? send(fd, req + sent, len - sent, MSG_NOSIGNAL) : -1;
            if (n > 0)
                sent += (size_t)n;
            else if (n == 0 || (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR))
                break;
        }
        /* the headers */
        size_t got = 0;
        char *end = NULL;
        while (sent == len && got < sizeof(r->head) - 1 && wait_fd(fd, POLLIN, deadline)) {
            ssize_t n = recv(fd, (char *)r->head + got, sizeof(r->head) - 1 - got, 0);
            if (n > 0) {
                got += (size_t)n;
                r->head[got] = 0;
                if ((end = strstr((char *)r->head, "\r\n\r\n")))
                    break;
            } else if (n == 0 || (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)) {
                break;
            }
        }
        int code;
        if (!end || sscanf((char *)r->head, "HTTP/%*d.%*d %d", &code) != 1) {
            close(fd);
            fail("No answer from the server");
            return false;
        }
        *end = 0;
        r->fd = fd;
        r->status = code;
        r->length = -1;
        r->extra_at = (size_t)(end + 4 - (char *)r->head);
        r->extra_len = got - r->extra_at;
        char loc[300] = "";
        for (char *line = strstr((char *)r->head, "\r\n"); line; line = strstr(line + 2, "\r\n")) {
            char *v = line + 2;
            if (!strncasecmp(v, "Content-Length:", 15))
                r->length = strtoll(v + 15, NULL, 10);
            else if (!strncasecmp(v, "Location:", 9))
                snprintf(loc, sizeof(loc), "%.*s", (int)strcspn(v + 9 + strspn(v + 9, " "), "\r\n"),
                         v + 9 + strspn(v + 9, " "));
        }
        if ((code == 301 || code == 302 || code == 303 || code == 307 || code == 308) && loc[0]) {
            close(fd);
            if (loc[0] == '/') {   /* same server */
                char host[160];
                snprintf(host, sizeof(host), "%s:%d", u.host, u.port);
                snprintf(cur, sizeof(cur), "http://%s%s", host, loc);
            } else {
                snprintf(cur, sizeof(cur), "%s", loc);
            }
            continue;
        }
        if (code != 200 && code != 206) {
            close(fd);
            char msg[64];
            snprintf(msg, sizeof(msg), code == 404 ? "Not on the server yet (404)" : "Server error %d", code);
            fail(msg);
            return false;
        }
        return true;
    }
    fail("Too many redirects");
    return false;
}

/* Reads up to n body bytes; 0 at the end, -1 on error. */
static ssize_t body_read(Resp *r, u8 *buf, size_t n)
{
    if (r->extra_len) {
        size_t k = r->extra_len < n ? r->extra_len : n;
        memcpy(buf, r->head + r->extra_at, k);
        r->extra_at += k;
        r->extra_len -= k;
        return (ssize_t)k;
    }
    for (;;) {
        if (!wait_fd(r->fd, POLLIN, platform_ms() + TIMEOUT_MS))
            return -1;
        ssize_t got = recv(r->fd, (char *)buf, n, 0);
        if (got >= 0)
            return got;
        if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
            return -1;
    }
}

static void make_dirs(const char *full)
{
    char tmp[460];
    snprintf(tmp, sizeof(tmp), "%s", full);
    for (char *p = tmp + 1; *p; p++)
        if (*p == '/') {
            *p = 0;
            mkdir(tmp, 0777);
            *p = '/';
        }
}

static bool safe_name(const char *s, bool path)
{
    if (!*s || *s == '/' || *s == '.')
        return false;
    for (; *s; s++) {
        if (!(isalnum((unsigned char)*s) || *s == '-' || *s == '_' || *s == '.' || (path && *s == '/')))
            return false;
        if (s[0] == '.' && s[1] == '.')
            return false;
    }
    return true;
}

static u64 file_size(const char *p)
{
    struct stat st;
    return stat(p, &st) == 0 ? (u64)st.st_size : 0;
}

static u8 *wbuf;
static u8 rbuf[32 * 1024];

/* Downloads one file of the manifest into dir/rel (via .part). */
static bool fetch_file(const char *dir, const char *rel, u64 size, u32 crc)
{
    char full[460], part[470], url[600];
    snprintf(full, sizeof(full), "%s/%s", dir, rel);
    if (file_size(full) == size) {   /* already here (a finished file only ever has its real name) */
        NET.bytes_done += size;
        NET.bytes_skipped += size;
        return true;
    }
    snprintf(part, sizeof(part), "%s.part", full);
    make_dirs(full);
    /* pick up a broken download: what is on the card already counts */
    u64 have = file_size(part);
    uLong c = crc32(0, Z_NULL, 0);
    if (have > 0 && have < size) {
        FILE *f = fopen(part, "rb");
        size_t n;
        while (f && (n = fread(rbuf, 1, sizeof(rbuf), f)) > 0)
            c = crc32(c, rbuf, (uInt)n);
        if (f)
            fclose(f);
    } else {
        have = 0;
    }
    snprintf(url, sizeof(url), "%s/%s", base_url, rel);
    Resp r;
    if (!get(url, have, &r))
        return false;
    if (have && r.status != 206) {   /* no ranges here: from the start */
        have = 0;
        c = crc32(0, Z_NULL, 0);
    }
    FILE *f = fopen(part, have ? "ab" : "wb");
    if (!f) {
        close(r.fd);
        fail("Cannot write to the SD card");
        return false;
    }
    NET.bytes_done += have;
    NET.bytes_skipped += have;
    u64 done = have;
    size_t wlen = 0;
    bool ok = true;
    while (done < size && !quit) {
        ssize_t n = body_read(&r, rbuf, sizeof(rbuf));
        if (n <= 0) {
            ok = false;
            fail("The connection broke off");
            break;
        }
        if ((u64)n > size - done)
            n = (ssize_t)(size - done);
        c = crc32(c, rbuf, (uInt)n);
        memcpy(wbuf + wlen, rbuf, (size_t)n);
        wlen += (size_t)n;
        if (wlen > WBUF_SIZE - sizeof(rbuf)) {
            ok = fwrite(wbuf, 1, wlen, f) == wlen;
            wlen = 0;
            if (!ok) {
                fail("The SD card is full");
                break;
            }
        }
        done += (u64)n;
        NET.bytes_done += (u64)n;
    }
    if (wlen && fwrite(wbuf, 1, wlen, f) != wlen && ok) {
        ok = false;
        fail("The SD card is full");
    }
    fclose(f);
    close(r.fd);
    if (!ok || quit)
        return false;
    if ((u32)c != crc) {
        remove(part);
        fail("A file arrived damaged: try again");
        return false;
    }
    remove(full);
    if (rename(part, full) != 0) {
        fail("Cannot write to the SD card");
        return false;
    }
    return true;
}

static void run(void)
{
    /* the manifest */
    char url[300];
    snprintf(url, sizeof(url), "%s/manifest.txt", base_url);
    Resp r;
    char *mf = malloc(MANIFEST_MAX + 1);
    if (!mf || !get(url, 0, &r)) {
        free(mf);
        return;
    }
    size_t mlen = 0;
    ssize_t n;
    while (mlen < MANIFEST_MAX && (n = body_read(&r, (u8 *)mf + mlen, MANIFEST_MAX - mlen)) > 0)
        mlen += (size_t)n;
    close(r.fd);
    mf[mlen] = 0;
    char id[64];
    int ver = 0;
    if (sscanf(mf, "vn3ds-dl %d %63s", &ver, id) != 2 || ver != 1 || !safe_name(id, false)) {
        free(mf);
        fail("The server sent something unexpected");
        return;
    }
    /* count first, so the bar knows the whole size */
    u32 files = 0;
    u64 total = 0;
    for (char *p = strchr(mf, '\n'); p && p[1]; p = strchr(p + 1, '\n')) {
        unsigned long long sz;
        if (sscanf(p + 1, "%llu", &sz) == 1) {
            files++;
            total += sz;
        }
    }
    snprintf(NET.game, sizeof(NET.game), "%s", id);
    NET.files_total = files;
    NET.files_done = NET.refused = NET.skipped = 0;
    NET.bytes_total = total;
    NET.bytes_done = NET.bytes_skipped = 0;
    NET.staged = NET.engine_updated = false;
    NET.last_game[0] = 0;
    snprintf(NET.message, sizeof(NET.message), "Downloading %s", id);
    __sync_synchronize();
    NET.receiving = true;
    char dir[400];
    snprintf(dir, sizeof(dir), "%s/games/%s", E.root, id);
    bool ok = files > 0;
    for (char *p = strchr(mf, '\n'); ok && p && p[1] && !quit; p = strchr(p + 1, '\n')) {
        unsigned long long sz;
        unsigned crc;
        char rel[200];
        if (sscanf(p + 1, "%llu %x %199s", &sz, &crc, rel) != 3)
            continue;
        if (!safe_name(rel, true)) {
            fail("The server sent something unexpected");
            ok = false;
            break;
        }
        snprintf(NET.current, sizeof(NET.current), "%s", rel);
        ok = fetch_file(dir, rel, sz, crc);
        if (ok)
            NET.files_done++;
    }
    free(mf);
    if (ok && !quit) {
        snprintf(NET.last_game, sizeof(NET.last_game), "%s", id);
        snprintf(NET.message, sizeof(NET.message), "Done: %s", id);
        NET.completed++;
    }
    NET.receiving = false;
}

static void worker(void *arg)
{
    (void)arg;
    run();
    FETCH.failed = FETCH.error[0] != 0 && !quit;
    if (FETCH.failed)
        LOG("download: %s", FETCH.error);
    __sync_synchronize();
    FETCH.busy = false;
}

#ifndef __3DS__
static void *worker_host(void *arg)
{
    worker(arg);
    return NULL;
}
#endif

static void read_url(void)
{
    snprintf(base_url, sizeof(base_url), "%s", fetch_url_override ? fetch_url_override : SNAPSHOT_URL);
    char path[400], line[300];
    snprintf(path, sizeof(path), "%s/download.cfg", E.root);
    FILE *f = fopen(path, "r");
    while (f && fgets(line, sizeof(line), f)) {
        char v[256];
        if (sscanf(line, " snapshot = %255s", v) == 1)
            snprintf(base_url, sizeof(base_url), "%s", v);
    }
    if (f)
        fclose(f);
    size_t n = strlen(base_url);
    while (n > 0 && base_url[n - 1] == '/')
        base_url[--n] = 0;
}

static void join(void)
{
    if (!running)
        return;
#ifdef __3DS__
    threadJoin(thread, U64_MAX);
    threadFree(thread);
#else
    pthread_join(thread, NULL);
#endif
    running = false;
}

bool fetch_start(void)
{
    if (FETCH.busy || NET.receiving)
        return false;
    join();
    memset(&FETCH, 0, sizeof(FETCH));
    read_url();
    if (!wbuf && !(wbuf = malloc(WBUF_SIZE))) {
        FETCH.failed = true;
        fail("Not enough memory");
        return false;
    }
    if (!soc_held && !(soc_held = net_soc_acquire())) {
        FETCH.failed = true;
        fail("Wi-Fi is not available (is it switched on?)");
        return false;
    }
    quit = false;
    FETCH.busy = true;
#ifdef __3DS__
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    /* below the main thread, like the Wi-Fi receiver: the menus never stutter */
    thread = threadCreate(worker, NULL, 32 * 1024, prio < 0x3F ? prio + 1 : prio, -2, false);
    running = thread != NULL;
#else
    running = pthread_create(&thread, NULL, worker_host, NULL) == 0;
#endif
    if (!running) {
        FETCH.busy = false;
        FETCH.failed = true;
        fail("Cannot start the download");
    }
    return running;
}

void fetch_poll(void)
{
    if (FETCH.busy)
        return;
    join();
    free(wbuf);
    wbuf = NULL;
    if (soc_held)
        net_soc_release();
    soc_held = false;
}

void fetch_stop(void)
{
    quit = true;
    join();
    FETCH.busy = false;
    fetch_poll();
}
