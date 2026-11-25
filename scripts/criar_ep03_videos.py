# -*- coding: utf-8 -*-
"""Episodio 3: SÓ vídeos (aprovados visualmente) + fotos relacionadas, com 30 overframes."""
from __future__ import annotations
import json, re, sqlite3, sys, io, unicodedata
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
IND = ROOT / "_indice_videos.json"
DB = r"E:\videomaker\banco de imagens\acervo.db"
MAN = ROOT / "manifestos"
# indices aprovados na auditoria visual (p1/p2/p3) — outdoor + espaço/lua
APROVADOS = [0,2,5,6,10,15,17,18,19,23,25,26,28,29,30,32,35,36,37,40,41,42,43,44,46,47,49,50,56,63,66,67,68,76,77,82,84]
MOVIMENTOS = ["estrela_cadente","estrelinhas_piscando","galho_caindo","mosquinha_voando",
    "borboletas","folhas_redemoinho","gotas_espelho","nuvens_passando","lua_crescente",
    "brilho_suave","coracoes_subindo","bolhas_subindo","confete_colorido","flocos_de_neve",
    "petalas","sementes_vento","espuma_subindo","onda_luminosa","tracos_de_luz",
    "po_de_estrelas","fagulhas","arco_iris","folha_giro","pluminhas","pingos_finos",
    "lagrimas_luz","borboletas_luz","zeco_subindo","estrela_giro","brisa_suave"]

def norm(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",(s or "").lower()).encode("ascii","ignore").decode())
def tokens(s): return set(w for w in norm(s).split() if len(w)>3)

def main():
    indice = json.loads(IND.read_text(encoding="utf-8"))
    videos = [indice[i] for i in APROVADOS if i < len(indice)]
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); con.row_factory = sqlite3.Row
    imagens = []
    for r in con.execute("select caminho,titulo,descricao,cluster_id,ambiente_principal from midia where tipo='imagem' and estilo_visual like '%Anim%'"):
        t = norm((r["titulo"] or "")+" "+(r["descricao"] or ""))
        if any(p in t for p in ["stick","palito","boneco","avatar","humano","cozinha","quarto","sala de estar"]): continue
        if r["ambiente_principal"] in ("Stickman","Estúdio e gráficos","Casa"): continue
        imagens.append((r, tokens(r["titulo"]+" "+r["descricao"])))
    print("VIDEOS:",len(videos),"| IMAGENS CANDIDATAS:",len(imagens))
    cenas=[]; t=0.0; mi=0; usadas=set()
    def add(caminho,titulo,desc,cid,amb,efeito,dur,tipo):
        nonlocal t
        cenas.append({"ordem":len(cenas)+1,"inicio_s":round(t,1),"fim_s":round(t+dur,1),
                      "duracao_s":dur,"caminho":caminho,"titulo":titulo,"descricao":desc[:180],
                      "cluster_id":cid,"ambiente":amb,"efeito":efeito,"tipo":tipo})
        t+=dur
    anterior=""
    for v in videos:
        txt = norm(v["titulo"])
        # agrupa: escolhe 3 fotos com maior sobreposicao de tokens com o video
        tk = tokens(txt)
        cand = sorted(imagens, key=lambda x: -len(x[1]&tk))[:4]
        if len(cand) < 4:
            passo = 97
            for k in range(len(cand), 4):
                cand.append(imagens[(mi*passo + k*131) % len(imagens)])
        efeito = MOVIMENTOS[mi % len(MOVIMENTOS)]; mi+=1
        add(v["caminho"], v["titulo"], "Video aprovado na auditoria visual.",
            v.get("cluster_id",""), "Jardim", efeito, 8.0, "video")
        for r,_ in cand:
            if r["caminho"] in usadas: continue
            usadas.add(r["caminho"])
            efeito = MOVIMENTOS[mi % len(MOVIMENTOS)]; mi+=1
            if efeito == anterior:
                efeito = MOVIMENTOS[(mi+7) % len(MOVIMENTOS)]; mi+=1
            anterior = efeito
            add(r["caminho"], r["titulo"], r["descricao"], r["cluster_id"],
                r["ambiente_principal"], efeito, 35.0, "imagem")
    bruto = t - (len(cenas)-1)*4
    pac = {"episodio":3,"tema":"somente videos - jardim, parque e lua","modo":"videos_relacionados",
           "duracao_alvo_s":3900,"duracao_alcancada_s":round(bruto,1),
           "cenas":cenas,"overframes":len(MOVIMENTOS),
           "regra":"video toca uma vez, fotos relacionadas intercaladas, 30 movimentos"}
    MAN.mkdir(parents=True,exist_ok=True)
    dest=MAN/"ep03_somente_videos.json"
    dest.write_text(json.dumps(pac,ensure_ascii=False,indent=1),encoding="utf-8")
    nv=sum(1 for c in cenas if c["tipo"]=="video")
    print("MANIFESTO:",dest,"| CENAS:",len(cenas),"| VIDEOS:",nv,"| FOTOS:",len(cenas)-nv,
          "| DURACAO:",round(bruto/60,1),"min")

if __name__=="__main__":
    main()
