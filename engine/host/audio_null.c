/* Desktop test build: audio calls are only logged. With --audio-log they
 * are also written, timestamped, to a file that tools/vn3ds-record mixes
 * into a soundtrack. Files the engine plays are checked with the same
 * decoder the 3DS uses (Opus here; Vorbis needs Tremor, 3DS only), and
 * --decode-audio renders a file through the 3DS's streaming path. */
#include "../source/audio.h"
#include "../source/audio_dec.h"
#include "host.h"

#include <time.h>

static bool playing[CH_COUNT];
FILE *host_audio_log;
double host_now;
static float last_duck = 1.0f, last_vol[CH_COUNT] = {-1, -1, -1};

bool audio_init(void) { return true; }
void audio_exit(void) {}

void audio_play(int ch, const char *path, bool loop, float fadein, bool queue)
{
    const char *name = strrchr(path, '/');
    printf("    [audio] %s ch%d %s%s fadein=%.1f\n", queue ? "queue" : "play", ch,
           name ? name + 1 : path, loop ? " (loop)" : "", fadein);
    FILE *f = fopen(path, "rb");
    if (!f) {
        printf("    [audio] MISSING %s\n", path);
    } else {
        u8 head[512];
        size_t n = fread(head, 1, sizeof(head), f);
        fclose(f);
        int codec = adec_sniff(head, n);
        ADec d;
        if (codec == ADEC_NONE)
            printf("    [audio] NOT OGG OPUS/VORBIS %s\n", path);
#ifdef VN_HAVE_OPUS
        else if (codec == ADEC_OPUS && !adec_open(&d, path))
            printf("    [audio] BAD OPUS %s\n", path);
        else if (codec == ADEC_OPUS)
            adec_close(&d);
#endif
        (void)d;
    }
    playing[ch] = ch == CH_MUSIC;
    if (host_audio_log)
        fprintf(host_audio_log, "%.4f play %d %d %.3f %d %s\n", host_now, ch, loop, fadein, queue, path);
}

void audio_stop(int ch, float fadeout)
{
    if (playing[ch])
        printf("    [audio] stop ch%d fadeout=%.1f\n", ch, fadeout);
    playing[ch] = false;
    if (host_audio_log)
        fprintf(host_audio_log, "%.4f stop %d %.3f\n", host_now, ch, fadeout);
}

bool audio_playing(int ch) { return playing[ch]; }

void audio_pause(int ch, bool paused)
{
    if (host_audio_log)
        fprintf(host_audio_log, "%.4f %s %d\n", host_now, paused ? "pause" : "resume", ch);
}
void audio_set_volume(int ch, float v)
{
    if (host_audio_log && ch >= 0 && ch < CH_COUNT && v != last_vol[ch])
        fprintf(host_audio_log, "%.4f volume %d %.3f\n", host_now, ch, v);
    if (ch >= 0 && ch < CH_COUNT)
        last_vol[ch] = v;
}
void audio_update(float dt) { (void)dt; }

int host_vox_count;
static int vox_loaded;

void audio_vox_load(const char **paths, int n)
{
    vox_loaded = 0;
    for (int i = 0; i < n; i++) {
        FILE *f = fopen(paths[i], "rb");
        if (f) {
            vox_loaded++;
            fclose(f);
        }
        if (host_audio_log)
            fprintf(host_audio_log, "%.4f bank %d %s\n", host_now, i, paths[i]);
    }
    printf("    [audio] voice bank: %d of %d syllables\n", vox_loaded, n);
}

void audio_vox_free(void) { vox_loaded = 0; }
void audio_vox_play(int index, float rate, float volume)
{
    host_vox_count++;
    if (host_audio_log && vox_loaded)
        fprintf(host_audio_log, "%.4f vox %d %.4f %.4f\n", host_now, index, rate, volume);
}
void audio_music_duck(float gain)
{
    if (host_audio_log && fabsf(gain - last_duck) > 0.005f) {
        fprintf(host_audio_log, "%.4f duck %.4f\n", host_now, gain);
        last_duck = gain;
    }
}

static int sfx_loaded;

