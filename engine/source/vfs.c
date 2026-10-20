/* Loose files and pack files behind one interface; see vfs.h. */

#include "vfs.h"

#ifdef __3DS__
#include <3ds.h>
typedef Handle PackHandle;
#define PACK_NONE 0
#else
#include <fcntl.h>
#include <unistd.h>
typedef int PackHandle;
#define PACK_NONE (-1)
#endif

#define MAX_PACKS 4096
#define VBUF 32768   /* read-ahead per open file: Ogg pages and video frames are small */

typedef struct {
    const char *name;   /* in names[] */
    u32 pack, offset, size;
} Entry;

static struct {
    char dir[400];
    size_t dirlen;
    PackHandle *h;
    char **pack_names;
    u32 npacks;
    Entry *e;
    u32 ne;
    u32 *slots;   /* open addressing: index + 1, 0 = empty */
    u32 nslots;
    char *names;
    u32 gen;      /* bumped on every mount and unmount */
} V;

struct VFile {
    FILE *fp;     /* a loose file */
    s32 pack;     /* else: pack index */
    u32 gen;
    u64 base, size, pos;
    u8 *buf;
    u64 buf_at;
    u32 buf_len;
};

static u32 hash_name(const char *s)
{
    u32 h = 2166136261u;
    while (*s)
        h = (h ^ (u8)*s++) * 16777619u;
    return h;
}

/* ---- the platform's positioned reads ----------------------------------- */

static bool pack_open(const char *path, PackHandle *out)
{
#ifdef __3DS__
    const char *p = strncmp(path, "sdmc:", 5) ? path : path + 5;
    Handle h = 0;
    if (R_FAILED(FSUSER_OpenFileDirectly(&h, ARCHIVE_SDMC, fsMakePath(PATH_EMPTY, ""),
                                         fsMakePath(PATH_ASCII, p), FS_OPEN_READ, 0)))
        return false;
    *out = h;
    return true;
#else
    int fd = open(path, O_RDONLY);
    if (fd < 0)
        return false;
    *out = fd;
    return true;
#endif
}

static void pack_close(PackHandle h)
{
#ifdef __3DS__
    if (h)
        FSFILE_Close(h);
#else
    if (h >= 0)
        close(h);
#endif
}

static size_t pack_read(PackHandle h, u64 off, void *dst, size_t n)
{
    size_t done = 0;
    while (done < n) {
        size_t chunk = n - done > (1u << 20) ? (1u << 20) : n - done;
#ifdef __3DS__
        u32 got = 0;
        if (R_FAILED(FSFILE_Read(h, &got, off + done, (u8 *)dst + done, (u32)chunk)) || got == 0)
            break;
#else
        ssize_t got = pread(h, (u8 *)dst + done, chunk, (off_t)(off + done));
        if (got <= 0)
            break;
#endif
        done += (size_t)got;
    }
    return done;
}

/* ---- the table ---------------------------------------------------------- */

void vfs_unmount(void)
{
    for (u32 i = 0; i < V.npacks; i++) {
        pack_close(V.h[i]);
        free(V.pack_names[i]);
    }
    free(V.h);
    free(V.pack_names);
    free(V.e);
    free(V.slots);
    free(V.names);
    u32 gen = V.gen;
    memset(&V, 0, sizeof(V));
    V.gen = gen + 1;
}

int vfs_packs(void) { return (int)V.npacks; }

const char *vfs_pack_name(int i) { return i >= 0 && (u32)i < V.npacks ? V.pack_names[i] : NULL; }

static const Entry *lookup(const char *path)
{
    if (!V.ne || strncmp(path, V.dir, V.dirlen) || path[V.dirlen] != '/')
        return NULL;
    const char *rel = path + V.dirlen + 1;
    u32 mask = V.nslots - 1;
    for (u32 i = hash_name(rel) & mask;; i = (i + 1) & mask) {
        u32 s = V.slots[i];
        if (!s)
            return NULL;
        if (!strcmp(V.e[s - 1].name, rel))
            return &V.e[s - 1];
    }
}

