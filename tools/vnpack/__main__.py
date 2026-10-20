"""vnpack: convert a Ren'Py project into a vn3ds game folder.

    python3 -m vnpack path/to/renpy/project -o build

Copy the resulting build/<id>/ folder to sdmc:/3ds/vn3ds/games/ on the SD card.
"""

import argparse
import fnmatch
import hashlib
import multiprocessing
import time
import json
import math
import os
import re
import sys
from collections import OrderedDict

import numpy as np
from PIL import Image

from . import rpy
from .assets import (AUDIO_EXTS, IMAGE_EXTS, AssetFS, ImageBuilder,
                     convert_audio, encode_ctex, encode_cvh, encode_cvid, resize_rgba, video_frames)
from .compiler import CompileError, Compiler, write_game

DEFAULT_DEPTH_BY_TAG = {"cg": 0.45, "event": 0.45, "ev": 0.45}


class Warnings:
    def __init__(self, quiet):
        self.items = OrderedDict()
        self.quiet = quiet

    def __call__(self, line, msg):
        where = f"{line.filename}:{line.lineno}" if line is not None else ""
        key = (where, msg)
        self.items[key] = self.items.get(key, 0) + 1

    def report(self, limit=60):
        if not self.items or self.quiet:
            return
        print(f"\n{len(self.items)} warning(s):", file=sys.stderr)
        shown = 0
        for (where, msg), count in self.items.items():
            if shown >= limit:
                print(f"  ... {len(self.items) - shown} more (use --all-warnings)",
                      file=sys.stderr)
                break
            print(f"  {where + ': ' if where else ''}{msg}" +
                  (f" (x{count})" if count > 1 else ""), file=sys.stderr)
            shown += 1


_W = {}


def _image_job(name):
    """Render and encode one image (runs in a worker process)."""
    b = _W["builder"]
    warnings = []
    b.warn = lambda line, msg: warnings.append(
        (f"{line.filename}:{line.lineno}: " if line is not None else "") + msg)
    try:
        src = b.source(_W["defs"][name])
        if src is None:
            return name, None, warnings
        scale = _W["scale"]
        if src[0] == "solid":
            _, rgba, w, h = src
            w = (w or _W["gw"]) * scale
            h = (h or _W["gh"]) * scale
            full = w >= _W["vw"] * 0.95 and h >= _W["vh"] * 0.95
            return name, ("solid", rgba, w, h, full), warnings
        if src[0] == "movie":
            if not _W.get("video", True):
                return name, None, warnings
            _, key, loop = src
            gw, gh = _W["gw"], _W["gh"]
            lw, lh = gw * scale, gh * scale
            w, h = int(round(lw)), int(round(lh))
            if w > 1024 or h > 1024:
                f = min(1024 / w, 1024 / h)
                w, h = int(w * f), int(h * f)
            if _W.get("video_codec", "h264") == "h264":
                kbps = _W["video_kbps"]
                data, poster, _ = encode_cvh(
                    b.fs.read(key), key, lw, lh, loop, kbps=kbps,
                    fps_cap=_W["video_fps"] or 30, max_seconds=_W["video_seconds"],
                    profile=_W["video_profile"], poster_scale=1.0 if kbps > 400 else 0.5,
                    poster_jpeg=_W.get("jpeg", 0) if _W.get("jpeg_posters") else 0,
                    jpeg_encoder=_W.get("jpeg_encoder", "pillow"),
                    jpeg_qscale=_W.get("jpeg_qscale", 5.0))
                return name, ("cvh", data, lw, lh, True, poster), warnings
            fps = _W["video_fps"] or 12
            frames = video_frames(b.fs.read(key), key, w, h, fps, _W["video_seconds"] or 12)
            if len(frames) == 0:
                warnings.append(f"movie '{key}' has no frames")
                return name, None, warnings
            data = encode_cvid(frames, lw, lh, fps, loop)
            return name, ("video", data, lw, lh, True), warnings
        img = b.render(src)
        if img is None:
            return name, None, warnings
        lw, lh = img.width * scale, img.height * scale
        w, h = max(1, int(round(lw))), max(1, int(round(lh)))
        small = resize_rgba(img, w, h)
        data, opaque = encode_ctex(small, lw, lh, allow_565=_W["rgb565"],
                                   jpeg_quality=_W.get("jpeg", 0),
                                   jpeg_encoder=_W.get("jpeg_encoder", "pillow"),
                                   jpeg_qscale=_W.get("jpeg_qscale", 5.0),
                                   jpeg_rgb8=_W.get("jpeg_rgb8", False))
        full = img.width >= _W["gw"] * 0.95 and img.height >= _W["gh"] * 0.95
        if _W.get("cg_patches") and opaque and full and _W.get("jpeg", 0) > 0:
            # the picture as stored, for comparing with its neighbours (--cg-patches)
            pixels = np.asarray(small.convert("RGB"), dtype=np.uint8)
            return name, ("tex", data, lw, lh, full, pixels), warnings
        return name, ("tex", data, lw, lh, full), warnings
    except (OSError, ValueError, SyntaxError, MemoryError) as e:
        warnings.append(f"image '{name}': {e}")
        return name, None, warnings


ANIM_KINDS = {"sway": 1, "pulse": 2, "breathe": 3, "fall": 4, "rise": 5, "stars": 6}


