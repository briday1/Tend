"""Theme-aware deterministic PNG calendar exports using Pillow (no AI/network)."""
from datetime import date
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .snapshots import snapshot

THEMES={
"light":("#fafaf9","#333b44","#e2e3e3"),
"dark":("#303438","#f0f2f4","#1f2225"),
"sage":("#fafcf6","#293d31","#e4e9e0"),
"rose":("#fff9fc","#463044","#ebe1e6"),
"sepia":("#fff8e9","#45372a","#e4ded3"),
"dusk":("#393b54","#f2efff","#24253a"),
"ocean":("#2d4e58","#f1faf9","#19333b"),
"solarized-light":("#fdf6e3","#4c4538","#e9e3d1"),
"solarized-dark":("#164955","#edf7f8","#073541")}
COLORS=["#afd4c0","#f3c5aa","#c6c2ed","#e7d89b","#a9cadf","#edbfcb","#b8d5a1","#d4c3a5"]
def _font(size,bold=False):
    paths=(["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf"] if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","C:/Windows/Fonts/arial.ttf"])
    for path in paths:
        try:return ImageFont.truetype(path,size)
        except OSError:pass
    return ImageFont.load_default()
def png(start,end,category="",theme="sage",scale=2):
    if theme not in THEMES:raise ValueError("Unknown theme")
    if scale not in (1,2,4):raise ValueError("Scale must be 1, 2, or 4")
    data=snapshot(start,end,category)
    days=data["days"];cols=1 if len(days)==1 else 7
    rows=(len(days)+cols-1)//cols
    w=1190;cellh=185 if cols==7 else 280
    h=285+rows*cellh+100
    bg,ink,surface=THEMES[theme]
    im=Image.new("RGB",(w*scale,h*scale),bg)
    d=ImageDraw.Draw(im)
    def rect(box,fill,r=0):
        points=tuple(round(q*scale) for q in box)
        d.rounded_rectangle(points,radius=r*scale,fill=fill)
    def txt(x,y,s,size=16,color=ink,bold=False):
        d.text((x*scale,y*scale),str(s),fill=color,font=_font(size*scale,bold))
    def clip(s,width,font):
        s=str(s)
        if d.textlength(s,font=font)<=width*scale:return s
        while s and d.textlength(s+"…",font=font)>width*scale:s=s[:-1]
        return s+"…" if s else ""
    categories=sorted(data["insights"]["categories"],key=str.casefold)
    cmap={c:COLORS[i%len(COLORS)] for i,c in enumerate(categories)}
    txt(40,28,"TEND  /  SNAPSHOTS",17,bold=True)
    txt(40,70,start if start==end else f"{start}  —  {end}",35,bold=True)
    counts=data["insights"]
    for i,(name,num) in enumerate((("TASKS DUE",counts["scheduled_due"]),
                                    ("ACTIVITY LOGGED",counts["activity_events"]),
                                    ("ACTIVE DAYS",counts["active_days"]))):
        x=40+i*370
        rect((x,137,x+350,218),surface,14)
        txt(x+18,148,num,29,bold=True)
        txt(x+18,192,name,13)
    top=252;cw=1110/cols
    for i,day in enumerate(days):
        x=40+(i%cols)*cw;y=top+(i//cols)*cellh
        rect((x,y,x+cw-6,y+cellh-7),surface,12)
        dt=date.fromisoformat(day["date"])
        txt(x+12,y+10,dt.strftime("%a %d %b"),14,bold=True)
        shown=3 if cols==7 else 7
        for j,item in enumerate(day["tasks"][:shown]):
            ty=y+43+j*36
            color=cmap.get(item["category"],COLORS[0])
            rect((x+10,ty,x+cw-16,ty+31),color,6)
            font=_font(12*scale,True)
            label=clip(item["title"],cw-44,font)
            txt(x+16,ty+7,label,12,"#24312c",True)
        extra=len(day["tasks"])-shown
        if extra>0:txt(x+12,y+cellh-29,f"+{extra} more tasks",12)
        if day["activity"]:
            txt(x+12,y+cellh-48,f"{len(day['activity'])} activity",11)
    ly=top+rows*cellh+10
    lx=40
    for cat in categories:
        if lx>1050:break
        rect((lx,ly+4,lx+10,ly+14),cmap[cat],5)
        name=cat if len(cat)<19 else cat[:18]+"…"
        txt(lx+17,ly,name,13)
        lx+=max(115,min(205,len(name)*9+26))
    txt(40,h-39,"Recorded activity is historical; due dates and task states reflect current records.",12)
    out=BytesIO();im.save(out,format="PNG",optimize=True)
    return out.getvalue()
