"""Stereoscopic 3D for movies: a right-eye view made from each frame's depth.

The 3DS shows the movie's own frames to the left eye and a second view,
synthesised here, to the right eye. For every frame:

1. depth: Depth Anything V2 Small (Apache-2.0, as ONNX, run with onnxruntime
   on the CPU) estimates relative inverse depth on some frames: every
   `KEY_MAX`-th, sooner when the picture changes a lot, and at every scene cut.
   Frames in between get the depth of the keyframes on either side, blended.
2. temporal smoothing: the depth range is normalised per keyframe to
   percentiles that follow an exponential moving average over the shot, and
   each keyframe's depth is averaged with the previous keyframe's where the
   picture didn't change, so the depth doesn't flicker. Both reset at cuts.
3. edges: a guided filter, guided by the frame itself, snaps the soft depth
   edges onto the picture's edges, then nearer regions grow by a pixel so an
   object's edge pixels move with the object (no halo of its colour on the
   background).
4. disparity: nearness 0..1 maps linearly (inverse depth is proportional to
   screen disparity) to `far_px` .. `near_px`: most of a scene sits behind
   the screen, its nearest part slightly in front.
5. the right view: depth-image-based rendering. Each pixel's disparity is
   splatted to where it lands in the right view, the nearest one wins, and
   the right view samples the left one through that disparity (sub-pixel,
   linear). Disoccluded pixels, which the left eye never saw, are filled
   from the background side of the hole, mirrored so its texture carries on,
   then softened.

Disparity is in pixels of the coded frame (positive: behind the screen, the
right eye's copy further right). Everything is deterministic: the same
frames give the same views (onnxruntime on the CPU with a fixed number of
threads; the depth is quantised).

This file has no imports from the rest of vnpack: vnpack runs it as a filter
with whatever Python has onnxruntime installed (`python stereo.py filter
...`: rgb24 frames on stdin, side-by-side rgb24 frames on stdout).
"""

import json
import os
import sys

import numpy as np

MODEL_FILE = "depth_anything_v2_small.onnx"
MODEL_URL = ("https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/"
             "4472b7362082ad9968fee890ca0f1e5aca36b93d/onnx/model.onnx")
MODEL_SHA256 = "afb6a5c28f3b6bf1618c6e43f02073ef9dfdc70e937502d51603e57b0a1df10c"
MODEL_BYTES = 99060839
MODEL_LICENSE = "Apache-2.0 (Depth Anything V2 Small, onnx-community export)"

# Disparity at full 3D, in coded pixels (432 wide for a 16:9 movie, shown
# about 427 px wide): the far end behind the screen, the near end in front.
FAR_PX = 6.0
NEAR_PX = -2.0
KEY_MAX = 3          # a depth estimate at least every this many frames
THREADS = 2          # onnxruntime threads per filter (fixed: determinism)
NET_H = 182          # network input height (multiple of 14); width follows the aspect


def model_dirs():
    """Where the model may be, in order: next to this file (a checkout,
    tools/vnpack/models/, gitignored), then the user's cache."""
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    cache = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
                         "vn3ds", "models")
    return [here, cache]


TEST_MODEL = ":test"   # VN3DS_DEPTH_MODEL=:test: brightness as depth (tests, no onnxruntime)


def find_model():
    env = os.environ.get("VN3DS_DEPTH_MODEL")
    if env:
        return env if env == TEST_MODEL or os.path.isfile(env) else None
    for d in model_dirs():
        p = os.path.join(d, MODEL_FILE)
        if os.path.isfile(p) and os.path.getsize(p) == MODEL_BYTES:
            return p
    return None


_runtime = {}


def runtime_python(model=None):
    """A Python that can run this file as the filter (has onnxruntime, numpy
    and Pillow): $VN3DS_PYTHON, this one, or the checkout's .venv. None if
    there is none (or this is a frozen build without the sources)."""
    test = model == TEST_MODEL
    if test and not getattr(sys, "frozen", False):
        return sys.executable
    if "py" in _runtime:
        return _runtime["py"]
    import subprocess
    here = os.path.abspath(__file__)
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    cands = [os.environ.get("VN3DS_PYTHON")]
    if not getattr(sys, "frozen", False):
        cands.append(sys.executable)
    for v in (".venv/bin/python3", ".venv/bin/python", ".venv/Scripts/python.exe"):
        cands.append(os.path.join(root, v))
    found = None
    if os.path.isfile(here):
        for py in cands:
            if not py or not os.path.isfile(py):
                continue
            try:
                r = subprocess.run([py, here, "check"], capture_output=True, timeout=120)
            except (OSError, subprocess.TimeoutExpired):
                continue
            if r.returncode == 0:
                found = py
                break
    _runtime["py"] = found
    return found


