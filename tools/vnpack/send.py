"""Wireless transfer to a 3DS.

Three ways in, all from `vn3ds-port`:

- **vn3ds's own receiver** (`--3ds IP`): open vn3ds, press Y ("Receive over
  Wi-Fi") and the game folder is streamed straight onto the SD card. The
  same channel updates vn3ds.3dsx itself.
- **3dslink** (`--install --3ds IP`): first-time install with no SD card
  juggling. In the Homebrew Launcher press Y (netloader); vn3ds is sent and
  started, and it opens its receiver automatically so it can be saved to the
  card. Needs the `3dslink` tool from devkitPro.
- **FTP** (`--ftp IP[:PORT]`): for people who use the ftpd homebrew app;
  uploads into sdmc:/3ds/.
"""

import ftplib
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
import zlib

VN3DS_PORT = 5555


def say(msg):
    print(f"[vn3ds-port] {msg}", flush=True)


def _files_of(folder, prefix):
    out = []
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if f.endswith((".part", ".txt")) and f != "port-report.txt":
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            out.append((f"{prefix}/{rel}", full))
    return out


def plan(game_dirs=(), engine=None):
    """[(remote path relative to sdmc:/3ds/vn3ds, local file)]"""
    files = []
    for gd in game_dirs:
        files += _files_of(gd, "games/" + os.path.basename(gd.rstrip("/")))
    if engine:
        files.append(("vn3ds.3dsx", engine))
    return files


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("the 3DS closed the connection")
        buf += chunk
    return buf


def _state_path(host, files):
    """Where the progress of a transfer is remembered between runs."""
    import hashlib
    import tempfile
    sig = hashlib.sha1(host.encode())
    for remote, local in files:
        st = os.stat(local)
        sig.update(f"{remote}|{st.st_size}|{int(st.st_mtime)}".encode())
    return os.path.join(tempfile.gettempdir(), f"vn3ds-send-{sig.hexdigest()[:16]}.txt")


def _load_done(path):
    try:
        with open(path) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def _crc32(path):
    crc = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            crc = zlib.crc32(chunk, crc)
    return crc & 0xFFFFFFFF


