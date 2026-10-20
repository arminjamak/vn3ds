# vn3ds-port: the one-command route, and how its downloads are built

There are two ways to run vn3ds-port. Both do the same thing; the second needs
nothing installed.

| | what to type | needs |
|---|---|---|
| from this repository | `tools/vn3ds-port <game>` | Python 3.9+ with Pillow and numpy, ffmpeg |
| the standalone command | the one-line installer below | nothing |

## Using it

### macOS (Terminal)

```sh
curl -fsSL https://arminjamak.github.io/vn3ds/install.sh | sh -s -- 
```

Type that (the space after `--` matters), drag the visual novel (its folder,
`.zip`, `.apk` or `.app`) into the Terminal window and press Enter. Leaving the
game out works too: it then asks you to drag it in.

### Windows (PowerShell 5.1 or 7)

```powershell
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString((iwr -useb https://arminjamak.github.io/vn3ds/install.ps1).RawContentStream.ToArray()))) 
```

Type or paste that (a space at the end), drag the game into the window, press
Enter. The command reads the script as bytes and decodes it itself, so it works
in both PowerShell versions however the web server labels `.ps1` files
(GitHub Pages may send `application/octet-stream`, for which
`[scriptblock]::Create((irm ...))` can receive bytes instead of text).

### What happens

The installer downloads the standalone build for the computer
(`vn3ds-cli-mac-arm64.tar.gz`, `vn3ds-cli-mac-x64.tar.gz` or
`vn3ds-cli-windows-x64.zip`, about 80 MB, checked against its `.sha256`) from
`https://github.com/arminjamak/vn3ds/releases/latest/download/` into

- macOS: `~/Library/Application Support/vn3ds/cli/`
- Windows: `%LOCALAPPDATA%\vn3ds\cli\`

and runs `vn3ds-port` on the game. Later runs reuse it and download again only
when a new release is out (offline, the copy already there is used). Converted
games are kept in `vn3ds/games/` next to it.

`vn3ds-port` then prints numbered steps:

```
1. Converting (compact, for Wi-Fi)
   While this converts, get your 3DS ready:
   1. On the 3DS, open the Homebrew Launcher.
   2. Press Y.
   Already have vn3ds? Open it and press Y instead.
   ✓ Reading the scripts  161 labels
   ✓ Audio                250/250
   ✓ Images               644/644
   ✓ Packing              14.1 MB
2. Finding your 3DS
   ✓ Finding your 3DS     found your 3DS at 192.168.1.242 (the Homebrew Launcher)
3. Sending vn3ds
   ✓ vn3ds                vn3ds sent and started
4. Sending your game
     12.3 MB of 23.4 MB  ·  0.61 MB/s  ·  18 s left
   ✓ Your game            1303 of 1303 files sent: 21.1 MB (23.4 MB unpacked)
   vn3ds.3dsx was saved on the SD card
