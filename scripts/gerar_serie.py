# -*- coding: utf-8 -*-
"""
Orquestra a serie de 11 episodios Soninho (cada um com 60-90 min).

Uso:
  python scripts/gerar_serie.py --de 2 --ate 11 --minutos 75
  python scripts/gerar_serie.py --status
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
STATUS = ROOT / "SERIE_STATUS.json"
TEMAS = [
    "soninho da lua", "passeio no parque", "jardim ensolarado", "caminhada na floresta",
    "praia tranquila", "praça das estrelas", "rio sereno", "campo de flores",
    "neve no jardim", "passeio na cidade", "amanhecer no parque",
]


def rodar(args: list[str]) -> bool:
    print(">>", " ".join(args), flush=True)
    r = subprocess.run(args)
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--de", type=int, default=1)
    ap.add_argument("--ate", type=int, default=11)
    ap.add_argument("--minutos", type=float, default=75.0)
    ap.add_argument("--cena-s", type=float, default=35.0)
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    estado = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    if a.status:
        print(json.dumps(estado, ensure_ascii=False, indent=2)); return

    for ep in range(a.de, min(a.ate, len(TEMAS)) + 1):
        tema = TEMAS[ep - 1]
        saida = ROOT / "projetos" / f"ep{ep:02d}" / f"ep{ep:02d}_soninho.mp4"
        if saida.exists() and estado.get(str(ep), {}).get("status") == "OK":
            print(f"ep{ep:02d}: ja pronto, pulando"); continue
        print(f"\n=== EPISODIO {ep:02d}: {tema} ===", flush=True)
        seletor = "selecionar_cenas.py" if ep == 1 else "selecionar_cenas_outdoor.py"
        sel = [PY, str(ROOT / "scripts" / seletor),
               "--episodio", str(ep), "--tema", tema,
               "--minutos", str(a.minutos), "--cena-s", str(a.cena_s)]
        if not rodar(sel):
            estado[str(ep)] = {"tema": tema, "status": "FALHOU_SELECAO"}
            STATUS.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
            continue
        manifestos = sorted((ROOT / "manifestos").glob(f"ep{ep:02d}_*.json"))
        if not manifestos:
            estado[str(ep)] = {"tema": tema, "status": "SEM_MANIFESTO"}
            continue
        rend = [PY, str(ROOT / "scripts" / "render_sono.py"),
                "--manifesto", str(manifestos[-1]), "--workers", "2"]
        if ep >= 2:
            rend += ["--playlist", str(ROOT / "banco_musicas" / "playlist_ep02.json")]
        ok = rodar(rend)
        if ok:
            # ajuste de brilho/volume + overlay de inscricao (video do usuario,chroma key)
            rodar([PY, str(ROOT / "scripts" / "ajustar_final.py"), str(saida)])
            rodar([PY, str(ROOT / "scripts" / "adicionar_subscribe.py"), str(saida),
                   "--intervalo", "600"])
            auditoria = [PY, str(ROOT / "scripts" / "verificar_sono.py"), str(saida)]
            rodar(auditoria)
        estado[str(ep)] = {"tema": tema, "status": "OK" if ok else "FALHOU_RENDER",
                           "video": str(saida) if saida.exists() else ""}
        STATUS.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    print("STATUS FINAL:", json.dumps(estado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
