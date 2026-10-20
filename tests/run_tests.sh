#!/bin/sh
# Packs the example games, plays them in the desktop build and checks the
# transcripts. Run from the repository root: sh tests/run_tests.sh
set -e
cd "$(dirname "$0")/.."
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT

make -s -C engine -f Makefile.host
[ -f examples/demo/game/images/"bg room.png" ] || python3 examples/make_demo_assets.py
tools/vnpack.sh examples/demo -o "$OUT/build" -q
tools/vnpack.sh examples/syntax_test -o "$OUT/build" -q

fail=0
check() { # transcript, expected line
    if grep -qF -- "$2" "$1"; then echo "  ok: $2"; else echo "  MISSING: $2"; fail=1; fi
}

echo "Snapshot tutorial, first path"
engine/build-host/vn3ds-host "$OUT/build/snapshot" --root "$OUT/root1" --choices 0 --max-lines 20 > "$OUT/t1.txt"
check "$OUT/t1.txt" "Mira: That's the pop-up book effect."
check "$OUT/t1.txt" "Aron: Watch this."
check "$OUT/t1.txt" "Commander Seraphiel: Calibration complete."

echo "Snapshot tutorial, second path with save/load"
engine/build-host/vn3ds-host "$OUT/build/snapshot" --root "$OUT/root2" --choices 1,1 --test-save --max-lines 16 > "$OUT/t2.txt"
check "$OUT/t2.txt" "[test] loaded slot 1: PASS"
check "$OUT/t2.txt" "Push the slider on the right edge"

echo "syntax test"
engine/build-host/vn3ds-host "$OUT/build/syntax-test" --root "$OUT/root3" --choices 0,0,1 > "$OUT/t3.txt"
check "$OUT/t3.txt" 'small screen. And this part was extended."'
check "$OUT/t3.txt" "Eileen: \"Score is 20, bonus 1, flags 'a'.\""
check "$OUT/t3.txt" "Inside a local label."
check "$OUT/t3.txt" "Loop iteration 3."
check "$OUT/t3.txt" "Loop finished correctly."
check "$OUT/t3.txt" "You picked visible."
check "$OUT/t3.txt" "Kim: My name comes from a variable."
check "$OUT/t3.txt" "Formatting: -1 / KIM / kim."
check "$OUT/t3.txt" "f-string: score=-1"
check "$OUT/t3.txt" "The End"
check "$OUT/t3.txt" "Name Orion, echo nnn, part ri."
check "$OUT/t3.txt" "-> Left (top left)"
check "$OUT/t3.txt" "Went left."
if grep -q "This line must not be reached" "$OUT/t3.txt"; then echo "  call screen fell through"; fail=1; fi
if grep -q "This should never show" "$OUT/t3.txt"; then echo "  hidden menu option was shown"; fail=1; fi

echo "3dslink (netloader) sender"
python3 tests/test_3dslink.py > "$OUT/3dslink.txt" 2>&1 || { grep -v "  ok:" "$OUT/3dslink.txt"; fail=1; }
tail -1 "$OUT/3dslink.txt"

echo "JPEG textures"
python3 tests/test_jpeg.py > "$OUT/jpeg.txt" 2>&1 || { grep -v "  ok:" "$OUT/jpeg.txt"; fail=1; }
tail -1 "$OUT/jpeg.txt"

echo "CG patches (--cg-patches)"
python3 tests/test_cg_patches.py > "$OUT/cgp.txt" 2>&1 || { grep -v "  ok:" "$OUT/cgp.txt"; fail=1; }
tail -1 "$OUT/cgp.txt"

[ $fail = 0 ] && echo "all tests passed" || { echo "FAILED"; exit 1; }
