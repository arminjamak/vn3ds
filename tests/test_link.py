"""Games from a browser: the vn3ds link (server/link) end to end.

    python3 tests/test_link.py [engine/build-host/vn3ds-host] [game folder]

`vn3ds-host --receive` stands in for the 3DS, server/link/devrelay.py for
the Cloudflare Worker, and Node runs the page's sender
(server/link/web/vn3ds-send.js). Checked:
1. the 3DS links up by itself once paired and the page finds it by its
   public address ("same network"); the code matches the server's;
2. a game goes through and arrives byte for byte; the sender never runs
   more than its window ahead of the 3DS's acks;
3. sending again skips everything;
4. a link cut in the middle of a transfer is retried and finishes;
5. the QR code on the receive screen is the standard one (a full-capacity
   code, checked module for module against an independent encoder once);
6. self-update: a newer release replaces the running .3dsx (checked by its
   SHA-256), the same version leaves it alone.
Nothing here needs the internet: everything runs on 127.0.0.1.

VN3DS_TEST_LINK=http://127.0.0.1:8799 runs 1-3 against another link
instead, such as the Worker itself under `npx wrangler dev` in server/link
(4 needs devrelay's test hook)."""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(REPO, "server", "link"))

import devrelay  # noqa: E402

HOST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "engine", "build-host", "vn3ds-host")
GAME = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
KEY = "00112233445566778899aabbccddeeff"
EXT = os.environ.get("VN3DS_TEST_LINK", "").rstrip("/")
fail = 0


def check(cond, what):
    global fail
    print(("  ok: " if cond else "  FAIL: ") + what)
    fail |= not cond


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def base(port):
    return EXT or f"http://127.0.0.1:{port}"


def relay(port, *extra):
    if EXT:
        return None
    p = subprocess.Popen([sys.executable, os.path.join(REPO, "server", "link", "devrelay.py"),
                          "--host", "127.0.0.1", "--port", str(port), *extra],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/near", timeout=1)
            return p
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("the relay didn't start")


def receiver(root, port):
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "relay.cfg"), "w") as f:
        f.write(f"key = {KEY}\nserver = {base(port).split('://')[1]}\nweb = https://vn3ds.com\n")
    return subprocess.Popen([HOST, "--receive", "--root", root], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)


def get(port, path):
    return json.loads(urllib.request.urlopen(base(port) + path, timeout=5).read())


def wait_online(port, code, seconds=15):
    t0 = time.time()
    while time.time() - t0 < seconds:
        if any(d["code"] == code and d["online"] for d in get(port, "/near")):
            return True
        time.sleep(0.2)
    return False


def node(port, code, *mode):
    p = subprocess.run(["node", os.path.join(HERE, "link_send.mjs"), base(port), code, GAME, *mode],
                       capture_output=True, text=True, timeout=300)
    lines = [json.loads(line) for line in p.stdout.splitlines() if line.startswith("{")]
    return p.returncode, lines, p.stderr


def same_files(root):
    gid = os.path.basename(GAME)
    bad = 0
    n = 0
    for dirpath, _, names in os.walk(GAME):
        for name in names:
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, GAME)
            if (name.endswith((".part", ".txt")) and name != "port-report.txt") or name == "savemap.json":
                continue
            n += 1
            dst = os.path.join(root, "games", gid, rel)
            if not os.path.isfile(dst) or open(src, "rb").read() != open(dst, "rb").read():
                bad += 1
    return n, bad


if shutil.which("node") is None:
    print("  skipped: no node (the page's sender runs in Node here)")
    sys.exit(0)

tmp = tempfile.mkdtemp(prefix="vn3ds-link-")
if GAME is None:
    # a stand-in game: media that doesn't compress, and a big file that does
    # (deflated on the way; and bigger than the sender's 4 MB window)
    GAME = os.path.join(tmp, "src", "link-test")
    os.makedirs(os.path.join(GAME, "img"))
    rnd = __import__("random").Random(7)
    with open(os.path.join(GAME, "game.bin"), "wb") as f:
        f.write(bytes(rnd.randrange(256) for _ in range(30000)))
    for i in range(12):
        with open(os.path.join(GAME, "img", f"bg{i}.jpg"), "wb") as f:
            f.write(rnd.randbytes(150000 + i * 7000))
    with open(os.path.join(GAME, "script.txt.bin"), "wb") as f:
        f.write(b"".join(b"line %d: the quick brown fox\n" % i for i in range(220000)))
