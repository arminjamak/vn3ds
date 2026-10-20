# Snapshot: the score

Mystical dream pop, written as code in [vnsynth](vnsynth.py): hazy pads,
chorused guitars, soft drum machines, slow tempos (one club cue at 126 BPM),
and public-domain 1921-1925 records ([samples/CREDITS.md](samples/CREDITS.md))
woven through as processed fragments: 78rpm band-limiting, stretch, reverse,
pitch, tape wobble and glitch. They surface like memories, sometimes as
loops locked to the cue's tempo (`fit=`), never just pasted on top.

Every cue is one file in `cues/`, a seamless loop of 32-64 s that renders to
`../demo/game/audio/<cue>.ogg` (32 kHz stereo Vorbis):

    python3 examples/music/render.py [cue ...]   # render (4 workers)
    python3 examples/music/check.py [cue ...]    # duration, clipping, loudness, loop seam, voice band
    python3 examples/music/make_review.py        # snapshot_soundtrack_review.mp3 + .txt

## Mixing for the machine voices

The game speaks over the music in soft synthetic syllables (150-600 Hz
fundamentals, formants up to about 3 kHz), so every cue leaves room:

- `render()` carves a pocket: -4 dB at 1.9 kHz, -1.5 dB at 3.2 kHz and a
  -4 dB shelf above 7 kHz; reverb returns are darkened above 6 kHz.
- Leads are soft (felt piano, flute, vibes, glass, music box) and sit with
  their fundamentals below about 1 kHz; the choir is a dark "ooh", not an
  "aah"; the plucked guitar, Rhodes and rim/brush/tick were darkened; the
  `78rpm` and `telephone` effects are centred low (about 260-2400 Hz with a
  dip at 1.9 kHz) so the old records don't sit on the voices' formants.
- Every cue is levelled to the same loudness (`loudness=-18`: the mean of
  plain and K-weighted RMS, in dBFS) with a loop-safe peak limiter at -1.4
  dBFS, so switching cues never jumps in level. `check.py` keeps every cue
  within +-3 dB of the median.
- Seamless loops: reverb and delay tails fold back onto the start, LFOs and
  filter sweeps complete whole cycles per loop, the master EQ runs
  circularly, and the loop length is rounded to whole 128-sample blocks (at
  most 2 ms) because the Vorbis encoder pads a partial last block with
  silence. Each .ogg is decoded again after encoding and re-encoded a little
  quieter if the codec overshoots. `check.py` compares the wrap with the
  cue's own bar lines.

## Cues

Aliases kept for the script's existing file names (each re-renders its source
cue into the old name): `morning` = `morning_render`, `unease` = `unraveling`,
`ward` = `closed_ward`, `entities` = `angel_ops` (the script plays it for every
cut to the governing entities), `watch` = `lantern_watch`. `voices` is its own
cue.