void audio_sfx_load(const char **paths, int n)
{
    sfx_loaded = n;
    for (int i = 0; i < n && host_audio_log; i++)
        fprintf(host_audio_log, "%.4f sfxbank %d %s\n", host_now, i, paths[i]);
}

void audio_sfx_free(void) { sfx_loaded = 0; }

void audio_sfx_play(int index, float volume, float rate)
{
    if (host_audio_log && index >= 0 && index < sfx_loaded)
        fprintf(host_audio_log, "%.4f sfx %d %.3f %.3f\n", host_now, index, volume, rate);
}

/* ---- --decode-audio --------------------------------------------------------
 * Decodes `in` the way the 3DS streams music: wave-buffer sized calls to
 * adec_fill(), wrapping to the start for `loops` passes, into a 16-bit WAV.
 * Prints the decoder's time per second of audio. */

static void put_u32(FILE *f, u32 v) { fwrite(&v, 4, 1, f); }
static void put_u16(FILE *f, u16 v) { fwrite(&v, 2, 1, f); }

int host_decode_audio(const char *in, const char *out, int loops)
{
    ADec d;
    if (!adec_open(&d, in)) {
        fprintf(stderr, "%s: cannot decode (not Ogg Opus%s)\n", in,
#ifdef VN_HAVE_TREMOR
                " or Vorbis"
#else
                "; Vorbis is decoded on the 3DS only"
#endif
        );
        return 1;
    }
    s64 len = adec_length(&d);
    if (len <= 0 || loops < 1) {
        fprintf(stderr, "%s: unknown length\n", in);
        adec_close(&d);
        return 1;
    }
    FILE *f = out ? fopen(out, "wb") : NULL;
    if (out && !f) {
        perror(out);
        adec_close(&d);
        return 1;
    }
    /* the 3DS's wave buffer size for this rate (audio_3ds.c) */
    long chunk = d.rate / 6 < 4096 ? 4096 : d.rate / 6;
    if (chunk > 8192 * 2 / d.channels)
        chunk = 8192 * 2 / d.channels;
    s64 total = len * loops, done = 0;
    u32 bytes = (u32)(total * d.channels * 2);
    if (f) {
        fwrite("RIFF", 1, 4, f);
        put_u32(f, 36 + bytes);
        fwrite("WAVEfmt ", 1, 8, f);
        put_u32(f, 16);
        put_u16(f, 1);
        put_u16(f, (u16)d.channels);
        put_u32(f, (u32)d.rate);
        put_u32(f, (u32)(d.rate * d.channels * 2));
        put_u16(f, (u16)(d.channels * 2));
        put_u16(f, 16);
        fwrite("data", 1, 4, f);
        put_u32(f, bytes);
    }
    s16 *pcm = malloc((size_t)chunk * d.channels * sizeof(s16));
    double secs = 0;
    bool ended = false;
    while (pcm && done < total && !ended) {
        long want = total - done < chunk ? (long)(total - done) : chunk;
        struct timespec t0, t1;
        clock_gettime(CLOCK_MONOTONIC, &t0);
        /* loop: the last pass is cut at the file's length like the others */
        long got = adec_fill(&d, pcm, want, true, &ended);
        clock_gettime(CLOCK_MONOTONIC, &t1);
        secs += (double)(t1.tv_sec - t0.tv_sec) + (double)(t1.tv_nsec - t0.tv_nsec) * 1e-9;
        if (f)
            fwrite(pcm, sizeof(s16) * d.channels, (size_t)got, f);
        done += got;
    }
    free(pcm);
    double audio = (double)done / (double)d.rate;
    printf("%s: %s, %d ch, %ld Hz, %lld frames per pass, %d pass%s: %lld frames\n", in,
           adec_codec_name(d.codec), d.channels, d.rate, (long long)len, loops,
           loops == 1 ? "" : "es", (long long)done);
    printf("decode: %.3f ms per second of audio (%.0fx real time)\n",
           audio > 0 ? secs * 1000.0 / audio : 0.0, secs > 0 ? audio / secs : 0.0);
    adec_close(&d);
    if (f)
        fclose(f);
    return done == total ? 0 : 1;
}
