# -*- coding: utf-8 -*-
"""Folha de contato de TODOS os videos animados do acervo (auditoria visual)."""
import sqlite3, subprocess, sys, io
from pathlib import Path
from PIL import Image, ImageDraw
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
TEMP = ROOT / "_tmp_video_frames"
TEMP.mkdir(exist_ok=True)
DB = r"E:\videomaker\banco de imagens\acervo.db"

def main():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); c.row_factory = sqlite3.Row
    vids = [dict(r) for r in c.execute("select caminho,titulo,duracao_s,ambiente_principal,cluster_id from midia where tipo='video' and estilo_visual like '%Anim%' order by titulo")]
    print("TOTAL VIDEOS ANIMADOS:", len(vids))
    items = []
    for i, v in enumerate(vids):
        alvo = TEMP / f"all_{i:03d}.jpg"
        if not alvo.exists():
            subprocess.run([str(FFMPEG),"-y","-loglevel","error","-ss","2",
                            "-i",v["caminho"],"-frames:v","1",str(alvo)],check=False)
        if alvo.exists():
            items.append((i, v, Image.open(alvo).convert("RGB").resize((240,135))))
    cols, lw, lh, per = 4, 240, 158, 32
    for pag in range((len(items)+per-1)//per):
        chunk = items[pag*per:(pag+1)*per]
        rows = (len(chunk)+cols-1)//cols
        sheet = Image.new("RGB",(cols*lw,rows*lh),(18,18,22)); d=ImageDraw.Draw(sheet)
        for k,(i,v,im) in enumerate(chunk):
            x,y=(k%cols)*lw,(k//cols)*lh
            sheet.paste(im,(x,y))
            d.text((x+3,y+137),f"[{i}] {v['titulo'][:30]}",fill=(255,255,255))
        dest = ROOT/f"auditoria_todos_videos_p{pag+1}.jpg"
        sheet.save(dest,quality=85)
        print("PAGINA",pag+1,dest,"videos",len(chunk))
    (ROOT/"_indice_videos.json").write_text(__import__("json").dumps(
        [{"i":i,"titulo":v["titulo"],"caminho":v["caminho"],"cluster_id":v["cluster_id"]}
         for i,v,_ in items],ensure_ascii=False,indent=1),encoding="utf-8")

if __name__=="__main__":
    main()
