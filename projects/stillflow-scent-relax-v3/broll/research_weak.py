#!/usr/bin/env python3
"""重搜 v01b / v03 / v09 三個弱格，更新 manifest 與縮圖。"""
import json, os, subprocess, urllib.parse
from pathlib import Path
KEY=os.environ["PIXABAY_API_KEY"]; HERE=Path(__file__).resolve().parent; CAND=HERE/"candidates"
EXCLUDE={"abstract","background","particle","bokeh","pattern","loop","neon","text","logo","sign",
         "food","fruit","vegetable","wine","beer","coffee","tea","water pipe","pipe","valve","industrial"}
SLOTS={
 "v01b":("L1-2 擴香運作",["essential oil diffuser mist home","aromatherapy diffuser bedroom steam","reed diffuser table home"]),
 "v03":("L3 擴香霧氣特寫",["essential oil diffuser steam close up","aromatherapy mist macro","diffuser water vapor close up"]),
 "v09":("L9 精油滴管",["essential oil dropper glass bottle","facial oil serum dropper","essential oil bottle pipette"]),
}
def cj(u):
    r=subprocess.run(["curl","-sS","--max-time","40",u],capture_output=True,text=True)
    try:return json.loads(r.stdout)
    except Exception:return None
def dl(u,d):
    subprocess.run(["curl","-sS","--max-time","60",u,"-o",str(d)],capture_output=True,text=True)
    return d.exists() and d.stat().st_size>1000
man=json.loads((HERE/"manifest.json").read_text(encoding="utf-8"))
for sid,(zh,queries) in SLOTS.items():
    seen,picked,users=set(),[],set()
    for q in queries:
        d=cj(f"https://pixabay.com/api/videos/?key={KEY}&q={urllib.parse.quote(q)}&per_page=20&safesearch=true&order=popular")
        for h in (d or {}).get("hits",[]):
            if h["id"] in seen or h.get("isLowQuality") or not h.get("isGRated",True):continue
            tags={t.strip().lower() for t in (h.get("tags") or "").split(",")}
            if tags & EXCLUDE:continue
            sizes=h["videos"];best=max(sizes.values(),key=lambda v:v["width"]*v["height"])
            if max(best["width"],best["height"])<1920:continue
            if h.get("user") in users:continue
            seen.add(h["id"]);users.add(h.get("user"));dlsz=sizes.get("large",best)
            picked.append({"id":h["id"],"w":dlsz["width"],"h":dlsz["height"],"dur":h.get("duration"),
                "dl_url":dlsz["url"],"thumb":dlsz.get("thumbnail") or best.get("thumbnail"),"tags":h.get("tags"),
                "user":h.get("user"),"page":h.get("pageURL"),"ai":h.get("isAiGenerated",False)})
            if len(picked)>=3:break
        if len(picked)>=3:break
    for i in range(1,4):
        f=CAND/f"{sid}_c{i}.jpg"
        if f.exists():f.unlink()
    for i,c in enumerate(picked,1):
        f=CAND/f"{sid}_c{i}.jpg";c["thumb_file"]=f.name if dl(c["thumb"],f) else None
    man[sid]={"zh":zh,"q":"（重搜）"+queries[0],"kind":"video","candidates":picked}
    print(f"[{sid}] {zh} -> {len(picked)}")
(HERE/"manifest.json").write_text(json.dumps(man,ensure_ascii=False,indent=1),encoding="utf-8")
print("done")
