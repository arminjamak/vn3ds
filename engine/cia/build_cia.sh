#!/bin/sh
# vn3ds.cia: vn3ds as an installable title for FBI (the Mac app's QR code).
#
#   engine/cia/build_cia.sh          (after `make` in engine/)
#
# Needs makerom and bannertool. The first run fetches them into
# engine/cia/tools/: makerom's macOS (or, in CI, Linux) release from
# 3DSGuy/Project_CTR, and bannertool (diasurgical/bannertool, no macOS
# release) built from source.
# The same engine/vn3ds.elf that becomes vn3ds.3dsx becomes the CIA; as a
# title it has no .3dsx path, so it always opens its library.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ENGINE="$HERE/.."
TOOLS="$HERE/tools"
OUT="${1:-$ENGINE/vn3ds.cia}"
mkdir -p "$TOOLS"

if [ ! -x "$TOOLS/makerom" ]; then
    arch=$(uname -m); [ "$arch" = arm64 ] || arch=x86_64
    os=macos; [ "$(uname -s)" = Linux ] && os=ubuntu
    echo "fetching makerom"
    curl -fsSL -o "$TOOLS/makerom.zip" \
        "https://github.com/3DSGuy/Project_CTR/releases/download/makerom-v0.19.0/makerom-v0.19.0-${os}_$arch.zip"
    (cd "$TOOLS" && unzip -oq makerom.zip makerom && rm makerom.zip && chmod +x makerom)
fi
if [ ! -x "$TOOLS/bannertool" ]; then
    echo "building bannertool"
    rm -rf "$TOOLS/bannertool-src"
    git clone -q --depth 1 https://github.com/diasurgical/bannertool.git "$TOOLS/bannertool-src"
    (cd "$TOOLS/bannertool-src" && mkdir -p o &&
     for f in source/pc/stb_image.c source/pc/stb_vorbis.c; do
         cc -O2 -w -c "$f" -o "o/$(basename "$f").o"; done &&
     for f in source/*.cpp source/pc/*.cpp source/3ds/*.cpp; do
         c++ -std=c++11 -O2 -w -Isource -DVERSION_MAJOR=1 -DVERSION_MINOR=2 -DVERSION_MICRO=0 \
             -c "$f" -o "o/$(basename "$f").o"; done &&
     c++ o/*.o -o "$TOOLS/bannertool")
    rm -rf "$TOOLS/bannertool-src"
fi

[ -f "$ENGINE/vn3ds.elf" ] || { echo "engine/vn3ds.elf isn't built yet: run make in engine/"; exit 1; }
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
"$TOOLS/bannertool" makebanner -i "$HERE/banner.png" -a "$HERE/banner.wav" -o "$WORK/banner.bnr" >/dev/null
"$TOOLS/bannertool" makesmdh -s "vn3ds" -l "vn3ds - Ren'Py visual novels in stereoscopic 3D" \
    -p "vn3ds" -i "$ENGINE/icon.png" -o "$WORK/icon.icn" >/dev/null
"$TOOLS/makerom" -f cia -o "$OUT" -elf "$ENGINE/vn3ds.elf" -rsf "$HERE/vn3ds.rsf" \
    -target t -exefslogo -icon "$WORK/icon.icn" -banner "$WORK/banner.bnr" \
    -major 1 -minor 0 -micro 0 \
    -DAPP_TITLE="vn3ds" -DAPP_PRODUCT_CODE="CTR-H-VN3D" -DAPP_UNIQUE_ID="0xFB3D5" \
    -DAPP_SYSTEM_MODE="64MB" -DAPP_SYSTEM_MODE_EXT="124MB" -DAPP_CATEGORY="Application" \
    -DAPP_USE_ON_SD="true" -DAPP_MEMORY_TYPE="Application" -DAPP_CPU_SPEED="804MHz" \
    -DAPP_ENABLE_L2_CACHE="true" -DAPP_VERSION_MAJOR="1" -DAPP_ENCRYPTED="false"
echo "built $OUT ($(wc -c < "$OUT" | tr -d ' ') bytes)"
