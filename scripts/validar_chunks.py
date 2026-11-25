# -*- coding: utf-8 -*-
"""Remove chunks invalidos/incompletos para que o render possa retomar com 1 worker."""
from __future__ import annotations
import subprocess, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
FFPROBE = Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")

def main():
    if len(sys.argv) < 2:
        print("Uso: python validar_chunks.py <pasta_chunks> [min_duracao]"); return
    d = Path(sys.argv[1]); minimo = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    ruins = []
    for p in sorted(d.glob("chunk_*.mp4")):
        try:
            r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
            dur = float(r.stdout.strip())
        except Exception:
            dur = 0.0
        if dur < minimo:
            ruins.append((p.name, dur, p.stat().st_size))
    for nome, dur, tam in ruins:
        (d / nome).unlink(missing_ok=True)
        print(f"REMOVIDO {nome} (dur={dur}, bytes={tam})")
    print(f"CHUNKS VALIDOS: {len(list(d.glob('chunk_*.mp4')))} | REMOVIDOS: {len(ruins)}")

if __name__ == "__main__":
    main()
