"""Snapshot's otherworldly places, moving: seamless stereo loops of the
worlds in the soundtrack video (the Remotion + three.js project
snapshot-ost), for the layered scenes in scenes3d.py.

The worlds are raymarched shaders; the 3DS can't run them, so they are
rendered beforehand, in the video's 16:9 framing, once per eye:

    cd snapshot-ost
    OUT=/tmp/raw SHOTS=63,25,... node scripts/render-loops.mjs           # left eyes
    OUT=/tmp/raw SHOTS=63,25,... EYE=0.01 node scripts/render-loops.mjs  # right eyes

(src/gameloops: LOOP_FRAMES frames at 15 fps from the middle of each shot,
the camera slowed down; the right eye is a second camera beside the first,
parallel to it). This script turns each pair into game/loops/<name>.mp4:
8 seconds, the last 1.5 s crossfaded into the start so the loop has no seam,
cropped to the shape of the opening it is seen through, the left eye's view
and the right eye's side by side. vnpack codes them as stereo .cvh clips
(vn3ds.json layers with "stereo": true).

    python3 examples/make_loops.py /tmp/raw
"""

import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo", "game", "loops")

FPS = 15
LOOP = 120     # frames in the loop
FADE = 22      # rendered after the loop, crossfaded into its start

# name: (shot in the soundtrack video, width / height of the opening, view height[, gain])
LOOPS = {
    "purgatorium": (63, 16 / 9, 270),    # the Purgatorium, under every world
    "spawning": (25, 16 / 9, 270),       # its pools, where little lights learn to blink
    "council": (60, 16 / 9, 270),        # the Council of Worlds
    "vampire": (158, 310 / 430, 180),    # Lord Ashveil's window: a world being fed on
    "angel ops": (11, 240 / 420, 180),   # through angel ops' great doors
    "watch": (7, 1.0, 180),              # the Lantern Watch's round window
    "earth": (265, 16 / 9, 270),         # the captured Earth
    "worlds": (396, 16 / 9, 270),        # worlds upon worlds
    "goldlight": (244, 16 / 9, 270),     # the gold, where the Maker speaks
    "foundry": (361, 16 / 9, 270),       # the false god's machine streams
    "shadow": (421, 1.0, 200),           # the mirror realm, in Osric's telescope mirror
    "title": (206, 16 / 9, 270, 0.5),    # the title screen, dimmed under the title
}


def frames(path):
    """All frames of a clip as one uint8 array (n, h, w, 3)."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", path],
                           capture_output=True, text=True, check=True)
    w, h = map(int, probe.stdout.strip().split(","))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def seamless(f):
    """LOOP frames whose end runs into their start: the first FADE frames
    blend from the frames after the loop (which continue its last frame)
    into the loop's own."""
    if len(f) < LOOP + FADE:
        raise ValueError(f"{len(f)} frames, need {LOOP + FADE}")
    out = f[:LOOP].astype(np.float32)
    for i in range(FADE):
        t = (i + 0.5) / FADE
        t = t * t * (3 - 2 * t)
        out[i] = out[i] * t + f[LOOP + i].astype(np.float32) * (1 - t)
    return out


def crop(f, aspect):
    """The middle of the picture at this width / height."""
    h, w = f.shape[1:3]
    if w / h > aspect:
        cw = int(round(h * aspect))
        x = (w - cw) // 2
        return f[:, :, x:x + cw]
    ch = int(round(w / aspect))
    y = (h - ch) // 2
    return f[:, y:y + ch]


def make(name, raw):
    shot, aspect, vh, *gain = LOOPS[name]
    left = os.path.join(raw, f"shot{shot}.mp4")
    right = os.path.join(raw, f"shot{shot}r.mp4")
    if not os.path.exists(left) or not os.path.exists(right):
        print(f"  {name}: no shot{shot}.mp4 / shot{shot}r.mp4 in {raw}, skipped")
        return
    views = [crop(seamless(frames(p)), aspect) for p in (left, right)]
    pair = np.clip(np.concatenate(views, axis=2) * (gain[0] if gain else 1) + 0.5, 0, 255).astype(np.uint8)
    n, h, w = pair.shape[:3]
    vw = int(round(vh * aspect / 2)) * 2
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, name + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                    "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
                    "-vf", f"scale={2 * vw}:{vh}:flags=area,setsar=1", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-an", dst], input=pair.tobytes(), check=True)
    print(f"  {name}: shot {shot}, {2 * vw}x{vh}, {os.path.getsize(dst) // 1024} KiB")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for name in (sys.argv[2:] or LOOPS):
        make(name, sys.argv[1])
