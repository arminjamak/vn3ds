"""vn3ds-record: render a playthrough of a ported game as a video.

    tools/vn3ds-record build/snapshot -o playthrough.mp4 --until chapter2 --choices 0,1,0
    tools/vn3ds-record build/snapshot -o yt.mp4 --reel reel.mp4 --until chapter2

The desktop build of the engine plays the game by itself, holding every line
and menu long enough to read. It writes the top screen (left eye) at 30 fps
and the bottom screen, plus a timestamped log of the audio calls. This script
mixes the music, sound effects and machine voices from that log the way the
3DS does, then encodes a 1920x1080 H.264/AAC video for YouTube (top screen
only) and, with --reel, a 1080x1920 vertical video for Instagram Reels /
Shorts / TikTok (top screen above, bottom screen below, each in half).

Needs ffmpeg, numpy and the desktop build (make -C engine -f Makefile.host).
"""

import argparse
import os
import subprocess
import sys
import tempfile
import threading

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
HOST = os.environ.get("VN3DS_HOST") or os.path.join(ROOT, "engine", "build-host", "vn3ds-host")
RATE = 48000
TOP_W, TOP_H = 400, 240
BOT_W = 320
REC_W = TOP_W + BOT_W            # recorded frame: [top left eye | bottom]
CH_MUSIC, CH_SOUND, CH_VOICE = 0, 1, 2


def say(msg):
    print(f"[vn3ds-record] {msg}", flush=True)


# ---- audio ----------------------------------------------------------------

_cache = {}


def decode(path):
    """Ogg (or anything ffmpeg reads) -> float32 stereo at RATE."""
    if path not in _cache:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2",
                            "-ar", str(RATE), "-"], capture_output=True)
        if r.returncode != 0:
            say(f"could not decode {path}: {r.stderr.decode(errors='replace')[:200]}")
            _cache[path] = np.zeros((1, 2), np.float32)
        else:
            _cache[path] = np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()
    return _cache[path]


