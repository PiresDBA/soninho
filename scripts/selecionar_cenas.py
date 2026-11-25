# -*- coding: utf-8 -*-
"""
Seletor de cenas do canal Soninho — so usa o acervo existente (sem IA, sem Flow).

Regras duras:
  - apenas animacao/cartoon (o canal e 100% desenho);
  - temas calmos (dormir, noite, lua, estrela, cama, cobertor, chuva, jardim...);
  - sem stickman, sem avatar, sem humanos, sem cenas "ensolaradas/energia";
  - no maximo UMA cena por cluster visual (anti-repeticao do contrato);
  - clusters ja usados em outros episodios sao descartados enquanto houver alternativas.

Uso:
  python scripts/selecionar_cenas.py --episodio 1 --minutos 75 --cena-s 35 --tema lua
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DB = Path(r"E:\videomaker\banco de imagens\acervo.db")
MAN = ROOT / "manifestos"
USADOS = ROOT / "clusters_usados.json"

CALMOS = {
    "dormir": 10, "dormindo": 10, "sono": 9, "sonhar": 8, "cobertor": 7,
    "travesseiro": 7, "cama": 6, "lua": 8, "estrela": 7, "noite": 7,
    "chuva": 6, "calmo": 9, "suave": 7, "aconchegante": 8, "relax": 8,
    "nuvem": 5, "jardim": 4, "floresta": 4, "brisa": 6, "silencio": 6,
}
AMBIENTES_OK = {"Casa", "Jardim", "Floresta", "Espaço", "Praia", "Neve e inverno",
                "Cena animada e ilustração", "Praça e parque"}
PROIBIDOS = ["stickman", "avatar", "humano", "crian", "mulher", "homem", "pessoa",
             "ensolarad", "energia", "corrida", "briga", "susto", "monstro"]
EFEITOS = [
    ("estrelinhas", ["estrela", "lua", "noite", "espaco", "sonho"]),
    ("chuva", ["chuva", "gota", "tempestade", "agua"]),
    ("folhinhas_vento", ["folha", "vento", "jardim", "floresta", "arvore"]),
    ("coracoes", ["amor", "carinho", "abraço", "coracao"]),
    ("soninho_zzz", ["dormir", "dormindo", "sono", "cama", "cobertor"]),
]


def norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s)


def base_nome(caminho: str) -> str:
    s = Path(caminho).stem.lower()
    s = re.sub(r"[0-9a-f]{6,}$", "", s)
    s = re.sub(r"_scene[_ -]?[b-z]$", "", s)
    return re.sub(r"_(b|c|d|e|f|1|2|3)$", "", s)


def escolher_efeito(texto: str, tema: str) -> str:
    t = norm(texto + " " + tema)
    for efeito, chaves in EFEITOS:
        if any(k in t for k in chaves):
            return efeito
    return "folhinhas_vento"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodio", type=int, default=1)
    ap.add_argument("--tema", default="soninho da lua")
    ap.add_argument("--minutos", type=float, default=75.0)
    ap.add_argument("--cena-s", type=float, default=35.0)
    ap.add_argument("--limite", type=int, default=0, help="0 = sem limite de cenas")
    ap.add_argument("--permitir-reuso", action="store_true")
    args = ap.parse_args()

    total_s = int(args.minutos * 60)
    n_cenas = args.limite or -(-total_s // int(args.cena_s))
    usados = set(json.loads(USADOS.read_text(encoding="utf-8"))) if USADOS.exists() else set()

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    candidatos = []
    for r in con.execute("SELECT * FROM midia"):
        if "Anim" not in (r["estilo_visual"] or ""):
            continue
        if not (r["caminho"] or "").lower().endswith((".jpg", ".jpeg", ".png", ".mp4")):
            continue
        if not Path(r["caminho"]).is_file():
            continue
        txt = norm(" ".join(str(r[k] or "") for k in
                            ("titulo", "descricao", "palavras_chave", "elementos", "categoria_principal")))
        if any(p in txt for p in PROIBIDOS):
            continue
        pts = sum(peso for chave, peso in CALMOS.items() if chave in txt)
        if r["ambiente_principal"] in AMBIENTES_OK:
            pts += 3
        for token in norm(args.tema).split():
            if len(token) > 3 and token in txt:
                pts += 6
        if pts < 6:
            continue
        candidatos.append((pts, r))

    candidatos.sort(key=lambda x: (-x[0], x[1]["caminho"]))
    vistos_cluster: set[str] = set()
    vistos_base: set[str] = set()
    selecionadas = []
    reaproveitadas = 0
    for pts, r in candidatos:
        cid = r["cluster_id"] or ""
        b = base_nome(r["caminho"])
        if cid and cid in vistos_cluster:
            continue
        if b and b in vistos_base:
            continue
        if cid and cid in usados and not args.permitir_reuso:
            reaproveitadas += 1
            continue
        vistos_cluster.add(cid)
        vistos_base.add(b)
        inicio = round(len(selecionadas) * args.cena_s, 1)
        selecionadas.append({
            "ordem": len(selecionadas) + 1,
            "inicio_s": inicio,
            "fim_s": round(inicio + args.cena_s, 1),
            "duracao_s": args.cena_s,
            "caminho": r["caminho"],
            "titulo": r["titulo"],
            "descricao": (r["descricao"] or "")[:220],
            "cluster_id": cid,
            "ambiente": r["ambiente_principal"],
            "score": pts,
            "efeito": escolher_efeito((r["descricao"] or "") + " " + (r["titulo"] or ""), args.tema),
        })
        if len(selecionadas) >= n_cenas:
            break

    if len(selecionadas) < n_cenas:
        print(f"AVISO: pediu {n_cenas} cenas, encontrou {len(selecionadas)} "
              f"({reaproveitadas} descartadas por ja terem sido usadas).")
        print("Opcoes: --permitir-reuso, --cena-s maior ou --minutos menor.")
    pacote = {
        "episodio": args.episodio, "tema": args.tema,
        "duracao_alvo_s": total_s, "duracao_alcancada_s": round(len(selecionadas) * args.cena_s, 1),
        "cenas": selecionadas, "clusters_descartados_por_uso": reaproveitadas,
        "regra": "uma cena por cluster, sem humanos, sem repeticao entre episodios",
    }
    MAN.mkdir(parents=True, exist_ok=True)
    slug = f"ep{args.episodio:02d}_" + re.sub(r"[^a-z0-9]+", "-", norm(args.tema)).strip("-")[:40]
    destino = MAN / f"{slug}.json"
    destino.write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    linhas = [f"# Episódio {args.episodio} — {args.tema}", "",
              f"**{len(selecionadas)} cenas · {pacote['duracao_alcancada_s']/60:.1f} min · "
              f"{reaproveitadas} clusters evitados por já terem sido usados**", ""]
    for c in selecionadas[:15]:
        linhas.append(f"- {c['ordem']:3d}. {c['titulo'][:55]} [{c['efeito']}]")
    if len(selecionadas) > 15:
        linhas.append(f"- ... e mais {len(selecionadas)-15} cenas")
    destino.with_suffix(".md").write_text("\n".join(linhas), encoding="utf-8")
    print(f"MANIFESTO: {destino}")
    print(f"CENAS: {len(selecionadas)} | DURACAO: {pacote['duracao_alcancada_s']/60:.1f} min | "
          f"CLUSTERS UNICOS: {len(set(c['cluster_id'] for c in selecionadas if c['cluster_id']))}")

    if not args.permitir_reuso and len(selecionadas) >= n_cenas:
        usados |= set(c["cluster_id"] for c in selecionadas if c["cluster_id"])
        USADOS.write_text(json.dumps(sorted(usados), ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
