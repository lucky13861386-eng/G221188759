#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""換掉含品牌字樣的兩格(05,23)，排除該作者，重畫 overview。"""
import json, os, subprocess, textwrap
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont

KEY = os.environ["PIXABAY_API_KEY"]
HERE = Path(__file__).resolve().parent
CAND = HERE / "candidates"
man = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))

REDO = {"05": "essential oil diffuser steam"}
EXCLUDE_USERS = {"ha11ok"}         # 之前混進 dōTERRA 品牌瓶的作者
BAD = {"logo","text","sign","banner","poster","label","typography","word",
       "quote","watermark","doterra","brand"}

def api(q):
    url = (f"https://pixabay.com/api/?key={KEY}&q={quote(q)}&image_type=photo"
           f"&safesearch=true&per_page=40&order=popular&orientation=all")
    r = subprocess.run(["curl","-sS","--max-time","40",url],capture_output=True,text=True)
    try: return json.loads(r.stdout).get("hits", [])
    except Exception: return []
def dl(url,dst):
    subprocess.run(["curl","-sS","--max-time","60",url,"-o",str(dst)],capture_output=True,text=True)
    return dst.exists() and dst.stat().st_size>5000

for sid,q in REDO.items():
    hits=api(q); picked,seen=[],set()
    for h in hits:
        if h.get("isAiGenerated"): continue
        if h.get("user","") in EXCLUDE_USERS: continue
        tags={t.strip().lower() for t in h.get("tags","").split(",")}
        if tags & BAD: continue
        u=h.get("user","")
        if u in seen: continue
        seen.add(u); picked.append(h)
        if len(picked)==3: break
    cands=[]
    for i,h in enumerate(picked,1):
        thumb=CAND/f"{sid}_{i}.jpg"; ok=dl(h.get("webformatURL",""),thumb)
        cands.append({"id":h["id"],"w":h.get("imageWidth"),"h":h.get("imageHeight"),
                      "tags":h.get("tags"),"user":h.get("user"),
                      "web":h.get("webformatURL"),"large":h.get("largeImageURL"),
                      "page":h.get("pageURL"),"file":thumb.name if ok else None})
    man[sid]["q"]=q; man[sid]["candidates"]=cands
    print(f"{sid} 換 -> {len(cands)} 張 ({q})  作者:{[c['user'] for c in cands]}")

(HERE/"manifest.json").write_text(json.dumps(man,ensure_ascii=False,indent=1),encoding="utf-8")

ORDER=["01","02","03","04","05","16","18","19","21","22","23","24"]
def find_font():
    for root in ["/usr/share/fonts",str(Path.home())]:
        for p in Path(root).rglob("*.otf"):
            if "NotoSansTC" in p.name or "NotoSansCJK" in p.name: return str(p)
        for p in Path(root).rglob("*.ttc"):
            if "NotoSansCJK" in p.name or "NotoSerifCJK" in p.name: return str(p)
    return None
fp=find_font()
def font(sz):
    try: return ImageFont.truetype(fp,sz) if fp else ImageFont.load_default()
    except Exception: return ImageFont.load_default()
LBLW,TW,TH,PAD=300,300,200,10
W=LBLW+3*(TW+PAD)+PAD; H=len(ORDER)*(TH+PAD)+PAD
canvas=Image.new("RGB",(W,H),(247,240,227)); d=ImageDraw.Draw(canvas)
f_lbl,f_sub,f_small=font(30),font(22),font(18)
for ri,sid in enumerate(ORDER):
    y=PAD+ri*(TH+PAD)
    d.rectangle([PAD,y,LBLW-4,y+TH],fill=(74,51,32))
    for li,line in enumerate(textwrap.wrap(man[sid]["zh"],8)[:3]):
        d.text((PAD+14,y+16+li*38),line,font=f_lbl,fill=(255,251,243))
    d.text((PAD+14,y+TH-30),man[sid]["q"][:26],font=f_small,fill=(205,187,160))
    for ci in range(3):
        x=LBLW+PAD+ci*(TW+PAD)
        d.rectangle([x,y,x+TW,y+TH],outline=(200,180,150),width=2)
        cl=man[sid]["candidates"]; c=cl[ci] if ci<len(cl) else None
        if c and c.get("file"):
            try:
                im=Image.open(CAND/c["file"]).convert("RGB"); iw,ih=im.size
                sc=max(TW/iw,(TH-26)/ih); im=im.resize((int(iw*sc),int(ih*sc)))
                cw,ch=im.size; im=im.crop(((cw-TW)//2,0,(cw-TW)//2+TW,TH-26))
                canvas.paste(im,(x,y))
            except Exception: pass
        d.rectangle([x,y+TH-26,x+TW,y+TH],fill=(255,251,243))
        tag=f"{sid}-{ci+1}"+(f"  {c['user']}" if c else "  (無)")
        d.text((x+8,y+TH-24),tag[:30],font=f_sub,fill=(74,51,32))
canvas.save(HERE/"overview.png"); print("overview 重畫完成")
