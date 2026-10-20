#!/usr/bin/env python3
"""vn3ds online leaderboard: a tiny HTTP server for minigame high scores.

Python 3 standard library only. Scores live in a SQLite file. The API is
plain text so the 3DS can parse it with a few lines of C:

  GET  /v1/top?game=<id>&n=10
       200, one line per entry: rank<TAB>name<TAB>score
       (an empty body means nobody has played yet)

  POST /v1/score   (application/x-www-form-urlencoded)
       game=<id>&name=<name>&score=<0..100>&player=<console id>&nonce=<random>&sig=<hex>
       sig = hex(HMAC-SHA256(key, "game|name|score|nonce"))
       200, "ok<TAB>rank<TAB>total"

  GET  /v1/health  ->  "ok"

Errors are a 4xx/5xx status with the body "error<TAB>message".

Each (game, player, name) keeps its best score; ties are ranked by who got
there first. Ranks are competition ranks: 100, 90, 90, 80 -> 1, 2, 2, 4.

Run it:
  python3 leaderboard.py --port 8080 --db leaderboard.db
Admin:
  python3 leaderboard.py --db leaderboard.db --list [--game quiz]
  python3 leaderboard.py --db leaderboard.db --delete 12 [--delete 13 ...]

The shared key comes from $LEADERBOARD_KEY, or the file named by
$LEADERBOARD_KEY_FILE, or $CREDENTIALS_DIRECTORY/key (systemd), or else the
development default below (which matches the engine's default in
engine/source/leaderboard_config.h).
"""

import argparse
import hmac
import hashlib
import os
import re
import sqlite3
import sys
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

DEV_KEY = "vn3ds-dev-key-change-me"

GAMES = ("quiz", "miso", "draw", "lantern", "snake", "tower", "invaders")

MAX_BODY = 1024            # bytes in a POST body
MAX_PATH = 512             # bytes in the request path + query
NAME_MAX = 16
TOP_MAX = 100

