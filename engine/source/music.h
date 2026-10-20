#pragma once
/* The music channel's mixer, shared by the 3DS (audio_3ds.c, which queues
 * its output on NDSP) and the desktop build (audio_null.c, which can write
 * it to a WAV file).
 *
 * Tracks play from "decks": the background thread opens each file and keeps
 * a second or so of it decoded ahead in the deck's buffer, so the main
 * thread never decodes. The mixer pulls from up to three decks at once
 * (the current track, the next one, one fading out) with sample-exact gain
 * envelopes, which is what makes splices on a bar line and gapless queues
 * possible. All calls are from the main thread except music_bg_work() (the
 * background thread) and music_mix() (either). */
#include "audio.h"

void music_init(void);
void music_exit(void);

void music_play_now(const char *path, bool loop, float fadein);
void music_queue(const char *path, bool loop);
void music_change(const char *path, bool loop, float fadein);
void music_prefetch(const char *path, bool loop);
void music_stop(float fadeout);
bool music_playing(void);

/* Mixes the next `frames` stereo frames into `out` at music_rate(). Returns
 * the frames written: 0 when nothing is playing (or about to). */
long music_mix(s16 *out, long frames);
long music_rate(void);
/* True once after a cut (play now, stop without a fade): output already
 * queued for the speaker should be dropped. */
bool music_take_flush(void);
/* The work the mixer needs done off the main thread: opening files
 * (music_open_work, the background thread), and closing and decoding
 * (music_decode_work, the 3DS audio thread). music_bg_work does both, for
 * a build with one worker thread. Each returns true if it did something. */
bool music_open_work(void);
bool music_decode_work(void);
bool music_bg_work(void);
/* Frames mixed so far (the mixer's clock). */
s64 music_clock(void);
