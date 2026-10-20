"""The whole trip, shared by `vn3ds-port` and the vn3ds app: convert a Ren'Py
game, pick where it goes and get it there together with vn3ds itself.

    flow.run(flow.Options(inputs=["path/to/game"]), flow.ConsoleUI())

Where it goes, unless the options say:
  - a 3DS SD card plugged into this computer: best quality ("sd"), copied
    there with vn3ds.3dsx (copied only when it is missing or different);
  - otherwise Wi-Fi, compact quality ("wifi"). After converting it looks for
    the 3DS: vn3ds's receiver (Y in vn3ds), or the Homebrew Launcher's
    netloader (Y in the launcher), which first gets vn3ds itself and starts
    it; then the game (and vn3ds.3dsx, so it is saved to the card or
    updated) is streamed to vn3ds. Nothing times out: it waits for the 3DS
    and retries dropped connections until the transfer is complete, and
    only files the 3DS doesn't already have are sent.

The UI object gets the progress as steps (see UI below); ConsoleUI prints
them as numbered steps for the terminal.
"""

import os
import shutil
import sys
import time
from dataclasses import dataclass, field

from . import detect, send

STEPS = {
    "unpack": "Unpacking",
    "decompile": "Decompiling scripts",
    "scripts": "Reading the scripts",
    "audio": "Audio",
    "music": "Music tempo",
    "images": "Images",
    "video": "Video",
    "pack": "Packing",
    "target": "Finding your 3DS",
    "engine": "vn3ds",
    "game": "Your game",
}
CONVERT_STEPS = ("unpack", "decompile", "scripts", "audio", "music", "images", "video", "pack")

HINT_NETLOADER = [
    "1. On the 3DS, open the Homebrew Launcher.",
    "2. Press Y.",
]
HINT_OR_VN3DS = "Already have vn3ds? Open it and press Y instead."
HINT_OR_SD = "Or put the 3DS's SD card into this computer."


class Cancelled(send.Cancelled):
    pass


class FlowError(SystemExit):
    """A problem to tell the user about (exits with the message on the
    command line; the app shows it)."""


class UI:
    """What the flow reports. Every method may be left as it is."""

    def phase(self, title):
        """A new numbered part of the trip begins ("Converting", ...)."""

    def step(self, id, state, detail="", done=None, total=None, unit=None, label=None):
        """A step (ids in STEPS) is "active", "done", "skip" or "fail".
        done/total count files, or bytes when unit == "bytes"."""

    def hint(self, lines):
        """Instructions to show while waiting for the user ([] clears)."""

    def log(self, text):
        """A line worth keeping (warnings, the conversion report)."""

    def stopped(self):
        """Return True to cancel (raises Cancelled inside the flow)."""
        return False

    def target(self, kind, where):
        """Where the game is going: "sd", "wifi", "ftp" or None (build only)."""

    def converted(self, summary):
        """The game is converted (summary["out_dir"] holds it)."""


@dataclass
class Options:
    inputs: list = field(default_factory=list)
    output: str = "build"
    quality: str = "auto"          # auto / sd / wifi
    sd: str = None                 # SD card (or emulator sdmc) root
    console: str = None            # the 3DS's IP address
    ftp: str = None                # IP[:PORT] of ftpd
    detect: bool = True            # look for a card / the 3DS when none is given
    engine: str = None             # vn3ds.3dsx to install (default: the bundled one)
    with_engine: bool = True       # deliver vn3ds too (skipped when the 3DS already has it)
    work: str = None
    keep_work: bool = False
    id: str = None
    title: str = None
    rgb565: bool = False
    jpeg: int = None
    no_audio: bool = False
    no_video: bool = False
    video_codec: str = None
    video_kbps: int = None
    fit: bool = False
    jobs: int = 0


def _check(ui):
    if ui.stopped():
        raise Cancelled()


def mb(n):
    return f"{n / 1e6:.1f} MB"


def duration(seconds):
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds} s"
    if seconds < 3600:
        return f"{seconds // 60} min"
    return f"{seconds // 3600} h {seconds % 3600 // 60:02d} min"


# --------------------------------------------------------------------------
# The SD card
# --------------------------------------------------------------------------

