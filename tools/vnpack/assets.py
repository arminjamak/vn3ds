"""Game file access (loose files and .rpa archives), image building and
texture/audio conversion for vn3ds."""

import ast
import io
import os
import pickle
import shutil
import struct
import subprocess
import tempfile
import zlib

import numpy as np
from PIL import Image

from .compiler import dotted, parse_color

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tga")
AUDIO_EXTS = (".ogg", ".opus", ".mp3", ".wav", ".flac", ".oga", ".m4a")
MAX_TEX = 1024


# --------------------------------------------------------------------------
# File system
# --------------------------------------------------------------------------

class _IndexUnpickler(pickle.Unpickler):
    """RPA indexes only hold dicts/lists/tuples/strings/ints; refuse anything
    that would need a class, so a hostile archive can't run code."""

    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"refusing to load {module}.{name} from an RPA index")


def _fix_text(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    try:
        return v.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return v


def _fix_bytes(v):
    if isinstance(v, bytes):
        return v
    if isinstance(v, str):
        return v.encode("latin-1", "replace")
    return b""


def read_rpa(path, base=0):
    """Index of an .rpa archive that starts `base` bytes into `path` (non-zero
    when the archive is stored inside an .apk). Offsets returned are absolute."""
    with open(path, "rb") as f:
        f.seek(base)
        header = f.readline()
        parts = header.split()
        if not parts:
            raise ValueError("empty archive")
        if parts[0] == b"RPA-3.0":
            offset, key = int(parts[1], 16), int(parts[2], 16)
        elif parts[0] == b"RPA-2.0":
            offset, key = int(parts[1], 16), 0
        else:
            raise ValueError(f"unsupported archive format {parts[0][:16]!r}")
        f.seek(base + offset)
        data = zlib.decompress(f.read())
    index = _IndexUnpickler(io.BytesIO(data), encoding="latin-1").load()
    out = {}
    for name, entries in index.items():
        name = _fix_text(name)
        e = entries[0]
        off, length = e[0] ^ key, e[1] ^ key
        prefix = _fix_bytes(e[2]) if len(e) > 2 else b""
        out[name] = (base + off, length, prefix)
    return out


def _zip_data_offset(path, info):
    """Where a stored zip member's bytes start in the zip file."""
    import struct as _st
    with open(path, "rb") as f:
        f.seek(info.header_offset)
        hdr = f.read(30)
        if hdr[:4] != b"PK\x03\x04":
            raise ValueError("bad zip local header")
        n, m = _st.unpack("<HH", hdr[26:30])
    return info.header_offset + 30 + n + m


def apk_game_path(member):
    """Map a zip member to a path inside the game folder, or None.

    Ren'Py's Android builds keep the game in assets/x-game/ with every path
    component prefixed by "x-"; plain zips just have a game/ folder."""
    parts = member.split("/")
    for i, p in enumerate(parts):
        if p in ("x-game", "game") and i + 1 < len(parts):
            rest = parts[i + 1:]
            if p == "x-game":
                rest = [c[2:] if c.startswith("x-") else c for c in rest]
            return "/".join(rest)
    return None


class AssetFS:
    """Case-insensitive lookup of game files: loose files, .rpa archives, and
    the game inside an Android .apk / .zip (read in place, never unpacked).

    `overlay_dirs` are searched first, so decompiled .rpy files can be added
    next to an archive that only has .rpyc."""

    def __init__(self, game_dir, warn, overlay_dirs=()):
        import zipfile
        self.game_dir = game_dir
        self.files = {}
        archives = []  # (container path, base offset, display name)
        self.zips = {}
        roots = list(overlay_dirs)
        is_zip = os.path.isfile(game_dir) and zipfile.is_zipfile(game_dir)
        if not is_zip:
            roots.append(game_dir)
        for top in roots:
            for root, dirs, files in os.walk(top):
                dirs[:] = [d for d in dirs if d not in ("cache", "saves", "__pycache__")]
                for fn in files:
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, top).replace(os.sep, "/")
                    if fn.lower().endswith(".rpa"):
                        archives.append((full, 0, fn))
                        continue
                    self.files.setdefault(rel.lower(), ("disk", full, rel))
        if is_zip:
            z = zipfile.ZipFile(game_dir)
            self.zips[game_dir] = z
            self._pid = os.getpid()
            for info in z.infolist():
                rel = apk_game_path(info.filename)
                if not rel or info.is_dir():
                    continue
                if rel.lower().endswith(".rpa"):
                    if info.compress_type != zipfile.ZIP_STORED:
                        warn(None, f"{rel} is compressed inside the archive; unpack the .apk first")
                        continue
                    archives.append((game_dir, _zip_data_offset(game_dir, info), rel))
                    continue
                self.files.setdefault(rel.lower(), ("zip", game_dir, rel, info.filename))
        for arc, base, shown in sorted(archives):
            try:
                index = read_rpa(arc, base)
            except (ValueError, OSError, zlib.error, pickle.UnpicklingError, EOFError) as e:
                warn(None, f"cannot read archive {shown}: {e}")
                continue
            for name, (off, length, prefix) in index.items():
                key = name.replace("\\", "/").lower()
                self.files.setdefault(key, ("rpa", arc, name, off, length, prefix))

    def find(self, name, dirs=("", "images/")):
        name = name.replace("\\", "/").lstrip("/").lower()
        for d in dirs:
            if d + name in self.files:
                return d + name
        return None

    def read(self, key):
        entry = self.files[key]
        if entry[0] == "disk":
            with open(entry[1], "rb") as f:
                return f.read()
        if entry[0] == "zip":
            if getattr(self, "_pid", None) != os.getpid():
                import zipfile
                self.zips = {p: zipfile.ZipFile(p) for p in self.zips}
                self._pid = os.getpid()
            return self.zips[entry[1]].read(entry[3])
        _, arc, _, off, length, prefix = entry
        with open(arc, "rb") as f:
            f.seek(off)
            return prefix + f.read(length - len(prefix))

    def display(self, key):
        e = self.files[key]
        return e[2]

    def keys(self):
        return self.files.keys()


