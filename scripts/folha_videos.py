# -*- coding: utf-8 -*-
"""Folha de contato dos videos do manifesto para auditoria visual."""
import json, subprocess, sys, io
from pathlib import Path
from PIL import Image, ImageDraw
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / "_tmp_video_frames"
TEMP.mkdir(exist_ok=True)

def main():
    man = json.loads((ROOT / "manifestos" / "ep02_outdoor_v2_passeio-no-parque.json").read_text(encoding="utf-8"))
    vids = [c for c in man["cenas"] if c.get("tipo") == "video"]
    frames = []
    for i, c in enumerate(vids):
        alvo = TEMP / f"v{i:02d}.jpg"
        if not alvo.exists():
            subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-ss", "2",
                            "-i", c["caminho"], "-frames:v", "1", str(alvo)], check=False)
        if alvo.exists():
            im = Image.open(alvo).convert("RGB").resize((320, 180))
            frames.append((i, c["ordem"], c["titulo"], im))
    cols, lw, lh = 3, 320, 205
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols*lw, rows*lh), (20, 20, 25))
    d = ImageDraw.Draw(sheet)
    for k, (i, ordem, titulo, im) in enumerate(frames):
        x, y = (k % cols)*lw, (k//cols)*lh
        sheet.paste(im, (x, y))
        d.text((x+4, y+182), f"[{i}] cena {ordem}: {titulo[:38]}", fill=(255, 255, 255))
    dest = ROOT / "auditoria_videos_ep02.jpg"
    sheet.save(dest, quality=88)
    print("FOLHA:", dest, "|", len(frames), "videos")

if __name__ == "__main__":
    main()