PLAYER_RE = re.compile(r"^[A-Za-z0-9]{1,32}$")
NONCE_RE = re.compile(r"^[A-Za-z0-9]{8,64}$")
SCORE_RE = re.compile(r"^[0-9]{1,3}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS scores (
    id       INTEGER PRIMARY KEY,
    game     TEXT    NOT NULL,
    player   TEXT    NOT NULL,
    name     TEXT    NOT NULL,
    score    INTEGER NOT NULL,
    achieved INTEGER NOT NULL,   -- unix time the best score was reached
    UNIQUE (game, player, name)
);
CREATE INDEX IF NOT EXISTS scores_by_rank ON scores (game, score DESC, achieved);
CREATE TABLE IF NOT EXISTS nonces (
    nonce TEXT    PRIMARY KEY,
    seen  INTEGER NOT NULL
);
"""


def load_key():
    key = os.environ.get("LEADERBOARD_KEY")
    if key:
        return key
    path = os.environ.get("LEADERBOARD_KEY_FILE")
    if not path and os.environ.get("CREDENTIALS_DIRECTORY"):   # systemd LoadCredential=key:...
        path = os.path.join(os.environ["CREDENTIALS_DIRECTORY"], "key")
    if path:
        with open(path, encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    print("leaderboard: WARNING using the development key", file=sys.stderr)
    return DEV_KEY


def sign(key, game, name, score, nonce):
    msg = f"{game}|{name}|{score}|{nonce}".encode("utf-8")
    return hmac.new(key.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def clean_name(raw):
    """Printable ASCII only (no tabs or newlines), whitespace collapsed."""
    kept = "".join(c for c in raw if " " <= c <= "~")
    return " ".join(kept.split())


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class Store:
    """The SQLite file, shared by all request threads behind one lock."""

    def __init__(self, path):
        self.lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)

    def use_nonce(self, nonce):
        """False if the nonce was seen before."""
        with self.lock:
            try:
                self.db.execute("INSERT INTO nonces (nonce, seen) VALUES (?, ?)",
                                (nonce, int(time.time())))
                return True
            except sqlite3.IntegrityError:
                return False

    def submit(self, game, player, name, score):
        """Keeps the best score; returns (rank, total) of that best."""
        now = int(time.time())
        with self.lock:
            self.db.execute("BEGIN")
            try:
                row = self.db.execute(
                    "SELECT score FROM scores WHERE game=? AND player=? AND name=?",
                    (game, player, name)).fetchone()
                if row is None:
                    self.db.execute(
                        "INSERT INTO scores (game, player, name, score, achieved) VALUES (?,?,?,?,?)",
                        (game, player, name, score, now))
                    best = score
                elif score > row[0]:
                    self.db.execute(
                        "UPDATE scores SET score=?, achieved=? WHERE game=? AND player=? AND name=?",
                        (score, now, game, player, name))
                    best = score
                else:
                    best = row[0]
                higher = self.db.execute(
                    "SELECT COUNT(*) FROM scores WHERE game=? AND score>?", (game, best)).fetchone()[0]
                total = self.db.execute(
                    "SELECT COUNT(*) FROM scores WHERE game=?", (game,)).fetchone()[0]
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise
        return higher + 1, total

    def top(self, game, n):
        with self.lock:
            rows = self.db.execute(
                "SELECT name, score FROM scores WHERE game=? ORDER BY score DESC, achieved, id LIMIT ?",
                (game, n)).fetchall()
        out, rank, last = [], 0, None
        for i, (name, score) in enumerate(rows):
            if score != last:
                rank, last = i + 1, score
            out.append((rank, name, score))
        return out

    # admin
    def list(self, game=None):
        with self.lock:
            sql = "SELECT id, game, score, name, player, achieved FROM scores"
            if game:
                return self.db.execute(sql + " WHERE game=? ORDER BY score DESC, achieved", (game,)).fetchall()
            return self.db.execute(sql + " ORDER BY game, score DESC, achieved").fetchall()

    def delete(self, ids):
        with self.lock:
            cur = self.db.execute(
                f"DELETE FROM scores WHERE id IN ({','.join('?' * len(ids))})", list(ids))
            return cur.rowcount


class RateLimiter:
    """At most `limit` events per `window` seconds for each key (client IP)."""

    def __init__(self, limit, window=60.0):
        self.limit, self.window = limit, window
        self.events = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self.lock:
            q = self.events[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            if len(self.events) > 10000:   # forget idle clients now and then
                for k in [k for k, v in self.events.items() if not v]:
                    del self.events[k]
            return True


class Handler(BaseHTTPRequestHandler):
    server_version = "vn3ds-leaderboard/1"
    sys_version = ""
    protocol_version = "HTTP/1.0"
    timeout = 10    # seconds a client may take to send its request

    # ---- plumbing ----
    def reply(self, status, text):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def fail(self, err):
        self.reply(err.status, f"error\t{err.message}\n")

    def handle_api(self, fn):
        try:
            if len(self.path) > MAX_PATH:
                raise ApiError(414, "request too long")
            fn()
        except ApiError as e:
            self.fail(e)
        except Exception as e:   # keep serving whatever happens
            self.log_error("internal error: %r", e)
            self.fail(ApiError(500, "internal error"))

    def limited(self, limiter):
        if not limiter.allow(self.client_address[0]):
            raise ApiError(429, "too many requests, try again in a minute")

    # ---- routes ----
    def do_GET(self):
        self.handle_api(self.get)

    def do_POST(self):
        self.handle_api(self.post)

    def get(self):
        url = urlsplit(self.path)
        if url.path in ("/", "/v1/health"):
            return self.reply(200, "ok\n")
        if url.path != "/v1/top":
            raise ApiError(404, "not found")
        self.limited(self.server.get_limiter)
        q = parse_qs(url.query)
        game = q.get("game", [""])[0]
        if game not in GAMES:
            raise ApiError(400, "unknown game")
        try:
            n = int(q.get("n", ["10"])[0])
        except ValueError:
            raise ApiError(400, "bad n")
        n = max(1, min(TOP_MAX, n))
        rows = self.server.store.top(game, n)
        self.reply(200, "".join(f"{r}\t{name}\t{s}\n" for r, name, s in rows))

    def post(self):
        if urlsplit(self.path).path != "/v1/score":
            raise ApiError(404, "not found")
        self.limited(self.server.post_limiter)
        length = self.headers.get("Content-Length")
        if length is None or not length.isdigit():
            raise ApiError(411, "Content-Length required")
        if int(length) > MAX_BODY:
            raise ApiError(413, "request too large")
        raw = self.rfile.read(int(length))
        try:
            form = parse_qs(raw.decode("ascii"), keep_blank_values=True, strict_parsing=False)
        except UnicodeDecodeError:
            raise ApiError(400, "bad form")
        f = {k: v[0] for k, v in form.items()}
        game, name, score = f.get("game", ""), f.get("name", ""), f.get("score", "")
        player, nonce, sig = f.get("player", ""), f.get("nonce", ""), f.get("sig", "")

        if game not in GAMES:
            raise ApiError(400, "unknown game")
        if not SCORE_RE.match(score) or not 0 <= int(score) <= 100:
            raise ApiError(400, "score must be 0..100")
        if not PLAYER_RE.match(player):
            raise ApiError(400, "bad player id")
        if not NONCE_RE.match(nonce):
            raise ApiError(400, "bad nonce")
        want = sign(self.server.key, game, name, score, nonce)
        if not hmac.compare_digest(want, sig.lower()):
            raise ApiError(403, "bad signature")
        clean = clean_name(name)
        if not 1 <= len(clean) <= NAME_MAX:
            raise ApiError(400, f"name must be 1..{NAME_MAX} printable characters")
        if not self.server.store.use_nonce(nonce):
            raise ApiError(409, "nonce already used")
        rank, total = self.server.store.submit(game, player, clean, int(score))
        self.reply(200, f"ok\t{rank}\t{total}\n")


class LeaderboardServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32

    def __init__(self, addr, store, key, post_limit=20, get_limit=120, window=60.0):
        super().__init__(addr, Handler)
        self.store = store
        self.key = key
        self.post_limiter = RateLimiter(post_limit, window)
        self.get_limiter = RateLimiter(get_limit, window)


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def main(argv=None):
    ap = argparse.ArgumentParser(description="vn3ds minigame leaderboard server")
    ap.add_argument("--host", default=os.environ.get("LEADERBOARD_HOST", "0.0.0.0"))
    ap.add_argument("--port", type=int, default=env_int("LEADERBOARD_PORT", 8080))
    ap.add_argument("--db", default=os.environ.get("LEADERBOARD_DB", "leaderboard.db"))
    ap.add_argument("--list", action="store_true", help="print the entries and exit")
    ap.add_argument("--game", help="with --list: only this game")
    ap.add_argument("--delete", type=int, action="append", metavar="ID",
                    help="delete the entry with this id (see --list); repeatable")
    args = ap.parse_args(argv)

    store = Store(args.db)
    if args.list:
        print("id\tgame\tscore\tname\tplayer\tachieved (UTC)")
        for id_, game, score, name, player, ts in store.list(args.game):
            when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts))
            print(f"{id_}\t{game}\t{score}\t{name}\t{player}\t{when}")
        return 0
    if args.delete:
        print(f"deleted {store.delete(args.delete)} entr(y/ies)")
        return 0

    server = LeaderboardServer((args.host, args.port), store, load_key(),
                               post_limit=env_int("LEADERBOARD_POST_LIMIT", 20),
                               get_limit=env_int("LEADERBOARD_GET_LIMIT", 120))
    print(f"leaderboard: serving on {args.host}:{server.server_address[1]}, db {args.db}",
          file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
