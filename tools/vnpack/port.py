"""vn3ds-port: port a Ren'Py game to the Nintendo 3DS in one command.

    tools/vn3ds-port GAME [MORE INPUTS...] [--sd /Volumes/3DS | --3ds IP]

With no destination given it finds one: the 3DS's SD card if it is plugged
into this computer (best quality, copied there with vn3ds), otherwise the 3DS
on the Wi-Fi (compact quality). Over Wi-Fi it first sends vn3ds itself
through the Homebrew Launcher's netloader when vn3ds isn't open yet, then
the game, in one go. It waits for the 3DS and retries dropped connections
until everything has arrived.

GAME can be any of the shapes Ren'Py games are shipped in (or a folder that
vn3ds-port already produced, which is then just delivered):
  - a Ren'Py project folder, or its game/ folder
  - a PC / Linux build folder (Game-1.0-pc/), or a Mac app (Game.app)
  - an Android .apk (read in place, never unpacked)
  - a .zip download (unpacked to a work folder only as far as needed)
  - extra .rpa archives or folders that belong to the same game
    (e.g. an Android build that ships its art as a separate archive.rpa)

Compiled-only games (.rpyc, no .rpy) are decompiled automatically with the
bundled unrpyc. The result is a folder for sdmc:/3ds/vn3ds/games/, plus a
compatibility report.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter

from . import __main__ as vnpack
from .assets import AssetFS

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = bool(getattr(sys, "frozen", False))
if FROZEN:   # a PyInstaller build: everything sits next to the program
    REPO = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    UNRPYC = os.path.join(REPO, "unrpyc", "unrpyc.py")
else:
    REPO = os.path.dirname(os.path.dirname(HERE))
    UNRPYC = os.path.join(REPO, "tools", "third_party", "unrpyc", "unrpyc.py")
ENGINE_3DSX = os.environ.get("VN3DS_ENGINE") or os.path.join(REPO, "engine", "vn3ds.3dsx")
GAME_EXTS = (".rpy", ".rpyc", ".rpa")


class PortError(SystemExit):
    """A problem with the inputs. A SystemExit, so the command line exits
    with the message as before; the app catches it and shows it."""


def say(msg):
    print(f"[vn3ds-port] {msg}", flush=True)


def unrpyc_command():
    """How to run the bundled unrpyc. A frozen build has no separate Python:
    it runs itself with --vn3ds-unrpyc (see run_unrpyc)."""
    if FROZEN:
        return [sys.executable, "--vn3ds-unrpyc"]
    return [sys.executable, UNRPYC]


def run_unrpyc(argv):
    """unrpyc's command line, in this process (for frozen builds)."""
    folder = os.path.dirname(UNRPYC)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import unrpyc   # noqa: E402 - bundled third-party module
    sys.argv = ["unrpyc"] + list(argv)
    unrpyc.main()


def has_game_files(folder):
    try:
        return any(fn.lower().endswith(GAME_EXTS) for fn in os.listdir(folder))
    except OSError:
        return False


def find_game_dir(folder):
    """The folder Ren'Py would treat as game/ inside a project or build."""
    if os.path.basename(folder.rstrip("/")) == "game" and has_game_files(folder):
        return folder
    direct = os.path.join(folder, "game")
    if os.path.isdir(direct) and has_game_files(direct):
        return direct
    # PC/Mac builds bury it a little deeper (Game.app/Contents/Resources/autorun/game).
    for root, dirs, _ in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in ("renpy", "lib", "__pycache__", "cache", "saves")]
        if os.path.basename(root) == "game" and has_game_files(root):
            return root
    if has_game_files(folder):
        return folder
    return None


def unpack_zip(path, work, progress=None):
    """Unpack a downloaded .zip as far as needed: game files and nested
    archives. Returns the folder holding them. progress(done, total)."""
    dest = os.path.join(work, "unzipped", os.path.splitext(os.path.basename(path))[0])
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(path) as z:
        wanted = [i for i in z.infolist() if not i.is_dir() and (
            i.filename.lower().endswith(GAME_EXTS + (".apk", ".zip")) or "/game/" in "/" + i.filename)]
        total = sum(i.file_size for i in wanted)
        free = shutil.disk_usage(work).free
        if total > free * 0.9:
            raise PortError(f"vn3ds-port: unpacking {path} needs {total >> 20} MiB but only "
                     f"{free >> 20} MiB are free in {work}; pass --work on a bigger disk")
        if progress is None:
            say(f"unpacking {len(wanted)} files ({total >> 20} MiB) from {os.path.basename(path)}")
        for k, i in enumerate(wanted):
            z.extract(i, dest)
            if progress:
                progress(k + 1, len(wanted))
    return dest