def layer_anim(spec, scale):
    """(kind, a, b, period) for a layer's motion; amplitudes become 3DS px.
    sway: a = x amplitude, b = y amplitude (virtual px)
    pulse: a = lowest alpha (0..1)
    breathe: a = extra scale (e.g. 0.01)
    fall / rise: a = distance per loop (virtual px), looped seamlessly
    stars: a = how many, b = largest size (virtual px); the engine scatters
           and twinkles them procedurally, differently every time the
           image is shown (the layer's own picture is not drawn)"""
    if not spec:
        return (0, 0.0, 0.0, 1.0)
    kind = ANIM_KINDS.get(spec.get("type"), 0)
    a = float(spec.get("x", spec.get("a", 0.0)))
    b = float(spec.get("y", spec.get("b", 0.0)))
    if kind in (1, 4, 5):
        a *= scale
        b *= scale
    elif kind == 6:
        b *= scale
    return (kind, a, b, max(0.05, float(spec.get("period", 4.0))))


# --cg-patches: a picture that differs from a recently stored one only in a
# small region (a face, a hand: the usual CG variant) is stored as that
# region alone, drawn over the earlier picture's texture. The engine puts the
# two together into one texture when it loads them, so the result is drawn
# exactly like an ordinary image.
PATCH_BLOCK = 16       # JPEG 4:2:0 MCU size: patch edges fall on block boundaries
PATCH_THRESHOLD = 8    # a block changed when a channel differs by more than this
PATCH_SPILL = 3        # a neighbouring row/column of blocks that differs by more
                       # than this (the soft edge of the change) joins the patch,
                       # so the patch edge falls where the pictures agree
PATCH_KEYFRAMES = 4    # compare with this many of the last pictures stored whole
PATCH_MAX_AREA = 0.5   # at most this share of the picture becomes a patch
PATCH_MAX_BYTES = 0.8  # and the patch must be this much smaller than the whole
ANIM_PATCH = 7         # layer record kind the engine composites at load time


def natural_key(s):
    """Sort key putting "cg 9" before "cg 10"."""
    return [int(t) if i % 2 else t for i, t in enumerate(re.split(r"(\d+)", s))]


def plan_patch(pixels, keyframes):
    """Compare a picture with the keyframes [(res, pixels), ...] (newest
    last). Returns None or (share of picture, res, (x0, y0, x1, y1)); the box
    is None when nothing changed by more than the threshold."""
    h, w = pixels.shape[:2]
    bh, bw = -(-h // PATCH_BLOCK), -(-w // PATCH_BLOCK)
    a = pixels.astype(np.int16)
    best = None
    for res, kp in reversed(keyframes):
        if kp.shape != pixels.shape:
            continue
        d = np.zeros((bh * PATCH_BLOCK, bw * PATCH_BLOCK), np.int16)
        d[:h, :w] = np.abs(a - kp).max(-1)
        diff = d.reshape(bh, PATCH_BLOCK, bw, PATCH_BLOCK).max((1, 3))
        blocks = diff > PATCH_THRESHOLD
        if not blocks.any():
            return (0.0, res, None)
        ys, xs = np.nonzero(blocks)
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
        share = (y1 - y0) * (x1 - x0) / float(bh * bw)
        if best is None or share < best[0]:
            best = (share, res, diff, (x0, y0, x1, y1))
    if best is None or best[3] is None:
        return best
    share, res, diff, (x0, y0, x1, y1) = best
    bh, bw = diff.shape
    nx0 = x0 - 1 if x0 > 0 and diff[y0:y1, x0 - 1].max() > PATCH_SPILL else x0
    nx1 = x1 + 1 if x1 < bw and diff[y0:y1, x1].max() > PATCH_SPILL else x1
    ny0 = y0 - 1 if y0 > 0 and diff[y0 - 1, x0:x1].max() > PATCH_SPILL else y0
    ny1 = y1 + 1 if y1 < bh and diff[y1, x0:x1].max() > PATCH_SPILL else y1
    return (share, res, (nx0 * PATCH_BLOCK, ny0 * PATCH_BLOCK,
                         min(w, nx1 * PATCH_BLOCK), min(h, ny1 * PATCH_BLOCK)))


def find_game_dir(path):
    if os.path.isfile(path):
        return path  # an Android .apk or a .zip of the game
    if os.path.isdir(os.path.join(path, "game")):
        return os.path.join(path, "game")
    return path


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:32] or "game"


def layout(game_w, game_h, fit):
    """Scale and place the virtual screen on the 400x240 top screen."""
    s_fit = min(400 / game_w, 240 / game_h)
    s_fill = max(400 / game_w, 240 / game_h)
    # Fill (crop the edges) when that loses less than ~8% of the picture.
    crop = 1 - s_fit / s_fill
    s = s_fit if (fit or crop > 0.08) else s_fill
    vw, vh = game_w * s, game_h * s
    return s, (400 - vw) / 2, (240 - vh) / 2, vw, vh


def auto_images(fs):
    """Ren'Py defines an image for every file under game/images/."""
    out = {}
    for key in fs.keys():
        if not key.startswith("images/") or not key.endswith(IMAGE_EXTS):
            continue
        base = os.path.splitext(os.path.basename(key))[0]
        name = " ".join(base.lower().split())
        if name:
            out.setdefault(name, key)
    return out


