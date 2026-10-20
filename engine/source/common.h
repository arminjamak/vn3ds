#pragma once

#include <math.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef __3DS__
#include <3ds/types.h>
#else
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;
typedef int64_t s64;
#endif

#define NONE_STR 0xFFFFFFFFu
#define ZORDER_KEEP ((s32)0x80000000)

#define TOP_W 400
#define TOP_H 240
#define BOT_W 320
#define BOT_H 240

#define ARRAY_LEN(a) (sizeof(a) / sizeof((a)[0]))

static inline float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
static inline float lerpf(float a, float b, float t) { return a + (b - a) * t; }

static inline u32 rd_u32(const u8 *p) { u32 v; memcpy(&v, p, 4); return v; }
static inline s32 rd_s32(const u8 *p) { s32 v; memcpy(&v, p, 4); return v; }
static inline u16 rd_u16(const u8 *p) { u16 v; memcpy(&v, p, 2); return v; }
static inline float rd_f32(const u8 *p) { float v; memcpy(&v, p, 4); return v; }
static inline double rd_f64(const u8 *p) { double v; memcpy(&v, p, 8); return v; }

/* Colours are 0xRRGGBBAA throughout the engine. */
#define RGBA(r, g, b, a) (((u32)(r) << 24) | ((u32)(g) << 16) | ((u32)(b) << 8) | (u32)(a))
static inline u32 rgba_alpha(u32 c, float a)
{
    u32 al = (u32)(clampf((c & 0xFF) * a, 0, 255));
    return (c & 0xFFFFFF00u) | al;
}

void platform_log(const char *fmt, ...);
#define LOG(...) platform_log(__VA_ARGS__)
/* Timing lines ("perf: ..."): buffered in memory on the 3DS and written to
 * the log by the background thread, so measuring never costs a frame; on
 * the desktop printed with --perf. Safe from any thread. */
void platform_perf(const char *fmt, ...);
#define PERF(...) platform_perf(__VA_ARGS__)
/* A microsecond clock (for timing). */
u64 platform_us(void);

/* Bytes of the next UTF-8 code point and its value. */
int utf8_decode(const char *s, u32 *cp);
/* Byte offset of the n-th code point (or strlen). */
size_t utf8_offset(const char *s, size_t n);
size_t utf8_len(const char *s);
u32 crc32_update(u32 crc, const void *data, size_t len);