def parse_log(path):
    events, bank = [], {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split(" ", 2)
            if len(parts) < 2:
                continue
            try:
                t, kind = float(parts[0]), parts[1]
            except ValueError:      # continuation of a multi-line "line" event
                continue
            rest = parts[2] if len(parts) > 2 else ""
            if kind == "play":
                ch, loop, fadein, queue, p = rest.split(" ", 4)
                events.append((t, "play", int(ch), loop == "1", float(fadein), queue == "1", p))
            elif kind == "stop":
                ch, fade = rest.split()
                events.append((t, "stop", int(ch), float(fade)))
            elif kind == "volume":
                ch, v = rest.split()
                events.append((t, "volume", int(ch), float(v)))
            elif kind == "bank":
                i, p = rest.split(" ", 1)
                bank[int(i)] = p
            elif kind == "vox":
                i, rate, vol = rest.split()
                events.append((t, "vox", int(i), float(rate), float(vol)))
            elif kind == "duck":
                events.append((t, "duck", float(rest)))
            elif kind == "sfxbank":
                i, p = rest.split(" ", 1)
                bank[("sfx", int(i))] = p
            elif kind == "sfx":
                i, vol, rate = rest.split()
                events.append((t, "sfx", int(i), float(vol), float(rate)))
            elif kind == "line":
                events.append((t, "line", rest))
            elif kind in ("pause", "resume"):
                events.append((t, "pause", int(rest), kind == "pause"))
            elif kind == "keys":
                down, held, tx, ty, cx, cy = rest.split()
                events.append((t, "keys", int(down), int(held), int(tx), int(ty),
                               float(cx), float(cy)))
            elif kind == "end":
                events.append((t, "end"))
    return events, bank


def mix(events, bank, duration):
    n = int(duration * RATE) + RATE
    out = np.zeros((n, 2), np.float32)
    # control curves at 100 Hz: channel volume and music duck (step functions)
    cr = 100
    nc = int(duration * cr) + cr + 1
    vol = np.ones((3, nc), np.float32)
    duck = np.ones(nc, np.float32)
    for e in events:
        k = min(nc - 1, int(e[0] * cr))
        if e[1] == "volume" and 0 <= e[2] < 3:
            vol[e[2], k:] = e[3]
        elif e[1] == "duck":
            duck[k:] = e[2]

    def curve(c, a, b):
        idx = np.minimum(nc - 1, (np.arange(a, b) * cr) // RATE)
        return c[idx]

    # playback instances per channel
    inst = []                      # dicts: ch, src, t0, loop, fadein, stop, fadeout
    current = {0: None, 1: None, 2: None}
    queued = {0: [], 1: [], 2: []}

    def natural_end(it):
        if it["loop"]:
            return None
        return it["t0"] + len(it["src"]) / RATE

    def settle(ch, t):
        """Start queued files whose predecessor ended before time t."""
        while queued[ch]:
            cur = current[ch]
            end = None
            if cur is None or cur["stop"] is not None:
                end = cur["stop"] if cur is not None else 0.0
            else:
                end = natural_end(cur)
                if end is None:   # looping: the queue starts after this loop pass
                    period = len(cur["src"]) / RATE
                    passes = max(1, int(np.ceil((t - cur["t0"]) / period)))
                    end = cur["t0"] + passes * period
                    if end > t:
                        return
                    cur["stop"], cur["fadeout"] = end, 0.0
            if end > t:
                return
            loop, p = queued[ch].pop(0)
            it = dict(ch=ch, src=decode(p), t0=end, loop=loop, fadein=0.0, stop=None, fadeout=0.0)
            inst.append(it)
            current[ch] = it

    for e in events:
        t = e[0]
        if e[1] == "play":
            _, _, ch, loop, fadein, queue, p = e
            settle(ch, t)
            cur = current[ch]
            if queue and cur is not None and cur["stop"] is None:
                queued[ch].append((loop, p))
                continue
            if cur is not None and cur["stop"] is None:
                cur["stop"], cur["fadeout"] = t, 0.0
            elif cur is not None and cur["stop"] + cur["fadeout"] > t:
                # still fading out: the 3DS (and Ren'Py) cuts it when the
                # channel starts the next file, it does not keep playing
                # under it (that layered two songs out of beat)
                cur["cut"] = t
            queued[ch] = []
            it = dict(ch=ch, src=decode(p), t0=t, loop=loop, fadein=fadein, stop=None, fadeout=0.0)
            inst.append(it)
            current[ch] = it
        elif e[1] == "stop":
            _, _, ch, fade = e
            settle(ch, t)
            cur = current[ch]
            if cur is not None and cur["stop"] is None:
                cur["stop"], cur["fadeout"] = t, fade
            queued[ch] = []
        elif e[1] == "end":
            for ch in range(3):
                settle(ch, t)

    for it in inst:
        src = it["src"]
        a = int(it["t0"] * RATE)
        stop = it["stop"]
        if stop is None:
            b = n if it["loop"] else a + len(src)
        else:
            b = int((stop + it["fadeout"]) * RATE)
            if "cut" in it:
                b = min(b, int(it["cut"] * RATE))
            if not it["loop"]:
                b = min(b, a + len(src))
        b = min(b, n)
        if b <= a:
            continue
        length = b - a
        if it["loop"]:
            reps = length // len(src) + 1
            sig = np.tile(src, (reps, 1))[:length]
        else:
            sig = src[:length]
        env = np.ones(length, np.float32)
        if it["fadein"] > 0:
            m = min(length, int(it["fadein"] * RATE))
            env[:m] = np.linspace(0, 1, m, dtype=np.float32)
        if stop is not None and it["fadeout"] > 0:
            s0 = int(stop * RATE) - a
            if 0 <= s0 < length:
                # the slope of the fade, also when a cut ends it early
                k = np.arange(length - s0, dtype=np.float32) / (it["fadeout"] * RATE)
                env[s0:] *= np.clip(1 - k, 0, 1)
        if stop is not None and (it["fadeout"] == 0 or "cut" in it):
            k = min(length, 96)    # a 2 ms ramp where a file is cut, against clicks
            env[length - k:] *= np.linspace(1, 0, k, dtype=np.float32)
        env *= curve(vol[it["ch"]], a, b)
        if it["ch"] == CH_MUSIC:
            env *= curve(duck, a, b)
        out[a:b] += sig * env[:, None]

    # machine voices: one syllable at a time; a new one cuts the previous
    vox = [e for e in events if e[1] == "vox"]
    voice_vol = vol[CH_VOICE]
    for i, e in enumerate(vox):
        t, _, idx, rate, v = e
        nvox = sum(1 for k in bank if isinstance(k, int))
        p = bank.get(idx % max(1, nvox)) if nvox else None
        if not p:
            continue
        src = decode(p)
        # rate scales playback speed (and pitch), like ndspChnSetRate
        m = int(len(src) / rate)
        if m < 2:
            continue
        pos = np.arange(m) * rate
        i0 = np.minimum(len(src) - 1, pos.astype(int))
        sig = src[i0]
        a = int(t * RATE)
        if i + 1 < len(vox):
            m = min(m, int(vox[i + 1][0] * RATE) - a)
        m = min(m, n - a)
        if m <= 0:
            continue
        g = v * voice_vol[min(nc - 1, int(t * cr))]
        tail = np.ones(m, np.float32)
        k = min(m, 96)
        tail[-k:] = np.linspace(1, 0, k)   # avoid clicks where a syllable is cut
        out[a:a + m] += sig[:m] * (g * tail)[:, None]
    # minigame sound effects: polyphonic, each plays to its end
    for e in events:
        if e[1] != "sfx":
            continue
        t, _, idx, v, rate = e
        p = bank.get(("sfx", idx))
        if not p:
            continue
        src = decode(p)
        m = int(len(src) / max(rate, 0.05))
        if m < 2:
            continue
        sig = src[np.minimum(len(src) - 1, (np.arange(m) * rate).astype(int))]
        a = int(t * RATE)
        m = min(m, n - a)
        if m > 0:
            out[a:a + m] += sig[:m] * v
    return out[: int(duration * RATE)]


# ---- input timeline ---------------------------------------------------------

BUTTONS = [("A", 1 << 0), ("B", 1 << 1), ("X", 1 << 2), ("Y", 1 << 3), ("L", 1 << 4),
           ("R", 1 << 5), ("start", 1 << 6), ("select", 1 << 7), ("up", 1 << 8),
           ("down", 1 << 9), ("left", 1 << 10), ("right", 1 << 11), ("touch", 1 << 12),
           ("ZL", 1 << 13), ("ZR", 1 << 14)]
FRAME = 1 / 60


def input_timeline(events):
    """The auto-player's presses from the host's "keys" log: one entry per
    press with its start time and how long it was held (a one-frame tap is
    1/60 s), touches with their path, and circle-pad moves."""
    presses, open_, pad, last_pad = [], {}, [], (0.0, 0.0)
    for e in events:
        if e[1] != "keys":
            continue
        t, _, down, held, tx, ty, cx, cy = e
        active = down | held
        for name, bit in BUTTONS:
            if bit & active and name not in open_:
                p = {"t": round(t, 4), "button": name, "duration": FRAME}
                if name == "touch":
                    p["x"], p["y"], p["path"] = tx, ty, [[round(t, 4), tx, ty]]
                presses.append(p)
                open_[name] = p
            elif name in open_:
                p = open_[name]
                if bit & held:
                    if name == "touch" and p["path"][-1][1:] != [tx, ty]:
                        p["path"].append([round(t, 4), tx, ty])
                else:
                    p["duration"] = round(max(FRAME, t - p["t"]), 4)
                    del open_[name]
                    if bit & down:          # released and pressed again
                        q = {"t": round(t, 4), "button": name, "duration": FRAME}
                        presses.append(q)
                        open_[name] = q
            if name in open_ and not (bit & held) and open_[name]["t"] == round(t, 4):
                del open_[name]             # a tap: down for this frame only
        if (cx, cy) != last_pad:
            pad.append({"t": round(t, 4), "x": cx, "y": cy})
            last_pad = (cx, cy)
    for p in presses:
        p["duration"] = round(p["duration"], 4)
        if p.get("path") is not None and len(p["path"]) < 2:
            del p["path"]
    return {"clock": "seconds from the first video frame (30 fps: frame n at n/30)",
            "presses": presses, "circle_pad": pad}


# ---- driver ---------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="vn3ds-record", description=__doc__.split("\n\n")[0])
    ap.add_argument("game", help="a ported game folder (output of vn3ds-port / vnpack)")
    ap.add_argument("-o", "--output", default="playthrough.mp4", help="16:9 video (YouTube)")
    ap.add_argument("--reel", metavar="FILE", help="also write a 9:16 vertical video")
    ap.add_argument("--screens", metavar="PREFIX",
                    help="also write the plain screens in high quality: PREFIX-top.mp4 (400x240, "
                         "left eye) and PREFIX-bottom.mp4 (320x240)")
    ap.add_argument("--audio-out", metavar="FILE", help="also write the soundtrack (.wav or .m4a)")
    ap.add_argument("--inputs", metavar="FILE",
                    help="also write the auto-player's button presses as JSON")
    ap.add_argument("--no-youtube", action="store_true",
                    help="skip the 16:9 video (-o then only names the transcripts)")
    ap.add_argument("--until", metavar="LABEL", help="stop when the script reaches this label")
    ap.add_argument("--label", help="start at this label instead of the title screen")
    ap.add_argument("--minigame", metavar="ID", help="record one minigame played by its bot")
    ap.add_argument("--choices", default="", help="menu picks in order, e.g. 0,1,0 (0 after that)")
    ap.add_argument("--max-lines", type=int, default=0)
    ap.add_argument("--crf", type=int, default=16, help="x264 quality (lower = better)")
    ap.add_argument("--keep", action="store_true", help="keep the intermediate files")
    args = ap.parse_args(argv)

    if not os.path.exists(HOST):
        sys.exit("vn3ds-record: build the desktop engine first: make -C engine -f Makefile.host")
    work = tempfile.mkdtemp(prefix="vn3ds-record-")
    fifo = os.path.join(work, "frames.rgb")
    os.mkfifo(fifo)
    alog = os.path.join(work, "audio.txt")
    silent = os.path.join(work, "video.mp4")

    # YouTube: the top screen x4.5 (1800x1080), centred on a 1920x1080 frame.
    # Reel: 1080x1920; the top screen fills the upper half and the bottom
    # screen the lower half, each over a blurred, darkened copy of itself.
    yt = (f"[0:v]crop={TOP_W}:{TOP_H}:0:0,scale=1800:1080:flags=lanczos,"
          "pad=1920:1080:60:0:black,format=yuv420p[yt]")
    graph = yt
    outs = [("[yt]", silent, ["-preset", "slow", "-crf", str(args.crf), "-tune", "animation"])]
    if args.screens or args.no_youtube:
        # one split feeding every output; each branch crops what it needs
        branches = []
        if not args.no_youtube:
            branches.append(f"crop={TOP_W}:{TOP_H}:0:0,scale=1800:1080:flags=lanczos,"
                            "pad=1920:1080:60:0:black,format=yuv420p[yt]")
        else:
            outs = []
        # RGB, no chroma subsampling, visually lossless (about 55 dB PSNR)
        lossless = ["-c:v", "libx264rgb", "-preset", "medium", "-crf", "8", "-tune", "animation"]
        if args.screens:
            branches.append(f"crop={TOP_W}:{TOP_H}:0:0[stop]")
            branches.append(f"crop={BOT_W}:{TOP_H}:{TOP_W}:0[sbot]")
            outs += [("[stop]", os.path.abspath(args.screens + "-top.mp4"), lossless),
                     ("[sbot]", os.path.abspath(args.screens + "-bottom.mp4"), lossless)]
        graph = (f"[0:v]split={len(branches)}" + "".join(f"[s{i}]" for i in range(len(branches)))
                 + ";" + ";".join(f"[s{i}]{b}" for i, b in enumerate(branches)))
    if args.reel and (args.screens or args.no_youtube):
        sys.exit("vn3ds-record: --reel cannot be combined with --screens / --no-youtube")
    if args.reel:
        reel_silent = os.path.join(work, "reel.mp4")

        def half(src, w, label):
            return (f"[{src}]split[{label}a][{label}b];"
                    f"[{label}a]scale=-2:960:flags=bicubic,crop=1080:960,boxblur=24:2,"
                    f"eq=brightness=-0.18:saturation=0.8[{label}bg];"
                    f"[{label}b]scale=1080:-2:flags=lanczos[{label}fg];"
                    f"[{label}bg][{label}fg]overlay=(W-w)/2:(H-h)/2[{label}]")
        graph = (f"[0:v]split[v1][v2];"
                 f"[v1]crop={TOP_W}:{TOP_H}:0:0,scale=1800:1080:flags=lanczos,"
                 f"pad=1920:1080:60:0:black,format=yuv420p[yt];"
                 f"[v2]split[t0][b0];[t0]crop={TOP_W}:{TOP_H}:0:0[tsrc];"
                 f"[b0]crop={BOT_W}:{TOP_H}:{TOP_W}:0[bsrc];"
                 + half("tsrc", TOP_W, "top") + ";" + half("bsrc", BOT_W, "bot") + ";"
                 "[top][bot]vstack,format=yuv420p[reel]")
        outs.append(("[reel]", reel_silent, ["-preset", "medium", "-crf", str(args.crf + 2),
                                             "-maxrate", "12M", "-bufsize", "24M"]))
    ff = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
          "-s", f"{REC_W}x{TOP_H}", "-r", "30", "-i", fifo, "-filter_complex", graph]
    for label, path, opts in outs:
        codec = [] if "-c:v" in opts else ["-c:v", "libx264"]
        ff += ["-map", label, *codec, *opts, "-g", "60", "-bf", "2",
               "-movflags", "+faststart", path]
    enc = subprocess.Popen(ff)

    cmd = [HOST, os.path.abspath(args.game), "--record", fifo, "--audio-log", alog, "--pace",
           "--root", os.path.join(work, "root"), "--choices", args.choices]
    if args.until:
        cmd += ["--stop-label", args.until]
    if args.label:
        cmd += ["--label", args.label]
    if args.max_lines:
        cmd += ["--max-lines", str(args.max_lines)]
    if args.minigame:
        cmd += ["--minigame", args.minigame]
    say("playing the game (the transcript goes to transcript.txt)")
    with open(os.path.join(work, "transcript.txt"), "w") as tr:
        host = subprocess.run(cmd, stdout=tr, stderr=subprocess.STDOUT)
    enc.wait()
    if host.returncode != 0 or enc.returncode != 0:
        sys.exit(f"vn3ds-record: playback or encoding failed; see {work}/transcript.txt")

    events, bank = parse_log(alog)
    duration = max((e[0] for e in events if e[1] == "end"), default=0.0)
    say(f"mixing {duration / 60:.1f} minutes of audio")
    audio = mix(events, bank, duration)
    peak = float(np.abs(audio).max()) if audio.size else 0.0
    if peak > 0.98:
        audio *= 0.98 / peak
    wav = os.path.join(work, "audio.f32")
    audio.astype("<f4").tofile(wav)

    say("muxing")
    targets = ([] if args.no_youtube else [(silent, args.output)]) + \
        ([(reel_silent, args.reel)] if args.reel else [])
    if args.audio_out:
        aac = [] if args.audio_out.lower().endswith(".wav") else ["-c:a", "aac", "-b:a", "320k"]
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(RATE), "-ac", "2", "-i", wav,
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(RATE), *aac,
             os.path.abspath(args.audio_out)])
        if r.returncode != 0:
            sys.exit(f"vn3ds-record: writing {args.audio_out} failed")
    if args.inputs:
        import json
        tl = input_timeline(events)
        with open(args.inputs, "w") as f:   # one press per line
            f.write('{"clock": %s,\n"presses": [\n' % json.dumps(tl["clock"]))
            f.write(",\n".join(json.dumps(p) for p in tl["presses"]))
            f.write('\n],\n"circle_pad": [\n')
            f.write(",\n".join(json.dumps(p) for p in tl["circle_pad"]))
            f.write("\n]}\n")
    for video, dest in targets:
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", video,
             "-f", "f32le", "-ar", str(RATE), "-ac", "2", "-i", wav,
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(RATE),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest",
             "-movflags", "+faststart", os.path.abspath(dest)])
        if r.returncode != 0:
            sys.exit(f"vn3ds-record: muxing {dest} failed")
    with open(os.path.splitext(args.output)[0] + "-lines.txt", "w") as f:
        for e in events:
            if e[1] == "line":
                m, sec = divmod(e[0], 60)
                f.write(f"{int(m):02d}:{sec:05.2f}  {e[2]}\n")
    if args.keep:
        say(f"intermediate files kept in {work}")
    else:
        for f in (wav, silent, fifo) + ((reel_silent,) if args.reel else ()):
            try:
                os.remove(f)
            except OSError:
                pass
        os.replace(os.path.join(work, "transcript.txt"), os.path.splitext(args.output)[0] + ".txt")
    extra = [args.screens + "-top.mp4", args.screens + "-bottom.mp4"] if args.screens else []
    say("done: " + ", ".join([d for _, d in targets] + extra +
                             [x for x in (args.audio_out, args.inputs) if x]))


if __name__ == "__main__":
    main()
