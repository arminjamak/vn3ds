/* Loose files and pack files behind one interface; see vfs.h. */

#include "vfs.h"

#ifdef __3DS__
#include <3ds.h>
typedef Handle PackHandle;
#define PACK_NONE 0
/* main_3ds.c: a standalone app's packs, inside its .3dsx */
bool appfs_locate(const char *path, Handle *h, u64 *off, u64 *size);
Handle appfs_handle(void);
static LightLock lock;
static void lock_init(void) { LightLock_Init(&lock); }
static void lock_on(void) { LightLock_Lock(&lock); }
static void lock_off(void) { LightLock_Unlock(&lock); }
#else
#include <fcntl.h>
#include <pthread.h>
#include <unistd.h>
typedef int PackHandle;
#define PACK_NONE (-1)
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static void lock_init(void) {}
static void lock_on(void) { pthread_mutex_lock(&lock); }
static void lock_off(void) { pthread_mutex_unlock(&lock); }
#endif

#define MAX_PACKS 4096
/* A 3DS lets a program hold only so many files open, so packs are opened
 * when first read and at most this many stay open, closing the one unused
 * the longest (when an open fails, every idle one, and it tries again). */
#define MAX_OPEN 8
#define VBUF 32768   /* read-ahead per open file: Ogg pages and video frames are small */

typedef struct {
    const char *name;   /* in names[] */
    u32 pack, offset, size;
} Entry;

static struct {
    char dir[400];
    size_t dirlen;
    PackHandle *h;    /* PACK_NONE while closed (see MAX_OPEN) */
    u64 *pack_base;   /* where each pack starts in its file (0, or inside a .3dsx) */
    u16 *refs;        /* reads in progress per pack (an open one isn't closed under them) */
    u32 *last_use;
    u32 nopen, tick;
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

static bool pack_open(const char *path, PackHandle *out, u64 *base)
{
    *base = 0;
#ifdef __3DS__
    u64 size;
    if (appfs_locate(path, out, base, &size))
        return true;
    const char *p = strncmp(path, "sdmc:", 5) ? path : path + 5;
    Handle h = 0;
    Result rc = FSUSER_OpenFileDirectly(&h, ARCHIVE_SDMC, fsMakePath(PATH_EMPTY, ""),
                                        fsMakePath(PATH_ASCII, p), FS_OPEN_READ, 0);
    if (R_FAILED(rc)) {
        LOG("cannot open %s (FS result 0x%08lX)", path, (unsigned long)rc);
        return false;
    }
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
    if (h && h != appfs_handle())
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

static void ensure_lock(void)
{
    static bool ready;   /* (first used on the main thread, before any reader) */
    if (!ready) {
        lock_init();
        ready = true;
    }
}

void vfs_unmount(void)
{
    ensure_lock();
    lock_on();
    for (u32 i = 0; i < V.npacks; i++) {
        if (V.h && V.h[i] != PACK_NONE)
            pack_close(V.h[i]);
        free(V.pack_names[i]);
    }
    free(V.h);
    free(V.pack_base);
    free(V.refs);
    free(V.last_use);
    free(V.pack_names);
    free(V.e);
    free(V.slots);
    free(V.names);
    u32 gen = V.gen;
    memset(&V, 0, sizeof(V));
    V.gen = gen + 1;
    lock_off();
}

static bool shared_handle(u32 i)
{
    /* a standalone app's packs live in its .3dsx: one handle, never closed */
#ifdef __3DS__
    return V.h[i] != PACK_NONE && V.h[i] == appfs_handle();
#else
    (void)i;
    return false;
#endif
}

/* An open handle for pack i, counted as in use until release(i); NULL-like
 * PACK_NONE if it can't be opened. */
static PackHandle acquire(u32 i, u32 gen)
{
    lock_on();
    if (gen != V.gen || !V.h || i >= V.npacks) {   /* unmounted meanwhile */
        lock_off();
        return PACK_NONE;
    }
    if (V.h[i] == PACK_NONE) {
        if (V.nopen >= MAX_OPEN) {   /* make room: the idle one unused the longest */
            s32 victim = -1;
            for (u32 k = 0; k < V.npacks; k++)
                if (V.h[k] != PACK_NONE && !V.refs[k] && !shared_handle(k) &&
                    (victim < 0 || V.last_use[k] < V.last_use[victim]))
                    victim = (s32)k;
            if (victim >= 0) {
                pack_close(V.h[victim]);
                V.h[victim] = PACK_NONE;
                V.nopen--;
            }
        }
        char full[600];
        snprintf(full, sizeof(full), "%s/%s", V.dir, V.pack_names[i]);
        u64 base;
        if (!pack_open(full, &V.h[i], &base)) {
            /* out of handles? close every idle pack and try once more */
            for (u32 k = 0; k < V.npacks; k++)
                if (k != i && V.h[k] != PACK_NONE && !V.refs[k] && !shared_handle(k)) {
                    pack_close(V.h[k]);
                    V.h[k] = PACK_NONE;
                    V.nopen--;
                }
            if (!pack_open(full, &V.h[i], &base)) {
                V.h[i] = PACK_NONE;
                lock_off();
                return PACK_NONE;
            }
        }
        if (!shared_handle(i))
            V.nopen++;
    }
    V.refs[i]++;
    V.last_use[i] = ++V.tick;
    PackHandle h = V.h[i];
    lock_off();
    return h;
}

static void release(u32 i)
{
    lock_on();
    if (V.refs && i < V.npacks && V.refs[i])
        V.refs[i]--;
    lock_off();
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
    V.pack_base = calloc(np, sizeof(u64));
    V.pack_names = calloc(np, sizeof(char *));
    V.refs = calloc(np, sizeof(u16));
    V.last_use = calloc(np, sizeof(u32));
    if (!V.h || !V.pack_base || !V.pack_names || !V.refs || !V.last_use)
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
    /* Packs are opened when first read (see MAX_OPEN); a standalone app's,
     * inside its .3dsx, are located now (that costs no file handle). A pack
     * missing on the card only loses its own files. */
    for (u32 i = 0; i < np; i++) {
        V.h[i] = PACK_NONE;
#ifdef __3DS__
        char full[600];
        snprintf(full, sizeof(full), "%s/%s", dir, V.pack_names[i]);
        u64 size;
        Handle h;
        if (appfs_locate(full, &h, &V.pack_base[i], &size))
            V.h[i] = h;
#endif
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
        f->base = V.pack_base[e->pack] + e->offset;
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
        PackHandle h = acquire((u32)f->pack, f->gen);
        if (h == PACK_NONE)
            return done;
        if (left >= VBUF) {   /* big reads go straight to the card */
            size_t got = pack_read(h, f->base + f->pos, out + done, left);
            release((u32)f->pack);
            f->pos += got;
            done += got;
        } else {
            if (!f->buf && !(f->buf = malloc(VBUF))) {
                release((u32)f->pack);
                return done;
            }
            u64 want = f->size - f->pos < VBUF ? f->size - f->pos : VBUF;
            size_t got = pack_read(h, f->base + f->pos, f->buf, (size_t)want);
            release((u32)f->pack);
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
