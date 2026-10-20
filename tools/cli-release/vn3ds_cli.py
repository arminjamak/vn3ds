"""Entry point of the standalone vn3ds-port build (PyInstaller).

The same command as tools/vn3ds-port, with Python, the converter, unrpyc,
vn3ds.3dsx and ffmpeg/ffprobe inside. It also answers two internal flags:
  --vn3ds-unrpyc ARGS   run the bundled unrpyc (the converter calls this,
                        as there is no separate Python to run it with)
  --version             print the build's version
"""

import multiprocessing
import os
import sys


def main():
    multiprocessing.freeze_support()   # unrpyc's worker processes start here too
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    tools = os.path.join(base, "ffmpeg")
    if os.path.isdir(tools):   # the bundled ffmpeg and ffprobe come first
        os.environ["PATH"] = tools + os.pathsep + os.environ.get("PATH", "")
    if len(sys.argv) > 1 and sys.argv[1] == "--vn3ds-unrpyc":
        from vnpack import port
        port.run_unrpyc(sys.argv[2:])
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        try:
            import vn3ds_build
            print(f"vn3ds-port {vn3ds_build.VERSION}")
        except ImportError:
            print("vn3ds-port (development build)")
        return
    from vnpack import port
    port.main()


if __name__ == "__main__":
    main()