def _send_batch(host, files, start, progress, port, timeout, state, proto=2):
    """Send files[start:] over one connection; progress["done"] counts the
    files the 3DS has confirmed so far (it survives an exception)."""
    batch = files[start:]
    total = sum(os.path.getsize(p) for _, p in batch)
    sock = socket.create_connection((host, port), timeout=timeout)
    # Each file ends with a 1-byte reply from the 3DS; without NODELAY the
    # last piece of every file can sit in Nagle's buffer waiting for an ACK.
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
    sock.settimeout(90)
    try:
        sock.sendall(b"VN3D" + struct.pack("<IIQ", proto, len(batch), total))
        done = 0
        t0 = time.time()
        last = 0
        for remote, local in batch:
            size = os.path.getsize(local)
            name = remote.encode("utf-8")
            head = struct.pack("<H", len(name)) + name + struct.pack("<Q", size)
            if proto == 2:
                sock.sendall(head + struct.pack("<I", _crc32(local)))
                if _recv_exact(sock, 1)[0] == 3:   # the 3DS already has this exact file
                    progress["sent"] += 1
                    progress["skipped"] = progress.get("skipped", 0) + 1
                    progress["done"] += 1
                    done += size
                    with open(state, "w") as f:
                        f.write(str(progress["done"]))
                    continue
            else:
                sock.sendall(head)
            with open(local, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    done += len(chunk)
                    if time.time() - last > 1 or done == total:
                        last = time.time()
                        rate = done / max(1e-3, time.time() - t0) / 1e6
                        print(f"\r  file {progress['done'] + 1}/{len(files)}  "
                              f"{done / 1e6:7.1f} / {total / 1e6:.1f} MB  ({rate:.2f} MB/s)   ",
                              end="", flush=True)
            code = _recv_exact(sock, 1)[0]
            if code == 0:
                progress["sent"] += 1
            else:
                progress["refused"] += 1
                print(f"\n  the 3DS {'refused' if code == 1 else 'could not write'} {remote}")
            progress["done"] += 1
            with open(state, "w") as f:
                f.write(str(progress["done"]))
        print()
        if _recv_exact(sock, 4) != b"DONE":
            raise ConnectionError("transfer did not finish cleanly")
    finally:
        sock.close()


def send_vn3ds(host, files, port=VN3DS_PORT, timeout=15, retries=8):
    """Stream files to vn3ds's receive screen. Returns (sent, refused).

    Wi-Fi on the 3DS drops out now and then, so a broken connection is
    retried, continuing after the last file the 3DS confirmed. The position
    is also remembered on disk: running the same command again resumes."""
    state = _state_path(host, files)
    start = _load_done(state)
    if 0 < start < len(files):
        say(f"resuming: the first {start} of {len(files)} files are already on the 3DS")
    else:
        start = 0
    progress = {"done": start, "sent": 0, "refused": 0, "skipped": 0}
    proto = 2
    for attempt in range(retries + 1):
        before = progress["done"]
        try:
            _send_batch(host, files, progress["done"], progress, port, timeout, state, proto)
            if progress["skipped"]:
                say(f"{progress['skipped']} unchanged files were already on the 3DS and skipped")
            try:
                os.remove(state)
            except OSError:
                pass
            return progress["sent"] + start, progress["refused"]
        except (OSError, ConnectionError) as e:
            print()
            if proto == 2 and progress["done"] == before and isinstance(e, ConnectionError):
                # an older vn3ds hangs up on protocol 2: send everything the old way
                say("this vn3ds is older: sending every file (update it with --install)")
                proto = 1
                time.sleep(1)
                continue
            if attempt == retries:
                say(f"giving up after {retries} reconnects; run the same command again to resume")
                raise
            say(f"connection dropped ({e.__class__.__name__}); reconnecting to resume at file "
                f"{progress['done'] + 1} of {len(files)}")
            if not wait_for_receiver(host, port, seconds=180):
                say("vn3ds isn't listening; open its Receive screen (Y), then run the same "
                    "command again to resume")
                raise


def find_3dslink():
    for cand in (shutil.which("3dslink"), "/opt/devkitpro/tools/bin/3dslink"):
        if cand and os.path.exists(cand):
            return cand
    return None


def install_via_3dslink(host, engine):
    """Send vn3ds.3dsx to the Homebrew Launcher's netloader and start it."""
    tool = find_3dslink()
    if not tool:
        sys.exit("vn3ds-port: 3dslink not found. Install devkitPro's 3dstools, use --ftp, "
                 "or copy engine/vn3ds.3dsx to sdmc:/3ds/ once by hand.")
    say("in the Homebrew Launcher on the 3DS, press Y (netloader) now")
    # argv[0] tells vn3ds it was started over the network, so it opens its
    # receiver and can save itself to the SD card.
    cmd = [tool, engine, "-0", "3dslink:/vn3ds.3dsx", "-r", "10"] + (["-a", host] if host else [])
    for attempt in range(90):   # about three minutes to open the netloader
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            say("vn3ds sent and started")
            return
        time.sleep(2)
    sys.exit("vn3ds-port: 3dslink could not reach the Homebrew Launcher:\n" + r.stdout + r.stderr)


def wait_for_receiver(host, port=VN3DS_PORT, seconds=60):
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            socket.create_connection((host, port), timeout=2).close()
            return True
        except OSError:
            time.sleep(1)
    return False


def send_ftp(target, files):
    """Upload through the ftpd homebrew app (default port 5000)."""
    host, _, port = target.partition(":")
    ftp = ftplib.FTP()
    ftp.connect(host, int(port or 5000), timeout=20)
    ftp.login()
    made = set()

    def mkdirs(path):
        parts = path.strip("/").split("/")
        for i in range(1, len(parts) + 1):
            d = "/" + "/".join(parts[:i])
            if d in made:
                continue
            try:
                ftp.mkd(d)
            except ftplib.error_perm:
                pass
            made.add(d)

    total = sum(os.path.getsize(p) for _, p in files)
    done = 0
    for remote, local in files:
        dest = "/3ds/" + ("vn3ds.3dsx" if remote == "vn3ds.3dsx" else "vn3ds/" + remote)
        mkdirs(os.path.dirname(dest))
        with open(local, "rb") as f:
            ftp.storbinary("STOR " + dest, f, blocksize=64 * 1024)
        done += os.path.getsize(local)
        print(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB", end="", flush=True)
    print()
    ftp.quit()
    return len(files)
