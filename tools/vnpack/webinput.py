"""The dropped game file in a web page, read past 2 GB.

In a page the game is mounted where it is (WORKERFS) and read as needed,
but Pyodide's file positions are 32-bit: a seek past 2 GiB comes back
negative ("Raw stream returned invalid position"), so a big download (an
Android build with a 6.5 GB archive.rpa) can't be opened. install() makes
open() of a file under the mount read it straight from the browser's File
instead (FileReaderSync on a slice: synchronous, in a worker), with 64-bit
positions. Everything else opens as usual."""

import builtins
import io
import os

_open = builtins.open
_io_open = io.open


class BlobFile(io.RawIOBase):
    """A read-only, seekable file over a JS Blob/File."""

    def __init__(self, blob, name):
        import js
        self.blob, self.name = blob, name
        self.size = int(blob.size)
        self.pos = 0
        self.reader = js.FileReaderSync.new()

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, pos, whence=0):
        if whence == 1:
            pos += self.pos
        elif whence == 2:
            pos += self.size
        if pos < 0:
            raise OSError("negative seek position")
        self.pos = pos
        return pos

    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        data = self.reader.readAsArrayBuffer(self.blob.slice(self.pos, self.pos + n)).to_py()
        b[:n] = data
        self.pos += n
        return n


def install(mount="/in"):
    """open() of a file under `mount` (a WORKERFS mount) reads the browser's
    File directly."""
    import pyodide_js
    prefix = mount.rstrip("/") + "/"

    def blob_for(path):
        if not isinstance(path, str):
            return None
        path = os.path.abspath(path)
        if not path.startswith(prefix):
            return None
        try:
            node = pyodide_js.FS.lookupPath(path).node
        except Exception:   # noqa: BLE001 - not there: the usual error from open()
            return None
        contents = getattr(node, "contents", None)
        return contents if contents is not None and hasattr(contents, "slice") else None

    def opener(base):
        def open_(file, mode="r", buffering=-1, *a, **k):
            if "r" in mode and not any(c in mode for c in "wax+"):
                blob = blob_for(file)
                if blob is not None:
                    raw = BlobFile(blob, file)
                    if buffering == 0 and "b" in mode:
                        return raw
                    f = io.BufferedReader(raw, buffer_size=1 << 20)
                    if "b" in mode:
                        return f
                    return io.TextIOWrapper(f, *a, **k)
            return base(file, mode, buffering, *a, **k)
        return open_

    builtins.open = opener(_open)
    io.open = opener(_io_open)
