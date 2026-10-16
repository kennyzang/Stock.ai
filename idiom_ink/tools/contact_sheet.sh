#!/usr/bin/env bash
# Runs on the GPU server. Contact sheet of a clip for review: 8 evenly spaced frames in a 4x2 grid (360 px wide each).
# Usage: contact_sheet.sh CLIP.mp4 OUT.jpg
set -euo pipefail
clip=$1 out=$2
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$clip")
fps=$(python3 -c "print(8/max(float('$dur'),0.5))")
ffmpeg -v error -y -i "$clip" -vf "fps=$fps,scale=360:-2,tile=4x2:padding=6:color=white" -frames:v 1 -q:v 3 "$out"
