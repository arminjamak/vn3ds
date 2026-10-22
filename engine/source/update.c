/* Self-update from the newest release; see update.h. The network part runs
 * on its own thread with the receiver's rules (non-blocking sockets, poll()
 * with no timeout and a millisecond's nap), so nothing waits on the main
 * thread or holds up the 3DS's one socket service. */

#include "update.h"
#include "app.h"
#include "fetch.h"
#include "net.h"
#include "sha256.h"

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <poll.h>
#include <sys/stat.h>
#include <unistd.h>

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

#define START_DELAY_MS 8000           /* let vn3ds settle first */
#define EVERY_S (6 * 3600)
#define TIMEOUT_MS 20000

UpdateStatus UPDATE;
const char *update_version_override;

static bool running, started, checked, disabled, soc_held;
static volatile bool quit, finished;
static u64 start_at;
static char base[160];

static void nap(void)
{
#ifdef __3DS__
    svcSleepThread(1000000LL);
#else
    usleep(1000);
#endif
}

static const char *current(void) { return update_version_override ? update_version_override : VN3DS_VERSION; }

int update_compare(const char *a, const char *b)
{
    int va[3] = {0}, vb[3] = {0};
    if (*a == 'v')
        a++;
    if (*b == 'v')
        b++;
    if (!isdigit((unsigned char)*a) || !isdigit((unsigned char)*b))
        return -1;
    sscanf(a, "%d.%d.%d", &va[0], &va[1], &va[2]);
    sscanf(b, "%d.%d.%d", &vb[0], &vb[1], &vb[2]);
    for (int i = 0; i < 3; i++)
        if (va[i] != vb[i])
            return va[i] > vb[i] ? 1 : 0;
    return 0;
}

static void fail(const char *why)
{
    snprintf(UPDATE.error, sizeof(UPDATE.error), "%s", why);
    UPDATE.state = UPD_FAILED;
    LOG("update: %s", why);
}

/* ---- a small HTTP/1.0 GET ---- */

typedef struct {
    char host[128], path[256];
    int port;
} Url;

static bool parse_url(const char *u, Url *out)
{
    memset(out, 0, sizeof(*out));
    if (strncmp(u, "http://", 7))
        return false;
    u += 7;
    size_t hl = strcspn(u, ":/");
    if (!hl || hl >= sizeof(out->host))
        return false;
    memcpy(out->host, u, hl);
    u += hl;
    out->port = 80;
    if (*u == ':') {
        out->port = atoi(u + 1);
        u += 1 + strspn(u + 1, "0123456789");
    }
    snprintf(out->path, sizeof(out->path), "%s", *u ? u : "/");
    return out->port > 0 && out->port < 65536;
}

/* Waits for fd to be ready for events; false on timeout, error or quit. */
static bool ready(int fd, short events, u64 deadline)
{
    while (!quit && platform_ms() < deadline) {
        struct pollfd p = {fd, events, 0};
        int r = poll(&p, 1, 0);
        if (r > 0)
            return true;
        if (r < 0 && errno != EINTR)
            return false;
        nap();
    }
    return false;
}

/* Opens url (from byte `from`), reads the headers. Returns the socket with
 * *status and *length (of what follows) set, or -1. */
static int http_open(const char *url, u64 from, int *status, s64 *length)
{
    Url u;
    if (!parse_url(url, &u))
        return -1;
    struct sockaddr_in sa;
    memset(&sa, 0, sizeof(sa));
    sa.sin_family = AF_INET;
    sa.sin_port = htons((u16)u.port);
    if (inet_pton(AF_INET, u.host, &sa.sin_addr) != 1) {
        struct addrinfo hints, *res = NULL;
        memset(&hints, 0, sizeof(hints));
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;
        if (getaddrinfo(u.host, NULL, &hints, &res) || !res)
            return -1;
        sa.sin_addr = ((struct sockaddr_in *)res->ai_addr)->sin_addr;
        freeaddrinfo(res);
    }
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0)
        return -1;
