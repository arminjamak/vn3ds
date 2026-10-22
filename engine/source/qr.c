/* A small QR code encoder; see qr.h. The steps follow the standard (and
 * Project Nayuki's clear write-up of it): bits, Reed-Solomon blocks,
 * function patterns, the zigzag placement, masking, format and version
 * information. */

#include "qr.h"

/* level M, versions 1-10 */
static const u8 ECC_PER_BLOCK[11] = {0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26};
static const u8 NUM_BLOCKS[11] = {0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5};

typedef struct {
    int size;
    u8 *m;      /* modules */
    u8 fn[QR_MAX_SIZE * QR_MAX_SIZE];   /* 1: part of a function pattern */
} Qr;

static void set_fn(Qr *q, int x, int y, bool dark)
{
    q->m[y * q->size + x] = dark;
    q->fn[y * q->size + x] = 1;
}

static int raw_modules(int ver)   /* data + ECC modules of a version */
{
    int r = (16 * ver + 128) * ver + 64;
    if (ver >= 2) {
        int n = ver / 7 + 2;
        r -= (25 * n - 10) * n - 55;
        if (ver >= 7)
            r -= 36;
    }
    return r;
}

static int data_codewords(int ver) { return raw_modules(ver) / 8 - ECC_PER_BLOCK[ver] * NUM_BLOCKS[ver]; }

/* ---- Reed-Solomon over GF(256), polynomial 0x11D ---- */

static u8 gf_mul(u8 a, u8 b)
{
    int z = 0;
    for (int i = 7; i >= 0; i--) {
        z = (z << 1) ^ ((z >> 7) * 0x11D);
        z ^= ((b >> i) & 1) * a;
    }
    return (u8)z;
}

static void rs_divisor(int degree, u8 *out)
{
    memset(out, 0, (size_t)degree);
    out[degree - 1] = 1;
    u8 root = 1;
    for (int i = 0; i < degree; i++) {
        for (int j = 0; j < degree; j++) {
            out[j] = gf_mul(out[j], root);
            if (j + 1 < degree)
                out[j] ^= out[j + 1];
        }
        root = gf_mul(root, 2);
    }
}

static void rs_remainder(const u8 *data, int len, const u8 *div, int degree, u8 *out)
{
    memset(out, 0, (size_t)degree);
    for (int i = 0; i < len; i++) {
        u8 f = data[i] ^ out[0];
        memmove(out, out + 1, (size_t)degree - 1);
        out[degree - 1] = 0;
        for (int j = 0; j < degree; j++)
            out[j] ^= gf_mul(div[j], f);
    }
}

/* ---- function patterns ---- */

static void finder(Qr *q, int cx, int cy)
{
    for (int dy = -4; dy <= 4; dy++)
        for (int dx = -4; dx <= 4; dx++) {
            int x = cx + dx, y = cy + dy;
            if (x < 0 || y < 0 || x >= q->size || y >= q->size)
                continue;
            int d = abs(dx) > abs(dy) ? abs(dx) : abs(dy);
            set_fn(q, x, y, d != 2 && d != 4);
        }
}

static void alignment(Qr *q, int cx, int cy)
{
    for (int dy = -2; dy <= 2; dy++)
        for (int dx = -2; dx <= 2; dx++) {
            int d = abs(dx) > abs(dy) ? abs(dx) : abs(dy);
            set_fn(q, cx + dx, cy + dy, d != 1);
        }
}

static int align_positions(int ver, int size, int *out)
{
    if (ver == 1)
        return 0;
    int n = ver / 7 + 2;
    int step = (ver * 4 + n * 2 + 1) / (n * 2 - 2) * 2;
    out[0] = 6;
    for (int i = n - 1, pos = size - 7; i >= 1; i--, pos -= step)
        out[i] = pos;
    return n;
}