| cue (`cues/<name>.py` -> `audio/<name>.ogg`) | story placement | motifs | samples | key | BPM | loop |
|---|---|---|---|---|---|---|
| **Tutorial** | | | | | | |
| `theme` | tutorial / calibration | aron, clock (tick), system (rim) | - | C major | 96 | 40.0 s (16 bars) |
| **Chapter 1 - The Morning Render** | | | | | | |
| `morning_render` | waking at 7:07 (alias `morning`) | clock, aron | April Showers | D major | 78 | 49.2 s (16 bars) |
| `kitchen_talk` | kitchen, the bird on the wire, Mira's small talk | mira, clock | April Showers | G major | 88 | 43.6 s (16 bars) |
| `questions` | thinking through Bostrom | aron, aron_rising | April Showers | E dorian | 72 | 53.3 s (16 bars) |
| `miso` | Aron lectures Miso; "Meow." (any chapter) | miso, aron | Ogopogo | F major | 108 | 35.6 s (16 bars) |
| `purgatorium_shift` | cut: Pim and Dross, kitchen-talk shift 7 | system, mira | Ogopogo, Krooked Blues | Ab major | 109 | 52.8 s (24 bars) |
| `angel_ops` | cut: Seraphiel's ops room (alias `entities`) | system, aron | Wooden Soldiers | B minor | 77.4 | 49.6 s (16 bars) |
| `umbrella_rain` | the umbrella for a stranger | aron, lantern (first hint) | My Buddy | Ab major | 66 | 43.6 s (12 bars) |
| `notebook` | the notebook's first line | aron (+ half-answer) | Farewell Blues | B minor | 70 | 54.9 s (16 bars) |
| `voices` | the transmissions (vox lines) | system, clock | Wooden Soldiers, Ogopogo | C# minor | 90 | 32.0 s (12 bars) |
| `unraveling` | obsession, no sleep, the mirror (alias `unease`) | aron, clock, system | April Showers | C minor | 96 | 60.0 s (24 bars) |
| `ambulance_transfer` | the ambulance ride: transfer complete | mira (fading), system | Somebody Loves Me | E minor | 72 | 53.3 s (16 bars) |
| **Chapter 2 - Fog** | | | | | | |
| `closed_ward` | the ward (alias `ward`) | clock, aron | April Showers | F# phrygian | 64 | 45.0 s (12 bars) |
| `fog` | life on the medication | aron (half speed) | My Buddy | A minor, 3/4 | 60 | 60.0 s (20 bars) |
| `group_therapy` | group therapy, breathing | aron (+ half-answer) | My Buddy | F major | 76 | 50.5 s (16 bars) |
| `mira_visits` | Mira's visits: the love theme | mira_love | Somebody Loves Me | Db major | 70 | 54.9 s (16 bars) |
| `theo_nights` | nights at Theo's | theo, aron | Krooked Blues | Db major | 80.7 | 47.6 s (16 bars) |
| `club_speed` | the speed night | aron (hook), aron_rising | Ogopogo | A minor | 126 | 61.0 s (32 bars) |
| `crash` | the comedown | aron (falling) | Ogopogo | D minor | 60 | 48.0 s (12 bars) |
| `council` | cut: the Council meets | ashveil_box, ashveil | St. Louis Blues | C minor | 60 | 64.0 s (16 bars) |
| `lantern_watch` | cut: the Lantern Watch (alias `watch`) | lantern, aron | My Buddy | E major | 72 | 53.3 s (16 bars) |
| `rooftop_mission` | rooftop: three flickers, the mission | aron -> aron_rising, lantern | April Showers | A minor | 92 | 62.6 s (24 bars) |
| **Chapter 3 - Snapshot** | | | | | | |
| `protected_world` | the too-perfect protected world | clock (35 cents sharp once) | April Showers | C major | 98.4 | 39.0 s (16 bars) |
| `the_leak` | the leak glitches | clock, system, aron (cut off) | April Showers, Krooked Blues, Ogopogo | F minor | 90 | 42.7 s (16 bars) |
| `cafe` | the cafe with Mira | mira | Somebody Loves Me | F major | 82 | 46.8 s (16 bars) |
| `fight` | the fight with Mira | mira (minor), aron | Somebody Loves Me | B minor | 104 | 36.9 s (16 bars) |
| `together_night` | together at night | mira, aron -> mira_love + aron resolved | Somebody Loves Me | Eb major | 66 | 58.2 s (16 bars) |
| `real_world_vigil` | cut: the real Mira at his coma bed | mira (minor, unresolved) | My Buddy | C minor | 60 | 48.0 s (12 bars) |
| `ember_trial` | cut: Ember's trial | lantern (minor, broken), ashveil | Wooden Soldiers | G minor | 76 | 50.5 s (16 bars) |
| `ashveil_offer` | Ashveil's offer | ashveil_box, light's ending in minor | St. Louis Blues | D minor | 69 | 55.7 s (16 bars) |
| **Chapter 4 - Chief Architect** | | | | | | |
| `deepest_layer` | the superintelligence: LOOM, ORCHARD, MERIDIAN, TIDEWATER | system (4-voice canon), aron | Wooden Soldiers | C# phrygian | 60 | 64.0 s (16 bars) |
| `captured_earth` | the captured real Earth | system (organ pedal), aron | St. Louis Blues | Db lydian | 63 | 61.0 s (16 bars) |
| `blueprint` | the architect at the blueprint | aron -> light, system (grid) | Wooden Soldiers | D lydian | 96 | 60.0 s (24 bars) |
| `starving` | Ashveil starves himself | ashveil (decaying), aron | St. Louis Blues | A minor | 58 | 49.7 s (12 bars) |
| `office` | the office presentation (last scene) | light | - | C major | 100 | 38.4 s (16 bars) |
| `ovation` | coda: the ovation | light, mira | Somebody Loves Me, Wooden Soldiers | E major | 104 | 55.4 s (24 bars) |
| `worlds_upon_worlds` | coda: worlds upon worlds | light (3-speed canon), system | Ogopogo, Krooked Blues, April Showers, My Buddy | B lydian | 64 | 60.0 s (16 bars) |
| `goldlight` | coda: the light technique | light | April Showers | E lydian | 72 | 53.3 s (16 bars) |
| `the_record` | the record closes | aron (unresolved), light (broken off) | Farewell Blues | F# minor | 60 | 64.0 s (16 bars) |
39