def collect(inputs, work, progress=None):
    """Turn the user's inputs into (primary, overlay folders)."""
    primary, overlays = None, []
    queue = list(inputs)
    while queue:
        item = os.path.abspath(queue.pop(0))
        low = item.lower()
        if os.path.isdir(item):
            gd = find_game_dir(item)
            nested = [os.path.join(r, f) for r, _, fs in os.walk(item) for f in fs
                      if f.lower().endswith((".apk", ".zip"))]
            if gd is None and not nested:
                raise PortError(f"vn3ds-port: no Ren'Py game files in {item}")
            if gd:
                if primary is None:
                    primary = gd
                else:
                    overlays.append(gd)
            queue += nested
        elif low.endswith(".apk"):
            if primary is None or not primary.lower().endswith(".apk"):
                if primary is not None:
                    overlays.append(primary)
                primary = item
        elif low.endswith(".zip"):
            queue.append(unpack_zip(item, work, progress))
        elif low.endswith(".rpa"):
            overlays.append(os.path.dirname(item))
        else:
            raise PortError(f"vn3ds-port: don't know what to do with {item}")
    if primary is None:
        raise PortError("vn3ds-port: no game found in the inputs")
    # An apk with its art shipped beside it: the folder is an overlay.
    return primary, [o for o in dict.fromkeys(overlays) if o != primary]


def decompile_if_needed(primary, overlays, work, started=None):
    fs = AssetFS(primary, lambda *a: None, overlay_dirs=overlays)
    keys = [k for k in fs.keys() if not k.startswith(("renpy/", "tl/"))]
    if any(k.endswith(".rpy") for k in keys):
        return None
    rpyc = [k for k in keys if k.endswith(".rpyc")]
    if not rpyc:
        raise PortError("vn3ds-port: no scripts (.rpy or .rpyc) in the game")
    out = os.path.join(work, "scripts")
    os.makedirs(out, exist_ok=True)
    for k in rpyc:
        dest = os.path.join(out, fs.display(k))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(fs.read(k))
    if started:
        started(len(rpyc))
    else:
        say(f"only compiled scripts found; decompiling {len(rpyc)} .rpyc files with unrpyc")
    kw = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if os.name == "nt" else {}
    r = subprocess.run(unrpyc_command() + ["-c", out], capture_output=True, text=True, **kw)
    made = sum(1 for _, _, fs_ in os.walk(out) for f in fs_ if f.endswith(".rpy"))
    if made == 0:
        raise PortError("vn3ds-port: unrpyc could not decompile the scripts:\n" +
                        r.stdout[-2000:] + r.stderr[-2000:])
    if made < len(rpyc):
        say(f"warning: only {made} of {len(rpyc)} scripts decompiled")
    for root, _, files in os.walk(out):   # keep only the .rpy text
        for f in files:
            if f.endswith(".rpyc"):
                os.remove(os.path.join(root, f))
    return out


CATEGORIES = [
    ("screens (UI built with screen language)", r"screen|style statements"),
    ("Python beyond simple assignments", r"python|cannot evaluate|call to|unsupported expression"),
    ("animated / movie images", r"Movie|animated|displayable"),
    ("missing files", r"not found|not defined"),
    ("transitions approximated", r"transition"),
    ("ATL features", r"ATL"),
    ("other", r""),
]