def available():
    """(python, model) when 3D movies can be made, else None."""
    model = find_model()
    py = runtime_python(model) if model else None
    return (py, model) if py and model else None


def download_model(say=print, dest_dir=None):
    """Fetches the model once (99 MB) into the first writable model folder
    and checks its SHA-256. Returns its path."""
    import hashlib
    import urllib.request
    dirs = [dest_dir] if dest_dir else model_dirs()
    last = None
    for d in dirs:
        try:
            os.makedirs(d, exist_ok=True)
            part = os.path.join(d, MODEL_FILE + ".part")
            say(f"downloading the depth model for 3D movies ({MODEL_BYTES / 1e6:.0f} MB, "
                f"{MODEL_LICENSE}) into {d}")
            h = hashlib.sha256()
            got = 0
            with urllib.request.urlopen(MODEL_URL, timeout=60) as r, open(part, "wb") as f:
                step = MODEL_BYTES // 10
                mark = step
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
                    h.update(b)
                    got += len(b)
                    if got >= mark:
                        say(f"  {got * 100 // MODEL_BYTES}%")
                        mark += step
            if h.hexdigest() != MODEL_SHA256:
                os.remove(part)
                raise OSError("the downloaded depth model doesn't match its checksum")
            path = os.path.join(d, MODEL_FILE)
            os.replace(part, path)
            return path
        except OSError as e:
            last = e
    raise OSError(f"cannot download the depth model: {last}")


# ---------------------------------------------------------------------------
# image helpers (numpy only)

def _box(a, r):
    """Mean over a (2r+1)^2 window, edges clamped (summed-area table)."""
    p = np.pad(a, ((r + 1, r), (r + 1, r)), mode="edge")
    c = p.cumsum(0).cumsum(1)
    n = 2 * r + 1
    s = c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]
    return s / float(n * n)


def guided_filter(guide, src, r=4, eps=2e-3):
    """He et al.'s guided filter with a grey guide: src's edges follow guide's."""
    mi, mp = _box(guide, r), _box(src, r)
    cov = _box(guide * src, r) - mi * mp
    var = _box(guide * guide, r) - mi * mi
    a = cov / (var + eps)
    b = mp - a * mi
    return _box(a, r) * guide + _box(b, r)


def _resize(a, w, h):
    from PIL import Image
    return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w, h), Image.BILINEAR),
                      np.float32)


def grey(rgb):
    return (rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114).astype(np.float32) / 255


# ---------------------------------------------------------------------------
# depth

class TestDepth:
    """Brightness as nearness: for tests without the model."""

    def __init__(self, w, h):
        self.w, self.h = w, h

    def __call__(self, rgb):
        return grey(rgb)


class Depth:
    """Depth Anything V2 Small: relative inverse depth (larger = nearer)."""

    def __init__(self, model, w, h, threads=THREADS):
        import onnxruntime as ort
        if hasattr(ort, "disable_telemetry_events"):
            ort.disable_telemetry_events()
        self.nh = NET_H
        self.nw = max(14, int(round(NET_H * w / h / 14.0)) * 14)
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads
        so.inter_op_num_threads = 1
        so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        so.log_severity_level = 3
        # don't spin while waiting for work: several filters share the CPU
        # with x264 (vnpack converts a few movies at once)
        so.add_session_config_entry("session.intra_op.allow_spinning", "0")
        so.add_session_config_entry("session.inter_op.allow_spinning", "0")
        for n, v in (("batch_size", 1), ("height", self.nh), ("width", self.nw)):
            so.add_free_dimension_override_by_name(n, v)
        self.s = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"])
        self.w, self.h = w, h
        self.mean = np.array([0.485, 0.456, 0.406], np.float32) * 255
        self.std = np.array([0.229, 0.224, 0.225], np.float32) * 255

    def __call__(self, rgb):
        from PIL import Image
        x = np.asarray(Image.fromarray(rgb).resize((self.nw, self.nh), Image.BICUBIC), np.float32)
        x = ((x - self.mean) / self.std).transpose(2, 0, 1)[None]
        d = self.s.run(None, {"pixel_values": np.ascontiguousarray(x, np.float32)})[0][0]
        return _resize(d, self.w, self.h)


# ---------------------------------------------------------------------------
# view synthesis

