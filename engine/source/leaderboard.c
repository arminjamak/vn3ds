/* Online leaderboard client; see leaderboard.h and server/leaderboard/. */

#include "leaderboard.h"
#include "app.h"
#include "leaderboard_config.h"
#include "net.h"
#include "sha256.h"

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <poll.h>
#include <unistd.h>

#ifdef __3DS__
#include <3ds.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
typedef Thread LbThread;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sys/socket.h>
#include <time.h>
typedef pthread_t LbThread;
#endif

#ifndef MSG_NOSIGNAL
#define MSG_NOSIGNAL 0
#endif

#define TIMEOUT_MS 10000
#define RESP_MAX 4096

LbJob LB_POST, LB_TOP;

/* ---- settings ------------------------------------------------------------- */

static struct {
    char host[128], prefix[128];
    int port;
    bool online;
} url;
static char url_text[200];
static char player[40];          /* per-console id, made on the first post */
static char name[LB_NAME_MAX + 1];

static void cfg_path(char *out, size_t len) { snprintf(out, len, "%s/leaderboard.cfg", E.root); }

static char *trim(char *s)
{
    while (isspace((unsigned char)*s))
        s++;
    char *e = s + strlen(s);
    while (e > s && isspace((unsigned char)e[-1]))
        *--e = 0;
    return s;
}

/* Printable ASCII, single spaces, at most LB_NAME_MAX characters. */
static void clean_name(const char *in, char *out)
{
    size_t n = 0;
    for (; *in && n < LB_NAME_MAX; in++) {
        char c = *in;
        if (c < 0x20 || c > 0x7e || (c == ' ' && (n == 0 || out[n - 1] == ' ')))
            continue;
        out[n++] = c;
    }
    while (n > 0 && out[n - 1] == ' ')
        n--;
    out[n] = 0;
}

static bool parse_url(const char *u)
{
    memset(&url, 0, sizeof(url));
    if (!*u)
        return false;
    if (strncmp(u, "http://", 7) != 0) {
        LOG("leaderboard: only http:// URLs work (got '%s')", u);
        return false;
    }
    u += 7;
    size_t hl = strcspn(u, ":/");
    if (hl == 0 || hl >= sizeof(url.host))
        return false;
    memcpy(url.host, u, hl);
    u += hl;
    url.port = 80;
    if (*u == ':') {
        url.port = atoi(u + 1);
        u += 1 + strspn(u + 1, "0123456789");
    }
    if ((*u && *u != '/') || url.port <= 0 || url.port > 65535)
        return false;
    snprintf(url.prefix, sizeof(url.prefix), "%s", u);
    size_t pl = strlen(url.prefix);
    while (pl > 0 && url.prefix[pl - 1] == '/')
        url.prefix[--pl] = 0;
    return true;
}

static void read_name(const char *cfg_name)
{
    char raw[64] = "";
    if (cfg_name && *cfg_name) {
        snprintf(raw, sizeof(raw), "%s", cfg_name);
    } else {
#ifdef __3DS__
        /* the profile nickname: UTF-16, up to 10 characters */
        u16 nick[0x1C / 2 + 1];
        memset(nick, 0, sizeof(nick));
        if (R_SUCCEEDED(cfguInit())) {
            CFGU_GetConfigInfoBlk2(0x1C, 0x000A0000, nick);
            cfguExit();
        }
        size_t n = 0;
        for (int i = 0; i < 0x1C / 2 && nick[i] && n < sizeof(raw) - 1; i++)
            if (nick[i] >= 0x20 && nick[i] <= 0x7e)
                raw[n++] = (char)nick[i];
        raw[n] = 0;
#else
        snprintf(raw, sizeof(raw), "Desktop");
#endif
    }
    clean_name(raw, name);
    if (!name[0])
        snprintf(name, sizeof(name), "Player");
}

