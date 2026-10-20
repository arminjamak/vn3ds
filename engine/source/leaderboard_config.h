#pragma once

/* Online leaderboard settings compiled into the engine (see leaderboard.h
 * and server/leaderboard/README.md).
 *
 * LEADERBOARD_URL: the server, e.g. "http://203.0.113.7" (plain HTTP, an
 *   optional :port and path prefix). Empty means offline. A player can
 *   override it with `url = ...` in leaderboard.cfg in the vn3ds folder.
 * LEADERBOARD_KEY: the shared HMAC-SHA256 key that signs submissions. It
 *   must match the server's key. Anyone with the game file can dig it out, so
 *   it only stops casual cheating. The default is the server's public
 *   development key; make a real one with `openssl rand -hex 32` before
 *   deploying. */

/* Release settings (the real key, the server address) live in
 * leaderboard_secret.h, which is kept out of git. */
#if defined(__has_include)
#if __has_include("leaderboard_secret.h")
#include "leaderboard_secret.h"
#endif
#endif

/* The desktop test build never talks to the real server on its own (bots
 * would fill the board); point it at one with leaderboard.cfg instead. */
#ifndef __3DS__
#undef LEADERBOARD_URL
#endif

#ifndef LEADERBOARD_URL
#define LEADERBOARD_URL ""
#endif

#ifndef LEADERBOARD_KEY
#define LEADERBOARD_KEY "vn3ds-dev-key-change-me"
#endif
