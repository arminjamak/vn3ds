#!/usr/bin/env python3
"""A stand-in for the vn3ds link Worker (worker.js), for tests and for a
link on your own computer. Same endpoints, same behaviour:

  GET /3ds            WebSocket from vn3ds (X-VN3DS-Key, X-VN3DS-Name)
  GET /send?code=...  WebSocket from the page
  GET /near           3DSes behind the caller's address
  GET /fetch?url=...  a download passed on with CORS headers
  GET /<file>         the page and vn3ds-send.js from web/

    python3 server/link/devrelay.py --port 8787
    (and in the vn3ds folder's relay.cfg:  server = <this computer's IP>:8787)

Python 3 standard library only. Test hooks (never in the Worker):
--cut-after N closes the 3DS's link once N bytes went to it (once), and
/stats says how far the sender ran ahead of the 3DS's acks."""

import argparse
import base64
import hashlib
import json
import os
import re
import socket
import struct
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_RE = re.compile(r"^[2-9A-HJ-NP-Z]{8}$")
KEY_RE = re.compile(r"^[0-9a-f]{32}$")
GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def device_code(key):
    d = hashlib.sha256(b"vn3ds-relay-code:" + key.encode()).digest()
    bits = int.from_bytes(d[:5], "big")
    return "".join(CODE_ALPHABET[(bits >> (35 - 5 * i)) & 31] for i in range(8))


class WS:
    """One WebSocket (server side): messages in, messages out."""

    def __init__(self, sock):
        self.sock = sock
        self.wlock = threading.Lock()
        self.closed = False

    def _exact(self, n):
        b = b""
        while len(b) < n:
            c = self.sock.recv(n - len(b))
            if not c:
                raise ConnectionError("closed")
            b += c
        return b

    def recv(self):
        """(opcode, payload) of the next whole message."""
        op, data = None, b""
        while True:
            h = self._exact(2)
            fin, o, masked, n = h[0] & 0x80, h[0] & 0x0F, h[1] & 0x80, h[1] & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._exact(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._exact(8))[0]
            mask = self._exact(4) if masked else None
            p = self._exact(n)
            if mask:
                p = bytes(b ^ mask[i & 3] for i, b in enumerate(p)) if any(mask) else p
            if o >= 8:   # control frames may come between fragments
                if o == 9:
                    self.send(p, 10)
                    continue
                if o == 10:
                    continue
                return o, p
            if o:
                op = o
            data += p
            if fin:
                return op, data

    def send(self, payload, op=None):
        if isinstance(payload, str):
            payload, op = payload.encode(), op or 1
        op = op or 2
        n = len(payload)
        h = bytes([0x80 | op])
        if n < 126:
            h += bytes([n])
        elif n < 65536:
            h += bytes([126]) + struct.pack(">H", n)
        else:
            h += bytes([127]) + struct.pack(">Q", n)
        with self.wlock:
            self.sock.sendall(h + payload)

    def close(self, code=1000, reason=""):
        if self.closed:
            return
        self.closed = True
        try:
            self.send(struct.pack(">H", code) + reason.encode()[:100], 8)
        except OSError:
            pass
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


class Hub:
    def __init__(self, cut_after=0, release=None):
        self.release = release   # a folder standing in for the newest GitHub release
        self.lock = threading.Lock()
        self.links = {}      # code -> {"3ds": WS, "web": WS, "name": str}
        self.rooms = {}      # ip -> {code: {code, name, online}}
        self.cut_after = cut_after
        self.stats = {"max_ahead": 0, "acks": 0, "to_3ds": 0, "links": 0, "cuts": 0}

    def link(self, code):
        return self.links.setdefault(code, {"3ds": None, "web": None, "name": "", "sent": 0, "acked": 0})

    def tell_web(self, code):
        L = self.links.get(code)
        if L and L["web"]:
            try:
                L["web"].send(json.dumps({"t": "state", "online": bool(L["3ds"]), "name": L["name"]}))
            except OSError:
                pass

    def serve(self, ws, role, code, name="", ip=""):
        with self.lock:
            L = self.link(code)
            old = L[role]
            L[role] = ws
            if role == "3ds":
                L["name"] = name
                L["sent"] = L["acked"] = 0
                self.rooms.setdefault(ip, {})[code] = {"code": code, "name": name, "online": True}
                self.stats["links"] += 1
        if old:
            old.close(4000, "replaced by a newer connection")
        self.tell_web(code)
        try:
            while True:
                op, data = ws.recv()
                if op == 8:
                    break
                with self.lock:
                    L = self.link(code)
                    other = L["web" if role == "3ds" else "3ds"]
                if role == "3ds" and op == 1 and data == b"ping":
                    ws.send("pong")
                    continue
                if role == "web" and op == 1:
                    try:
                        if json.loads(data).get("t") == "end" and L["3ds"]:
                            L["3ds"].close(1000, "transfer over")
                    except ValueError:
                        pass
                    continue
                if role == "3ds" and op == 1 and data.startswith(b"ack "):
                    L["acked"] = int(data[4:])
                    self.stats["acks"] += 1
                if other is None:
                    if role == "web":
                        ws.send(json.dumps({"t": "state", "online": False, "name": ""}))
                    continue
                try:
                    other.send(data, op)
                except OSError:
                    continue
                if role == "web" and op == 2:
                    L["sent"] += len(data)
                    self.stats["to_3ds"] += len(data)
                    self.stats["max_ahead"] = max(self.stats["max_ahead"], L["sent"] - L["acked"])
                    if self.cut_after and self.stats["to_3ds"] >= self.cut_after:
                        self.cut_after = 0
                        self.stats["cuts"] += 1
                        other.close(1001, "test: link cut")
        except (ConnectionError, OSError):
            pass
        finally:
            ws.close()
            with self.lock:
                L = self.link(code)
                mine = L[role] is ws
                if mine:
                    L[role] = None
                if role == "3ds" and mine:
                    room = self.rooms.get(ip, {})
                    if code in room:
                        room[code]["online"] = False
                peer = L["3ds"] if role == "web" and mine else None
            if role == "3ds" and mine:
                self.tell_web(code)
            if peer:
                peer.close(1000, "sender left")


