#!/usr/bin/env python3
"""搜尋 Pixabay 候選素材（影片 B-roll ＋大腦插畫），下載縮圖、寫 manifest。
金鑰從環境變數 PIXABAY_API_KEY 讀，不印出。透過已設定好的 curl 代理連線。"""
import json, os, subprocess, sys, urllib.parse
from pathlib import Path

KEY = os.environ.get("PIXABAY_API_KEY")
if not KEY:
    sys.exit("PIXABAY_API_KEY 未設定")
HERE = Path(__file__).resolve().parent
CAND = HERE / "candidates"
CAND.mkdir(exist_ok=True)

# 每一句（或每個場景）→ 具體英文畫面關鍵字（香氛療癒：柔光、自然、精油、蠟燭、植物、放鬆的人）
SLOTS = [
    ("s01", "L1 開場・放鬆", "woman relaxing spa aromatherapy", "video"),
    ("s02", "L2 疲憊媽媽的夜晚", "exhausted woman resting couch home", "video"),
    ("s03", "L3 用鼻子深呼吸", "woman breathing fresh air eyes closed", "video"),
    ("s08", "L8 照顧自己的小儀式", "scented candle plant cozy home", "video"),
    ("s09", "L9 精油要稀釋", "aromatherapy oil dropper skincare serum", "video"),
    ("s10", "L10 孕婦嬰兒寵物小心", "mother baby tender home", "video"),
    ("sCTA", "L11-13 結尾 CTA 背景", "lavender field flowers soft", "video"),
    ("brainA", "大腦矢狀切面插畫 A", "brain sagittal cross section anatomy", "illustration"),
    ("brainB", "大腦插畫 B（腦區）", "human brain anatomy medical illustration", "illustration"),
]
# 影片 B-roll 要排除的抽象/背景類標籤
EXCLUDE = {"abstract", "background", "backgrounds", "particle", "particles", "bokeh",
           "pattern", "loop", "motion", "neon", "confetti", "fireworks", "glitter",
           "wallpaper", "digital", "animation", "render", "3d render"}

def curl_json(url):
    r = subprocess.run(["curl", "-sS", "--max-time", "40", url], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None

def curl_dl(url, dst):
    r = subprocess.run(["curl", "-sS", "--max-time", "60", url, "-o", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 1000

manifest = {}
for sid, zh, q, kind in SLOTS:
    qs = urllib.parse.quote(q)
    if kind == "video":
        url = f"https://pixabay.com/api/videos/?key={KEY}&q={qs}&per_page=20&safesearch=true&order=popular"
    else:
        url = f"https://pixabay.com/api/?key={KEY}&q={qs}&image_type=illustration&per_page=20&safesearch=true&order=popular"
    d = curl_json(url)
    if not d:
        print(f"[{sid}] 搜尋失敗"); manifest[sid] = {"zh": zh, "q": q, "kind": kind, "candidates": []}; continue
    hits = d.get("hits", [])
    cands, seen_users = [], set()
    for h in hits:
        if h.get("isLowQuality"): continue
        if kind == "video":
            if not h.get("isGRated", True): continue
            htags = {t.strip().lower() for t in (h.get("tags") or "").split(",")}
            if htags & EXCLUDE: continue        # 跳過抽象/背景類
            sizes = h["videos"]
            best = max(sizes.values(), key=lambda v: v["width"] * v["height"])
            if max(best["width"], best["height"]) < 1080: continue
            dl = sizes.get("large", best)
            thumb = dl.get("thumbnail") or best.get("thumbnail")
            meta = {"id": h["id"], "w": dl["width"], "h": dl["height"], "dur": h.get("duration"),
                    "dl_url": dl["url"], "thumb": thumb, "tags": h.get("tags"),
                    "user": h.get("user"), "page": h.get("pageURL"), "ai": h.get("isAiGenerated", False)}
        else:
            if max(h.get("imageWidth", 0), h.get("imageHeight", 0)) < 1080: continue
            thumb = h.get("webformatURL")
            meta = {"id": h["id"], "w": h.get("imageWidth"), "h": h.get("imageHeight"),
                    "dl_url": h.get("largeImageURL"), "thumb": thumb, "tags": h.get("tags"),
                    "user": h.get("user"), "page": h.get("pageURL"), "ai": h.get("isAiGenerated", False)}
        u = meta["user"]
        if u in seen_users: continue       # 盡量不同作者、避免重複素材
        seen_users.add(u)
        cands.append(meta)
        if len(cands) >= 3: break
    # 下載縮圖
    for i, c in enumerate(cands, 1):
        dst = CAND / f"{sid}_c{i}.jpg"
        c["thumb_file"] = dst.name if curl_dl(c["thumb"], dst) else None
    manifest[sid] = {"zh": zh, "q": q, "kind": kind, "candidates": cands}
    print(f"[{sid}] {zh} → {len(cands)} 候選 ({q})")

(HERE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nmanifest 寫入完成")
