#!/usr/bin/env python3
"""重搜 v01：疲累的媽媽癱在沙發上。"""
import json, os, subprocess, urllib.parse
from pathlib import Path
KEY=os.environ["PIXABAY_API_KEY"]; HERE=Path(__file__).resolve().parent; CAND=HERE/"candidates"
QUERIES=["exhausted mother resting sofa home","tired woman lying couch living room","woman relaxing tired sofa evening home"]
EXCLUDE={"abstract","background","particle","loop","text","logo","yoga","fitness","workout","gym","exercise"}
def cj(u):
    r=subprocess.run(["curl","-sS","--max-time","40",u],capture_output=True,text=True)
    try:return json.loads(r.stdout)
    except Exception:return None
def dl(u,d):
    subprocess.run(["curl","-sS","--max-time","60",u,"-o",str(d)],capture_output=True,text=True)
    return d.exists() and d.stat().st_size>1000
seen,picked,users=set(),[],set()
for q in QUERIES:
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
    f=CAND/f"v01_c{i}.jpg"
    if f.exists():f.unlink()
for i,c in enumerate(picked,1):
    f=CAND/f"v01_c{i}.jpg";c["thumb_file"]=f.name if dl(c["thumb"],f) else None
man=json.loads((HERE/"manifest.json").read_text(encoding="utf-8"))
man["v01"]={"zh":"L1-2 疲累媽媽癱沙發","q":"（重搜）exhausted mother resting sofa","kind":"video","candidates":picked}
(HERE/"manifest.json").write_text(json.dumps(man,ensure_ascii=False,indent=1),encoding="utf-8")
for c in picked: print(c["id"],f"{c['w']}x{c['h']}",c.get("dur"),"|",(c["tags"] or "")[:60],"| by",c["user"])