#ifdef SO_NOSIGPIPE
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &one, sizeof(one));
#endif
    net_tune_socket(fd);
    fcntl(fd, F_SETFL, fcntl(fd, F_GETFL, 0) | O_NONBLOCK);
    u64 deadline = platform_ms() + TIMEOUT_MS;
    if (connect(fd, (struct sockaddr *)&sa, sizeof(sa)) < 0 && errno != EINPROGRESS && errno != EWOULDBLOCK)
        goto bad;
    if (!ready(fd, POLLOUT, deadline))
        goto bad;
    int err = 0;
    socklen_t el = sizeof(err);
    if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &el) < 0 || err)
        goto bad;
    char req[512];
    int n = snprintf(req, sizeof(req), "GET %s HTTP/1.0\r\nHost: %s\r\nUser-Agent: vn3ds/%s\r\n", u.path, u.host,
                     current());
    if (from)
        n += snprintf(req + n, sizeof(req) - n, "Range: bytes=%llu-\r\n", (unsigned long long)from);
    n += snprintf(req + n, sizeof(req) - n, "\r\n");
    for (int sent = 0; sent < n;) {
        ssize_t r = send(fd, req + sent, (size_t)(n - sent), MSG_NOSIGNAL);
        if (r > 0)
            sent += (int)r;
        else if (r < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
            goto bad;
        else if (!ready(fd, POLLOUT, deadline))
            goto bad;
    }
    char h[2048];
    size_t got = 0;   /* the headers, a byte at a time: the body stays in the socket */
    while (got < sizeof(h) - 1 && !(got >= 4 && !memcmp(h + got - 4, "\r\n\r\n", 4))) {
        ssize_t r = recv(fd, h + got, 1, 0);
        if (r == 1)
            got++;
        else if (r == 0 || (r < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR))
            goto bad;
        else if (!ready(fd, POLLIN, deadline))
            goto bad;
    }
    h[got] = 0;
    *status = 0;
    sscanf(h, "HTTP/%*s %d", status);
    *length = -1;
    for (char *p = h; (p = strchr(p, '\n')); p++)
        if (!strncasecmp(p + 1, "Content-Length:", 15))
            *length = strtoll(p + 16, NULL, 10);
    return fd;
bad:
    close(fd);
    return -1;
}

/* Reads up to n bytes; 0 at the end, -1 on trouble. */
static ssize_t http_read(int fd, void *buf, size_t n)
{
    u64 deadline = platform_ms() + TIMEOUT_MS;
    for (;;) {
        ssize_t r = recv(fd, buf, n, 0);
        if (r >= 0)
            return r;
        if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
            return -1;
        if (!ready(fd, POLLIN, deadline))
            return -1;
    }
}

/* ---- the update ---- */

static bool sha256_file(const char *path, char hex[65])
{
    FILE *f = fopen(path, "rb");
    if (!f)
        return false;
    static u8 buf[64 * 1024];
    Sha256 s;
    sha256_init(&s);
    size_t r;
    while ((r = fread(buf, 1, sizeof(buf), f)) > 0)
        sha256_update(&s, buf, r);
    fclose(f);
    u8 d[32];
    sha256_final(&s, d);
    for (int i = 0; i < 32; i++)
        snprintf(hex + i * 2, 3, "%02x", d[i]);
    return true;
}