def _same_file(src, dst, hashed):
    try:
        a, b = os.stat(src), os.stat(dst)
    except OSError:
        return False
    if a.st_size != b.st_size:
        return False
    # Packed files are named by their contents; the few others (game.bin,
    # the report) are small enough to compare.
    return hashed or _files_identical(src, dst)


def _files_identical(a, b):
    try:
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        with open(a, "rb") as fa, open(b, "rb") as fb:
            while True:
                x, y = fa.read(1 << 20), fb.read(1 << 20)
                if x != y:
                    return False
                if not x:
                    return True
    except OSError:
        return False


def _copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".part"
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def install_engine_sd(sd, engine):
    """Copies vn3ds.3dsx to sdmc:/3ds/ when it is missing or different.
    Returns "installed", "updated" or "up to date"."""
    dest = os.path.join(sd, "3ds", "vn3ds.3dsx")
    if _files_identical(engine, dest):
        return "up to date"
    existed = os.path.exists(dest)
    _copy(engine, dest)
    return "updated" if existed else "installed"


def install_game_sd(out_dir, game_id, sd, report=None, stop=None):
    """Brings sdmc:/3ds/vn3ds/games/<id>/ in line with out_dir: copies what
    is new or changed (game.bin last, so a half-copied game is never seen
    as complete) and removes what the new version no longer has. Returns
    (copied files, bytes copied, unchanged files)."""
    dest = os.path.join(sd, "3ds", "vn3ds", "games", game_id)
    files, dirs_ = [], set()
    for root, _, names in os.walk(out_dir):
        rel_root = os.path.relpath(root, out_dir)
        dirs_.add(os.path.normcase(os.path.normpath(os.path.join(dest, rel_root))))
        os.makedirs(os.path.join(dest, rel_root), exist_ok=True)
        for n in sorted(names):
            if n.endswith(".part"):
                continue
            full = os.path.join(root, n)
            files.append((os.path.relpath(full, out_dir), full))
    files.sort(key=lambda f: f[0] == "game.bin")
    todo = [(rel, full) for rel, full in files
            if not _same_file(full, os.path.join(dest, rel), "/" in rel.replace(os.sep, "/"))]
    total = sum(os.path.getsize(full) for _, full in todo)
    done = 0
    for k, (rel, full) in enumerate(todo):
        if stop and stop():
            raise Cancelled()
        _copy(full, os.path.join(dest, rel))
        done += os.path.getsize(full)
        if report:
            report(k + 1, len(todo), done, total)
    keep = {os.path.normcase(os.path.join(dest, rel)) for rel, _ in files}
    for root, dirs, names in os.walk(dest, topdown=False):
        for n in names:
            p = os.path.join(root, n)
            if os.path.normcase(p) not in keep:
                os.remove(p)
        for d in dirs:
            p = os.path.join(root, d)
            if os.path.normcase(os.path.normpath(p)) in dirs_:
                continue
            try:
                os.rmdir(p)   # only if empty
            except OSError:
                pass
    return len(todo), total, len(files) - len(todo)


def deliver_sd(game_dirs, sd, engine, ui):
    ui.target("sd", sd)
    ui.phase(f"Copying to the SD card ({sd})")
    if engine:
        ui.step("engine", "active", "", label="vn3ds")
        how = install_engine_sd(sd, engine)
        ui.step("engine", "done", f"vn3ds.3dsx {how}", label="vn3ds")
    for gd in game_dirs:
        gid = os.path.basename(gd.rstrip("/\\"))
        ui.step("game", "active", "", label="Your game")

        def report(n, count, done, total):
            ui.step("game", "active", f"{mb(done)} of {mb(total)}", done=done, total=total,
                    unit="bytes", label="Your game")
            _check(ui)
        copied, nbytes, same = install_game_sd(gd, gid, sd, report, ui.stopped)
        detail = (f"{copied} files copied ({mb(nbytes)})" if copied else "already on the card")
        if copied and same:
            detail += f", {same} unchanged"
        ui.step("game", "done", detail + f"  ->  sdmc:/3ds/vn3ds/games/{gid}/", label="Your game")
    ui.hint([])


# --------------------------------------------------------------------------
# Wi-Fi
# --------------------------------------------------------------------------

