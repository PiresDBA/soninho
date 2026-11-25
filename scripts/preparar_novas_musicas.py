# -*- coding: utf-8 -*-
"""
Prepara a trilha do episodio usando SOMENTE as musicas novas da pasta
banco_musicas/ninar_original (com crossfade de 3 s entre faixas).

- exclui vocais e duplicatas exatas;
- quando existe "(Instrumental)", descarta a versao sem o rotulo;
- normaliza cada faixa (48 kHz, lowpass 8 kHz, -19 LUFS);
- mistura em ordem embaralhada deterministica, com crossfade, ate cobrir a duracao;
- saida: projetos/ep01/trilha_final.m4a (pronta para o adicionar_subscribe.py).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import wave
import io
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
FONTE = ROOT / "banco_musicas" / "ninar_original"
PRON = ROOT / "banco_musicas" / "novas_prontas"
PROJ = ROOT / "projetos" / "ep01"
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")
SR, CROSS, GANHO = 48000, 3.0, 0.55


def duracao(p: Path) -> float:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def selecionar() -> list[Path]:
    arquivos = sorted(FONTE.glob("*.mp3"))
    hashes: dict[str, Path] = {}
    for p in arquivos:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h in hashes:
            continue
        hashes[h] = p
    unicos = list(hashes.values())
    # exclui vocal
    unicos = [p for p in unicos if "vocal" not in p.name.lower()]
    # se existe versao instrumental, tira a versao sem rotulo
    instrumentais = [p for p in unicos if "instrumental" in p.name.lower()]
    bases = set()
    for p in instrumentais:
        base = re.sub(r"\s*\(instrumental\)", "", p.name, flags=re.I).lower()
        bases.add(base)
    selecionados = [p for p in unicos if "instrumental" in p.name.lower() or
                    p.name.lower() not in bases]
    return sorted(selecionados, key=lambda p: p.name.lower())


def normalizar(p: Path) -> Path:
    dest = PRON / (re.sub(r"[^a-zA-Z0-9]+", "_", p.stem).strip("_")[:80] + ".wav")
    if not dest.exists():
        subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(p),
                        "-af", "lowpass=f=8000,loudnorm=I=-19:TP=-3:LRA=7",
                        "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", str(dest)], check=True)
    return dest


def ler_wav(p: Path) -> np.ndarray:
    with wave.open(str(p), "rb") as w:
        dados = w.readframes(w.getnframes())
    x = np.frombuffer(dados, dtype=np.int16).astype(np.float32) / 32768.0
    return x.reshape(-1, 2)


def main() -> None:
    PRON.mkdir(parents=True, exist_ok=True)
    faixas = selecionar()
    print(f"FAIXAS SELECIONADAS: {len(faixas)}")
    normalizadas = [normalizar(p) for p in faixas]
    total_faixas = sum(duracao(p) for p in normalizadas)
    alvo = duracao(PROJ / "ep01_soninho.mp4")
    print(f"DURACAO DAS FAIXAS: {total_faixas/60:.1f} min | ALVO: {alvo/60:.1f} min")

    # ordem embaralhada deterministica (sem repetir a mesma faixa seguida)
    rng = np.random.default_rng(241124)
    ordem = rng.permutation(len(normalizadas)).tolist()
    bruto = PROJ / "_trilha_crossfade.wav"
    n_cross = int(CROSS * SR)
    with wave.open(str(bruto), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
        anterior: np.ndarray | None = None
        escrito = 0
        repeticoes = 0
        while escrito < alvo + 2.0:   # +2 s de margem (nao usar SR aqui: isso e 48000 s!)
            for i in ordem:
                y = ler_wav(normalizadas[i])
                if anterior is not None:
                    n = min(n_cross, len(y), len(anterior))
                    rampa = np.linspace(0, 1, n, dtype=np.float32)[:, None]
                    mistura = anterior[:n] * (1 - rampa) + y[:n] * rampa
                    out.writeframes((np.clip(mistura, -1, 1) * 32767).astype(np.int16).tobytes())
                    restante = y[n:]
                else:
                    restante = y
                out.writeframes((np.clip(restante, -1, 1) * 32767).astype(np.int16).tobytes())
                escrito += (len(restante) + (n if anterior is not None else 0)) / SR
                anterior = y[-n_cross:]
                if escrito >= alvo + 2.0:
                    break
            repeticoes += 1
            if repeticoes > 5:
                break
    print(f"MIXADO: {escrito/60:.1f} min")

    destino = PROJ / "trilha_final.m4a"
    fim = max(0, alvo - 12)
    subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(bruto),
                    "-t", f"{alvo:.2f}",
                    "-af", f"afade=t=in:st=0:d=5,afade=t=out:st={fim:.2f}:d=12,volume={GANHO}",
                    "-c:a", "aac", "-b:a", "128k", "-ar", str(SR), str(destino)], check=True)
    (ROOT / "banco_musicas" / "playlist_instrumental.json").write_text(
        json.dumps([{"arquivo": str(p), "nome": p.name, "origem": "usuario_ninar_original"}
                    for p in normalizadas], ensure_ascii=False, indent=1), encoding="utf-8")
    print("TRILHA:", destino, f"{destino.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