## Minigames

The seven minigames have their own loops and sound effects in
`cues/minigame/`, rendered into `../demo/game/audio/minigame/` (the engine
plays them by name, e.g. `minigame/tower_3`). Shared helpers live in
`cues/minigame/_mg.py` (exact tempo grid, pizzicato, bubble, hungry bass,
beat kick, crush/dive); `_tower.py` builds the four tower tiers.

    python3 examples/music/render.py minigame            # all minigame loops + sfx
    python3 examples/music/render.py minigame/lantern    # one of them
    python3 examples/music/check.py minigame             # loops, levelled against the main score

Every minigame loop is a whole number of bars to the sample (`exact_bpm()`
nudges the tempo by at most a few thousandths of a BPM so the bars fill whole
128-sample blocks).

| cue (`cues/minigame/<name>.py`) | game | motifs | samples | key | BPM | loop |
|---|---|---|---|---|---|---|
| `quiz` | The Big Questions | aron, aron_rising, clock (+ tick-tock) | April Showers | E dorian | 84 | 45.7 s (16 bars) |
| `miso` | Miso's Hunt | miso (minor, pizzicato), aron, system (crushed) | Ogopogo | D minor, swing | 104 | 36.9 s (16 bars) |
| `draw` | Echo of a Shape | aron + its echo, light's last turn | My Buddy | C lydian | 64 | 45.0 s (12 bars) |
| `lantern` | Lantern Rhythm | lantern (in every section), aron answered | My Buddy | E major | 96 exactly | 40.000 s = 1 280 000 samples (16 bars) |
| `snake` | Crown of the Worm | system (as bubbles), aron (grinning) | Krooked Blues, Ogopogo | G dorian | 116 | 33.1 s (16 bars) |
| `tower_1`..`tower_4` | The Tower, tiers 1-4 | aron_rising; tier 4 ends on light | Wooden Soldiers (tiers 2-4) | D minor | 100 / 112 / 124 / 138 | 38.4 / 42.9 / 46.5 / 41.7 s (16 / 20 / 24 / 24 bars) |
| `invaders` | The Hungry Sky | system (fanfare), lantern, ashveil (bass strings) | Wooden Soldiers, St. Louis Blues | B minor | 120 | 48.0 s (24 bars) |
| `invaders_boss` | the energy vampire | ashveil_box, ashveil (as the bass line), lantern | St. Louis Blues | C minor | 96 | 40.0 s (16 bars) |

`lantern` is a rhythm-game grid: beat 1 of bar 1 is sample 0, a warm kick on
every beat, and the density rises every 4 bars (quarters, eighths,
syncopation, fuller). Don't change its tempo or length without the chart.

