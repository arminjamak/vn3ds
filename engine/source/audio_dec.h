#pragma once
/* Ogg audio decoding shared by the 3DS sound code and the desktop build.
 *
 * Ogg Opus is decoded with opusfile (fixed point, always 48 kHz); Ogg Vorbis
 * with Tremor where it is linked in (the 3DS build, VN_HAVE_TREMOR). The
 * codec is sniffed from the first Ogg page (OpusHead / \x01vorbis), never
 * from the file name: packed files are all called .ogg. */
#include "common.h"

enum { ADEC_NONE = 0, ADEC_VORBIS, ADEC_OPUS };

typedef struct {
    int codec;     /* ADEC_* */
    int channels;  /* 1 or 2 */
    long rate;     /* Hz; 48000 for Opus */
    bool downmix;  /* Opus with more than two channels, mixed to stereo */
    void *h;       /* OggOpusFile * or OggVorbis_File * */
    void *mem;     /* adec_open_mem: the file in memory (owned) */
} ADec;

/* Codec of an Ogg file from its first bytes (at least the first page). */
int adec_sniff(const u8 *head, size_t n);
const char *adec_codec_name(int codec);
/* Opens `path`; false (with *d cleared) if it is missing or not a mono or
 * stereo Ogg Opus / Vorbis file this build can decode. */
bool adec_open(ADec *d, const char *path);
/* The same for a whole file already in memory (malloc'd; taken over and
 * freed by adec_close, also on failure): decoding then never touches the
 * SD card. */
bool adec_open_mem(ADec *d, u8 *data, size_t len);
/* Reads a file into memory (NULL if missing or bigger than `max`). */
u8 *adec_read_file(const char *path, size_t max, size_t *len);
void adec_close(ADec *d);
/* Back to the first sample (Opus: the first one after the pre-skip). */
bool adec_rewind(ADec *d);
/* Length in frames, or -1 if unknown. */
s64 adec_length(ADec *d);
/* Fills `pcm` with up to `frames` interleaved PCM16 frames. With `loop`,
 * the end of the file wraps to its start sample-exactly (Ren'Py loops
 * whole files), so loops are gapless. Returns the frames written; sets
 * *ended (and stops short) once the file is over or broken. */
long adec_fill(ADec *d, s16 *pcm, long frames, bool loop, bool *ended);
/* Decodes at most `max_seconds` of a short clip into a malloc'd mono
 * buffer (stereo is mixed down). NULL if it cannot be read. */
s16 *adec_load_mono(const char *path, float max_seconds, u32 *frames, long *rate);