void lb_init(void)
{
    char path[400], line[300], cfg_name[64] = "";
    bool have_url = false;
    snprintf(url_text, sizeof(url_text), "%s", LEADERBOARD_URL);
    player[0] = 0;
    cfg_path(path, sizeof(path));
    FILE *f = fopen(path, "r");
    if (f) {
        while (fgets(line, sizeof(line), f)) {
            char *s = trim(line), *eq = strchr(s, '=');
            if (*s == '#' || !eq)
                continue;
            *eq = 0;
            char *key = trim(s), *val = trim(eq + 1);
            if (!strcmp(key, "url")) {
                snprintf(url_text, sizeof(url_text), "%s", val);
                have_url = true;
            } else if (!strcmp(key, "player") && strlen(val) < sizeof(player) &&
                       strspn(val, "0123456789abcdefABCDEF") == strlen(val)) {
                snprintf(player, sizeof(player), "%s", val);
            } else if (!strcmp(key, "name")) {
                snprintf(cfg_name, sizeof(cfg_name), "%s", val);
            }
        }
        fclose(f);
    }
    url.online = parse_url(url_text);
    read_name(cfg_name);
    LOG("leaderboard: %s%s, playing as %s", url.online ? url_text : "offline",
        have_url ? " (leaderboard.cfg)" : "", name);
}

bool lb_online(void) { return url.online; }
const char *lb_url(void) { return url_text; }
const char *lb_name(void) { return name; }

/* ---- randomness -------------------------------------------------------------- */

static void hex(const u8 *in, size_t n, char *out)
{
    static const char H[] = "0123456789abcdef";
    for (size_t i = 0; i < n; i++) {
        out[i * 2] = H[in[i] >> 4];
        out[i * 2 + 1] = H[in[i] & 15];
    }
    out[n * 2] = 0;
}

static u64 now_ms(void)
{
#ifdef __3DS__
    return osGetTime();
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (u64)ts.tv_sec * 1000 + (u64)ts.tv_nsec / 1000000;
#endif
}

/* 16 random bytes: the system's generator, or a hash of clocks if it fails. */
static void random16(u8 out[16])
{
#ifdef __3DS__
    bool ok = false;
    if (R_SUCCEEDED(psInit())) {
        ok = R_SUCCEEDED(PS_GenerateRandomBytes(out, 16));
        psExit();
    }
    if (ok)
        return;
    u64 tick = svcGetSystemTick();
#else
    FILE *f = fopen("/dev/urandom", "rb");
    if (f) {
        size_t got = fread(out, 1, 16, f);
        fclose(f);
        if (got == 16)
            return;
    }
    u64 tick = (u64)clock();
#endif
    static u32 counter;
    struct { u64 tick, ms; u32 t, frame, counter; const void *where; } seed = {
        tick, now_ms(), platform_time(), E.frame, ++counter, &seed};
    Sha256 s;
    u8 d[32];
    sha256_init(&s);
    sha256_update(&s, &seed, sizeof(seed));
    sha256_final(&s, d);
    memcpy(out, d, 16);
}

/* The per-console id: made once and appended to leaderboard.cfg. */
static void ensure_player(void)
{
    if (player[0])
        return;
    u8 r[16];
    random16(r);
    hex(r, 16, player);
    char path[400];
    cfg_path(path, sizeof(path));
    bool newline = false;
    FILE *f = fopen(path, "rb");
    if (f) {
        if (fseek(f, -1, SEEK_END) == 0)
            newline = fgetc(f) != '\n';
        fclose(f);
    }
    f = fopen(path, "ab");
    if (!f) {
        LOG("leaderboard: cannot write %s", path);
        return;   /* still fine for this session */
    }
    fprintf(f, "%splayer = %s\n", newline ? "\n" : "", player);
    fclose(f);
}

/* ---- requests ------------------------------------------------------------------ */

typedef struct {
    LbJob *job;
    bool is_post;
    bool running;   /* thread started and not yet joined */
    bool soc;       /* holds a net_soc_acquire() */
    LbThread thread;
    char req[1200];
    char resp[RESP_MAX + 1];
} Worker;

static Worker W[2] = {{&LB_POST, true}, {&LB_TOP, false}};
static volatile bool quitting;
static char pending_top[24];

static void fail(LbJob *j, const char *msg)
{
    snprintf(j->error, sizeof(j->error), "%s", msg);
    __sync_synchronize();
    j->state = LB_FAILED;
}

/* Waits until fd is ready for `events`; false on timeout or shutdown. */
static bool wait_fd(int fd, int events, u64 deadline)
{
    while (!quitting && now_ms() < deadline) {
        struct pollfd p = {fd, events, 0};
        int r = poll(&p, 1, 100);
        if (r > 0)
            return true;
        if (r < 0 && errno != EINTR)
            return false;
    }
    return false;
}

static bool resolve(struct in_addr *out)
{
    if (inet_pton(AF_INET, url.host, out) == 1)
        return true;
    struct addrinfo hints, *res = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(url.host, NULL, &hints, &res) != 0 || !res)
        return false;
    *out = ((struct sockaddr_in *)res->ai_addr)->sin_addr;
    freeaddrinfo(res);
    return true;
}

