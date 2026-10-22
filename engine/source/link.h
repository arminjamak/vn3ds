#pragma once
/* App linking: vn3ds and the novels exported as apps of their own
 * (vn3ds-port --app) jump to each other and share where you are reading.
 *
 * Jumps (platform_launch) use Luma3DS's homebrew loader: a .3dsx names the
 * next .3dsx and its arguments on Rosalina's hb:ldr port, then exits, and
 * Luma starts that one (what the Homebrew Launcher itself does). Where that
 * isn't possible (vn3ds installed as a CIA, an older homebrew setup), the
 * player is told which app to open and the record below carries the rest.
 *
 * sdmc:/3ds/vn3ds/reading.cfg   what is being read, written by both sides:
 *     id=<game id>  title=<title>  app=<.3dsx of a standalone app, or empty
 *     for vn3ds's library>  slot=<save slot to carry on from>  time=<unix>
 * sdmc:/3ds/<id>/app.cfg        a standalone app, for vn3ds's library:
 *     id=  title=  app=   (with cover.thm beside it; saves in saves/<id>/)
 *
 * Arguments: an app started with "--continue" carries on from its resume
 * save; vn3ds started with "--from <id>" shows that game's card. */
#include "common.h"

typedef struct {
    char id[64];
    char title[96];
    char app[256];   /* "" = in vn3ds's library */
    int slot;
    u32 time;
} Reading;

bool link_read(Reading *r);
/* The current game is being read here (on opening it and every autosave). */
void link_note_reading(bool background);
/* vn3ds.3dsx on the card (sdmc:/3ds/vn3ds.3dsx or sdmc:/3ds/vn3ds/vn3ds.3dsx), or NULL. */
const char *link_vn3ds_path(void);
/* A standalone app: registers itself for vn3ds's library (app.cfg, cover). */
void link_register_app(void);
/* The same for an app made elsewhere (an export): sdmc:/3ds/<id>/app.cfg. */
void link_register(const char *id, const char *title, const char *app, const char *cover);
/* Calls cb for each registered standalone app (id, title, .3dsx, its folder). */
void link_scan_apps(void (*cb)(const char *id, const char *title, const char *app,
                               const char *dir, void *ud), void *ud);
/* Jumps to another .3dsx with these arguments; the caller then quits.
 * False when this setup can't (then tell the player what to open). */
bool link_launch(const char *app, const char *arg1, const char *arg2);
/* The arguments this app was started with ("--continue", "--from id"). */
void link_take_args(int argc, char **argv);
extern bool link_continue;          /* "--continue" */
extern char link_from[64];          /* "--from <id>" */
