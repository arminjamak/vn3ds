#!/bin/sh
# The vn3ds Mac app as a downloadable disk image, without Xcode.
#
#   apps/mac/build_dmg.sh            ->  apps/mac/dist/vn3ds.dmg
#   apps/mac/build_dmg.sh --dev      ->  apps/mac/dist/vn3ds.app only, running the
#                                        converter from this repository (quick to try)
#
# The full build puts everything inside the app: the frozen converter
# (tools/cli-release/build_cli.py: Python, vnpack, unrpyc, ffmpeg and
# engine/vn3ds.3dsx), vn3ds.cia for FBI (engine/cia/build_cia.sh) and the
# ported Snapshot (build/snapshot). Each is built first when missing;
# REBUILD_CONVERTER=1 freezes the converter again. Needs the Swift command line tools
# (xcode-select --install), the project's .venv with PyInstaller, numpy and
# Pillow, and devkitPro's build of the engine.
#
# The app is signed ad hoc, not notarised: the first time, open it with a
# right-click > Open (or set DEVELOPER_ID to a "Developer ID Application"
# identity to sign it properly; notarise the .dmg with notarytool after).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DIST="$HERE/dist"
# assembled and signed outside the repository: an iCloud-synced folder keeps
# adding Finder metadata, which codesign refuses
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
APP="$STAGE/vn3ds.app"
DEV=0
[ "$1" = "--dev" ] && DEV=1
PY="$REPO/.venv/bin/python3"
[ -x "$PY" ] || PY=python3

echo "== the app"
(cd "$HERE" && swift build -c release --arch arm64)
BIN="$(cd "$HERE" && swift build -c release --arch arm64 --show-bin-path)/VN3DSPort"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN" "$APP/Contents/MacOS/vn3ds"
"$PY" "$HERE/make_icon.py" "$APP/Contents/Resources/AppIcon.icns"
VERSION="$(cd "$REPO" && git describe --tags --always 2>/dev/null || echo dev)"
DEVKEY=""
[ $DEV = 1 ] && DEVKEY="<key>VN3DSRepo</key><string>$REPO</string>"
cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>vn3ds</string>
  <key>CFBundleDisplayName</key><string>vn3ds</string>
  <key>CFBundleIdentifier</key><string>io.github.arminjamak.vn3ds</string>
  <key>CFBundleExecutable</key><string>vn3ds</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleVersion</key><string>$VERSION</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSLocalNetworkUsageDescription</key><string>vn3ds finds your 3DS on the Wi-Fi and sends games to it.</string>
  $DEVKEY
</dict></plist>
EOF

if [ $DEV = 0 ]; then
    echo "== vn3ds.cia"
    [ -f "$REPO/engine/vn3ds.cia" ] || "$REPO/engine/cia/build_cia.sh"
    cp "$REPO/engine/vn3ds.cia" "$APP/Contents/Resources/"
    echo "== Snapshot (the route step's \"Also send Snapshot\")"
    [ -f "$REPO/build/snapshot/game.bin" ] || "$REPO/tools/vn3ds-port" "$REPO/examples/demo" --no-detect
    mkdir -p "$APP/Contents/Resources/snapshot"
    (cd "$REPO/build/snapshot" && tar cf - --exclude port-report.txt .) |
        (cd "$APP/Contents/Resources/snapshot" && tar xf -)
    echo "== the converter"
    PKG="$REPO/tools/cli-release/work/package/vn3ds"
    if [ ! -x "$PKG/vn3ds-port" ] || [ "$REBUILD_CONVERTER" = 1 ]; then
        "$PY" "$REPO/tools/cli-release/build_cli.py"
    fi
    cp -R "$PKG" "$APP/Contents/Resources/port"
fi

echo "== signing"
xattr -cr "$APP" 2>/dev/null || true
ID="${DEVELOPER_ID:--}"
OPTS=""
[ "$ID" != "-" ] && OPTS="--options runtime --timestamp"
# inside out: the converter's libraries and programs, then the app
find "$APP/Contents/Resources" -type f \( -name "*.dylib" -o -name "*.so" -o -perm -111 \) \
    -exec codesign --force $OPTS -s "$ID" {} \; 2>/dev/null || true
codesign --force $OPTS -s "$ID" "$APP"

codesign --verify --deep "$APP"
mkdir -p "$DIST"
rm -rf "$DIST/vn3ds.app"
ditto "$APP" "$DIST/vn3ds.app"
if [ $DEV = 1 ]; then
    echo "built $DIST/vn3ds.app (development: runs the converter from $REPO)"
    exit 0
fi
echo "== the disk image"
ln -s /Applications "$STAGE/Applications"
rm -f "$DIST/vn3ds.dmg"
hdiutil create -quiet -volname "vn3ds" -srcfolder "$STAGE" -fs HFS+ -format UDZO "$DIST/vn3ds.dmg"
[ "$ID" != "-" ] && codesign -s "$ID" "$DIST/vn3ds.dmg"
echo "built $DIST/vn3ds.dmg ($(du -h "$DIST/vn3ds.dmg" | cut -f1))"
