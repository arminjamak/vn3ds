#pragma once
#include "common.h"

/* Online minigame leaderboard client (server: server/leaderboard/).
 *
 * Plain HTTP/1.0 over BSD sockets, each request on a background thread so
 * the UI never waits. There are two request slots, one for posting a score
 * and one for fetching a top list; each goes idle -> busy -> done/failed and
 * keeps its result until the next request on it.
 *
 * Settings: the server URL is LEADERBOARD_URL (leaderboard_config.h) unless
 * leaderboard.cfg in the vn3ds root has a `url = http://...` line (an empty
 * one turns the leaderboard off). The same file keeps `player = <id>`, a
 * random id made once per console so players with the same name stay
 * apart, and may set `name = ...` to override the player name (the 3DS
 * profile nickname; "Desktop" on the desktop build). */

#define LB_TOP_MAX 10
#define LB_NAME_MAX 16

typedef enum { LB_IDLE, LB_BUSY, LB_DONE, LB_FAILED } LbState;

typedef struct {
    int rank, score;
    char name[LB_NAME_MAX + 1];
} LbEntry;

typedef struct {
    volatile LbState state;
    char game[24];          /* the game this request is about */
    int score;              /* posts: the score sent */
    int rank, total;        /* posts, when done: rank of the player's best, entries */
    LbEntry top[LB_TOP_MAX];/* top lists, when done */
    int ntop;
    char error[80];         /* when failed: a short reason for the screen */
} LbJob;

extern LbJob LB_POST, LB_TOP;

/* Reads leaderboard.cfg and the player name; call once E.root is set. */
void lb_init(void);
/* Waits for running requests (they give up quickly once asked to). */
void lb_shutdown(void);
/* Once per frame: tidies up finished requests and starts a queued fetch. */
void lb_poll(void);

bool lb_online(void);           /* a server URL is set */
const char *lb_url(void);
const char *lb_name(void);

/* Sends a finished run's score. False if offline or a post is still busy. */
bool lb_post(const char *game, int score);
/* Fetches the top LB_TOP_MAX for a game into LB_TOP. If a fetch is running
 * it is queued and replaces any earlier queued one. False if offline. */
bool lb_fetch_top(const char *game);
/* True when LB_TOP holds (or is fetching) the list for `game`. */
bool lb_top_is(const char *game);
