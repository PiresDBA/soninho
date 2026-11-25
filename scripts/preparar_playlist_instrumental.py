# -*- coding: utf-8 -*-
"""Monta playlist 100% instrumental: Audio Library + ninar original sintetizado."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
BANCO = ROOT / "banco_musicas"
PRON = BANCO / "prontas"
FORA = BANCO / "wikimedia_fora_da_playlist"
ORIGINAL = BANCO / "ninar_original"
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
PALAVRAS_VOZ = ["vocal", "voice", " sings ", " sung ", "choir", "feat.", " ft.", "cantada"]

def main() -> None:
    FORA.mkdir(parents=True, exist_ok=True)
    # 1) tira da playlist qualquer faixa com voz conhecida/duvidosa (Wikimedia)
    movidas = []
    for p in list(PRON.glob("*.wav")):
        if any(k in p.name.lower() for k in ["brahms", "axletree", "ninna", "lullaby", "monplaisir", "another-lullaby"]):
            shutil.move(str(p), str(FORA / p.name))
            movidas.append(p.name)
    print("FORA DA PLAYLIST (voz/duvidosas):", movidas)

    # 2) normaliza as musicas originais e inclui na playlist
    for p in sorted(ORIGINAL.glob("*.wav")):
        dest = PRON / (p.stem + ".m4a")
        if not dest.exists():
            subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(p),
                            "-af", "loudnorm=I=-20:TP=-3:LRA=7",
                            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", str(dest)], check=True)

    itens = []
    for p in sorted(PRON.glob("*")):
        if p.suffix.lower() not in (".m4a", ".wav", ".mp3"):
            continue
        nome = p.name.lower()
        if any(k in nome for k in PALAVRAS_VOZ):
            print("IGNORADA (voz no nome):", p.name); continue
        itens.append({"arquivo": str(p), "nome": p.stem,
                      "origem": "ninar_original" if "ninar_original" in p.name else
                                ("youtube_audio_library" if p.name.startswith("yt_") else "outra")})
    (BANCO / "playlist_instrumental.json").write_text(
        json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"PLAYLIST: {len(itens)} faixas 100% instrumentais")
    print("  Audio Library:", sum(i['origem']=='youtube_audio_library' for i in itens))
    print("  Ninar original:", sum(i['origem']=='ninar_original' for i in itens))

if __name__ == "__main__":
    main()
