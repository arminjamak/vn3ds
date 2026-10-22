/* A library game as a .3dsx of its own; see export.h and
 * tools/vnpack/app3dsx.py (the romfs is laid out the same way: each folder's
 * folders and files by name, folders depth first, data 16-byte aligned). */

#include "export.h"

#include <dirent.h>
#include <stdarg.h>
#include <sys/stat.h>

#define UNUSED 0xFFFFFFFFu
#define SMDH_SIZE 0x36C0
#define COPY_BUF (256 * 1024)

typedef struct {
    char *name;   /* UTF-8 */
    int parent;
    int *dirs, ndirs;
    int *files, nfiles;
    u32 off;
} XDir;

typedef struct {
    char *name, *src;
    int dir;
    u64 size, data;
    u32 off;
} XFile;

typedef struct {
    XDir *d;
    int nd, cd;
    XFile *f;
    int nf, cf;
    char *err;
    size_t errlen;
} Tree;

static void say(Tree *t, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(t->err, t->errlen, fmt, ap);
    va_end(ap);
}

static int push_int(int **a, int *n, int v)
{
    int *g = realloc(*a, sizeof(int) * (size_t)(*n + 1));
    if (!g)
        return -1;
    *a = g;
    (*a)[(*n)++] = v;
    return 0;
}

static int cmp_str(const void *a, const void *b)
{
    return strcmp(*(char *const *)a, *(char *const *)b);
}

/* UTF-8 name -> UTF-16 units (returns the count). */
static int utf16(const char *s, u16 *out, int max)
{
    int n = 0;
    const u8 *p = (const u8 *)s;
    while (*p && n < max) {
        u32 c = *p++;
        if (c >= 0xF0 && p[0] && p[1] && p[2]) {
            c = ((c & 7) << 18) | ((p[0] & 63u) << 12) | ((p[1] & 63u) << 6) | (p[2] & 63u);
            p += 3;
        } else if (c >= 0xE0 && p[0] && p[1]) {
            c = ((c & 15) << 12) | ((p[0] & 63u) << 6) | (p[1] & 63u);
            p += 2;
        } else if (c >= 0xC0 && p[0]) {
            c = ((c & 31) << 6) | (p[0] & 63u);
            p += 1;
        }
        if (c >= 0x10000) {
            if (n + 2 > max)
                break;
            c -= 0x10000;
            out[n++] = (u16)(0xD800 | (c >> 10));
            out[n++] = (u16)(0xDC00 | (c & 0x3FF));
        } else {
            out[n++] = (u16)c;
        }
    }
    return n;
}

/* The folder at `path` into dir `di` (names sorted, as the Python side). */
static bool scan(Tree *t, const char *path, int di)
{
    DIR *dh = opendir(path);
    if (!dh) {
        say(t, "can't read %s", path);
        return false;
    }
    char **names = NULL;
    int n = 0;
    struct dirent *e;
    while ((e = readdir(dh))) {
        const char *nm = e->d_name;
        size_t l = strlen(nm);
        if (nm[0] == '.' || !strcmp(nm, "port-report.txt") || !strcmp(nm, "savemap.json") ||
            (l > 5 && !strcmp(nm + l - 5, ".part")))
            continue;
        char **g = realloc(names, sizeof(char *) * (size_t)(n + 1));
        if (!g)
            break;
        names = g;
        names[n++] = strdup(nm);
    }
    closedir(dh);
    qsort(names, (size_t)n, sizeof(char *), cmp_str);
    bool ok = true;
    for (int i = 0; i < n && ok; i++) {
        char full[600];
        snprintf(full, sizeof(full), "%s/%s", path, names[i]);
        struct stat st;
        if (stat(full, &st) != 0)
            continue;
        if (S_ISDIR(st.st_mode)) {
            if (t->nd == t->cd) {
                t->cd = t->cd ? t->cd * 2 : 16;
                XDir *g = realloc(t->d, sizeof(XDir) * (size_t)t->cd);
                if (!g) {
                    ok = false;
                    break;
                }
                t->d = g;
            }
            int ci = t->nd++;
            memset(&t->d[ci], 0, sizeof(XDir));
            t->d[ci].name = strdup(names[i]);
            t->d[ci].parent = di;
            push_int(&t->d[di].dirs, &t->d[di].ndirs, ci);
            ok = scan(t, full, ci);
        } else {
            if (t->nf == t->cf) {
                t->cf = t->cf ? t->cf * 2 : 64;
                XFile *g = realloc(t->f, sizeof(XFile) * (size_t)t->cf);
                if (!g) {
                    ok = false;
                    break;
                }
                t->f = g;
            }
            int fi = t->nf++;
            memset(&t->f[fi], 0, sizeof(XFile));
            t->f[fi].name = strdup(names[i]);
            t->f[fi].src = strdup(full);
            t->f[fi].dir = di;
            t->f[fi].size = (u64)st.st_size;
            push_int(&t->d[di].files, &t->d[di].nfiles, fi);
        }
    }
    for (int i = 0; i < n; i++)
        free(names[i]);
    free(names);
    if (!ok && !t->err[0])
        say(t, "out of memory");
    return ok;
}