Done. The game is in vn3ds's list on the 3DS.
```

- **Where it goes:** the 3DS's SD card if one is plugged into the computer
  (recognised by its `Nintendo 3DS` folder or `boot.firm`): best quality, the
  game is copied (only new or changed files) and `sdmc:/3ds/vn3ds.3dsx` is
  copied when it is missing or different. Otherwise Wi-Fi, compact quality.
- **Over Wi-Fi** it converts first, then looks for the 3DS: vn3ds's receiver
  (Y in vn3ds) or the Homebrew Launcher's netloader (Y in the launcher). With
  the netloader, vn3ds itself is sent first (the same bytes devkitPro's
  `3dslink` would send) and started; it opens its receiver, and the game and
  `vn3ds.3dsx` follow in the same run, so vn3ds is saved on the card. If vn3ds
  is already open, the game is sent with `vn3ds.3dsx`, which the 3DS skips when
  its copy is the same.
- **Nothing times out.** It waits for the 3DS as long as it takes, and a
  dropped connection is retried until the transfer is complete. Only files the
  3DS doesn't have yet are sent (each one compressed when that helps), so
  stopping with Ctrl+C and running the same command again carries on where it
  stopped.
- Options: `--sd PATH` or `--3ds IP` to choose the destination, `--quality sd|wifi`,
  `--no-detect` (just build), `--no-engine`, `-o FOLDER`, and the rest in
  `vn3ds-port --help`.

### Unsigned program: first launch

The builds are not signed with an Apple or Microsoft certificate.

- **macOS:** files downloaded with `curl` (as the installer does) aren't
  quarantined, so macOS runs them without asking. If you download the
  `.tar.gz` with a browser instead, macOS refuses to open `vn3ds-port`
  ("cannot be opened because the developer cannot be verified"); either run
  `xattr -dr com.apple.quarantine <the vn3ds folder>` once, or Control-click
  `vn3ds-port`, choose **Open** and confirm (on macOS 15: try to open it, then
  **System Settings > Privacy & Security > Open Anyway**). The Apple-silicon
  build is ad-hoc signed, which arm64 Macs require.
- **Windows:** downloads made by PowerShell carry no "downloaded from the
  internet" mark, so SmartScreen doesn't step in. A browser-downloaded zip
  does: right-click it, **Properties**, tick **Unblock** before unpacking, or
  choose **More info > Run anyway** when SmartScreen appears. Antivirus
  programs sometimes flag PyInstaller programs they haven't seen before; that
  is a false positive, and signing the program is the lasting fix.

## Building the standalone command

Everything happens in this folder; `vendor/`, `work/` and `dist/` are
git-ignored.

```sh
/opt/anaconda3/bin/python3.12 -m venv .venv          # any Python 3.12; the repo root
.venv/bin/pip install -r tools/cli-release/requirements.txt   # PyInstaller 6.22.3, numpy 1.26.4, Pillow 10.4.0
make -C engine                                        # engine/vn3ds.3dsx (devkitARM)
.venv/bin/python tools/cli-release/fetch_ffmpeg.py    # ffmpeg + ffprobe for this Mac, checksums verified
.venv/bin/python tools/cli-release/build_cli.py --version 1.0.0
```

`build_cli.py` freezes `tools/cli-release/vn3ds_cli.py` with PyInstaller
(one folder, console program, the generated spec lands in `work/`). It bundles
the converter (`tools/vnpack`), unrpyc (frozen in; the converter runs it as
`vn3ds-port --vn3ds-unrpyc`), `engine/vn3ds.3dsx`, ffmpeg and ffprobe (copied
unchanged), the licences, and writes `dist/vn3ds-cli-<target>.tar.gz` (or
`.zip` on Windows) plus a `.sha256`. It refuses an ffmpeg without libx264,
libvorbis and libopus. Inside the archive:

```
vn3ds/vn3ds-port(.exe)      the program
vn3ds/_internal/            Python, the converter, engine/vn3ds.3dsx, ffmpeg/ffmpeg + ffprobe
vn3ds/README.txt, LICENSE.txt, THIRD_PARTY_NOTICES.md, licenses/
```

Each OS has to be built on that OS. macOS arm64 is built and tested here; the
release workflow (`.github/workflows/release.yml`) builds all three on a tag
push (`git tag v1.0.0 && git push --tags`):

1. builds `vn3ds.3dsx` in the devkitARM container (add the repository secret
   `LEADERBOARD_SECRET_H` with the contents of `engine/source/leaderboard_secret.h`
   for an engine with the online leaderboard; without it the leaderboard is off),
2. on macOS 15 (arm64), macOS 15 Intel and Windows: fetches the pinned ffmpeg,
   builds, converts `examples/syntax_test`, and runs the installers against a
   local server that labels every file `application/octet-stream` (install.sh
   with a path as Terminal pastes it; install.ps1 in Windows PowerShell 5.1 and
   PowerShell 7 with a quoted path, an apostrophe, brackets and a trailing
   backslash, checking the user's session stays open),
3. creates the GitHub release with the three archives, their `.sha256` files
   and the FFmpeg source tarball.

A manual run (`workflow_dispatch`) builds and tests without publishing.

### The bundled ffmpeg

All three are FFmpeg 9.0.2 static builds with libx264, libvorbis and libopus
(checked by `build_cli.py`), pinned in `fetch_ffmpeg.py`:

| target | download | SHA-256 (as published by the builder) |
|---|---|---|
| mac-arm64 | https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2/ffmpeg.zip (28.4 MB) | `c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924` |
| | https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2/ffprobe.zip (28.3 MB) | `fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6` |
| mac-x64 | https://ffmpeg.martin-riedl.de/download/macos/amd64/1789931006_9.0.2/ffmpeg.zip (33.8 MB) | `7c6b4125b191cbf773832dc51f424cf2b6bb7da43007d1e066f95909e47cacd4` |
| | https://ffmpeg.martin-riedl.de/download/macos/amd64/1789931006_9.0.2/ffprobe.zip | `2322438ed2f6319a691291b247d09c69dcaa3a982460d1f269a7e1af335cfdfd` |
| windows-x64 | https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-10-20-13-08/ffmpeg-n9.0.2-29-g6dfaba896f-win64-gpl-9.0.zip (194 MB) | `5d2804fd10e90610657375a8777611f858426f29da61bf5f0c4f8e78798a7119` |

The unpacked macOS arm64 programs: `ffmpeg` 66.3 MB, sha256
`2e11c6f90993cdb79fff84d3f90044d28316b310e75b3e030cfc9a54f2c9d384`; `ffprobe`
66.2 MB, sha256 `2738aa46a7f9acbc8ab09a6715554c90f7de603171ac403726765685df6a0059`
(signed by their builder, team KU3N25YGLU). Martin Riedl's macOS Intel builds
stop in January 2027 (his announcement); BtbN deletes old daily builds after a
while, so when that URL disappears pick the current `autobuild-*` release and
update the URL and sum from its `checksums.sha256`.

Converted files are the same bytes as the source command produces when both
use the same ffmpeg. They can differ from a conversion made with another
ffmpeg build: Homebrew's ffmpeg, for example, has no libvorbis, so audio that
needs re-encoding is made with ffmpeg's own Vorbis encoder there and with
libvorbis in the standalone build; H.264 movies depend on the x264 version;
and JPEG textures (the Wi-Fi quality) depend on Pillow's JPEG library (the
Pillow wheel from PyPI, which the builds use, has libjpeg-turbo; Anaconda's
Pillow uses libjpeg 9, which writes different, equally valid bytes). Checked:
with the same ffmpeg and the same Pillow, the frozen build and
`python -m vnpack.port` produce identical folders for examples/demo in both
qualities.

### ffmpeg, x264 and the GPL

ffmpeg built with x264 (and `--enable-gpl --enable-version3`) is licensed under
the **GPL v3**, so every release that bundles it distributes GPL software. That
means:

- each download carries the GPL text and `THIRD_PARTY_NOTICES.md`, which names
  the exact builds and where their source is;
- the corresponding source must be available to everyone who gets the binary:
  the release workflow attaches `ffmpeg-9.0.2.tar.xz` to every release, and the
  notices point to the builders' scripts, which pin every library's version
  and source. The notices also promise the source on request for three years:
  keep that promise or mirror the libraries' sources as release assets too;
- ffmpeg stays a separate program that vn3ds-port runs; vn3ds's own code keeps
  its licence. Don't link ffmpeg's libraries into vn3ds-port without
  re-checking this;
- anyone may redistribute the downloads, under the same terms.

## Testing

```sh
python3 tests/test_3dslink.py                 # the netloader framing (and against devkitPro's 3dslink if installed)
sh tests/test_cli_delivery.sh                 # SD card, Wi-Fi and vn3ds-first, all on this computer
PORT_CMD=tools/cli-release/work/package/vn3ds/vn3ds-port \
ENGINE=tools/cli-release/work/package/vn3ds/_internal/engine/vn3ds.3dsx \
    sh tests/test_cli_delivery.sh             # the same against the frozen build
```

`test_cli_delivery.sh` uses a fake SD card folder, the desktop engine
(`engine/build-host/vn3ds-host --listen`) as the 3DS's receiver on 127.0.0.1,
and `tests/fake_netloader.py` as the Homebrew Launcher. It needs port 5555
free. These environment variables keep the search on this computer (they are
read by `tools/vnpack/detect.py`):

| variable | effect |
|---|---|
| `VN3DS_VOLUMES` | extra folders to treat as possible SD cards |
| `VN3DS_SCAN_HOSTS` | hosts to probe instead of the local network (e.g. `127.0.0.1`) |
| `VN3DS_NETLOADER_ADDRESS` | where the netloader ping goes instead of the broadcast |
| `VN3DS_ENGINE` | the vn3ds.3dsx to deliver |
| `VN3DS_DOWNLOAD_URL` | where install.sh / install.ps1 download from |

`tests/serve_octet.py DIR PORT` serves a folder with every file labelled
`application/octet-stream`, for trying the installers locally.
