#pragma once
#include "common.h"

/* vn3ds updates itself from the newest GitHub release, through the vn3ds
 * link (server/link/worker.js, plain HTTP: the 3DS has no TLS worth using):
 *
 *   GET <url>/latest  ->  vn3ds-latest 1
 *                         <tag, e.g. v0.3.0>
 *                         3dsx <size> <sha256 hex>
 *                         cia <size> <sha256 hex>
 *   GET <url>/vn3ds.3dsx, <url>/vn3ds.cia  ->  that release's file
 *
 * A .3dsx copy replaces itself; one installed as a HOME Menu title (FBI)
 * installs the new .cia over itself with the AM service, as FBI does. The
 * download is checked against its SHA-256 before anything is replaced, and
 * resumes after a drop. The new version runs from the next start.
 *
 * update.cfg in the vn3ds folder:  auto = off  (no checks)
 *                                  url = http://link.vn3ds.com
 * Builds without a release tag (VN3DS_VERSION "dev") never update. */
#ifndef VN3DS_VERSION
#define VN3DS_VERSION "dev"
#endif
#define UPDATE_URL "http://link.vn3ds.com"

typedef enum { UPD_IDLE, UPD_CHECKING, UPD_DOWNLOADING, UPD_INSTALLING, UPD_DONE, UPD_FAILED } UpdateState;

typedef struct {
    volatile UpdateState state;
    char latest[24];        /* the newest release's tag, once known */
    volatile u64 done, total;
    char error[96];
} UpdateStatus;

extern UpdateStatus UPDATE;
extern const char *update_version_override;   /* the desktop build's --version (tests) */

/* Main thread, every frame: checks once a while after start (when the
 * network is up), at most every 6 hours. */
void update_poll(void);
void update_stop(void);
/* 1 when version a is newer than b ("v1.2.3" against "v1.2"), 0 when not,
 * -1 when either isn't a version. */
int update_compare(const char *a, const char *b);
