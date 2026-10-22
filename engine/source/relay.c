/* The link to the vn3ds relay; see relay.h and server/relay/relay.py.
 *
 * Connecting (name lookup, connect, the hello) happens on a short-lived
 * thread, so the main loop never waits on the network. That thread follows
 * the receiver's rules: non-blocking calls, poll() with no timeout and a
 * millisecond's nap in between (a blocking call holds up the 3DS's one
 * socket service for everyone). The connected socket then goes to net.c
 * (net_adopt), which treats it like a computer that connected to us: the
 * same receiver, checks against the card, staging, resume after a drop. */

#include "relay.h"
#include "app.h"
#include "fetch.h"
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
static Thread thread;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sys/socket.h>
#include <time.h>
static pthread_t thread;
#endif

#ifndef MSG_NOSIGNAL
#define MSG_NOSIGNAL 0
#endif

#define CONNECT_MS 10000
#define CODE_ALPHABET "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

RelayStatus RELAY;

static char key[33], host[128], nick[24];
static int port = RELAY_PORT;
static bool loaded, paired, disabled;
static bool running;              /* the connect thread exists (until joined) */
static volatile bool done, quit;  /* it finished / it should stop */
static volatile int result_fd = -1;
static u64 next_try, linked_at;
static int fails;
static bool linked;               /* our socket is with the receiver now */

static void cfg_path(char *out, size_t len) { snprintf(out, len, "%s/relay.cfg", E.root); }

static void nap(void)
{
#ifdef __3DS__
    svcSleepThread(1000000LL);
#else
    usleep(1000);
#endif
}

void relay_code_of(const char *k, char out[9])
{
    Sha256 s;
    u8 d[32];
    static const char prefix[] = "vn3ds-relay-code:";
    sha256_init(&s);
    sha256_update(&s, prefix, sizeof(prefix) - 1);
    sha256_update(&s, k, strlen(k));
    sha256_final(&s, d);
    u64 bits = 0;
    for (int i = 0; i < 5; i++)
        bits = bits << 8 | d[i];
    for (int i = 0; i < 8; i++)
        out[i] = CODE_ALPHABET[(bits >> (35 - 5 * i)) & 31];
    out[8] = 0;
}

void relay_code_text(char *out, size_t len)
{
    snprintf(out, len, "%.4s %.4s", RELAY.code, RELAY.code + 4);
}

static char *trim(char *s)
{
    while (isspace((unsigned char)*s))
        s++;
    char *e = s + strlen(s);
    while (e > s && isspace((unsigned char)e[-1]))
        *--e = 0;
    return s;
}

static bool valid_key(const char *k)
{
    if (strlen(k) != 32)
        return false;
    for (int i = 0; i < 32; i++)
        if (!isxdigit((unsigned char)k[i]) || isupper((unsigned char)k[i]))
            return false;
    return true;
}

static void set_server(const char *v)
{
    host[0] = 0;
    port = RELAY_PORT;
    if (!*v) {
        disabled = true;
        return;
    }
    const char *colon = strrchr(v, ':');
    size_t n = colon ? (size_t)(colon - v) : strlen(v);
    if (n >= sizeof(host))
        n = sizeof(host) - 1;
    memcpy(host, v, n);
    host[n] = 0;
    if (colon && atoi(colon + 1) > 0 && atoi(colon + 1) < 65536)
        port = atoi(colon + 1);
}