def find_3ds(opts, ui, allow_sd=True):
    """Waits until the 3DS shows up. Returns (kind, where): "vn3ds" with an
    IP, "netloader" with an IP, "ftp" with IP:PORT, or "sd" with a card."""
    ui.phase("Finding your 3DS")
    where = f" at {opts.console}" if opts.console else " on the Wi-Fi"
    ui.step("target", "active", "looking" + where)
    hinted = False
    while True:
        _check(ui)
        if opts.console:
            ip = opts.console
            if detect.listening(ip, send.VN3DS_PORT):
                return "vn3ds", ip
            if detect.ping_netloader(ip):
                return "netloader", ip
        else:
            if allow_sd:
                cards = detect.find_sd()
                if cards:
                    return "sd", cards[0]
            lan = detect.scan_lan()
            if lan.get(detect.VN3DS_PORT):
                return "vn3ds", lan[detect.VN3DS_PORT][0]
            ip = detect.find_netloader()
            if ip:
                return "netloader", ip
            if lan.get(detect.FTPD_PORT):
                return "ftp", f"{lan[detect.FTPD_PORT][0]}:{detect.FTPD_PORT}"
        if not hinted:
            lines = HINT_NETLOADER + [HINT_OR_VN3DS]
            if allow_sd and not opts.console:
                lines.append(HINT_OR_SD)
            ui.hint(lines)
            ui.step("target", "active", "waiting for your 3DS" + where)
            hinted = True
        send._sleep(2, ui.stopped)


def _send_engine_netloader(ip, engine, ui):
    """vn3ds through the Homebrew Launcher's netloader, until it works."""
    ui.phase("Sending vn3ds")
    ui.step("engine", "active", "sending to the Homebrew Launcher", label="vn3ds")
    while True:
        _check(ui)

        def report(done, total):
            ui.step("engine", "active", f"{mb(done)} of {mb(total)}", done=done, total=total,
                    unit="bytes", label="vn3ds")
        try:
            send.send_3dslink(ip, engine, argv0="3dslink:/vn3ds.3dsx", name="vn3ds.3dsx",
                              report=report)
            ui.step("engine", "done", "vn3ds sent and started", label="vn3ds")
            return
        except send.NetloaderError as e:
            raise FlowError(f"The Homebrew Launcher could not take vn3ds: {e}")
        except OSError as e:
            ui.step("engine", "active", f"trying again ({e.__class__.__name__}); keep the "
                    "Homebrew Launcher's netloader open (Y)", label="vn3ds")
            ui.hint(HINT_NETLOADER)
            send._sleep(3, ui.stopped)
            while not detect.ping_netloader(ip):
                send._sleep(2, ui.stopped)
            ui.hint([])


def deliver_wifi(game_dirs, ip, kind, engine, ui):
    ui.target("wifi", ip)
    if kind == "netloader":
        _send_engine_netloader(ip, engine, ui)
    elif engine:
        ui.step("engine", "done", "vn3ds is open and listening (updated with the game if needed)",
                label="vn3ds")
    files = send.plan(game_dirs, engine)
    if not files:
        return
    label = "Your game" if game_dirs else "vn3ds.3dsx"
    ui.phase("Sending your game" if game_dirs else "Saving vn3ds to the SD card")
    if not detect.listening(ip, send.VN3DS_PORT):
        ui.step("game", "active", "waiting for vn3ds to open its receiver", label=label)
        t0 = time.time()
        hinted = False
        while not send.wait_for_receiver(ip, seconds=5, stop=ui.stopped):
            if not hinted and time.time() - t0 > 20:
                ui.hint(["vn3ds should open on its own. If it doesn't, open vn3ds and press Y."])
                hinted = True
        ui.hint([])
    t_total = sum(os.path.getsize(p) for _, p in files)

    def report(event, **info):
        if event == "checking":
            ui.step("game", "active", f"checking {info['files']} files ({mb(t_total)})", label=label)
        elif event == "skipped":
            ui.log(f"{info['skipped']} files are already on the 3DS; sending {info['need']}")
        elif event == "bytes":
            rate = info["rate"]
            detail = f"{mb(info['done'])} of {mb(info['total'])}"
            if rate > 0:
                detail += f"  ·  {rate / 1e6:.2f} MB/s  ·  {duration(info['left'])} left"
            ui.step("game", "active", detail, done=info["done"], total=info["total"],
                    unit="bytes", label=label)
        elif event in ("retry", "waiting"):
            ui.step("game", "active", info["text"], label=label)
            ui.log(info["text"])
        elif event == "info":
            ui.log(info["text"])
    info = {}
    sent, refused = send.send_vn3ds(ip, files, forever=True, report=report, stop=ui.stopped,
                                    info=info)
    need = info.get("need")
    n_needed = len(need) if need is not None else sent
    engine_sent = engine and need is not None and (len(files) - 1) in need
    if need is not None and not need:
        detail = "already on the 3DS: nothing to send"
    else:
        detail = f"{n_needed} of {len(files)} files sent"
        wire, unpacked = info.get("wire"), info.get("unpacked")
        if wire is not None and unpacked:
            detail += f": {mb(wire)}" + (f" ({mb(unpacked)} unpacked)" if wire < unpacked else "")
        if refused:
            detail += f", {refused} refused"
    ui.step("game", "fail" if refused else "done", detail, label=label)
    if engine_sent:
        ui.log("vn3ds.3dsx was saved on the SD card" + (
            "" if kind == "netloader" else "; restart vn3ds to use the new version"))
    if refused:
        raise FlowError(f"The 3DS could not write {refused} files (is the SD card full?)")


