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

echo "Snapshot smoothness: preloads, music changes on the beat, gapless splices"
mkdir -p "$OUT/root4"; printf 'text_speed = 6\n' > "$OUT/root4/settings.cfg"   # instant text
engine/build-host/vn3ds-host "$OUT/build/snapshot" --root "$OUT/root4" --pace --no-draw --perf \
    --max-lines 400 --music-wav "$OUT/music.wav" > "$OUT/t4.txt" 2> "$OUT/p4.txt"
python3 tests/check_smoothness.py "$OUT/p4.txt" "$OUT/t4.txt" "$OUT/music.wav" > "$OUT/smooth.txt" || fail=1
grep -v "^        " "$OUT/smooth.txt"

echo "pack files (packed vs loose, update stability)"
python3 tests/test_packs.py "$OUT/build/snapshot" > "$OUT/packs.txt" 2>&1 || { grep -v "  ok:" "$OUT/packs.txt"; fail=1; }
tail -1 "$OUT/packs.txt"

echo "free roam, talk menus, the game's own functions, jump expression"
python3 tests/test_freeroam.py > "$OUT/freeroam.txt" 2>&1 || { grep -v "  ok:" "$OUT/freeroam.txt"; fail=1; }
tail -1 "$OUT/freeroam.txt"

echo "standalone app (vn3ds-port --app: romfs, SMDH, single-game mode)"
python3 tests/test_app3dsx.py "$OUT/build/snapshot" > "$OUT/app.txt" 2>&1 || { grep -v "  ok:" "$OUT/app.txt"; fail=1; }
tail -1 "$OUT/app.txt"

echo "finding the 3DS again (new IP, restart hint, not on the Wi-Fi)"
python3 tests/test_relocate.py engine/build-host/vn3ds-host "$OUT/build/syntax-test" > "$OUT/relocate.txt" 2>&1 || { grep -v "  ok:" "$OUT/relocate.txt"; fail=1; }
tail -1 "$OUT/relocate.txt"

echo "saves: Ren'Py <-> vn3ds conversion, two-way sync over Wi-Fi, installed games"
python3 tests/test_savesync.py engine/build-host/vn3ds-host > "$OUT/savesync.txt" 2>&1 || { grep -v "  ok:" "$OUT/savesync.txt"; fail=1; }
tail -1 "$OUT/savesync.txt"

echo "a dead connection never blocks the receiver (takeover, 20 s idle close)"
python3 tests/test_rx_stuck.py engine/build-host/vn3ds-host "$OUT/build/syntax-test" > "$OUT/rxstuck.txt" 2>&1 || { grep -v "  ok:" "$OUT/rxstuck.txt"; fail=1; }
tail -1 "$OUT/rxstuck.txt"

# Games from a browser (tests/test_link.py: page -> relay -> 3DS) is on hold:
# vn3ds no longer links up with the relay (app_receive_open), so the test
# would only time out. Run it by hand once the link is switched back on.

echo "3dslink (netloader) sender"
python3 tests/test_3dslink.py > "$OUT/3dslink.txt" 2>&1 || { grep -v "  ok:" "$OUT/3dslink.txt"; fail=1; }
tail -1 "$OUT/3dslink.txt"

echo "JPEG textures"
python3 tests/test_jpeg.py > "$OUT/jpeg.txt" 2>&1 || { grep -v "  ok:" "$OUT/jpeg.txt"; fail=1; }
tail -1 "$OUT/jpeg.txt"

echo "stereoscopic movies (--video-3d)"
python3 tests/test_stereo_video.py > "$OUT/stereo.txt" 2>&1 || { grep -v "  ok:" "$OUT/stereo.txt"; fail=1; }
tail -1 "$OUT/stereo.txt"
echo "movies through another encoder (a web page's: prefetch, same .cvh)"
python3 tests/test_movie_hook.py > "$OUT/moviehook.txt" 2>&1 || { grep -v "  ok:" "$OUT/moviehook.txt"; fail=1; }
tail -1 "$OUT/moviehook.txt"