def right_view(left, disp):
    """Depth-image-based rendering: the right eye's view of `left` (h x w x 3
    uint8) where pixel x has disparity disp[y, x] (px, positive = behind:
    it appears at x + disp in the right view). Returns uint8 h x w x 3."""
    h, w = disp.shape
    xs = np.arange(w, dtype=np.float32)[None, :]
    t = xs + disp                                   # where each pixel lands
    rows = (np.arange(h) * w)[:, None]
    # splat the disparity to the two pixels around each landing spot; the
    # nearest (smallest disparity) wins
    dr = np.full(h * w, np.inf, np.float32)
    f = np.floor(t).astype(np.int64)
    for c in (f, f + 1):
        ok = (c >= 0) & (c < w)
        np.minimum.at(dr, (rows + c)[ok], disp[ok])
    dr = dr.reshape(h, w)
    hole = ~np.isfinite(dr)
    # sample the left view through it (linear, horizontal only)
    d0 = np.where(hole, 0, dr)
    sx = np.clip(xs - d0, 0, w - 1)
    x0 = np.floor(sx).astype(np.int64)
    x1 = np.minimum(x0 + 1, w - 1)
    a = (sx - x0)[..., None]
    L = left.astype(np.float32)
    yy = np.arange(h)[:, None]
    out = L[yy, x0] * (1 - a) + L[yy, x1] * a
    if hole.any():
        out = fill_holes(out, hole)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def fill_holes(img, hole):
    """Fills disoccluded pixels from the side of the hole that is background
    (the right side in a right-eye view), mirrored about the hole's edge so
    the background's texture carries on, then softens what was filled."""
    h, w = hole.shape
    idx = np.where(hole, w, np.arange(w)[None, :])
    nxt = np.minimum.accumulate(idx[:, ::-1], axis=1)[:, ::-1]      # next valid to the right
    idx2 = np.where(hole, -1, np.arange(w)[None, :])
    prv = np.maximum.accumulate(idx2, axis=1)                         # previous valid to the left
    x = np.arange(w)[None, :]
    use_r = nxt < w
    src = np.where(use_r, nxt + (nxt - x) - 1, prv - (x - prv) + 1)  # mirrored
    anchor = np.where(use_r, nxt, prv)
    src = np.clip(src, 0, w - 1)
    yy = np.arange(h)[:, None].repeat(w, 1)
    bad = hole[yy, src] | (use_r & (src <= x)) | (~use_r & (src >= x))
    src = np.where(bad, anchor, src)
    src = np.clip(src, 0, w - 1)
    filled = img.copy()
    filled[hole] = img[yy[hole], src[hole]]
    # soften the filled pixels (and one around them) horizontally
    soft = filled.copy()
    soft[:, 1:-1] = (filled[:, :-2] + 2 * filled[:, 1:-1] + filled[:, 2:]) / 4
    near = hole.copy()
    near[:, 1:] |= hole[:, :-1]
    near[:, :-1] |= hole[:, 1:]
    filled[near] = soft[near]
    return filled


def grow_near(n, px=1):
    """Grows nearer regions (larger n) by px pixels horizontally."""
    out = n.copy()
    for k in range(1, px + 1):
        out[:, k:] = np.maximum(out[:, k:], n[:, :-k])
        out[:, :-k] = np.maximum(out[:, :-k], n[:, k:])
    return out


# ---------------------------------------------------------------------------
# a whole clip

