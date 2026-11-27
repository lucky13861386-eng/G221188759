#!/usr/bin/env python3
"""v3 定稿：處理 3 張使用者照片 + 下載選定影片，寫 selections.json。"""
import json, os, subprocess
from pathlib import Path
from PIL import Image, ImageChops

KEY=os.environ["PIXABAY_API_KEY"]; HERE=Path(__file__).resolve().parent
UP=HERE/"uploaded"; COMP=HERE.parent/"composition"; CLIPS=HERE/"clips"; CLIPS.mkdir(exist_ok=True)
man=json.loads((HERE/"manifest.json").read_text(encoding="utf-8"))

def trim_white(src,dst):
    im=Image.open(src).convert("RGB")
    bg=Image.new("RGB",im.size,(255,255,255))
    bbox=ImageChops.difference(im,bg).getbbox()
    if bbox and (bbox[2]-bbox[0])<im.width-8:   # 有明顯白邊才裁
        p=4; im=im.crop((bbox[0]+p,bbox[1]+p,bbox[2]-p,bbox[3]-p))
    im.save(dst); return im.size

# 3 張使用者照片
photos={
 "open_photo.png": UP/"1.png",
 "diffuser.png":   UP/"zip_905b5ca6-____"/"1234.png",
 "oil.png":        UP/"zip_9b1d3efd-____"/"5678.png",
}
for name,src in photos.items():
    print(name, trim_white(src, COMP/name))

# 影片：只剩 vmem/v08/v10a/v10b + CTA（v03擴香、v09滴管改用照片）
PICKS={"vmem":2,"v08":2,"v10a":2,"v10b":3}; CTA_ID=80417
def cj(u):
    r=subprocess.run(["curl","-sS","--max-time","40",u],capture_output=True,text=True)
    try:return json.loads(r.stdout)
    except Exception:return None
def dl(u,d):
    subprocess.run(["curl","-sS","--max-time","120",u,"-o",str(d)],capture_output=True,text=True)
    return d.exists() and d.stat().st_size>10000
sel={"open":{"zh":"開場 疲累癱沙發","file":"open_photo.png","user":"使用者提供"},
     "diffuser":{"zh":"擴香霧氣","file":"diffuser.png","user":"使用者提供"},
     "oil":{"zh":"精油滴管稀釋","file":"oil.png","user":"使用者提供"}}
for slot,idx in PICKS.items():
    c=man[slot]["candidates"][idx-1]
    sel[slot]={"zh":man[slot]["zh"],"id":c["id"],"w":c["w"],"h":c["h"],"dur":c.get("dur"),
               "dl_url":c["dl_url"],"user":c["user"],"page":c["page"],"ai":c.get("ai",False)}
d=cj(f"https://pixabay.com/api/videos/?key={KEY}&id={CTA_ID}")
h=d["hits"][0]; big=h["videos"].get("large") or max(h["videos"].values(),key=lambda v:v['width']*v['height'])
sel["CTA"]={"zh":"結尾薰衣草","id":h["id"],"w":big["width"],"h":big["height"],"dur":h.get("duration"),
            "dl_url":big["url"],"user":h.get("user"),"page":h.get("pageURL"),"ai":h.get("isAiGenerated",False)}
for slot in ["vmem","v08","v10a","v10b","CTA"]:
    s=sel[slot]; dst=CLIPS/f"{slot}.mp4"; ok=dl(s["dl_url"],dst); s["file"]=dst.name if ok else None
    print(f"{slot:6}{'OK' if ok else 'FAIL'} {s['w']}x{s['h']} {s.get('dur')}s by {s['user']}")
(HERE/"selections.json").write_text(json.dumps(sel,ensure_ascii=False,indent=1),encoding="utf-8")
print("done")