static void format_bits(Qr *q, int mask)
{
    int data = (0 << 3) | mask;   /* level M is 00 */
    int rem = data;
    for (int i = 0; i < 10; i++)
        rem = (rem << 1) ^ ((rem >> 9) * 0x537);
    int bits = ((data << 10) | rem) ^ 0x5412;
    int s = q->size;
#define FBIT(i) (((bits) >> (i)) & 1)
    for (int i = 0; i <= 5; i++)
        set_fn(q, 8, i, FBIT(i));
    set_fn(q, 8, 7, FBIT(6));
    set_fn(q, 8, 8, FBIT(7));
    set_fn(q, 7, 8, FBIT(8));
    for (int i = 9; i < 15; i++)
        set_fn(q, 14 - i, 8, FBIT(i));
    for (int i = 0; i < 8; i++)
        set_fn(q, s - 1 - i, 8, FBIT(i));
    for (int i = 8; i < 15; i++)
        set_fn(q, 8, s - 15 + i, FBIT(i));
#undef FBIT
    set_fn(q, 8, s - 8, true);   /* the dark module */
}

static void function_patterns(Qr *q, int ver)
{
    int s = q->size;
    for (int i = 0; i < s; i++) {   /* timing */
        set_fn(q, 6, i, i % 2 == 0);
        set_fn(q, i, 6, i % 2 == 0);
    }
    finder(q, 3, 3);
    finder(q, s - 4, 3);
    finder(q, 3, s - 4);
    int pos[7], n = align_positions(ver, s, pos);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            if (!((i == 0 && j == 0) || (i == 0 && j == n - 1) || (i == n - 1 && j == 0)))
                alignment(q, pos[i], pos[j]);
    format_bits(q, 0);   /* reserves the area; drawn for real after masking */
    if (ver >= 7) {
        int rem = ver;
        for (int i = 0; i < 12; i++)
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25);
        long bits = (long)ver << 12 | rem;
        for (int i = 0; i < 18; i++) {
            bool b = (bits >> i) & 1;
            int a = s - 11 + i % 3, c = i / 3;
            set_fn(q, a, c, b);
            set_fn(q, c, a, b);
        }
    }
}

/* ---- data ---- */

static void place(Qr *q, const u8 *data, int len)
{
    int s = q->size, i = 0;
    for (int right = s - 1; right >= 1; right -= 2) {
        if (right == 6)
            right = 5;
        for (int vert = 0; vert < s; vert++)
            for (int j = 0; j < 2; j++) {
                int x = right - j;
                bool up = ((right + 1) & 2) == 0;
                int y = up ? s - 1 - vert : vert;
                if (!q->fn[y * s + x] && i < len * 8) {
                    q->m[y * s + x] = (data[i >> 3] >> (7 - (i & 7))) & 1;
                    i++;
                }
            }
    }
}

static bool mask_bit(int mask, int x, int y)
{
    switch (mask) {
    case 0: return (x + y) % 2 == 0;
    case 1: return y % 2 == 0;
    case 2: return x % 3 == 0;
    case 3: return (x + y) % 3 == 0;
    case 4: return (x / 3 + y / 2) % 2 == 0;
    case 5: return x * y % 2 + x * y % 3 == 0;
    case 6: return (x * y % 2 + x * y % 3) % 2 == 0;
    default: return ((x + y) % 2 + x * y % 3) % 2 == 0;
    }
}

static void apply_mask(Qr *q, int mask)
{
    for (int y = 0; y < q->size; y++)
        for (int x = 0; x < q->size; x++)
            if (!q->fn[y * q->size + x] && mask_bit(mask, x, y))
                q->m[y * q->size + x] ^= 1;
}

