"""Wireless transfer to a 3DS.

Three ways in, all from `vn3ds-port`:

- **vn3ds's own receiver** (`--3ds IP`): open vn3ds, press Y ("Receive over
  Wi-Fi") and the game folder is streamed straight onto the SD card. The
  same channel updates vn3ds.3dsx itself.
- **3dslink** (the Homebrew Launcher's netloader): first-time install with
  no SD card juggling. In the Homebrew Launcher press Y; vn3ds is sent and
  started (`send_3dslink`, a pure-Python version of devkitPro's 3dslink),
  and it opens its receiver automatically so it can be saved to the card.
- **FTP** (`--ftp IP[:PORT]`): for people who use the ftpd homebrew app;
  uploads into sdmc:/3ds/.
"""

import ftplib
import os
import shutil
import socket
import struct
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


def _print_progress(event, **info):
    """The command line's progress display (the default for send_vn3ds)."""
    if event == "checking":
        say(f"checking {info['files']} files")
    elif event == "skipped":
        say(f"{info['skipped']} files are already on the 3DS; sending {info['need']}")
    elif event == "bytes":
        print(f"\r  {info['done'] / 1e6:7.1f} / {info['total'] / 1e6:.1f} MB  ({info['rate'] / 1e6:.3f} MB/s, "
              f"about {info['left'] / 60:.0f} min left)   ", end="", flush=True)
    elif event == "sent" and info.get("need"):
        print()
    elif event in ("retry", "waiting", "info"):
        if event == "retry":
            print()
        say(info["text"])


# Protocol 4 is protocol 3 with each file framed as u32 index, u8 method,
# u64 wire length: method 0 = the raw bytes, 1 = raw deflate (wbits -15),
# which the 3DS unpacks as it arrives and checks against the manifest's size
# and CRC. Older vn3ds builds hang up on version 4; then protocol 3 is used
# for that 3DS for the rest of the session.
_PROTO = {}                       # host -> protocol to use (3 after a 3DS refused 4)
_PROTO_OK = set()                 # hosts a transfer has worked with
COMPRESS_MIN_GAIN = 0.97          # deflate only when it saves at least 3%
PROBE_ABOVE = 8 << 20             # bigger files: test-compress the start first
PROBE_BYTES = 1 << 20


def _deflate(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15, 9)
    return co.compress(data) + co.flush()


def _pack_file(path, size):
    """(method, payload or None): payload None means "stream it raw from disk"."""
    if size > PROBE_ABOVE:
        with open(path, "rb") as f:
            head = f.read(PROBE_BYTES)
        if len(_deflate(head)) >= len(head) * COMPRESS_MIN_GAIN:
            return 0, None        # media that doesn't shrink: no need to hold it in memory
    with open(path, "rb") as f:
        data = f.read()
    z = _deflate(data)
    if len(z) < len(data) * COMPRESS_MIN_GAIN:
        return 1, z
    return 0, data


def _packer(files, sizes, need, q, quit_):
    """Compresses the needed files one or two ahead of the socket."""
    import queue
    try:
        for i in need:
            item = (i,) + _pack_file(files[i][1], sizes[i])
            while True:
                if quit_.is_set():
                    return
                try:
                    q.put(item, timeout=0.25)
                    break
                except queue.Full:
                    pass
        q.put(None)
    except BaseException as e:   # noqa: BLE001 - handed to the sending thread
        q.put(e)