/* Downloads url to path (resuming a .part), checking size and SHA-256. */
static bool download(const char *url, const char *path, u64 size, const char *sha)
{
    char part[420];
    snprintf(part, sizeof(part), "%s.part", path);
    struct stat st;
    u64 have = stat(part, &st) == 0 ? (u64)st.st_size : 0;
    if (have > size)
        have = 0;
    UPDATE.total = size;
    for (int attempt = 0; have < size && attempt < 5 && !quit; attempt++) {
        int status;
        s64 len;
        int fd = http_open(url, have, &status, &len);
        if (fd < 0)
            continue;
        if (status == 200)
            have = 0;   /* the server ignored the range: from the start */
        else if (status != 206) {
            close(fd);
            fail("the download link answered with an error");
            return false;
        }
        FILE *f = fopen(part, have ? "ab" : "wb");
        if (!f) {
            close(fd);
            fail("can't write to the SD card");
            return false;
        }
        static u8 buf[64 * 1024];
        ssize_t r;
        while (!quit && (r = http_read(fd, buf, sizeof(buf))) > 0) {
            if (fwrite(buf, 1, (size_t)r, f) != (size_t)r)
                break;
            have += (u64)r;
            UPDATE.done = have;
        }
        fclose(f);
        close(fd);
    }
    if (have != size) {
        if (!UPDATE.error[0])
            fail("the download stopped (it carries on next time)");
        return false;
    }
    char hex[65];
    if (!sha256_file(part, hex) || strcasecmp(hex, sha)) {
        remove(part);
        fail("the download was damaged (it starts again next time)");
        return false;
    }
    remove(path);
    return rename(part, path) == 0;
}

#ifdef __3DS__
/* Installs a .cia over this title, as FBI does (the AM service). */
static bool install_cia(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f)
        return false;
    bool ok = false;
    Handle h;
    if (R_SUCCEEDED(amInit())) {
        if (R_SUCCEEDED(AM_StartCiaInstall(MEDIATYPE_SD, &h))) {
            static u8 buf[128 * 1024];
            u64 off = 0;
            size_t r;
            ok = true;
            while (ok && (r = fread(buf, 1, sizeof(buf), f)) > 0) {
                u32 w = 0;
                ok = R_SUCCEEDED(FSFILE_Write(h, &w, off, buf, (u32)r, 0)) && w == r;
                off += r;
            }
            if (ok)
                ok = R_SUCCEEDED(AM_FinishCiaInstall(h));
            else
                AM_CancelCIAInstall(h);
        }
        amExit();
    }
    fclose(f);
    return ok;
}
#endif

static void run(void *arg)
{
    (void)arg;
    char url[220];
    snprintf(url, sizeof(url), "%s/latest", base);
    int status;
    s64 len;
    int fd = http_open(url, 0, &status, &len);
    if (fd < 0 || status != 200) {
        if (fd >= 0)
            close(fd);
        UPDATE.state = UPD_IDLE;   /* offline: quietly try again another time */
        finished = true;
        return;
    }
    char body[1024];
    size_t got = 0;
    ssize_t r;
    while (got < sizeof(body) - 1 && (r = http_read(fd, body + got, sizeof(body) - 1 - got)) > 0)
        got += (size_t)r;
    close(fd);
    body[got] = 0;
    char tag[24] = "", sha3[65] = "", shac[65] = "";
    unsigned long long size3 = 0, sizec = 0;
    if (sscanf(body, "vn3ds-latest 1 %23s", tag) != 1) {
        UPDATE.state = UPD_IDLE;
        finished = true;
        return;
    }
    char *p = strstr(body, "\n3dsx ");
    if (p)
        sscanf(p, "\n3dsx %llu %64s", &size3, sha3);
    p = strstr(body, "\ncia ");
    if (p)
        sscanf(p, "\ncia %llu %64s", &sizec, shac);
    snprintf(UPDATE.latest, sizeof(UPDATE.latest), "%s", tag);
    if (update_compare(tag, current()) != 1) {
        UPDATE.state = UPD_IDLE;   /* up to date */
        finished = true;
        return;
    }
#ifdef __3DS__
    bool as_title = !envIsHomebrew();
#else
    bool as_title = false;
#endif
    const char *self = platform_self_path();
    if (!as_title && (!self || !self[0] || !size3)) {
        UPDATE.state = UPD_IDLE;   /* (no .3dsx to replace, or none in the release) */
        finished = true;
        return;
    }
    if (as_title && !sizec) {
        UPDATE.state = UPD_IDLE;
        finished = true;
        return;
    }
    LOG("update: %s -> %s (%s)", current(), tag, as_title ? "cia" : "3dsx");
    UPDATE.state = UPD_DOWNLOADING;
    char file[400];
    snprintf(file, sizeof(file), "%s/update-%s.%s", E.root, tag, as_title ? "cia" : "3dsx");
    snprintf(url, sizeof(url), "%s/vn3ds.%s", base, as_title ? "cia" : "3dsx");
    if (!download(url, file, as_title ? sizec : size3, as_title ? shac : sha3)) {
        finished = true;
        return;
    }
    UPDATE.state = UPD_INSTALLING;
    bool ok;
#ifdef __3DS__
    if (as_title) {
        ok = install_cia(file);
        remove(file);
    } else
#endif
    {
        char old[420];   /* the running copy moves aside first, then is deleted */
        snprintf(old, sizeof(old), "%s.old", self);
        remove(old);
        ok = rename(self, old) == 0 && rename(file, self) == 0;
        if (ok)
            remove(old);
        else
            rename(old, self);
    }
    if (ok)
        UPDATE.state = UPD_DONE;
    else
        fail("couldn't install the update");
    finished = true;
}