def report(summary, path):
    by_cat = Counter()
    examples = {}
    for (where, msg), n in summary["warnings"].items():
        for name, pat in CATEGORIES:
            if re.search(pat, msg):
                by_cat[name] += n
                examples.setdefault(name, f"{where}: {msg}" if where else msg)
                break
    lines = [
        f"{summary['title']}  ->  sdmc:/3ds/vn3ds/games/{summary['id']}/",
        f"  {summary['labels']} labels, {summary['images']} images "
        f"({summary['texture_bytes'] >> 20} MiB), {summary['audio']} of "
        f"{summary['audio_refs']} audio files, script {summary['script_bytes'] >> 10} KiB, "
        f"virtual screen {summary['screen'][0]}x{summary['screen'][1]}",
    ]
    if by_cat:
        lines.append("  Skipped or approximated (the story still plays; these parts are left out):")
        for name, _ in CATEGORIES:
            if by_cat[name]:
                lines.append(f"    {by_cat[name]:6d}  {name}   e.g. {examples[name][:110]}")
    else:
        lines.append("  Everything converted.")
    if summary.get("outcomes"):
        lines.append(f"  {len(summary['outcomes'])} custom minigame screens vn3ds can't play "
                     f"show a card where the player chooses the outcome.")
    grids = summary.get("music_grids") or []
    if grids:
        ok = sum(1 for g in grids if g[2])
        lines.append(f"  Music: {ok} of {len(grids)} tracks got a measured tempo grid (music "
                     f"changes land on the loop's end or a phrase); the rest crossfade.")
    if summary.get("video_3d"):
        lines.append("  Movies are in stereoscopic 3D (a right-eye view made from estimated depth; "
                     "New 3DS).")
    text = "\n".join(lines)
    with open(path, "w") as f:
        f.write(text + "\n")
        outs = summary.get("outcomes") or []
        if outs:
            f.write("\nMinigames vn3ds can't play (a card lets the player choose the outcome):\n")
            for screen, how, labels in outs:
                f.write(f"  {screen}: {' / '.join(labels)}  (from {how})\n")
        if grids:
            f.write("\nMeasured music grids (confidence 0-1):\n")
            for name, conf, e, why in grids:
                f.write(f"  {name}: " + (f"{e['bpm']:g} bpm, {e['beats_per_bar']}/bar, phrase "
                                         f"{e['phrase_bars']} bars, loop {e['bars'] or '?'} bars"
                                         if e else f"no grid ({why})") + f", confidence {conf:.2f}\n")
        f.write("\nAll warnings:\n")
        for (where, msg), n in summary["warnings"].items():
            f.write(f"{where + ': ' if where else ''}{msg}{f' (x{n})' if n > 1 else ''}\n")
    return text


def install(out_dir, game_id, sd, engine=None):
    """Copy a ported game (and vn3ds.3dsx) onto an SD card."""
    from . import flow
    dest = os.path.join(sd, "3ds", "vn3ds", "games", game_id)
    say(f"copying to {dest}")
    flow.install_game_sd(out_dir, game_id, sd)
    engine = engine or ENGINE_3DSX
    if os.path.exists(engine):
        flow.install_engine_sd(sd, engine)
    else:
        say("engine/vn3ds.3dsx isn't built yet (run make in engine/); copy it to sdmc:/3ds/ yourself")


# What each quality mode asks of the packager. Options the packager doesn't
# know yet are left out, so this works while features are being added. Both
# keep the pictures, sounds and videos in pack files (the packager's default).
# Wi-Fi, the smallest that still looks and sounds good: Opus audio (mono,
# 14-20 kbps), ffmpeg's trellis JPEG at quantiser 5.5 decoded to RGB565,
# near-duplicate CGs as patches, JPEG movie posters, H.264 at 100 kbps /
# 20 fps (Eternum: ~290 MB).
# SD card, close to the original: trellis JPEG at quantiser 2 (about 45 dB
# PSNR, a third of the old zlib RGB8 size) decoded to RGB8 textures, CG
# patches (no loss: the patch is the same JPEG as the whole picture would be),
# the game's own Ogg Vorbis / Opus files untouched and anything else as Opus
# at 96 kbps stereo, H.264 at 450 kbps / 30 fps.
QUALITY = {
    "wifi": [("--audio-profile", "wifi"), ("--jpeg", "75"), ("--rgb565", None),
             ("--jpeg-encoder", "ffmpeg"), ("--jpeg-qscale", "5.5"), ("--cg-patches", None),
             ("--jpeg-posters", None),
             ("--video-codec", "h264"), ("--video-kbps", "100"), ("--video-fps", "20")],
    "sd": [("--audio-profile", "sd"), ("--jpeg", "92"), ("--jpeg-rgb8", None),
           ("--jpeg-encoder", "ffmpeg"), ("--jpeg-qscale", "2"), ("--cg-patches", None),
           ("--jpeg-posters", None),
           ("--video-codec", "h264"), ("--video-kbps", "450"), ("--video-fps", "30")],
}


