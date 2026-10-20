/* Compact baseline JPEG decoder, see jpeg.h.
 *
 * Pass 1 entropy-decodes the whole image into one 8-bit plane per component.
 * Huffman codes are read through a 9-bit lookahead table (which also yields
 * small AC values directly), and each block goes through jidctint's integer
 * IDCT, skipping the columns and rows the decoded coefficients show to be
 * zero. Pass 2 upsamples the chroma and writes 8x8 PICA200 tiles directly;
 * 4:2:0 has its own faster path. Temporary memory is about 1.5 bytes per pixel
 * for 4:2:0 (3 for 4:4:4) and is freed before returning.
 *
 * On an Old 3DS (268 MHz ARM11) a 427x240 4:2:0 picture of 10-25 KB is roughly
 * 5-7 million instructions: about 20-40 ms. */

#include "jpeg.h"

#include <stdlib.h>
#include <string.h>

#if defined(__ARM_FEATURE_SAT) && __ARM_FEATURE_SAT
#include <arm_acle.h> /* SSAT / USAT on ARMv6 */
#define SSAT(v, bits) __ssat((v), (bits))
#define USAT(v, bits) __usat((v), (bits))
#else
static inline int SSAT(int v, int bits)
{
    int hi = (1 << (bits - 1)) - 1;
    return v < -hi - 1 ? -hi - 1 : v > hi ? hi : v;
}
static inline int USAT(int v, int bits)
{
    int hi = (1 << bits) - 1;
    return v < 0 ? 0 : v > hi ? hi : v;
}
#endif

#define LOOK 9        /* Huffman lookahead bits */
#define MAX_DIM 8192

typedef struct {
    uint8_t len[1 << LOOK]; /* code length for this LOOK-bit prefix, 0 = longer code */
    uint8_t sym[1 << LOOK];
    int16_t fast[1 << LOOK]; /* AC: value << 8 | run << 4 | bits used, when code + value fit */
    int32_t maxcode[17];    /* end of the codes of length l, left-aligned to 16 bits */
    int32_t delta[17];      /* vals index = code + delta[l] */
    uint8_t vals[256];
    int nvals;
    int defined;
} Huff;

typedef struct {
    int id, h, v, tq;
    int hs, vs;          /* upsampling factor to full resolution (1 or 2) */
    int cw, ch;          /* size in samples */
    int stride, rows;    /* plane size, padded to whole MCUs */
    uint8_t *plane;
    uint8_t *line;       /* 8 upsampled rows (when hs or vs is 2) */
    int pred;            /* DC predictor */
    int td, ta;          /* Huffman tables of the current scan */
} Comp;

typedef struct {
    const uint8_t *p, *end;
    uint32_t bits;       /* bit buffer, MSB first */
    int nbits;
    int fake;            /* zero bytes fed after a marker or the end of data */
    int marker;          /* the reader stopped at a marker */
    uint16_t q[4][64];   /* quantisation tables, zigzag order */
    int qdef[4];
    Huff dc[4], ac[4];
    Comp comp[3];
    int ncomp, w, h, w8, hmax, vmax, mcux, mcuy, ri, frame, scans;
    int maxw, maxh, exact;
    int16_t blk[64];
} D;

static const uint8_t zigzag[64] = {
    0,  1,  8,  16, 9,  2,  3,  10, 17, 24, 32, 25, 18, 11, 4,  5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6,  7,  14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
};

/* ---- colour tables -------------------------------------------------------
 * RGB output uses libjpeg's jdcolor.c arithmetic exactly. RGB565 output packs
 * two terms per entry: the high half is the R (or B) offset plus rounding for
 * the 5-bit result, the low half the G contribution in 1/256 units (both
 * extracted with one instruction each on ARMv6). */

static int16_t t_crr[256], t_cbb[256];
static int32_t t_crg[256], t_cbg[256];
static uint32_t t_cr565[256], t_cb565[256];
static uint32_t t_wrg[256];          /* 4:2:0 path: (R + 1040) << 16 | (G from Cr + 1032) */
static int32_t t_wg[256], t_wb[256]; /* G from Cb; B + 1040 (quarter levels) */
static uint8_t t_clamp[768]; /* index + 256, clamps to 0..255 */
static int tables_ready;

/* Per zigzag position: bit c = column c has a coefficient below row 0, plus
 * where the coefficient lies, so the IDCT can skip what is known to be zero. */
#define K_C2 0x100   /* column >= 2 */
#define K_C4 0x200   /* column >= 4 */
#define K_R2 0x400   /* row >= 2 */
#define K_R4 0x800   /* row >= 4 */
#define K_AC 0x1000
static uint16_t kinfo[64];

static void init_tables(void)
{
    if (tables_ready)
        return;
    for (int i = 0; i < 256; i++) {
        int x = i - 128;
        t_crr[i] = (int16_t)((91881 * x + 32768) >> 16);   /* 1.40200 */
        t_cbb[i] = (int16_t)((116130 * x + 32768) >> 16);  /* 1.77200 */
        t_crg[i] = -46802 * x;                             /* 0.71414 */
        t_cbg[i] = -22554 * x + 32768;                     /* 0.34414 */
        /* G rounding (half a 1/256 unit, then half a 6-bit step) goes with Cr */
        int gcr = (-46802 * x + 128) >> 8, gcb = (-22554 * x + 128) >> 8;
        t_cr565[i] = (uint32_t)(t_crr[i] + 4) << 16 | (uint16_t)(gcr + 128 + 512);
        t_cb565[i] = (uint32_t)(t_cbb[i] + 4) << 16 | (uint16_t)gcb;
        /* Quarter levels; the biases keep every lane positive and fold in the
         * rounding of the 5- and 6-bit results (+16 = half of 32, +8 of 16). */
        int rq = (4 * 91881 * x + 32768) >> 16, bq = (4 * 116130 * x + 32768) >> 16;
        int gcrq = (-4 * 46802 * x + 32768) >> 16, gcbq = (-4 * 22554 * x + 32768) >> 16;
        t_wrg[i] = (uint32_t)(rq + 1040) << 16 | (uint32_t)(gcrq + 1032);
        t_wg[i] = gcbq;
        t_wb[i] = bq + 1040;
    }
    for (int k = 0; k < 64; k++) {
        int r = zigzag[k] >> 3, c = zigzag[k] & 7;
        kinfo[k] = (uint16_t)((r ? 1 << c : 0) | (c >= 2 ? K_C2 : 0) | (c >= 4 ? K_C4 : 0) |
                              (r >= 2 ? K_R2 : 0) | (r >= 4 ? K_R4 : 0) | (k ? K_AC : 0));
    }
    for (int i = 0; i < 768; i++) {
        int v = i - 256;
        t_clamp[i] = (uint8_t)(v < 0 ? 0 : v > 255 ? 255 : v);
    }
    tables_ready = 1;
}

