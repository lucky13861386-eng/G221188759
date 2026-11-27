#!/usr/bin/env python3
"""重搜 s03（用鼻子深呼吸／聞香）更貼切的候選，更新 manifest 與縮圖。"""
import json, os, subprocess, urllib.parse
from pathlib import Path

KEY = os.environ["PIXABAY_API_KEY"]
HERE = Path(__file__).resolve().parent
CAND = HERE / "candidates"
QUERIES = [
    "woman smelling flower close up",
    "woman smelling lavender eyes closed",
    "girl enjoying scent flower nature",
]
EXCLUDE = {"abstract", "background", "particle", "bokeh", "pattern", "loop", "neon", "clock"}

def curl_json(url):
    r = subprocess.run(["curl", "-sS", "--max-time", "40", url], capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception: return None

def curl_dl(url, dst):
    subprocess.run(["curl", "-sS", "--max-time", "60", url, "-o", str(dst)], capture_output=True, text=True)
    return dst.exists() and dst.stat().st_size > 1000

seen, cands = set(), []
for q in QUERIES:
    d = curl_json(f"https://pixabay.com/api/videos/?key={KEY}&q={urllib.parse.quote(q)}&per_page=20&safesearch=true&order=popular")
    for h in (d or {}).get("hits", []):
        if h.get("isLowQuality") or not h.get("isGRated", True): continue
        tags = {t.strip().lower() for t in (h.get("tags") or "").split(",")}
        if tags & EXCLUDE: continue
        if h["id"] in seen: continue
        sizes = h["videos"]; best = max(sizes.values(), key=lambda v: v["width"]*v["height"])
        if max(best["width"], best["height"]) < 1080: continue
        dl = sizes.get("large", best)
        seen.add(h["id"])
        cands.append({"id": h["id"], "w": dl["width"], "h": dl["height"], "dur": h.get("duration"),
                      "dl_url": dl["url"], "thumb": dl.get("thumbnail") or best.get("thumbnail"),
                      "tags": h.get("tags"), "user": h.get("user"), "page": h.get("pageURL"),
                      "ai": h.get("isAiGenerated", False), "q": q})
# 不同作者，取前 3
picked, users = [], set()
for c in cands:
    if c["user"] in users: continue
    users.add(c["user"]); picked.append(c)
    if len(picked) >= 3: break

for i, c in enumerate(picked, 1):
    dst = CAND / f"s03_c{i}.jpg"
    c["thumb_file"] = dst.name if curl_dl(c["thumb"], dst) else None

man = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
man["s03"] = {"zh": "L3 用鼻子深呼吸", "q": "聞花/聞香特寫（重搜）", "kind": "video", "candidates": picked}
(HERE / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
for c in picked:
    print(c["id"], f"{c['w']}x{c['h']}", c.get("dur"), "|", c["tags"], "| by", c["user"])
