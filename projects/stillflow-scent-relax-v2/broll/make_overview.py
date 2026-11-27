#!/usr/bin/env python3
"""把候選縮圖排成一張總覽圖，附中文標籤與素材資訊，給使用者挑選。"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
CAND = HERE / "candidates"
ROOT = HERE.parents[2]
FONT = ROOT / "fonts" / "NotoSansTC-Regular.otf"
FONTB = ROOT / "fonts" / "NotoSansTC-Bold.otf"
man = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))

f_title = ImageFont.truetype(str(FONTB), 36)
f_slot = ImageFont.truetype(str(FONTB), 27)
f_q = ImageFont.truetype(str(FONT), 18)
f_cap = ImageFont.truetype(str(FONT), 17)

COLS, TW, TH = 3, 366, 206           # 每欄縮圖框 16:9
GAP, MARGIN = 20, 36
ROW_LABEL_H, CAP_H = 72, 56
W = MARGIN * 2 + COLS * TW + (COLS - 1) * GAP
rows = list(man.items())
ROW_H = ROW_LABEL_H + TH + CAP_H + 18
H = MARGIN + 60 + len(rows) * ROW_H + MARGIN

img = Image.new("RGB", (W, H), "#20242b")
d = ImageDraw.Draw(img)
d.text((MARGIN, MARGIN - 6), "STILLFLOW v2・素材候選總覽（每格 3 選 1，告訴我代號即可，例：s01→2）",
       font=f_title, fill="#f4f1e8")

y = MARGIN + 62
for sid, info in rows:
    d.text((MARGIN, y), f"{sid}  {info['zh']}", font=f_slot, fill="#e9c46a")
    d.text((MARGIN, y + 36), f"搜尋字：{info['q']}", font=f_q, fill="#9fb0bf")
    cy = y + ROW_LABEL_H
    for i, c in enumerate(info["candidates"]):
        x = MARGIN + i * (TW + GAP)
        box = (x, cy, x + TW, cy + TH)
        d.rectangle(box, fill="#2e3740")
        tf = CAND / (c.get("thumb_file") or "")
        if c.get("thumb_file") and tf.exists():
            try:
                im = Image.open(tf).convert("RGB")
                im.thumbnail((TW, TH))
                img.paste(im, (x + (TW - im.width) // 2, cy + (TH - im.height) // 2))
            except Exception:
                pass
        d.rectangle(box, outline="#4a5560", width=2)
        tag = f"{sid}→{i+1}"
        d.rectangle((x, cy, x + 74, cy + 30), fill="#e76f51")
        d.text((x + 8, cy + 4), tag, font=f_cap, fill="#ffffff")
        dur = f"{c['dur']}s" if c.get("dur") else "插畫"
        ai = "  ⚠AI" if c.get("ai") else ""
        d.text((x + 2, cy + TH + 6), f"{c['w']}×{c['h']} · {dur}{ai}", font=f_cap, fill="#cdd6de")
        d.text((x + 2, cy + TH + 30), f"by {c.get('user','')}", font=f_cap, fill="#8a97a2")
    y += ROW_H

out = HERE / "overview.png"
img.save(out)
print("總覽圖：", out, img.size)
