#pragma once
/* Reading a game's files, loose or from its pack files.
 *
 * A game packed with pack files (game.bin section PACK, see FORMAT.md) keeps
 * its pictures, sounds and videos inside a few big files in pk/: opening a
 * file in a folder of a thousand costs a 3DS a few hundred milliseconds, a
 * seek inside an open pack nothing. vfs_mount() is given that table when the
 * game loads; from then on vf_open() of a path inside the game's folder that
 * the table names reads from the pack (one handle per pack, shared by every
 * thread: reads carry their own offset), and any other path is an ordinary
 * file, so games with loose files load as before.
 *
 * VFile is used like a FILE: one per reader, not shared between threads. */
#include "common.h"

typedef struct VFile VFile;

/* `dir` is the game's folder; `sec` the PACK section (NULL or size 0: the
 * game has loose files only). Returns false if the section is malformed or
 * a pack cannot be opened (the game then falls back to loose files). */
bool vfs_mount(const char *dir, const u8 *sec, u32 size);
void vfs_unmount(void);
/* Number of mounted packs (0 when the game has loose files). */
int vfs_packs(void);
/* Path of pack i relative to the game folder ("pk/0123456789abcdef.pak"). */
const char *vfs_pack_name(int i);

VFile *vf_open(const char *path);
size_t vf_read(VFile *f, void *buf, size_t n);
/* whence: SEEK_SET, SEEK_CUR or SEEK_END. 0 on success. */
int vf_seek(VFile *f, s64 off, int whence);
s64 vf_tell(VFile *f);
s64 vf_size(VFile *f);
void vf_close(VFile *f);
/* True if `path` exists (in a pack or as a file). */
bool vf_exists(const char *path);
/* The whole file in memory (malloc'd; NULL if missing, empty or bigger than
 * `max`). */
u8 *vf_read_all(const char *path, size_t max, size_t *len);
/* Where the bytes of `path` really are: the file holding them and their
 * offset and length in it (the pack, or the file itself with offset 0). */
bool vf_location(const char *path, char *file, size_t len, u64 *offset, u64 *size);