echo "an .rpa compressed inside a .zip download, read in place"
python3 tests/test_zip_archive.py > "$OUT/ziparc.txt" 2>&1 || { grep -v "  ok:" "$OUT/ziparc.txt"; fail=1; }
tail -1 "$OUT/ziparc.txt"

echo "CG patches (--cg-patches)"
python3 tests/test_cg_patches.py > "$OUT/cgp.txt" 2>&1 || { grep -v "  ok:" "$OUT/cgp.txt"; fail=1; }
tail -1 "$OUT/cgp.txt"

echo "ported minigames (call screen -> native lockpick, instrument, timing, captions; overlays; outcome cards)"
mkdir -p "$OUT/ported"
cp -R tests/ported/game "$OUT/ported/game"
python3 tests/ported/make_assets.py "$OUT/ported"
tools/vnpack.sh "$OUT/ported" -o "$OUT/build" -q --no-audio
engine/build-host/vn3ds-host "$OUT/build/ported-test" --root "$OUT/root_ported1" --mg-seed 1 > "$OUT/tp1.txt" 2>&1
check "$OUT/tp1.txt" "The vault opened."
check "$OUT/tp1.txt" "A rising tune."
check "$OUT/tp1.txt" "You plucked 8 strings: lhlhlhlh."
check "$OUT/tp1.txt" "Points: 1."
check "$OUT/tp1.txt" "The tape ended."
check "$OUT/tp1.txt" "[hud] overlay @"
check "$OUT/tp1.txt" "Log one heard: False."
check "$OUT/tp1.txt" "You caught a fish."
check "$OUT/tp1.txt" "You won the dice."
engine/build-host/vn3ds-host "$OUT/build/ported-test" --root "$OUT/root_ported3" --mg-seed 1 \
    --hud-at 7 > "$OUT/tp3.txt" 2>&1
check "$OUT/tp3.txt" "[hud] pressed the overlay button"
check "$OUT/tp3.txt" "Log one heard: True."
engine/build-host/vn3ds-host "$OUT/build/ported-test" --root "$OUT/root_ported2" --mg-seed 1 \
    --mg-input "0.5:a:2,3:right:1.3,4.5:a:2,7:b:1,7.5:a" > "$OUT/tp2.txt" 2>&1
check "$OUT/tp2.txt" "The vault stayed shut."
check "$OUT/tp2.txt" "You plucked 2 strings: lh."
check "$OUT/tp2.txt" "Points: -1."
check "$OUT/tp2.txt" "The tape ended."

echo "screen language -> Python, the interpreter's dialect, the screen runtime (CPython)"
python3 tests/test_screenlang.py > "$OUT/screenlang.txt" 2>&1 || { grep -v "  ok:" "$OUT/screenlang.txt"; fail=1; }
tail -1 "$OUT/screenlang.txt"

echo "the game's own screens and Python (a minigame class, timers, keys, an overlay with a menu)"
tools/vnpack.sh tests/pyscreens -o "$OUT/build" -q --no-audio
engine/build-host/vn3ds-host "$OUT/build/pyscreens" --root "$OUT/root_py" \
    --mg-input "1.5:a,1.7:a,2.2:b" --hud-at 3 > "$OUT/tpy.txt" 2>&1
check "$OUT/tpy.txt" "The minigame returned 10, score 20."
check "$OUT/tpy.txt" '[hud] screen button shown: "Phone"'
check "$OUT/tpy.txt" "Flag is True."
check "$OUT/tpy.txt" "You won."
if grep -q "This line must not be reached" "$OUT/tpy.txt"; then echo "  a screen's Jump fell through"; fail=1; fi
if grep -q "left out\|\[pyscreen\].*Error" "$OUT/tpy.txt" && ! grep -q "0 left out" "$OUT/tpy.txt"; then
    echo "  the screens' Python didn't all load"; grep "\[pyscreen\]" "$OUT/tpy.txt"; fail=1
fi

[ $fail = 0 ] && echo "all tests passed" || { echo "FAILED"; exit 1; }
