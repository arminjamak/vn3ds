#pragma once
#include "common.h"

#define NET_PORT 5555

typedef struct {
    bool listening, receiving, engine_updated;
    int port;
    char address[32];
    char message[160];
    char current[300];
    char last_game[64];
    u32 files_total, files_done, refused, completed;
    u64 bytes_total, bytes_done;
} NetStatus;

extern NetStatus NET;

bool net_start(int port);
void net_stop(void);
/* Accept connections; call once per frame while receiving. Each transfer
 * then runs on its own thread and updates NET as it goes. */
void net_poll(void);
