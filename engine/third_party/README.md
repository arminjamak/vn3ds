# Third-party code in the engine

Built by `Makefile` (3DS) and `Makefile.host` (desktop) through `opus.mk`,
with their own flags and warnings off. Only the files the decoder needs are
here; tests, docs, the encoders, the platform-specific SIMD code other than
the ARM inline-assembly headers, and the DNN models (deep PLC, DRED, OSCE)
are left out.

| Folder      | Version | Source                                                        | SHA-256 of the release tarball                                     | License                  |
|-------------|---------|---------------------------------------------------------------|--------------------------------------------------------------------|--------------------------|
| `opus/`     | 1.5.2   | https://downloads.xiph.org/releases/opus/opus-1.5.2.tar.gz     | `65c1d2f78b9f2fb20082c38cbe47c951ad5839345876e46941612ee87f9a7ce1` | BSD-3-Clause, `opus/COPYING` |
| `pocketpy/` | 2.2.0   | https://github.com/pocketpy/pocketpy/releases/tag/v2.2.0 (`pocketpy.c`, `pocketpy.h`; `LICENSE` from the tag) | `pocketpy.c` `0f0c19071b4fd0b37cb292e15bea49ca163f151af901b00893d3a2005bb056e6`, `pocketpy.h` `43864cfa090d65b80915467900430dfae52c769f13d6edb137d0227d1fbe03ad` | MIT, `pocketpy/LICENSE` |
| `opusfile/` | 0.12    | https://downloads.xiph.org/releases/opus/opusfile-0.12.tar.gz  | `118d8601c12dd6a44f52423e68ca9083cc9f2bfe72da7a8c1acb22a80ae3550b` | BSD-3-Clause, `opusfile/COPYING` |

The checksums match xiph's `SHA256SUMS.txt` next to the tarballs and the
release notes on GitHub (xiph/opus v1.5.2, xiph/opusfile v0.12). The files
are unmodified copies from those tarballs.

## Build configuration

libopus: `FIXED_POINT OPUS_BUILD DISABLE_FLOAT_API USE_ALLOCA HAVE_LRINTF
HAVE_LRINT`, decoder sources only (CELT, SILK, the multistream decoder),
no `ENABLE_DEEP_PLC` / `ENABLE_DRED` / `ENABLE_OSCE`. On the 3DS also
`OPUS_ARM_INLINE_ASM OPUS_ARM_INLINE_EDSP OPUS_ARM_INLINE_MEDIA`: the
ARMv5E/ARMv6 multiply-accumulate macros in `celt/arm/*.h` and `silk/arm/*.h`
(no external `.s` files, no run-time CPU detection).

opusfile: `OP_FIXED_POINT OP_DISABLE_FLOAT_API OP_HAVE_LRINTF`, without
`http.c` / `wincerts.c` (no `OP_ENABLE_HTTP`), against libogg (3DS portlib
`3ds-libogg`; on the desktop `pkg-config ogg`).

To update: download the new tarballs, check their SHA-256 against xiph's
`SHA256SUMS.txt`, copy the same file list over (see `opus.mk` for the `.c`
files; the headers are the ones they include), and update this table.

pocketpy: the two amalgamated release files, unmodified, built with warnings
off as one object (`libvnpy.a` on the 3DS, `build-host/tp/pocketpy.o` on the
desktop); on the 3DS with `PK_ENABLE_OS=0` (no `os` module). It runs a game's
own screens and Python (`source/pyscreen.c`).