/* ---- bit reader --------------------------------------------------------- */

static void fill(D *d)
{
    while (d->nbits <= 24) {
        uint32_t b = 0;
        if (!d->marker && d->p < d->end) {
            b = *d->p;
            if (b != 0xFF) {
                d->p++;
            } else if (d->p + 1 < d->end && d->p[1] == 0x00) {
                d->p += 2;            /* stuffed 0xFF */
            } else {
                d->marker = 1;        /* stay on the marker */
                b = 0;
                d->fake++;
            }
        } else {
            d->fake++;
        }
        d->bits |= b << (24 - d->nbits);
        d->nbits += 8;
    }
}

/* A code longer than LOOK bits (d->bits holds at least 16 valid bits). */
static int huff_slow(D *d, const Huff *h)
{
    int32_t c16 = (int32_t)(d->bits >> 16);
    int l = LOOK + 1;
    while (l <= 16 && c16 >= h->maxcode[l])
        l++;
    if (l > 16)
        return -1;
    int idx = (int)(c16 >> (16 - l)) + h->delta[l];
    if (idx < 0 || idx >= h->nvals)
        return -1;
    d->bits <<= l;
    d->nbits -= l;
    return h->vals[idx];
}

/* The block decoder keeps the bit buffer in locals (bits, nbits); these move
 * it to and from D around the out-of-line refill and slow Huffman path. */
#define BR_OUT() (d->bits = bits, d->nbits = nbits)
#define BR_IN() (bits = d->bits, nbits = d->nbits)
#define BR_NEED() do { if (nbits <= 24) { BR_OUT(); fill(d); BR_IN(); } } while (0)
#define BR_SYM(h, out) do { \
        BR_NEED(); \
        uint32_t lk_ = bits >> (32 - LOOK); \
        int ln_ = (h)->len[lk_]; \
        if (ln_) { \
            bits <<= ln_; \
            nbits -= ln_; \
            (out) = (h)->sym[lk_]; \
        } else { \
            BR_OUT(); \
            (out) = huff_slow(d, (h)); \
            BR_IN(); \
        } \
    } while (0)
#define BR_VAL(s, out) do { /* 1 <= s <= 11 */ \
        BR_NEED(); \
        int v_ = (int)(bits >> (32 - (s))); \
        bits <<= (s); \
        nbits -= (s); \
        (out) = v_ < (1 << ((s) - 1)) ? v_ - (1 << (s)) + 1 : v_; \
    } while (0)

static int build_huff(Huff *h, const uint8_t *counts, const uint8_t *vals, int n)
{
    memset(h->len, 0, sizeof(h->len));
    int code = 0, k = 0;
    for (int l = 1; l <= 16; l++) {
        h->delta[l] = k - code;
        for (int i = 0; i < counts[l - 1]; i++, code++, k++) {
            if (code >= (1 << l))
                return -1; /* more codes than fit in l bits */
            if (l <= LOOK) {
                int shift = LOOK - l, base = code << shift;
                for (int j = 0; j < (1 << shift); j++) {
                    h->len[base + j] = (uint8_t)l;
                    h->sym[base + j] = vals[k];
                }
            }
        }
        h->maxcode[l] = code << (16 - l);
        code <<= 1;
    }
    for (int i = 0; i < (1 << LOOK); i++) {
        int l = h->len[i], rs = h->sym[i], s = rs & 15;
        h->fast[i] = 0;
        if (!l || !s || l + s > LOOK)
            continue;
        int v = (i >> (LOOK - l - s)) & ((1 << s) - 1);
        if (v < (1 << (s - 1)))
            v -= (1 << s) - 1;
        if (v >= -128 && v <= 127)
            h->fast[i] = (int16_t)(v * 256 + (rs >> 4) * 16 + l + s);
    }
    memcpy(h->vals, vals, (size_t)n);
    h->nvals = n;
    h->defined = 1;
    return 0;
}

/* ---- blocks ------------------------------------------------------------- */

/* Dequantised coefficients and the IDCT's intermediate values are kept within
 * +-8192 (one SSAT on ARMv6), far outside what real images produce, so even
 * garbage input can't overflow an int. */
#define clampc(v) SSAT((v), 14)
#define clamp8(v) ((uint8_t)USAT((v), 8))

/* Decodes one block into d->blk (natural order, dequantised). Returns the
 * kinfo bits of its coefficients (0 = DC only) or -1 on corrupt data. */
