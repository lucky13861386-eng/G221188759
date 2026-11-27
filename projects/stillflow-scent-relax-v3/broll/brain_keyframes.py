#!/usr/bin/env python3
"""大腦動畫 3 張關鍵畫面（給使用者確認動畫走法與配色）。
底圖＝Pixabay 矢狀切面插畫，暖色化；發光路徑／亮區／標籤＝向量圖層疊加。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FONT = str(ROOT/"fonts"/"NotoSansTC-Regular.otf"); FONTB=str(ROOT/"fonts"/"NotoSansTC-Bold.otf")
brain = Image.open(ROOT/"projects"/"stillflow-scent-relax-v2"/"composition"/"brain_sagittal.png").convert("RGB")
# 暖色化：降一點飽和、微暖，避免原本的洋紅太跳
brain = ImageEnhance.Color(brain).enhance(0.72)
brain = ImageEnhance.Brightness(brain).enhance(1.04)
W,H = 1080,1920
CREAM=(243,233,216); INK=(58,46,30); LAV=(155,134,201); GOLD=(255,196,110); RED=(206,74,60)
fb=lambda s: ImageFont.truetype(FONTB,s); fr=lambda s: ImageFont.truetype(FONT,s)

def base_frame(zoom_note):
    im=Image.new("RGB",(W,H),CREAM); d=ImageDraw.Draw(im)
    d.text((W/2,300),"氣味訊號走的路",font=fb(78),fill=INK,anchor="mm")
    d.text((W/2,370),"示意圖，非真實解剖比例",font=fr(32),fill=(140,110,74),anchor="mm")
    sc=1.504; bw,bh=brain.size; disp=brain.resize((int(bw*sc),int(bh*sc)))
    ox,oy=130,540; im.paste(disp,(ox,oy))
    def P(bx,by): return (ox+bx*sc, oy+by*sc)
    return im,d,P

def chip(d,xy,text,sub=""):
    f=fb(40); tw=d.textlength(text,font=f); sw=d.textlength(sub,font=fr(28)) if sub else 0
    w=tw+sw+(18 if sub else 0)+36; x,y=xy
    d.rounded_rectangle((x-w/2,y-34,x+w/2,y+34),radius=14,fill=(255,249,238))
    d.text((x-w/2+18,y),text,font=f,fill=INK,anchor="lm")
    if sub: d.text((x-w/2+18+tw+18,y+4),sub,font=fr(28),fill=(122,90,56),anchor="lm")

def glow(im,xy,r,color):
    g=Image.new("RGBA",(r*4,r*4),(0,0,0,0)); gd=ImageDraw.Draw(g)
    gd.ellipse((r,r,r*3,r*3),fill=color+(230,)); g=g.filter(ImageFilter.GaussianBlur(r*0.5))
    im.paste(Image.alpha_composite(Image.new("RGBA",g.size,(0,0,0,0)),g),(int(xy[0]-r*2),int(xy[1]-r*2)),g)

def cap(d,txt):
    d.rounded_rectangle((60,1640,W-60,1820),radius=24,fill=(40,28,16))
    d.text((W/2,1730),txt,font=fb(44),fill=(248,238,220),anchor="mm")

# A：眼耳 → 視丘，鏡頭推近視丘
im,d,P=base_frame(True); imr=im.convert("RGBA")
tx,ty=P(240,250)
for (by,lab) in [(300,"眼"),(430,"耳")]:
    sx,sy=P(-70,by); d.ellipse((sx-34,sy-34,sx+34,sy+34),fill=(255,249,238),outline=(150,120,80),width=3)
    d.text((sx,sy),lab,font=fb(34),fill=INK,anchor="mm"); d.line((sx+34,sy,tx,ty),fill=(150,120,80),width=5)
d.ellipse((tx-74,ty-74,tx+74,ty+74),outline=LAV,width=10)
d.rectangle((tx-150,ty-150,tx+150,ty+150),outline=(120,120,120),width=3)
d.text((tx+170,ty-150),"鏡頭推近",font=fr(34),fill=(120,100,70))
chip(d,(tx+40,ty-210),"視丘","轉運站")
cap(d,"① 眼耳訊號匯集到視丘，鏡頭推近視丘")
im.save(HERE/"kf_A.png")

# B：繞過視丘（打叉）· 放大嗅球
im,d,P=base_frame(True);
nx,ny=P(10,350); bx,by=P(60,320); tx,ty=P(240,250)
d.line((nx,ny,(nx+bx)/2,(ny+by)/2-20,bx,by),fill=GOLD,width=14,joint="curve")
glow(imr:=im.convert("RGBA"),(bx,by),70,GOLD); im=imr.convert("RGB"); d=ImageDraw.Draw(im)
# 重畫金線在光上
d.line((nx,ny,bx,by),fill=GOLD,width=12)
# 視丘變暗＋打叉
d.ellipse((tx-60,ty-60,tx+60,ty+60),fill=(150,150,150))
d.line((tx-46,ty-46,tx+46,ty+46),fill=RED,width=12); d.line((tx-46,ty+46,tx+46,ty-46),fill=RED,width=12)
chip(d,(bx-10,by-130),"嗅球")
chip(d,(tx+60,ty-150),"視丘")
cap(d,"② 不經過視丘（打叉）· 鏡頭放大嗅球")
im.save(HERE/"kf_B.png")

# C：杏仁核・海馬迴亮起 · 回憶泡泡放大
im,d,P=base_frame(True); imr=im.convert("RGBA")
ax,ay=P(205,360); hx,hy=P(255,392)
glow(imr,(ax,ay),60,LAV); glow(imr,(hx,hy),66,LAV); im=imr.convert("RGB"); d=ImageDraw.Draw(im)
chip(d,(ax-120,ay+150),"杏仁核","情緒")
chip(d,(hx+150,hy+120),"海馬迴","記憶")
# 回憶泡泡
d.rounded_rectangle((660,980,980,1180),radius=40,fill=(255,255,255),outline=(210,200,180),width=3)
d.ellipse((690,1180,740,1230),fill=(255,255,255),outline=(210,200,180),width=3)
d.text((820,1050),"外婆家",font=fb(50),fill=INK,anchor="mm")
d.text((820,1120),"安心的午後",font=fr(40),fill=(120,90,56),anchor="mm")
d.text((820,1250),"放大成全畫面 → 接實拍",font=fr(32),fill=(120,100,70),anchor="mm")
cap(d,"③ 杏仁核・海馬迴亮起 · 回憶泡泡放大成全畫面")
im.save(HERE/"kf_C.png")

# 三合一
m=Image.new("RGB",(W*3+40,H+20),(26,26,30))
for i,n in enumerate(["kf_A","kf_B","kf_C"]):
    t=Image.open(HERE/f"{n}.png").resize((W,H)); m.paste(t,(10+i*(W+10),10))
m.save(HERE/"brain_keyframes.png"); print("saved", m.size)