# Stereoscopic movies (vnpack --video-3d, on whenever the depth model and
# onnxruntime are there): both eyes' views side by side at 1.5x the 2D
# bitrate, which keeps the left view as good as the 2D movie and the right
# one 1.5-2 dB below it (tools/vnpack/stereo.py).
VIDEO_3D_KBPS = {"wifi": 150, "sd": 675}


def video_3d_wanted(opts):
    """Whether this conversion makes 3D movies: --video-3d / --no-video-3d,
    else whenever it can."""
    on = getattr(opts, "video_3d", None)
    if on is False or opts.no_video or (opts.video_codec or "h264") != "h264":
        return False
    if on:
        return True
    from . import stereo
    return stereo.available() is not None


# Per-file sizes the presets come out at, measured on Eternum's Wi-Fi
# edition (12,702 textures in 104 MiB) and Snapshot's pictures (sd's JPEG at
# quantiser 2 is 1.7x the Wi-Fi one); audio and video by their length.
EST_PICTURE = {"wifi": 8.4e3, "sd": 14.5e3}
EST_AUDIO_BPS = {"wifi": 20e3 / 8, "sd": 96e3 / 8}     # transcoded audio
EST_VIDEO_BPS = {"wifi": 100e3 / 8, "sd": 450e3 / 8}
EST_VIDEO_3D_BPS = {q: k * 1e3 / 8 for q, k in VIDEO_3D_KBPS.items()}
MOVIE_EXTS = (".webm", ".mp4", ".ogv", ".mkv", ".avi", ".mpg", ".mpeg", ".mov")


def _seconds(data):
    """Length of an audio or video file (in memory) by ffprobe, or None."""
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        with tempfile.NamedTemporaryFile() as f:   # (piped, many formats have no length)
            f.write(data)
            f.flush()
            r = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration", "-of",
                                "default=nw=1:nk=1", f.name], capture_output=True, timeout=60)
        return float(r.stdout.decode().strip().splitlines()[0])
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


def estimate(primary, overlays):
    """Roughly how big the converted game will be, per preset, from the
    game's file list and the length of a sample of its sounds and movies
    (a few seconds). {"wifi": bytes, "sd": bytes} or None."""
    import random
    from .assets import AUDIO_EXTS, IMAGE_EXTS, AssetFS
    try:
        fs = AssetFS(primary, lambda *a: None, overlay_dirs=overlays)
    except OSError:
        return None
    keys = [k for k in fs.keys() if not k.startswith(("renpy/", "tl/", "gui/", "cache/"))]
    pictures = sum(1 for k in keys if k.endswith(IMAGE_EXTS))
    audio = [k for k in keys if k.endswith(tuple(AUDIO_EXTS))]
    movies = [k for k in keys if k.endswith(MOVIE_EXTS)]
    rnd = random.Random(1)

    def seconds_per_byte(ks, n):
        sample = rnd.sample(ks, min(n, len(ks)))
        secs = byts = 0
        for k in sample:
            data = fs.read(k)
            t = _seconds(data)
            if t:
                secs, byts = secs + t, byts + len(data)
        return secs / byts if byts else 0.0
    a_bytes = sum(fs.size(k) for k in audio)
    a_secs = a_bytes * seconds_per_byte(audio, 12)
    ogg_bytes = sum(fs.size(k) for k in audio if k.endswith((".ogg", ".opus", ".oga")))
    other_secs = (a_bytes - ogg_bytes) * seconds_per_byte(
        [k for k in audio if not k.endswith((".ogg", ".opus", ".oga"))] or audio, 6)
    m_secs = sum(fs.size(k) for k in movies) * seconds_per_byte(movies, 6) if movies else 0
    out = {}
    for q in ("wifi", "sd"):
        audio_q = a_secs * EST_AUDIO_BPS["wifi"] if q == "wifi" else \
            ogg_bytes + other_secs * EST_AUDIO_BPS["sd"]
        out[q] = int(pictures * EST_PICTURE[q] + audio_q + m_secs * EST_VIDEO_BPS[q] +
                     len(movies) * EST_PICTURE[q])
        out[q + "_3d"] = int(m_secs * (EST_VIDEO_3D_BPS[q] - EST_VIDEO_BPS[q]))
    out["movie_seconds"] = m_secs
    return out


