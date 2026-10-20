#!/bin/sh
# Plays every Snapshot ending (routes and the seven systems in both
# flavours) through the desktop build and checks each reaches the end.
#   sh tests/run_routes.sh
set -e
cd "$(dirname "$0")/.."
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
make -s -C engine -f Makefile.host
mkdir -p "$OUT/proj"
cp -R examples/demo/game "$OUT/proj/game"
cp tests/snapshot/route_tests.rpy "$OUT/proj/game/zz_route_tests.rpy"
tools/vnpack.sh "$OUT/proj" -o "$OUT/build" -q --no-audio
mkdir -p "$OUT/root"
printf 'text_speed = 6\n' > "$OUT/root/settings.cfg"   # instant text
fail=0
# engine notices that are not problems
benign='leaderboard: offline\|open [a-z0-9-]*: \|removed [0-9]* files'
problems() { grep -E "ERROR|\[log\]" "$1" | grep -v "$benign"; }
for label in $(grep -oE '^label (ch4_test_[a-z_]+)' tests/snapshot/route_tests.rpy | cut -d' ' -f2); do
    engine/build-host/vn3ds-host "$OUT/build/snapshot" --label "$label" --root "$OUT/root" > "$OUT/t.txt" 2>&1 || true
    if problems "$OUT/t.txt" > /dev/null || ! grep -q "Did the birds just stop moving" "$OUT/t.txt"; then
        echo "  FAIL $label"; problems "$OUT/t.txt" | head -3; fail=1
    else
        echo "  ok   $label ($(grep -vcE '^\s+\[' "$OUT/t.txt") lines)"
    fi
done
[ $fail = 0 ] && echo "all routes reach the end" || { echo FAILED; exit 1; }