static int decode_block(D *d, Comp *c, const uint16_t *q)
{
    int16_t *blk = d->blk;
    uint32_t bits = d->bits;
    int nbits = d->nbits, t, v, mask = 0;
    BR_SYM(&d->dc[c->td], t);
    if (t < 0 || t > 11)
        goto fail;
    int pred = c->pred;
    if (t) {
        BR_VAL(t, v);
        pred += v;
    }
    pred = pred < -2047 ? -2047 : pred > 2047 ? 2047 : pred;
    c->pred = pred;
    blk[0] = (int16_t)clampc(pred * q[0]);
    const Huff *h = &d->ac[c->ta];
    const int16_t *fast = h->fast;
    for (int k = 1; k < 64;) {
        BR_NEED();
        int f = fast[bits >> (32 - LOOK)];
        if (f) { /* code and value in one lookup */
            k += (f >> 4) & 15;
            if (k > 63)
                goto fail;
            bits <<= f & 15;
            nbits -= f & 15;
            blk[zigzag[k]] = (int16_t)clampc((f >> 8) * q[k]);
            mask |= kinfo[k];
            k++;
            continue;
        }
        int rs;
        BR_SYM(h, rs);
        if (rs < 0)
            goto fail;
        int r = rs >> 4, s = rs & 15;
        if (!s) {
            if (r != 15)
                break;      /* end of block */
            k += 16;
            continue;
        }
        k += r;
        if (k > 63 || s > 11)
            goto fail;
        BR_VAL(s, v);
        blk[zigzag[k]] = (int16_t)clampc(v * q[k]);
        mask |= kinfo[k];
        k++;
    }
    BR_OUT();
    return mask;
fail:
    BR_OUT();
    return -1;
}

/* jidctint's integer IDCT (Loeffler-Ligtenberg-Moschytz), 13-bit constants,
 * 2 extra bits between the passes. Rounding and the +128 level shift are
 * folded into the DC term. ONE_D does a full 8-point pass; ONE_D4 and ONE_D2
 * are the same pass with inputs 4..7 (or 2..7) known to be zero: identical
 * results with less work, and most blocks only have low frequencies. */
#define CB 13
#define P1 2
#define ONE_D(x0, x1, x2, x3, x4, x5, x6, x7, round, OUT) do { \
        int z2 = (x2), z3 = (x6); \
        int z1 = (z2 + z3) * 4433; \
        int t2 = z1 - z3 * 15137, t3 = z1 + z2 * 6270; \
        int t0 = ((x0) + (x4)) * (1 << CB) + (round), t1 = ((x0) - (x4)) * (1 << CB) + (round); \
        int a10 = t0 + t3, a13 = t0 - t3, a11 = t1 + t2, a12 = t1 - t2; \
        int o0 = (x7), o1 = (x5), o2 = (x3), o3 = (x1); \
        z1 = o0 + o3; \
        z2 = o1 + o2; \
        z3 = o0 + o2; \
        int z4 = o1 + o3, z5 = (z3 + z4) * 9633; \
        o0 *= 2446; \
        o1 *= 16819; \
        o2 *= 25172; \
        o3 *= 12299; \
        z1 *= -7373; \
        z2 *= -20995; \
        z3 = z3 * -16069 + z5; \
        z4 = z4 * -3196 + z5; \
        o0 += z1 + z3; \
        o1 += z2 + z4; \
        o2 += z2 + z3; \
        o3 += z1 + z4; \
        OUT(0, a10 + o3); OUT(7, a10 - o3); OUT(1, a11 + o2); OUT(6, a11 - o2); \
        OUT(2, a12 + o1); OUT(5, a12 - o1); OUT(3, a13 + o0); OUT(4, a13 - o0); \
    } while (0)
#define ONE_D4(x0, x1, x2, x3, round, OUT) do { \
        int z2 = (x2), o2 = (x3), o3 = (x1); \
        int t0 = (x0) * (1 << CB) + (round), t2 = z2 * 4433, t3 = z2 * 10703; \
        int a10 = t0 + t3, a13 = t0 - t3, a11 = t0 + t2, a12 = t0 - t2; \
        int z5 = (o2 + o3) * 9633; \
        int b0 = z5 - o3 * 7373 - o2 * 16069, b1 = z5 - o2 * 20995 - o3 * 3196; \
        int b2 = z5 - o2 * 11892, b3 = z5 + o3 * 1730; \
        OUT(0, a10 + b3); OUT(7, a10 - b3); OUT(1, a11 + b2); OUT(6, a11 - b2); \
        OUT(2, a12 + b1); OUT(5, a12 - b1); OUT(3, a13 + b0); OUT(4, a13 - b0); \
    } while (0)
#define ONE_D2(x0, x1, round, OUT) do { \
        int t0 = (x0) * (1 << CB) + (round), o3 = (x1); \
        int b0 = o3 * 2260, b1 = o3 * 6437, b2 = o3 * 9633, b3 = o3 * 11363; \
        OUT(0, t0 + b3); OUT(7, t0 - b3); OUT(1, t0 + b2); OUT(6, t0 - b2); \
        OUT(2, t0 + b1); OUT(5, t0 - b1); OUT(3, t0 + b0); OUT(4, t0 - b0); \
    } while (0)
#define R1 (1 << (CB - P1 - 1))
#define R2 ((1 << (CB + P1 + 2)) + (128 << (CB + P1 + 3)))
#define COL_OUT(n, x) w[(n) * 8] = clampc((x) >> (CB - P1))
#define ROW_OUT(n, x) out[n] = clamp8((x) >> (CB + P1 + 3))