# --------------------------------------------------------------------------
# Image definitions -> pixels
# --------------------------------------------------------------------------

class ImageBuilder:
    def __init__(self, fs, comp, game_w, game_h, warn):
        self.fs = fs
        self.comp = comp
        self.game_w = game_w
        self.game_h = game_h
        self.warn = warn
        self.extra_defs = {}   # automatic images etc., set by the packager
        # Small LRU: composites reuse parts, but a big game has thousands of
        # full-HD pictures that must not all stay in memory.
        from collections import OrderedDict
        self.cache = OrderedDict()

    def source(self, definition):
        """An image definition (from the compiler or auto images) -> source tree."""
        kind = definition[0]
        if kind == "file":
            return ("file", definition[1])
        if kind == "alias":
            return self.source(definition[1])
        if kind == "expr":
            _, src, line = definition
            try:
                node = ast.parse(src, mode="eval").body
            except SyntaxError:
                self.warn(line, f"cannot parse image expression {src}")
                return None
            return self.ev(node, line, 0)
        if kind == "atl":
            _, block, line = definition
            # Animated images: use the first displayable in the block.
            for l in walk_lines(block):
                t = l.text.strip()
                if t[:1] in "\"'":
                    end = t.find(t[0], 1)
                    try:
                        node = ast.parse(t[:end + 1], mode="eval").body
                    except SyntaxError:
                        continue
                    self.warn_once("anim", line, "animated images show their first frame only")
                    return self.ev(node, line, 0)
            self.warn(line, "image block has no displayable")
            return None
        return None

    def warn_once(self, key, line, msg):
        self.comp.warn_once("img:" + key, line, msg)

    def ev(self, node, line, depth):
        if depth > 10:
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if s.startswith("#"):
                return ("solid", parse_color(s), None, None)
            key = self.fs.find(s)
            if key is not None:
                return ("file", key)
            if s in self.comp.image_defs or s in self.extra_defs:
                return ("ref", s)
            self.warn(line, f"image file '{s}' not found")
            return None
        name = dotted(node)
        if name is not None:
            if name in self.comp.defines:
                return self.ev(self.comp.defines[name][0], line, depth + 1)
            self.warn(line, f"unknown displayable '{name}'")
            return None
        if not isinstance(node, ast.Call):
            self.warn(line, f"unsupported image expression {ast.unparse(node)}")
            return None
        fn = dotted(node.func) or ""
        args = node.args
        kw = {k.arg: k.value for k in node.keywords if k.arg}

        def const(n, default=None):
            if n is None:
                return default
            try:
                return ast.literal_eval(n)
            except (ValueError, SyntaxError):
                try:
                    return self.comp.eval_ast(n, {})
                except Exception:
                    return default

        def child(i=0, key="im"):
            n = args[i] if len(args) > i else kw.get(key)
            return self.ev(n, line, depth + 1) if n is not None else None

        if fn in ("Image", "im.Image"):
            return child(0, "filename")
        if fn == "Solid":
            size = const(kw.get("xysize"))
            w = const(kw.get("xsize")) or (size[0] if size else None)
            h = const(kw.get("ysize")) or (size[1] if size else None)
            return ("solid", parse_color(const(args[0] if args else kw.get("color"), "#000")),
                    w, h)
        if fn in ("Composite", "LiveComposite", "im.Composite"):
            size = const(args[0] if args else kw.get("size"))
            parts = []
            for pos, ch in zip(args[1::2], args[2::2]):
                p = const(pos, (0, 0))
                c = self.ev(ch, line, depth + 1)
                if c is not None:
                    parts.append((int(p[0]), int(p[1]), c))
            if not size:
                size = (self.game_w, self.game_h)
            return ("composite", int(size[0]), int(size[1]), parts)
        if fn in ("Transform", "At"):
            c = child(0, "child")
            if c is None:
                return None
            zoom = float(const(kw.get("zoom"), 1.0))
            xz = float(const(kw.get("xzoom"), 1.0)) * zoom
            yz = float(const(kw.get("yzoom"), 1.0)) * zoom
            alpha = float(const(kw.get("alpha"), 1.0))
            size = const(kw.get("size")) or const(kw.get("xysize"))
            if size:
                return ("scale", c, int(size[0]), int(size[1]))
            if fn == "At":
                self.warn_once("at", line, "At(...) in image definitions ignores the transforms")
            return ("xform", c, xz, yz, alpha)
        if fn in ("im.Flip", "Flip"):
            return ("flip", child(), bool(const(kw.get("horizontal"), False)),
                    bool(const(kw.get("vertical"), False)))
        if fn == "im.Scale":
            return ("scale", child(), int(const(args[1])), int(const(args[2])))
        if fn == "im.FactorScale":
            fx = float(const(args[1]))
            fy = float(const(args[2])) if len(args) > 2 else fx
            return ("xform", child(), fx, fy, 1.0)
        if fn in ("im.Crop", "Crop"):
            if fn == "Crop":
                rect = const(args[0])
                c = self.ev(args[1], line, depth + 1) if len(args) > 1 else None
            else:
                c = child()
                rect = const(args[1]) if len(args) == 2 else tuple(const(a) for a in args[1:5])
            return ("crop", c, tuple(int(v) for v in rect))
        if fn in ("im.Grayscale", "im.Sepia"):
            return ("gray" if fn.endswith("Grayscale") else "sepia", child())
        if fn == "im.Alpha":
            return ("xform", child(), 1.0, 1.0, float(const(args[1], 1.0)))
        if fn in ("Movie", "MovieDisplayable"):
            play = const(kw.get("play")) or (const(args[0]) if args else None)
            if isinstance(play, (list, tuple)):
                play = play[0] if play else None
            if not isinstance(play, str):
                self.warn(line, "Movie without a play= file")
                return None
            key = self.fs.find(play, dirs=("", "images/", "video/", "movies/"))
            if key is None:
                self.warn(line, f"movie file '{play}' not found")
                return None
            loop = const(kw.get("loop"), True)
            return ("movie", key, bool(loop))
        if fn in ("im.MatrixColor", "im.Recolor", "im.Tile", "im.AlphaMask"):
            self.warn_once(fn, line, f"{fn} is ignored (the plain image is used)")
            return child()
        if fn in ("ConditionSwitch", "ShowingSwitch"):
            self.warn_once(fn, line, f"{fn} always shows its first option")
            return self.ev(args[1], line, depth + 1) if len(args) > 1 else None
        self.warn(line, f"unsupported displayable {fn}()")
        return None

    def render(self, src, depth=0):
        """Render a source tree to an RGBA PIL image at virtual resolution."""
        if src is None or depth > 16:
            return None
        key = repr(src)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        kind = src[0]
        img = None
        if kind == "file":
            data = self.fs.read(src[1])
            im = Image.open(io.BytesIO(data))
            im.load()
            img = im.convert("RGBA")
        elif kind == "solid":
            _, rgba, w, h = src
            color = ((rgba >> 24) & 255, (rgba >> 16) & 255, (rgba >> 8) & 255, rgba & 255)
            img = Image.new("RGBA", (int(w or self.game_w), int(h or self.game_h)), color)
        elif kind == "ref":
            d = self.comp.image_defs.get(src[1]) or self.extra_defs.get(src[1])
            img = self.render(self.source(d), depth + 1) if d else None
        elif kind == "composite":
            _, w, h, parts = src
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            for x, y, c in parts:
                ci = self.render(c, depth + 1)
                if ci is not None:
                    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                    layer.paste(ci, (x, y))
                    img = Image.alpha_composite(img, layer)
        elif kind == "xform":
            _, c, xz, yz, alpha = src
            ci = self.render(c, depth + 1)
            if ci is not None:
                w = max(1, int(round(ci.width * abs(xz))))
                h = max(1, int(round(ci.height * abs(yz))))
                img = resize_rgba(ci, w, h) if (w, h) != ci.size else ci.copy()
                if xz < 0:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                if yz < 0:
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
                if alpha < 1.0:
                    a = np.asarray(img).copy()
                    a[..., 3] = (a[..., 3].astype(np.float32) * alpha).astype(np.uint8)
                    img = Image.fromarray(a, "RGBA")
        elif kind == "flip":
            _, c, h, v = src
            img = self.render(c, depth + 1)
            if img is not None:
                if h:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                if v:
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
        elif kind == "scale":
            _, c, w, h = src
            ci = self.render(c, depth + 1)
            img = resize_rgba(ci, w, h) if ci is not None else None
        elif kind == "crop":
            _, c, (x, y, w, h) = src
            ci = self.render(c, depth + 1)
            img = ci.crop((x, y, x + w, y + h)) if ci is not None else None
        elif kind in ("gray", "sepia"):
            ci = self.render(src[1], depth + 1)
            if ci is not None:
                a = ci.getchannel("A")
                g = ci.convert("L")
                if kind == "sepia":
                    from PIL import ImageOps
                    g = ImageOps.colorize(g, (40, 26, 13), (255, 240, 192))
                img = g.convert("RGBA")
                img.putalpha(a)
        self.cache[key] = img
        while len(self.cache) > 8:
            self.cache.popitem(last=False)
        return img