/* Sends w->req and reads the reply into w->resp. Returns the HTTP status and
 * points *body at the body, or -1 with *body set to the reason. */
static int http(Worker *w, const char **body)
{
    u64 deadline = now_ms() + TIMEOUT_MS;
    struct sockaddr_in sa;
    memset(&sa, 0, sizeof(sa));
    sa.sin_family = AF_INET;
    sa.sin_port = htons((u16)url.port);
    if (!resolve(&sa.sin_addr)) {
        *body = "Cannot find the server";
        return -1;
    }
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        *body = "No network";
        return -1;
    }
#ifdef SO_NOSIGPIPE
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &one, sizeof(one));
#endif
    fcntl(fd, F_SETFL, fcntl(fd, F_GETFL, 0) | O_NONBLOCK);
    *body = "Cannot reach the server";
    int status = -1;
    if (connect(fd, (struct sockaddr *)&sa, sizeof(sa)) < 0 &&
        errno != EINPROGRESS && errno != EWOULDBLOCK && errno != EAGAIN)
        goto out;
    if (!wait_fd(fd, POLLOUT, deadline))
        goto out;
    int soerr = 0;
    socklen_t sl = sizeof(soerr);
    if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &soerr, &sl) == 0 && soerr != 0)
        goto out;

    size_t len = strlen(w->req), sent = 0;
    while (sent < len) {
        if (!wait_fd(fd, POLLOUT, deadline))
            goto out;
        ssize_t r = send(fd, w->req + sent, len - sent, MSG_NOSIGNAL);
        if (r > 0)
            sent += (size_t)r;
        else if (r < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
            goto out;
    }
    size_t got = 0;
    *body = "No answer from the server";
    for (;;) {
        if (got == RESP_MAX || !wait_fd(fd, POLLIN, deadline))
            break;
        ssize_t r = recv(fd, w->resp + got, RESP_MAX - got, 0);
        if (r > 0)
            got += (size_t)r;
        else if (r == 0)
            break;   /* HTTP/1.0: the server closes after the reply */
        else if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
            break;
    }
    w->resp[got] = 0;
    char *b = strstr(w->resp, "\r\n\r\n");
    int code;
    if (b && sscanf(w->resp, "HTTP/%*d.%*d %d", &code) == 1) {
        status = code;
        *body = b + 4;
    }
out:
    close(fd);
    return status;
}

static void parse_top(LbJob *j, const char *p)
{
    j->ntop = 0;
    while (*p && j->ntop < LB_TOP_MAX) {
        LbEntry *e = &j->top[j->ntop];
        char *end;
        e->rank = (int)strtol(p, &end, 10);
        if (end == p || *end != '\t')
            break;
        p = end + 1;
        size_t n = strcspn(p, "\t\n");
        char raw[64];
        snprintf(raw, sizeof(raw), "%.*s", (int)(n < 63 ? n : 63), p);
        clean_name(raw, e->name);
        p += n;
        if (*p != '\t')
            break;
        e->score = atoi(p + 1);
        j->ntop++;
        p += strcspn(p, "\n");
        if (*p == '\n')
            p++;
    }
}

static void work(void *arg)
{
    Worker *w = arg;
    LbJob *j = w->job;
    const char *body;
    int status = http(w, &body);
    if (status < 0) {
        fail(j, body);
        return;
    }
    if (status != 200) {
        char msg[80];
        if (!strncmp(body, "error\t", 6))
            snprintf(msg, sizeof(msg), "%.*s", (int)strcspn(body + 6, "\r\n"), body + 6);
        else
            snprintf(msg, sizeof(msg), "Server error %d", status);
        fail(j, msg);
        return;
    }
    if (w->is_post) {
        if (sscanf(body, "ok\t%d\t%d", &j->rank, &j->total) != 2) {
            fail(j, "Unexpected reply");
            return;
        }
    } else {
        parse_top(j, body);
    }
    __sync_synchronize();
    j->state = LB_DONE;
}

#ifndef __3DS__
static void *work_host(void *arg)
{
    work(arg);
    return NULL;
}
#endif

static void join(Worker *w)
{
    if (!w->running)
        return;
#ifdef __3DS__
    threadJoin(w->thread, U64_MAX);
    threadFree(w->thread);
#else
    pthread_join(w->thread, NULL);
#endif
    w->running = false;
    if (w->soc)
        net_soc_release();
    w->soc = false;
}

