/* Compact baseline JPEG decoder for .ctex textures (no external libraries).
 *
 * Supports baseline / extended-sequential Huffman JPEGs with 8-bit samples:
 * grayscale or YCbCr, sampling 4:4:4, 4:2:2, 4:2:0 and 4:4:0, interleaved or
 * not, with restart markers. Progressive, arithmetic-coded, lossless, 12-bit
 * and CMYK files are rejected. Chroma is upsampled with libjpeg's "fancy"
 * (triangle) filter and colours use libjpeg's fixed-point YCbCr->RGB, so the
 * output matches libjpeg / Pillow to within rounding.
 *
 * All input is treated as untrusted: every read is bounds-checked and corrupt
 * or truncated data returns an error instead of crashing. */
#pragma once

#include <stddef.h>
#include <stdint.h>

enum {
    JPEG_OK = 0,
    JPEG_ERR_FORMAT = -1,      /* not a JPEG / malformed marker segment */
    JPEG_ERR_UNSUPPORTED = -2, /* arithmetic, lossless, 12-bit, CMYK, odd sampling */
    JPEG_ERR_PROGRESSIVE = -3,
    JPEG_ERR_DATA = -4,        /* corrupt or truncated entropy-coded data */
    JPEG_ERR_MEMORY = -5,
    JPEG_ERR_SIZE = -6,        /* image does not fit the destination */
};

/* Builds the decoder's tables. Call once before decoding on more than one
 * thread (the decoder itself keeps no other shared state). */
void jpeg_init(void);

/* Width and height from the frame header. */
int jpeg_size(const uint8_t *src, size_t len, int *w, int *h);

/* Decodes into a tw x th RGB565 texture in the PICA200 tiled layout (8x8
 * tiles in row-major order from the top-left, Morton order inside a tile, top
 * image row first). tw and th must be multiples of 8 and at least the image
 * size; texels outside the image repeat its edge. *w / *h get the image size. */
int jpeg_decode_tiled565(const uint8_t *src, size_t len, uint16_t *dst, int tw, int th,
                         int *w, int *h);

/* The same into an RGB8 texture (3 bytes per texel: B, G, R), for pictures
 * packed with vnpack --jpeg-rgb8. */
int jpeg_decode_tiled888(const uint8_t *src, size_t len, uint8_t *dst, int tw, int th,
                         int *w, int *h);

/* Decodes into packed RGB888 rows (w * h * 3 bytes; the image must be exactly
 * w x h). Used by the tests. */
int jpeg_decode_rgb(const uint8_t *src, size_t len, uint8_t *dst, int w, int h);