static void load(void)
{
    if (loaded)
        return;
    loaded = true;
    snprintf(host, sizeof(host), "%s", RELAY_SERVER);
    char web[128];
    snprintf(web, sizeof(web), "%s", RELAY_WEB);
    char path[400], line[300];
    cfg_path(path, sizeof(path));
    FILE *f = fopen(path, "rb");
    if (f) {
        while (fgets(line, sizeof(line), f)) {
            char *eq = strchr(line, '=');
            if (!eq || line[0] == '#')
                continue;
            *eq = 0;
            char *k = trim(line), *v = trim(eq + 1);
            char *hash = strchr(v, '#');   /* a comment after the value */
            if (hash) {
                *hash = 0;
                v = trim(v);
            }
            if (!strcmp(k, "key") && valid_key(v))
                snprintf(key, sizeof(key), "%s", v);
            else if (!strcmp(k, "server"))
                set_server(v);
            else if (!strcmp(k, "web") && *v)
                snprintf(web, sizeof(web), "%s", v);
        }
        fclose(f);
    }
    while (strlen(web) > 1 && web[strlen(web) - 1] == '/')
        web[strlen(web) - 1] = 0;
    const char *shown = strstr(web, "://") ? strstr(web, "://") + 3 : web;
    snprintf(RELAY.web, sizeof(RELAY.web), "%s", shown);
    /* the name the page lists this 3DS by: the profile nickname, plain ASCII */
#ifdef __3DS__
    u16 n16[0x1C / 2 + 1];
    memset(n16, 0, sizeof(n16));
    if (R_SUCCEEDED(cfguInit())) {
        CFGU_GetConfigInfoBlk2(0x1C, 0x000A0000, n16);
        cfguExit();
    }
    size_t nn = 0;
    for (int i = 0; i < 0x1C / 2 && n16[i] && nn < sizeof(nick) - 1; i++)
        if (isalnum(n16[i] & 0x7F) && n16[i] < 0x80)
            nick[nn++] = (char)n16[i];
        else if (n16[i] == ' ' && nn > 0)
            nick[nn++] = ' ';
    nick[nn] = 0;
#endif
    if (!nick[0])
        snprintf(nick, sizeof(nick), "3DS");
    paired = key[0] != 0;
    if (paired) {
        relay_code_of(key, RELAY.code);
        snprintf(RELAY.url, sizeof(RELAY.url), "%s/#%s", web, RELAY.code);
    }
}

static void random_key(char out[33])
{
    u8 r[16];
    bool ok = false;
#ifdef __3DS__
    if (R_SUCCEEDED(psInit())) {
        ok = R_SUCCEEDED(PS_GenerateRandomBytes(r, 16));
        psExit();
    }
#else
    FILE *f = fopen("/dev/urandom", "rb");
    if (f) {
        ok = fread(r, 1, 16, f) == 16;
        fclose(f);
    }
#endif
    if (!ok) {   /* a hash of whatever differs from run to run */
        struct { u64 ms; u32 t, frame; const void *where; } seed = {platform_ms(), platform_time(), E.frame, &seed};
        Sha256 s;
        u8 d[32];
        sha256_init(&s);
        sha256_update(&s, &seed, sizeof(seed));
        sha256_final(&s, d);
        memcpy(r, d, 16);
    }
    static const char H[] = "0123456789abcdef";
    for (int i = 0; i < 16; i++) {
        out[i * 2] = H[r[i] >> 4];
        out[i * 2 + 1] = H[r[i] & 15];
    }
    out[32] = 0;
}

void relay_pair(void)
{
    load();
    if (paired)
        return;
    random_key(key);
    char path[400];
    cfg_path(path, sizeof(path));
    FILE *f = fopen(path, "ab");
    if (f) {
        fprintf(f, "key = %s\n", key);
        fclose(f);
    }
    loaded = false;   /* read it back: the code and address follow from it */
    load();
    LOG("relay: paired, code %s", RELAY.code);
}

/* ---- the connect thread ---- */

