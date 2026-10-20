"""vn3ds-port: port a Ren'Py game to the Nintendo 3DS in one command.

    tools/vn3ds-port GAME [MORE INPUTS...] [--sd /Volumes/3DS]

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
compatibility report. With --sd it is copied onto the SD card together with
vn3ds.3dsx.
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
REPO = os.path.dirname(os.path.dirname(HERE))
UNRPYC = os.path.join(REPO, "tools", "third_party", "unrpyc", "unrpyc.py")
ENGINE_3DSX = os.path.join(REPO, "engine", "vn3ds.3dsx")
GAME_EXTS = (".rpy", ".rpyc", ".rpa")


def say(msg):
    print(f"[vn3ds-port] {msg}", flush=True)


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


def unpack_zip(path, work):
    """Unpack a downloaded .zip as far as needed: game files and nested
    archives. Returns the folder holding them."""
    dest = os.path.join(work, "unzipped", os.path.splitext(os.path.basename(path))[0])
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(path) as z:
        wanted = [i for i in z.infolist() if not i.is_dir() and (
            i.filename.lower().endswith(GAME_EXTS + (".apk", ".zip")) or "/game/" in "/" + i.filename)]
        total = sum(i.file_size for i in wanted)
        free = shutil.disk_usage(work).free
        if total > free * 0.9:
            sys.exit(f"vn3ds-port: unpacking {path} needs {total >> 20} MiB but only "
                     f"{free >> 20} MiB are free in {work}; pass --work on a bigger disk")
        say(f"unpacking {len(wanted)} files ({total >> 20} MiB) from {os.path.basename(path)}")
        for i in wanted:
            z.extract(i, dest)
    return dest


def collect(inputs, work):
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
                sys.exit(f"vn3ds-port: no Ren'Py game files in {item}")
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
            queue.append(unpack_zip(item, work))
        elif low.endswith(".rpa"):
            overlays.append(os.path.dirname(item))
        else:
            sys.exit(f"vn3ds-port: don't know what to do with {item}")
    if primary is None:
        sys.exit("vn3ds-port: no game found in the inputs")
    # An apk with its art shipped beside it: the folder is an overlay.
    return primary, [o for o in dict.fromkeys(overlays) if o != primary]


def decompile_if_needed(primary, overlays, work):
    fs = AssetFS(primary, lambda *a: None, overlay_dirs=overlays)
    keys = [k for k in fs.keys() if not k.startswith(("renpy/", "tl/"))]
    if any(k.endswith(".rpy") for k in keys):
        return None
    rpyc = [k for k in keys if k.endswith(".rpyc")]
    if not rpyc:
        sys.exit("vn3ds-port: no scripts (.rpy or .rpyc) in the game")
    out = os.path.join(work, "scripts")
    os.makedirs(out, exist_ok=True)
    for k in rpyc:
        dest = os.path.join(out, fs.display(k))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(fs.read(k))
    say(f"only compiled scripts found; decompiling {len(rpyc)} .rpyc files with unrpyc")
    r = subprocess.run([sys.executable, UNRPYC, "-c", out], capture_output=True, text=True)
    made = sum(1 for _, _, fs_ in os.walk(out) for f in fs_ if f.endswith(".rpy"))
    if made == 0:
        sys.exit("vn3ds-port: unrpyc could not decompile the scripts:\n" + r.stdout[-2000:] + r.stderr[-2000:])
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
    text = "\n".join(lines)
    with open(path, "w") as f:
        f.write(text + "\n\nAll warnings:\n")
        for (where, msg), n in summary["warnings"].items():
            f.write(f"{where + ': ' if where else ''}{msg}{f' (x{n})' if n > 1 else ''}\n")
    return text


def install(out_dir, game_id, sd):
    dest = os.path.join(sd, "3ds", "vn3ds", "games", game_id)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    say(f"copying to {dest}")
    shutil.copytree(out_dir, dest)
    if os.path.exists(ENGINE_3DSX):
        shutil.copy2(ENGINE_3DSX, os.path.join(sd, "3ds", "vn3ds.3dsx"))
    else:
        say("engine/vn3ds.3dsx isn't built yet (run make in engine/); copy it to sdmc:/3ds/ yourself")


def deliver(args, game_dirs):
    """Wireless delivery (--3ds / --ftp), optionally with the engine."""
    from . import send
    engine = ENGINE_3DSX if args.install else None
    files = send.plan(game_dirs, engine)
    if not files or not (args.console or args.ftp):
        return
    total = sum(os.path.getsize(p) for _, p in files) / 1e6
    if args.ftp:
        say(f"uploading {len(files)} files ({total:.1f} MB) over FTP to {args.ftp}")
        send.send_ftp(args.ftp, files)
        say("uploaded. Start vn3ds from the Homebrew Launcher.")
        return
    host = args.console
    if not send.wait_for_receiver(host, seconds=3):
        if args.install:
            send.install_via_3dslink(host, ENGINE_3DSX)
        else:
            say(f"waiting for vn3ds on {host}: open vn3ds and press Y (Receive over Wi-Fi)")
        if not send.wait_for_receiver(host, seconds=120):
            sys.exit(f"vn3ds-port: nothing is listening on {host}:{send.VN3DS_PORT}. Is vn3ds on "
                     "the receive screen, and is the 3DS on the same Wi-Fi?")
    say(f"sending {len(files)} files ({total:.1f} MB) to {host}")
    sent, refused = send.send_vn3ds(host, files)
    say(f"sent {sent} files" + (f", {refused} refused" if refused else "") +
        (". vn3ds updated: restart it." if engine else ". The game is in vn3ds's list."))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vn3ds-port", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", help="game folder, build, .apk, .zip or .rpa")
    ap.add_argument("-o", "--output", default="build", help="output folder (default: build)")
    ap.add_argument("--sd", help="SD card (or emulator sdmc) root to install to")
    ap.add_argument("--3ds", dest="console", metavar="IP",
                    help="send over Wi-Fi to vn3ds's receive screen (press Y in vn3ds)")
    ap.add_argument("--install", action="store_true",
                    help="also install/update vn3ds itself; with --3ds and no vn3ds running yet, "
                         "starts it through the Homebrew Launcher's netloader (3dslink)")
    ap.add_argument("--ftp", metavar="IP[:PORT]", help="upload with the ftpd homebrew app instead")
    ap.add_argument("--work", help="scratch folder for unpacking (default: a temp folder)")
    ap.add_argument("--keep-work", action="store_true", help="don't delete the scratch folder")
    ap.add_argument("--id", help="folder name on the SD card")
    ap.add_argument("--title", help="override the game title")
    ap.add_argument("--rgb565", action="store_true",
                    help="16-bit textures for opaque images: about 60%% smaller, slight banding")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--no-video", action="store_true", help="skip Movie() animations")
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("-j", "--jobs", type=int, default=0)
    args = ap.parse_args(argv)

    if not args.inputs and not args.install:
        ap.error("give a game to port, or --install to send just the engine")
    if args.install and not os.path.exists(ENGINE_3DSX):
        sys.exit("vn3ds-port: engine/vn3ds.3dsx isn't built yet (run make in engine/)")
    if not args.inputs:
        deliver(args, [])
        return
    # Already-ported games (folders with game.bin): just deliver them.
    ported = [os.path.abspath(i) for i in args.inputs
              if os.path.isfile(os.path.join(i, "game.bin"))]
    if ported and len(ported) == len(args.inputs):
        for d in ported:
            if args.sd:
                install(d, os.path.basename(d.rstrip("/")), args.sd)
        if not (args.console or args.ftp or args.sd):
            say("these are already-ported games; add --3ds IP, --ftp or --sd to deliver them")
        deliver(args, ported)
        return

    work = args.work or tempfile.mkdtemp(prefix="vn3ds-port-",
                                         dir=os.path.dirname(os.path.abspath(args.output)) or ".")
    os.makedirs(work, exist_ok=True)
    try:
        primary, overlays = collect(args.inputs, work)
        say(f"game: {primary}" + (f" (+ {len(overlays)} more)" if overlays else ""))
        scripts = decompile_if_needed(primary, overlays, work)
        vargs = [primary, "-o", args.output, "-q"]
        for o in ([scripts] if scripts else []) + overlays:
            vargs += ["--scripts", o]
        for flag, val in (("--id", args.id), ("--title", args.title), ("-j", args.jobs or None)):
            if val:
                vargs += [flag, str(val)]
        for flag in ("rgb565", "no_audio", "no_video", "fit"):
            if getattr(args, flag):
                vargs.append("--" + flag.replace("_", "-"))
        say("converting (images are the slow part)")
        summary = vnpack.main(vargs)
        text = report(summary, os.path.join(summary["out_dir"], "port-report.txt"))
        print("\n" + text)
        if args.sd:
            install(summary["out_dir"], summary["id"], args.sd)
        deliver(args, [summary["out_dir"]])
        say(f"done. Full report: {os.path.join(summary['out_dir'], 'port-report.txt')}")
    finally:
        if not args.keep_work and not args.work:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
