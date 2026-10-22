#pragma once
#include "common.h"

/* Games from a browser. vn3ds.com converts a game in the browser and sends
 * it through the vn3ds relay (server/link: a Cloudflare Worker), which
 * passes the bytes to this 3DS over a connection the 3DS opened: it is
 * behind the home router, so nothing can connect to it from outside, and a
 * web page can't open a connection into the home network either.
 *
 * Once the receive screen has been opened (which makes this 3DS's key),
 * vn3ds keeps that link whenever it listens for games:
 *
 *   GET /3ds HTTP/1.1 + WebSocket upgrade, with X-VN3DS-Key: <32 hex>,
 *   X-VN3DS-Name: <profile nickname>, X-VN3DS-Version: 1
 *
 * then binary frames carry the receiver protocol of net.c (VN3D 4) both
 * ways, exactly as from vn3ds-port, and text frames the link's own words
 * ("ping"/"pong", "ack <bytes>"). The page finds this 3DS by itself when
 * both are behind the same router (the relay sees the same public
 * address); anywhere else, the QR code or the code on screen says which.
 *
 * relay.cfg in the vn3ds folder:
 *   key = <32 hex digits, made on first use: the code is derived from it>
 *   server = link.vn3ds.com:80        (optional; "server =" turns it off)
 *   web = https://vn3ds.com           (optional: the page the QR code opens)
 */
#define RELAY_SERVER "link.vn3ds.com"
#define RELAY_PORT 80
#define RELAY_WEB "https://vn3ds.com"

typedef enum { RELAY_OFF, RELAY_TRYING, RELAY_ONLINE, RELAY_UNREACHABLE } RelayState;

typedef struct {
    RelayState state;
    char code[9];      /* "ABCD2345" */
    char url[160];     /* what the QR code holds: <web>/#<code> */
    char web[128];     /* the address to type, without https:// */
} RelayStatus;

extern RelayStatus RELAY;

/* Main thread. The receive screen calls relay_pair (makes the key the
 * first time, and from then on vn3ds links up whenever it listens). */
void relay_pair(void);
void relay_poll(void);   /* every frame */
void relay_stop(void);   /* before the socket service goes away */
/* The code as shown: "ABCD 2345". */
void relay_code_text(char *out, size_t len);
/* The pairing code of a key (the server does the same). */
void relay_code_of(const char *key, char out[9]);