def _send_v3(host, files, port, timeout, progress, report=_print_progress, stop=None, proto=4):
    """Protocols 3 and 4: manifest, one bitmap back, then the needed files
    in one stream. Returns (sent, skipped, failed); progress["need"] lists
    the indices of the files that had to be sent, progress["bitmap"] says
    whether the 3DS answered the manifest."""
    import queue
    import threading
    total = sum(os.path.getsize(p) for _, p in files)
    progress["bitmap"] = False
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
    quit_ = threading.Event()
    try:
        sock.settimeout(90)
        head = [b"VN3D" + struct.pack("<IIQ", proto, len(files), total)]
        sizes = []
        report("checking", files=len(files))
        for remote, local in files:
            name = remote.encode("utf-8")
            size = os.path.getsize(local)
            sizes.append(size)
            head.append(struct.pack("<H", len(name)) + name + struct.pack("<QI", size, _crc32(local)))
        sock.sendall(b"".join(head))
        # the 3DS compares the list with its card (this can take a while)
        sock.settimeout(1800)
        bits = _recv_exact(sock, (len(files) + 7) // 8)
        progress["bitmap"] = True
        sock.settimeout(120)
        need = [i for i in range(len(files)) if bits[i >> 3] >> (i & 7) & 1]
        progress["need"] = need
        skipped = len(files) - len(need)
        if skipped:
            report("skipped", skipped=skipped, need=len(need))
        want = sum(sizes[i] for i in need)
        # Progress counts unpacked bytes, so the speed and time left are
        # what the transfer really achieves; wire counts what went out.
        done, wire, t0, last = 0, 0, time.time(), 0

        def tick(force=False):
            nonlocal last
            if force or time.time() - last > 1:
                last = time.time()
                rate = done / max(1e-3, time.time() - t0)
                report("bytes", done=done, total=want, rate=rate,
                       left=(want - done) / max(rate, 1), wire=wire)
                if stop and stop():
                    raise Cancelled()
        tick(True)
        q = queue.Queue(maxsize=2)
        if proto >= 4 and need:
            threading.Thread(target=_packer, args=(files, sizes, need, q, quit_),
                             daemon=True).start()
        for i in need:
            if proto >= 4:
                while True:
                    try:
                        item = q.get(timeout=0.5)
                        break
                    except queue.Empty:
                        if stop and stop():
                            raise Cancelled()
                if isinstance(item, BaseException):
                    raise item
                _, method, payload = item
                wire_len = sizes[i] if payload is None else len(payload)
                sock.sendall(struct.pack("<IBQ", i, method, wire_len))
            else:
                method, payload = 0, None
                sock.sendall(struct.pack("<I", i))
            base = done
            if payload is not None:
                step = 64 * 1024
                for k in range(0, len(payload), step):
                    piece = payload[k:k + step]
                    sock.sendall(piece)
                    wire += len(piece)
                    done = base + sizes[i] * (k + len(piece)) // max(1, len(payload))
                    tick()
                done = base + sizes[i]
            else:
                with open(files[i][1], "rb") as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        sock.sendall(chunk)
                        done += len(chunk)
                        wire += len(chunk)
                        tick()
            progress["done"] = i
        if need:
            tick(True)
        progress["wire"], progress["unpacked"] = wire, want
        report("sent", need=len(need), wire=wire, unpacked=want)
        if _recv_exact(sock, 4) != b"DONE":
            raise ConnectionError("transfer did not finish cleanly")
        failed = struct.unpack("<I", _recv_exact(sock, 4))[0]
        return len(need) - failed, skipped, failed
    finally:
        quit_.set()
        sock.close()


class Cancelled(Exception):
    """The caller's stop() said to stop."""


def send_vn3ds(host, files, port=VN3DS_PORT, timeout=15, retries=8, forever=False,
               report=None, stop=None, info=None):
    """Stream files to vn3ds's receive screen. Returns (sent, refused).

    Newer vn3ds builds get protocol 4 (3 with each file deflated when that
    saves something; builds that only know 3 get 3): a dropped connection
    is simply retried (with `forever`, until it works, e.g. overnight), and
    every retry skips what already arrived. Older builds fall back to
    protocols 2 and 1 below.

    report(event, **info) gets the progress ("checking", "skipped",
    "bytes", "sent", "retry", "waiting", "info"); by default it is printed.
    "bytes" counts unpacked bytes (wire= what actually went out). stop()
    is asked now and then; when it returns True, Cancelled is raised. If
    `info` is a dict, info["need"] lists the indices of the files that had
    to be sent (protocols 3 and 4) and info["wire"] the bytes sent."""
    report = report or _print_progress
    progress = {"done": 0} if info is None else info
    progress.setdefault("done", 0)
    attempt = 0
    proto = _PROTO.get(host, 4)
    while True:
        if stop and stop():
            raise Cancelled()
        try:
            sent, skipped, failed = _send_v3(host, files, port, timeout, progress, report, stop,
                                             proto)
            _PROTO[host] = proto
            _PROTO_OK.add(host)
            if skipped and report is _print_progress:
                say(f"{skipped} unchanged files were already on the 3DS")
            return sent + skipped, failed
        except ConnectionError as e:
            if attempt == 0 and not progress.get("bitmap") and host not in _PROTO_OK:
                if proto == 4:
                    proto = _PROTO[host] = 3   # an older vn3ds hung up on protocol 4: try 3
                    report("info", text="this vn3ds is older: sending without compression")
                    time.sleep(0.5)
                    continue
                if "closed" in str(e):
                    break   # and on protocol 3 too: use the old protocols
            err = e
        except OSError as e:
            err = e
        attempt += 1
        if not forever and attempt > retries:
            print()
            say(f"giving up after {retries} reconnects; run the same command again to resume")
            raise err
        wait = min(60, 5 * attempt)
        report("retry", attempt=attempt, wait=wait,
               text=f"connection dropped ({err.__class__.__name__}); retrying in {wait} s "
                    f"(attempt {attempt}{'' if forever else f' of {retries}'})")
        _sleep(wait, stop)
        while not wait_for_receiver(host, port, seconds=120, stop=stop):
            if not forever:
                raise err
            report("waiting", text="waiting for vn3ds (keep it open; it listens on its own)")
    return _send_v12(host, files, port, timeout, retries)


def _send_v12(host, files, port=VN3DS_PORT, timeout=15, retries=8):
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


# --------------------------------------------------------------------------
# 3dslink: send a .3dsx to the Homebrew Launcher's netloader and start it
# --------------------------------------------------------------------------
#
# The same framing as devkitPro's 3dslink (3dstools), all integers int32
# little-endian, on TCP port 17491:
#
#   -> namelen, name (no NUL)           e.g. 10, "vn3ds.3dsx"
#   -> file size (uncompressed)
#   <- response: 0 ok, -1 cannot create the file, -2 no space, -3 no memory
#   -> zlib stream (deflate, default level) in chunks: length, bytes
#      (each at most 16 KiB: the launcher's inflate buffer), until the
#      stream ends
#   <- response (0)
#   -> argv block: length, then the arguments, each ending in NUL;
#      argv[0] "3dslink:/vn3ds.3dsx" tells vn3ds it was started this way
#
# The launcher reads namelen first thing after accepting; a connection that
# sends nothing (or anything else) makes it show an error like "namelen 11"
# (11 = EAGAIN), so never probe this port with a bare TCP connect. Finding
# the 3DS uses the UDP "3dsboot" ping (detect.find_netloader).

NETLOADER_PORT = 17491
NETLOADER_CHUNK = 16 * 1024
NETLOADER_ERRORS = {-1: "the 3DS could not create the file", -2: "not enough space on the SD card",
                    -3: "not enough memory on the 3DS"}


class NetloaderError(OSError):
    pass


def netloader_frames(path, argv0=None, args=(), name=None):
    """The byte pieces send_3dslink writes, in order (the two responses
    come after the header and after the data): (header, [chunks], argv)."""
    name = (name or os.path.basename(path)).encode("utf-8")
    with open(path, "rb") as f:
        data = f.read()
    header = struct.pack("<i", len(name)) + name + struct.pack("<i", len(data))
    # Exactly what 3dslink's deflate loop produces: the file fed in 16 KiB
    # pieces, each piece's output sent in pieces of at most 16 KiB.
    z = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION)
    chunks = []
    pieces = [data[i:i + NETLOADER_CHUNK] for i in range(0, len(data), NETLOADER_CHUNK)] or [b""]
    for k, piece in enumerate(pieces):
        out = z.compress(piece)
        if k == len(pieces) - 1:
            out += z.flush(zlib.Z_FINISH)
        chunks += [out[i:i + NETLOADER_CHUNK] for i in range(0, len(out), NETLOADER_CHUNK)]
    argv = [argv0 or "3dslink:/" + name.decode("utf-8")] + list(args)
    block = b"".join(a.encode("utf-8") + b"\0" for a in argv)
    return header, chunks, struct.pack("<i", len(block)) + block


