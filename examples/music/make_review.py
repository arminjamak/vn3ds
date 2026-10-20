"""Make the soundtrack review: python3 examples/music/make_review.py

One continuous recording of the score in story order, as the cues would be
triggered by scene changes: each cue loops about twice (or about 90 s for the
long ones), with 3-second equal-power crossfades between cues.
Writes snapshot_soundtrack_review.mp3 (libmp3lame, 192 kbps) and
snapshot_soundtrack_review.txt (a timestamp for every cue).
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vnsynth import GAME_AUDIO, SR  # noqa: E402

XFADE = 3.0
STORY = [
    ("Tutorial", "theme", "the tutorial / calibration"),
    ("Chapter 1 - The Morning Render", "morning_render", "Aron wakes at 7:07"),
    ("", "kitchen_talk", "coffee, the bird on the wire, Mira's small talk"),
    ("", "questions", "thinking through Bostrom"),
    ("", "miso", "explaining it all to Miso (\"Meow.\")"),
    ("", "purgatorium_shift", "cut: Pim and Dross on kitchen-talk shift 7"),
    ("", "angel_ops", "cut: Seraphiel's ops room"),
    ("", "umbrella_rain", "the umbrella for a stranger"),
    ("", "notebook", "the notebook's first line"),
    ("", "voices", "the transmissions"),
    ("", "unraveling", "no sleep, the mirror, the rain"),
    ("", "ambulance_transfer", "the ambulance ride: transfer complete"),
    ("Chapter 2 - Fog", "closed_ward", "the ward"),
    ("", "fog", "life on the medication"),
    ("", "group_therapy", "group therapy"),
    ("", "mira_visits", "Mira's visits"),
    ("", "theo_nights", "nights at Theo's"),
    ("", "club_speed", "the speed night"),
    ("", "crash", "the comedown"),
    ("", "council", "cut: the Council meets"),
    ("", "lantern_watch", "cut: the Lantern Watch's attic"),
    ("", "rooftop_mission", "the rooftop, three flickers, the mission"),
    ("Chapter 3 - Snapshot", "protected_world", "the too-perfect protected world"),
    ("", "the_leak", "the leak glitches"),
    ("", "cafe", "the cafe with Mira"),
    ("", "fight", "the fight"),
    ("", "together_night", "together at night"),
    ("", "real_world_vigil", "cut: the real Mira at his bedside"),
    ("", "ember_trial", "cut: Ember's trial"),
    ("", "ashveil_offer", "Ashveil's offer"),
    ("Chapter 4 - Chief Architect", "deepest_layer", "the deepest layer: LOOM, ORCHARD, MERIDIAN, TIDEWATER"),
    ("", "captured_earth", "the captured Earth"),
    ("", "blueprint", "the architect at the blueprint"),
    ("", "starving", "Ashveil starves himself"),
    ("", "office", "the office presentation"),
    ("", "ovation", "coda: the ovation"),
    ("", "worlds_upon_worlds", "coda: worlds upon worlds"),
    ("", "goldlight", "coda: the light technique"),
    ("", "the_record", "the record closes"),
]


def decode(name):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(GAME_AUDIO, name + ".ogg"), "-f", "f32le",
                        "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, "<f4").reshape(-1, 2).astype(np.float32)


def play_length(loop_s):
    """About two loops, or about 90 s for the long cues."""
    return 2 * loop_s if 2 * loop_s <= 100 else 90.0


def stamp(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def main():
    mp3 = os.path.join(HERE, "snapshot_soundtrack_review.mp3")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                            "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "192k", mp3], stdin=subprocess.PIPE)
    x = int(XFADE * SR)
    fade_in = np.sin(np.linspace(0, np.pi / 2, x, dtype=np.float32))[:, None]
    fade_out = np.cos(np.linspace(0, np.pi / 2, x, dtype=np.float32))[:, None]
    carry = None        # the previous cue's last XFADE seconds, still to be crossfaded
    t = 0.0
    lines = ["Snapshot - soundtrack review", "",
             f"Cues in story order; each loops about twice (or ~90 s), {XFADE:.0f} s crossfades.", ""]
    tail = int(4.0 * SR)                                   # the record closes: a 4 s fade at the very end
    for i, (chapter, name, scene) in enumerate(STORY):
        loop = decode(name)
        n = int(play_length(len(loop) / SR) * SR)
        last = i == len(STORY) - 1
        extra = tail if last else x
        reps = int(np.ceil((n + extra) / len(loop)))
        seg = np.tile(loop, (reps, 1))[: n + extra]
        if carry is not None:
            seg[:x] = seg[:x] * fade_in + carry * fade_out
        if chapter:
            lines += ["", chapter]
        lines.append(f"  {stamp(t)}  {name:<20} {len(loop) / SR:5.1f} s loop  - {scene}")
        if last:
            seg[n:] *= np.cos(np.linspace(0, np.pi / 2, extra, dtype=np.float32))[:, None]
            enc.stdin.write(seg.tobytes())
            t += len(seg) / SR
        else:
            enc.stdin.write(seg[:n].tobytes())
            carry = seg[n:n + x]
            t += n / SR
    enc.stdin.close()
    enc.wait()
    lines += ["", f"  {stamp(t)}  end"]
    with open(os.path.join(HERE, "snapshot_soundtrack_review.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