bool vfs_mount(const char *dir, const u8 *sec, u32 size)
{
    vfs_unmount();
    if (!sec || size < 8)
        return true;
    u64 t0 = platform_us();
    const u8 *p = sec, *end = sec + size;
    u32 np = rd_u32(p);
    p += 4;
    if (np == 0)
        return true;   /* nothing packed */
    if (np > MAX_PACKS)
        goto bad;
    V.h = malloc(sizeof(PackHandle) * np);
    V.pack_names = calloc(np, sizeof(char *));
    if (!V.h || !V.pack_names)
        goto bad;
    for (u32 i = 0; i < np; i++)
        V.h[i] = PACK_NONE;
    for (u32 i = 0; i < np; i++) {
        if (p + 2 > end)
            goto bad;
        u16 len = rd_u16(p);
        p += 2;
        if (p + len > end || len == 0 || len > 200)
            goto bad;
        V.pack_names[i] = malloc(len + 1u);
        if (!V.pack_names[i])
            goto bad;
        memcpy(V.pack_names[i], p, len);
        V.pack_names[i][len] = 0;
        p += len;
        V.npacks = i + 1;
    }
    if (p + 4 > end)
        goto bad;
    u32 ne = rd_u32(p);
    p += 4;
    /* names: at most the rest of the section plus a NUL each */
    if (ne == 0 || ne > (u32)(end - p) / 12)
        goto bad;
    V.e = malloc(sizeof(Entry) * ne);
    V.names = malloc((size_t)(end - p) + ne);
    for (V.nslots = 16; V.nslots < ne * 2; V.nslots <<= 1) {}
    V.slots = calloc(V.nslots, 4);
    if (!V.e || !V.names || !V.slots)
        goto bad;
    char *nm = V.names;
    for (u32 i = 0; i < ne; i++) {
        if (p + 12 > end)
            goto bad;
        u16 pk = rd_u16(p), len = rd_u16(p + 2);
        u32 off = rd_u32(p + 4), sz = rd_u32(p + 8);
        p += 12;
        if (pk >= np || p + len > end || len == 0)
            goto bad;
        memcpy(nm, p, len);
        nm[len] = 0;
        p += len;
        Entry *e = &V.e[i];
        e->name = nm;
        e->pack = pk;
        e->offset = off;
        e->size = sz;
        nm += len + 1;
        u32 mask = V.nslots - 1, k = hash_name(e->name) & mask;
        while (V.slots[k])
            k = (k + 1) & mask;
        V.slots[k] = i + 1;
        V.ne = i + 1;
    }
    for (u32 i = 0; i < np; i++) {
        char full[600];
        snprintf(full, sizeof(full), "%s/%s", dir, V.pack_names[i]);
        if (!pack_open(full, &V.h[i])) {
            LOG("cannot open %s", full);
            goto bad;
        }
    }
    snprintf(V.dir, sizeof(V.dir), "%s", dir);
    V.dirlen = strlen(V.dir);
    V.gen++;
    PERF("vfs: %u packs, %u files mounted in %.1f ms", (unsigned)np, (unsigned)ne,
         (platform_us() - t0) / 1000.0);
    return true;
bad:
    LOG("PACK table of %s is unusable; reading loose files", dir);
    vfs_unmount();
    return false;
}

/* ---- files -------------------------------------------------------------- */

VFile *vf_open(const char *path)
{
    const Entry *e = lookup(path);
    if (e) {
        VFile *f = calloc(1, sizeof(VFile));
        if (!f)
            return NULL;
        f->pack = (s32)e->pack;
        f->gen = V.gen;
        f->base = e->offset;
        f->size = e->size;
        return f;
    }
    FILE *fp = fopen(path, "rb");
    if (!fp)
        return NULL;
    VFile *f = calloc(1, sizeof(VFile));
    if (!f) {
        fclose(fp);
        return NULL;
    }
    f->fp = fp;
    f->pack = -1;
    return f;
}

