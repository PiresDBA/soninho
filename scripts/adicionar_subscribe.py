# -*- coding: utf-8 -*-
"""
Overlays de CTA do canal Soninho (spec do usuario 24/11/2026).

MEIO / DURANTE: like-subscribe-sonoplastia.mp4 (a cada 10 min + 50% do video)
FINAL:          joinha-like-subscribe.mp4      (ultimos 10 s)

Regras:
  - chroma key #00FF00, similaridade 0.28, blend 0.12 + despill;
  - 31% da largura (400 px em 1280), lower-third, margem 5%, sem cobrir rostos;
  - fade in/out de 0,2 s no alpha;
  - audio dos CTA mantido a -14 dB (volume 0.20) sobre a trilha principal.

Implementado em DUAS PASSAGENS: na passagem de video so entram os clipes em loop
(um input de audio extra faz o ffmpeg parar o loop e matar o overlay); o audio e
mixado na passagem 2.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")
PASTA_CTA = Path(r"E:\videomaker\banco de imagens\categorias\Outros")
MEIO = PASTA_CTA / "like-subscribe-sonoplastia.mp4"
FIM = PASTA_CTA / "joinha-like-subscribe.mp4"
CHROMA = "colorkey=0x00FF00:0.28:0.12,despill=green:0.5"
LARGURA, MARGEM, FADE, GANHO = 400, 40, 0.2, 0.20


def rodar(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duracao(p: Path) -> float:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def audio_do_clipe(clipe: Path) -> Path:
    dest = ROOT / "efeitos" / (clipe.stem + "_audio.wav")
    if not dest.exists():
        rodar([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(clipe),
               "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(dest)])
    return dest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--intervalo", type=int, default=600)
    ap.add_argument("--sem-meio", action="store_true")
    ap.add_argument("--sem-fim", action="store_true")
    a = ap.parse_args()
    for p in (MEIO, FIM):
        if not p.exists():
            print("CLIPE NAO ENCONTRADO:", p); return
    video = Path(a.video).resolve()
    pai = video.parent
    base_v, trilha = pai / "video_ajustado.mp4", pai / "trilha_final.m4a"
    if not base_v.exists() or not trilha.exists():
        print("FALTA video_ajustado.mp4 / trilha_final.m4a em", pai); return

    total = duracao(video)
    d_meio, d_fim = min(10.0, duracao(MEIO)), min(10.0, duracao(FIM))
    eventos: list[tuple[Path, float, float]] = []
    if not a.sem_meio:
        tempos = list(range(a.intervalo, int(total) - 12, a.intervalo))
        metade = total / 2
        if not any(abs(metade - t) < 90 for t in tempos):
            tempos.append(metade)
        tempos.sort()
        eventos += [(MEIO, float(t), d_meio) for t in tempos]
    if not a.sem_fim:
        eventos.append((FIM, max(0.0, total - 10.0), d_fim))
    print(f"VIDEO {total/60:.1f} min | {len(eventos)} eventos: {[round(t,1) for _,t,_ in eventos]}")

    # ---------- PASSAGEM 1: somente video (NINGUEM mais entra com audio) ----------
    cmd = [str(FFMPEG), "-y", "-loglevel", "error", "-i", str(base_v)]
    filtros: list[str] = []
    atual = "0:v"
    for i, (clipe, t, dur) in enumerate(eventos):
        # SEM -stream_loop: o clipe toca uma vez e e deslocado no tempo com setpts
        cmd += ["-i", str(clipe)]
        fim = min(total, t + dur)
        filtros.append(
            f"[{i+1}:v]{CHROMA},scale={LARGURA}:-1,"
            f"fade=t=in:st=0:d={FADE}:alpha=1,"
            f"fade=t=out:st={max(0.1,dur-FADE):.2f}:d={FADE}:alpha=1,"
            f"setpts=PTS+{t:.2f}/TB[cta{i}];"
            f"[{atual}][cta{i}]overlay=x='(W-w)/2':y='H-h-{MARGEM}':"
            f"enable='between(t,{t:.2f},{fim:.2f})'[v{i}]"
        )
        atual = f"v{i}"
    filtros.append(f"[{atual}]null[v]")
    video_tmp = pai / "_video_com_ctas.mp4"
    cmd += ["-filter_complex", ";".join(filtros), "-t", f"{total:.2f}",
            "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "25", "-pix_fmt", "yuv420p", str(video_tmp)]
    rodar(cmd)

    # ---------- PASSAGEM 2: audio da trilha + CTA a -14 dB ----------
    cmd2 = [str(FFMPEG), "-y", "-loglevel", "error", "-i", str(video_tmp), "-i", str(trilha)]
    audio_f = ["[1:a]anull[cta_a0]"]
    entradas = ["[cta_a0]"]
    for i, (clipe, t, _) in enumerate(eventos):
        wav = audio_do_clipe(clipe)
        cmd2 += ["-i", str(wav)]
        idx = 2 + i
        audio_f.append(f"[{idx}:a]adelay={int(t*1000)}|{int(t*1000)},volume={GANHO}[cta_s{i}]")
        entradas.append(f"[cta_s{i}]")
    mistura = ";".join(audio_f) + (";" + "".join(entradas) +
              f"amix=inputs={len(entradas)}:duration=first:dropout_transition=0:"
              f"normalize=0[a]")
    cmd2 += ["-filter_complex", mistura, "-t", f"{total:.2f}",
             "-map", "0:v:0", "-map", "[a]", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
             str(pai / "_com_subscribe.mp4")]
    rodar(cmd2)
    backup = video.with_suffix(".antes_subscribe.mp4")
    if not backup.exists():
        shutil.copy2(video, backup)
    (pai / "_com_subscribe.mp4").replace(video)
    print("PRONTO:", video, f"{video.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