Sound effects (`cues/minigame/sfx.py`, one generator for all 194 clips: the
192 in `sfx_requests.md`, round 1 (shared, quiz, tower, draw, lantern, snake,
miso, invaders) and round 2 for the redesigned games, plus the leaderboard's
`board_tick` and `board_land`). `invaders_beam` is a seamless loop: periodic
in 1024-sample blocks, so it wraps cleanly even when the encoder drops a
final block).
Each is a function registered with `@sfx(loudness, peak)`, written in its
game's key and timbre: the tower in D minor (vibes, plucks, wood), draw in C
lydian (felt piano, glass, paper), lantern in E major (its hit bells on E5,
pitched per lane at runtime), snake in G dorian (bubbles, bit-crush, dives),
Miso in D minor (pizzicato and the synthesized cat), invaders in B minor and
the boss in C minor (choir, glass, the hungry voice). Each starts on its
first sample with a short ramp, ends on an exact zero, gets the score's soft
top end, and is levelled by loudness with a peak ceiling (transients gently
limited); rapid ones (steps, ticks, clicks) sit 8-12 dB lower. Every clip has
its own random seed, so `SFX=tower_,draw_ python3 examples/music/render.py
minigame/sfx` re-renders just those and matches a full render. The ffmpeg
Vorbis encoder here only writes stereo, so they are dual mono (the engine
folds them to mono), padded with a little silence because the encoder can
drop a final partial block.

## The motifs

All motifs live in `MOTIFS` in vnsynth.py as scale degrees, so each cue
quotes them in its own key and mode (`@n` = n semitones from the root, for
the chromatic ones). Variants: `aron_rising`, `mira_love`, `ashveil_box`, plus
the new `theo` and `miso`.

### Aron: the question (`aron`, `aron_rising`)
`1 - 5 - 4 3 ... 2`: it rises and stops on the second degree, unresolved.
It is stated plainly on vibes in the tutorial `theme` and on glass keys at the
7:07 wake-up, then becomes the thread of chapter 1: counted out over a
proof-like arpeggio in `questions`, softened in the rain, almost answered in
`notebook` (a phrase climbs 3-4-5 and falls back), broken into pieces in
`unraveling`. In chapter 2 it slows to half speed in `fog`, falls past its
own ending in `crash`, and becomes a chopped vocal hook in `club_speed`, sped
up until it nearly sounds like an answer. `group_therapy` gives it its first
half-answer from someone else (2-3-1). On the rooftop it grows:
plain, then `aron_rising` (asked twice, higher), then doubled by strings and
lead. In chapter 3 it is cut off after three notes in `the_leak` and it
argues over Mira in `fight`; in `together_night` it finally lands on her
root. In chapter 4 it shrinks to a ghost in `deepest_layer`, rises in awe in
`captured_earth`, and turns into the Light at the blueprint. In `the_record`
it is unresolved again, exactly as at the start.

### Mira: the warm turn (`mira`, `mira_love`)
`3 4 5 - 3 | 2 - 1`: a step up and a turn home, the only motif that ends on
the root. Domestic in `kitchen_talk`, run by the spirits on a too-jaunty
muted horn in `purgatorium_shift` ("was that line yours or hers?"), and closed
off by a filter during `ambulance_transfer` while the System takes over. In
chapter 2 it grows into the love theme (`mira_love`, climbing to the sixth) in
`mira_visits`. In chapter 3 it is lovely but too exact on vibes in `cafe`,
sour and minor in `fight`, intertwined with Aron's question in
`together_night`, and in `real_world_vigil` the real Mira's version, in the
minor, never reaches home. In `ovation` it answers the Light on guitar.

### The System (`system`)
`1 1 1 - 7,`: three mechanical pulses and a step down, always on exact, cold
timbres (sine pings, woodblock, crushed bits). It is hidden in the rim of the
tutorial, then it is the spirits' time clock, the angels' brass fanfare,
the carrier of the `voices`, and the process creeping under `unraveling`. It
takes over in `ambulance_transfer`, is crushed to bits in `the_leak`, and
becomes four processes in canon in `deepest_layer` (LOOM, ORCHARD, MERIDIAN,
TIDEWATER, each with its own octave, pan and period). The occupier hides in
the organ pedal of `captured_earth`, and in `blueprint` Aron repurposes it as
his drafting grid.

### 7:07: the clock (`clock`)
`1 - - 7 - - 1`: two notes a seventh apart in a 3+3+2 rhythm, a clock that's
slightly wrong. It is the Braun alarm's tick in `theme`, a music box at the
wake-up, the bird landing in `kitchen_talk`. In `unraveling` and
`closed_ward` its seventh bends to the major seventh, wrong in the key. It
skips and sticks in `the_leak`; in `protected_world` it is perfect on every
bar of the muzak except once, 35 cents sharp. In `office` it is only a soft
tick, in time at last.

