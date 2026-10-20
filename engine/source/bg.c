/* The background thread (see bg.h). */

#include "bg.h"
#include "platform.h"

#ifdef __3DS__
#include <3ds.h>
static Thread thread;
static LightLock lock = 1;   /* (1 = unlocked, as LightLock_Init leaves it) */
static LightEvent wake_ev;
#else
#include <pthread.h>
#include <time.h>
static pthread_t thread;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t idle_mx = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t wake_cv = PTHREAD_COND_INITIALIZER, idle_cv = PTHREAD_COND_INITIALIZER;
static bool wake_flag;
static u32 idle_req, idle_ack;
#endif

static volatile bool running, quit;

/* ---- file writes ----------------------------------------------------------- */

typedef struct FileJob {
    struct FileJob *next;
    char path[320];
    void *data;
    size_t len;
} FileJob;
static FileJob *files_head, *files_tail;
static volatile int files_busy;

static void write_now(const char *path, const void *data, size_t len)
{
    u64 t0 = platform_us();
    FILE *f = fopen(path, "wb");
    bool ok = f && fwrite(data, 1, len, f) == len;
    if (f)
        ok = (fclose(f) == 0) && ok;
    if (!ok)
        LOG("cannot write %s", path);
    PERF("bg: wrote %s (%u bytes) in %.1f ms", path, (unsigned)len, (platform_us() - t0) / 1000.0);
}

static bool files_work(void)
{
    bg_lock();
    FileJob *j = files_head;
    if (j) {
        files_head = j->next;
        if (!files_head)
            files_tail = NULL;
        files_busy++;
    }
    bg_unlock();
    if (!j)
        return false;
    write_now(j->path, j->data, j->len);
    free(j->data);
    free(j);
    bg_lock();
    files_busy--;
    bg_unlock();
    return true;
}

void bg_write_file(const char *path, void *data, size_t len)
{
    FileJob *j = running ? calloc(1, sizeof(*j)) : NULL;
    if (!j) {
        write_now(path, data, len);
        free(data);
        return;
    }
    snprintf(j->path, sizeof(j->path), "%s", path);
    j->data = data;
    j->len = len;
    bg_lock();
    /* a newer version of the same file replaces one still waiting */
    for (FileJob *o = files_head; o; o = o->next)
        if (!strcmp(o->path, j->path)) {
            free(o->data);
            o->data = j->data;
            o->len = j->len;
            free(j);
            j = NULL;
            break;
        }
    if (j) {
        if (files_tail)
            files_tail->next = j;
        else
            files_head = j;
        files_tail = j;
    }
    bg_unlock();
    bg_wake();
}

void bg_flush_files(void)
{
    for (int i = 0; i < 5000; i++) {
        bg_lock();
        bool pending = files_head || files_busy;
        bg_unlock();
        if (!pending)
            return;
        if (!running) {
            while (files_work())
                ;
            return;
        }
        bg_wake();
        bg_sleep_ms(1);
    }
}

/* ---- the thread ---------------------------------------------------------------- */

static bool work_once(void)
{
    /* music first, a texture stage at a time in between */
    bool did = audio_bg_work();
    if (!did)
        did = texcache_bg_work();
    if (!did)
        did = files_work();
    return did;
}

static void loop(void)
{
    u64 last_flush = platform_ms();
    while (!quit) {
#ifndef __3DS__
        pthread_mutex_lock(&idle_mx);
        u32 req = idle_req;
        pthread_mutex_unlock(&idle_mx);
#endif
        bool did = work_once();
        u64 now = platform_ms();
        if (now - last_flush > 2000) {
            platform_perf_flush();
            last_flush = now;
        }
        if (did)
            continue;
#ifdef __3DS__
        /* a short timeout: music keeps being decoded as the music plays */
        LightEvent_WaitTimeout(&wake_ev, 4 * 1000000LL);
#else
        pthread_mutex_lock(&idle_mx);
        if (idle_ack < req) {
            idle_ack = req;
            pthread_cond_broadcast(&idle_cv);
        }
        if (!wake_flag && !quit) {
            struct timespec ts;
            clock_gettime(CLOCK_REALTIME, &ts);
            ts.tv_nsec += 4 * 1000000L;
            if (ts.tv_nsec >= 1000000000L) {
                ts.tv_sec++;
                ts.tv_nsec -= 1000000000L;
            }
            pthread_cond_timedwait(&wake_cv, &idle_mx, &ts);
        }
        wake_flag = false;
        pthread_mutex_unlock(&idle_mx);
#endif
    }
    while (files_work())
        ;
    platform_perf_flush();
}

#ifdef __3DS__
static void thread_main(void *arg)
{
    (void)arg;
    loop();
}
#else
static void *thread_main(void *arg)
{
    (void)arg;
    loop();
    return NULL;
}
#endif

bool bg_start(void)
{
    if (running)
        return true;
    quit = false;
#ifdef __3DS__
    LightEvent_Init(&wake_ev, RESET_ONESHOT);
    s32 prio = 0x30;
    svcGetThreadPriority(&prio, CUR_THREAD_HANDLE);
    /* below the main thread, on its core: it runs while the main thread
     * waits for the screen. A big stack for the Vorbis/Opus decoders and the
     * JPEG decoder. */
    thread = threadCreate(thread_main, NULL, 128 * 1024, prio < 0x3F ? prio + 1 : prio, -2, false);
    running = thread != NULL;
#else
    running = pthread_create(&thread, NULL, thread_main, NULL) == 0;
#endif
    if (!running)
        LOG("bg: cannot start the background thread; loading on the main thread");
    return running;
}

void bg_stop(void)
{
    if (!running)
        return;
    quit = true;
    bg_wake();
#ifdef __3DS__
    threadJoin(thread, U64_MAX);
    threadFree(thread);
#else
    pthread_join(thread, NULL);
#endif
    running = false;
}

bool bg_running(void) { return running; }

void bg_wake(void)
{
    if (!running)
        return;
#ifdef __3DS__
    LightEvent_Signal(&wake_ev);
#else
    pthread_mutex_lock(&idle_mx);
    wake_flag = true;
    pthread_cond_signal(&wake_cv);
    pthread_mutex_unlock(&idle_mx);
#endif
}

void bg_idle(void)
{
#ifndef __3DS__
    if (!running)
        return;
    pthread_mutex_lock(&idle_mx);
    u32 req = ++idle_req;
    wake_flag = true;
    pthread_cond_signal(&wake_cv);
    while (idle_ack < req)
        pthread_cond_wait(&idle_cv, &idle_mx);
    pthread_mutex_unlock(&idle_mx);
#endif
}

void bg_lock(void)
{
#ifdef __3DS__
    LightLock_Lock(&lock);
#else
    pthread_mutex_lock(&lock);
#endif
}

void bg_unlock(void)
{
#ifdef __3DS__
    LightLock_Unlock(&lock);
#else
    pthread_mutex_unlock(&lock);
#endif
}

void bg_sleep_ms(int ms)
{
#ifdef __3DS__
    svcSleepThread((s64)ms * 1000000LL);
#else
    struct timespec ts = {0, ms * 1000000L};
    nanosleep(&ts, NULL);
#endif
}

void bg_mutex_lock(BgMutex *m)
{
#ifdef __3DS__
    LightLock_Lock(m);
#else
    pthread_mutex_lock(m);
#endif
}

void bg_mutex_unlock(BgMutex *m)
{
#ifdef __3DS__
    LightLock_Unlock(m);
#else
    pthread_mutex_unlock(m);
#endif
}