def quality_args_src():
    """The packager's source, to see which options it knows ("" when frozen:
    then it is the matching one and knows them all)."""
    try:
        return open(os.path.join(os.path.dirname(__file__), "__main__.py"), encoding="utf-8").read()
    except OSError:
        return "--video-3d"


def quality_args(mode):
    try:
        src = open(os.path.join(os.path.dirname(__file__), "__main__.py"), encoding="utf-8").read()
    except OSError:   # a frozen build has no sources: the packager is the matching one
        src = None
    out = []
    for flag, val in QUALITY.get(mode, []):
        if src is None or f'"{flag}"' in src:
            out += [flag] + ([val] if val is not None else [])
    return out


def vnpack_args(opts, quality, primary, overlays, scripts):
    """The packager's command line for these options (the same for the
    command line and the app, so both produce the same files)."""
    vargs = [primary, "-o", opts.output, "-q"]
    for o in ([scripts] if scripts else []) + overlays:
        vargs += ["--scripts", o]
    for flag, val in (("--id", opts.id), ("--title", opts.title), ("-j", opts.jobs or None)):
        if val:
            vargs += [flag, str(val)]
    for flag in ("rgb565", "no_audio", "no_video", "fit"):
        if getattr(opts, flag):
            vargs.append("--" + flag.replace("_", "-"))
    vargs += quality_args(quality)
    if video_3d_wanted(opts) and "--video-3d" in "".join(quality_args_src()):
        vargs += ["--video-3d", "--video-3d-kbps", str(VIDEO_3D_KBPS.get(quality, 150))]
    for flag, val in (("--video-codec", opts.video_codec), ("--video-kbps", opts.video_kbps),
                      ("--video-fps", getattr(opts, "video_fps", None)),
                      ("--jpeg-encoder", getattr(opts, "jpeg_encoder", None)),
                      ("--jpeg-qscale", getattr(opts, "jpeg_qscale", None))):
        if val:   # after the quality preset, so these win
            vargs += [flag, str(val)]
    for flag in ("cg_patches", "jpeg_posters"):
        on = getattr(opts, flag, None)
        opt = "--" + flag.replace("_", "-")
        if on and opt not in vargs:
            vargs.append(opt)
        elif on is False and opt in vargs:   # --no-cg-patches / --no-jpeg-posters
            vargs.remove(opt)
    if opts.jpeg is not None:
        vargs += ["--jpeg", str(opts.jpeg)]
    return vargs


def convert(opts, quality, ui):
    """Convert opts.inputs into a game folder under opts.output, reporting
    the steps to ui (see flow.UI). Returns vnpack's summary plus "report"
    (the compatibility report's text)."""
    from . import flow
    work = opts.work or tempfile.mkdtemp(
        prefix="vn3ds-port-", dir=os.path.dirname(os.path.abspath(opts.output)) or ".")
    os.makedirs(work, exist_ok=True)
    os.makedirs(opts.output, exist_ok=True)
    unpacked = []

    def unpack_progress(done, total):
        unpacked.append(1)
        ui.step("unpack", "active", "", done=done, total=total)
        if ui.stopped():
            raise flow.Cancelled()
    try:
        primary, overlays = collect(opts.inputs, work, unpack_progress)
        ui.step("unpack", "done" if unpacked else "skip", "")
        ui.log(f"game: {primary}" + (f" (+ {len(overlays)} more)" if overlays else ""))
        if ui.stopped():
            raise flow.Cancelled()
        scripts = decompile_if_needed(
            primary, overlays, work,
            started=lambda n: ui.step("decompile", "active", f"{n} compiled scripts (unrpyc)"))
        ui.step("decompile", "done" if scripts else "skip",
                "with unrpyc" if scripts else "")
        est = estimate(primary, overlays) if getattr(opts, "estimate", True) else None
        v3d = video_3d_wanted(opts)
        if est:
            other = "sd" if quality == "wifi" else "wifi"
            if v3d:
                for q in (quality, other):
                    est[q] += est[q + "_3d"]
            ui.log(f"projected size: about {est[quality] / 1e6:.0f} MB ({quality}); the "
                   f"{other} preset would be about {est[other] / 1e6:.0f} MB "
                   f"(--quality {other})")
            if v3d and est["movie_seconds"]:
                ui.log(f"3D movies ({est['movie_seconds'] / 60:.0f} min): about "
                       f"{est[quality + '_3d'] / 1e6:.0f} MB more than 2D ones "
                       f"(--no-video-3d for 2D)")
        seen = set()

        def progress(step, state=None, done=None, total=None, **info):
            if ui.stopped():
                raise flow.Cancelled()
            seen.add(step)
            if step == "scripts":
                ui.step("scripts", state, f"{info['labels']} labels" if state == "done" else "")
            elif step == "pack":
                ui.step("pack", state, f"{info['bytes'] / 1e6:.1f} MB" if state == "done" else "")
            else:
                if total == 0:
                    ui.step(step, "skip")
                else:
                    ui.step(step, state or "active", "", done=done, total=total)
        summary = vnpack.main(vnpack_args(opts, quality, primary, overlays, scripts), progress)
        if "video" not in seen:
            ui.step("video", "skip")
        text = report(summary, os.path.join(summary["out_dir"], "port-report.txt"))
        summary["report"] = text
        ui.log(text)
        return summary
    finally:
        if not opts.keep_work and not opts.work:
            shutil.rmtree(work, ignore_errors=True)


