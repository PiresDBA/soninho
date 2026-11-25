# -*- coding: utf-8 -*-
"""
Renderizador do canal Soninho — video longo, escuro, SEM narracao.

Novelidades (pedido do usuario):
  - CROSSFADE REAL entre TODAS as cenas (xfade), sem corte e sem queda a preto;
  - overlay azul-marinho translucido + vinheta: a TV nao acende o quarto.

Arquitetura em 2 passos (para nao re-encoding 129 vezes):
  1) grupos de 6 cenas sao fundidas com xfade -> chunks/;
  2) os chunks sao fundidos com xfade -> video final.

Uso:
  python scripts/render_sono.py --manifesto manifestos/ep01_....json --demo
  python scripts/render_sono.py --manifesto manifestos/ep01_....json --workers 4
  # ajustes: --dim 0.30 --transicao-s 5 --cenas-por-chunk 6
"""
from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
PARTICULAS = Path(r"E:\videomaker\videomaker\BIBLIOTECA_EFEITOS\assets")
EFEITOS = ROOT / "efeitos"
W, H, FPS = 1280, 720, 15
COR = "0x050914"          # azul-marinho quase preto
BASE_EQ = "eq=brightness=-0.06:saturation=0.62:gamma=0.94,vignette=PI/7,lut=y='min(val,115)'"

EFEITO_PNG = {
    "chuva": "gota.png",
    "folhinhas_vento": "folha.png",
    "coracoes": "coracao_suave.png",
    "estrelinhas": "estrela.png",
    "soninho_zzz": "zzz.png",
    "cometa": "cometa.png",
    "solzinho": "solzinho.png",
    "passarinhos": "passaro.png",
    "bolinhas_sabao": "bolha.png",
}
TAM_EFEITO = {"cometa": (160, 62), "solzinho": (100, 100), "soninho_zzz": (54, 27),
              "nuvens_passando": (120, 55), "lua_crescente": (80, 80), "arco_iris": (130, 76),
              "onda_luminosa": (120, 48), "tracos_de_luz": (100, 25), "brisa_suave": (100, 34),
              "galho_caindo": (80, 35), "brilho_suave": (90, 90)}
OPACIDADE = {"cometa": 0.22, "solzinho": 0.13, "coracoes": 0.16,
             "estrela_cadente": 0.20, "fagulhas": 0.15, "po_de_estrelas": 0.14}
# 30 novos overframes + categorias de movimento
_mov = EFEITOS / "movimentos.json"
MOVIMENTO = ({m["nome"]: m["movimento"] for m in json.loads(_mov.read_text(encoding="utf-8"))}
             if _mov.exists() else {})
MOVIMENTO.update({
    "chuva": "cair", "gotas_espelho": "cair", "pingos_finos": "cair",
    "folhinhas_vento": "deriva", "coracoes": "subir", "estrelinhas": "piscar",
    "soninho_zzz": "subir", "cometa": "deriva", "solzinho": "piscar",
    "passarinhos": "deriva", "bolinhas_sabao": "subir",
})
for _m in MOVIMENTO:
    EFEITO_PNG.setdefault(_m, _m + ".png")


