#pragma once
#include "common.h"

#define NET_PORT 5555

typedef struct {
    bool listening, receiving, engine_updated;
    bool staged;   /* the last transfer updated the open game (see updates/) */
    int port;
    char address[32];
    char message[160];
    char current[300];
    char last_game[64];
    char game[64];       /* the game the transfer is working on now ("" until known) */
    u32 files_total, files_done, refused, skipped, completed;
    u64 bytes_total, bytes_done;
    u64 bytes_skipped;   /* part of bytes_done that was already on the card */
} NetStatus;

extern NetStatus NET;

bool net_start(int port);
/* Shared, reference-counted socket service (socInit on the 3DS, nothing on
 * the desktop): every successful acquire needs one release. Main thread only. */
bool net_soc_acquire(void);
void net_soc_release(void);
void net_stop(void);
/* The game currently open (NULL for none): its incoming files are staged in
 * <root>/updates/<id>/ and moved into place when it is next loaded. */
void net_set_live_game(const char *id);
/* Accept connections; call once per frame while receiving. Each transfer
 * then runs on its own thread and updates NET as it goes. */
void net_poll(void);
/* A connection this side opened (relay.c: the link to the vn3ds relay) is
 * served by the receiver like one that came in; with websocket, the stream
 * comes in WebSocket frames (see net.c). False while the receiver is busy;
 * the caller keeps the socket then. Main thread. */
bool net_adopt(int fd, bool websocket);
bool net_rx_busy(void);           /* a connection is with the receiver */
void net_tune_socket(int fd);     /* the receive window the 3DS needs */

/* Save sync with a computer (savesync.c). */
enum { SYNC_OPENED = 1, SYNC_SAVED = 2, SYNC_LIBRARY = 3, SYNC_EXIT = 4 };
/* Receiver thread: serves a "VN3S" connection (header: its first 20 bytes). */
void sync_session(int fd, const u8 header[20]);
/* Main thread: a save was written to slot (nudges the computer soon). */
void sync_note_saved(int slot);
/* Main thread: vn3ds opened, a game closed, or vn3ds is exiting (then it
 * waits a few seconds for the computer if it has saves the computer lacks). */
void sync_event(u32 reason);
/* Main thread, every frame: sends due nudges; true when a sync changed saves. */
bool sync_poll(void);
u32 sync_sessions(void);
