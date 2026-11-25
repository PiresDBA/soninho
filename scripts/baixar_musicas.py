# -*- coding: utf-8 -*-
"""
Baixa cancoes de ninar com licenca verificavel (Wikimedia Commons) e gera
versoes prontas para o canal Soninho: WAV 48 kHz, -20 LUFS, lowpass 8 kHz.

Uso: python scripts/baixar_musicas.py
Saida: banco_musicas/originais/, banco_musicas/prontas/, LICENCAS.md, musicas.json
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import io
import time
from pathlib import Path

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "banco_musicas" / "originais"
PRON = ROOT / "banco_musicas" / "prontas"
API = "https://commons.wikimedia.org/w/api.php"
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
if not FFMPEG.exists():
    FFMPEG = Path(r"E:\videomaker\videomaker\ffmpeg\bin\ffmpeg.exe")

# (titulo na Commons, "cantada" | "instrumental", uso)
FAIXAS = [
    ("File:Brahms - Schumann-Heink - Wiegenlied (Berceuse) (1915).ogg", "cantada", "Brahms — Wiegenlied (gravacao historica)"),
    ("File:Johannes Brahms ninna nanna op 49 n 4.ogg", "cantada", "Brahms — Ninna Nanna op.49 n.4"),
    ("File:Lullaby wound up clock.ogg", "instrumental", "Caixa de musica — Lullaby wound up clock"),
    ("File:Lullaby wound up clock guten abend gute nacht.ogg", "instrumental", "Caixa de musica — Guten Abend, gut Nacht"),
    ("File:Another Lullaby (Antti Luode).mp3", "instrumental", "Antti Luode — Another Lullaby"),
    ("File:Axletree - 02 - Ailsas Lullaby Vocal Version.ogg", "cantada", "Axletree — Ailsa's Lullaby (vocal)"),
    ("File:Monplaisir - 05 - Technical Difficulties Lullaby Pigeon Song.ogg", "instrumental", "Monplaisir — Lullaby Pigeon Song"),
]

session = requests.Session()
session.headers.update({"User-Agent": "VideomakerSoninho/1.0 (download de musicas licenciadas)"})


def limpar(texto: str) -> str:
    texto = html.unescape(re.sub(r"<[^>]+>", "", texto or ""))
    return re.sub(r"\s+", " ", texto).strip()


def info(titulo: str) -> dict:
    r = session.get(API, params={
        "action": "query", "format": "json", "titles": titulo,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
    }, timeout=30)
    r.raise_for_status()
    paginas = r.json().get("query", {}).get("pages", {})
    for p in paginas.values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        campo = lambda k: limpar(md.get(k, {}).get("value", ""))
        return {
            "titulo_commons": titulo,
            "url": ii.get("url", "").split("?")[0],
            "pagina": ii.get("descriptionurl", ""),
            "licenca": campo("LicenseShortName") or campo("License"),
            "autor": campo("Artist"),
            "credito_obrigatorio": campo("AttributionRequired"),
            "duracao_s": round(ii.get("duration", 0), 1),
        }
    raise RuntimeError("nao encontrado: " + titulo)


def slug(texto: str) -> str:
    s = texto.replace("File:", "").rsplit(".", 1)[0]
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:70]


def main() -> None:
    ORIG.mkdir(parents=True, exist_ok=True)
    PRON.mkdir(parents=True, exist_ok=True)
    registros = []
    for titulo, variante, nome_amigavel in FAIXAS:
        try:
            meta = info(titulo)
            if not meta["url"]:
                raise RuntimeError("sem URL de download")
            destino = ORIG / (slug(titulo) + Path(meta["url"]).suffix.lower())
            if not destino.exists():
                for tentativa in range(5):
                    try:
                        resp = session.get(meta["url"], timeout=120)
                        resp.raise_for_status()
                        destino.write_bytes(resp.content)
                        break
                    except requests.HTTPError as exc:
                        if exc.response is not None and exc.response.status_code == 429 and tentativa < 4:
                            espera = 6 * (tentativa + 1)
                            print(f"  429 — aguardando {espera}s para retry...")
                            time.sleep(espera)
                        else:
                            raise
            time.sleep(2)
            final = PRON / (slug(titulo) + ".wav")
            if not final.exists():
                cmd = [str(FFMPEG), "-y", "-loglevel", "error", "-i", str(destino),
                       "-af", "lowpass=f=8000,loudnorm=I=-20:TP=-2:LRA=7",
                       "-ar", "48000", "-ac", "2", str(final)]
                subprocess.run(cmd, check=True)
            meta.update({"arquivo_original": str(destino), "arquivo_pronto": str(final),
                         "variante": variante, "nome": nome_amigavel})
            registros.append(meta)
            print(f"OK  {variante:12s} {meta['licenca']:16s} {final.name}")
        except Exception as exc:
            print(f"FALHOU {titulo}: {exc}")

    (ROOT / "musicas.json").write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    linhas = ["# Licenças — banco de músicas do canal Soninho", "",
              "Todas as faixas foram obtidas da Wikimedia Commons. Confira sempre a página",
              "de origem antes de publicar. CC-BY exige crédito na descrição do vídeo.", ""]
    for m in registros:
        linhas += [f"## {m['nome']} ({m['variante']})", "",
                   f"- Licença: **{m['licenca']}**",
                   f"- Autor: {m['autor'] or 'não informado'}",
                   f"- Página: {m['pagina']}",
                   f"- Arquivo: `{m['arquivo_pronto']}`", ""]
    (ROOT / "LICENCAS.md").write_text("\n".join(linhas), encoding="utf-8")
    print(f"\n{len(registros)} faixas prontas em {PRON}")


if __name__ == "__main__":
    main()
