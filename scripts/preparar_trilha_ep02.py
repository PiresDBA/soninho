# -*- coding: utf-8 -*-
"""Trilha do episodio 2 (outdoor): musicas DIFERENTES do episodio 1.

Fontes: 12 ninar originais novas + 16 faixas sleep da Audio Library arquivada.
Crossfade de 3 s, ordem embaralhada deterministica.
"""
from __future__ import annotations
import json, re, subprocess, sys, io, wave
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
ARQ = ROOT / "banco_musicas" / "arquivo_musicas_antigas"
NOVAS = ROOT / "banco_musicas" / "ninar_ep02"
PRON = ROOT / "banco_musicas" / "ep02_prontas"
PROJ = ROOT / "projetos" / "ep02"
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")
SR, CROSS, GANHO = 48000, 3.0, 0.55
PALAVRAS = ["somnia", "sleep", "lullab", "moonlight", "snowfall", "starlight",
            "rest-your-head", "moonbeam", "highway-to-the-moon"]

def duracao(p: Path) -> float:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

def fontes() -> list[Path]:
    # somente as 20 ninar v2 (arranjo cheio); nada dos audios reprovados
    return sorted((ROOT / "banco_musicas" / "ninar_v2").glob("*.wav"))

def normalizar(p: Path) -> Path:
    dest = PRON / (re.sub(r"[^a-zA-Z0-9]+", "_", p.stem).strip("_")[:80] + ".wav")
    if not dest.exists():
        subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(p),
                        "-af", "lowpass=f=8000,loudnorm=I=-19:TP=-3:LRA=7",
                        "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", str(dest)], check=True)
    return dest

def ler(p: Path) -> np.ndarray:
    with wave.open(str(p), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return x.reshape(-1, 2)

def main():
    PROJ.mkdir(parents=True, exist_ok=True)
    PRON.mkdir(parents=True, exist_ok=True)
    fontes_lista = fontes()
    print(f"FAIXAS FONTE: {len(fontes_lista)}")
    prontas = [normalizar(p) for p in fontes_lista]
    alvo = 4003.0
    print(f"DURACAO DAS FAIXAS: {sum(duracao(p) for p in prontas)/60:.1f} min")
    ordem = np.random.default_rng(251124).permutation(len(prontas)).tolist()
    bruto = PROJ / "_trilha_crossfade.wav"
    n_cross = int(CROSS * SR)
    with wave.open(str(bruto), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
        anterior = None; escrito = 0.0; voltas = 0
        while escrito < alvo + 2.0 and voltas < 5:
            for i in ordem:
                y = ler(prontas[i])
                if anterior is not None:
                    n = min(n_cross, len(y), len(anterior))
                    rampa = np.linspace(0, 1, n, dtype=np.float32)[:, None]
                    out.writeframes((np.clip(anterior[:n]*(1-rampa)+y[:n]*rampa,-1,1)*32767).astype(np.int16).tobytes())
                    restante = y[n:]
                else:
                    n = 0; restante = y
                out.writeframes((np.clip(restante,-1,1)*32767).astype(np.int16).tobytes())
                escrito += (len(restante)+n)/SR
                anterior = y[-n_cross:]
                if escrito >= alvo + 2.0: break
            voltas += 1
    print(f"MIXADO: {escrito/60:.1f} min")
    destino = PROJ / "trilha_final.m4a"
    subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(bruto),
                    "-t", f"{alvo:.2f}",
                    "-af", f"afade=t=in:st=0:d=5,afade=t=out:st={alvo-12:.2f}:d=12,volume={GANHO}",
                    "-c:a", "aac", "-b:a", "128k", "-ar", str(SR), str(destino)], check=True)
    (ROOT / "banco_musicas" / "playlist_ep02.json").write_text(
        json.dumps([{"arquivo": str(p), "nome": p.name} for p in prontas],
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("TRILHA:", destino, f"{destino.stat().st_size/1e6:.1f} MB")

if __name__ == "__main__":
    main()