/* folders depth first from d, into order[] */
static void preorder(Tree *t, int d, int *order, int *n)
{
    order[(*n)++] = d;
    for (int i = 0; i < t->d[d].ndirs; i++)
        preorder(t, t->d[d].dirs[i], order, n);
}

static u32 table_len(u32 count)
{
    if (count < 3)
        return 3;
    if (count < 19)
        return count | 1;
    static const u32 primes[] = {2, 3, 5, 7, 11, 13, 17};
    for (;; count++) {
        int ok = 1;
        for (int i = 0; i < 7; i++)
            if (count % primes[i] == 0)
                ok = 0;
        if (ok)
            return count;
    }
}

static u32 name_hash(u32 parent, const u16 *name, int n, u32 total)
{
    u32 h = parent ^ 123456789u;
    for (int i = 0; i < n; i++) {
        h = (h >> 5) | (h << 27);
        h ^= name[i];
    }
    return h % total;
}

static void put32(u8 *p, u32 v) { memcpy(p, &v, 4); }
static void put64(u8 *p, u64 v) { memcpy(p, &v, 8); }

/* ---- SMDH ---------------------------------------------------------------- */

static void smdh_text(u8 *dst, const char *s, int chars)
{
    u16 buf[256];
    int n = utf16(s, buf, chars - 1);
    memset(dst, 0, (size_t)chars * 2);
    memcpy(dst, buf, (size_t)n * 2);
}

/* size x size icon from the middle of cover.thm (RGB565, 200x120), tiled. */
static void smdh_icon(u8 *dst, const u16 *px, int w, int h, int size)
{
    int side = w < h ? w : h, x0 = (w - side) / 2, y0 = (h - side) / 2;
    for (int i = 0; i < size * size; i++) {
        int tile = i / 64, k = i % 64;
        int tx = (tile % (size / 8)) * 8, ty = (tile / (size / 8)) * 8;
        int x = tx + ((k & 1) | ((k >> 1) & 2) | ((k >> 2) & 4));
        int y = ty + (((k >> 1) & 1) | ((k >> 2) & 2) | ((k >> 3) & 4));
        u32 r = 0, g = 0, b = 0, n = 0;   /* the area this icon pixel covers */
        int sx0 = x0 + x * side / size, sx1 = x0 + (x + 1) * side / size;
        int sy0 = y0 + y * side / size, sy1 = y0 + (y + 1) * side / size;
        for (int sy = sy0; sy < sy1; sy++)
            for (int sx = sx0; sx < sx1; sx++) {
                u16 v = px[sy * w + sx];
                r += v >> 11;
                g += (v >> 5) & 63;
                b += v & 31;
                n++;
            }
        u16 v = n ? (u16)(((r / n) << 11) | ((g / n) << 5) | (b / n)) : 0;
        memcpy(dst + i * 2, &v, 2);
    }
}

static void make_smdh(u8 *smdh, const u8 *base, const char *title, const char *desc,
                      const char *author, const char *cover)
{
    if (base && !memcmp(base, "SMDH", 4)) {
        memcpy(smdh, base, SMDH_SIZE);
    } else {
        memset(smdh, 0, SMDH_SIZE);
        memcpy(smdh, "SMDH", 4);
        put32(smdh + 0x2018, 0x7FFFFFFF);   /* every region */
        put32(smdh + 0x2028, 1);            /* visible */
    }
    for (int lang = 0; lang < 16; lang++) {
        u8 *e = smdh + 8 + lang * 0x200;
        smdh_text(e, title, 0x40);
        smdh_text(e + 0x80, desc, 0x80);
        smdh_text(e + 0x180, author, 0x40);
    }
    FILE *f = fopen(cover, "rb");
    u8 head[8];
    if (f && fread(head, 1, 8, f) == 8 && !memcmp(head, "THM1", 4)) {
        u16 w, h;
        memcpy(&w, head + 4, 2);
        memcpy(&h, head + 6, 2);
        u16 *px = w && h && w <= 512 && h <= 512 ? malloc((size_t)w * h * 2) : NULL;
        if (px && fread(px, 2, (size_t)w * h, f) == (size_t)w * h) {
            smdh_icon(smdh + 0x2040, px, w, h, 24);
            smdh_icon(smdh + 0x24C0, px, w, h, 48);
        }
        free(px);
    }
    if (f)
        fclose(f);
}

