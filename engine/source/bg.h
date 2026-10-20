#pragma once
/* The background thread: slow work the main thread should never wait for.
 *
 * It runs below the main thread's priority on the same core, so on the 3DS
 * it gets the time the main thread spends waiting for the screen (and for
 * the SD card), and never takes a frame's time. In order of priority it
 *   - decodes music ahead into the music decks (audio_bg_work),
 *   - reads and decodes textures the script is about to show
 *     (texcache_bg_work),
 *   - writes autosaves (bg_write_file),
 *   - writes the buffered timing lines to the log. */
#include "common.h"

#ifdef __3DS__
#include <3ds/svc.h>
#include <3ds/synchronization.h>
typedef LightLock BgMutex;
#define BG_MUTEX_INIT 1
#else
#include <pthread.h>
typedef pthread_mutex_t BgMutex;
#define BG_MUTEX_INIT PTHREAD_MUTEX_INITIALIZER
#endif
void bg_mutex_lock(BgMutex *m);
void bg_mutex_unlock(BgMutex *m);

bool bg_start(void);
void bg_stop(void);
/* New work is queued: wake the thread up. */
void bg_wake(void);
/* Desktop build: wait until the thread has nothing left to do. The test
 * runner calls it once a frame, standing in for the 3DS main thread's wait
 * for the screen, so runs are reproducible. Does nothing on the 3DS. */
void bg_idle(void);
/* One lock for the job lists shared with the thread. Held briefly. */
void bg_lock(void);
void bg_unlock(void);
/* The main thread waiting for the background thread (lets it run). */
void bg_sleep_ms(int ms);
bool bg_running(void);
/* Writes `len` bytes to `path` in the background (the buffer is freed);
 * written straight away when the thread is not running. */
void bg_write_file(const char *path, void *data, size_t len);
/* Waits until queued file writes are done (before reading them back). */
void bg_flush_files(void);

/* Work functions the thread calls; each returns true if it did something. */
bool audio_bg_work(void);
bool texcache_bg_work(void);