/* The standard's four penalty rules (lower is easier to scan). */
static long penalty(const Qr *q)
{
    int s = q->size;
    long p = 0;
    for (int pass = 0; pass < 2; pass++)
        for (int a = 0; a < s; a++) {
            int run = 0, prev = -1;
            u32 window = 0;   /* the last 11 modules, for the finder-like rule */
            for (int b = 0; b < s; b++) {
                int v = pass ? q->m[b * s + a] : q->m[a * s + b];
                if (v == prev) {
                    if (++run == 5)
                        p += 3;
                    else if (run > 5)
                        p++;
                } else {
                    run = 1;
                    prev = v;
                }
                window = ((window << 1) | (u32)v) & 0x7FF;
                if (b >= 10 && (window == 0x5D0 || window == 0x05D))   /* 10111010000 / 00001011101 */
                    p += 40;
            }
        }
    for (int y = 0; y + 1 < s; y++)
        for (int x = 0; x + 1 < s; x++) {
            int c = q->m[y * s + x];
            if (c == q->m[y * s + x + 1] && c == q->m[(y + 1) * s + x] && c == q->m[(y + 1) * s + x + 1])
                p += 3;
        }
    int dark = 0, total = s * s;
    for (int i = 0; i < total; i++)
        dark += q->m[i];
    int k = (abs(dark * 20 - total * 10) + total - 1) / total - 1;
    return p + k * 10;
}

int qr_encode(const char *text, int mask, u8 out[QR_MAX_SIZE * QR_MAX_SIZE])
{
    int len = (int)strlen(text), ver;
    for (ver = 1; ver <= 10; ver++)
        if (4 + (ver < 10 ? 8 : 16) + len * 8 <= data_codewords(ver) * 8)
            break;
    if (ver > 10)
        return 0;
    int cap = data_codewords(ver);
    u8 data[400];
    memset(data, 0, sizeof(data));
    int bit = 0;
#define PUT(v, n) do { for (int _i = (n) - 1; _i >= 0; _i--, bit++) \
    if (((v) >> _i) & 1) data[bit >> 3] |= (u8)(0x80 >> (bit & 7)); } while (0)
    PUT(4, 4);   /* byte mode */
    PUT(len, ver < 10 ? 8 : 16);
    for (int i = 0; i < len; i++)
        PUT((u8)text[i], 8);
    int term = cap * 8 - bit < 4 ? cap * 8 - bit : 4;
    bit += term;
    bit = (bit + 7) & ~7;
#undef PUT
    for (int i = bit / 8, pad = 0xEC; i < cap; i++, pad ^= 0xEC ^ 0x11)
        data[i] = (u8)pad;

    /* blocks and their ECC, interleaved */
    int nb = NUM_BLOCKS[ver], ecc = ECC_PER_BLOCK[ver];
    int raw = raw_modules(ver) / 8, nshort = nb - raw % nb, short_len = raw / nb;
    u8 div[30], blocks[5][160], all[400];
    rs_divisor(ecc, div);
    for (int i = 0, k = 0; i < nb; i++) {
        int dlen = short_len - ecc + (i < nshort ? 0 : 1);
        u8 *b = blocks[i];
        memcpy(b, data + k, (size_t)dlen);
        k += dlen;
        int at = dlen;
        if (i < nshort)
            b[at++] = 0;   /* a gap, so every block has the same layout */
        rs_remainder(data + k - dlen, dlen, div, ecc, b + at);
    }
    int n = 0;
    for (int i = 0; i <= short_len; i++)
        for (int j = 0; j < nb; j++)
            if (i != short_len - ecc || j >= nshort)
                all[n++] = blocks[j][i];

    static Qr q;
    memset(&q, 0, sizeof(q));
    q.size = ver * 4 + 17;
    q.m = out;
    memset(out, 0, (size_t)q.size * q.size);
    function_patterns(&q, ver);
    place(&q, all, n);
    if (mask < 0) {
        long best = -1;
        for (int t = 0; t < 8; t++) {
            apply_mask(&q, t);
            format_bits(&q, t);
            long p = penalty(&q);
            if (best < 0 || p < best) {
                best = p;
                mask = t;
            }
            apply_mask(&q, t);   /* (XOR: undone) */
        }
    }
    apply_mask(&q, mask);
    format_bits(&q, mask);
    return q.size;
}
