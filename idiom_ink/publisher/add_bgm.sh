#!/usr/bin/env bash
# Usage: add_bgm.sh IN.mp4 OUT.mp4   (needs ffmpeg + python3 with numpy)
# Mixes an original synthesized D-pentatonic loop (bgm_synth.py) under the narration:
# music ~13 dB under speech on average, ducked by a mild sidechain compressor, video stream copied untouched.
set -euo pipefail
IN="$1"; OUT="$2"; D=$(dirname "$0"); T=$(mktemp -d)
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
python3 -I "$D/bgm_synth.py" "$T/bgm.wav" "$(python3 -c "print(float('$DUR')+2)")" >/dev/null
ffmpeg -hide_banner -loglevel error -y -i "$IN" -i "$T/bgm.wav" -filter_complex \
"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.75[m];[0:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[vo][sc];[m][sc]sidechaincompress=threshold=0.03:ratio=2:attack=20:release=400:makeup=1[md];[vo][md]amix=inputs=2:duration=first:weights='1 1':normalize=0,alimiter=limit=0.97[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -rf "$T"
