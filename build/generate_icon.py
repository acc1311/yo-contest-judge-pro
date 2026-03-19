#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YO Contest Judge PRO — Icon Generator
Regenereaza app_icon.ico folosind exclusiv stdlib Python.
Rulare: python build/generate_icon.py
Output: build/app_icon.ico + build/icons/icon_*.png
"""
import struct, zlib, math, os

# ── Utilitare grafice ─────────────────────────────────────────

def lerp_color(c1, c2, t):
    return tuple(int(a + (b-a)*t) for a,b in zip(c1,c2))

def dist(x1,y1,x2,y2):
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

def alpha_blend(bg, fg):
    fa=fg[3]/255.0; ba=bg[3]/255.0
    oa=fa+ba*(1-fa)
    if oa==0: return (0,0,0,0)
    r=int((fg[0]*fa+bg[0]*ba*(1-fa))/oa)
    g=int((fg[1]*fa+bg[1]*ba*(1-fa))/oa)
    b=int((fg[2]*fa+bg[2]*ba*(1-fa))/oa)
    return (r,g,b,int(oa*255))

def make_png(W, H, pixels):
    def chunk(n,d):
        c=zlib.crc32(n+d)&0xffffffff
        return struct.pack('>I',len(d))+n+d+struct.pack('>I',c)
    rows=b''
    for y in range(H):
        rows+=b'\x00'
        for x in range(W):
            r,g,b,a=pixels[y*W+x]; rows+=bytes([r,g,b,a])
    p=b'\x89PNG\r\n\x1a\n'
    p+=chunk(b'IHDR',struct.pack('>II',W,H)+bytes([8,6,0,0,0]))
    p+=chunk(b'IDAT',zlib.compress(rows,9))
    p+=chunk(b'IEND',b'')
    return p

def make_ico(pngs_dict):
    ss=sorted(pngs_dict.keys()); n=len(ss)
    ico=struct.pack('<HHH',0,1,n)
    offset=6+n*16; entries=b''; imgs=b''
    for sz in ss:
        d=pngs_dict[sz]; w=sz if sz<256 else 0
        entries+=struct.pack('<BBBBHHII',w,w,0,0,1,32,len(d),offset)
        imgs+=d; offset+=len(d)
    return ico+entries+imgs

# ── Desenare icon ─────────────────────────────────────────────

def draw_icon(size):
    W=H=size; s=size/256.0
    pixels=[(0,0,0,0)]*(W*H)

    def sp(x,y,col):
        x,y=int(x),int(y)
        if 0<=x<W and 0<=y<H:
            pixels[y*W+x]=alpha_blend(pixels[y*W+x],col)

    def fc(cx,cy,r,color,aa=1.0):
        for py in range(max(0,int(cy-r-2)),min(H,int(cy+r+3))):
            for px in range(max(0,int(cx-r-2)),min(W,int(cx+r+3))):
                d=dist(px+.5,py+.5,cx,cy)
                if d<=r+aa:
                    am=min(1.,max(0.,(r+aa-d)/aa))
                    sp(px,py,(*color[:3],int(color[3]*am)))

    def arc(cx,cy,r,t1,t2,col,thick):
        steps=max(60,int(abs(t2-t1)*r*s*.08))
        for i in range(steps+1):
            t=math.radians(t1+(t2-t1)*i/steps)
            fc(cx+r*math.cos(t),cy+r*math.sin(t),thick/2,col,.8)

    def rect(x1,y1,x2,y2,col,rx=0):
        for py in range(max(0,y1-1),min(H,y2+2)):
            for px in range(max(0,x1-1),min(W,x2+2)):
                ax=min(px-x1+1,x2-px+1,1.); ay=min(py-y1+1,y2-py+1,1.)
                am=max(0.,min(1.,ax))*max(0.,min(1.,ay))
                if rx>0:
                    for ccx,ccy in[(x1+rx,y1+rx),(x2-rx,y1+rx),(x1+rx,y2-rx),(x2-rx,y2-rx)]:
                        if px<x1+rx and py<y1+rx:
                            am=min(am,min(1.,max(0.,rx-dist(px+.5,py+.5,x1+rx,y1+rx)+1)))
                        if px>x2-rx and py<y1+rx:
                            am=min(am,min(1.,max(0.,rx-dist(px+.5,py+.5,x2-rx,y1+rx)+1)))
                        if px<x1+rx and py>y2-rx:
                            am=min(am,min(1.,max(0.,rx-dist(px+.5,py+.5,x1+rx,y2-rx)+1)))
                        if px>x2-rx and py>y2-rx:
                            am=min(am,min(1.,max(0.,rx-dist(px+.5,py+.5,x2-rx,y2-rx)+1)))
                if am>0: sp(px,py,(*col[:3],int(col[3]*am)))

    def strokes(segs,ox,oy,w,h,col,thick):
        for x1n,y1n,x2n,y2n in segs:
            x1=ox+x1n*w;y1=oy+y1n*h;x2=ox+x2n*w;y2=oy+y2n*h
            st=max(20,int(dist(x1,y1,x2,y2)*2))
            for i in range(st+1):
                t=i/st; fc(x1+(x2-x1)*t,y1+(y2-y1)*t,thick/2,col,.8)

    def draw_O(ox,oy,w,h,col,thick):
        pts=[(0.3,0),(0.7,0),(1.,.25),(1.,.75),(.7,1.),(.3,1.),(0.,.75),(0.,.25),(.3,0)]
        for i in range(len(pts)-1):
            x1=ox+pts[i][0]*w;y1=oy+pts[i][1]*h
            x2=ox+pts[i+1][0]*w;y2=oy+pts[i+1][1]*h
            st=max(20,int(dist(x1,y1,x2,y2)*2))
            for j in range(st+1):
                t=j/st; fc(x1+(x2-x1)*t,y1+(y2-y1)*t,thick/2,col,.8)

    cx=W/2; cy=H/2; R=W*.455
    # BG
    for py in range(H):
        for px in range(W):
            d=dist(px+.5,py+.5,cx,cy)
            if d<R+1:
                col=lerp_color((26,58,92),(13,32,53),py/H)
                pixels[py*W+px]=(*col,int(255*min(1.,R-d+1.)))
    # Ring
    for py in range(H):
        for px in range(W):
            d=dist(px+.5,py+.5,cx,cy)
            if R-3*s<=d<=R:
                sp(px,py,(46,117,182,int(120*min(1.,min(R-d+1,d-(R-3*s)+1)))))

    # Radio waves
    BL=(74,157,224)
    wcx=W*.30; wcy=cy
    for wr,wt,wa in[(22,4.,230),(36,3.,160),(50,2.2,90)]:
        arc(wcx,wcy,wr*s,-80,80,(*BL,wa),wt*s)
    fc(wcx,wcy,7*s,(*BL,255)); fc(wcx,wcy,12*s,(*BL,50))

    # Divider
    vx=int(W*.375)
    for py in range(int(H*.22),int(H*.80)):
        sp(vx,py,(46,117,182,90))

    # YO
    tw=W*.16; th=W*.22; lx=W*.405; ly=W*.20; lt=max(2,W*.022)
    W2=(255,255,255,255)
    strokes([(0.,0.,.5,.45),(1.,0.,.5,.45),(.5,.45,.5,1.)],lx,ly,tw,th,W2,lt)
    draw_O(lx+tw*1.3,ly,tw,th,W2,lt)

    # Accent bar
    by=int(H*.498)
    for py in range(by,by+max(2,int(5*s))):
        for px in range(int(W*.40),int(W*.935)):
            t=(px-W*.40)/(W*.935-W*.40)
            sp(px,py,(*lerp_color((74,157,224),(46,117,182),t),220))

    # JUDGE
    LB=(74,157,224,220)
    J=[(0.7,0,1,0),(.85,0,.85,.8),(0,.65,.85,.65),(0,1,.6,1)]
    U=[(0,0,0,.85),(0,.85,.5,1),(.5,1,1,.85),(1,0,1,.85)]
    D=[(0,0,0,1),(0,0,.6,0),(.6,0,1,.3),(1,.3,1,.7),(.6,1,1,.7),(0,1,.6,1)]
    G=[(1,0,.3,0),(.3,0,0,.3),(0,.3,0,.7),(0,.7,.3,1),(.3,1,1,1),(1,1,1,.5),(.6,.5,1,.5)]
    E=[(0,0,1,0),(0,0,0,1),(0,1,1,1),(0,.5,.8,.5)]
    sw=W*.08; sh=W*.10; st=max(1,W*.014); jx=W*.405; jy=H*.56; gap=W*.095
    for i,(s2) in enumerate([J,U,D,G,E]):
        strokes(s2,jx+i*gap,jy,sw,sh,LB,st)

    # PRO badge
    if size>=32:
        px1=int(W*.72);py1=int(H*.71);px2=int(W*.935);py2=int(H*.80)
        rect(px1,py1,px2,py2,(46,117,182,210),rx=int(4*s))
        P=[(0,0,0,1),(0,0,.6,0),(.6,0,1,.25),(1,.25,1,.5),(.6,.5,0,.5)]
        R2=[(0,0,0,1),(0,0,.6,0),(.6,0,1,.25),(1,.25,1,.5),(.6,.5,0,.5),(.5,.5,1,1)]
        pw=W*.055; ph=W*.070; pst=max(1,W*.013); pmx=px1+4*s; pmy=py1+4*s; pgap=W*.065
        strokes(P,pmx,pmy,pw,ph,(255,255,255,230),pst)
        strokes(R2,pmx+pgap,pmy,pw,ph,(255,255,255,230),pst)
        draw_O(pmx+pgap*2,pmy,pw,ph,(255,255,255,230),pst)

    return pixels

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir  = os.path.join(script_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)

    sizes = [16, 32, 48, 64, 128, 256]
    pngs  = {}
    for sz in sizes:
        px = draw_icon(sz)
        png = make_png(sz, sz, px)
        pngs[sz] = png
        out = os.path.join(icons_dir, f"icon_{sz}.png")
        with open(out, "wb") as f:
            f.write(png)
        print(f"  {sz}x{sz}: {len(png)} bytes → {out}")

    ico_path = os.path.join(script_dir, "app_icon.ico")
    ico = make_ico(pngs)
    with open(ico_path, "wb") as f:
        f.write(ico)
    print(f"\nICO: {len(ico)} bytes → {ico_path}")
    print("Gata! Iconul a fost generat.")
