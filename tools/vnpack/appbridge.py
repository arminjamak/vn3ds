"""The Mac app's link to the converter: commands that report as JSON lines.

    python3 -m vnpack.appbridge setup  --route wifi|sd [--cia vn3ds.cia] [--port 8380]
    python3 -m vnpack.appbridge port   --quality balanced|wifi|sd [--3d] -o OUT GAME [MORE INPUTS...]
    python3 -m vnpack.appbridge send   (--wifi IP | --sd PATH) GAME_DIR [MORE GAME DIRS...]
    python3 -m vnpack.appbridge export-apps --dest FOLDER GAMES_FOLDER_OR_GAME [...]
    python3 -m vnpack.appbridge library                  (Ren'Py games installed here)
    python3 -m vnpack.appbridge sync [--wifi IP | --sd PATH]   (saves, once)
    python3 -m vnpack.appbridge sync-agent [--port 5556] (saves, in the background: login item)

(The standalone build runs them as `vn3ds-port --vn3ds-bridge ...`.)

Every line on stdout is one JSON object with an "event":
  phase {title}                     a part of the trip begins
  step {id, state, detail, done, total, unit, label}   as flow.UI.step
  hint {lines}  log {text}  target {kind, where}
  cia {url}                         setup: FBI can install vn3ds.cia from url
  cia_fetched {ip}                  setup: a 3DS is downloading it
  netloader {ip}                    setup: the Homebrew Launcher is waiting
  ready {via, ip | sd}              setup: vn3ds is on the 3DS (or the card)
  converted {out_dir, id, title}    port: the game is ready to send
  done {}                           send: it is on the 3DS
  exported {apps: [[id, path, bytes]], dest}   export-apps: every game as <id>.3dsx
  saves {sent, kept_back: [[slot, why]], summary}   send: the Ren'Py saves that went along
  game {path, title, version, size, saves, where}   library: one installed game
  cover {path, cover}               library: its cover art (a PNG), found after the list
  library_done {count}
  synced {games: {id: {summary, to_3ds, to_mac, deleted, kept_back}}, host}   sync
  error {message}                   then exit status 1
The app stops a command by terminating the process.

setup is the first time only: it gets vn3ds onto the 3DS before any game
is sent. Over Wi-Fi it offers both ways at once and takes whichever the
player picks: the Homebrew Launcher's netloader (Y), which gets vn3ds.3dsx
and starts it, or FBI's "Remote Install" QR code for vn3ds.cia, served from
this computer; FBI installs it as a HOME menu app, and once it is opened it
listens for games. On the SD card route it copies vn3ds.3dsx to the card.
"""

import argparse
import http.server
import json
import os
import socketserver
import sys
import threading

from . import detect, flow, port, send


def emit(event, **data):
    data["event"] = event
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()


class JsonUI(flow.UI):
    last = {}

    def phase(self, title):
        emit("phase", title=title)

    def step(self, id, state, detail="", done=None, total=None, unit=None, label=None):
        import time
        now = time.monotonic()
        if state == "active" and done is not None and done != total and \
                now - self.last.get(id, 0) < 0.1:
            return   # progress at most 10 times a second
        self.last[id] = now
        emit("step", id=id, state=state, detail=detail, done=done, total=total, unit=unit,
             label=label or flow.STEPS.get(id, id))

    def hint(self, lines):
        emit("hint", lines=list(lines))

    def log(self, text):
        emit("log", text=text)

    def target(self, kind, where):
        emit("target", kind=kind, where=where)

    def saves(self, result):
        emit("saves", sent=result["sent"], kept_back=[list(k) for k in result["kept_back"]],
             summary=result.get("summary"))


# --------------------------------------------------------------------------
# setup: vn3ds onto the 3DS
# --------------------------------------------------------------------------

def serve_cia(path, port):
    """Serves the CIA at http://<this computer>:<port>/vn3ds.cia in the
    background (FBI: Remote Install > Scan QR Code). Returns the URL."""
    data = open(path, "rb").read()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] != "/vn3ds.cia":
                self.send_error(404)
                return
            emit("cia_fetched", ip=self.client_address[0])
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_HEAD = do_GET

        def log_message(self, *a):
            pass

    class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    for p in range(port, port + 20):   # the first free port from `port`
        try:
            srv = Server(("0.0.0.0", p), Handler)
            break
        except OSError:
            continue
    else:
        raise flow.FlowError(f"no free port for the FBI download from {port}")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    ip = detect.local_ipv4() or "127.0.0.1"
    return f"http://{ip}:{srv.server_address[1]}/vn3ds.cia"