static void idct(const int16_t *in, uint8_t *out, int stride, int mask)
{
    int ws[64];
    int ncols = mask & K_C4 ? 8 : mask & K_C2 ? 4 : 2; /* columns that can be non-zero */
    for (int c = 0; c < ncols; c++) {
        const int16_t *i = in + c;
        int *w = ws + c;
        if (!(mask & (1 << c)))
            w[0] = w[8] = w[16] = w[24] = w[32] = w[40] = w[48] = w[56] = i[0] * (1 << P1);
        else if (mask & K_R4)
            ONE_D(i[0], i[8], i[16], i[24], i[32], i[40], i[48], i[56], R1, COL_OUT);
        else if (mask & K_R2)
            ONE_D4(i[0], i[8], i[16], i[24], R1, COL_OUT);
        else
            ONE_D2(i[0], i[8], R1, COL_OUT);
    }
    const int *w = ws;
    if (ncols == 8) {
        for (int r = 0; r < 8; r++, out += stride, w += 8)
            ONE_D(w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7], R2, ROW_OUT);
    } else if (ncols == 4) {
        for (int r = 0; r < 8; r++, out += stride, w += 8)
            ONE_D4(w[0], w[1], w[2], w[3], R2, ROW_OUT);
    } else {
        for (int r = 0; r < 8; r++, out += stride, w += 8)
            ONE_D2(w[0], w[1], R2, ROW_OUT);
    }
}

static int do_block(D *d, Comp *c, const uint16_t *q, int bx, int by)
{
    int mask = decode_block(d, c, q);
    if (mask < 0)
        return -1;
    uint8_t *out = c->plane + (size_t)by * 8 * (size_t)c->stride + (size_t)bx * 8;
    if (mask) {
        idct(d->blk, out, c->stride, mask);
        memset(d->blk, 0, sizeof(d->blk));
    } else {
        int v = clamp8(((d->blk[0] + 4) >> 3) + 128);
        for (int r = 0; r < 8; r++)
            memset(out + (size_t)r * (size_t)c->stride, v, 8);
        d->blk[0] = 0;
    }
    return 0;
}

/* ---- scans -------------------------------------------------------------- */

/* Position of the next marker (other than RSTn) at or after p. */
static const uint8_t *next_marker(const uint8_t *p, const uint8_t *end)
{
    while (p + 1 < end) {
        if (p[0] == 0xFF && p[1] != 0x00 && p[1] != 0xFF && (p[1] < 0xD0 || p[1] > 0xD7))
            return p;
        p++;
    }
    return end;
}

static int restart(D *d, Comp **sc, int ns)
{
    const uint8_t *p = d->p;
    while (p + 1 < d->end && !(p[0] == 0xFF && p[1] != 0x00 && p[1] != 0xFF))
        p++;
    if (p + 1 >= d->end || p[1] < 0xD0 || p[1] > 0xD7)
        return -1;
    d->p = p + 2;
    d->bits = 0;
    d->nbits = 0;
    d->fake = 0;
    d->marker = 0;
    for (int i = 0; i < ns; i++)
        sc[i]->pred = 0;
    return 0;
}

static int decode_scan(D *d, Comp **sc, int ns)
{
    d->bits = 0;
    d->nbits = 0;
    d->fake = 0;
    d->marker = 0;
    const uint16_t *q[4];
    for (int i = 0; i < ns; i++) {
        sc[i]->pred = 0;
        q[i] = d->q[sc[i]->tq];
    }
    int nx = d->mcux, ny = d->mcuy;
    if (ns == 1) { /* non-interleaved: one block per MCU */
        nx = (sc[0]->cw + 7) / 8;
        ny = (sc[0]->ch + 7) / 8;
    }
    int left = d->ri;
    for (int my = 0; my < ny; my++) {
        for (int mx = 0; mx < nx; mx++) {
            if (d->ri) {
                if (!left) {
                    if (restart(d, sc, ns))
                        return JPEG_ERR_DATA;
                    left = d->ri;
                }
                left--;
            }
            if (ns == 1) {
                if (do_block(d, sc[0], q[0], mx, my))
                    return JPEG_ERR_DATA;
            } else {
                for (int i = 0; i < ns; i++) {
                    Comp *c = sc[i];
                    for (int v = 0; v < c->v; v++)
                        for (int h = 0; h < c->h; h++)
                            if (do_block(d, c, q[i], mx * c->h + h, my * c->v + v))
                                return JPEG_ERR_DATA;
                }
            }
            if (d->fake * 8 > d->nbits)
                return JPEG_ERR_DATA; /* used bits past the end of the data */
        }
    }
    d->p = next_marker(d->p, d->end);
    return JPEG_OK;
}

/* ---- headers ------------------------------------------------------------ */

static int parse_sof(D *d, const uint8_t *s, const uint8_t *se, int header_only)
{
    if (d->frame || se - s < 6)
        return JPEG_ERR_FORMAT;
    int prec = s[0], h = s[1] << 8 | s[2], w = s[3] << 8 | s[4], n = s[5];
    if (prec != 8 || (n != 1 && n != 3))
        return JPEG_ERR_UNSUPPORTED;
    if (!w || !h)
        return JPEG_ERR_UNSUPPORTED; /* height in a DNL marker */
    if (se - s < 6 + 3 * n)
        return JPEG_ERR_FORMAT;
    d->w = w;
    d->h = h;
    d->w8 = (w + 7) & ~7;
    d->ncomp = n;
    d->frame = 1;
    d->hmax = d->vmax = 1;
    for (int i = 0; i < n; i++) {
        Comp *c = &d->comp[i];
        const uint8_t *e = s + 6 + 3 * i;
        c->id = e[0];
        c->h = e[1] >> 4;
        c->v = e[1] & 15;
        c->tq = e[2];
        if (c->h < 1 || c->h > 4 || c->v < 1 || c->v > 4 || c->tq > 3)
            return JPEG_ERR_FORMAT;
        if (n == 1)
            c->h = c->v = 1; /* a lone component is never interleaved */
        if (c->h > d->hmax)
            d->hmax = c->h;
        if (c->v > d->vmax)
            d->vmax = c->v;
    }
    if (header_only)
        return JPEG_OK;
    if (w > MAX_DIM || h > MAX_DIM || w > d->maxw || h > d->maxh ||
        (d->exact && (w != d->maxw || h != d->maxh)))
        return JPEG_ERR_SIZE;
    d->mcux = (w + 8 * d->hmax - 1) / (8 * d->hmax);
    d->mcuy = (h + 8 * d->vmax - 1) / (8 * d->vmax);
    for (int i = 0; i < n; i++) {
        Comp *c = &d->comp[i];
        if (d->hmax % c->h || d->vmax % c->v)
            return JPEG_ERR_UNSUPPORTED;
        c->hs = d->hmax / c->h;
        c->vs = d->vmax / c->v;
        if (c->hs > 2 || c->vs > 2)
            return JPEG_ERR_UNSUPPORTED;
        c->cw = (w * c->h + d->hmax - 1) / d->hmax;
        c->ch = (h * c->v + d->vmax - 1) / d->vmax;
        c->stride = d->mcux * c->h * 8;
        c->rows = d->mcuy * c->v * 8;
        c->plane = calloc((size_t)c->stride, (size_t)c->rows);
        if (!c->plane)
            return JPEG_ERR_MEMORY;
        if (c->hs > 1 || c->vs > 1) {
            c->line = malloc((size_t)(d->w8 + 16) * 8);
            if (!c->line)
                return JPEG_ERR_MEMORY;
        }
    }
    return JPEG_OK;
}

