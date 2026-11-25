# -*- coding: utf-8 -*-
"""
Cria 30 NOVos sprites transparentes de overframe em efeitos/.

Cada sprite e um PNG RGBA pequeno; o movimento (queda, subida, deriva, giro,
piscada) e aplicado pelo renderizador via expressao de overlay.
"""
from __future__ import annotations
import math, sys, io
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SAIDA = Path(__file__).resolve().parents[1] / "efeitos"
SAIDA.mkdir(parents=True, exist_ok=True)
S = 4

EFEITOS = [
    # (nome, categoria de movimento, forma, cor RGB, tamanho)
    ("estrela_cadente", "cair", "estrela", (255, 232, 170), (40, 40)),
    ("estrelinhas_piscando", "piscar", "estrela", (255, 245, 205), (30, 30)),
    ("galho_caindo", "cair", "galho", (150, 110, 70), (70, 30)),
    ("mosquinha_voando", "deriva", "mosca", (90, 80, 70), (26, 22)),
    ("borboletas", "deriva", "borboleta", (255, 180, 210), (44, 38)),
    ("folhas_redemoinho", "giro", "folha", (150, 200, 110), (34, 26)),
    ("gotas_espelho", "cair", "gota", (170, 215, 255), (22, 30)),
    ("nuvens_passando", "deriva", "nuvem", (225, 235, 245), (110, 50)),
    ("lua_crescente", "deriva", "lua", (255, 244, 205), (60, 60)),
    ("brilho_suave", "piscar", "brilho", (255, 238, 190), (80, 80)),
    ("coracoes_subindo", "subir", "coracao", (255, 150, 175), (36, 34)),
    ("bolhas_subindo", "subir", "bolha", (190, 225, 255), (38, 38)),
    ("confete_colorido", "cair", "confete", (255, 190, 120), (20, 28)),
    ("flocos_de_neve", "cair", "neve", (235, 245, 255), (28, 28)),
    ("petalas", "cair", "petala", (255, 195, 210), (30, 22)),
    ("sementes_vento", "deriva", "semente", (200, 170, 120), (18, 26)),
    ("espuma_subindo", "subir", "bolha", (230, 245, 255), (32, 32)),
    ("onda_luminosa", "deriva", "onda", (180, 220, 255), (100, 40)),
    ("tracos_de_luz", "deriva", "traco", (255, 225, 160), (80, 20)),
    ("po_de_estrelas", "subir", "estrela", (255, 250, 220), (18, 18)),
    ("fagulhas", "subir", "fagulha", (255, 200, 130), (16, 16)),
    ("arco_iris", "piscar", "arco", (255, 210, 170), (120, 70)),
    ("folha_giro", "giro", "folha", (170, 210, 120), (36, 28)),
    ("pluminhas", "deriva", "pluma", (245, 240, 225), (34, 26)),
    ("pingos_finos", "cair", "gota", (190, 225, 255), (14, 22)),
    ("lagrimas_luz", "cair", "gota", (255, 230, 190), (18, 26)),
    ("borboletas_luz", "deriva", "borboleta", (255, 240, 180), (40, 34)),
    ("zeco_subindo", "subir", "z", (225, 240, 255), (42, 30)),
    ("estrela_giro", "giro", "estrela", (255, 235, 180), (32, 32)),
    ("brisa_suave", "deriva", "brisa", (210, 235, 255), (90, 30)),
]


