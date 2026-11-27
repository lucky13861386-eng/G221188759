#!/usr/bin/env python3
"""v3 候選搜尋：實拍素材（嚴格關鍵字）＋ 高解析大腦影片（抓定格當底圖）。"""
import json, os, subprocess, urllib.parse
from pathlib import Path

KEY = os.environ["PIXABAY_API_KEY"]
HERE = Path(__file__).resolve().parent
CAND = HERE / "candidates"; CAND.mkdir(exist_ok=True)

SLOTS = [
    ("v01",  "L1-2 疲憊上班族坐下",   "tired office worker sitting home evening", "video"),
    ("v01b", "L1-2 點擴香",           "lighting aroma diffuser home",            "video"),
    ("v03",  "L3 擴香霧氣（進鼻子）",  "aroma diffuser mist close up",            "video"),
    ("vmem", "L7 外婆家／午後陽光",    "sunlight through window cozy home afternoon","video"),
    ("v08",  "L8 放鬆氛圍",           "aroma diffuser cozy home candle",         "video"),
    ("v09",  "L9 滴管滴入基底油",      "essential oil dropper carrier oil",       "video"),
    ("v10a", "L10 嬰兒",             "mother baby tender home soft",            "video"),
    ("v10b", "L10 寵物",             "cat dog resting home cozy",               "video"),
    ("brainvid", "大腦剖面影片（抓定格）", "brain cross section anatomy medical",  "video"),
]
EXCLUDE = {"abstract","background","particle","bokeh","pattern","loop","neon","text","logo",
           "food","fruit","vegetable","salad","kitchen","cooking","coffee","tea","wine","beer",
           "pizza","meat","bread","cake","sign","banner","typography"}

def cj(url):
    r = subprocess.run(["curl","-sS","--max-time","40",url],capture_output=True,text=True)
    try: return json.loads(r.stdout)
    except Exception: return None

def dl(url,dst):
    subprocess.run(["curl","-sS","--max-time","60",url,"-o",str(dst)],capture_output=True,text=True)
    return dst.exists() and dst.stat().st_size>1000

man={}
for sid,zh,q,kind in SLOTS:
    d=cj(f"https://pixabay.com/api/videos/?key={KEY}&q={urllib.parse.quote(q)}&per_page=25&safesearch=true&order=popular")
    cands,users=[],set()
    for h in (d or {}).get("hits",[]):
        if h.get("isLowQuality") or not h.get("isGRated",True): continue
        tags={t.strip().lower() for t in (h.get("tags") or "").split(",")}
        if tags & EXCLUDE: continue
        sizes=h["videos"]; best=max(sizes.values(),key=lambda v:v["width"]*v["height"])
        if max(best["width"],best["height"])<1920: continue      # v3 要 1080p 以上，偏好大尺寸
        if h.get("user") in users: continue
        users.add(h.get("user"))
        dlsz=sizes.get("large",best)
        cands.append({"id":h["id"],"w":dlsz["width"],"h":dlsz["height"],"dur":h.get("duration"),
                      "dl_url":dlsz["url"],"thumb":dlsz.get("thumbnail") or best.get("thumbnail"),
                      "tags":h.get("tags"),"user":h.get("user"),"page":h.get("pageURL"),"ai":h.get("isAiGenerated",False)})
        if len(cands)>=3: break
    for i,c in enumerate(cands,1):
        dst=CAND/f"{sid}_c{i}.jpg"; c["thumb_file"]=dst.name if dl(c["thumb"],dst) else None
    man[sid]={"zh":zh,"q":q,"kind":kind,"candidates":cands}
    print(f"[{sid}] {zh} -> {len(cands)} ({q})")

(HERE/"manifest.json").write_text(json.dumps(man,ensure_ascii=False,indent=1),encoding="utf-8")
print("done")