def default_output():
    """build/ next to where the command runs; a frozen build keeps its
    games in the user's data folder instead."""
    if not FROZEN:
        return "build"
    return os.path.join(user_data_dir(), "games")


def user_data_dir():
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "vn3ds")


def clean_path(arg):
    """A path as a terminal pastes it when a file is dragged in: maybe in
    quotes, maybe with backslash-escaped spaces, maybe with a trailing space."""
    p = arg.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in "'\"":
        p = p[1:-1]
    if not os.path.exists(p) and os.name != "nt" and "\\" in p:
        unescaped = re.sub(r"\\(.)", r"\1", p)
        if os.path.exists(unescaped):
            p = unescaped
    return p


def split_pasted(line):
    """The paths in a line pasted by dragging files into a terminal: quoted
    or backslash-escaped (macOS), quoted (Windows), several at once."""
    import shlex
    line = line.strip()
    if not line:
        return []
    if os.path.exists(clean_path(line)):
        return [clean_path(line)]
    try:
        parts = shlex.split(line, posix=os.name != "nt")
    except ValueError:
        return [clean_path(line)]
    return [clean_path(p) for p in parts]


def ask_for_game():
    print("Drag your visual novel (its folder, .zip, .apk or .app) into this window, "
          "then press Enter:")
    try:
        return split_pasted(input("> "))
    except EOFError:
        return []


def prepare_video_3d():
    """--video-3d: fetch the depth model the first time, and say what else
    is missing."""
    from . import stereo
    if not stereo.find_model():
        try:
            stereo.download_model(say=lambda m: print("   " + m, flush=True))
        except OSError as e:
            print(f"   {e}; movies stay 2D")
            return
    if not stereo.runtime_python():
        print("   3D movies need onnxruntime: python3 -m pip install onnxruntime "
              "(or into a .venv in the repository); movies stay 2D")


