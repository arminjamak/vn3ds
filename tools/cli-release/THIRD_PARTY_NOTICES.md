# Third-party notices for the standalone vn3ds-port builds

The `vn3ds-cli-*` downloads (vn3ds-cli-mac-arm64.tar.gz, vn3ds-cli-mac-x64.tar.gz,
vn3ds-cli-windows-x64.zip) contain vn3ds's own code (see `LICENSE.txt`) and the
components below. Their full licence texts are in the `licenses/` folder next to
this file.

## FFmpeg (ffmpeg and ffprobe programs) - GNU GPL version 3

The bundled `ffmpeg` and `ffprobe` are unmodified static builds of FFmpeg 9.0.2,
configured with `--enable-gpl --enable-version3`, so they are distributed under
the **GNU General Public License, version 3** (`licenses/GPL-3.0.txt`). They are
separate programs that vn3ds-port runs; vn3ds-port itself is not a derivative of
them. Among the libraries linked into them are x264 (GPL-2.0-or-later), x265
(GPL-2.0-or-later), libvorbis and libogg (BSD-3-Clause), Opus (BSD-3-Clause),
LAME (LGPL-2.0-or-later), libvpx (BSD-3-Clause), dav1d (BSD-2-Clause) and others;
the builders' pages list them all.

| download | FFmpeg build | from |
|---|---|---|
| vn3ds-cli-mac-arm64 | 9.0.2 static, by Martin Riedl | https://ffmpeg.martin-riedl.de/ (build `1789931890_9.0.2`) |
| vn3ds-cli-mac-x64 | 9.0.2 static, by Martin Riedl | https://ffmpeg.martin-riedl.de/ (build `1789931006_9.0.2`) |
| vn3ds-cli-windows-x64 | 9.0.2 (n9.0.2-29-g6dfaba896f) win64 GPL, by BtbN | https://github.com/BtbN/FFmpeg-Builds (release `autobuild-2026-10-20-13-08`) |

**Source code.** You are entitled to the complete corresponding source code of
these FFmpeg binaries under the terms of the GPL:

- FFmpeg 9.0.2: https://ffmpeg.org/releases/ffmpeg-9.0.2.tar.xz
  (git: https://git.ffmpeg.org/ffmpeg.git, tag `n9.0.2`; the Windows build is the
  `release/9.0` branch at commit `6dfaba896f`)
- the scripts that built them, which name every library version and its source:
  https://gitlab.com/martinriedl/ffmpeg-build-script (macOS) and
  https://github.com/BtbN/FFmpeg-Builds (Windows)
- the same source archives are attached to each vn3ds release on
  https://github.com/arminjamak/vn3ds/releases (see the release notes), and are
  available on request from the vn3ds author for at least three years after the
  release.

## unrpyc - MIT

Decompiles compiled Ren'Py scripts (.rpyc). https://github.com/CensoredUsername/unrpyc
`licenses/unrpyc-MIT.txt`.

## Python 3.12 - PSF License

The Python interpreter and standard library, frozen with PyInstaller.
https://www.python.org/ `licenses/Python.txt` (includes the licences of the
libraries Python bundles, such as zlib, OpenSSL/libffi where present).

## NumPy 1.26.4 - BSD-3-Clause (with bundled OpenBLAS: BSD-3-Clause)

https://numpy.org/ `licenses/numpy.txt`.

## Pillow 10.4.0 - MIT-CMU (HPND), with bundled libjpeg-turbo, libpng, zlib, libtiff, libwebp, freetype and others

https://python-pillow.org/ `licenses/Pillow.txt`.

## PyInstaller bootloader - GPL-2.0 with the bootloader exception

The small program that starts the frozen Python. The exception allows it to be
distributed with programs under any licence. https://pyinstaller.org/
`licenses/PyInstaller.txt`.

vn3ds does not include or redistribute Ren'Py. Games you port remain under their
own licences; only port games you have the rights to.
