#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v5 第一階段：為照片格各抓 3 張 Pixabay 候選，下載縮圖＋做總覽圖。"""
import json, os, subprocess, textwrap
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont

KEY = os.environ["PIXABAY_API_KEY"]
HERE = Path(__file__).resolve().parent
CAND = HERE / "candidates"; CAND.mkdir(exist_ok=True)

# slot -> (編號標籤, 中文說明, 查詢字, image_type)
SLOTS = [
    ("01", "1 放鬆（hook）",      "woman relax eyes closed calm",       "photo"),
    ("02", "2 小孩睡了碗洗完",     "cozy living room evening warm lamp",  "photo"),
    ("03", "3 終於坐下來",        "tired woman sitting sofa home",       "photo"),
    ("04", "4 放鬆不下來",        "stressed tired woman home",           "photo"),
    ("05", "5 擴香（方法）",       "aroma diffuser mist home",            "photo"),
    ("16", "16-17 外婆家午後",     "warm sunlight window cozy old home",  "photo"),
    ("18", "18 放鬆氛圍蠟燭",      "scented candle cozy warm home",       "photo"),
    ("19", "19 照顧自己小儀式",    "woman self care tea calm morning",    "photo"),
    ("21", "21 精油稀釋滴管",      "essential oil dropper bottle",        "photo"),
    ("22", "22 孕婦嬰兒毛孩",      "mother baby hands tender",            "photo"),
    ("23", "23 謹慎使用",         "hands holding oil bottle gentle",     "photo"),
    ("24", "24 結尾薰衣草",        "lavender flowers soft purple",        "photo"),
]

def api(q, itype):
    url = (f"https://pixabay.com/api/?key={KEY}&q={quote(q)}&image_type={itype}"
           f"&safesearch=true&per_page=30&order=popular&orientation=all")
    r = subprocess.run(["curl", "-sS", "--max-time", "40", url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("hits", [])
    except Exception:
        return []

def dl(url, dst):
    subprocess.run(["curl", "-sS", "--max-time", "60", url, "-o", str(dst)],
                   capture_output=True, text=True)
    return dst.exists() and dst.stat().st_size > 5000

BAD = {"logo", "text", "sign", "banner", "poster", "label", "typography",
       "word", "quote", "watermark"}

manifest = {}
for sid, zh, q, itype in SLOTS:
    hits = api(q, itype)
    picked, seen_users = [], set()
    for h in hits:
        if h.get("isAiGenerated"):   # 排除 AI 生成
            continue
        tags = {t.strip().lower() for t in h.get("tags", "").split(",")}
        if tags & BAD:               # 排除含品牌字樣／文字類
            continue
        u = h.get("user", "")
        if u in seen_users:          # 同一格不重複同作者
            continue
        seen_users.add(u)
        picked.append(h)
        if len(picked) == 3:
            break
    cands = []
    for i, h in enumerate(picked, 1):
        thumb = CAND / f"{sid}_{i}.jpg"
        ok = dl(h.get("webformatURL", ""), thumb)
        cands.append({
            "id": h["id"], "w": h.get("imageWidth"), "h": h.get("imageHeight"),
            "tags": h.get("tags"), "user": h.get("user"),
            "web": h.get("webformatURL"), "large": h.get("largeImageURL"),
            "page": h.get("pageURL"), "file": thumb.name if ok else None,
        })
    manifest[sid] = {"zh": zh, "q": q, "candidates": cands}
    print(f"{sid} {zh:14s} -> {len(cands)} 張  ({q})")

(HERE / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

# ---- 做總覽圖 ----
FONT_DIRS = ["/usr/share/fonts", str(Path.home())]
def find_font():
    for root in FONT_DIRS:
        for p in Path(root).rglob("*.otf"):
            if "NotoSansTC" in p.name or "NotoSansCJK" in p.name:
                return str(p)
        for p in Path(root).rglob("*.ttc"):
            if "NotoSansCJK" in p.name or "NotoSerifCJK" in p.name:
                return str(p)
    return None
fp = find_font()
def font(sz):
    try:
        return ImageFont.truetype(fp, sz) if fp else ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

LBLW, TW, TH, PAD = 300, 300, 200, 10
rows = len(SLOTS)
W = LBLW + 3 * (TW + PAD) + PAD
H = rows * (TH + PAD) + PAD
canvas = Image.new("RGB", (W, H), (247, 240, 227))
d = ImageDraw.Draw(canvas)
f_lbl, f_sub, f_small = font(30), font(22), font(18)

for ri, (sid, zh, q, itype) in enumerate(SLOTS):
    y = PAD + ri * (TH + PAD)
    d.rectangle([PAD, y, LBLW - 4, y + TH], fill=(74, 51, 32))
    for li, line in enumerate(textwrap.wrap(zh, 8)[:3]):
        d.text((PAD + 14, y + 16 + li * 38), line, font=f_lbl, fill=(255, 251, 243))
    d.text((PAD + 14, y + TH - 30), q[:26], font=f_small, fill=(205, 187, 160))
    for ci in range(3):
        x = LBLW + PAD + ci * (TW + PAD)
        d.rectangle([x, y, x + TW, y + TH], outline=(200, 180, 150), width=2)
        c = manifest[sid]["candidates"][ci] if ci < len(manifest[sid]["candidates"]) else None
        if c and c["file"]:
            try:
                im = Image.open(CAND / c["file"]).convert("RGB")
                iw, ih = im.size; sc = max(TW / iw, (TH - 26) / ih)
                im = im.resize((int(iw * sc), int(ih * sc)))
                cw, ch = im.size
                im = im.crop(((cw - TW) // 2, 0, (cw - TW) // 2 + TW, TH - 26))
                canvas.paste(im, (x, y))
            except Exception:
                d.text((x + 10, y + 10), "load err", font=f_small, fill=(150, 0, 0))
        # 候選編號條
        d.rectangle([x, y + TH - 26, x + TW, y + TH], fill=(255, 251, 243))
        tag = f"{sid}-{ci+1}" + (f"  {c['user']}" if c else "  (無)")
        d.text((x + 8, y + TH - 24), tag[:30], font=f_sub, fill=(74, 51, 32))

out = HERE / "overview.png"
canvas.save(out)
print("總覽圖：", out)
