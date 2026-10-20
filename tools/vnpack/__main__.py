"""vnpack: convert a Ren'Py project into a vn3ds game folder.

    python3 -m vnpack path/to/renpy/project -o build

Copy the resulting build/<id>/ folder to sdmc:/3ds/vn3ds/games/ on the SD card.
"""

import argparse
import hashlib
import multiprocessing
import time
import json
import math
import os
import re
import sys
from collections import OrderedDict

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
                    profile=_W["video_profile"], poster_scale=1.0 if kbps > 400 else 0.5)
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
        data, _ = encode_ctex(resize_rgba(img, w, h), lw, lh, allow_565=_W["rgb565"],
                              jpeg_quality=_W.get("jpeg", 0))
        full = img.width >= _W["gw"] * 0.95 and img.height >= _W["gh"] * 0.95
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


def main(argv=None):
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
    ap.add_argument("--no-audio", action="store_true", help="skip audio")
    ap.add_argument("--audio-profile", choices=("sd", "wifi"), default="sd",
                    help="sd: keep Ogg files as they are; wifi: re-encode everything small")
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
    try:
        comp.compile(files)
    except (CompileError, rpy.ParseError) as e:
        warn.report()
        sys.exit(f"vnpack: {e}")

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
    for sub in ("img", "snd"):
        d = os.path.join(out_dir, sub)
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            if fn.endswith((".ctex", ".ogg", ".cvid", ".cvh")):
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
                                   allow_565=args.rgb565, jpeg_quality=args.jpeg)
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
        audio_jobs.append((key, rel))
    # ffmpeg runs in its own process, so threads are enough to use every core
    from concurrent.futures import ThreadPoolExecutor

    def audio_job(job):
        key, rel = job
        return convert_audio(fs.read(key), fs.display(key), os.path.join(out_dir, rel), warn,
                             args.audio_profile)
    with ThreadPoolExecutor(max_workers=max(2, os.cpu_count() or 2)) as ex:
        audio_count = sum(1 for ok in ex.map(audio_job, audio_jobs) if ok)
    for i, rel in enumerate(resources):
        if os.path.exists(os.path.join(out_dir, rel)):
            resources[i] = rename_by_content(rel)

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
            if convert_audio(fs.read(key), fs.display(key), os.path.join(out_dir, rel), warn):
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
    # Layered illustrations (vn3ds.json "layers"): each layer becomes its own
    # texture with its own depth; the flat image is only for Ren'Py itself.
    layer_cfg = {k: v for k, v in cfg.get("layers", {}).items() if k.split()[0] in used_tags}
    names = [n for n in names if n not in layer_cfg]
    _W.update(builder=builder, defs=defs, scale=scale, gw=gw, gh=gh, vw=vw, vh=vh,
              rgb565=args.rgb565, video=not args.no_video, video_fps=args.video_fps,
              video_seconds=args.video_seconds, video_codec=args.video_codec,
              video_kbps=args.video_kbps, video_profile=args.video_profile)
    _W["jpeg"] = args.jpeg
    # Each worker holds a few full-size pictures; more than 4 mostly adds swap.
    jobs = max(1, args.jobs or min(4, os.cpu_count() or 2))
    by_hash = {}
    done = 0
    t0 = time.time()

    def results():
        if jobs == 1 or len(names) < 50:
            yield from map(_image_job, names)
            return
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(jobs) as pool:
            yield from pool.imap(_image_job, names, chunksize=8)

    for name, result, warnings in results():
        for w in warnings:
            warn(None, w)
        done += 1
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
            images.append(dict(name=name, res=-1, color=rgba, w=w, h=h,
                               flags=1 | (2 if full else 0), depth=depth))
            continue
        kind, data, lw, lh, full = result[:5]
        digest = hashlib.sha1(data).digest()
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
        images.append(dict(name=name, res=res, color=0xFFFFFFFF, w=lw, h=lh,
                           flags=(2 if full else 0) | (4 if kind in ("video", "cvh") else 0),
                           depth=depth))

    layer_records = []
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
                                  jpeg_quality=args.jpeg)
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
                      layer_records, voices)

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
                audio_refs=len(comp.resources), screen=(gw, gh))


if __name__ == "__main__":
    main()
