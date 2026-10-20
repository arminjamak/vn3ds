#pragma once
#include "common.h"

/* SHA-256 and HMAC-SHA256 (FIPS 180-4, RFC 2104), small and dependency
 * free. Used to sign leaderboard submissions. */

typedef struct {
    u32 h[8];
    u8 buf[64];
    u64 len;   /* bytes hashed so far */
} Sha256;

void sha256_init(Sha256 *s);
void sha256_update(Sha256 *s, const void *data, size_t n);
void sha256_final(Sha256 *s, u8 out[32]);

void hmac_sha256(const void *key, size_t key_len, const void *msg, size_t msg_len, u8 out[32]);
/* The same as 64 lowercase hex digits plus a terminator. */
void hmac_sha256_hex(const char *key, const char *msg, char out[65]);
