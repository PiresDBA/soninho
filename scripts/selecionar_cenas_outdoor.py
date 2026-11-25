# -*- coding: utf-8 -*-
"""
Seletor de cenas OUTDOOR do canal Soninho — so imagens animadas do acervo,
com personagens fora de casa (parque, jardim, floresta, praia, rua, campo).
Nunca reusa clusters ja usados em episodios anteriores.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, io, unicodedata
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DB = Path(r"E:\videomaker\banco de imagens\acervo.db")
MAN = ROOT / "manifestos"
USADOS = ROOT / "clusters_usados.json"
OUTDOOR = {
    "parque": 12, "pra a": 10, "praça": 10, "jardim": 10, "floresta": 10,
    "praia": 9, "campo": 9, "grama": 9, " rvore": 9, "ar livre": 12,
    "caminh": 9, "passeio": 9, "rua": 7, "cidade": 6, "c u": 7,
    "nuvem": 7, "rio": 8, "lago": 8, "montanha": 8, "neve": 7,
    "quadra": 7, "jardim zool": 9, "parque de divers": 9, " varanda": 6,
}
AMBIENTES = {"Jardim", "Floresta", "Praia", "Praça e parque", "Cidade",
             "Estrada e campo", "Neve e inverno", "Parque de diversões", "Urbano e Arquitetura"}
INTERIOR = ["quarto", "sala de estar", "cozinha", "cama", "sof", "interior",
            "dentro de casa", "banheiro", "escrit rio", "gabinete", "arm rio"]
PROIBIDOS = ["stickman", "avatar", "humano", "crian", "mulher", "homem", "pessoa",
             "ensolarad", "energia", "corrida", "briga", "susto", "monstro"]
EFEITOS = [("solzinho", ["sol", "manh", "dia", "campo", "praca", "jardim"]),
           ("passarinhos", ["passaro", "ave", "voar", "ceu", "ninho", "arvore"]),
           ("folhinhas_vento", ["folha", "vento", "arvore", "floresta", "jardim", "grama"]),
           ("chuva", ["chuva", "gota", "umido", "rio", "lago"]),
           ("bolinhas_sabao", ["agua", "praia", "piscina", "mar"]),
           ("cometa", ["noite", "estrela", "lua", "ceu"]),
           ("coracoes", ["amor", "carinho", "amizade", "abraco"]),
           ("soninho_zzz", ["dormir", "sono", "descans"]),
           ("estrelinhas", ["estrela", "brilho", "magia"])]

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s)

def base_nome(c: str) -> str:
    s = Path(c).stem.lower()
    s = re.sub(r"[0-9a-f]{6,}$", "", s)
    s = re.sub(r"_scene[_ -]?[b-z]$", "", s)
    return re.sub(r"_(b|c|d|e|f|1|2|3)$", "", s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodio", type=int, default=2)
    ap.add_argument("--tema", default="passeio no parque")
    ap.add_argument("--minutos", type=float, default=75.0)
    ap.add_argument("--cena-s", type=float, default=35.0)
    a = ap.parse_args()
    total_s = int(a.minutos * 60)
    n_cenas = -(-total_s // int(a.cena_s))
    usados = set(json.loads(USADOS.read_text(encoding="utf-8"))) if USADOS.exists() else set()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cand = []
    for r in con.execute("SELECT * FROM midia"):
        if "Anim" not in (r["estilo_visual"] or ""):
            continue
        if not (r["caminho"] or "").lower().endswith((".jpg", ".jpeg", ".png", ".mp4")):
            continue
        if not Path(r["caminho"]).is_file():
            continue
        txt = norm(" ".join(str(r[k] or "") for k in
                            ("titulo", "descricao", "palavras_chave", "elementos",
                             "categoria_principal", "local")))
        if any(p in txt for p in PROIBIDOS) or any(i in txt for i in INTERIOR):
            continue
        pts = sum(v for k, v in OUTDOOR.items() if k in txt)
        if r["ambiente_principal"] in AMBIENTES:
            pts += 5
        if pts < 8:
            continue
        cand.append((pts, r))
    cand.sort(key=lambda x: (-x[0], x[1]["caminho"]))
    vistos_c, vistos_b, sel, evitados = set(), set(), [], 0
    for pts, r in cand:
        cid, b = r["cluster_id"] or "", base_nome(r["caminho"])
        if cid and cid in vistos_c: continue
        if b and b in vistos_b: continue
        if cid and cid in usados:
            evitados += 1; continue
        vistos_c.add(cid); vistos_b.add(b)
        ini = round(len(sel) * a.cena_s, 1)
        txt = norm((r["descricao"] or "") + " " + (r["titulo"] or ""))
        efeito = next((e for e, chaves in EFEITOS if any(k in txt for k in chaves)), "folhinhas_vento")
        sel.append({"ordem": len(sel)+1, "inicio_s": ini, "fim_s": round(ini+a.cena_s,1),
                    "duracao_s": a.cena_s, "caminho": r["caminho"], "titulo": r["titulo"],
                    "descricao": (r["descricao"] or "")[:220], "cluster_id": cid,
                    "ambiente": r["ambiente_principal"], "score": pts, "efeito": efeito})
        if len(sel) >= n_cenas: break
    print(f"CANDIDATOS OUTDOOR: {len(cand)} | EVITADOS POR USO: {evitados} | SELECIONADAS: {len(sel)}")
    if len(sel) < n_cenas:
        print("AVISO: faltam cenas. Use --cena-s maior ou --minutos menor.")
    pac = {"episodio": a.episodio, "tema": a.tema, "modo": "outdoor",
           "duracao_alvo_s": total_s, "duracao_alcancada_s": round(len(sel)*a.cena_s,1),
           "cenas": sel, "regra": "somente cenas externas, animacao, sem repeticao de cluster"}
    MAN.mkdir(parents=True, exist_ok=True)
    slug = f"ep{a.episodio:02d}_outdoor_" + re.sub(r"[^a-z0-9]+","-",norm(a.tema)).strip("-")[:35]
    dest = MAN / f"{slug}.json"
    dest.write_text(json.dumps(pac, ensure_ascii=False, indent=1), encoding="utf-8")
    dest.with_suffix(".md").write_text("\n".join(
        [f"# Episódio {a.episodio} — {a.tema} (outdoor)", "",
         f"**{len(sel)} cenas · {len(sel)*a.cena_s/60:.1f} min**", ""] +
        [f"- {c['ordem']}. {c['titulo']}" for c in sel[:20]]), encoding="utf-8")
    print("MANIFESTO:", dest)
    if len(sel) >= n_cenas:
        usados |= set(c["cluster_id"] for c in sel if c["cluster_id"])
        USADOS.write_text(json.dumps(sorted(usados), ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
