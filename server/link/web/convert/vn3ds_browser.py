"""vnpack in a web page (Pyodide, in convert/worker.js).

The converter is the same code as `vn3ds-port`; what a browser lacks is
stood in for here:
- ffmpeg and ffprobe: subprocess.run on them goes to ffmpeg.wasm, through
  the worker's ff_exec (files are copied between the two file systems);
  subprocess.Popen(..., stdout=PIPE), which movies use to pipe decoded
  frames into the encoder, runs to a temporary file the next step reads;
- unrpyc: run in this process, as a frozen build does (port.run_unrpyc);
- threads: a thread pool runs its jobs one after another (a page has more
  workers for speed, not threads).

convert(path, out, report) ports one game file with --quality balanced and
returns the game folder; report(kind, data) gets the progress."""

import concurrent.futures
import contextlib
import io
import os
import shutil
import subprocess
import sys

FFMPEG, FFPROBE = "/usr/bin/ffmpeg", "/usr/bin/ffprobe"
ff_exec = None   # set by the worker: (probe, args, stdin bytes or None) -> {rc, stdout, stderr}

_which = shutil.which


def _which_ff(cmd, *a, **k):
    if os.path.basename(str(cmd)) in ("ffmpeg", "ffprobe"):
        return FFPROBE if str(cmd).endswith("ffprobe") else FFMPEG
    return _which(cmd, *a, **k)


class _InOrder:
    """ThreadPoolExecutor's interface, one job at a time."""

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def map(self, fn, *its, **k):
        return map(fn, *its)

    def submit(self, fn, *a, **k):
        f = concurrent.futures.Future()
        try:
            f.set_result(fn(*a, **k))
        except BaseException as e:   # noqa: BLE001 - the future carries it
            f.set_exception(e)
        return f

    def shutdown(self, *a, **k):
        pass


def _is_ff(exe):
    return exe in (FFMPEG, FFPROBE) or os.path.basename(exe) in ("ffmpeg", "ffprobe")


def _ff(args, stdin=None, input=None):
    """(rc, stdout, stderr) of an ffmpeg/ffprobe run. stdin may be a file
    (a pipe from _Popen): then "-i -" reads that file."""
    if stdin is not None and hasattr(stdin, "name"):
        args = [stdin.name if a == "-" and args[i - 1] == "-i" else a for i, a in enumerate(args)]
    if isinstance(input, str):
        input = input.encode()
    r = ff_exec(args[0].endswith("ffprobe"), args[1:], input).to_py()
    return r["rc"], bytes(r["stdout"]), r["stderr"].encode()


_pipes = 0


class _PipeFile(io.FileIO):
    """A finished ffmpeg run's output, read like a pipe; the file goes when
    it is closed (the next ffmpeg reads it by name first)."""

    def __init__(self, path):
        super().__init__(path, "rb")

    def close(self):
        if not self.closed:
            super().close()
            try:
                os.unlink(self.name)
            except OSError:
                pass


class _Popen:
    """Popen for ffmpeg: the run happens at once; with stdout=PIPE, what it
    writes goes to a temporary file, which .stdout reads (and the next
    ffmpeg takes as its input)."""

    def __init__(self, cmd, stdin=None, stdout=None, stderr=None, **k):
        global _pipes
        args = [str(c) for c in cmd]
        if not _is_ff(args[0]):
            return _real_popen.__init__(self, cmd, stdin=stdin, stdout=stdout, stderr=stderr, **k)
        self.args = cmd
        self.stdout = None
        if stdout == subprocess.PIPE and args[-1] in ("-", "pipe:", "pipe:1"):
            _pipes += 1
            path = f"/tmp/ffpipe-{_pipes}"
            args[-1] = path
        self.returncode, out, err = _ff(args, stdin)
        if stdout == subprocess.PIPE:
            self.stdout = _PipeFile(path)
        if stderr is not None and hasattr(stderr, "write"):
            stderr.write(err)

    def wait(self, timeout=None):
        return self.returncode

    def poll(self):
        return self.returncode

    def communicate(self, input=None, timeout=None):
        return (self.stdout.read() if self.stdout else None), None

    def kill(self):
        pass

    terminate = kill


_real_popen = subprocess.Popen


def _run(cmd, *a, input=None, capture_output=False, text=False, check=False, stdout=None, stderr=None,
         stdin=None, **k):
    args = [str(c) for c in cmd] if isinstance(cmd, (list, tuple)) else [str(cmd)]
    exe = args[0] if args else ""
    if _is_ff(exe):
        rc, out, err = _ff(args, stdin, input)
    elif len(args) > 1 and (args[1].endswith("unrpyc.py") or args[1] == "--vn3ds-unrpyc"):
        from vnpack import port
        buf = io.StringIO()
        rc = 0
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                port.run_unrpyc(args[2:])
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 0
        out, err = buf.getvalue().encode(), b""
    else:
        raise FileNotFoundError(f"{exe}: not available in the browser")
    if text:
        out, err = out.decode("utf-8", "replace"), err.decode("utf-8", "replace")
    r = subprocess.CompletedProcess(cmd, rc, out if (capture_output or stdout) else None,
                                    err if (capture_output or stderr) else None)
    if check and rc:
        raise subprocess.CalledProcessError(rc, cmd, r.stdout, r.stderr)
    return r


def install():
    shutil.which = _which_ff
    concurrent.futures.ThreadPoolExecutor = _InOrder
    subprocess.run = _run
    subprocess.Popen = _Popen
    from vnpack import webmovies   # movies through the page's WebCodecs + x264 pool, where it can
    webmovies.install()
    from vnpack import webinput    # the game under /in read with 64-bit positions (games over 2 GB)
    webinput.install("/in")


def convert(path, out, report):
    install()
    from vnpack import flow

    class BrowserUI(flow.UI):
        def phase(self, title):
            report("phase", {"title": title})

        def step(self, id, state, detail="", done=None, total=None, unit=None, label=None):
            report("step", {"id": id, "state": state, "detail": detail, "done": done, "total": total,
                            "unit": unit, "label": label})

        def hint(self, lines):
            report("hint", {"lines": list(lines)})

        def log(self, text):
            report("log", {"text": text})

        def converted(self, summary):
            report("converted", {"summary": str(summary)})

    os.makedirs(out, exist_ok=True)
    opts = flow.Options(inputs=[path], output=out, quality="balanced", sd=None, console=None, ftp=None,
                        detect=False, with_engine=False, work="/tmp/work", keep_work=False, id=None,
                        title=None, rgb565=False, jpeg=None, no_audio=False, no_video=False,
                        video_codec=None, video_kbps=None, fit=False, jobs=1, saves=False)
    for k in ("video_fps", "jpeg_encoder", "jpeg_qscale", "cg_patches", "jpeg_posters", "video_3d"):
        setattr(opts, k, None)
    r = flow.run(opts, BrowserUI())
    game = r.get("out_dir")
    if not game or not os.path.isfile(os.path.join(game, "game.bin")):
        raise RuntimeError("The converter could not make a 3DS version of this game")
    return game


def files_of(game):
    """The files a transfer sends (as tools/vnpack/send.py picks them)."""
    from vnpack import send
    return [(remote, local) for remote, local in send.plan([game])]