static int parse_sos(D *d, const uint8_t *s, const uint8_t *se)
{
    if (!d->frame || se - s < 1)
        return JPEG_ERR_FORMAT;
    int ns = s[0];
    if (ns < 1 || ns > d->ncomp || se - s < 1 + 2 * ns + 3)
        return JPEG_ERR_FORMAT;
    Comp *sc[3];
    int blocks = 0;
    for (int i = 0; i < ns; i++) {
        int id = s[1 + 2 * i], tables = s[2 + 2 * i];
        Comp *c = NULL;
        for (int j = 0; j < d->ncomp; j++)
            if (d->comp[j].id == id)
                c = &d->comp[j];
        for (int j = 0; j < i; j++)
            if (sc[j] == c)
                c = NULL;
        if (!c)
            return JPEG_ERR_FORMAT;
        c->td = tables >> 4;
        c->ta = tables & 15;
        if (c->td > 3 || c->ta > 3 || !d->dc[c->td].defined || !d->ac[c->ta].defined ||
            !d->qdef[c->tq])
            return JPEG_ERR_FORMAT;
        sc[i] = c;
        blocks += c->h * c->v;
    }
    const uint8_t *t = s + 1 + 2 * ns;
    if (t[0] != 0 || t[1] != 63 || t[2] != 0)
        return JPEG_ERR_UNSUPPORTED;
    if (ns > 1 && blocks > 10)
        return JPEG_ERR_FORMAT;
    int r = decode_scan(d, sc, ns);
    if (r == JPEG_OK)
        d->scans++;
    return r;
}

static int parse_dht(D *d, const uint8_t *s, const uint8_t *se)
{
    while (s < se) {
        if (se - s < 17)
            return JPEG_ERR_FORMAT;
        int tc = s[0] >> 4, th = s[0] & 15, n = 0;
        if (tc > 1 || th > 3)
            return JPEG_ERR_FORMAT;
        for (int i = 1; i <= 16; i++)
            n += s[i];
        if (n > 256 || se - s < 17 + n)
            return JPEG_ERR_FORMAT;
        if (build_huff(tc ? &d->ac[th] : &d->dc[th], s + 1, s + 17, n))
            return JPEG_ERR_FORMAT;
        s += 17 + n;
    }
    return JPEG_OK;
}

static int parse_dqt(D *d, const uint8_t *s, const uint8_t *se)
{
    while (s < se) {
        int pq = s[0] >> 4, tq = s[0] & 15;
        s++;
        if (pq > 1 || tq > 3 || se - s < 64 * (pq + 1))
            return JPEG_ERR_FORMAT;
        for (int k = 0; k < 64; k++)
            d->q[tq][k] = pq ? (uint16_t)(s[2 * k] << 8 | s[2 * k + 1]) : s[k];
        s += 64 * (pq + 1);
        d->qdef[tq] = 1;
    }
    return JPEG_OK;
}

static int parse(D *d, const uint8_t *src, size_t len, int header_only)
{
    const uint8_t *p = src, *end = src + len;
    if (len < 4 || p[0] != 0xFF || p[1] != 0xD8)
        return JPEG_ERR_FORMAT;
    p += 2;
    d->end = end;
    for (;;) {
        while (p < end && *p != 0xFF)
            p++;
        while (p < end && *p == 0xFF)
            p++;
        if (p >= end)
            break;
        int m = *p++;
        if (m == 0xD9)
            break;
        if (m == 0x00 || m == 0x01 || (m >= 0xD0 && m <= 0xD7))
            continue; /* no length field */
        if (end - p < 2)
            return JPEG_ERR_FORMAT;
        int seg = p[0] << 8 | p[1];
        if (seg < 2 || seg > end - p)
            return JPEG_ERR_FORMAT;
        const uint8_t *s = p + 2, *se = p + seg;
        p = se;
        int r = JPEG_OK;
        switch (m) {
        case 0xC0: case 0xC1:
            r = parse_sof(d, s, se, header_only);
            if (r == JPEG_OK && header_only)
                return JPEG_OK;
            break;
        case 0xC2: case 0xC6: case 0xCA: case 0xCE:
            return JPEG_ERR_PROGRESSIVE;
        case 0xC3: case 0xC5: case 0xC7: case 0xC9: case 0xCB: case 0xCD: case 0xCF:
            return JPEG_ERR_UNSUPPORTED;
        case 0xC4:
            if (!header_only)
                r = parse_dht(d, s, se);
            break;
        case 0xDB:
            if (!header_only)
                r = parse_dqt(d, s, se);
            break;
        case 0xDD:
            if (se - s < 2)
                return JPEG_ERR_FORMAT;
            d->ri = s[0] << 8 | s[1];
            break;
        case 0xDA:
            if (header_only)
                return JPEG_ERR_FORMAT; /* scan before the frame header */
            d->p = se;
            r = parse_sos(d, s, se);
            p = d->p;
            break;
        default:
            break; /* APPn, COM, DNL, ... */
        }
        if (r != JPEG_OK)
            return r;
    }
    if (!d->frame)
        return JPEG_ERR_FORMAT;
    return header_only || d->scans ? JPEG_OK : JPEG_ERR_DATA;
}