def walk_lines(block):
    for l in block:
        yield l
        yield from walk_lines(l.block)


def resize_rgba(img, w, h):
    """Resize with premultiplied alpha so transparent edges don't go dark."""
    if (w, h) == img.size:
        return img
    return img.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")


# --------------------------------------------------------------------------
# Textures
# --------------------------------------------------------------------------

FMT_RGBA8, FMT_RGB8, FMT_RGB565 = 0, 1, 2
_swizzle_cache = {}


def next_pow2(n):
    p = 8
    while p < n:
        p *= 2
    return p


def swizzle_index(tw, th):
    """Destination index of each (memory row, column) in PICA200 tiled order."""
    key = (tw, th)
    idx = _swizzle_cache.get(key)
    if idx is None:
        y = np.arange(th, dtype=np.int64)[:, None]
        x = np.arange(tw, dtype=np.int64)[None, :]
        tile = (y >> 3) * (tw >> 3) + (x >> 3)
        morton = ((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) |
                  ((x & 4) << 2) | ((y & 4) << 3))
        idx = (tile * 64 + morton).ravel()
        _swizzle_cache[key] = idx
    return idx


def bleed_edges(arr, iterations=6):
    """Copy colour from opaque pixels into neighbouring transparent ones so
    bilinear filtering doesn't pull in black at sprite edges."""
    alpha = arr[..., 3]
    known = alpha > 0
    if known.all() or not known.any():
        return arr
    rgb = arr[..., :3].astype(np.float32)
    for _ in range(iterations):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(alpha.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            k = np.roll(known, (dy, dx), (0, 1))
            acc += np.roll(rgb, (dy, dx), (0, 1)) * k[..., None]
            cnt += k
        new = (~known) & (cnt > 0)
        if not new.any():
            break
        rgb[new] = acc[new] / cnt[new][:, None]
        known |= new
    out = arr.copy()
    out[..., :3] = np.where((alpha > 0)[..., None], arr[..., :3], rgb.astype(np.uint8))
    return out


def encode_ctex(img, logical_w, logical_h, allow_565=False):
    """Encode a PIL RGBA image (already at its on-screen size) as .ctex bytes.

    Returns (bytes, opaque).
    """
    w, h = img.size
    if w > MAX_TEX or h > MAX_TEX:
        f = min(MAX_TEX / w, MAX_TEX / h)
        w, h = max(1, int(w * f)), max(1, int(h * f))
        img = resize_rgba(img, w, h)
    arr = np.asarray(img.convert("RGBA"), dtype=np.uint8)
    opaque = bool(arr[..., 3].min() == 255)
    if not opaque:
        arr = bleed_edges(arr)
    tw, th = next_pow2(w), next_pow2(h)
    canvas = np.pad(arr, ((0, th - h), (0, tw - w), (0, 0)), mode="edge")
    rows = canvas.reshape(-1, 4)  # top row first, as tex3ds does
    idx = swizzle_index(tw, th)
    if opaque and allow_565:
        fmt, bpp = FMT_RGB565, 2
        r = rows[:, 0].astype(np.uint16)
        g = rows[:, 1].astype(np.uint16)
        b = rows[:, 2].astype(np.uint16)
        px = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        out = np.empty(tw * th, np.uint16)
        out[idx] = px
        payload = out.astype("<u2").tobytes()
    elif opaque:
        fmt, bpp = FMT_RGB8, 3
        out = np.empty((tw * th, 3), np.uint8)
        out[idx] = rows[:, [2, 1, 0]]
        payload = out.tobytes()
    else:
        fmt, bpp = FMT_RGBA8, 4
        out = np.empty((tw * th, 4), np.uint8)
        out[idx] = rows[:, [3, 2, 1, 0]]
        payload = out.tobytes()
    packed = zlib.compress(payload, 9)
    header = b"CTEX" + struct.pack("<HHHHHHffIII", 1, fmt, tw, th, w, h,
                                   float(logical_w), float(logical_h), 1,
                                   len(payload), len(packed))
    assert len(header) == 36
    return header + packed, opaque


# --------------------------------------------------------------------------
# Audio
# --------------------------------------------------------------------------

def is_ogg_vorbis(data):
    return data[:4] == b"OggS" and b"\x01vorbis" in data[:256]


def convert_audio(data, name, out_path, warn):
    """Write Ogg Vorbis to out_path, transcoding with ffmpeg when needed."""
    if is_ogg_vorbis(data):
        with open(out_path, "wb") as f:
            f.write(data)
        return True
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        warn(None, f"{name}: not Ogg Vorbis and ffmpeg is not installed; skipped")
        return False
    ext = os.path.splitext(name)[1] or ".bin"
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in" + ext)
        with open(src, "wb") as f:
            f.write(data)
        cmd = [ffmpeg, "-v", "error", "-y", "-i", src, "-vn", "-ac", "2", "-ar", "32000",
               "-c:a", "libvorbis", "-q:a", "3", out_path]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0:
            # Builds without libvorbis only have ffmpeg's experimental encoder.
            cmd = [ffmpeg, "-v", "error", "-y", "-i", src, "-vn", "-ac", "2", "-ar", "32000",
                   "-c:a", "vorbis", "-strict", "-2", "-b:a", "112k", out_path]
            r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0:
            warn(None, f"{name}: ffmpeg failed: {r.stderr.decode(errors='replace').strip()}")
            return False
    return True


# --------------------------------------------------------------------------
# Video (.cvid)
# --------------------------------------------------------------------------
#
#   "CVID" u16 version(2) u16 format(2 = RGB565) u16 tex_w tex_h img_w img_h
#   f32 logical_w logical_h f32 fps u32 frames u32 flags(1 = loop) u32 reserved
#   u32 offset[frames] u32 size[frames]   (from the start of the file)
#   frame k = zlib(changed-tile bitmap + changed tiles), frame 0 = all tiles
#
# Frames are already in the PICA200 tiled layout, so the 3DS just XORs the
# delta into its copy and uploads it. Still parts of an animation cost
# almost nothing.

def video_frames(data, name, w, h, fps, max_seconds):
    """Decode a movie (any format ffmpeg reads) into RGB frames of w x h."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise OSError("ffmpeg is needed to convert movies")
    ext = os.path.splitext(name)[1] or ".webm"
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in" + ext)
        with open(src, "wb") as f:
            f.write(data)
        cmd = [ffmpeg, "-v", "error", "-i", src, "-t", str(max_seconds), "-an",
               "-vf", f"fps={fps},scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0:
            raise OSError(r.stderr.decode(errors="replace").strip()[:200])
    raw = np.frombuffer(r.stdout, np.uint8)
    n = len(raw) // (w * h * 3)
    return raw[: n * w * h * 3].reshape(n, h, w, 3)


def encode_cvid(frames, logical_w, logical_h, fps, loop, threshold=2):
    """Version 2: per frame, only the 8x8 tiles that changed visibly.

    frame = zlib(bitmap of changed tiles (1 bit per tile) + those tiles' 64
    RGB565 pixels each, in tile order). Frame 0 stores every tile. A tile counts
    as changed when any colour channel moves by more than `threshold` steps
    (5/6/5-bit units) from what the decoder currently shows, so tiny
    shimmer is skipped and the error never accumulates."""
    n, h, w, _ = frames.shape
    tw, th = next_pow2(w), next_pow2(h)
    idx = swizzle_index(tw, th)
    ntiles = (tw // 8) * (th // 8)
    shown = np.zeros((ntiles, 64), np.uint16)
    chunks = []
    for k in range(n):
        canvas = np.pad(frames[k], ((0, th - h), (0, tw - w), (0, 0)), mode="edge").reshape(-1, 3)
        r = canvas[:, 0].astype(np.int32) >> 3
        g = canvas[:, 1].astype(np.int32) >> 2
        b = canvas[:, 2].astype(np.int32) >> 3
        tex = np.empty(tw * th, np.uint16)
        tex[idx] = ((r << 11) | (g << 5) | b).astype(np.uint16)
        tiles = tex.reshape(ntiles, 64)
        if k == 0:
            changed = np.ones(ntiles, bool)
        else:
            def ch(v):
                return ((v >> 11) & 31).astype(np.int16), ((v >> 5) & 63).astype(np.int16), (v & 31).astype(np.int16)
            a1, a2, a3 = ch(tiles)
            b1, b2, b3 = ch(shown)
            diff = np.maximum(np.maximum(np.abs(a1 - b1), np.abs(a2 - b2) // 2), np.abs(a3 - b3))
            changed = diff.max(axis=1) > threshold
        shown[changed] = tiles[changed]
        bitmap = np.packbits(changed, bitorder="little").tobytes()
        chunks.append(zlib.compress(bitmap + tiles[changed].astype("<u2").tobytes(), 9))
    head = b"CVID" + struct.pack("<HHHHHHfffIII", 2, 2, tw, th, w, h, float(logical_w),
                                 float(logical_h), float(fps), n, 1 if loop else 0, 0)
    assert len(head) == 40
    table_at = len(head)
    offset = table_at + 8 * n
    offs, sizes = [], []
    for c in chunks:
        offs.append(offset)
        sizes.append(len(c))
        offset += len(c)
    return head + struct.pack(f"<{n}I", *offs) + struct.pack(f"<{n}I", *sizes) + b"".join(chunks)
