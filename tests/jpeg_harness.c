/* Command-line wrapper around engine/source/jpeg.c for tests/test_jpeg.py.
 *   rgb   in.jpg out.rgb             packed RGB888
 *   tiled in.jpg tw th out.bin       PICA200-tiled RGB565
 *   bench in.jpg tw th iterations    prints ms per tiled decode
 *   fuzz  in.jpg tw th iterations seed   mutated/truncated copies must not crash */
#include "jpeg.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static unsigned char *slurp(const char *path, size_t *n)
{
    FILE *f = fopen(path, "rb");
    if (!f)
        exit(2);
    fseek(f, 0, SEEK_END);
    *n = (size_t)ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *b = malloc(*n ? *n : 1);
    if (!b || fread(b, 1, *n, f) != *n)
        exit(2);
    fclose(f);
    return b;
}

static unsigned rng = 1;
static unsigned rnd(void) { return (rng = rng * 1103515245u + 12345u) >> 8; }

int main(int argc, char **argv)
{
    if (argc < 3)
        return 2;
    size_t n;
    unsigned char *src = slurp(argv[2], &n);
    int w, h, r;
    if (!strcmp(argv[1], "rgb") && argc == 4) {
        if ((r = jpeg_size(src, n, &w, &h)) != JPEG_OK) {
            printf("error %d\n", r);
            return 1;
        }
        unsigned char *o = malloc((size_t)w * (size_t)h * 3);
        if ((r = jpeg_decode_rgb(src, n, o, w, h)) != JPEG_OK) {
            printf("error %d\n", r);
            return 1;
        }
        FILE *f = fopen(argv[3], "wb");
        fwrite(o, 3, (size_t)w * (size_t)h, f);
        fclose(f);
        return 0;
    }
    if (argc < 6)
        return 2;
    int tw = atoi(argv[3]), th = atoi(argv[4]);
    uint16_t *o = malloc((size_t)tw * (size_t)th * 2);
    if (!strcmp(argv[1], "tiled")) {
        if ((r = jpeg_decode_tiled565(src, n, o, tw, th, &w, &h)) != JPEG_OK) {
            printf("error %d\n", r);
            return 1;
        }
        FILE *f = fopen(argv[5], "wb");
        fwrite(o, 2, (size_t)tw * (size_t)th, f);
        fclose(f);
        return 0;
    }
    int iters = atoi(argv[5]);
    if (!strcmp(argv[1], "bench")) {
        clock_t t0 = clock();
        for (int i = 0; i < iters; i++)
            if (jpeg_decode_tiled565(src, n, o, tw, th, &w, &h) != JPEG_OK)
                return 1;
        printf("%.3f\n", (double)(clock() - t0) * 1000.0 / CLOCKS_PER_SEC / iters);
        return 0;
    }
    if (!strcmp(argv[1], "fuzz") && argc == 7) {
        rng = (unsigned)atoi(argv[6]);
        unsigned char *m = malloc(n);
        int ok = 0;
        for (int i = 0; i < iters; i++) {
            memcpy(m, src, n);
            size_t len = n;
            switch (rnd() % 4) {
            case 0: len = rnd() % n; break;                                    /* truncated */
            case 1: for (int k = 1 + rnd() % 8; k--;) m[rnd() % n] = (unsigned char)rnd(); break;
            case 2: for (int k = 1 + rnd() % 4; k--;) m[rnd() % (n < 700 ? n : 700)] = (unsigned char)rnd(); break;
            default: { size_t a = rnd() % n, b = a + rnd() % 64; memset(m + a, rnd() & 1 ? 0xFF : 0, (b < n ? b : n) - a); }
            }
            ok += jpeg_decode_tiled565(m, len, o, tw, th, &w, &h) == JPEG_OK;
            if (jpeg_size(m, len, &w, &h) == JPEG_OK && w > 0 && h > 0 && w <= 2048 && h <= 2048) {
                unsigned char *rgb = malloc((size_t)w * (size_t)h * 3);
                jpeg_decode_rgb(m, len, rgb, w, h);
                free(rgb);
            }
        }
        printf("%d of %d decoded\n", ok, iters);
        return 0;
    }
    return 2;
}