/* ---- output ------------------------------------------------------------- */

/* Full-resolution samples of component c for image row y (w8 of them). */
static const uint8_t *comp_line(const D *d, const Comp *c, int y, uint8_t *buf)
{
    if (c->hs == 1 && c->vs == 1)
        return c->plane + (size_t)y * (size_t)c->stride;
    int iw = d->w, cy = c->vs == 2 ? y >> 1 : y;
    const uint8_t *near = c->plane + (size_t)cy * (size_t)c->stride, *far = near;
    if (c->vs == 2) {
        int fy = (y & 1) ? cy + 1 : cy - 1;
        fy = fy < 0 ? 0 : fy >= c->ch ? c->ch - 1 : fy;
        far = c->plane + (size_t)fy * (size_t)c->stride;
    }
    int cw = c->cw;
    if (c->hs == 1) { /* 4:4:0 */
        int bias = (y & 1) ? 2 : 1;
        for (int x = 0; x < iw; x++)
            buf[x] = (uint8_t)((near[x] * 3 + far[x] + bias) >> 2);
    } else if (c->vs == 1) { /* 4:2:2 */
        for (int x = 0; x < cw; x++) {
            int v3 = near[x] * 3;
            int l = near[x ? x - 1 : 0], r = near[x + 1 < cw ? x + 1 : cw - 1];
            buf[2 * x] = (uint8_t)((v3 + l + 1) >> 2);
            buf[2 * x + 1] = (uint8_t)((v3 + r + 2) >> 2);
        }
    } else { /* 4:2:0 */
        int cur = near[0] * 3 + far[0], prev = cur;
        for (int x = 0; x < cw; x++) {
            int next = x + 1 < cw ? near[x + 1] * 3 + far[x + 1] : cur;
            buf[2 * x] = (uint8_t)((cur * 3 + prev + 8) >> 4);
            buf[2 * x + 1] = (uint8_t)((cur * 3 + next + 7) >> 4);
            prev = cur;
            cur = next;
        }
    }
    for (int x = iw; x < d->w8; x++)
        buf[x] = buf[iw - 1];
    return buf;
}

/* Repeat the last real column of full-resolution planes up to w8. */
static void pad_planes(D *d)
{
    for (int i = 0; i < d->ncomp; i++) {
        Comp *c = &d->comp[i];
        if (c->hs != 1 || c->vs != 1 || d->w8 == d->w)
            continue;
        for (int y = 0; y < d->h; y++) {
            uint8_t *row = c->plane + (size_t)y * (size_t)c->stride;
            memset(row + d->w, row[d->w - 1], (size_t)(d->w8 - d->w));
        }
    }
}

/* Morton offsets inside a tile: x bits 0,2,4 and y bits 1,3,5. */
static const uint8_t mx_off[8] = {0, 1, 4, 5, 16, 17, 20, 21};
static const uint8_t my_off[8] = {0, 2, 8, 10, 32, 34, 40, 42};

/* Any sampling: upsample 8 rows at a time into line buffers, then convert. */
static void tiles_generic(D *d, uint16_t *dst, int tpr)
{
    int ih = d->h, nty = (ih + 7) / 8, ntx = d->w8 / 8, lw = d->w8 + 16;
    const uint8_t *L[3][8];
    for (int ty = 0; ty < nty; ty++) {
        for (int r = 0; r < 8; r++) {
            int y = ty * 8 + r < ih ? ty * 8 + r : ih - 1;
            for (int i = 0; i < d->ncomp; i++) {
                Comp *c = &d->comp[i];
                L[i][r] = comp_line(d, c, y, c->line ? c->line + r * lw : NULL);
            }
        }
        uint16_t *row = dst + (size_t)ty * (size_t)tpr * 64;
        for (int tx = 0; tx < ntx; tx++) {
            uint16_t *t = row + tx * 64;
            for (int r = 0; r < 8; r++) {
                uint16_t *o = t + my_off[r];
                const uint8_t *py = L[0][r] + tx * 8;
                if (d->ncomp == 1) {
#define GRAY(k, off) do { \
        int yy = py[k]; \
        o[off] = (uint16_t)(USAT((yy + 4) >> 3, 5) << 11 | USAT((yy + 2) >> 2, 6) << 5 | \
                            USAT((yy + 4) >> 3, 5)); \
    } while (0)
                    GRAY(0, 0); GRAY(1, 1); GRAY(2, 4); GRAY(3, 5);
                    GRAY(4, 16); GRAY(5, 17); GRAY(6, 20); GRAY(7, 21);
#undef GRAY
                } else {
                    const uint8_t *pb = L[1][r] + tx * 8, *pr = L[2][r] + tx * 8;
#define PIX(k, off) do { \
        int yy = py[k]; \
        int32_t tr = (int32_t)t_cr565[pr[k]], tb = (int32_t)t_cb565[pb[k]]; \
        int g = yy + (((int16_t)tr + (int16_t)tb) >> 8); \
        o[off] = (uint16_t)(USAT((yy + (tr >> 16)) >> 3, 5) << 11 | USAT(g >> 2, 6) << 5 | \
                            USAT((yy + (tb >> 16)) >> 3, 5)); \
    } while (0)
                    PIX(0, 0); PIX(1, 1); PIX(2, 4); PIX(3, 5);
                    PIX(4, 16); PIX(5, 17); PIX(6, 20); PIX(7, 21);
#undef PIX
                }
            }
        }
    }
}

