#!/bin/sh
# End-to-end test of vn3ds-port's default flow, all on this computer:
#   1. a fake SD card (found automatically): best quality, vn3ds.3dsx + game
#   2. Wi-Fi to the desktop engine's receiver (--3ds 127.0.0.1); a second
#      send must transfer nothing
#   3. the engine-first flow: a fake Homebrew Launcher netloader takes
#      vn3ds.3dsx, "starts" it (the desktop engine with --listen), then the
#      game follows in the same run
# Nothing is sent to a real 3DS: the network search is pointed at 127.0.0.1.
#
#   sh tests/test_cli_delivery.sh                    # the source command
#   PORT_CMD=path/to/vn3ds-port ENGINE=path/to/vn3ds.3dsx sh tests/test_cli_delivery.sh
set -e
cd "$(dirname "$0")/.."
REPO=$(pwd)
PORT_CMD=${PORT_CMD:-$REPO/tools/vn3ds-port}
ENGINE=${ENGINE:-$REPO/engine/vn3ds.3dsx}
HOST=$REPO/engine/build-host/vn3ds-host
OUT=${OUT:-$(mktemp -d)}
mkdir -p "$OUT"
# a copy, so a rebuild of the engine during the test doesn't change it
cp "$ENGINE" "$OUT/vn3ds.3dsx"
ENGINE=$OUT/vn3ds.3dsx
export VN3DS_ENGINE=$ENGINE VN3DS_SCAN_HOSTS=127.0.0.1 VN3DS_NETLOADER_ADDRESS=127.0.0.1
make -s -C engine -f Makefile.host
fail=0
ok() { echo "  ok: $1"; }
bad() { echo "  FAIL: $1"; fail=1; }
same_game() { # built folder, delivered folder: the same files, byte for byte
    if python3 - "$1" "$2" > "$OUT/diff.txt" <<'PY'
import filecmp, os, sys
a, b = sys.argv[1:]
def files(d):
    return {os.path.relpath(os.path.join(r, f), d) for r, _, fs in os.walk(d) for f in fs
            if f != "prune.flag"}
fa, fb = files(a), files(b)
bad = sorted(fa ^ fb) + [f for f in sorted(fa & fb)
                         if not filecmp.cmp(os.path.join(a, f), os.path.join(b, f), shallow=False)]
print("\n".join(bad))
sys.exit(1 if bad else 0)
PY
    then ok "$3"; else bad "$3"; head -5 "$OUT/diff.txt"; fi
}
port_free() {
    if netstat -an -p tcp 2>/dev/null | grep -qE "[.:]5555 .*LISTEN"; then
        echo "  port 5555 is in use by another program; stop it and run again"; exit 1
    fi
}
start_host() { # root
    port_free
    mkdir -p "$1" "$1.shots"
    "$HOST" --root "$1" --home --listen --out "$1.shots" > "$1.log" 2>&1 &
    HOST_PID=$!
    sleep 1
}
wait_host() { wait "$HOST_PID" 2>/dev/null || true; }

echo "Reference builds"
"$PORT_CMD" examples/demo --no-detect --quality sd -o "$OUT/ref-sd" > "$OUT/ref-sd.log" 2>&1
"$PORT_CMD" examples/syntax_test --no-detect --quality wifi -o "$OUT/ref-wifi" > "$OUT/ref-wifi.log" 2>&1
ok "built"

echo "1. Fake SD card"
mkdir -p "$OUT/sd/Nintendo 3DS" "$OUT/sd/3ds"
VN3DS_VOLUMES="$OUT/sd" "$PORT_CMD" examples/demo -o "$OUT/b-sd" > "$OUT/sd1.log" 2>&1
grep -q "Copying to the SD card" "$OUT/sd1.log" && ok "found the card" || bad "found the card"
grep -q "best quality" "$OUT/sd1.log" && ok "best quality" || bad "best quality"
same_game "$OUT/ref-sd/snapshot" "$OUT/sd/3ds/vn3ds/games/snapshot" "game on the card, byte-identical"
cmp -s "$ENGINE" "$OUT/sd/3ds/vn3ds.3dsx" && ok "vn3ds.3dsx on the card" || bad "vn3ds.3dsx on the card"
VN3DS_VOLUMES="$OUT/sd" "$PORT_CMD" examples/demo -o "$OUT/b-sd" > "$OUT/sd2.log" 2>&1
grep -q "already on the card" "$OUT/sd2.log" && grep -q "up to date" "$OUT/sd2.log" \
    && ok "second run copies nothing" || bad "second run copies nothing"

echo "2. Wi-Fi to the desktop engine"
start_host "$OUT/wifi/3ds/vn3ds"
"$PORT_CMD" examples/syntax_test --3ds 127.0.0.1 -o "$OUT/b-wifi" > "$OUT/wifi1.log" 2>&1
wait_host
grep -q "compact, for Wi-Fi" "$OUT/wifi1.log" && ok "compact quality" || bad "compact quality"
same_game "$OUT/ref-wifi/syntax-test" "$OUT/wifi/3ds/vn3ds/games/syntax-test" "game received, byte-identical"
cmp -s "$ENGINE" "$OUT/wifi/3ds/vn3ds.3dsx" && ok "vn3ds.3dsx received" || bad "vn3ds.3dsx received"
start_host "$OUT/wifi/3ds/vn3ds"
"$PORT_CMD" "$OUT/b-wifi/syntax-test" --3ds 127.0.0.1 > "$OUT/wifi2.log" 2>&1
wait_host
grep -q "nothing to send" "$OUT/wifi2.log" && ok "second send transfers nothing" || bad "second send transfers nothing"

echo "3. vn3ds first, through the Homebrew Launcher's netloader"
port_free
mkdir -p "$OUT/nl/3ds/vn3ds" "$OUT/nl.shots"
python3 tests/fake_netloader.py --save "$OUT/nl/netloaded.3dsx" --then \
    "$HOST" --root "$OUT/nl/3ds/vn3ds" --home --listen --out "$OUT/nl.shots" > "$OUT/nl.log" 2>&1 &
NL_PID=$!
sleep 1
"$PORT_CMD" examples/syntax_test -o "$OUT/b-nl" > "$OUT/nl1.log" 2>&1
wait "$NL_PID" 2>/dev/null || true
grep -q "the Homebrew Launcher" "$OUT/nl1.log" && ok "found the netloader" || bad "found the netloader"
grep -q "vn3ds sent and started" "$OUT/nl1.log" && ok "vn3ds sent and started" || bad "vn3ds sent and started"
cmp -s "$ENGINE" "$OUT/nl/netloaded.3dsx" && ok "netloader got vn3ds.3dsx intact" || bad "netloader got vn3ds.3dsx intact"
grep -q "3dslink:/vn3ds.3dsx" "$OUT/nl.log" && ok "argv[0] 3dslink:/vn3ds.3dsx" || bad "argv[0]"
same_game "$OUT/ref-wifi/syntax-test" "$OUT/nl/3ds/vn3ds/games/syntax-test" "then the game, byte-identical"
cmp -s "$ENGINE" "$OUT/nl/3ds/vn3ds.3dsx" && ok "vn3ds saved to the card" || bad "vn3ds saved to the card"

[ $fail = 0 ] && echo "delivery: all passed ($OUT)" || { echo "delivery: FAILED (logs in $OUT)"; exit 1; }
