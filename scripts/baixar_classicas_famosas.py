# -*- coding: utf-8 -*-
"""Baixa classicas famosas de dominio publico/CC0 (Wikimedia), sem vocal."""
from __future__ import annotations
import subprocess, sys, io, json, time
from pathlib import Path
import requests
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"banco_musicas"/"classicas_famosas"
DEST.mkdir(parents=True,exist_ok=True)
FFMPEG=Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
S=requests.Session(); S.headers.update({"User-Agent":"VideomakerSoninho/1.0 (classicas PD)"})
FAIXAS=[
 ("Clair_de_Lune_violinos.ogg","https://upload.wikimedia.org/wikipedia/commons/9/97/Clair_de_Lune_WikiOrchestra_backing_track_violins.ogg"),
 ("Clair_de_Lune_piano_1905.opus","https://upload.wikimedia.org/wikipedia/commons/6/67/Clair_de_Lune_by_Claude_Debussy_%281905%2C_piano_solo%29.opus"),
 ("Clair_de_Lune_Suite_bergamasque.ogg","https://upload.wikimedia.org/wikipedia/commons/b/be/Clair_de_lune_%28Claude_Debussy%29_Suite_bergamasque.ogg"),
 ("Clair_de_Lune_metais.ogg","https://upload.wikimedia.org/wikipedia/commons/6/63/Clair_de_Lune_-_Wright_Brass_-_United_States_Air_Force_Band_of_Flight.mp3"),
 ("Fur_Elise.ogg","https://upload.wikimedia.org/wikipedia/commons/7/7b/FurElise.ogg"),
 ("Minuet_Bach_Anna_Magdalena.wav","https://upload.wikimedia.org/wikipedia/commons/6/60/Menuet_bwv_anh_114_115_Anna_Magdalena.wav"),
 ("Minuet_G_BWV114.flac","https://upload.wikimedia.org/wikipedia/commons/3/39/Minuet_in_G_major%2C_BWV_Anh._114_%28played_by_PLATO_GSW%29.flac"),
 ("Sleeping_Beauty_Waltz.ogg","https://upload.wikimedia.org/wikipedia/commons/9/9e/PDP-CH_-_Marek_Weber%2C_piano_-_The_Sleeping_Beauty_Waltz_-_Tchaikovsky_-_Hmv-fkx110-2b4657.flac"),
 ("Serenade_Schubert.ogg","https://upload.wikimedia.org/wikipedia/commons/0/09/IMSLP654418-PMLP29767-Serenade-D889-Schubert.ogg"),
]
def main():
    ok=[]
    for nome,url in FAIXAS:
        alvo=DEST/nome
        if not alvo.exists():
            for tent in range(4):
                try:
                    r=S.get(url,timeout=120); r.raise_for_status(); alvo.write_bytes(r.content); break
                except Exception as e:
                    if tent==3: print("FALHOU",nome,type(e).__name__); alvo=None; break
                    time.sleep(5*(tent+1))
            if alvo is None: continue
        print("BAIXADA:",nome)
        ok.append(alvo)
    # converte o que o ffmpeg souber ler para wav normalizado
    finais=[]
    for p in ok:
        dest=DEST/(p.stem+".wav")
        if not dest.exists():
            r=subprocess.run([str(FFMPEG),"-y","-loglevel","error","-i",str(p),
                              "-af","lowpass=f=8000,loudnorm=I=-19:TP=-3:LRA=7",
                              "-ar","48000","-ac","2",str(dest)],capture_output=True)
            if r.returncode!=0:
                print("CONVERSAO FALHOU:",p.name); continue
        finais.append(dest)
    (ROOT/"banco_musicas"/"classicas_famosas.json").write_text(json.dumps(
        [{"arquivo":str(p),"nome":p.name,"fonte":"Wikimedia Commons - dominio publico/CC0"} for p in finais],
        ensure_ascii=False,indent=1),encoding="utf-8")
    print("PRONTAS:",len(finais),"em",DEST)

if __name__=="__main__": main()
