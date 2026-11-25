# -*- coding: utf-8 -*-
"""
Episodio 2 v2 — cenas outdoor + VIDEOS REAIS intercalados (cada video toca UMA vez).

- 125 imagens (35 s) + ~20 videos do acervo (duracao real do clipe);
- um video a cada 6 imagens;
- nenhum stickman/boneco de palito/avatar/humano;
- nenhuma cena de interior (casa, estudio, cozinha, quarto);
- nenhum cluster ja usado no episodio 1.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, io, unicodedata
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
DB = Path(r"E:\videomaker\banco de imagens\acervo.db")
MAN = ROOT / "manifestos"
USADOS = ROOT / "clusters_usados.json"
OUT = {"Jardim", "Floresta", "Praia", "Praça e parque", "Cidade", "Estrada e campo",
       "Neve e inverno", "Parque de diversões", "Fazenda", "Cena animada e ilustração"}
TERMOS = ["parque","pra a","praça","jardim","floresta","praia","campo","rua","cidade",
          "ar livre","grama"," rvore","ceu","nuvem","rio","lago","neve","passeio","caminh"]
PROIBIDOS = ["stick","palito","boneco","avatar","humano","crian","mulher","homem","pessoa",
             "detetive","casa","cozinha","quarto","sala de estar","interior","estúdio"]
EFEITOS = [("solzinho",["sol","manh","dia","campo","pra a","jardim"]),
           ("passarinhos",["passaro","ave","voar","ceu","ninho","arvore"]),
           ("folhinhas_vento",["folha","vento","arvore","floresta","jardim","grama"]),
           ("chuva",["chuva","gota","rio","lago","umido"]),
           ("bolinhas_sabao",["agua","praia","piscina","mar"]),
           ("cometa",["noite","estrela","lua","ceu"]),
           ("coracoes",["amor","carinho","amizade","abraco"]),
           ("soninho_zzz",["dormir","sono","descans"]),
           ("estrelinhas",["estrela","brilho","magia"])]

def norm(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",(s or "").lower()).encode("ascii","ignore").decode())
def base(c):
    s=Path(c).stem.lower(); s=re.sub(r"[0-9a-f]{6,}$","",s); s=re.sub(r"_scene[_ -]?[b-z]$","",s)
    return re.sub(r"_(b|c|d|e|f|1|2|3)$","",s)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--episodio",type=int,default=2)
    ap.add_argument("--tema",default="passeio no parque")
    ap.add_argument("--imagens",type=int,default=125)
    ap.add_argument("--videos",type=int,default=20)
    ap.add_argument("--cena-s",type=float,default=35.0)
    a=ap.parse_args()
    usados=set(json.loads(USADOS.read_text(encoding="utf-8"))) if USADOS.exists() else set()
    con=sqlite3.connect(f"file:{DB}?mode=ro",uri=True); con.row_factory=sqlite3.Row
    imgs,vids=[],[]
    for r in con.execute("SELECT * FROM midia"):
        if "Anim" not in (r["estilo_visual"] or ""): continue
        cam=r["caminho"] or ""
        if not cam.lower().endswith((".jpg",".jpeg",".png",".mp4")): continue
        if not Path(cam).is_file(): continue
        if r["ambiente_principal"] not in OUT: continue
        txt=norm(" ".join(str(r[k] or "") for k in ("titulo","descricao","palavras_chave","elementos","local")))
        if any(p in txt for p in PROIBIDOS): continue
        cid=r["cluster_id"] or ""
        if cid and cid in usados: continue
        if not any(k in txt for k in TERMOS): continue
        item=(r,cid,base(cam))
        if cam.lower().endswith(".mp4"):
            d=float(r["duracao_s"] or 0)
            if 3.5 <= d <= 12: vids.append((r,cid,base(cam),d))
        else:
            imgs.append(item)
    imgs.sort(key=lambda x:(-sum(1 for k in TERMOS if k in norm(x[0]["titulo"]+" "+x[0]["descricao"])),x[0]["caminho"]))
    vids.sort(key=lambda x:(-x[3],x[0]["caminho"]))
    vistos_c=set(); vistos_b=set(); imagens_ok=[]
    for r,cid,b in imgs:
        if cid and cid in vistos_c: continue
        if b and b in vistos_b: continue
        vistos_c.add(cid); vistos_b.add(b); imagens_ok.append(r)
        if len(imagens_ok)>=a.imagens: break
    videos_ok=[]
    for r,cid,b,d in vids:
        if cid and cid in vistos_c: continue
        if b and b in vistos_b: continue
        vistos_c.add(cid); vistos_b.add(b); videos_ok.append((r,d))
        if len(videos_ok)>=a.videos: break
    print(f"CANDIDATOS: imagens={len(imgs)} videos={len(vids)} | USADOS: {len(imagens_ok)} imagens + {len(videos_ok)} videos")

    cenas=[]; iv=0; t=0.0
    for i,r in enumerate(imagens_ok):
        txt=norm((r["descricao"] or "")+" "+(r["titulo"] or ""))
        efeito=next((e for e,ks in EFEITOS if any(k in txt for k in ks)),"folhinhas_vento")
        cenas.append({"ordem":len(cenas)+1,"inicio_s":round(t,1),"fim_s":round(t+a.cena_s,1),
                      "duracao_s":a.cena_s,"caminho":r["caminho"],"titulo":r["titulo"],
                      "descricao":(r["descricao"] or "")[:200],"cluster_id":r["cluster_id"],
                      "ambiente":r["ambiente_principal"],"efeito":efeito,"tipo":"imagem"})
        t+=a.cena_s
        if (i+1)%6==0 and iv<len(videos_ok):
            rv,d=videos_ok[iv]; iv+=1
            cenas.append({"ordem":len(cenas)+1,"inicio_s":round(t,1),"fim_s":round(t+d,1),
                          "duracao_s":round(d,1),"caminho":rv["caminho"],"titulo":rv["titulo"],
                          "descricao":(rv["descricao"] or "")[:200],"cluster_id":rv["cluster_id"],
                          "ambiente":rv["ambiente_principal"],"efeito":"folhinhas_vento","tipo":"video"})
            t+=d
    bruto=sum(c["duracao_s"] for c in cenas)-(len(cenas)-1)*4
    pac={"episodio":a.episodio,"tema":a.tema,"modo":"outdoor_v2",
         "duracao_alvo_s":int(a.imagens*a.cena_s+len(videos_ok)*8),
         "duracao_alcancada_s":round(bruto,1),"videos":{"quantidade":len(videos_ok),"sem_loop":True},
         "cenas":cenas,"regra":"outdoor, sem stickman, video toca uma vez, sem repetir cluster"}
    MAN.mkdir(parents=True,exist_ok=True)
    dest=MAN/f"ep{a.episodio:02d}_outdoor_v2_{re.sub('[^a-z0-9]+','-',norm(a.tema)).strip('-')[:30]}.json"
    dest.write_text(json.dumps(pac,ensure_ascii=False,indent=1),encoding="utf-8")
    print("MANIFESTO:",dest)
    print("CENAS:",len(cenas),"VIDEOS:",len(videos_ok),"DURACAO BRUTA:",round(bruto/60,1),"min")
    # auditoria dura
    ruins=[c for c in cenas if any(p in norm(c["titulo"]+" "+c["descricao"]) for p in ["stick","palito","boneco","avatar"])]
    print("STICKMAN NA SELECAO:",len(ruins))
    usados|=set(c["cluster_id"] for c in cenas if c["cluster_id"])
    USADOS.write_text(json.dumps(sorted(usados),ensure_ascii=False,indent=1),encoding="utf-8")

if __name__=="__main__":
    main()