def png_do_efeito(efeito: str) -> Path:
    nome = EFEITO_PNG.get(efeito, "folha.png")
    novo = EFEITOS / nome
    return novo if novo.exists() else PARTICULAS / nome


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duracao_video(p: Path) -> float:
    r = subprocess.run([str(FFMPEG).replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error",
                        "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def render_chunk(cenas: list[dict], destino: Path, D: float, trans: float,
                 dim: float, particulas: bool, demo: bool) -> str:
    """Cada cena tem a SUA duracao. Video toca UMA vez (sem -stream_loop)."""
    n = len(cenas)
    durs = [8.0 if demo else float(c["duracao_s"]) for c in cenas]
    tr = min(0.8, min(durs) / 4) if demo else trans
    cmd = [str(FFMPEG), "-y", "-loglevel", "error"]
    for c, d in zip(cenas, durs):
        caminho = c["caminho"]
        if caminho.lower().endswith((".mp4", ".mov", ".webm")):
            # SEM loop: o clipe inteiro toca uma vez; tpad so protege se o
            # arquivo terminar um pouco antes da duracao declarada.
            cmd += ["-t", f"{d:.2f}", "-i", caminho]
        else:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.2f}", "-i", caminho]
    maior = max(durs)
    cmd += ["-f", "lavfi", "-t", f"{maior:.2f}", "-i", f"color=c={COR}:s={W}x{H}:r={FPS}"]
    if particulas:
        for c, d in zip(cenas, durs):
            png = png_do_efeito(c.get("efeito", ""))
            for _ in range(4):
                cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.2f}", "-i", str(png)]

    f: list[str] = [f"[{n}:v]split={n}" + "".join(f"[d{i}]" for i in range(n))]
    for i, (c, d) in enumerate(zip(cenas, durs)):
        f.append(f"[d{i}]format=rgba,colorchannelmixer=aa={dim}[dim{i}]")
        extra = ",tpad=stop_mode=clone:stop_duration=2" if c["caminho"].lower().endswith((".mp4",".mov",".webm")) else ""
        f.append(f"[{i}:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
                 f"crop={W}:{H},{BASE_EQ}{extra}[b{i}]")
        f.append(f"[b{i}][dim{i}]overlay=0:0:format=auto[bd{i}]")
        atual = f"bd{i}"
        if particulas:
            for k in range(4):
                pin = n + 1 + i * 4 + k
                x0 = 90 + k * 310
                efeito = c.get("efeito", "")
                cat = MOVIMENTO.get(efeito, "deriva")
                if efeito == "cometa":
                    ex = f"-260 + (t/{d:.2f})*({W}+520)"
                    ey = f"{80 + k*150} + (t/{d:.2f})*220"
                elif efeito == "solzinho":
                    ex, ey = f"{W-190 - k*20} + 8*sin(t/6)", f"{60 + k*18} + 5*cos(t/7)"
                elif cat == "cair":
                    ex, ey = f"{x0} + 6*sin(t/3)", f"-40 + (t/{d:.2f})*({H}+80)"
                elif cat == "subir":
                    ex, ey = f"{x0} + 10*sin(t/4)", f"{H} - (t/{d:.2f})*({H}+60)"
                elif cat == "giro":
                    ex = f"-40 + (t/{d:.2f})*({W}+80)"
                    ey = f"{60 + k*170} + 26*sin(t/5)"
                elif cat == "piscar":
                    ex, ey = f"{x0} + 5*sin(t/5)", f"{70 + k*140} + 5*cos(t/4)"
                else:
                    ex, ey = f"-40 + (t/{d:.2f})*({W}+80)", f"{70 + k*180} + 14*sin(t/5)"
                tw, th = TAM_EFEITO.get(efeito, (44, 44) if MOVIMENTO.get(efeito) else (30, 30))
                op = OPACIDADE.get(efeito, 0.22 if MOVIMENTO.get(efeito) else 0.16)
                f.append(f"[{pin}:v]scale={tw}:{th},format=rgba,colorchannelmixer=aa={op}[p{i}_{k}]")
                f.append(f"[{atual}][p{i}_{k}]overlay=x='{ex}':y='{ey}':eval=frame[pp{i}_{k}]")
                atual = f"pp{i}_{k}"
        f.append(f"[{atual}]null[v{i}]")

    atual = "v0"
    for i in range(1, n):
        offset = sum(durs[:i]) - i * tr
        saida = f"x{i}"
        f.append(f"[{atual}][v{i}]xfade=transition=fade:duration={tr:.2f}:"
                 f"offset={offset:.2f}[{saida}]")
        atual = saida
    total = sum(durs) - (n - 1) * tr
    cmd += ["-filter_complex", ";".join(f), "-map", f"[{atual}]",
            "-t", f"{total:.2f}", "-r", str(FPS), "-an",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destino)]
    try:
        run(cmd)
        return "ok"
    except subprocess.CalledProcessError as e:
        return (e.stderr or b"").decode("utf-8", "replace")[-500:]


