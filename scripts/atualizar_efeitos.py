# -*- coding: utf-8 -*-
"""
Reatribui efeitos de overlay cena a cena, garantindo VARIEDADE:
  - nunca dois efeitos iguais em cenas consecutivas;
  - nenhum efeito domina mais que ~18% das cenas;
  - vocabulario rico: cometa, chuva, solzinho, passarinhos, bolhas, coracao,
    zzz, folhas, estrelas.

Uso: python scripts/atualizar_efeitos.py manifestos/ep01_....json
"""
from __future__ import annotations

import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REGRAS = [
    ("chuva", ["chuva", "gota", "tempestad", "agua", "umido"]),
    ("bolinhas_sabao", ["banho", "bolha", "espuma", "piscina", "lava"]),
    ("cometa", ["espaco", "astronaut", "foguete", "estrela cadente", "galaxia", "lua", "sistema solar"]),
    ("passarinhos", ["passaro", "pajaro", "ave", "voar", "ceu", "ninho"]),
    ("solzinho", ["sol ", "ensolarad", "campo", "praca", "jardim claro", "manha"]),
    ("folhinhas_vento", ["folha", "vento", "arvore", "floresta", "jardim", "grama", "parque"]),
    ("coracoes", ["amor", "carinho", "abraco", "coracao", "amizade"]),
    ("soninho_zzz", ["dormir", "dormindo", "sono", "cama", "cobertor", "travesseiro", "roncar"]),
    ("estrelinhas", ["estrela", "noite", "sonho", "magia", "brilho", "ceu estrelado"]),
]
PALETA = [r[0] for r in REGRAS]
LIMITE = 0.18


def norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python atualizar_efeitos.py <manifesto.json>"); return
    caminho = Path(sys.argv[1])
    man = json.loads(caminho.read_text(encoding="utf-8"))
    cenas = man["cenas"]
    contagem: dict[str, int] = {}
    anterior = ""
    for i, c in enumerate(cenas):
        txt = norm(" ".join(str(c.get(k, "")) for k in ("titulo", "descricao", "ambiente")))
        cand = [nome for nome, chaves in REGRAS if any(k in txt for k in chaves)]
        if not cand:
            cand = ["folhinhas_vento", "soninho_zzz", "estrelinhas"]
        # ordena por preferencia, mas descarta o anterior e os esgotados
        limite_n = max(1, int(len(cenas) * LIMITE))
        escolhido = None
        for nome in cand + [p for p in PALETA if p not in cand]:
            if nome == anterior:
                continue
            if contagem.get(nome, 0) >= limite_n:
                continue
            escolhido = nome
            break
        if escolhido is None:
            escolhido = next(p for p in PALETA if p != anterior)
        c["efeito"] = escolhido
        contagem[escolhido] = contagem.get(escolhido, 0) + 1
        anterior = escolhido
    backup = caminho.with_suffix(".antes_efeitos.json")
    if not backup.exists():
        backup.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    caminho.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DISTRIBUICAO DE EFEITOS:")
    for k, v in sorted(contagem.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")


if __name__ == "__main__":
    main()
