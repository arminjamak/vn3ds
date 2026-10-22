# Third-party components

| component | where | licence |
|---|---|---|
| unrpyc (decompiler for compiled Ren'Py scripts) | `tools/third_party/unrpyc/` | MIT, see its `LICENSE` |
| libopus 1.5.2 and opusfile 0.12 (Opus decoder, Xiph.Org), compiled into the 3DS and desktop builds | `engine/third_party/` | BSD-3-Clause, see the `COPYING` files and `README.md` there |
| pocketpy 2.2.0 (Python interpreter that runs a game's own screens and Python), compiled into the 3DS and desktop builds | `engine/third_party/pocketpy/` | MIT, see its `LICENSE` |
| Aileron font (baked into the desktop test build's glyph atlas) | `engine/host/font_data.h` | CC0 / public domain (bundled with Pillow) |
| buildtools `3ds/template.rsf` (Steveice10), the CIA's title settings | `engine/cia/vn3ds.rsf` | MIT, notice in the file |
| makerom (3DSGuy/Project_CTR) and bannertool (diasurgical), fetched by `engine/cia/build_cia.sh` to build `vn3ds.cia`; not in the repository or the app | `engine/cia/tools/` | MIT |
| 1921–1925 recordings sampled in the Snapshot soundtrack | `examples/music/samples/` | public domain, see `CREDITS.md` there |

The 3DS build (`vn3ds.3dsx`) links, statically:

| library | licence |
|---|---|
| libctru, citro3d, citro2d (devkitPro) | zlib |
| Tremor / libvorbisidec, libogg (Xiph.Org) | BSD-3-Clause |
| libopus, opusfile (Xiph.Org, vendored in `engine/third_party/`) | BSD-3-Clause |
| pocketpy (blueloveTH, vendored in `engine/third_party/pocketpy/`) | MIT |
| zlib | zlib |

vn3ds does not include or redistribute Ren'Py. Games you port remain under
their own licences; only port games you have the rights to.