#ifndef __3DS__
static void *run_host(void *arg)
{
    run(arg);
    return NULL;
}
#endif

static void load_cfg(void)
{
    snprintf(base, sizeof(base), "%s", UPDATE_URL);
    char path[400], line[300];
    snprintf(path, sizeof(path), "%s/update.cfg", E.root);
    FILE *f = fopen(path, "rb");
    if (!f)
        return;
    while (fgets(line, sizeof(line), f)) {
        char k[32], v[200] = "";
        if (sscanf(line, " %31[a-z] = %199s", k, v) < 1)
            continue;
        if (!strcmp(k, "auto") && !strcmp(v, "off"))
            disabled = true;
        else if (!strcmp(k, "url") && !strncmp(v, "http://", 7))
            snprintf(base, sizeof(base), "%s", v);
    }
    fclose(f);
    while (strlen(base) > 7 && base[strlen(base) - 1] == '/')
        base[strlen(base) - 1] = 0;
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
    if (soc_held)
        net_soc_release();
    soc_held = false;
}

void update_poll(void)
{
    if (!started) {
        started = true;
        start_at = platform_ms() + START_DELAY_MS;
        load_cfg();
    }
    if (running) {
        if (!finished)
            return;
        join();
        if (UPDATE.state == UPD_DONE) {
            char msg[96];
            snprintf(msg, sizeof(msg), "vn3ds %s is installed: restart vn3ds to use it", UPDATE.latest);
            app_toast(msg);
            E.toast_t = 5.0f;
        }
        return;
    }
    if (checked || disabled || app_single_game || platform_ms() < start_at || FETCH.busy || NET.receiving)
        return;
    if (!strcmp(current(), "dev"))
        return;
    /* at most every 6 hours (the time of the last check is the file's) */
    char stamp[400];
    snprintf(stamp, sizeof(stamp), "%s/update.last", E.root);
    struct stat st;
    if (stat(stamp, &st) == 0 && platform_time() - (u32)st.st_mtime < EVERY_S && !update_version_override)
        return;
    checked = true;
    FILE *f = fopen(stamp, "wb");
    if (f)
        fclose(f);
    if (!net_soc_acquire())
        return;
    soc_held = true;
    quit = finished = false;
    UPDATE.state = UPD_CHECKING;
    UPDATE.error[0] = 0;
#ifdef __3DS__
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    thread = threadCreate(run, NULL, 32 * 1024, prio < 0x3F ? prio + 1 : prio, -2, false);
    running = thread != NULL;
#else
    running = pthread_create(&thread, NULL, run_host, NULL) == 0;
#endif
    if (!running) {
        net_soc_release();
        soc_held = false;
        UPDATE.state = UPD_IDLE;
    }
}

void update_stop(void)
{
    if (!running)
        return;
    quit = true;
    join();
}