def montar_audio(arquivos: list[Path], dur_total: float, destino: Path) -> None:
    if not arquivos:
        raise RuntimeError("nenhuma musica normalizada encontrada")
    lista = destino.parent / "audio_lista.txt"
    linhas = []
    while len(linhas) * 200 < dur_total + 300:
        for a in arquivos:
            linhas.append(f"file '{a.as_posix()}'")
        if len(linhas) > 3000:
            break
    lista.write_text("\n".join(linhas), encoding="utf-8")
    fim = max(0, dur_total - 12)
    run([str(FFMPEG), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(lista), "-t", f"{dur_total}", "-af",
         f"afade=t=in:st=0:d=5,afade=t=out:st={fim}:d=12,volume=0.55",
         "-c:a", "aac", "-b:a", "128k", "-ar", "48000", str(destino)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifesto", required=True)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dim", type=float, default=0.15, help="opacidade do overlay marinho (0-1)")
    ap.add_argument("--transicao-s", type=float, default=4.0)
    ap.add_argument("--cenas-por-chunk", type=int, default=6)
    ap.add_argument("--sem-particulas", action="store_true")
    ap.add_argument("--playlist", default="", help="JSON da playlist de musicas (padrao: playlist_instrumental.json)")
    args = ap.parse_args()

    man = json.loads(Path(args.manifesto).read_text(encoding="utf-8"))
    cenas = man["cenas"][:3] if args.demo else man["cenas"]
    D = 35.0 if not cenas else float(cenas[0]["duracao_s"])
    trans = args.transicao_s
    tam = args.cenas_por_chunk
    particulas = not args.sem_particulas

    ep = man.get("episodio", 0)
    proj = ROOT / "projetos" / f"ep{ep:02d}"
    chunks_dir = proj / ("chunks_demo" if args.demo else "chunks")
    chunks_dir.mkdir(parents=True, exist_ok=True)
    grupos = [cenas[i:i + tam] for i in range(0, len(cenas), tam)]
    print(f"CENAS: {len(cenas)} | CHUNKS: {len(grupos)} | DIM: {args.dim} | "
          f"TRANSICAO: {trans}s | PARTICULAS: {particulas}", flush=True)

    falhas = []
    def tarefa(i: int, grupo: list[dict]) -> tuple[int, Path, str]:
        dest = chunks_dir / f"chunk_{i:03d}.mp4"
        if dest.exists() and dest.stat().st_size > 10000:
            return (i, dest, "ok")
        res = render_chunk(grupo, dest, D, trans, args.dim, particulas, args.demo)
        return (i, dest, res)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        fut = {pool.submit(tarefa, i, g): i for i, g in enumerate(grupos)}
        for n, f in enumerate(as_completed(fut), 1):
            i, dest, res = f.result()
            if res != "ok":
                falhas.append((i, res))
            if n % 5 == 0 or n == len(fut):
                print(f"  chunks: {n}/{len(fut)} | falhas: {len(falhas)}", flush=True)
    if falhas:
        print("FALHAS:", falhas[:2]); return

    # passo 2: crossfade entre chunks
    caminhos = [chunks_dir / f"chunk_{i:03d}.mp4" for i in range(len(grupos))]
    durs = [duracao_video(p) for p in caminhos]
    cmd = [str(FFMPEG), "-y", "-loglevel", "error"]
    for p in caminhos:
        cmd += ["-i", str(p)]
    f = []
    atual = "0:v"
    offset = 0.0
    for i in range(1, len(caminhos)):
        offset += durs[i - 1] - trans
        saida = f"c{i}"
        f.append(f"[{atual}][{i}:v]xfade=transition=fade:duration={trans:.2f}:"
                 f"offset={offset:.2f}[{saida}]")
        atual = saida
    total = sum(durs) - (len(caminhos) - 1) * trans
    f.append(f"[{atual}]fade=t=in:st=0:d=4:color={COR},"
             f"fade=t=out:st={max(0,total-10):.2f}:d=10:color={COR}[v]")
    video = proj / "video_sem_audio.mp4"
    print(f"FUNDINDO CHUNKS... duracao final {total/60:.1f} min", flush=True)
    run([str(FFMPEG), "-y", "-loglevel", "error"] +
        sum([["-i", str(p)] for p in caminhos], []) +
        ["-filter_complex", ";".join(f), "-map", "[v]", "-an",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)])

    #usa SOMENTE a playlist atual (musicas novas do usuario), se existir
    playlist_json = Path(args.playlist) if args.playlist else \
        ROOT / "banco_musicas" / "playlist_instrumental.json"
    if playlist_json.exists():
        musicas = [Path(i["arquivo"]) for i in
                   json.loads(playlist_json.read_text(encoding="utf-8"))]
    else:
        musicas = sorted(glob.glob(str(ROOT / "banco_musicas" / "prontas" / "*.m4a")))
    trilha = proj / "trilha.m4a"
    print(f"MUSICAS: {len(musicas)}", flush=True)
    montar_audio([Path(m) for m in musicas], total, trilha)

    final = proj / (f"demo_{ep:02d}.mp4" if args.demo else f"ep{ep:02d}_soninho.mp4")
    print("MIXANDO FINAL...", flush=True)
    run([str(FFMPEG), "-y", "-loglevel", "error", "-i", str(video), "-i", str(trilha),
         "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-shortest",
         "-movflags", "+faststart", str(final)])
    print("FINAL:", final, f"{final.stat().st_size/1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