def deliver_ftp(game_dirs, where, engine, ui):
    ui.target("ftp", where)
    files = send.plan(game_dirs, engine)
    ui.phase(f"Uploading over FTP to {where}")

    def report(done, total):
        ui.step("game", "active", f"{mb(done)} of {mb(total)}", done=done, total=total,
                unit="bytes", label="Your game")
    send.send_ftp(where, files, report=report, stop=ui.stopped)
    ui.step("game", "done", f"{len(files)} files uploaded. Start vn3ds from the Homebrew Launcher.",
            label="Your game")


# --------------------------------------------------------------------------
# Everything
# --------------------------------------------------------------------------

def plan_target(opts):
    """Where the game goes and the quality that suits it, before converting:
    (kind, where, quality). kind "wifi" with where None means: find the
    3DS on the network after converting."""
    if opts.sd:
        kind, where = "sd", opts.sd
    elif opts.console:
        kind, where = "wifi", opts.console
    elif opts.ftp:
        kind, where = "ftp", opts.ftp
    elif opts.detect:
        cards = detect.find_sd()
        kind, where = ("sd", cards[0]) if cards else ("wifi", None)
    else:
        kind, where = None, None
    quality = opts.quality
    if quality == "auto":
        quality = "wifi" if kind in ("wifi", "ftp") else "sd"
    return kind, where, quality


