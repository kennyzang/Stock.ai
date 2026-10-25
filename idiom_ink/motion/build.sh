#!/bin/sh
# Build a code-animated Idiom Ink short:  build.sh EPISODE_DIR VO_DIR OUT_DIR [--skip-render]
#   EPISODE_DIR: page.html, timeline.js/json, ev.json   VO_DIR: <line id>.wav (ASR-checked)
set -e
HERE=$(cd "$(dirname "$0")" && pwd); EP=$(cd "$1" && pwd); VO=$2; OUT=$3; mkdir -p "$OUT"
NAME=$(basename "$EP")
[ "$4" = "--skip-render" ] || node "$HERE/render.mjs" "$EP/page.html" video "$OUT/video.mp4" 30
python3 "$HERE/mix.py" "$EP" "$VO" "$OUT/mix.wav"
ffmpeg -v error -y -i "$OUT/video.mp4" -i "$OUT/mix.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 22 -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-2:LRA=11,alimiter=limit=0.84:level=false" -ar 48000 -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/$NAME.mp4"
node "$HERE/render.mjs" "$EP/page.html" still 0 "$OUT/${NAME}_cover.png"
ffmpeg -nostats -i "$OUT/$NAME.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" || true
ffprobe -v error -show_entries format=duration,size -of compact "$OUT/$NAME.mp4"