def desenhar(forma: str, cor, w: int, h: int) -> Image.Image:
    W, H = w*S, h*S
    img = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(img)
    c = (*cor, 190)
    if forma == "estrela":
        pts=[]
        for i in range(10):
            a=-math.pi/2+i*math.pi/5
            r=(W*0.46 if i%2==0 else W*0.20)
            pts.append((W/2+r*math.cos(a), H/2+r*math.sin(a)))
        d.polygon(pts, fill=c)
        d.ellipse((W*0.40,H*0.40,W*0.60,H*0.60), fill=(255,255,255,220))
    elif forma == "coracao":
        r=int(W*0.26); cx,cy=W//2,int(H*0.42)
        d.ellipse((cx-r,cy-r,cx,cy+int(r*0.5)),fill=c)
        d.ellipse((cx,cy-r,cx+r,cy+int(r*0.5)),fill=c)
        d.polygon([(cx-r,cy),(cx+r,cy),(cx,cy+int(r*1.9))],fill=c)
    elif forma in ("bolha", "brilho", "gota"):
        d.ellipse((W*0.12,H*0.12,W*0.88,H*0.88), outline=c, width=3*S)
        d.ellipse((W*0.28,H*0.20,W*0.42,H*0.34), fill=(255,255,255,150))
    elif forma == "folha":
        d.ellipse((W*0.10,H*0.25,W*0.90,H*0.75), fill=c)
        d.line((W*0.10,H*0.50,W*0.90,H*0.50), fill=(255,255,255,110), width=2*S)
    elif forma == "galho":
        d.line((W*0.05,H*0.70,W*0.95,H*0.30), fill=c, width=4*S)
        for i in (0.35,0.62,0.82):
            x=int(W*i); y=int(H*(0.70-0.40*i))
            d.ellipse((x-6*S,y-6*S,x+6*S,y+6*S), fill=c)
    elif forma == "mosca":
        d.ellipse((W*0.35,H*0.35,W*0.65,H*0.65), fill=c)
        d.ellipse((W*0.10,H*0.20,W*0.42,H*0.48), fill=(255,255,255,120))
        d.ellipse((W*0.58,H*0.20,W*0.90,H*0.48), fill=(255,255,255,120))
    elif forma == "borboleta":
        for s in (-1,1):
            cx=W/2+s*W*0.20
            d.ellipse((cx-W*0.20,H*0.15,cx+W*0.20,H*0.55), fill=c)
            d.ellipse((cx-W*0.16,H*0.50,cx+W*0.16,H*0.85), fill=(*cor,150))
        d.line((W/2,H*0.35,W/2,H*0.70), fill=c, width=3*S)
    elif forma == "nuvem":
        for cx,cy,r in [(0.3,0.6,0.28),(0.5,0.45,0.34),(0.7,0.6,0.27)]:
            d.ellipse((W*(cx-r),H*(cy-r),W*(cx+r),H*(cy+r)), fill=c)
    elif forma == "lua":
        d.ellipse((W*0.12,H*0.12,W*0.88,H*0.88),fill=c)
        d.ellipse((W*0.34,H*0.20,W*1.0,H*0.80),fill=(0,0,0,0))
    elif forma == "confete":
        d.rectangle((W*0.25,H*0.10,W*0.75,H*0.90),fill=c)
    elif forma == "neve":
        for a in range(6):
            ang=a*math.pi/3
            d.line((W/2,H/2,W/2+W*0.42*math.cos(ang),H/2+H*0.42*math.sin(ang)),fill=c,width=2*S)
    elif forma == "petala":
        d.ellipse((W*0.10,H*0.30,W*0.90,H*0.70),fill=c)
    elif forma == "semente":
        d.ellipse((W*0.35,H*0.10,W*0.65,H*0.90),fill=c)
        d.line((W*0.5,H*0.5,W*0.8,H*0.9),fill=(255,255,255,130),width=2*S)
    elif forma == "onda":
        for k in range(2):
            pts=[(x, H/2+math.sin(x/W*2*math.pi+k*math.pi)*H*0.2) for x in range(0,W,4*S)]
            d.line(pts,fill=c,width=3*S)
    elif forma == "traco":
        grad=Image.new("RGBA",(W,H),(0,0,0,0))
        gd=ImageDraw.Draw(grad)
        for x in range(W):
            a=int(200*x/W)
            gd.line((x,0,x,H),fill=(*cor,a))
        img=grad
    elif forma == "fagulha":
        d.ellipse((W*0.25,H*0.25,W*0.75,H*0.75),fill=(255,255,255,230))
    elif forma == "arco":
        for i,(rr,cc) in enumerate([(0.44,(255,170,170)),(0.40,(255,210,160)),(0.36,(255,245,170)),
                                    (0.32,(180,235,170)),(0.28,(170,210,255))]):
            d.arc((W*(0.5-rr),H*(0.85-rr),W*(0.5+rr),H*(0.85+rr)),180,360,fill=(*cc,150),width=3*S)
    elif forma == "pluma":
        d.ellipse((W*0.20,H*0.35,W*0.80,H*0.65),fill=c)
        d.line((W*0.10,H*0.55,W*0.90,H*0.45),fill=(255,255,255,140),width=2*S)
    elif forma == "z":
        d.line((W*0.15,H*0.25,W*0.85,H*0.25),fill=c,width=4*S)
        d.line((W*0.85,H*0.25,W*0.20,H*0.75),fill=c,width=4*S)
        d.line((W*0.20,H*0.75,W*0.85,H*0.75),fill=c,width=4*S)
    elif forma == "brisa":
        for k in range(3):
            y=int(H*(0.25+k*0.25))
            d.line((W*0.05,y,W*0.75,y),fill=c,width=2*S)
            d.arc((W*0.65,y-6*S,W*0.85,y+6*S),0,180,fill=c,width=2*S)
    return img.resize((w,h), Image.LANCZOS)

def main():
    meta=[]
    for nome,cat,forma,cor,tam in EFEITOS:
        dest=SAIDA/(nome+".png")
        if not dest.exists():
            desenhar(forma,cor,*tam).save(dest)
        meta.append({"nome":nome,"movimento":cat,"arquivo":dest.name})
        print("CRIADO:",dest.name,cat)
    (SAIDA/"movimentos.json").write_text(
        __import__("json").dumps(meta,ensure_ascii=False,indent=1),encoding="utf-8")
    print("TOTAL:",len(meta),"novos overframes em",SAIDA)

if __name__=="__main__":
    main()
