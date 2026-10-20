# Third-party components

| component | where | licence |
|---|---|---|
| unrpyc (decompiler for compiled Ren'Py scripts) | `tools/third_party/unrpyc/` | MIT, see its `LICENSE` |
| Aileron font (baked into the desktop test build's glyph atlas) | `engine/host/font_data.h` | CC0 / public domain (bundled with Pillow) |
| 1921–1925 recordings sampled in the Snapshot soundtrack | `examples/music/samples/` | public domain, see `CREDITS.md` there |

The 3DS build (`vn3ds.3dsx`) links, statically:

| library | licence |
|---|---|
| libctru, citro3d, citro2d (devkitPro) | zlib |
| Tremor / libvorbisidec, libogg (Xiph.Org) | BSD-3-Clause |
| zlib | zlib |

vn3ds does not include or redistribute Ren'Py. Games you port remain under
their own licences; only port games you have the rights to.