def main(argv=None):
    from . import flow
    ap = argparse.ArgumentParser(prog="vn3ds-port", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", help="game folder, build, .apk, .zip or .rpa")
    ap.add_argument("-o", "--output", default=None,
                    help=f"output folder (default: {default_output()})")
    ap.add_argument("--sd", help="SD card (or emulator sdmc) root to install to")
    ap.add_argument("--3ds", dest="console", metavar="IP",
                    help="send over Wi-Fi to the 3DS at IP (vn3ds's receive screen, or the "
                         "Homebrew Launcher's netloader, which first gets vn3ds)")
    ap.add_argument("--install", action="store_true",
                    help="install/update vn3ds itself (the default whenever a game is "
                         "delivered; on its own, sends just vn3ds)")
    ap.add_argument("--no-engine", action="store_true",
                    help="deliver only the game, not vn3ds.3dsx")
    ap.add_argument("--ftp", metavar="IP[:PORT]", help="upload with the ftpd homebrew app instead")
    ap.add_argument("--work", help="scratch folder for unpacking (default: a temp folder)")
    ap.add_argument("--keep-work", action="store_true", help="don't delete the scratch folder")
    ap.add_argument("--id", help="folder name on the SD card")
    ap.add_argument("--title", help="override the game title")
    ap.add_argument("--rgb565", action="store_true",
                    help="16-bit textures for opaque images: about 60%% smaller, slight banding")
    ap.add_argument("--jpeg", type=int, metavar="Q",
                    help="JPEG quality for opaque images (e.g. 80; 0 = off; default: 80 for "
                         "Wi-Fi, off for the SD card)")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--no-video", action="store_true", help="skip Movie() animations")
    ap.add_argument("--video-codec", choices=("h264", "cvid"),
                    help="movie format (default h264: smooth on a New 3DS, a still elsewhere)")
    ap.add_argument("--video-kbps", type=int,
                    help="H.264 bitrate (default: 900 for the SD card, 100 for Wi-Fi)")
    ap.add_argument("--video-fps", type=int,
                    help="highest movie frame rate (default: 30 for the SD card, 20 for Wi-Fi)")
    ap.add_argument("--video-3d", action=argparse.BooleanOptionalAction, default=None,
                    help="stereoscopic movies from estimated depth (default: on when the "
                         "depth model is installed; --video-3d downloads it once, 99 MB)")
    ap.add_argument("--jpeg-encoder", choices=("pillow", "ffmpeg"),
                    help="JPEG encoder (default: ffmpeg for Wi-Fi, pillow otherwise)")
    ap.add_argument("--jpeg-qscale", type=float, metavar="QS",
                    help="ffmpeg JPEG quantiser scale, lower is better (default 5.5 for Wi-Fi)")
    ap.add_argument("--cg-patches", action=argparse.BooleanOptionalAction, default=None,
                    help="store CG variants as patches over an earlier picture "
                         "(default: on for Wi-Fi)")
    ap.add_argument("--jpeg-posters", action=argparse.BooleanOptionalAction, default=None,
                    help="JPEG movie poster frames (default: on for Wi-Fi)")
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("-j", "--jobs", type=int, default=0)
    ap.add_argument("--quality", choices=("auto", "wifi", "sd"), default="auto",
                    help="wifi: compact files for sending over Wi-Fi; sd: best quality for "
                         "copying to the SD card (default: from where the game is going)")
    ap.add_argument("--no-detect", action="store_true",
                    help="don't look for an SD card or a 3DS on the network: just build")
    args = ap.parse_args(argv)
    inputs = [clean_path(i) for i in args.inputs]
    if not inputs and not args.install and sys.stdin.isatty():
        inputs = ask_for_game()
    if not inputs and not args.install:
        ap.error("give a game to port, or --install to send just vn3ds")
    missing = [i for i in inputs if not os.path.exists(i)]
    if missing:
        ap.error(f"{missing[0]} does not exist")
    opts = flow.Options(
        inputs=inputs, output=args.output or default_output(), quality=args.quality,
        sd=args.sd, console=args.console, ftp=args.ftp, detect=not args.no_detect,
        with_engine=not args.no_engine or not inputs, work=args.work, keep_work=args.keep_work,
        id=args.id, title=args.title, rgb565=args.rgb565, jpeg=args.jpeg,
        no_audio=args.no_audio, no_video=args.no_video, video_codec=args.video_codec,
        video_kbps=args.video_kbps, fit=args.fit, jobs=args.jobs)
    # not in flow.Options: the app never sets these
    opts.video_fps = args.video_fps
    opts.jpeg_encoder = args.jpeg_encoder
    opts.jpeg_qscale = args.jpeg_qscale
    opts.cg_patches = args.cg_patches
    opts.jpeg_posters = args.jpeg_posters
    opts.video_3d = args.video_3d
    if args.video_3d and inputs:
        prepare_video_3d()
    ui = flow.ConsoleUI()
    try:
        r = flow.run(opts, ui)
    except KeyboardInterrupt:
        ui._end_live()
        print("\nStopped. Run the same command again to carry on: only what's missing is sent.")
        sys.exit(130)
    if r["target"] == "sd":
        print("Done. Eject the SD card, put it back in the 3DS and start vn3ds from the "
              "Homebrew Launcher.")
    elif r["target"] in ("wifi", "ftp"):
        print("Done. The game is in vn3ds's list on the 3DS." if r["out_dir"] else "Done.")
    elif r["out_dir"]:
        print(f"Done. Full report: {os.path.join(r['out_dir'], 'port-report.txt')}")


if __name__ == "__main__":
    main()
