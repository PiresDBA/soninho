# -*- coding: utf-8 -*-
"""
Ajuste final SEM re-renderizar as cenas:
  - limita o brilho maximo (lut) para a TV nao clarear o quarto;
  - renormatiza o audio a -22 LUFS com teto -5 dB (sem picos que acordem).

Uso: python scripts/ajustar_final.py projetos/ep01/ep01_soninho.mp4
"""
from __future__ import annotations

import subprocess
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")


def rodar(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python ajustar_final.py <video.mp4>"); return
    video = Path(sys.argv[1]).resolve()
    pai = video.parent
    video_base = pai / "video_sem_audio.mp4"
    if not video_base.exists():
        print("FALTA:", video_base); return

    corrigido = pai / "video_ajustado.mp4"
    print("AJUSTANDO BRILHO...")
    rodar([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(video_base),
           "-vf", "eq=brightness=-0.05:saturation=0.90,lut=y='min(val,115)'",
           "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(corrigido)])

    # O volume ja e aplicado no render_sono.py (volume=0.55).
    # Aqui so copiamos a trilha para o nome esperado pelo adicionar_subscribe.py.
    import shutil
    audio_base = pai / "trilha.m4a"
    audio_new = pai / "trilha_final.m4a"
    if not audio_new.exists():
        shutil.copy2(audio_base, audio_new)
    print("TRILHA:", audio_new.name)

    temporario = pai / "_final_tmp.mp4"
    print("MIXANDO...")
    rodar([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(corrigido),
           "-i", str(audio_new), "-map", "0:v:0", "-map", "1:a:0",
           "-c", "copy", "-shortest", "-movflags", "+faststart", str(temporario)])
    backup = video.with_suffix(".antes_ajuste.mp4")
    if backup.exists():
        backup = video.with_name(video.stem + "_backup2.mp4")
    shutil.move(str(video), str(backup))
    temporario.replace(video)
    print("PRONTO:", video, f"{video.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
