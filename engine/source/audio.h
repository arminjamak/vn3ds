#pragma once
#include "common.h"

enum { CH_MUSIC = 0, CH_SOUND = 1, CH_VOICE = 2, CH_COUNT = 3 };

bool audio_init(void);
void audio_exit(void);
/* Starts `path` (Ogg Vorbis). With `queue`, it plays after the current file. */
void audio_play(int ch, const char *path, bool loop, float fadein, bool queue);
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