### The Lantern Watch (`lantern`)
`5 - 5 - 5 - 6 1'`: three soft flickers and a rising answer (the lighthouse
from Aron's dream). It is first a barely-noticed hint on glass harmonica in
`umbrella_rain` (the moment Ember starts watching), then the Watch's own
theme in `lantern_watch`, the sign on the rooftop at bar 8 of
`rooftop_mission`, and in `ember_trial` it plays in the minor with the third
flicker missing until the last phrase.

### Lord Ashveil (`ashveil`, `ashveil_box`)
A slow chromatic descent, root down four semitones: velvet and hungry, but
childlike. It is always two things at once: a toddler's music box (with a
little hungry leap back up) over drones the size of galaxies in `council`,
and a deep string line under the floor. It shadows `ember_trial`, seduces in
`ashveil_offer` (where the music box plays the Light's last four notes in the
minor: the offer sounds like the answer, in the wrong mode), and in
`starving` it decays, each music-box phrase shorter than the last, until one
note is left; then the strings play the whole descent once, high and tender.

### The Light (`light`)
Aron's question completed: `1 - 5 - 4 3 | 2 - 3 - 5 - 1'`. Withheld until
chapter 4, except as Ashveil's counterfeit. It emerges in `blueprint` (eight
bars of the question, then the answer on vibes, then flute), stands plainly
in the Rams-clean `office`, becomes the hook of `ovation`, plays at three
speeds at once in `worlds_upon_worlds` (the same idea in different worlds),
radiates in `goldlight`, and in `the_record` appears only as a ghost that
breaks off before its last note.

### Theo and Miso (`theo`, `miso`)
Theo: a shrug and a grin, a bluesy minor-to-major third (`theo_nights`).
Miso: pounce, pause and a falling "meow" (`miso`, with a tiny synthesized
mew at the end of each loop half; the motif always has the last word).

## The records

| record | used in | treatment |
|---|---|---|
| April Showers (1921) | morning_render, kitchen_talk, questions, unraveling, closed_ward, rooftop_mission, protected_world, the_leak, worlds_upon_worlds, goldlight | the ordinary morning: a radio half-heard, then sour and reversed, frozen behind glass on the ward, a reversed swell of resolve on the rooftop, perfect muzak at its own tempo (one repeat a semitone sharp), and finally stretched into golden haze |
| Krooked Blues (1923) | purgatorium_shift, theo_nights, the_leak, worlds_upon_worlds | stabs on the spirits' shift; Theo's lo-fi loop (slowed 4 semitones, which sets the cue's tempo) |
| Ogopogo (1925) | purgatorium_shift, voices, club_speed, crash, the_leak, miso, worlds_upon_worlds | the shift radio loop at its natural tempo; stuttered on the club floor, then an octave down and reversed for the comedown |
| Parade of the Wooden Soldiers (1923) | angel_ops / entities, voices, ember_trial, deepest_layer, blueprint, ovation | the angels' procedure (slowed a fourth so it drops into the bar), a funeral march at the trial, stretched eightfold into machinery, toy soldiers on the drafting table, distant applause |
| My Buddy (1922) | umbrella_rain, fog, group_therapy, lantern_watch, real_world_vigil, worlds_upon_worlds | companionship and missing someone: the bed of `fog` (stretched, slowed), "a song on the radio" from the Watch, the real Mira's vigil |
| The St. Louis Blues (1925) | council, ashveil_offer, captured_earth, starving | the vampires' record: Bessie Smith and Louis Armstrong pitched down and stretched into a breathing smear, warbling close in the offer, a hymn for the captured Earth, fading as Ashveil starves |
| Somebody Loves Me (1924) | ambulance_transfer, mira_visits, cafe, fight, together_night, ovation | Mira's record: the last warm thing in the ambulance, her swell, the cafe loop, reversed and flat in the fight, faint in the next room, and the ovation's swells |
| Farewell Blues (1923) | notebook, the_record | bookends: already playing far away when the notebook is started, and through a closed door when the record closes |
