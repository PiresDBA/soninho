# -*- coding: utf-8 -*-
"""Trilha ep03 SEM musicas espaciais: 25 do usuario + 10 classicas."""
from __future__ import annotations
import json, subprocess, sys, io, wave
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(__file__).resolve().parents[1]
BANCO=ROOT/"banco_musicas"
PROJ=ROOT/"projetos"/"ep03"
PRON=BANCO/"ep03_prontas"
FFMPEG=Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
FFPROBE=Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")
SR,CROSS,GANHO,ALVO=48000,3.0,0.55,3970.0
ESPAÇO=["pulsar","event horizon","laniakea","rain over kyoto","akatsuki","somnia",
        "starlight","moonlight","galaxia","nebula","cosmos","orbita"]

def dur(p):
    r=subprocess.run([str(FFPROBE),"-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

def norm(p):
    import re
    d=PRON/(re.sub(r"[^a-zA-Z0-9]+","_",p.stem).strip("_")[:80]+".wav")
    if not d.exists():
        subprocess.run([str(FFMPEG),"-y","-loglevel","error","-i",str(p),
                        "-af","lowpass=f=8000,loudnorm=I=-19:TP=-3:LRA=7",
                        "-ar",str(SR),"-ac","2","-c:a","pcm_s16le",str(d)],check=True)
    return d

def ler(p):
    with wave.open(str(p),"rb") as w:
        x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
    return x.reshape(-1,2)

def main():
    PROJ.mkdir(parents=True,exist_ok=True); PRON.mkdir(parents=True,exist_ok=True)
    pl=json.loads((BANCO/"playlist_ep02_v3.json").read_text(encoding="utf-8"))
    fontes=[]
    for i in pl:
        p=Path(i["arquivo"])
        if any(k in p.name.lower() for k in ESPAÇO): continue
        fontes.append(p)
    # classicos conhecidos (Bach, Vivaldi, Mozart, Offenbach, Schubert, Debussy)
    classicos=[Path(i["arquivo"]) for i in json.loads(
        (BANCO/"compositores.json").read_text(encoding="utf-8")) if Path(i["arquivo"]).exists()]
    print("CLASSICOS ADICIONADOS:",len(classicos))
    todos=fontes+classicos
    print("FAIXAS SEM ESPACIAIS:",len(todos))
    prontas=[norm(p) for p in todos]
    print("DURACAO FAIXAS:",round(sum(dur(p) for p in prontas)/60,1),"min")
    # ordem: 3 faixas normais + 1 classico conhecido, repetindo
    n_cl=len(classicos)
    famosos=list(range(len(prontas)-n_cl,len(prontas)))
    outros=list(range(len(prontas)-n_cl))
    np.random.default_rng(311124).shuffle(outros)
    np.random.default_rng(311125).shuffle(famosos)
    ordem=[]
    k=0
    while outros or famosos:
        for _ in range(3):
            if outros: ordem.append(outros.pop(0))
        if famosos: ordem.append(famosos.pop(0))
        k+=1
        if k>500: break
    bruto=PROJ/"_trilha_crossfade.wav"; n=int(CROSS*SR)
    with wave.open(str(bruto),"wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
        ant=None; escrito=0.0; voltas=0
        while escrito<ALVO+2 and voltas<5:
            for i in ordem:
                y=ler(prontas[i])
                if ant is not None:
                    k=min(n,len(y),len(ant)); rp=np.linspace(0,1,k,dtype=np.float32)[:,None]
                    out.writeframes((np.clip(ant[:k]*(1-rp)+y[:k]*rp,-1,1)*32767).astype(np.int16).tobytes())
                    rest=y[k:]
                else: k=0; rest=y
                out.writeframes((np.clip(rest,-1,1)*32767).astype(np.int16).tobytes())
                escrito+=(len(rest)+k)/SR; ant=y[-n:]
                if escrito>=ALVO+2: break
            voltas+=1
    dest=PROJ/"trilha_final.m4a"
    subprocess.run([str(FFMPEG),"-y","-loglevel","error","-i",str(bruto),"-t",f"{ALVO:.2f}",
                    "-af",f"afade=t=in:st=0:d=5,afade=t=out:st={ALVO-12:.2f}:d=12,volume={GANHO}",
                    "-c:a","aac","-b:a","128k","-ar",str(SR),str(dest)],check=True)
    (BANCO/"playlist_ep03.json").write_text(json.dumps([{"arquivo":str(p),"nome":p.name} for p in todos],ensure_ascii=False,indent=1),encoding="utf-8")
    print("TRILHA:",dest,f"{dest.stat().st_size/1e6:.1f} MB")

if __name__=="__main__": main()