/* ---- the .3dsx ------------------------------------------------------------- */

static bool write_all(FILE *o, const void *p, size_t n) { return fwrite(p, 1, n, o) == n; }

static bool pad(FILE *o, u64 n)
{
    static const u8 zero[16];
    while (n) {
        size_t k = n > sizeof(zero) ? sizeof(zero) : (size_t)n;
        if (!write_all(o, zero, k))
            return false;
        n -= k;
    }
    return true;
}

bool export_app(const char *engine_3dsx, const char *game_dir, const char *id,
                const char *title, const char *author, const char *out_path,
                ExportProgress progress, void *ud, char *err, size_t errlen)
{
    Tree t;
    memset(&t, 0, sizeof(t));
    t.err = err;
    t.errlen = errlen;
    err[0] = 0;
    bool ok = false;
    u8 *code = NULL, *base_smdh = NULL, *meta = NULL, *buf = NULL;
    int *order = NULL;
    FILE *in = NULL, *out = NULL;
    char tmp[600];
    snprintf(tmp, sizeof(tmp), "%s.part", out_path);

    /* the engine: code and relocations, and its SMDH's settings */
    in = fopen(engine_3dsx, "rb");
    u32 hdr[11];
    if (!in || fread(hdr, 1, sizeof(hdr), in) != sizeof(hdr) || memcmp(hdr, "3DSX", 4) ||
        (hdr[1] & 0xFFFF) < 0x2C) {
        say(&t, "%s isn't a .3dsx with an extended header", engine_3dsx);
        goto done;
    }
    fseek(in, 0, SEEK_END);
    u32 fsize = (u32)ftell(in), cut = fsize;
    if (hdr[8] && hdr[8] < cut)
        cut = hdr[8];
    if (hdr[10] && hdr[10] < cut)
        cut = hdr[10];
    code = malloc(cut);
    fseek(in, 0, SEEK_SET);
    if (!code || fread(code, 1, cut, in) != cut) {
        say(&t, "can't read %s", engine_3dsx);
        goto done;
    }
    if (hdr[8] && hdr[9] == SMDH_SIZE && (base_smdh = malloc(SMDH_SIZE))) {
        fseek(in, (long)hdr[8], SEEK_SET);
        if (fread(base_smdh, 1, SMDH_SIZE, in) != SMDH_SIZE) {
            free(base_smdh);
            base_smdh = NULL;
        }
    }
    fclose(in);
    in = NULL;

    /* the romfs: games/<id>/ with the game folder in it */
    t.cd = 16;
    t.d = calloc((size_t)t.cd, sizeof(XDir));
    if (!t.d)
        goto done;
    t.nd = 3;
    t.d[0].name = strdup("");
    t.d[1].name = strdup("games");
    t.d[1].parent = 0;
    t.d[2].name = strdup(id);
    t.d[2].parent = 1;
    push_int(&t.d[0].dirs, &t.d[0].ndirs, 1);
    push_int(&t.d[1].dirs, &t.d[1].ndirs, 2);
    if (!scan(&t, game_dir, 2))
        goto done;
    order = malloc(sizeof(int) * (size_t)t.nd);
    int no = 0;
    preorder(&t, 0, order, &no);

    u16 nm[256];
    u32 dsize = 0, fsize_t = 0;
    for (int i = 0; i < no; i++) {
        XDir *d = &t.d[order[i]];
        d->off = dsize;
        dsize += 0x18 + (((u32)utf16(d->name, nm, 255) * 2 + 3) & ~3u);
    }
    u64 data = 0;
    int nfiles = 0;
    for (int i = 0; i < no; i++) {
        XDir *d = &t.d[order[i]];
        for (int k = 0; k < d->nfiles; k++) {
            XFile *f = &t.f[d->files[k]];
            f->off = fsize_t;
            fsize_t += 0x20 + (((u32)utf16(f->name, nm, 255) * 2 + 3) & ~3u);
            data = (data + 15) & ~(u64)15;
            f->data = data;
            data += f->size;
            nfiles++;
        }
    }
    u32 nd = table_len((u32)no), nf = table_len((u32)nfiles);
    u32 dh_off = 0x28, dt_off = dh_off + nd * 4, fh_off = dt_off + dsize, ft_off = fh_off + nf * 4;
    u32 data_off = (ft_off + fsize_t + 15) & ~15u;
    meta = calloc(1, data_off);
    if (!meta) {
        say(&t, "out of memory");
        goto done;
    }
    u32 hv[10] = {0x28, dh_off, nd * 4, dt_off, dsize, fh_off, nf * 4, ft_off, fsize_t, data_off};
    memcpy(meta, hv, sizeof(hv));
    memset(meta + dh_off, 0xFF, nd * 4);
    memset(meta + fh_off, 0xFF, nf * 4);
    for (int i = 0; i < no; i++) {   /* folders: hash chains, then entries */
        XDir *d = &t.d[order[i]];
        int n = utf16(d->name, nm, 255);
        u32 parent = order[i] ? t.d[d->parent].off : 0;
        u32 *slot = (u32 *)(meta + dh_off) + name_hash(parent, nm, n, nd);
        u8 *e = meta + dt_off + d->off;
        u32 sibling = UNUSED;
        if (order[i]) {
            XDir *p = &t.d[d->parent];
            for (int k = 0; k < p->ndirs - 1; k++)
                if (p->dirs[k] == order[i])
                    sibling = t.d[p->dirs[k + 1]].off;
        }
        put32(e, parent);
        put32(e + 4, sibling);
        put32(e + 8, d->ndirs ? t.d[d->dirs[0]].off : UNUSED);
        put32(e + 12, d->nfiles ? t.f[d->files[0]].off : UNUSED);
        put32(e + 16, *slot);
        put32(e + 20, (u32)n * 2);
        memcpy(e + 24, nm, (size_t)n * 2);
        *slot = d->off;
    }
    for (int i = 0; i < no; i++) {
        XDir *d = &t.d[order[i]];
        for (int k = 0; k < d->nfiles; k++) {
            XFile *f = &t.f[d->files[k]];
            int n = utf16(f->name, nm, 255);
            u32 *slot = (u32 *)(meta + fh_off) + name_hash(d->off, nm, n, nf);
            u8 *e = meta + ft_off + f->off;
            put32(e, d->off);
            put32(e + 4, k + 1 < d->nfiles ? t.f[d->files[k + 1]].off : UNUSED);
            put64(e + 8, f->data);
            put64(e + 16, f->size);
            put32(e + 24, *slot);
            put32(e + 28, (u32)n * 2);
            memcpy(e + 32, nm, (size_t)n * 2);
            *slot = f->off;
        }
    }

    /* write it: code (with the new offsets), SMDH, romfs */
    u32 smdh_off = cut, fs_off = (cut + SMDH_SIZE + 3) & ~3u;
    put32(code + 0x20, smdh_off);
    put32(code + 0x24, SMDH_SIZE);
    put32(code + 0x28, fs_off);
    u8 smdh[SMDH_SIZE];
    char cover[600], desc[200];
    snprintf(cover, sizeof(cover), "%s/cover.thm", game_dir);
    snprintf(desc, sizeof(desc), "%s - plays with vn3ds", title);
    make_smdh(smdh, base_smdh, title, desc, author, cover);
    out = fopen(tmp, "wb");
    buf = malloc(COPY_BUF);
    if (!out || !buf) {
        say(&t, "can't write %s", tmp);
        goto done;
    }
    if (!write_all(out, code, cut) || !write_all(out, smdh, SMDH_SIZE) ||
        !pad(out, fs_off - cut - SMDH_SIZE) || !write_all(out, meta, data_off))
        goto wfail;
    u64 pos = 0, done_b = 0;
    for (int i = 0; i < no; i++) {
        XDir *d = &t.d[order[i]];
        for (int k = 0; k < d->nfiles; k++) {
            XFile *f = &t.f[d->files[k]];
            if (!pad(out, f->data - pos))
                goto wfail;
            FILE *src = fopen(f->src, "rb");
            if (!src) {
                say(&t, "can't read %s", f->src);
                goto done;
            }
            u64 left = f->size;
            while (left) {
                size_t want = left > COPY_BUF ? COPY_BUF : (size_t)left;
                size_t got = fread(buf, 1, want, src);
                if (got == 0 || !write_all(out, buf, got)) {
                    fclose(src);
                    goto wfail;
                }
                left -= got;
                done_b += got;
                if (progress)
                    progress(done_b, data, ud);
            }
            fclose(src);
            pos = f->data + f->size;
        }
    }
    if (fclose(out) != 0) {
        out = NULL;
        goto wfail;
    }
    out = NULL;
    remove(out_path);
    if (rename(tmp, out_path) != 0) {
        say(&t, "can't rename %s", tmp);
        goto done;
    }
    ok = true;
    goto done;
wfail:
    say(&t, "can't write %s (is the card full?)", tmp);
done:
    if (in)
        fclose(in);
    if (out)
        fclose(out);
    if (!ok)
        remove(tmp);
    for (int i = 0; i < t.nd; i++) {
        free(t.d[i].name);
        free(t.d[i].dirs);
        free(t.d[i].files);
    }
    for (int i = 0; i < t.nf; i++) {
        free(t.f[i].name);
        free(t.f[i].src);
    }
    free(t.d);
    free(t.f);
    free(order);
    free(code);
    free(base_smdh);
    free(meta);
    free(buf);
    return ok;
}
