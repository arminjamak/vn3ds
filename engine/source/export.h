#pragma once
/* "Export as app": a game of the library as a .3dsx of its own, made on the
 * console (tools/vnpack/app3dsx.py does the same on a computer, byte for byte
 * in the romfs). The engine's .3dsx is copied with a new SMDH (the game's
 * title, an icon from its cover.thm) and the game folder appended as its
 * romfs at games/<id>/; the app opens that game on start (main_3ds.c). */
#include "common.h"

typedef void (*ExportProgress)(u64 done, u64 total, void *ud);

bool export_app(const char *engine_3dsx, const char *game_dir, const char *id,
                const char *title, const char *author, const char *out_path,
                ExportProgress progress, void *ud, char *err, size_t errlen);
