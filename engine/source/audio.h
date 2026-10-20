#pragma once
#include "common.h"

enum { CH_MUSIC = 0, CH_SOUND = 1, CH_VOICE = 2, CH_COUNT = 3 };

bool audio_init(void);
void audio_exit(void);
/* Starts `path` (Ogg Opus or Vorbis) at once, cutting what was playing;
 * with `queue` it plays after the current file instead, gaplessly. On the
 * music channel a file that was prefetched starts without a pause; one that
 * wasn't is opened by the background thread first (the call waits for it),
 * so a start is always on time, e.g. for a rhythm game's chart. */
void audio_play(int ch, const char *path, bool loop, float fadein, bool queue);

/* ---- music ----------------------------------------------------------------
 * The music channel is one continuous stream mixed in software (music.c):
 * decoding runs on the background thread, a change of music waits for a
 * musically sensible point in the current track (see audio_music_change). */

/* A track's tempo grid (vn3ds.json "music"; 0 = unknown). */
typedef struct {
    float bpm;
    u8 beats_per_bar;
    u8 phrase_bars;   /* bars per phrase: where a change of music may land */
    u16 bars;         /* bars in one loop of the file (the grid is then exact) */
} MusicMeta;

/* The tempo grid of a music file, if the game has one (app.c). */
bool app_music_meta(const char *path, MusicMeta *out);
/* Changes the music without a cut: if music is playing, the new track
 * starts at the end of the current loop or the next phrase boundary (at
 * most 8 s away), with a short splice; otherwise (or without a tempo grid)
 * with a beat-aligned crossfade. From silence it starts as soon as it is
 * ready, fading in over `fadein`. The same track carries on. */
void audio_music_change(const char *path, bool loop, float fadein);
/* Opens `path` in the background and decodes its start, so a later change
 * to it (or audio_play) starts at once. */
void audio_music_prefetch(const char *path, bool loop);
void audio_stop(int ch, float fadeout);
bool audio_playing(int ch);
/* Freeze a channel where it is (and the minigame sound voices with the
 * music), e.g. while a minigame is paused. */
void audio_pause(int ch, bool paused);
void audio_set_volume(int ch, float v);
/* Machine voices: a bank of short syllables decoded into memory once per
 * game, played one at a time on their own channel. */
void audio_vox_load(const char **paths, int n);
void audio_vox_free(void);
void audio_vox_play(int index, float rate, float volume);
/* Minigame sound effects: short clips decoded into memory once per run and
 * played on a pool of voices, so rapid sounds (shots, steps) overlap
 * instead of cutting each other off. `rate` 1 = original pitch. */
void audio_sfx_load(const char **paths, int n);
void audio_sfx_free(void);
void audio_sfx_play(int index, float volume, float rate);
/* Lower the music while someone talks (1 = full volume). */
void audio_music_duck(float gain);
/* Called once per frame to refill stream buffers and run fades. */
void audio_update(float dt);
