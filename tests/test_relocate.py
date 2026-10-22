"""Finding the 3DS again: the sender against the desktop build's receiver.

    python3 tests/test_relocate.py [engine/build-host/vn3ds-host] [build/syntax-test]

1. The 3DS was last seen at another IP (a restart gave it a new one): the
   sender searches the network, finds vn3ds and sends the game there.
2. The 3DS is on the Wi-Fi but nothing listens (vn3ds closed, or its
   receiver stuck): the user is told to restart it, and the sender carries
   on by itself once vn3ds is back.
3. The 3DS isn't on the Wi-Fi: the user is told to wake it.

The network search is narrowed to this computer (VN3DS_SCAN_HOSTS), so the
test never touches a real 3DS."""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(REPO, "tools"))

os.environ["VN3DS_SCAN_HOSTS"] = "127.0.0.1"
os.environ["VN3DS_NETLOADER_ADDRESS"] = "127.0.0.1"

from vnpack import detect, flow  # noqa: E402

HOST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "engine", "build-host", "vn3ds-host")
GAME = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "build", "syntax-test")
GONE = "10.255.255.1"   # where the 3DS "was": nothing answers there

flow.RELOCATE_AFTER = 1
flow.DIAGNOSE_AFTER = 2
detect.nintendo_hosts = lambda: []

fail = 0


def check(cond, what):
    global fail
    print(("  ok: " if cond else "  FAIL: ") + what)
    fail |= not cond


class RecordingUI(flow.UI):
    def __init__(self):
        self.hints, self.logs, self.steps = [], [], []
        self.stop = False

    def hint(self, lines):
        self.hints.append(list(lines))

    def log(self, text):
        self.logs.append(text)

    def step(self, id, state, detail="", **kw):
        self.steps.append((id, state, detail))

    def stopped(self):
        return self.stop


def receiver(root):
    return subprocess.Popen([HOST, "--receive", "--root", root], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)


def wait_listening(seconds=10):
    t0 = time.time()
    while time.time() - t0 < seconds:
        if detect.listening("127.0.0.1"):
            return True
        time.sleep(0.2)
    return False


def find_in_thread(ui):
    result = {}

    def run():
        try:
            result["found"] = flow.find_3ds(flow.Options(console=GONE, detect=False), ui, allow_sd=False)
        except flow.send.Cancelled:
            result["found"] = None
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t, result


tmp = tempfile.mkdtemp()
try:
    print("the 3DS has a new IP: found again, the game is sent there")
    rx = receiver(os.path.join(tmp, "root1"))
    check(wait_listening(), "the desktop receiver listens")
    ui = RecordingUI()
    t, result = find_in_thread(ui)
    t.join(30)
    check(result.get("found") == ("vn3ds", "127.0.0.1"), f"found at its new address {result.get('found')}")
    check(any("now at 127.0.0.1" in line for line in ui.logs), "says it followed the 3DS")
    flow.deliver_wifi([GAME], "127.0.0.1", "vn3ds", None, ui)
    out, _ = rx.communicate(timeout=60)
    check(rx.returncode == 0, "the game arrived")

    print("on the Wi-Fi but not listening: restart hint, then carries on")
    detect.pingable = lambda ip, timeout=1.0: ip == GONE
    ui = RecordingUI()
    t, result = find_in_thread(ui)
    time.sleep(16)
    said = [line for lines in ui.hints for line in lines]
    check(any("restart the 3DS" in line for line in said), "tells the user to restart the 3DS")
    check(t.is_alive(), "keeps waiting meanwhile")
    rx = receiver(os.path.join(tmp, "root2"))
    t.join(30)
    check(result.get("found") == ("vn3ds", "127.0.0.1"), "carries on once vn3ds is back")
    rx.kill()
    rx.wait()

    print("not on the Wi-Fi: wake-up hint")
    detect.pingable = lambda ip, timeout=1.0: False
    ui = RecordingUI()
    t, result = find_in_thread(ui)
    time.sleep(16)
    said = [line for lines in ui.hints for line in lines]
    check(any("isn't on the Wi-Fi" in line for line in said), "tells the user the 3DS isn't on the Wi-Fi")
    ui.stop = True
    t.join(10)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("relocate: all passed" if not fail else "relocate: FAILED")
sys.exit(1 if fail else 0)
