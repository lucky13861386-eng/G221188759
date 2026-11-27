#!/usr/bin/env bash
# 把每段 Pixabay 影片裁成 1080x1920、套統一暖色調、對齊各句長度（短的循環）。
set -e
cd "$(dirname "$0")"
OUT=../composition
mkdir -p "$OUT"
# 統一暖色調：微升飽和與亮度，色彩平衡偏暖（加紅減藍），輕微柔光
WARM="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=saturation=1.07:brightness=0.015:contrast=1.02,colorbalance=rm=0.05:gm=0.01:bm=-0.07:rs=0.03:bs=-0.05:rh=0.03:bh=-0.04,format=yuv420p"
enc () { # $1=slot $2=dur $3=loop(1/0)
  local loop=""; [ "$3" = "1" ] && loop="-stream_loop -1"
  ffmpeg -y $loop -i "clips/$1.mp4" -t "$2" -an -vf "$WARM" -r 30 -c:v libx264 -crf 20 -preset veryfast -movflags +faststart "$OUT/bg_$1.mp4" -loglevel error
  echo "  bg_$1.mp4  ($2s)"
}
echo "preprocessing..."
enc s01 7.35 1
enc s02 6.75 0
enc s03 5.25 0
enc s08 8.25 0
enc s09 7.00 1
enc s10 7.25 0
enc sCTA 17.90 0
echo "done"
ls -lh "$OUT"/bg_*.mp4
