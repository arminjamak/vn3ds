/* Desktop test build: audio calls are only logged. With --audio-log they
 * are also written, timestamped, to a file that tools/vn3ds-record mixes
 * into a soundtrack. */
#include "../source/audio.h"

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
    if (!f)
        printf("    [audio] MISSING %s\n", path);
    else
        fclose(f);
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
