#!/usr/bin/env python3
"""依選定結果下載素材到 clips/，並寫 selections.json（含 credits 來源）。"""
import json, os, subprocess
from pathlib import Path

KEY = os.environ["PIXABAY_API_KEY"]
HERE = Path(__file__).resolve().parent
CLIPS = HERE / "clips"; CLIPS.mkdir(exist_ok=True)
man = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))

# slot -> 候選索引（1 起）；s03 特別指定 Pixabay video id
PICKS = {"s01": 3, "s02": 1, "s08": 2, "s09": 1, "s10": 2, "sCTA": 2, "brainA": 1}
S03_ID = 184538

def curl_json(url):
    r = subprocess.run(["curl","-sS","--max-time","40",url],capture_output=True,text=True)
    try: return json.loads(r.stdout)
    except Exception: return None

def dl(url, dst):
    subprocess.run(["curl","-sS","--max-time","120",url,"-o",str(dst)],capture_output=True,text=True)
    return dst.exists() and dst.stat().st_size > 10000

sel = {}
# s03：用 id 取回
d = curl_json(f"https://pixabay.com/api/videos/?key={KEY}&id={S03_ID}")
h = d["hits"][0]; sizes = h["videos"]; big = sizes.get("large") or max(sizes.values(),key=lambda v:v['width']*v['height'])
sel["s03"] = {"zh":"L3 用鼻子深呼吸","kind":"video","id":h["id"],"w":big["width"],"h":big["height"],
              "dur":h.get("duration"),"dl_url":big["url"],"user":h.get("user"),"page":h.get("pageURL"),"ai":h.get("isAiGenerated",False)}

for slot, idx in PICKS.items():
    c = man[slot]["candidates"][idx-1]
    sel[slot] = {"zh": man[slot]["zh"], "kind": man[slot]["kind"], "id": c["id"], "w": c["w"], "h": c["h"],
                 "dur": c.get("dur"), "dl_url": c["dl_url"], "user": c["user"], "page": c["page"], "ai": c.get("ai", False)}

for slot, s in sel.items():
    ext = "mp4" if s["kind"] == "video" else "png"
    dst = CLIPS / f"{slot}.{ext}"
    ok = dl(s["dl_url"], dst)
    s["file"] = dst.name if ok else None
    size = dst.stat().st_size // 1024 if ok else 0
    print(f"{slot:6} {'OK' if ok else 'FAIL'}  {s['w']}x{s['h']} {s.get('dur','')}  {size}KB  by {s['user']}")

(HERE / "selections.json").write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nselections.json 寫入完成")
