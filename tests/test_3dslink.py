"""The pure-Python 3dslink sender against a fake netloader (and, when
devkitPro's 3dslink is installed, byte for byte against what it sends).
    python3 tests/test_3dslink.py"""

import os
import random
import socket
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
sys.path.insert(0, HERE)

from fake_netloader import FakeNetloader  # noqa: E402
from vnpack import detect, send  # noqa: E402

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


tmp = tempfile.mkdtemp()
path = os.path.join(tmp, "vn3ds.3dsx")
rnd = random.Random(7)
# compressible and incompressible parts, more than a few chunks
blob = b"3DSX" + bytes(rnd.getrandbits(8) for _ in range(70000)) + b"\0" * 200000
with open(path, "wb") as f:
    f.write(blob)

# 1. framing and contents
fake = FakeNetloader(port=free_port())
send.send_3dslink("127.0.0.1", path, argv0="3dslink:/vn3ds.3dsx", port=fake.port)
fake.event.wait(5)
check(not fake.errors, f"no framing errors {fake.errors}")
got = fake.received[0] if fake.received else {}
check(got.get("name") == "vn3ds.3dsx", "file name")
check(got.get("data") == blob, "file arrives intact")
check(got.get("argv") == ["3dslink:/vn3ds.3dsx"], "argv[0] says it came over 3dslink")
check(all(n <= 16384 for n in got.get("chunks", [1 << 20])), "chunks fit the launcher's buffer")
head, chunks, argv = send.netloader_frames(path, "3dslink:/vn3ds.3dsx")
check(got.get("raw") == head + b"".join(len(c).to_bytes(4, "little") + c for c in chunks) + argv,
      "bytes on the wire match netloader_frames")
fake.close()

# 2. extra arguments and the default argv[0]
fake = FakeNetloader(port=free_port())
send.send_3dslink("127.0.0.1", path, args=("--x", "y z"), port=fake.port, name="other.3dsx")
fake.event.wait(5)
check(fake.received and fake.received[0]["argv"] == ["3dslink:/other.3dsx", "--x", "y z"],
      "default argv[0] and extra arguments")
fake.close()

# 3. the 3DS refusing (no space)
fake = FakeNetloader(port=free_port(), respond=-2)
try:
    send.send_3dslink("127.0.0.1", path, port=fake.port)
    check(False, "a refusal raises")
except send.NetloaderError as e:
    check("space" in str(e), f"a refusal raises NetloaderError ({e})")
fake.close()

# 4. the UDP ping (unicast, the same message as the broadcast)
fake = FakeNetloader(port=send.NETLOADER_PORT)
check(detect.ping_netloader("127.0.0.1"), "ping_netloader finds it")
send.install_via_3dslink("127.0.0.1", path, seconds=10)
fake.event.wait(5)
check(len(fake.received) == 1 and fake.received[0]["data"] == blob, "install_via_3dslink sends it")
fake.close()

# 5. the same bytes as devkitPro's 3dslink
tool = send.find_3dslink()
if tool:
    for p in (path, os.path.join(HERE, "..", "engine", "vn3ds.3dsx")):
        if not os.path.exists(p):
            continue
        fake = FakeNetloader(port=send.NETLOADER_PORT)
        r = subprocess.run([tool, p, "-0", "3dslink:/vn3ds.3dsx", "-a", "127.0.0.1"],
                           capture_output=True, text=True, timeout=30)
        fake.event.wait(5)
        theirs = fake.received[0]["raw"] if fake.received else b""
        fake.close()
        fake = FakeNetloader(port=send.NETLOADER_PORT)
        send.send_3dslink("127.0.0.1", p, argv0="3dslink:/vn3ds.3dsx")
        fake.event.wait(5)
        ours = fake.received[0]["raw"] if fake.received else b"?"
        fake.close()
        check(r.returncode == 0 and theirs == ours,
              f"byte-identical to {os.path.basename(tool)} for {os.path.basename(p)} ({len(ours)} bytes)")
else:
    print("  (devkitPro 3dslink not installed: byte comparison skipped)")

print("3dslink: " + ("FAILED" if fail else "all passed"))
sys.exit(1 if fail else 0)
