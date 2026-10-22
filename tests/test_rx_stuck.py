"""A dead connection must never block the receiver.

    python3 tests/test_rx_stuck.py [engine/build-host/vn3ds-host] [build/syntax-test]

The Wi-Fi can drop a connection without a goodbye. The receiver used to wait
in recv() on it forever, refusing every reconnect, so a transfer stuck at
"waiting for vn3ds". Now:
1. a connection that goes quiet is taken over by the sender's reconnect;
2. a connection that carries nothing for 20 s is closed on its own."""

import os
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(REPO, "tools"))

from vnpack import detect, send  # noqa: E402

HOST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "engine", "build-host", "vn3ds-host")
GAME = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "build", "syntax-test")

fail = 0


def check(cond, what):
    global fail
    print(("  ok: " if cond else "  FAIL: ") + what)
    fail |= not cond


def receiver(root):
    p = subprocess.Popen([HOST, "--receive", "--root", root], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    t0 = time.time()
    while time.time() - t0 < 10 and not detect.listening("127.0.0.1"):
        time.sleep(0.2)
    return p


def game_files():
    root = os.path.dirname(os.path.abspath(GAME))
    files = []
    for dirpath, _, names in os.walk(GAME):
        for n in sorted(names):
            full = os.path.join(dirpath, n)
            files.append(("games/" + os.path.relpath(full, root).replace(os.sep, "/"), full))
    return files


tmp = tempfile.mkdtemp()
print("a dead connection is taken over by the reconnect")
rx = receiver(os.path.join(tmp, "a"))
dead = socket.create_connection(("127.0.0.1", detect.VN3DS_PORT), timeout=5)
dead.sendall(b"VN3D")            # a transfer that started, then went silent
time.sleep(4)                    # quiet for longer than the takeover delay
t0 = time.time()
sent, refused = send.send_vn3ds("127.0.0.1", game_files(), report=lambda *a, **k: None, retries=3)
took = time.time() - t0
out, _ = rx.communicate(timeout=60)
check(rx.returncode == 0 and refused == 0, f"the game arrived ({sent} files)")
check(took < 15, f"without waiting for the dead connection ({took:.1f} s)")
dead.close()

print("a silent connection is closed by itself")
rx = receiver(os.path.join(tmp, "b"))
dead = socket.create_connection(("127.0.0.1", detect.VN3DS_PORT), timeout=5)
dead.settimeout(30)
t0 = time.time()
try:
    closed = dead.recv(1) == b""
except OSError:
    closed = True
waited = time.time() - t0
check(closed and 15 < waited < 28, f"closed after {waited:.0f} s of silence")
dead.close()
sent, refused = send.send_vn3ds("127.0.0.1", game_files(), report=lambda *a, **k: None, retries=3)
out, _ = rx.communicate(timeout=60)
check(rx.returncode == 0, "and the next transfer goes through")

print("rx_stuck: all passed" if not fail else "rx_stuck: FAILED")
sys.exit(1 if fail else 0)