def setup_wifi(cia, http_port, engine):
    ui = JsonUI()
    if cia and os.path.exists(cia):
        emit("cia", url=serve_cia(cia, http_port))
    netloader_tried = None
    while True:
        lan = detect.scan_lan(ports=(send.VN3DS_PORT,))
        if lan.get(send.VN3DS_PORT):
            emit("ready", via="vn3ds", ip=lan[send.VN3DS_PORT][0])
            return
        ip = detect.find_netloader()
        if ip and ip != netloader_tried:
            netloader_tried = ip
            emit("netloader", ip=ip)
            flow._send_engine_netloader(ip, engine, ui)
            ui.step("engine", "active", "waiting for vn3ds to start", label="vn3ds")
            if send.wait_for_receiver(ip, seconds=60):
                emit("ready", via="netloader", ip=ip)
                return
        send._sleep(2)


def setup_sd(engine):
    ui = JsonUI()
    shown = False
    while True:
        cards = detect.find_sd()
        if cards:
            ui.step("engine", "active", f"copying vn3ds to {cards[0]}", label="vn3ds")
            how = flow.install_engine_sd(cards[0], engine)
            ui.step("engine", "done", f"vn3ds.3dsx {how}", label="vn3ds")
            emit("ready", via="sd", sd=cards[0])
            return
        if not shown:
            ui.hint(["Put the 3DS's SD card into this Mac."])
            shown = True
        send._sleep(1)


# --------------------------------------------------------------------------
# port and send
# --------------------------------------------------------------------------

def get_depth_model(ui):
    """--3d: stereoscopic movies and scenes need the depth model (99 MB,
    fetched once, as the command line's --3d does) and onnxruntime to run
    it. Reports the download as a "depth" step with a percentage. Returns
    whether the game can be made in 3D; without the model (offline) or the
    runtime it stays 2D, and the step says so."""
    from . import stereo
    label = "3D"
    if not stereo.find_model():
        what = "getting the depth model (99 MB, once)"
        ui.step("depth", "active", what, done=0, total=100, label=label)

        def say(m):   # download_model says "  10%", "  20%", ...
            m = m.strip()
            if m.endswith("%") and m[:-1].isdigit():
                ui.step("depth", "active", what, done=int(m[:-1]), total=100, label=label)
        try:
            stereo.download_model(say=say)
        except OSError as e:
            ui.step("depth", "done", f"stays 2D: {e}", label=label)
            return False
    if not stereo.runtime_python(stereo.find_model()):
        ui.step("depth", "done", "stays 2D: this converter can't run the depth model "
                "(no onnxruntime)", label=label)
        return False
    ui.step("depth", "done", "depth model ready", label=label)
    return True


# --------------------------------------------------------------------------
# installed games and saves
# --------------------------------------------------------------------------

def library_cmd():
    from . import library, savesync
    games = library.find(say=lambda g: emit(
        "game", path=g.path, title=g.title, version=g.version, size=g.size, saves=g.saves,
        where=g.where))
    covers = os.path.join(os.path.dirname(savesync.data_dir()), "covers")
    for g in games:
        c = library.cover(g, covers)
        if c:
            emit("cover", path=g.path, cover=c)
    emit("library_done", count=len(games))


def sync_cmd(wifi, sd, games):
    from . import savesync
    for g in games:
        savesync.register(g)
    maps = savesync.game_maps(games)
    if not maps:
        raise flow.FlowError("no games to sync yet: send one to the 3DS first")
    ui = JsonUI()
    if sd:
        link = savesync.FolderLink(os.path.join(sd, "3ds", "vn3ds"))
    else:
        host = wifi or savesync._last_host()
        if not host or not detect.listening(host, send.VN3DS_PORT):
            kind, host = detect.locate(host)
            if kind != "vn3ds":
                raise flow.FlowError("Open vn3ds on the 3DS to sync the saves.")
        link = savesync.WifiLink(host)
    try:
        reports = savesync.sync(link, maps, say=ui.log)
    finally:
        link.close()
    emit("synced", host=getattr(link, "host", None),
         games={g: dict(summary=r.summary(), **r.as_dict()) for g, r in reports.items()})


