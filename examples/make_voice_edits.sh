#!/bin/bash
# Renders Snapshot's voice-edit clips (ch1_edit, ch3_voices_edit) from
# demo/game/audio/voices.ogg into demo/game/audio/edit/. Needs ffmpeg.
set -e
cd "$(dirname "$0")/demo/game/audio"
mkdir -p edit && cd edit
SRC=../voices.ogg
Q=(-c:a vorbis -strict -2 -b:a 96k -ar 32000 -ac 2)
ffmpeg -v error -y -ss 16 -t 4 -i $SRC -af "afade=t=in:d=0.2,afade=t=out:st=3.6:d=0.4" "${Q[@]}" voice_raw.ogg
ffmpeg -v error -y -ss 16 -t 4 -i $SRC -af "asetrate=32000*1.9,aresample=32000,afade=t=out:st=1.8:d=0.3" "${Q[@]}" voice_fast.ogg
ffmpeg -v error -y -ss 16 -t 1.4 -i $SRC -filter_complex "[0:a]asplit=2[f][r0];[r0]areverse[r];[f]asplit=2[f1][f2];[r]asplit=2[r1][r2];[f1][r1][f2][r2]concat=n=4:v=0:a=1,afade=t=out:st=5.2:d=0.4" "${Q[@]}" voice_pingpong.ogg
ffmpeg -v error -y -ss 16.5 -t 0.38 -i $SRC -af "aloop=loop=9:size=12160,afade=t=out:st=3.4:d=0.4" "${Q[@]}" voice_loop.ogg
ffmpeg -v error -y -ss 16.5 -t 0.42 -i $SRC -filter_complex "[0:a]asplit=6[a][b][c][d][e][f];[a]asetrate=32000*1.0,aresample=32000[n1];[b]asetrate=32000*1.26,aresample=32000[n2];[c]asetrate=32000*1.5,aresample=32000[n3];[d]asetrate=32000*1.26,aresample=32000[n4];[e]asetrate=32000*1.0,aresample=32000[n5];[f]asetrate=32000*0.75,aresample=32000,apad=pad_dur=0.6[n6];[n1][n2][n3][n4][n5][n6]concat=n=6:v=0:a=1" "${Q[@]}" voice_melody.ogg