/* 4:2:0, the common case. Each chroma sample is turned into its R, G and B
 * offsets first (quarter levels, biased positive; R and G share a word as two
 * 16-bit lanes, B has its own), so the fancy upsampling filter (weights 9, 3,
 * 3, 1 / 16) runs on those offsets two lanes at a time and no table lookups
 * are left per pixel. The filter's /16 is never done: the sums stay in 1/64
 * levels (at most 31168, so lanes can't carry into each other) and the final
 * shifts to 5 and 6 bits absorb it. Works a band of 8 rows (4 chroma rows plus
 * one above and below) at a time. */
static int tiles_420(D *d, uint16_t *dst, int tpr)
{
    const Comp *cy = &d->comp[0], *cb = &d->comp[1], *cr = &d->comp[2];
    int cw = cb->cw, ch = cb->ch, nty = (d->h + 7) / 8, ntx = d->w8 / 8;
    int ncx = d->w8 / 2 + 2; /* chroma columns -1 .. w8/2 */
    size_t ys = (size_t)cy->stride;
    uint32_t *buf = malloc(sizeof(uint32_t) * 12 * (size_t)ncx);
    if (!buf)
        return -1;
    uint32_t *wrg[6], *wb[6];
    for (int k = 0; k < 6; k++) {
        wrg[k] = buf + (size_t)(2 * k) * (size_t)ncx;
        wb[k] = wrg[k] + ncx;
    }
    for (int ty = 0; ty < nty; ty++) {
        for (int k = 0; k < 6; k++) {
            int y = ty * 4 - 1 + k;
            y = y < 0 ? 0 : y >= ch ? ch - 1 : y;
            const uint8_t *pb = cb->plane + (size_t)y * (size_t)cb->stride;
            const uint8_t *pr = cr->plane + (size_t)y * (size_t)cr->stride;
            uint32_t *a = wrg[k] + 1, *b = wb[k] + 1;
            for (int x = 0; x < cw; x++) {
                a[x] = t_wrg[pr[x]] + (uint32_t)t_wg[pb[x]];
                b[x] = (uint32_t)t_wb[pb[x]];
            }
            a[-1] = a[0];
            b[-1] = b[0];
            for (int x = cw; x < ncx - 1; x++) {
                a[x] = a[cw - 1];
                b[x] = b[cw - 1];
            }
        }
        uint16_t *trow = dst + (size_t)ty * (size_t)tpr * 64;
        const uint8_t *yrow = cy->plane + (size_t)ty * 8 * ys;
        for (int tx = 0; tx < ntx; tx++) {
            uint16_t *t = trow + tx * 64;
            for (int p = 0; p < 4; p++) {
                const uint32_t *nrg = wrg[p + 1] + 4 * tx, *arg = wrg[p] + 4 * tx, *brg = wrg[p + 2] + 4 * tx;
                const uint32_t *nbb = wb[p + 1] + 4 * tx, *abb = wb[p] + 4 * tx, *bbb = wb[p + 2] + 4 * tx;
                uint32_t urg[6], lrg[6], ub[6], lb[6];
                for (int j = 0; j < 6; j++) {
                    uint32_t n3 = nrg[j] * 3, m3 = nbb[j] * 3;
                    urg[j] = n3 + arg[j];
                    lrg[j] = n3 + brg[j];
                    ub[j] = m3 + abb[j];
                    lb[j] = m3 + bbb[j];
                }
                const uint8_t *yu = yrow + (size_t)(2 * p) * ys + tx * 8, *yl = yu + ys;
                uint16_t *ou = t + my_off[2 * p], *ol = t + my_off[2 * p + 1];
#define PIX420(yv, rg, bv, o) do { \
        int t_ = (yv) * 64 - 16 * 1024; \
        (o) = (uint16_t)(USAT((t_ + (int)((rg) >> 16)) >> 9, 5) << 11 | \
                         USAT((t_ + (int)((rg) & 0xFFFF)) >> 8, 6) << 5 | \
                         USAT((t_ + (int)(bv)) >> 9, 5)); \
    } while (0)
#define ROW420(v, vb, py, o, j, xe, xo) do { \
        uint32_t c_ = (v)[j] * 3, cb_ = (vb)[j] * 3; \
        uint32_t e_ = c_ + (v)[(j) - 1], o_ = c_ + (v)[(j) + 1]; \
        uint32_t eb_ = cb_ + (vb)[(j) - 1], ob_ = cb_ + (vb)[(j) + 1]; \
        PIX420((py)[2 * (j) - 2], e_, eb_, (o)[xe]); \
        PIX420((py)[2 * (j) - 1], o_, ob_, (o)[xo]); \
    } while (0)
                ROW420(urg, ub, yu, ou, 1, 0, 1);
                ROW420(urg, ub, yu, ou, 2, 4, 5);
                ROW420(urg, ub, yu, ou, 3, 16, 17);
                ROW420(urg, ub, yu, ou, 4, 20, 21);
                ROW420(lrg, lb, yl, ol, 1, 0, 1);
                ROW420(lrg, lb, yl, ol, 2, 4, 5);
                ROW420(lrg, lb, yl, ol, 3, 16, 17);
                ROW420(lrg, lb, yl, ol, 4, 20, 21);
#undef ROW420
#undef PIX420
            }
        }
    }
    free(buf);
    return 0;
}