size_t vf_read(VFile *f, void *buf, size_t n)
{
    if (f->fp)
        return fread(buf, 1, n, f->fp);
    if (f->gen != V.gen || f->pos >= f->size)
        return 0;
    if (n > f->size - f->pos)
        n = (size_t)(f->size - f->pos);
    u8 *out = buf;
    size_t done = 0;
    /* what the read-ahead buffer already holds */
    if (f->buf_len && f->pos >= f->buf_at && f->pos < f->buf_at + f->buf_len) {
        size_t k = (size_t)(f->buf_at + f->buf_len - f->pos);
        if (k > n)
            k = n;
        memcpy(out, f->buf + (f->pos - f->buf_at), k);
        done = k;
        f->pos += k;
    }
    if (done < n) {
        size_t left = n - done;
        if (left >= VBUF) {   /* big reads go straight to the card */
            size_t got = pack_read(V.h[f->pack], f->base + f->pos, out + done, left);
            f->pos += got;
            done += got;
        } else {
            if (!f->buf && !(f->buf = malloc(VBUF)))
                return done;
            u64 want = f->size - f->pos < VBUF ? f->size - f->pos : VBUF;
            size_t got = pack_read(V.h[f->pack], f->base + f->pos, f->buf, (size_t)want);
            f->buf_at = f->pos;
            f->buf_len = (u32)got;
            size_t k = got < left ? got : left;
            memcpy(out + done, f->buf, k);
            f->pos += k;
            done += k;
        }
    }
    return done;
}

int vf_seek(VFile *f, s64 off, int whence)
{
    if (f->fp)
        return fseek(f->fp, (long)off, whence);
    s64 base = whence == SEEK_SET ? 0 : whence == SEEK_CUR ? (s64)f->pos : (s64)f->size;
    s64 to = base + off;
    if (to < 0 || to > (s64)f->size)
        return -1;
    f->pos = (u64)to;
    return 0;
}

s64 vf_tell(VFile *f) { return f->fp ? (s64)ftell(f->fp) : (s64)f->pos; }

s64 vf_size(VFile *f)
{
    if (!f->fp)
        return (s64)f->size;
    long at = ftell(f->fp);
    if (fseek(f->fp, 0, SEEK_END) != 0)
        return -1;
    long n = ftell(f->fp);
    fseek(f->fp, at, SEEK_SET);
    return n;
}

void vf_close(VFile *f)
{
    if (!f)
        return;
    if (f->fp)
        fclose(f->fp);
    free(f->buf);
    free(f);
}

bool vf_exists(const char *path)
{
    if (lookup(path))
        return true;
    FILE *fp = fopen(path, "rb");
    if (fp)
        fclose(fp);
    return fp != NULL;
}

u8 *vf_read_all(const char *path, size_t max, size_t *len)
{
    *len = 0;
    VFile *f = vf_open(path);
    if (!f)
        return NULL;
    s64 n = vf_size(f);
    u8 *buf = n > 0 && (u64)n <= max ? malloc((size_t)n) : NULL;
    if (buf && vf_read(f, buf, (size_t)n) != (size_t)n) {
        free(buf);
        buf = NULL;
    }
    vf_close(f);
    if (buf)
        *len = (size_t)n;
    return buf;
}

bool vf_location(const char *path, char *file, size_t len, u64 *offset, u64 *size)
{
    const Entry *e = lookup(path);
    if (e) {
        snprintf(file, len, "%s/%s", V.dir, V.pack_names[e->pack]);
        *offset = e->offset;
        *size = e->size;
        return true;
    }
    FILE *fp = fopen(path, "rb");
    if (!fp)
        return false;
    fseek(fp, 0, SEEK_END);
    *size = (u64)ftell(fp);
    fclose(fp);
    snprintf(file, len, "%s", path);
    *offset = 0;
    return true;
}
