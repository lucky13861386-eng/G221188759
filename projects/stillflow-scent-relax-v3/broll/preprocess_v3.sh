#!/usr/bin/env bash
set -e; cd "$(dirname "$0")"; OUT=../composition
WARM="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=saturation=1.07:brightness=0.015:contrast=1.02,colorbalance=rm=0.05:gm=0.01:bm=-0.07:rs=0.03:bs=-0.05:rh=0.03:bh=-0.04,format=yuv420p"
enc(){ local loop=""; [ "$3" = "1" ] && loop="-stream_loop -1"; ffmpeg -y $loop -i "clips/$1.mp4" -t "$2" -an -vf "$WARM" -r 30 -c:v libx264 -crf 20 -preset veryfast -movflags +faststart "$OUT/bg_$1.mp4" -loglevel error; echo "  bg_$1 ($2s)"; }
echo "preprocessing..."
enc vmem 6.55 0
enc v08  8.55 0
enc v10a 4.25 0
enc v10b 4.20 0
enc CTA  18.20 0
echo done; ls -lh "$OUT"/bg_*.mp4