/* Texels outside the image repeat its edge, as the packer pads .ctex. */
static void pad_tiles(const D *d, uint16_t *dst, int tw, int th)
{
    int iw = d->w, ih = d->h, tpr = tw / 8, ntx = d->w8 / 8, nty = (ih + 7) / 8;
    size_t trow = (size_t)tpr * 64;
    if (iw & 7) { /* columns right of the image in its last tile column */
        int ex = (iw - 1) & 7;
        for (int ty = 0; ty < nty; ty++) {
            uint16_t *t = dst + (size_t)ty * trow + (size_t)(ntx - 1) * 64;
            for (int r = 0; r < 8; r++)
                for (int x = ex + 1; x < 8; x++)
                    t[my_off[r] + mx_off[x]] = t[my_off[r] + mx_off[ex]];
        }
    }
    if (ih & 7) { /* rows below the image in its last tile row */
        int ey = (ih - 1) & 7;
        uint16_t *row = dst + (size_t)(nty - 1) * trow;
        for (int tx = 0; tx < ntx; tx++)
            for (int r = ey + 1; r < 8; r++)
                for (int x = 0; x < 8; x++)
                    row[tx * 64 + my_off[r] + mx_off[x]] = row[tx * 64 + my_off[ey] + mx_off[x]];
    }
    if (ntx < tpr) { /* whole tiles right of the image */
        for (int ty = 0; ty < nty; ty++) {
            uint16_t *row = dst + (size_t)ty * trow;
            const uint16_t *edge = row + (size_t)(ntx - 1) * 64 + mx_off[(iw - 1) & 7];
            for (int r = 0; r < 8; r++) {
                uint16_t v = edge[my_off[r]];
                for (int tx = ntx; tx < tpr; tx++)
                    for (int x = 0; x < 8; x++)
                        row[tx * 64 + my_off[r] + mx_off[x]] = v;
            }
        }
    }
    if (nty * 8 < th) { /* whole tile rows below the image */
        const uint16_t *last = dst + (size_t)(nty - 1) * trow + my_off[(ih - 1) & 7];
        uint16_t *first = dst + (size_t)nty * trow;
        for (int tx = 0; tx < tpr; tx++)
            for (int x = 0; x < 8; x++) {
                uint16_t v = last[tx * 64 + mx_off[x]];
                for (int r = 0; r < 8; r++)
                    first[tx * 64 + my_off[r] + mx_off[x]] = v;
            }
        for (int ty = nty + 1; ty < th / 8; ty++)
            memcpy(dst + (size_t)ty * trow, first, trow * 2);
    }
}

static void out_tiled(D *d, uint16_t *dst, int tw, int th)
{
    const Comp *c = d->comp;
    int is420 = d->ncomp == 3 && c[0].hs == 1 && c[0].vs == 1 && c[1].hs == 2 && c[1].vs == 2 &&
                c[2].hs == 2 && c[2].vs == 2;
    if (!is420 || tiles_420(d, dst, tw / 8))
        tiles_generic(d, dst, tw / 8);
    pad_tiles(d, dst, tw, th);
}

static void out_rgb(D *d, uint8_t *dst)
{
    const uint8_t *C = t_clamp + 256;
    const uint8_t *L[3];
    for (int y = 0; y < d->h; y++) {
        for (int i = 0; i < d->ncomp; i++)
            L[i] = comp_line(d, &d->comp[i], y, d->comp[i].line);
        uint8_t *o = dst + (size_t)y * (size_t)d->w * 3;
        for (int x = 0; x < d->w; x++, o += 3) {
            int yy = L[0][x];
            if (d->ncomp == 1) {
                o[0] = o[1] = o[2] = (uint8_t)yy;
                continue;
            }
            int cb = L[1][x], cr = L[2][x];
            o[0] = C[yy + t_crr[cr]];
            o[1] = C[yy + ((t_cbg[cb] + t_crg[cr]) >> 16)];
            o[2] = C[yy + t_cbb[cb]];
        }
    }
}

static void release(D *d)
{
    for (int i = 0; i < 3; i++) {
        free(d->comp[i].plane);
        free(d->comp[i].line);
    }
    free(d);
}

/* ---- API ---------------------------------------------------------------- */

int jpeg_size(const uint8_t *src, size_t len, int *w, int *h)
{
    D *d = calloc(1, sizeof(D));
    if (!d)
        return JPEG_ERR_MEMORY;
    int r = parse(d, src, len, 1);
    *w = d->w;
    *h = d->h;
    release(d);
    return r;
}

int jpeg_decode_tiled565(const uint8_t *src, size_t len, uint16_t *dst, int tw, int th,
                         int *w, int *h)
{
    *w = *h = 0;
    if (tw < 8 || th < 8 || tw % 8 || th % 8 || tw > MAX_DIM || th > MAX_DIM)
        return JPEG_ERR_SIZE;
    D *d = calloc(1, sizeof(D));
    if (!d)
        return JPEG_ERR_MEMORY;
    d->maxw = tw;
    d->maxh = th;
    init_tables();
    int r = parse(d, src, len, 0);
    if (r == JPEG_OK) {
        pad_planes(d);
        out_tiled(d, dst, tw, th);
        *w = d->w;
        *h = d->h;
    }
    release(d);
    return r;
}

int jpeg_decode_rgb(const uint8_t *src, size_t len, uint8_t *dst, int w, int h)
{
    D *d = calloc(1, sizeof(D));
    if (!d)
        return JPEG_ERR_MEMORY;
    d->maxw = w;
    d->maxh = h;
    d->exact = 1;
    init_tables();
    int r = parse(d, src, len, 0);
    if (r == JPEG_OK) {
        out_rgb(d, dst);
    }
    release(d);
    return r;
}
