"""A stand-in for the Homebrew Launcher's netloader, for tests.

It answers the "3dsboot" UDP ping with "boot3ds" and receives one .3dsx over
TCP exactly the way the launcher does (see vnpack/send.py for the framing),
checking every field. Run it on its own to emulate "vn3ds sent and started":

    python3 tests/fake_netloader.py --save got.3dsx [--then CMD ...]

--then runs a command once a file has arrived (e.g. the desktop engine with
--listen, standing in for vn3ds starting up on the 3DS)."""

import argparse
import socket
import struct
import subprocess
import sys
import threading
import zlib

PORT = 17491
CHUNK = 16 * 1024   # the launcher's inflate input buffer


class FakeNetloader:
    def __init__(self, host="127.0.0.1", port=PORT, respond=0, respond_after=0):
        self.host, self.port = host, port
        self.respond, self.respond_after = respond, respond_after
        self.received = []        # dicts: name, size, data, argv, chunks, raw
        self.errors = []
        self.event = threading.Event()
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp.bind((host, port))
        self.tcp = socket.socket()
        self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp.bind((host, port))
        self.tcp.listen(2)
        self.pings = 0
        self._stop = False
        for fn in (self._serve_udp, self._serve_tcp):
            threading.Thread(target=fn, daemon=True).start()

    def close(self):
        self._stop = True
        for s in (self.udp, self.tcp):
            try:
                s.close()
            except OSError:
                pass

    def _serve_udp(self):
        while not self._stop:
            try:
                data, addr = self.udp.recvfrom(64)
            except OSError:
                return
            if data.startswith(b"3dsboot"):
                self.pings += 1
                self.udp.sendto(b"boot3ds", addr)

    def _serve_tcp(self):
        while not self._stop:
            try:
                c, _ = self.tcp.accept()
            except OSError:
                return
            try:
                self._one(c)
            except Exception as e:   # noqa: BLE001 - recorded for the test
                self.errors.append(repr(e))
            finally:
                c.close()
                self.event.set()

    def _one(self, c):
        raw = bytearray()
        c.settimeout(10)

        def rx(n):
            b = b""
            while len(b) < n:
                d = c.recv(n - len(b))
                if not d:
                    raise EOFError(f"closed after {len(raw) + len(b)} bytes")
                b += d
            raw.extend(b)
            return b

        def i32():
            return struct.unpack("<i", rx(4))[0]

        namelen = i32()
        if not 0 < namelen < 256:      # the launcher says "namelen <errno>"
            raise ValueError(f"namelen {namelen}")
        name = rx(namelen).decode()
        size = i32()
        c.sendall(struct.pack("<i", self.respond))
        if self.respond:
            return
        z = zlib.decompressobj()
        data, chunks = b"", []
        while not z.eof:
            n = i32()
            if not 0 < n <= CHUNK:
                raise ValueError(f"chunk of {n} bytes")
            chunks.append(n)
            data += z.decompress(rx(n))
        if len(data) != size:
            raise ValueError(f"got {len(data)} bytes, header said {size}")
        c.sendall(struct.pack("<i", self.respond_after))
        cmdlen = i32()
        block = rx(cmdlen)
        if not block.endswith(b"\0"):
            raise ValueError("argv block must end in NUL")
        argv = [a.decode() for a in block[:-1].split(b"\0")]
        self.received.append(dict(name=name, size=size, data=data, argv=argv,
                                  chunks=chunks, raw=bytes(raw)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--save", help="write the received file here")
    ap.add_argument("--then", nargs=argparse.REMAINDER, help="command to run after it arrived")
    args = ap.parse_args()
    fake = FakeNetloader(args.host)
    print(f"fake netloader on {args.host}:{PORT}", flush=True)
    while not fake.received:
        fake.event.wait()
        fake.event.clear()
        for e in fake.errors:
            print("error:", e, flush=True)
        fake.errors.clear()
    got = fake.received[0]
    print(f"received {got['name']} ({got['size']} bytes, {len(got['chunks'])} chunks), "
          f"argv {got['argv']}", flush=True)
    if args.save:
        with open(args.save, "wb") as f:
            f.write(got["data"])
    fake.close()
    if args.then:
        sys.exit(subprocess.call(args.then))


if __name__ == "__main__":
    main()
