# -*- coding: utf-8 -*-
"""Substitui os videos do ep02 por videos APROVADOS na auditoria visual (outdoor)."""
import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
MAN = ROOT / "manifestos" / "ep02_outdoor_v2_passeio-no-parque.json"
IND = ROOT / "_indice_videos.json"
USADOS = ROOT / "clusters_usados.json"
# indices aprovados na folha de contato (outdoor real, sem stickman, sem interior)
APROVADOS = [2,5,10,15,17,18,19,23,26,28,29,30,32,37,40,41,42,43,44,46,47,50,56,63,66,67,68,77,82,84]

def main():
    man = json.loads(MAN.with_suffix(".antes_videos.json").read_text(encoding="utf-8")) \
          if MAN.with_suffix(".antes_videos.json").exists() else json.loads(MAN.read_text(encoding="utf-8"))
    indice = json.loads(IND.read_text(encoding="utf-8"))
    image_clusters = set(c.get("cluster_id") for c in man["cenas"] if c.get("cluster_id"))
    usados = set(json.loads(USADOS.read_text(encoding="utf-8"))) if USADOS.exists() else set()
    man["cenas"] = [c for c in man["cenas"] if c.get("tipo") != "video"]
    # cluster ids dos videos antigos deixam de contar como usados
    old = json.loads(MAN.with_suffix(".antes_videos.json").read_text(encoding="utf-8")) \
          if MAN.with_suffix(".antes_videos.json").exists() else None
    if old:
        old_ids = set(c["cluster_id"] for c in old["cenas"] if c.get("tipo")=="video" and c.get("cluster_id"))
        usados -= old_ids
    if not old:
        MAN.with_suffix(".antes_videos.json").write_text(json.dumps(man,ensure_ascii=False,indent=1),encoding="utf-8")
    escolhidos = []
    vistos = set()
    ep1_video_ids = set()
    for i in APROVADOS:
        if i >= len(indice): continue
        v = indice[i]
        cid = v.get("cluster_id") or ""
        chave = cid or v["caminho"]
        if chave in vistos or (cid and cid in image_clusters): continue
        vistos.add(chave); escolhidos.append(v)
        if len(escolhidos) >= 20: break
    print("VIDEOS APROVADOS SELECIONADOS:", len(escolhidos))
    # insere 1 video a cada 6 imagens
    novas = []
    t = 0.0
    iv = 0
    for k, c in enumerate(man["cenas"]):
        c["ordem"] = len(novas)+1
        c["inicio_s"] = round(t,1); c["fim_s"] = round(t+c["duracao_s"],1)
        novas.append(c); t += c["duracao_s"]
        if (k+1)%6==0 and iv<len(escolhidos):
            v = escolhidos[iv]; iv+=1
            dur = 8.0  # clips aprovados duram ~8 s
            novas.append({"ordem":len(novas)+1,"inicio_s":round(t,1),"fim_s":round(t+dur,1),
                          "duracao_s":dur,"caminho":v["caminho"],"titulo":v["titulo"],
                          "descricao":"Video outdoor aprovado na auditoria visual.",
                          "cluster_id":v.get("cluster_id",""),"ambiente":"Jardim",
                          "efeito":"folhinhas_vento","tipo":"video"})
            t += dur
    man["cenas"] = novas
    man["duracao_alcancada_s"] = round(t - (len(novas)-1)*4,1)
    man["videos"] = {"quantidade":iv,"sem_loop":True,"origem":"auditoria_visual"}
    MAN.write_text(json.dumps(man,ensure_ascii=False,indent=1),encoding="utf-8")
    ruins = [c for c in novas if any(p in (c["titulo"]+c["descricao"]).lower()
             for p in ["stick","palito","boneco de palito","cozinha","sala de estar"])]
    print("CENAS:",len(novas),"VIDEOS:",iv,"DURACAO:",round(t/60,1),"min | SUSPEITOS:",len(ruins))
    usados |= set(c["cluster_id"] for c in novas if c.get("cluster_id"))
    USADOS.write_text(json.dumps(sorted(usados),ensure_ascii=False,indent=1),encoding="utf-8")

if __name__ == "__main__":
    main()