def options(**kw):
    o = flow.Options(**kw)
    for name in ("video_fps", "jpeg_encoder", "jpeg_qscale", "cg_patches", "jpeg_posters",
                 "video_3d", "three_d"):
        setattr(o, name, None)
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(prog="appbridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup")
    s.add_argument("--route", choices=("wifi", "sd"), required=True)
    s.add_argument("--cia")
    s.add_argument("--port", type=int, default=8380)
    p = sub.add_parser("port")
    p.add_argument("--quality", choices=("balanced", "wifi", "sd"), required=True)
    p.add_argument("--3d", dest="three_d", action=argparse.BooleanOptionalAction, default=False,
                   help="stereoscopic movies and scenes (port.py's --3d)")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("inputs", nargs="+")
    d = sub.add_parser("send")
    d.add_argument("--wifi")
    d.add_argument("--sd")
    d.add_argument("game_dirs", nargs="+", help="ported games (the app adds Snapshot when asked)")
    x = sub.add_parser("export-apps")
    x.add_argument("--dest", required=True)
    x.add_argument("games", nargs="+")
    sub.add_parser("library")
    y = sub.add_parser("sync")
    y.add_argument("--wifi")
    y.add_argument("--sd")
    y.add_argument("games", nargs="*")
    a = sub.add_parser("sync-agent")
    a.add_argument("--port", type=int, default=5556)
    args = ap.parse_args(argv)
    engine = port.ENGINE_3DSX
    try:
        if args.cmd == "setup":
            if not os.path.exists(engine):
                raise flow.FlowError(f"{engine} is missing")
            if args.route == "wifi":
                setup_wifi(args.cia, args.port, engine)
            else:
                setup_sd(engine)
        elif args.cmd == "port":
            o = options(inputs=args.inputs, output=args.output, quality=args.quality,
                        detect=False, with_engine=False)
            ui = JsonUI()
            ui.converted = lambda s: emit("converted", out_dir=s["out_dir"], id=s.get("id"),
                                          title=s.get("title"))
            # off unless asked (port.py's --3d default), never "whenever it can";
            # the model comes first, as the command line's prepare_video_3d()
            o.three_d = args.three_d and get_depth_model(ui)
            o.video_3d = o.three_d   # (what port.py read before --3d)
            flow.run(o, ui)
        elif args.cmd == "library":
            library_cmd()
        elif args.cmd == "sync":
            sync_cmd(args.wifi, args.sd, args.games)
        elif args.cmd == "sync-agent":
            from . import savesync
            savesync.run_agent(args.port, say=lambda t: emit("log", text=t))
        elif args.cmd == "export-apps":
            games = port.ported_games(args.games)
            if not games:
                raise flow.FlowError("no converted games to export yet")
            ui = JsonUI()
            done = port.export_apps(games, args.dest, lambda i, n, gid: ui.step(
                "apps", "active", f"{gid}.3dsx", done=i, total=n, label="Apps"))
            ui.step("apps", "done", f"{len(done)} apps", done=len(done), total=len(done),
                    label="Apps")
            emit("exported", apps=[list(a) for a in done], dest=args.dest)
        else:
            if bool(args.wifi) == bool(args.sd):
                raise flow.FlowError("give --wifi IP or --sd PATH")
            o = options(inputs=args.game_dirs, output=os.path.dirname(args.game_dirs[0]),
                        quality="sd" if args.sd else "wifi", sd=args.sd, console=args.wifi,
                        detect=False, with_engine=True)
            flow.run(o, JsonUI())
            emit("done")
    except SystemExit as e:   # FlowError, PortError
        if e.code not in (0, None):
            emit("error", message=str(e.code))
            sys.exit(1)
    except Exception as e:   # anything else: say it, don't hang the app
        emit("error", message=f"{e.__class__.__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
