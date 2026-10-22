#pragma once
#include "common.h"

/* Downloads a game from the web: the home screen's first-run offer of
 * Snapshot, the demo game. <url>/manifest.txt names the files:
 *
 *   vn3ds-dl 1 <game id>
 *   <size> <crc32, hex> <path inside the game folder>
 *   ...
 *
 * (tools/dl_manifest.py writes it.) Files land in games/<id>/ as .part
 * files and take their real names once their CRC matches, so a broken
 * download picks up where it stopped. Progress goes into the NET counters
 * (net.h), the same ones a Wi-Fi transfer uses, so the home screen shows the
 * game arriving the same way. Plain http:// only: a "download.cfg" in the
 * vn3ds folder can point elsewhere with a line "snapshot = http://...". */
#define SNAPSHOT_URL "http://vn3ds.com/dl/snapshot"
#define SNAPSHOT_SIZE_TEXT "44 MB"

typedef struct {
    volatile bool busy;   /* a download is running (Wi-Fi transfers wait) */
    bool failed;          /* the last one stopped: error says why */
    char error[96];
} FetchStatus;

extern FetchStatus FETCH;
extern const char *fetch_url_override;   /* the desktop build's --download-url */

bool fetch_start(void);   /* main thread */
void fetch_poll(void);    /* main thread, every frame */
void fetch_stop(void);    /* at exit */
