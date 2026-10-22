"""Movies in a web page: assets.H264_ENCODER on the page's own decoder and
x264 workers (server/link/web/convert/h264.js, vn3dsMovie).

In a browser vnpack runs on Pyodide, where ffmpeg (ffmpeg.wasm) decodes and
encodes a movie in one thread at a few frames a second. h264.js decodes with
the browser (WebCodecs) and runs x264 in several workers, and the movies
after the current one are started early (assets.prefetch_cvh), so a game
with hours of movies converts in a fraction of the time.

The wait for a movie is a JS promise, which Python waits on with
pyodide.ffi.run_sync: the conversion must be entered with callPromising
(JSPI). Where that isn't possible (a browser without JSPI), install() does
nothing and ffmpeg.wasm makes the movies as before."""

from fractions import Fraction


def available():
    try:
        import js
        from pyodide.ffi import can_run_sync   # noqa: F401
        return hasattr(js, "vn3dsMovie")
    except ImportError:
        return False


def install():
    """Use the page's movie encoder for the conversions that follow. True
    when it is in use."""
    from . import assets
    if not available():
        return False
    import js
    from pyodide.ffi import can_run_sync, run_sync, to_js

    started = set()

    def encoder(key, data, ext, w, h, fps_cap, kbps, gop_seconds, max_seconds, profile, level,
                preset, wait):
        if not can_run_sync():
            return None   # (not entered with callPromising: ffmpeg it is)
        # a movie already started isn't handed over again
        bytes_js = None if key in started or data is None else to_js(data)
        if wait:
            started.discard(key)
        else:
            started.add(key)
        p = js.vn3dsMovie(key, bytes_js, ext, w, h, fps_cap, kbps, gop_seconds, max_seconds,
                          profile, level, preset, wait)
        if not wait:
            return None
        r = run_sync(p)
        if r is None:
            return None
        first = r.first.to_bytes() if r.first is not None else None
        return r.annexb.to_bytes(), first, Fraction(int(r.fpsNum), int(r.fpsDen))

    assets.H264_ENCODER = encoder
    return True