port = free_port()
code = devrelay.device_code(KEY)
rl = relay(port)
try:
    print("the 3DS links up and the page finds it on the same network")
    rx = receiver(os.path.join(tmp, "a"), port)
    check(wait_online(port, code), f"listed by /near as {code}, online")
    rc, lines, err = node(port, code, "near")
    near = lines[-1].get("near", []) if lines else []
    check(rc == 0 and any(d["code"] == code for d in near), "findNearby() returns it")

    print("a game goes through the link")
    t0 = time.time()
    rc, lines, err = node(port, code)
    took = time.time() - t0
    res = lines[-1] if lines else {"error": err}
    check(rc == 0 and res.get("result", {}).get("failed") == 0, f"sent ({res}) in {took:.1f} s")
    out, _ = rx.communicate(timeout=30)
    check(rx.returncode == 0, "the receiver finished the transfer")
    n, bad = same_files(os.path.join(tmp, "a"))
    check(n > 0 and bad == 0, f"{n} files arrived byte for byte")
    if not EXT:
        st = get(port, "/stats")
        check(st["acks"] > 0, f"the 3DS acknowledged as it went ({st['acks']} acks)")
        check(st["max_ahead"] <= (4 << 20) + (256 << 10) + 4096,
              f"never more than the window ahead ({st['max_ahead']} bytes)")

    print("sending again skips everything")
    rx = receiver(os.path.join(tmp, "a"), port)
    check(wait_online(port, code), "linked again")
    rc, lines, err = node(port, code)
    skipped = [e for e in lines if e.get("event") == "skipped"]
    res = lines[-1] if lines else {}
    check(rc == 0 and skipped and res.get("result", {}).get("sent") == 0, f"all {n} files were already there")
    rx.communicate(timeout=30)

    print("nobody can replace vn3ds itself through the link")
    rx = receiver(os.path.join(tmp, "c"), port)
    check(wait_online(port, code), "linked")
    rc, lines, err = node(port, code, "engine")
    res = lines[-1] if lines else {}
    rx.communicate(timeout=30)
    check(res.get("result", {}).get("failed") == 1 and not os.path.exists(os.path.join(tmp, "c", "vn3ds.3dsx")),
          f"vn3ds.3dsx refused, the game itself arrived ({res})")
finally:
    if rl:
        rl.terminate()

print("a link cut in the middle is retried and finishes")
port = free_port()
total = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(GAME) for f in fs)
rl = relay(port, "--cut-after", str(1 << 20))   # (the wire bytes: the big file goes deflated)
try:
    if EXT:
        raise StopIteration
    rx = receiver(os.path.join(tmp, "b"), port)
    check(wait_online(port, code), "linked")
    rc, lines, err = node(port, code)
    retries = [e for e in lines if e.get("event") == "retry"]
    res = lines[-1] if lines else {"error": err}
    check(rc == 0 and retries and res.get("result", {}).get("failed") == 0,
          f"finished after {len(retries)} retry ({res})")
    rx.communicate(timeout=30)
    n, bad = same_files(os.path.join(tmp, "b"))
    check(get(port, "/stats")["cuts"] == 1 and bad == 0, f"all {n} files intact after the cut")
except StopIteration:
    print("  skipped: needs devrelay's test hook")
finally:
    if rl:
        rl.terminate()

print("the receive screen's QR code")
# a code that fills version 3 exactly, so no padding choices differ between
# encoders: its modules matched segno's (mask 2) when this was written
q = subprocess.run([HOST, "--qr", "https://vn3ds.com/#" + "A" * 23, "2"], capture_output=True, text=True).stdout
check(len(q.split()) == 29 and hashlib.sha256(q.encode()).hexdigest() == "66fc180a92b572eaaebe66ef8eac33cfe9363c5ebadc70449c843093082e7408",
      f"version 3, the expected modules ({hashlib.sha256(q.encode()).hexdigest()[:12]})")
q = subprocess.run([HOST, "--qr", "https://vn3ds.com/#" + code], capture_output=True, text=True).stdout
check(len(q.split()) == 29, "this 3DS's address is a version 3 code (29 x 29: 4-pixel modules on screen)")

print("vn3ds updates itself from the newest release")
rel = os.path.join(tmp, "release")
os.makedirs(rel)
with open(os.path.join(rel, "tag.txt"), "w") as f:
    f.write("v9.1.0\n")
new_engine = os.urandom(300000)
with open(os.path.join(rel, "vn3ds.3dsx"), "wb") as f:
    f.write(new_engine)
port = free_port()
EXT_SAVED, EXT = EXT, ""
rl = relay(port, "--release", rel)
try:
    for version, want_new in (("v0.2.1", True), ("v9.1.0", False)):
        root = os.path.join(tmp, "upd-" + version)
        os.makedirs(root)
        self_path = os.path.join(root, "vn3ds.3dsx")
        with open(self_path, "wb") as f:
            f.write(b"the old engine")
        with open(os.path.join(root, "update.cfg"), "w") as f:
            f.write(f"url = http://127.0.0.1:{port}\n")
        p = subprocess.run([HOST, "--receive", "--serve", "14", "--root", root, "--self", self_path,
                            "--version-as", version], capture_output=True, text=True, timeout=60)
        with open(self_path, "rb") as f:
            now = f.read()
        if want_new:
            check(now == new_engine and not os.path.exists(self_path + ".old"),
                  f"{version} -> v9.1.0: the .3dsx was replaced with the release's")
        else:
            check(now == b"the old engine", f"{version}: up to date, left alone")
finally:
    rl.terminate()
    EXT = EXT_SAVED

shutil.rmtree(tmp, ignore_errors=True)
print("all link tests passed" if not fail else "FAILED")
sys.exit(fail)