static int connect_once(void)
{
    struct sockaddr_in sa;
    memset(&sa, 0, sizeof(sa));
    sa.sin_family = AF_INET;
    sa.sin_port = htons((u16)port);
    if (inet_pton(AF_INET, host, &sa.sin_addr) != 1) {
        struct addrinfo hints, *res = NULL;
        memset(&hints, 0, sizeof(hints));
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;
        if (getaddrinfo(host, NULL, &hints, &res) != 0 || !res)
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
    net_tune_socket(fd);   /* before connect(), so the handshake advertises the window */
    fcntl(fd, F_SETFL, fcntl(fd, F_GETFL, 0) | O_NONBLOCK);
    u64 deadline = platform_ms() + CONNECT_MS;
    if (connect(fd, (struct sockaddr *)&sa, sizeof(sa)) < 0 && errno != EINPROGRESS && errno != EWOULDBLOCK) {
        close(fd);
        return -1;
    }
    for (;;) {   /* connected yet? */
        struct pollfd p = {fd, POLLOUT, 0};
        int r = poll(&p, 1, 0);
        if (r > 0) {
            int err = 0;
            socklen_t el = sizeof(err);
            if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &el) < 0 || err) {
                close(fd);
                return -1;
            }
            break;
        }
        if ((r < 0 && errno != EINTR) || quit || platform_ms() > deadline) {
            close(fd);
            return -1;
        }
        nap();
    }
    /* the WebSocket upgrade; the key says which 3DS this is */
    char hello[512];
    int hl = snprintf(hello, sizeof(hello),
                      "GET /3ds HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                      "Sec-WebSocket-Key: dm4zZHMtcmVsYXktbGluaw==\r\nSec-WebSocket-Version: 13\r\n"
                      "X-VN3DS-Key: %s\r\nX-VN3DS-Name: %s\r\nX-VN3DS-Version: 1\r\n\r\n",
                      host, key, nick);
    size_t sent = 0;
    while (sent < (size_t)hl) {
        ssize_t r = send(fd, hello + sent, (size_t)hl - sent, MSG_NOSIGNAL);
        if (r > 0) {
            sent += (size_t)r;
            continue;
        }
        if ((r < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR) || quit ||
            platform_ms() > deadline) {
            close(fd);
            return -1;
        }
        nap();
    }
    /* the answer, a byte at a time so nothing after it is taken from the
     * receiver: "HTTP/1.1 101 ..." and headers up to an empty line */
    char resp[1024];
    size_t got = 0;
    while (got < sizeof(resp) - 1 && !(got >= 4 && !memcmp(resp + got - 4, "\r\n\r\n", 4))) {
        ssize_t r = recv(fd, resp + got, 1, 0);
        if (r == 1) {
            got++;
            continue;
        }
        if (r == 0 || (r < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR) || quit ||
            platform_ms() > deadline) {
            close(fd);
            return -1;
        }
        nap();
    }
    resp[got] = 0;
    if (strncmp(resp, "HTTP/1.1 101", 12) != 0) {
        LOG("relay: the server said %.40s", resp);
        close(fd);
        return -1;
    }
    return fd;
}

static void thread_main(void *arg)
{
    (void)arg;
    result_fd = connect_once();
    done = true;
}

#ifndef __3DS__
static void *thread_main_host(void *arg)
{
    thread_main(arg);
    return NULL;
}
#endif

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

static bool start_thread(void)
{
    done = quit = false;
    result_fd = -1;
#ifdef __3DS__
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    thread = threadCreate(thread_main, NULL, 16 * 1024, prio < 0x3F ? prio + 1 : prio, -2, false);
    running = thread != NULL;
#else
    running = pthread_create(&thread, NULL, thread_main_host, NULL) == 0;
#endif
    return running;
}

static void retry_later(bool failed)
{
    if (failed)
        fails++;
    u64 wait = failed ? 2000ull << (fails < 5 ? fails : 5) : 500;   /* 4 s .. 64 s after failures */
    next_try = platform_ms() + wait;
}

void relay_stop(void)
{
    if (running) {
        quit = true;
        join();
        if (result_fd >= 0)
            close(result_fd);
        result_fd = -1;
    }
    linked = false;
    if (RELAY.state == RELAY_ONLINE || RELAY.state == RELAY_TRYING)
        RELAY.state = RELAY_OFF;
}

void relay_poll(void)
{
    load();
    if (!paired || disabled || !host[0])
        return;
    if (!NET.listening) {   /* the receiver is off (or a web download has the network) */
        relay_stop();
        return;
    }
    u64 now = platform_ms();
    if (linked) {
        if (net_rx_busy())
            return;   /* the receiver has it: waiting for a game, or receiving one */
        linked = false;
        /* the relay closes an idle link every 15 s: reconnect at once; a
         * link that ends straight away means something is wrong there */
        bool short_lived = now - linked_at < 3000;
        retry_later(short_lived);
        RELAY.state = short_lived ? RELAY_UNREACHABLE : RELAY_ONLINE;
        return;
    }
    if (running) {
        if (!done)
            return;
        join();
        int fd = result_fd;
        result_fd = -1;
        if (fd < 0) {
            RELAY.state = RELAY_UNREACHABLE;
            retry_later(true);
            return;
        }
        if (!net_adopt(fd, true)) {   /* a computer got there first: try again after it */
            close(fd);
            retry_later(false);
            return;
        }
        linked = true;
        linked_at = now;
        fails = 0;
        RELAY.state = RELAY_ONLINE;
        return;
    }
    if (now < next_try || FETCH.busy || net_rx_busy())
        return;
    if (RELAY.state == RELAY_OFF)
        RELAY.state = RELAY_TRYING;
    if (!start_thread())
        retry_later(true);
}
