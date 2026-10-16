#!/usr/bin/env bash
# Runs on the GPU server. Copy finished H3 clips of an episode into its clips/ folder (dropping the _00001_ suffix)
# and make a review contact sheet for each new one.
# Usage: collect_clips.sh epNN NN_slug          e.g. collect_clips.sh ep06 06_gua-tian-li-xia
set -euo pipefail
ep=$1 slug=$2
src=/root/autodl-tmp/ComfyUI-H3/output/idiom_$ep
dst=/root/autodl-tmp/idiom_handover/$slug
mkdir -p "$dst/clips" "$dst/review"
for f in "$src"/*_00001_.mp4; do
  [ -e "$f" ] || continue
  name=$(basename "$f" _00001_.mp4)
  if [ ! -e "$dst/clips/$name.mp4" ]; then
    cp "$f" "$dst/clips/$name.mp4"
    /root/autodl-tmp/idiom_handover/tools/contact_sheet.sh "$dst/clips/$name.mp4" "$dst/review/$name.jpg"
    echo "new $name $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$dst/clips/$name.mp4")s"
  fi
done
