# -*- coding: utf-8 -*-
"""
Ninar instrumental v2 — arranjo CHEIO e aquecido (nao e 'um piano de tecla solta').

Camadas simultaneas:
  - pad de acordes com ataque lento e tremolo suave;
  - arpeggio de caixa de musica em duas vozes (oitava);
  - melodia pentatonica em frases com harmonizacao em tercas;
  - grave suave pulsando no compasso;
  - reverberacao de 5 tap e estereo amplo.

Uso: python scripts/gerar_musica_ninar_v2.py --faixas 20 --duracao 180
"""
from __future__ import annotations
import argparse, math, sys, io
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SR, BPM = 48000, 50.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
PENTA = [0, 2, 4, 7, 9]
# (raiz grave, vozes do acorde em MIDI)
ACORDES = [
    (36, [60, 64, 67, 71]),   # Cmaj7
    (33, [57, 60, 64, 67]),   # Am7
    (29, [60, 65, 69, 72]),   # Fmaj9
    (31, [59, 62, 67, 71]),   # G6
]
PROG = [0, 0, 1, 1, 2, 2, 3, 0, 1, 2, 3, 2]


def hz(m: int) -> float:
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def caixa(freq: float, dur: float, amp: float) -> np.ndarray:
    t = np.arange(int(dur * SR), dtype=np.float64) / SR
    if len(t) < 8:
        return np.zeros(8)
    env = np.minimum(1.0, t / 0.008) * np.exp(-t * 1.7)
    return amp * env * (
        np.sin(2*np.pi*freq*t) + 0.33*np.sin(2*np.pi*freq*2.003*t)
        + 0.11*np.sin(2*np.pi*freq*3.01*t)
    )


def reverb(x: np.ndarray) -> np.ndarray:
    y = x.copy()
    for atraso, g in [(0.151, 0.30), (0.283, 0.21), (0.397, 0.15), (0.531, 0.09), (0.701, 0.05)]:
        n = int(atraso * SR)
        y[n:] += g * x[:-n]
    return y


def gerar(dur_s: float, semente: int) -> np.ndarray:
    rng = np.random.default_rng(semente)
    n = int(dur_s * SR)
    out = np.zeros(n, dtype=np.float64)

    # ---- PAD: acordes inteiros, com ataque/relaxamento lentos ----
    n_bars = math.ceil(dur_s / BAR)
    for bar in range(n_bars):
        ini = int(bar * BAR * SR)
        if ini >= n: break
        grau = PROG[bar % len(PROG)]
        voices = ACORDES[grau][1]
        t = np.arange(min(int(BAR * SR), n - ini), dtype=np.float64) / SR
        trem = 0.88 + 0.12 * np.sin(2 * np.pi * 0.22 * t)
        som = np.zeros_like(t)
        for j, m in enumerate(voices):
            f = hz(m)
            som += (0.55*np.sin(2*np.pi*f*t) + 0.18*np.sin(2*np.pi*f*1.004*t + j)
                    + 0.08*np.sin(2*np.pi*f*0.5*t))
        env = np.minimum(1.0, t/1.1) * np.minimum(1.0, (BAR-t)/1.5)
        out[ini:ini+len(t)] += 0.030 * som * trem * np.clip(env, 0, 1)

    # ---- GRAVE: pulso suave por tempo ----
    for k in range(int(dur_s / BEAT)):
        grau = PROG[(k // 4) % len(PROG)]
        ini = int(k * BEAT * SR)
        if ini >= n: break
        t = np.arange(min(int(BEAT * SR), n-ini), dtype=np.float64)/SR
        f = hz(ACORDES[grau][0])
        env = np.exp(-t*1.1) * np.minimum(1.0, t/0.05)
        out[ini:ini+len(t)] += 0.10*env*(np.sin(2*np.pi*f*t) + 0.25*np.sin(2*np.pi*f*2*t))

    # ---- ARPEGGIO: duas vozes por colcheia ----
    passo = BEAT / 2
    for i in range(int(dur_s / passo)):
        grau = PROG[(i // 8) % len(PROG)]
        voices = ACORDES[grau][1]
        ini = int(i * passo * SR)
        if ini >= n: break
        m = voices[i % len(voices)] + (12 if i % 8 in (2, 6) else 0)
        amp = 0.15 * (1.0 if i % 4 == 0 else 0.72) * (0.85 + 0.25*rng.random())
        nota = caixa(hz(m), min(2.2, passo*2.6), amp)
        fim = min(n, ini+len(nota))
        out[ini:fim] += nota[:fim-ini]
        # segunda voz (oitava acima, mais fraca) — dá corpo sem ficar "tecla solitaria"
        m2 = voices[(i+2) % len(voices)] + 24
        nota2 = caixa(hz(m2), min(1.6, passo*2.0), amp*0.45)
        fim2 = min(n, ini+len(nota2))
        out[ini:fim2] += nota2[:fim2-ini]

    # ---- MELODIA: frases de 2 tempos com terça paralela ----
    for frase in range(int(dur_s / (2*BEAT))):
        ini = int(frase * 2 * BEAT * SR)
        if ini >= n: break
        grau = PROG[frase % len(PROG)]
        base = ACORDES[grau][1][1]
        salto = int(rng.choice(PENTA, p=[.30,.18,.22,.18,.12]))
        m = base + salto + (12 if rng.random() < .18 else 0)
        amp = 0.11 * (0.8 + 0.4*rng.random())
        nota = caixa(hz(m), 1.8, amp)
        fim = min(n, ini+len(nota))
        out[ini:fim] += nota[:fim-ini]
        terça = caixa(hz(m+4), 1.6, amp*0.5)
        ini2 = ini + int(0.06*SR)
        fim2 = min(n, ini2+len(terça))
        if ini2 < n: out[ini2:fim2] += terça[:fim2-ini2]

    out = reverb(out)
    sos = butter(2, 7000, btype="lowpass", fs=SR, output="sos")
    out = sosfiltfilt(sos, out)
    sos_hp = butter(2, 55, btype="highpass", fs=SR, output="sos")
    out = sosfiltfilt(sos_hp, out)
    fi, fo = int(4*SR), int(8*SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    pico = float(np.max(np.abs(out)))
    if pico > 0: out *= 0.78 / pico
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--faixas", type=int, default=20)
    ap.add_argument("--duracao", type=int, default=180)
    ap.add_argument("--seed", type=int, default=20261126)
    ap.add_argument("--saida", default="ninar_v2")
    a = ap.parse_args()
    destino = ROOT / "banco_musicas" / a.saida
    destino.mkdir(parents=True, exist_ok=True)
    for i in range(a.faixas):
        p = destino / f"ninar_v2_{i+1:02d}.wav"
        if p.exists():
            print("ja existe:", p.name); continue
        x = gerar(a.duracao, a.seed + i * 1301)
        est = np.stack([x, np.roll(x, int(0.013*SR))], axis=1)
        wavfile.write(str(p), SR, est.astype(np.float32))
        print("GERADA:", p.name)
    print("TOTAL:", a.faixas*a.duracao/60, "min em", destino)

if __name__ == "__main__":
    main()
