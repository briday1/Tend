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
    all_days=data["days"]
    weekend_content=any(date.fromisoformat(day["date"]).weekday() >= 5
                        and (day["tasks"] or day["activity"]) for day in all_days)
    cols=1 if len(all_days)==1 else (7 if weekend_content else 5)
    days=[day for day in all_days if cols in (1,7) or date.fromisoformat(day["date"]).weekday()<5]
    # Empty weekday cells always remain visible. Weekend columns appear only for scheduled/recorded content.
    start_offset=date.fromisoformat(all_days[0]["date"]).weekday() if all_days and cols>1 else 0
    end_offset=date.fromisoformat(all_days[-1]["date"]).weekday() if all_days and cols>1 else 0
    visible_count=start_offset+len(days) if cols>1 else len(days)
    rows=max(1,(visible_count+cols-1)//cols)
    w=1190;cellh=170 if cols>1 else 240
    top=122;header_h=37 if cols>1 else 0
    h=top+header_h+rows*cellh+24
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
    categories=sorted({t.get("category") or "Uncategorized" for day in days for t in day["tasks"]},key=str.casefold)
    cmap={c:COLORS[i%len(COLORS)] for i,c in enumerate(categories)}
    txt(40,31,start if start==end else f"{start}  —  {end}",27,bold=True)
    cw=1110/cols
    if cols>1:
        for i,label in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][:cols]):
            txt(48+i*cw,top,label,13,bold=True)
    grid_top=top+header_h
    for i in range(rows*cols):
        x=40+(i%cols)*cw;y=grid_top+(i//cols)*cellh
        rect((x,y,x+cw-2,y+cellh-2),surface,0)
    for i,day in enumerate(days):
        slot=i+start_offset if cols>1 else i
        x=40+(slot%cols)*cw;y=grid_top+(slot//cols)*cellh
        dt=date.fromisoformat(day["date"])
        txt(x+9,y+8,dt.strftime("%a %d %b") if cols==1 else str(dt.day),13,bold=True)
        shown=max(1,(cellh-48)//31)
        for j,item in enumerate(day["tasks"][:shown]):
            ty=y+35+j*31
            color=cmap.get(item.get("category") or "Uncategorized",COLORS[0])
            rect((x+6,ty,x+cw-8,ty+27),color,4)
            font=_font(12*scale,True)
            label=clip(item["title"],cw-28,font)
            txt(x+12,ty+5,label,12,"#24312c",True)
        extra=len(day["tasks"])-shown
        if extra>0:txt(x+9,y+cellh-22,f"+{extra} more",11)
    out=BytesIO();im.save(out,format="PNG",optimize=True)
    return out.getvalue()
