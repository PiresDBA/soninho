# -*- coding: utf-8 -*-
"""Auditoria rapida de um episodio Soninho (duration, escuridao, volume)."""
from __future__ import annotations

import json
import subprocess
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")


def duracao(video: Path) -> float:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def luma(video: Path) -> dict:
    # amostra 1 quadro a cada 60 s; signalstats devolve YAVG/YMAX
    tmp = video.parent / "_luma_tmp.txt"
    intervalo = 60 if duracao(video) >= 600 else 2
    filtro = f"fps=1/{intervalo},signalstats,metadata=print:file=_luma_tmp.txt"
    subprocess.run([str(FFMPEG), "-y", "-v", "error", "-i", str(video),
                    "-vf", filtro, "-f", "null", "-"],
                   capture_output=True, text=True, cwd=str(video.parent), check=True)
    texto = tmp.read_text(encoding="utf-8", errors="replace") if tmp.exists() else ""
    valores = []
    for linha in texto.splitlines():
        if "lavfi.signalstats.YAVG=" in linha:
            try:
                valores.append(float(linha.split("=", 1)[1].strip()))
            except ValueError:
                pass
    tmp.unlink(missing_ok=True)
    return {"amostras": len(valores), "media_y": round(sum(valores) / len(valores), 1) if valores else None,
            "max_y": round(max(valores), 1) if valores else None}


def volume(video: Path) -> dict:
    r = subprocess.run([str(FFMPEG), "-v", "info", "-i", str(video), "-af",
                        "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    out = {}
    for linha in r.stderr.splitlines():
        if "mean_volume:" in linha or "max_volume:" in linha:
            k, v = linha.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python verificar_sono.py <video.mp4>"); return
    video = Path(sys.argv[1])
    d = duracao(video)
    l = luma(video)
    v = volume(video)
    checks = {
        "duracao_maior_60min": d >= 3600,
        "luma_medio_escuro": (l["media_y"] or 999) < 90,
        "sem_brilho_estourado": (l["max_y"] or 999) < 210,
        "volume_preservado": "mean_volume: -inf" not in str(v),
    }
    relatorio = {"arquivo": str(video), "duracao_s": round(d, 1), "luma": l,
                 "volume": v, "checks": checks, "status": "OK" if all(checks.values()) else "REPROVADO"}
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    video.with_suffix(".auditoria.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
