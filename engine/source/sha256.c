#include "sha256.h"

static const u32 K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
};

#define ROR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static void block(Sha256 *s, const u8 *p)
{
    u32 w[64], v[8];
    for (int i = 0; i < 16; i++)
        w[i] = (u32)p[i * 4] << 24 | (u32)p[i * 4 + 1] << 16 | (u32)p[i * 4 + 2] << 8 | p[i * 4 + 3];
    for (int i = 16; i < 64; i++) {
        u32 s0 = ROR(w[i - 15], 7) ^ ROR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        u32 s1 = ROR(w[i - 2], 17) ^ ROR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    memcpy(v, s->h, sizeof(v));
    for (int i = 0; i < 64; i++) {
        u32 a = v[0], e = v[4];
        u32 t1 = v[7] + (ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)) + ((e & v[5]) ^ (~e & v[6])) + K[i] + w[i];
        u32 t2 = (ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)) + ((a & v[1]) ^ (a & v[2]) ^ (v[1] & v[2]));
        memmove(v + 1, v, 7 * sizeof(u32));
        v[4] += t1;
        v[0] = t1 + t2;
    }
    for (int i = 0; i < 8; i++)
        s->h[i] += v[i];
}

void sha256_init(Sha256 *s)
{
    static const u32 H0[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                              0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    memcpy(s->h, H0, sizeof(H0));
    s->len = 0;
}

void sha256_update(Sha256 *s, const void *data, size_t n)
{
    const u8 *p = data;
    while (n--) {
        s->buf[s->len++ % 64] = *p++;
        if (s->len % 64 == 0)
            block(s, s->buf);
    }
}

void sha256_final(Sha256 *s, u8 out[32])
{
    u64 bits = s->len * 8;
    u8 b = 0x80;
    sha256_update(s, &b, 1);
    b = 0;
    while (s->len % 64 != 56)
        sha256_update(s, &b, 1);
    for (int i = 7; i >= 0; i--) {
        b = (u8)(bits >> (i * 8));
        sha256_update(s, &b, 1);
    }
    for (int i = 0; i < 8; i++) {
        out[i * 4] = (u8)(s->h[i] >> 24);
        out[i * 4 + 1] = (u8)(s->h[i] >> 16);
        out[i * 4 + 2] = (u8)(s->h[i] >> 8);
        out[i * 4 + 3] = (u8)s->h[i];
    }
}

void hmac_sha256(const void *key, size_t key_len, const void *msg, size_t msg_len, u8 out[32])
{
    u8 k[64] = {0}, pad[64], inner[32];
    Sha256 s;
    if (key_len > 64) {
        sha256_init(&s);
        sha256_update(&s, key, key_len);
        sha256_final(&s, k);
    } else {
        memcpy(k, key, key_len);
    }
    for (int i = 0; i < 64; i++)
        pad[i] = k[i] ^ 0x36;
    sha256_init(&s);
    sha256_update(&s, pad, 64);
    sha256_update(&s, msg, msg_len);
    sha256_final(&s, inner);
    for (int i = 0; i < 64; i++)
        pad[i] = k[i] ^ 0x5c;
    sha256_init(&s);
    sha256_update(&s, pad, 64);
    sha256_update(&s, inner, 32);
    sha256_final(&s, out);
}

void hmac_sha256_hex(const char *key, const char *msg, char out[65])
{
    static const char HEX[] = "0123456789abcdef";
    u8 mac[32];
    hmac_sha256(key, strlen(key), msg, strlen(msg), mac);
    for (int i = 0; i < 32; i++) {
        out[i * 2] = HEX[mac[i] >> 4];
        out[i * 2 + 1] = HEX[mac[i] & 15];
    }
    out[64] = 0;
}