def resolve_auto_audio(fs, name):
    for d in ("audio/", "music/", "sound/", "sounds/", "sfx/", "bgm/", ""):
        for ext in AUDIO_EXTS:
            key = fs.find(d + name + ext, dirs=("",))
            if key:
                return key
    # Ren'Py names every file anywhere under game/audio/ by its bare name
    # (audio/sfx/08/door.ogg is `door`), so look in subfolders too.
    index = getattr(fs, "_audio_by_name", None)
    if index is None:
        index = {}
        for key in sorted(fs.keys()):
            if key.startswith("audio/") and key.endswith(tuple(AUDIO_EXTS)):
                index.setdefault(key.rsplit("/", 1)[-1].rsplit(".", 1)[0], key)
        fs._audio_by_name = index
    return index.get(name.lower())


def _no_progress(step, **info):
    pass


def main(argv=None, progress=None):
    """Packs a game; returns a summary dict. `progress(step, **info)` is
    called as the work goes along: step "scripts", "audio", "images",
    "video" or "pack", with state="active"/"done" or done=n, total=N."""
    progress = progress or _no_progress
    ap = argparse.ArgumentParser(prog="vnpack", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="Ren'Py project folder, its game/ folder, or an Android .apk")
    ap.add_argument("--scripts", action="append", default=[], metavar="DIR",
                    help="extra folder of .rpy files (e.g. decompiled with unrpyc); "
                         "searched before the project")
    ap.add_argument("--dump-rpyc", metavar="DIR",
                    help="write the game's compiled .rpyc scripts to DIR and exit")
    ap.add_argument("-o", "--output", default="build", help="output folder (default: build)")
    ap.add_argument("--id", help="folder name on the SD card (default: from the title)")
    ap.add_argument("--title", help="override the game title")
    ap.add_argument("--fit", action="store_true",
                    help="always letterbox instead of cropping the edges to fill the screen")
    ap.add_argument("--config", help="JSON file with 3D depth settings (see README)")
    ap.add_argument("--rgb565", action="store_true",
                    help="store opaque images as RGB565 (half the memory, some banding)")
    ap.add_argument("--jpeg", type=int, default=0, metavar="Q",
                    help="store opaque images as JPEG at quality Q (1-100, e.g. 80: about a "
                         "fifth of the size, decoded to RGB565 on load); 0 = off")
    ap.add_argument("--jpeg-encoder", choices=("pillow", "ffmpeg"), default="pillow",
                    help="JPEG encoder for --jpeg: pillow (libjpeg, default) or ffmpeg "
                         "(trellis quantisation, about a quarter smaller; quality from "
                         "--jpeg-qscale)")
    ap.add_argument("--jpeg-qscale", type=float, default=5.0, metavar="QS",
                    help="ffmpeg JPEG quantiser scale (2-31, lower is better; default 5)")
    ap.add_argument("--jpeg-rgb8", action="store_true",
                    help="decode JPEG pictures into RGB8 textures instead of RGB565 (no "
                         "banding in gradients; textures take half as much memory again)")
    ap.add_argument("--jpeg-posters", action="store_true",
                    help="store movie poster frames as JPEG too (with --jpeg)")
    ap.add_argument("--cg-patches", action="store_true",
                    help="store pictures that differ from a recent one only in a region "
                         "as just that region (with --jpeg)")
    ap.add_argument("--no-packs", dest="packs", action="store_false",
                    help="leave the pictures and sounds as loose files in img/ and snd/ "
                         "instead of a few pack files in pk/ (slower to open on a 3DS)")
    ap.add_argument("--pack-mb", type=float, default=8.0, metavar="MB",
                    help="typical pack file size (default 8; packs run from a quarter to "
                         "twice this; a Wi-Fi update resends each pack that changed)")
    ap.add_argument("--no-music-grids", dest="music_grids", action="store_false",
                    help="don't measure the tempo of music tracks vn3ds.json has no grid for "
                         "(without a grid the engine crossfades music changes)")
    ap.add_argument("--no-audio", action="store_true", help="skip audio")
    ap.add_argument("--audio-profile", choices=("sd", "wifi"), default="sd",
                    help="sd: keep Ogg files as they are, the rest as Opus at a high bitrate; "
                         "wifi: re-encode everything small")
    ap.add_argument("--audio-masters", metavar="DIR",
                    help="lossless masters of the game's audio (DIR/<path under audio/>.flac "
                         "or .wav): encoded instead of the shipped files; also vn3ds.json "
                         "\"audio_masters\" (relative to the game folder)")
    ap.add_argument("--no-video", action="store_true", help="skip Movie() animations")
    ap.add_argument("--video-codec", choices=("h264", "cvid"), default="h264",
                    help="h264: hardware-decoded on a New 3DS, the first frame elsewhere "
                         "(default); cvid: the older tile format, any 3DS, low frame rate")
    ap.add_argument("--video-kbps", type=int, default=900,
                    help="H.264 bitrate (default 900 for the SD card; about 250 for Wi-Fi)")
    ap.add_argument("--video-profile", choices=("main", "baseline"), default="main",
                    help="H.264 profile (default main)")
    ap.add_argument("--video-fps", type=int, default=None,
                    help="frame rate for converted movies: the cap for h264 (default 30, "
                         "clips keep their own rate below it), the rate for cvid (default 12)")
    ap.add_argument("--video-seconds", type=float, default=None,
                    help="longest movie kept, in seconds (default: all of it for h264, "
                         "12 for cvid)")
    ap.add_argument("-j", "--jobs", type=int, default=0,
                    help="processes for image conversion (default: up to 4)")
    ap.add_argument("--only-images", action="append", default=[], metavar="GLOB",
                    help="pack only the images whose names match (fnmatch, repeatable): "
                         "a quick test build with the whole script")
    ap.add_argument("--only-audio", action="append", default=[], metavar="GLOB",
                    help="pack only the audio files whose paths match (fnmatch, repeatable)")
    ap.add_argument("--check", action="store_true",
                    help="only parse and compile the scripts and report problems")
    ap.add_argument("--all-warnings", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args(argv)
    if not 0 <= args.jpeg <= 100:
        ap.error("--jpeg takes a quality from 1 to 100 (0 = off)")

    warn = Warnings(args.quiet)
    game_dir = find_game_dir(args.project)
    if not os.path.exists(game_dir):
        ap.error(f"{args.project} does not exist")

    cfg = {}
    cfg_path = args.config or (os.path.join(game_dir, "vn3ds.json")
                               if os.path.isdir(game_dir) else "")
    if os.path.isfile(cfg_path) and not cfg_path.endswith((".apk", ".zip")):
        with open(cfg_path) as f:
            cfg = json.load(f)

    fs = AssetFS(game_dir, warn, overlay_dirs=args.scripts)

    if args.dump_rpyc:
        n = 0
        for key in fs.keys():
            if key.endswith(".rpyc") and not key.startswith(("renpy/", "tl/")):
                out = os.path.join(args.dump_rpyc, fs.display(key))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "wb") as f:
                    f.write(fs.read(key))
                n += 1
        print(f"wrote {n} .rpyc files to {args.dump_rpyc}")
        return

    # -- parse -------------------------------------------------------------
    progress("scripts", state="active")
    scripts = sorted(k for k in fs.keys()
                     if k.endswith(".rpy") and not k.startswith(("tl/", "renpy/")))
    if not scripts:
        if any(k.endswith(".rpyc") for k in fs.keys()):
            sys.exit("vnpack: only compiled .rpyc scripts were found. Extract them with "
                     "--dump-rpyc DIR, decompile them (for example with unrpyc), then "
                     "pass the folder with --scripts DIR.")
        sys.exit(f"vnpack: no .rpy files in {game_dir}")
    files = []
    for key in scripts:
        name = fs.display(key)
        src = fs.read(key).decode("utf-8", "replace")
        try:
            files.append(rpy.parse_file(src, name))
        except rpy.ParseError as e:
            sys.exit(f"vnpack: parse error: {e}")

    comp = Compiler(warn)
    comp.collect(files)
    # Custom screens rebuilt as native minigames (ported.py): the adapter is
    # chosen by the game's id, worked out as below.
    from .ported import Ported, load_spec
    _base = os.path.abspath(args.project)
    if os.path.basename(_base) == "game":
        _base = os.path.dirname(_base)
    _title = args.title or cfg.get("title") or comp.meta["title"] or \
        os.path.splitext(os.path.basename(_base))[0]
    ported_spec = load_spec(args.id or cfg.get("id") or slug(_title), cfg)
    if ported_spec:
        comp.ported = Ported(ported_spec, files, warn)
    try:
        comp.compile(files)
    except (CompileError, rpy.ParseError) as e:
        warn.report()
        sys.exit(f"vnpack: {e}")

    progress("scripts", state="done", labels=len(comp.defined_labels), files=len(scripts))
    if comp.ported is not None:
        comp.ported.prepare_assets(fs)   # crop boxes and sizes of the minigames' art
    if args.check:
        warn.report(limit=10**9 if args.all_warnings else 60)
        n_specs = len(comp.used_specs)
        print(f"\n{len(comp.defined_labels)} labels, {len(comp.code.b) // 1024} KiB of bytecode, "
              f"{n_specs} distinct images shown, {len(comp.resources)} audio files referenced")
        return

    # -- layout --------------------------------------------------------------
    gw = comp.meta["width"] or (1280 if fs.find("gui.rpy") else 800)
    gh = comp.meta["height"] or (720 if fs.find("gui.rpy") else 600)
    scale, vx, vy, vw, vh = layout(gw, gh, args.fit or cfg.get("fit", False))

    fallback = os.path.abspath(args.project)
    if os.path.basename(fallback) == "game":   # name it after the project, not "game"
        fallback = os.path.dirname(fallback)
    title = args.title or cfg.get("title") or comp.meta["title"] or \
        os.path.splitext(os.path.basename(fallback))[0]
    game_id = args.id or cfg.get("id") or slug(title)
    out_dir = os.path.join(args.output, game_id)
    for sub in ("img", "snd", "pk"):
        d = os.path.join(out_dir, sub)
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            if fn.endswith((".ctex", ".ogg", ".cvid", ".cvh", ".pak", ".tmp")):
                os.remove(os.path.join(d, fn))

    depth_map = dict(DEFAULT_DEPTH_BY_TAG)
    depth_map.update(cfg.get("depth", {}))

    # -- images ------------------------------------------------------------
    defs = dict(comp.image_defs)
    # Images Ren'Py itself defines.
    defs.setdefault("black", ("expr", '"#000"', None))
    defs.setdefault("white", ("expr", '"#fff"', None))
    autos = auto_images(fs)
    for name, key in autos.items():
        defs.setdefault(name, ("file", key))

    used_tags = {spec.split()[0] for spec in comp.used_specs}
    used_tags |= {c.image for c in comp.chars if c.image}

    by_tag = {}
    for name in defs:
        by_tag.setdefault(name.split()[0], []).append(name)

    # Specs that match nothing: try Ren'Py's other automatic-image separators.
    for spec, line in comp.used_specs.items():
        words = spec.split()
        tag, attrs = words[0], {a for a in words[1:] if not a.startswith("-")}
        cands = [n for n in by_tag.get(tag, []) if attrs <= set(n.split()[1:])]
        if cands:
            continue
        alias = None
        for sep in ("_", "-", "/"):
            joined = sep.join(words)
            for name, key in autos.items():
                if name == joined or os.path.splitext(key)[0].endswith("/" + joined):
                    alias = key
                    break
            if alias:
                break
        if alias:
            defs[spec] = ("file", alias)
            by_tag.setdefault(tag, []).append(spec)
        elif tag in by_tag:
            warn(line, f"no image '{tag}' has attributes {' '.join(sorted(attrs))}")
        else:
            warn(line, f"image '{spec}' is not defined")

    # Packed files are named by their contents, so a rebuild keeps the name of
    # everything that didn't change and Wi-Fi updates only send what did.
    def content_name(sub, data, ext):
        return f"{sub}/{hashlib.sha1(data).hexdigest()[:16]}.{ext}"

    def rename_by_content(rel):
        """Moves a file written under a temporary name to its content name."""
        src = os.path.join(out_dir, rel)
        with open(src, "rb") as f:
            final = content_name(rel.split("/", 1)[0], f.read(), rel.rsplit(".", 1)[1])
        os.replace(src, os.path.join(out_dir, final))
        return final

    builder = ImageBuilder(fs, comp, gw, gh, warn)
    builder.extra_defs = defs
    resources = []
    images = []
    tex_cache = {}
    total_bytes = 0

    def add_texture(img, logical_w, logical_h):
        nonlocal total_bytes
        key = (id(img), logical_w, logical_h)
        if key in tex_cache:
            return tex_cache[key]
        w = max(1, int(round(logical_w)))
        h = max(1, int(round(logical_h)))
        data, opaque = encode_ctex(resize_rgba(img, w, h), logical_w, logical_h,
                                   allow_565=args.rgb565, jpeg_quality=args.jpeg,
                                   jpeg_encoder=args.jpeg_encoder, jpeg_qscale=args.jpeg_qscale,
                                   jpeg_rgb8=args.jpeg_rgb8)
        idx = len(resources)
        rel = content_name("img", data, "ctex")
        with open(os.path.join(out_dir, rel), "wb") as f:
            f.write(data)
        total_bytes += len(data)
        resources.append(rel)
        tex_cache[key] = (idx, opaque)
        return tex_cache[key]

    # -- audio -------------------------------------------------------------
    # Minigames find their music and sound effects by name: everything in
    # game/audio/minigame/ is packed and listed in the AUDN table.
    if comp.minigames:
        for key in sorted(fs.keys()):
            if key.startswith("audio/minigame/") and key.rsplit(".", 1)[-1] in (
                    "ogg", "opus", "mp3", "wav", "flac"):
                comp.named_audio[key[len("audio/"):].rsplit(".", 1)[0]] = comp.audio_index(key)

    # Audio comes first in the resource table: PLAY operands are the
    # compiler's resource indices.
    audio_count = 0
    audio_jobs = []
    for kind, path in comp.resources:
        rel = f"snd/tmp-{len(resources):04d}.ogg"
        resources.append(rel)
        if args.no_audio:
            continue
        if path.startswith("?auto:"):
            key = resolve_auto_audio(fs, path[6:])
        else:
            key = fs.find(path, dirs=("", "audio/"))
        if key is None:
            warn(None, f"audio file '{path}' not found")
            continue
        if args.only_audio and not any(fnmatch.fnmatch(key, g.lower()) for g in args.only_audio):
            continue
        audio_jobs.append((key, rel))
    # ffmpeg runs in its own process, so threads are enough to use every core
    from concurrent.futures import ThreadPoolExecutor

    masters_dir = args.audio_masters or (
        os.path.join(game_dir, cfg["audio_masters"]) if cfg.get("audio_masters") and
        os.path.isdir(game_dir) else None)
    if masters_dir and not os.path.isdir(masters_dir):
        masters_dir = None   # not rendered here: the shipped files are used

    def master_of(key):
        """The lossless master of game file `key`, as bytes, or None."""
        if not masters_dir:
            return None
        base = os.path.splitext(key[len("audio/"):] if key.startswith("audio/") else key)[0]
        for ext in (".flac", ".wav"):
            p = os.path.join(masters_dir, base + ext)
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    return f.read()
        return None
    masters_used = [0]

    def audio_job(job):
        key, rel = job
        master = master_of(key)
        if master is not None:
            masters_used[0] += 1
        return convert_audio(fs.read(key), fs.display(key), os.path.join(out_dir, rel), warn,
                             args.audio_profile, master=master)
    progress("audio", done=0, total=len(audio_jobs))
    with ThreadPoolExecutor(max_workers=max(2, os.cpu_count() or 2)) as ex:
        for i, ok in enumerate(ex.map(audio_job, audio_jobs)):
            audio_count += 1 if ok else 0
            progress("audio", done=i + 1, total=len(audio_jobs))
    progress("audio", state="done", done=len(audio_jobs), total=len(audio_jobs))
    if masters_used[0] and not args.quiet:
        print(f"  audio: {masters_used[0]} files encoded from lossless masters in {masters_dir}",
              file=sys.stderr)
    for i, rel in enumerate(resources):
        if os.path.exists(os.path.join(out_dir, rel)):
            resources[i] = rename_by_content(rel)

    # Music tempo grids (vn3ds.json "music": {"audio/x.ogg": {"bpm", "beats_per_bar",
    # "phrase_bars", "bars"}}): the engine changes music on a phrase boundary or
    # at the end of the loop instead of cutting. Keyed by the file the script plays.
    music_meta = []
    mcfg = {}
    for name, m in (cfg.get("music") or {}).items():
        key = fs.find(name, dirs=("", "audio/"))
        if key and isinstance(m, dict) and float(m.get("bpm", 0)) > 0:
            mcfg[key] = m
    for i, (kind, path) in enumerate(comp.resources if mcfg else ()):
        key = resolve_auto_audio(fs, path[6:]) if path.startswith("?auto:") else \
            fs.find(path, dirs=("", "audio/"))
        if key in mcfg:
            m = mcfg[key]
            music_meta.append((i, float(m["bpm"]), int(m.get("beats_per_bar", 4)),
                               int(m.get("phrase_bars", 4)), int(m.get("bars", 0))))

    # Every other track the script plays as music gets its grid measured
    # (tempo.py), so any game's music changes on the loop's end or a phrase.
    # Grids the analysis isn't sure of, or whose first beat isn't at the
    # start of the file (MUSM has no phase), are left out: those tracks
    # crossfade. --no-music-grids or vn3ds.json "music_auto": false skip it.
    music_auto = []
    if args.music_grids and cfg.get("music_auto", True) and not args.no_audio:
        from .packs import music_resources
        from .tempo import analyse_file, music_entry
        have = {m[0] for m in music_meta}
        src_of = {int(rel[8:-4]): key for key, rel in audio_jobs}   # snd/tmp-NNNN.ogg
        todo = [(i, src_of[i]) for i in sorted(music_resources(bytes(comp.code.b)))
                if i not in have and i in src_of]
        progress("music", done=0, total=len(todo))

        def measure(job):
            i, key = job
            try:
                master = master_of(key)
                return i, key, analyse_file(master if master is not None else fs.read(key))
            except (OSError, ValueError, MemoryError):
                return i, key, None
        with ThreadPoolExecutor(max_workers=max(2, min(6, os.cpu_count() or 2))) as ex:
            for n, (i, key, r) in enumerate(ex.map(measure, todo)):
                progress("music", done=n + 1, total=len(todo))
                e = music_entry(r)
                why = "no steady beat" if r and not e else "not decodable" if not r else ""
                if e and abs(r.get("offset", 0.0)) > 0.1 * 60.0 / e["bpm"]:
                    e, why = None, f"first beat {r['offset']:.2f} s into the file"
                music_auto.append((fs.display(key), r, e, why))
                if e:
                    music_meta.append((i, float(e["bpm"]), int(e["beats_per_bar"]),
                                       int(e["phrase_bars"]), int(e["bars"])))
        progress("music", state="done", done=len(todo), total=len(todo))

    # Machine voices (vn3ds.json "voices"): a syllable bank plus a pitch per
    # character, played by the engine as text appears.
    voices = None
    vcfg = cfg.get("voices")
    if vcfg and not args.no_audio:
        bank = []
        for rel_src in vcfg.get("bank", []):
            key = fs.find(rel_src, dirs=("",))
            if key is None:
                warn(None, f"voice syllable '{rel_src}' not found")
                continue
            rel = f"snd/tmp-{len(resources):04d}.ogg"
            if convert_audio(fs.read(key), fs.display(key), os.path.join(out_dir, rel), warn,
                             args.audio_profile, master=master_of(key)):
                bank.append(len(resources))
                resources.append(rename_by_content(rel))
        pitch = {}
        for var, p in vcfg.get("pitch", {}).items():
            if var in comp.char_by_name:
                pitch[comp.char_by_name[var]] = float(p)
            else:
                warn(None, f"voices: no character variable '{var}'")
        if bank:
            voices = dict(bank=bank[:32], pitch=pitch, volume=float(vcfg.get("volume", 0.3)),
                          duck=float(vcfg.get("duck", 0.85)))

    names = sorted(n for n in defs if n.split()[0] in used_tags)
    if args.only_images:
        names = [n for n in names if any(fnmatch.fnmatch(n, g) for g in args.only_images)]
    # Layered illustrations (vn3ds.json "layers"): each layer becomes its own
    # texture with its own depth; the flat image is only for Ren'Py itself.
    layer_cfg = {k: v for k, v in cfg.get("layers", {}).items() if k.split()[0] in used_tags}
    names = [n for n in names if n not in layer_cfg]
    _W.update(builder=builder, defs=defs, scale=scale, gw=gw, gh=gh, vw=vw, vh=vh,
              rgb565=args.rgb565, video=not args.no_video, video_fps=args.video_fps,
              video_seconds=args.video_seconds, video_codec=args.video_codec,
              video_kbps=args.video_kbps, video_profile=args.video_profile)
    _W["jpeg"] = args.jpeg
    _W.update(jpeg_encoder=args.jpeg_encoder, jpeg_qscale=args.jpeg_qscale, jpeg_rgb8=args.jpeg_rgb8,
              jpeg_posters=args.jpeg_posters, cg_patches=args.cg_patches)
    if args.cg_patches:
        # neighbouring variants of a CG next to each other: "cg 9", "cg 10"
        names = sorted(names, key=natural_key)
    # Each worker holds a few full-size pictures; more than 4 mostly adds swap.
    jobs = max(1, args.jobs or min(4, os.cpu_count() or 2))
    by_hash = {}
    layer_records = []
    done = 0
    t0 = time.time()

    # Movies are converted in the same pass; count them for the progress.
    movies = sum(1 for n in names if "Movie" in repr(defs[n])) if not args.no_video else 0
    movies_done = 0
    progress("images", done=0, total=len(names))
    if movies:
        progress("video", done=0, total=movies)

    def results():
        # Workers inherit the state above by forking; where there is no fork
        # (Windows) the images are converted in this process.
        if jobs == 1 or len(names) < 50 or "fork" not in multiprocessing.get_all_start_methods():
            yield from map(_image_job, names)
            return
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(jobs) as pool:
            yield from pool.imap(_image_job, names, chunksize=8)

    entries = {}       # name -> (image record, layer items or None)
    keyframes = []     # [(res, pixels)] of the last pictures stored whole
    patches = [0, 0]   # pictures stored as a patch, bytes saved

    def write_res(data, ext):
        nonlocal total_bytes
        digest = hashlib.sha1(data).digest()
        res = by_hash.get(digest)
        if res is None:
            res = len(resources)
            rel = content_name("img", data, ext)
            with open(os.path.join(out_dir, rel), "wb") as f:
                f.write(data)
            total_bytes += len(data)
            resources.append(rel)
            by_hash[digest] = res
        return res

    for name, result, warnings in results():
        for w in warnings:
            warn(None, w)
        done += 1
        progress("images", done=done, total=len(names))
        if result is not None and result[0] in ("video", "cvh"):
            movies_done += 1
            progress("video", done=movies_done, total=max(movies, movies_done))
        if not args.quiet and (done % 250 == 0 or done == len(names)):
            rate = done / max(1e-6, time.time() - t0)
            print(f"  images {done}/{len(names)}  ({rate:.0f}/s, "
                  f"{total_bytes // (1 << 20)} MiB written)", file=sys.stderr, flush=True)
        if result is None:
            continue
        tag = name.split()[0]
        depth = depth_map.get(name, depth_map.get(tag, float("nan")))
        if result[0] == "solid":
            _, rgba, w, h, full = result
            entries[name] = (dict(name=name, res=-1, color=rgba, w=w, h=h,
                                  flags=1 | (2 if full else 0), depth=depth), None)
            continue
        kind, data, lw, lh, full = result[:5]
        digest = hashlib.sha1(data).digest()
        if kind == "tex" and len(result) > 5 and digest not in by_hash:
            pixels = result[5]
            plan = plan_patch(pixels, keyframes)
            items = None
            if plan is not None and plan[0] <= PATCH_MAX_AREA:
                _, base, box = plan
                if box is None:     # the same picture to within the threshold
                    items = ()
                else:
                    x0, y0, x1, y1 = box
                    ph, pw = pixels.shape[:2]
                    sx, sy = lw / pw, lh / ph
                    pdata, _ = encode_ctex(Image.fromarray(pixels[y0:y1, x0:x1]).convert("RGBA"),
                                           (x1 - x0) * sx, (y1 - y0) * sy, allow_565=True,
                                           jpeg_quality=args.jpeg, jpeg_encoder=args.jpeg_encoder,
                                           jpeg_qscale=args.jpeg_qscale, jpeg_rgb8=args.jpeg_rgb8)
                    if len(pdata) < len(data) * PATCH_MAX_BYTES:
                        pres = write_res(pdata, "ctex")
                        patches[1] += len(data) - len(pdata)
                        ldepth = depth if not math.isnan(depth) else float(cfg.get("depth_bg", 1.0))
                        items = [(base, ldepth, 0.0, 0.0, lw, lh, (0, 0.0, 0.0, 1.0)),
                                 (pres, ldepth, x0 * sx, y0 * sy, (x1 - x0) * sx, (y1 - y0) * sy,
                                  (ANIM_PATCH, float(x0), float(y0), 1.0))]
                if items is not None:
                    patches[0] += 1
                    if not items:
                        patches[1] += len(data)
                    entries[name] = (dict(name=name, res=base, color=0xFFFFFFFF, w=lw, h=lh,
                                          flags=2 if full else 0, depth=depth), items or None)
                    continue
            keyframes = (keyframes + [(write_res(data, "ctex"), pixels.astype(np.int16))])[
                -PATCH_KEYFRAMES:]
        elif kind == "tex" and len(result) > 5:
            keyframes = (keyframes + [(by_hash[digest], result[5].astype(np.int16))])[
                -PATCH_KEYFRAMES:]
        res = by_hash.get(digest)
        if res is None:
            res = len(resources)
            rel = content_name("img", data, {"video": "cvid", "cvh": "cvh"}.get(kind, "ctex"))
            with open(os.path.join(out_dir, rel), "wb") as f:
                f.write(data)
            total_bytes += len(data)
            if kind == "cvh":   # its poster frame: same name, .ctex (the engine looks there)
                with open(os.path.join(out_dir, rel[:-4] + ".ctex"), "wb") as f:
                    f.write(result[5])
                total_bytes += len(result[5])
            resources.append(rel)
            by_hash[digest] = res
        entries[name] = (dict(name=name, res=res, color=0xFFFFFFFF, w=lw, h=lh,
                              flags=(2 if full else 0) | (4 if kind in ("video", "cvh") else 0),
                              depth=depth), None)

    # Image records in name order, whatever order they were converted in.
    for name in sorted(entries):
        record, items = entries[name]
        if items:
            layer_records.append((len(images), items))
        images.append(record)
    if patches[0] and not args.quiet:
        print(f"  --cg-patches: {patches[0]} pictures stored as a patch or reused "
              f"({patches[1] >> 20} MiB saved)", file=sys.stderr)

    progress("images", state="done", done=done, total=len(names))
    if movies or movies_done:
        progress("video", state="done", done=movies_done, total=max(movies, movies_done))
    progress("pack", state="active")
    for name in sorted(layer_cfg):
        items = []
        canvas = None
        for layer in layer_cfg[name]:
            key = fs.find(layer["file"])
            if key is None:
                warn(None, f"layer file '{layer['file']}' of '{name}' not found")
                continue
            img = builder.render(("file", key))
            if canvas is None:
                canvas = img.size
            bbox = img.getchannel("A").getbbox()
            if bbox is None:
                continue
            part = img.crop(bbox)
            lw, lh = part.width * scale, part.height * scale
            w, h = max(1, int(round(lw))), max(1, int(round(lh)))
            data, _ = encode_ctex(resize_rgba(part, w, h), lw, lh, allow_565=args.rgb565,
                                  jpeg_quality=args.jpeg, jpeg_encoder=args.jpeg_encoder,
                                  jpeg_qscale=args.jpeg_qscale, jpeg_rgb8=args.jpeg_rgb8)
            digest = hashlib.sha1(data).digest()
            res = by_hash.get(digest)
            if res is None:
                res = len(resources)
                rel = content_name("img", data, "ctex")
                with open(os.path.join(out_dir, rel), "wb") as f:
                    f.write(data)
                total_bytes += len(data)
                resources.append(rel)
                by_hash[digest] = res
            items.append((res, float(layer.get("depth", 0.0)), bbox[0] * scale, bbox[1] * scale,
                          lw, lh, layer_anim(layer.get("anim"), scale)))
        if not items:
            continue
        full = canvas[0] >= gw * 0.95 and canvas[1] >= gh * 0.95
        layer_records.append((len(images), items))
        images.append(dict(name=name, res=-1, color=0xFFFFFFFF, w=canvas[0] * scale,
                           h=canvas[1] * scale, flags=2 if full else 0, depth=float("nan")))

    title_image = -1
    key = fs.find("gui/main_menu.png") or fs.find("gui/main_menu.jpg")
    if key:
        img = builder.render(("file", key))
        res, _ = add_texture(img, img.width * scale, img.height * scale)
        title_image = len(images)
        images.append(dict(name="__title", res=res, color=0xFFFFFFFF,
                           w=img.width * scale, h=img.height * scale, flags=2,
                           depth=float("nan")))

    meta = dict(title=title, version=comp.meta["version"] or "", game_w=gw, game_h=gh,
                scale=scale, view_x=vx, view_y=vy, view_w=vw, view_h=vh,
                depth_bg=float(cfg.get("depth_bg", 1.0)),
                depth_sprite=float(cfg.get("depth_sprite", 0.0)),
                depth_ui=float(cfg.get("depth_ui", -0.35)),
                max_shift=float(cfg.get("max_shift", 6.0)),
                title_image=title_image, camera=cfg.get("camera"))
    size = write_game(os.path.join(out_dir, "game.bin"), comp, meta, images, resources,
                      layer_records, voices, music=music_meta)

    packs = None
    if args.packs:
        from .packs import make_packs
        packs = make_packs(out_dir, target=int(args.pack_mb * (1 << 20)), quiet=args.quiet)
    else:
        try:
            os.rmdir(os.path.join(out_dir, "pk"))
        except OSError:
            pass
    progress("pack", state="done", bytes=size + total_bytes)
    warn.report(limit=10**9 if args.all_warnings else 60)
    if not args.quiet:
        print(f"\n{title}: {len(comp.defined_labels)} labels, {len(images)} images "
              f"({total_bytes // 1024} KiB of textures), {audio_count} audio files, "
              f"script {size // 1024} KiB")
        print(f"virtual screen {gw}x{gh} -> {vw:.0f}x{vh:.0f} at ({vx:.1f}, {vy:.1f}), "
              f"scale {scale:.4f}")
        print(f"wrote {out_dir}/  ->  copy it to sdmc:/3ds/vn3ds/games/{game_id}/")
    return dict(title=title, id=game_id, out_dir=out_dir, warnings=warn.items,
                labels=len(comp.defined_labels), images=len(images),
                texture_bytes=total_bytes, audio=audio_count, script_bytes=size,
                packs=packs["packs"] if packs else 0,
                music_grids=[(name, (r or {}).get("confidence", 0.0), e, why)
                             for name, r, e, why in music_auto],
                audio_refs=len(comp.resources), screen=(gw, gh))


if __name__ == "__main__":
    main()