/* Starts w->req on a thread; the job's game is already set. */
static void start(Worker *w)
{
    LbJob *j = w->job;
    j->state = LB_BUSY;
    j->error[0] = 0;
    j->ntop = 0;
    if (!net_soc_acquire()) {
        fail(j, "Wi-Fi is off");
        return;
    }
    w->soc = true;
#ifdef __3DS__
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    w->thread = threadCreate(work, w, 32 * 1024, prio > 0x18 ? prio - 1 : prio, -2, false);
    w->running = w->thread != NULL;
#else
    w->running = pthread_create(&w->thread, NULL, work_host, w) == 0;
#endif
    if (!w->running) {
        net_soc_release();
        w->soc = false;
        fail(j, "Cannot start a thread");
    }
}

static void host_header(char *out, size_t len)
{
    if (url.port == 80)
        snprintf(out, len, "%s", url.host);
    else
        snprintf(out, len, "%s:%d", url.host, url.port);
}

static void url_encode(const char *s, char *out, size_t len)
{
    static const char H[] = "0123456789ABCDEF";
    size_t n = 0;
    for (; *s && n + 4 < len; s++) {
        unsigned char c = (unsigned char)*s;
        if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            out[n++] = (char)c;
        } else {
            out[n++] = '%';
            out[n++] = H[c >> 4];
            out[n++] = H[c & 15];
        }
    }
    out[n] = 0;
}

static void start_top(const char *game)
{
    Worker *w = &W[1];
    char host[160];
    host_header(host, sizeof(host));
    snprintf(LB_TOP.game, sizeof(LB_TOP.game), "%s", game);
    snprintf(w->req, sizeof(w->req),
             "GET %s/v1/top?game=%s&n=%d HTTP/1.0\r\nHost: %s\r\nUser-Agent: vn3ds\r\n\r\n",
             url.prefix, game, LB_TOP_MAX, host);
    start(w);
}

void lb_poll(void)
{
    for (int i = 0; i < 2; i++)
        if (W[i].running && W[i].job->state != LB_BUSY)
            join(&W[i]);
    if (pending_top[0] && LB_TOP.state != LB_BUSY) {
        char game[24];
        snprintf(game, sizeof(game), "%s", pending_top);
        pending_top[0] = 0;
        start_top(game);
    }
}

bool lb_post(const char *game, int score)
{
    Worker *w = &W[0];
    lb_poll();
    if (!url.online || LB_POST.state == LB_BUSY)
        return false;
    ensure_player();
    u8 r[16];
    char nonce[33], msg[200], sig[65], ename[3 * LB_NAME_MAX + 1], form[400], host[160];
    random16(r);
    hex(r, 16, nonce);
    snprintf(msg, sizeof(msg), "%s|%s|%d|%s", game, name, score, nonce);
    hmac_sha256_hex(LEADERBOARD_KEY, msg, sig);
    url_encode(name, ename, sizeof(ename));
    snprintf(form, sizeof(form), "game=%s&name=%s&score=%d&player=%s&nonce=%s&sig=%s", game, ename,
             score, player, nonce, sig);
    host_header(host, sizeof(host));
    snprintf(w->req, sizeof(w->req),
             "POST %s/v1/score HTTP/1.0\r\nHost: %s\r\nUser-Agent: vn3ds\r\n"
             "Content-Type: application/x-www-form-urlencoded\r\nContent-Length: %d\r\n\r\n%s",
             url.prefix, host, (int)strlen(form), form);
    snprintf(LB_POST.game, sizeof(LB_POST.game), "%s", game);
    LB_POST.score = score;
    LB_POST.rank = LB_POST.total = 0;
    start(w);
    return true;
}

bool lb_fetch_top(const char *game)
{
    lb_poll();
    if (!url.online)
        return false;
    if (LB_TOP.state == LB_BUSY) {
        if (!strcmp(LB_TOP.game, game))
            pending_top[0] = 0;   /* already on its way */
        else
            snprintf(pending_top, sizeof(pending_top), "%s", game);
        return true;
    }
    start_top(game);
    return true;
}

bool lb_top_is(const char *game) { return !strcmp(LB_TOP.game, game) && !pending_top[0]; }

void lb_shutdown(void)
{
    quitting = true;
    for (int i = 0; i < 2; i++)
        join(&W[i]);
    pending_top[0] = 0;
    quitting = false;
}