def send_3dslink(host, path, argv0=None, args=(), port=NETLOADER_PORT, timeout=10,
                 report=None, name=None):
    """Send a .3dsx to the Homebrew Launcher's netloader at host, which then
    starts it. report(sent_bytes, total_bytes) follows the upload. Raises
    OSError (NetloaderError when the 3DS refuses)."""
    header, chunks, argv = netloader_frames(path, argv0, args, name)
    total = sum(len(c) + 4 for c in chunks)
    sock = socket.create_connection((host, port), timeout=timeout)
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(60)
        sock.sendall(header)
        code = struct.unpack("<i", _recv_exact(sock, 4))[0]
        if code != 0:
            raise NetloaderError(NETLOADER_ERRORS.get(code, f"the 3DS answered {code}"))
        sent = 0
        for c in chunks:
            sock.sendall(struct.pack("<i", len(c)) + c)
            sent += len(c) + 4
            if report:
                report(sent, total)
        code = struct.unpack("<i", _recv_exact(sock, 4))[0]
        if code != 0:
            raise NetloaderError(NETLOADER_ERRORS.get(code, f"the 3DS answered {code}"))
        sock.sendall(argv)
    finally:
        sock.close()


def find_3dslink():
    for cand in (shutil.which("3dslink"), "/opt/devkitpro/tools/bin/3dslink"):
        if cand and os.path.exists(cand):
            return cand
    return None