def release_text(folder):
    """/latest from a folder holding tag.txt, vn3ds.3dsx and vn3ds.cia."""
    with open(os.path.join(folder, "tag.txt")) as f:
        lines = ["vn3ds-latest 1", f.read().strip()]
    for kind in ("3dsx", "cia"):
        p = os.path.join(folder, "vn3ds." + kind)
        if os.path.isfile(p):
            with open(p, "rb") as f:
                lines.append(f"{kind} {os.path.getsize(p)} {hashlib.sha256(f.read()).hexdigest()}")
    return "\n".join(lines) + "\n"


def make_handler(hub):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *a):
            pass

        def cors(self):
            o = self.headers.get("Origin")
            if o:
                self.send_header("Access-Control-Allow-Origin", o)
                self.send_header("Access-Control-Expose-Headers", "Content-Length, X-File-Name")

        def reply(self, status, body, ctype="application/json"):
            if not isinstance(body, bytes):
                body = json.dumps(body).encode()
            self.send_response(status)
            self.cors()
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def upgrade(self):
            key = self.headers.get("Sec-WebSocket-Key", "")
            acc = base64.b64encode(hashlib.sha1(key.encode() + GUID).digest()).decode()
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.send_header("Sec-WebSocket-Accept", acc)
            self.end_headers()
            self.wfile.flush()
            self.close_connection = True
            return WS(self.connection)

        def do_OPTIONS(self):
            self.send_response(204)
            self.cors()
            self.send_header("Access-Control-Allow-Methods", "GET")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            u = urllib.parse.urlsplit(self.path)
            q = urllib.parse.parse_qs(u.query)
            ws_wanted = self.headers.get("Upgrade", "").lower() == "websocket"
            ip = self.client_address[0]
            if u.path == "/3ds":
                key = self.headers.get("X-VN3DS-Key", "")
                if not ws_wanted:
                    return self.reply(426, b"WebSocket only\n", "text/plain")
                if not KEY_RE.match(key):
                    return self.reply(400, b"bad key\n", "text/plain")
                name = re.sub(r"[^A-Za-z0-9 ]", "", self.headers.get("X-VN3DS-Name", "3DS"))[:20] or "3DS"
                return hub.serve(self.upgrade(), "3ds", device_code(key), name, ip)
            if u.path == "/send":
                code = re.sub(r"[\s-]", "", q.get("code", [""])[0]).upper()
                if not CODE_RE.match(code):
                    return self.reply(404, {"error": "That code doesn't look right"})
                if not ws_wanted:
                    return self.reply(426, {"error": "WebSocket only"})
                return hub.serve(self.upgrade(), "web", code)
            if u.path == "/near":
                with hub.lock:
                    return self.reply(200, list(hub.rooms.get(ip, {}).values()))
            if u.path == "/stats":
                return self.reply(200, hub.stats)
            if u.path == "/fetch":
                return self.fetch_url(q.get("url", [""])[0])
            if u.path == "/latest" and hub.release:
                return self.reply(200, release_text(hub.release).encode(), "text/plain")
            if u.path in ("/vn3ds.3dsx", "/vn3ds.cia") and hub.release:
                return self.release_file(os.path.join(hub.release, u.path[1:]))
            name = "index.html" if u.path in ("/", "") else u.path.lstrip("/")
            full = os.path.normpath(os.path.join(WEB, name))
            if full.startswith(WEB + os.sep) and os.path.isfile(full):
                ctype = {".js": "text/javascript", ".zip": "application/zip"}.get(
                    os.path.splitext(full)[1], "text/html; charset=utf-8")
                with open(full, "rb") as f:
                    return self.reply(200, f.read(), ctype)
            self.reply(404, {"error": "Not found"})

        def release_file(self, path):
            if not os.path.isfile(path):
                return self.reply(404, b"not in the newest release\n", "text/plain")
            size = os.path.getsize(path)
            m = re.match(r"bytes=(\d+)-$", self.headers.get("Range", ""))
            start = int(m.group(1)) if m and int(m.group(1)) < size else 0
            self.send_response(206 if start else 200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(size - start))
            if start:
                self.send_header("Content-Range", f"bytes {start}-{size - 1}/{size}")
            self.end_headers()
            with open(path, "rb") as f:
                f.seek(start)
                self.wfile.write(f.read())

        def fetch_url(self, url):
            try:
                r = urllib.request.urlopen(url, timeout=60)
            except Exception as e:   # noqa: BLE001 - told to the page
                return self.reply(502, {"error": str(e)})
            name = os.path.basename(urllib.parse.urlsplit(r.url).path) or "game.zip"
            self.send_response(200)
            self.cors()
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("X-File-Name", urllib.parse.quote(name))
            if r.headers.get("Content-Length"):
                self.send_header("Content-Length", r.headers["Content-Length"])
            else:
                self.close_connection = True
            self.end_headers()
            while True:
                c = r.read(1 << 20)
                if not c:
                    break
                self.wfile.write(c)

    return H


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--cut-after", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--release", help="a folder with tag.txt, vn3ds.3dsx, vn3ds.cia: the newest release")
    a = ap.parse_args(argv)
    srv = ThreadingHTTPServer((a.host, a.port), make_handler(Hub(a.cut_after, a.release)))
    srv.daemon_threads = True
    print(f"vn3ds link (local) on :{a.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
