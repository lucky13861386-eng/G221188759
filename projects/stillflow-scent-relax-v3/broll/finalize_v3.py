#!/usr/bin/env python3
"""v3 定稿：裁開場照片白邊、下載選定影片，寫 selections.json。"""
import json, os, subprocess
from pathlib import Path
from PIL import Image, ImageChops

KEY=os.environ["PIXABAY_API_KEY"]; HERE=Path(__file__).resolve().parent
CLIPS=HERE/"clips"; CLIPS.mkdir(exist_ok=True)
man=json.loads((HERE/"manifest.json").read_text(encoding="utf-8"))

# 1) 裁開場照片白邊
im=Image.open(HERE/"uploaded"/"1.png").convert("RGB")
bg=Image.new("RGB",im.size,(255,255,255))
diff=ImageChops.difference(im,bg); bbox=diff.getbbox()
if bbox:
    pad=4; b=(bbox[0]+pad,bbox[1]+pad,bbox[2]-pad,bbox[3]-pad); im=im.crop(b)
im.save(HERE.parent/"composition"/"open_photo.png")
print("開場照片裁切 ->", im.size)

# 2) 下載選定影片
PICKS={"v03":1,"vmem":2,"v08":2,"v09":3,"v10a":2,"v10b":3}
CTA_ID=80417
def cj(u):
    r=subprocess.run(["curl","-sS","--max-time","40",u],capture_output=True,text=True)
    try:return json.loads(r.stdout)
    except Exception:return None
def dl(u,d):
    subprocess.run(["curl","-sS","--max-time","120",u,"-o",str(d)],capture_output=True,text=True)
    return d.exists() and d.stat().st_size>10000
sel={}
for slot,idx in PICKS.items():
    c=man[slot]["candidates"][idx-1]
    sel[slot]={"zh":man[slot]["zh"],"id":c["id"],"w":c["w"],"h":c["h"],"dur":c.get("dur"),
               "dl_url":c["dl_url"],"user":c["user"],"page":c["page"],"ai":c.get("ai",False)}
# CTA by id
d=cj(f"https://pixabay.com/api/videos/?key={KEY}&id={CTA_ID}")
h=d["hits"][0]; big=h["videos"].get("large") or max(h["videos"].values(),key=lambda v:v['width']*v['height'])
sel["CTA"]={"zh":"結尾薰衣草","id":h["id"],"w":big["width"],"h":big["height"],"dur":h.get("duration"),
            "dl_url":big["url"],"user":h.get("user"),"page":h.get("pageURL"),"ai":h.get("isAiGenerated",False)}
for slot,s in sel.items():
    dst=CLIPS/f"{slot}.mp4"; ok=dl(s["dl_url"],dst); s["file"]=dst.name if ok else None
    print(f"{slot:6}{'OK' if ok else 'FAIL'} {s['w']}x{s['h']} {s.get('dur')}s by {s['user']}")
sel["open"]={"zh":"開場（使用者提供照片）","file":"open_photo.png","user":"使用者提供","source":"uploaded"}
(HERE/"selections.json").write_text(json.dumps(sel,ensure_ascii=False,indent=1),encoding="utf-8")
print("selections.json 完成")
