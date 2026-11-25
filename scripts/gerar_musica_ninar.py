# -*- coding: utf-8 -*-
"""
Gerador de cancoes de ninar 100% instrumentais (caixa de musica + piano suave).

Musica ORIGINAL, sintetizada localmente com numpy/scipy: sem voz, sem sample de
terceiros, sem direito autoral. Timbre de caixa de musica/celesta, andamento
lento (~52 BPM), progressao C-Am-F-G, reverberacao suave e grave discreto.

Uso:
  python scripts/gerar_musica_ninar.py --faixas 12 --duracao 180
"""
from __future__ import annotations

import argparse
import math
import sys
import io
from pathlib import Path

import numpy as np
from scipy.io import wavfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
BPM = 52.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
PENTA = [0, 2, 4, 7, 9]          # C D E G A
CHORDES = [                      # (raiz MIDI, notas do acorde)
    (48, [60, 64, 67, 71]),      # Cmaj7
    (45, [57, 60, 64, 67]),      # Am7
    (41, [60, 65, 69, 72]),      # Fmaj9 (vozising suave)
    (43, [59, 62, 67, 71]),      # G6
]
PROG = [0, 1, 2, 3, 0, 1, 3, 2]   # 8 compassos


def midi_hz(n: int) -> float:
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


def nota(freq: float, dur: float, rng: np.random.Generator, amplitude: float = 1.0) -> np.ndarray:
    t = np.arange(int(dur * SR), dtype=np.float64) / SR
    if len(t) < 10:
        return np.zeros(10)
    ataque = np.minimum(1.0, t / 0.006)
    envelope = ataque * np.exp(-t * 2.6)
    # timbre de caixa de musica: fundamentais + harmonicos com desalinhamento
    som = (
        1.00 * np.sin(2 * np.pi * freq * t)
        + 0.30 * np.sin(2 * np.pi * freq * 2.003 * t + 0.3)
        + 0.12 * np.sin(2 * np.pi * freq * 3.011 * t + 0.7)
        + 0.05 * np.sin(2 * np.pi * freq * 4.97 * t + 1.1)
    )
    return (amplitude * envelope * som).astype(np.float64)


def reverb(x: np.ndarray) -> np.ndarray:
    y = x.copy()
    for atraso, ganho in [(0.137, 0.32), (0.271, 0.20), (0.419, 0.11)]:
        a = int(atraso * SR)
        y[a:] += ganho * x[:-a]
    return y


def gerar(dur_s: float, semente: int) -> np.ndarray:
    rng = np.random.default_rng(semente)
    n = int(dur_s * SR)
    out = np.zeros(n, dtype=np.float64)
    # grave continuo, muito suave, um acorde por compasso
    for bar in range(math.ceil(dur_s / BAR)):
        inicio = int(bar * BAR * SR)
        if inicio >= n:
            break
        root = CHORDES[PROG[bar % len(PROG)]][0] - 12
        t = np.arange(min(int(BAR * SR), n - inicio), dtype=np.float64) / SR
        pad = (
            0.55 * np.sin(2 * np.pi * midi_hz(root) * t)
            + 0.18 * np.sin(2 * np.pi * midi_hz(root + 12) * t)
        )
        env = np.minimum(1.0, t / 0.8) * np.minimum(1.0, (BAR - t) / 1.2)
        out[inicio:inicio + len(t)] += 0.055 * pad * np.clip(env, 0, 1)

    # melodias em caixa de musica: duas vozes alternadas
    passo = BEAT / 2  # colcheias
    total = int(dur_s / passo)
    for i in range(total):
        bar = i // 8
        grau = PROG[bar % len(PROG)]
        root, acorde = CHORDES[grau]
        inicio = int(i * passo * SR)
        if inicio >= n:
            break
        # a cada 8 colcheias escolhe uma nota do acorde como "campo"
        if i % 8 in (0, 4):
            midi = int(acorde[rng.integers(0, len(acorde))]) + (12 if rng.random() < 0.22 else 0)
        else:
            salto = int(rng.choice(PENTA, p=[0.30, 0.18, 0.22, 0.18, 0.12]))
            midi = 72 + salto + (12 if rng.random() < 0.12 else 0)
        vol = 0.16 * (1.0 if i % 4 == 0 else 0.65) * (0.85 + 0.3 * rng.random())
        nota_curta = nota(midi_hz(midi), min(1.9, passo * 2.4), rng, vol)
        fim = min(n, inicio + len(nota_curta))
        out[inicio:fim] += nota_curta[:fim - inicio]
        # contramelodia suave a cada dois tempos
        if i % 8 == 2:
            inicio2 = int((i + 3) * passo * SR)
            m2 = acorde[rng.integers(0, len(acorde))] + 12
            n2 = nota(midi_hz(m2), 1.2, rng, 0.075)
            fim2 = min(n, inicio2 + len(n2))
            if inicio2 < n:
                out[inicio2:fim2] += n2[:fim2 - inicio2]

    out = reverb(out)
    # equalizacao simples: corte de agudos e grave (evita som "eletrico")
    from scipy.signal import butter, sosfiltfilt
    sos = butter(2, 6000, btype="lowpass", fs=SR, output="sos")
    out = sosfiltfilt(sos, out)
    sos_hp = butter(2, 65, btype="highpass", fs=SR, output="sos")
    out = sosfiltfilt(sos_hp, out)
    # fades de entrada/saida
    fi = int(4 * SR)
    fo = int(8 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    pico = float(np.max(np.abs(out)))
    if pico > 0:
        out *= 0.82 / pico
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--faixas", type=int, default=12)
    ap.add_argument("--duracao", type=int, default=180)
    ap.add_argument("--seed", type=int, default=20261124)
    ap.add_argument("--saida", default="ninar_original", help="pasta dentro de banco_musicas")
    a = ap.parse_args()
    destino = ROOT / "banco_musicas" / a.saida
    destino.mkdir(parents=True, exist_ok=True)
    for i in range(a.faixas):
        nome = destino / f"ninar_original_{i+1:02d}.wav"
        if nome.exists():
            print("ja existe:", nome.name); continue
        x = gerar(a.duracao, a.seed + i * 977)
        estereo = np.stack([x, np.roll(x, int(0.011 * SR))], axis=1)
        wavfile.write(str(nome), SR, estereo.astype(np.float32))
        print(f"GERADA {nome.name} ({a.duracao}s)")
    print("TOTAL:", a.faixas * a.duracao / 60, "min em", destino)


if __name__ == "__main__":
    main()