def run(opts, ui=None):
    """Convert (if there are inputs) and deliver. Returns a dict with title,
    id, out_dir, quality, target and where."""
    from . import port
    ui = ui or UI()
    engine = None
    if opts.with_engine:
        engine = opts.engine or port.ENGINE_3DSX
        if not os.path.exists(engine):
            if not opts.inputs:
                raise FlowError(f"vn3ds-port: {engine} isn't built yet (run make in engine/)")
            ui.log(f"{engine} isn't built yet (run make in engine/); sending the game alone")
            engine = None
    kind, where, quality = plan_target(opts)
    result = dict(quality=quality, target=kind, where=where, title=None, id=None, out_dir=None)

    game_dirs = []
    if opts.inputs:
        ported = [os.path.abspath(i) for i in opts.inputs
                  if os.path.isfile(os.path.join(i, "game.bin"))]
        if ported and len(ported) == len(opts.inputs):
            game_dirs = ported      # already-ported games: just deliver them
            for d in ported:
                ui.converted(dict(out_dir=d, id=os.path.basename(d.rstrip("/\\")), title=None))
        else:
            what = {"sd": "best quality, for the SD card", "wifi": "compact, for Wi-Fi"}[quality]
            ui.phase(f"Converting ({what})")
            if kind == "wifi" and not where:
                ui.hint(["While this converts, get your 3DS ready:"] + HINT_NETLOADER +
                        [HINT_OR_VN3DS])
            summary = port.convert(opts, quality, ui)
            game_dirs = [summary["out_dir"]]
            result.update(title=summary["title"], id=summary["id"], out_dir=summary["out_dir"])
            ui.converted(summary)
    elif not engine:
        raise FlowError("vn3ds-port: give a game to port")

    if kind is None:
        ui.hint([])
        ui.target(None, None)
        if game_dirs:
            ui.log(f"Built {game_dirs[0]}  ->  copy it to sdmc:/3ds/vn3ds/games/")
        return result
    if kind == "sd":
        deliver_sd(game_dirs, where, engine, ui)
    elif kind == "ftp":
        deliver_ftp(game_dirs, where, engine, ui)
    else:
        found, at = find_3ds(opts, ui, allow_sd=not opts.console and opts.detect)
        names = {"vn3ds": "vn3ds", "netloader": "the Homebrew Launcher", "ftp": "ftpd",
                 "sd": "the SD card"}
        ui.hint([])
        if found == "sd":
            ui.step("target", "done", f"found the 3DS's SD card at {at}")
            deliver_sd(game_dirs, at, engine, ui)
        else:
            ui.step("target", "done", f"found your 3DS at {at.split(':')[0]} ({names[found]})")
            if found == "ftp":
                deliver_ftp(game_dirs, at, engine, ui)
            else:
                deliver_wifi(game_dirs, at, found, engine, ui)
        kind, where = ("sd" if found == "sd" else "ftp" if found == "ftp" else "wifi"), at
    result.update(target=kind, where=where)
    return result


# --------------------------------------------------------------------------
# The terminal
# --------------------------------------------------------------------------

class ConsoleUI(UI):
    """Numbered steps on the terminal, with a live progress line."""

    def __init__(self, stream=None):
        self.out = stream or sys.stdout
        self.tty = self.out.isatty()
        self.n = 0
        self.last_line = 0.0
        self.live = False
        self.shown_hint = None
        self.last_detail = {}
        self.ok = "✓" if _can_print(self.out, "✓") else "+"

    def _end_live(self):
        if self.live:   # the next line takes the progress line's place
            # (blanks, not an escape code: older Windows consoles print those)
            self.out.write("\r" + " " * 112 + "\r")
            self.live = False

    def _print(self, text):
        self._end_live()
        try:
            self.out.write(text + "\n")
        except UnicodeEncodeError:   # e.g. a Windows console that can't show a title
            enc = getattr(self.out, "encoding", None) or "ascii"
            self.out.write(text.encode(enc, "replace").decode(enc) + "\n")
        self.out.flush()

    def phase(self, title):
        self.n += 1
        self._print(f"{self.n}. {title}")

    def step(self, id, state, detail="", done=None, total=None, unit=None, label=None):
        name = label or STEPS.get(id, id)
        if state == "skip":
            return
        if state in ("done", "fail"):
            mark = self.ok if state == "done" else "!"
            count = f"{done}/{total}" if (done is not None and unit != "bytes" and total) else ""
            text = "  ".join(t for t in (count, detail) if t)
            self._print(f"   {mark} {name:<20} {text}".rstrip())
            self.last_detail.pop(id, None)
            return
        # active
        if done is not None and total:
            if unit == "bytes":
                line = f"     {detail}"
            else:
                line = f"     {name} {done}/{total}" + (f"  {detail}" if detail else "")
            now = time.time()
            if self.tty:
                if now - self.last_line > 0.2 or done == total:
                    self.last_line = now
                    self.out.write("\r" + line[:110].ljust(80))
                    self.out.flush()
                    self.live = True
            elif done and now - self.last_line > 15:
                self.last_line = now
                self._print(line)
            return
        if detail and self.last_detail.get(id) != detail:
            self.last_detail[id] = detail
            self._print(f"     {detail}")

    def hint(self, lines):
        if lines and lines != self.shown_hint:
            for l in lines:
                self._print(f"   {l}")
        self.shown_hint = lines or None

    def log(self, text):
        self._print("   " + text.replace("\n", "\n   "))


def _can_print(stream, ch):
    try:
        ch.encode(getattr(stream, "encoding", None) or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False