def _small(rgb):
    g = grey(rgb)
    h, w = g.shape
    return g[: h // 4 * 4, : w // 4 * 4].reshape(h // 4, 4, w // 4, 4).mean((1, 3))


class Stereo:
    """Turns a clip's frames, in order, into side-by-side stereo frames.

    push(frame) returns the frames that are ready (a few frames of delay:
    the depth between keyframes is blended from both ends), flush() the
    rest. stats() gives the disparity range used."""

    def __init__(self, depth, far_px=FAR_PX, near_px=NEAR_PX, key_max=KEY_MAX):
        self.depth = depth
        self.far, self.near = far_px, near_px
        self.key_max = key_max
        self.pending = []          # frames since the last keyframe (excluded)
        self.last = None           # (frame, nearness) of the last keyframe
        self.lo = self.hi = None   # normalisation (EMA over the shot)
        self.hist = np.zeros(64, np.int64)
        self.nkeys = 0
        self.nframes = 0
        self.ncuts = 0
        self.keep_disp = None      # a list: every frame's disparity is kept (tests)

    # nearness 0 (far) .. 1 (near) for a keyframe, smoothed over the shot
    def _key(self, rgb, cut):
        raw = self.depth(rgb)
        lo, hi = np.percentile(raw, (2, 98))
        if hi - lo < 1e-3:
            hi = lo + 1e-3
        if cut or self.lo is None:
            self.lo, self.hi = lo, hi
        else:
            self.lo += 0.25 * (lo - self.lo)
            self.hi += 0.25 * (hi - self.hi)
        n = np.clip((raw - self.lo) / (self.hi - self.lo), 0, 1).astype(np.float32)
        if not cut and self.last is not None:
            # average with the previous keyframe where the picture held still
            change = np.abs(grey(rgb) - grey(self.last[0]))
            change = guided_filter(change, change, 3, 1e-2)
            keep = np.clip(0.5 - change * 6, 0, 0.5).astype(np.float32)
            n = n * (1 - keep) + self.last[1] * keep
        self.nkeys += 1
        return np.round(n * 4096) / 4096   # quantised: deterministic downstream

    def _views(self, rgb, n):
        g = grey(rgb)
        n = np.clip(guided_filter(g, n, 4, 2e-3), 0, 1)
        n = grow_near(n, 1)
        disp = (self.far + (self.near - self.far) * n).astype(np.float32)
        disp = np.round(disp * 16) / 16
        h = np.histogram(disp, 64, (self.near - 1, self.far + 1))[0]
        self.hist += h
        self.disp = disp
        if self.keep_disp is not None:
            self.keep_disp.append(disp)
        right = right_view(rgb, disp)
        self.nframes += 1
        return np.concatenate([rgb, right], axis=1)

    def push(self, rgb):
        out = []
        cut = False
        if self.last is not None:
            ref = self.pending[-1] if self.pending else self.last[0]
            diff = float(np.abs(_small(rgb) - _small(ref)).mean())
            cut = diff > 0.12
            moved = float(np.abs(_small(rgb) - _small(self.last[0])).mean())
        if self.last is None or cut:
            if cut:
                self.ncuts += 1
                # frames before the cut keep the last keyframe's depth
                for f in self.pending:
                    out.append(self._views(f, self.last[1]))
                self.pending = []
            n = self._key(rgb, True)
            self.last = (rgb, n)
            out.append(self._views(rgb, n))
            return out
        self.pending.append(rgb)
        if len(self.pending) >= self.key_max or moved > 0.06:
            k = self.pending.pop()
            n = self._key(k, False)
            m = len(self.pending) + 1
            for i, f in enumerate(self.pending):
                a = (i + 1) / m
                out.append(self._views(f, self.last[1] * (1 - a) + n * a))
            self.pending = []
            self.last = (k, n)
            out.append(self._views(k, n))
        return out

    def flush(self):
        out = [self._views(f, self.last[1]) for f in self.pending]
        self.pending = []
        return out

    def stats(self):
        """Disparity range (px): the median, and 5th / 95th percentiles."""
        c = np.cumsum(self.hist)
        edges = np.linspace(self.near - 1, self.far + 1, 65)

        def pct(p):
            if c[-1] == 0:
                return 0.0
            i = int(np.searchsorted(c, c[-1] * p))
            return float(round((edges[i] + edges[i + 1]) / 2, 2))
        return dict(mid=pct(0.5), p5=pct(0.05), p95=pct(0.95), far=self.far, near=self.near,
                    frames=self.nframes, keyframes=self.nkeys, cuts=self.ncuts)


# ---------------------------------------------------------------------------
# the filter vnpack runs

def _read_exact(f, n):
    buf = bytearray()
    while len(buf) < n:
        b = f.read(n - len(buf))
        if not b:
            break
        buf += b
    return bytes(buf)


def run_filter(model, w, h, stats_path, far_px=FAR_PX, near_px=NEAR_PX):
    st = Stereo(TestDepth(w, h) if model == TEST_MODEL else Depth(model, w, h), far_px, near_px)
    inp, out = sys.stdin.buffer, sys.stdout.buffer
    n = w * h * 3
    while True:
        b = _read_exact(inp, n)
        if len(b) < n:
            break
        for f in st.push(np.frombuffer(b, np.uint8).reshape(h, w, 3)):
            out.write(np.ascontiguousarray(f).tobytes())
    for f in st.flush() if st.last is not None else []:
        out.write(np.ascontiguousarray(f).tobytes())
    out.flush()
    with open(stats_path, "w") as f:
        json.dump(st.stats(), f)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="stereo.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("filter", help="rgb24 frames on stdin -> side-by-side rgb24 on stdout")
    p.add_argument("--model", required=True)
    p.add_argument("--size", required=True, help="WxH of the input frames")
    p.add_argument("--stats", required=True, help="where to write the disparity stats (JSON)")
    p.add_argument("--far", type=float, default=FAR_PX)
    p.add_argument("--near", type=float, default=NEAR_PX)
    sub.add_parser("check", help="exit 0 when onnxruntime and numpy import")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        import onnxruntime  # noqa: F401
        from PIL import Image  # noqa: F401
        return 0
    w, h = (int(v) for v in a.size.lower().split("x"))
    run_filter(a.model, w, h, a.stats, a.far, a.near)
    sys.stdout.flush()
    sys.stderr.flush()
    # Leave without running onnxruntime's exit handlers: its telemetry
    # teardown can spin for many minutes after the work is done.
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