def install_via_3dslink(host, engine, stop=None, seconds=None):
    """Send vn3ds.3dsx to the Homebrew Launcher's netloader and start it,
    trying until the netloader is open (for `seconds`, or forever)."""
    from . import detect
    t0 = time.time()
    # argv[0] tells vn3ds it was started over the network, so it opens its
    # receiver and can save itself to the SD card.
    while True:
        if stop and stop():
            raise Cancelled()
        if detect.ping_netloader(host):
            try:
                send_3dslink(host, engine, argv0="3dslink:/vn3ds.3dsx", name="vn3ds.3dsx")
                return
            except NetloaderError:
                raise
            except OSError:
                pass
        if seconds is not None and time.time() - t0 > seconds:
            raise OSError(f"the Homebrew Launcher's netloader did not answer on {host}")
        _sleep(2, stop)


def _sleep(seconds, stop=None):
    end = time.time() + seconds
    while time.time() < end:
        if stop and stop():
            raise Cancelled()
        time.sleep(min(0.25, max(0, end - time.time())))


def wait_for_receiver(host, port=VN3DS_PORT, seconds=60, stop=None):
    """True once something listens on host:port (seconds=None: forever)."""
    t0 = time.time()
    while seconds is None or time.time() - t0 < seconds:
        if stop and stop():
            raise Cancelled()
        try:
            socket.create_connection((host, port), timeout=2).close()
            return True
        except OSError:
            time.sleep(1)
    return False


def send_ftp(target, files, report=None, stop=None):
    """Upload through the ftpd homebrew app (default port 5000).
    report(done_bytes, total_bytes) follows the upload."""
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
        if stop and stop():
            raise Cancelled()
        with open(local, "rb") as f:
            ftp.storbinary("STOR " + dest, f, blocksize=64 * 1024)
        done += os.path.getsize(local)
        if report:
            report(done, total)
        else:
            print(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB", end="", flush=True)
    if not report:
        print()
    ftp.quit()
    return len(files)
