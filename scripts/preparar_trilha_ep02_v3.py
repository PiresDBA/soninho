# -*- coding: utf-8 -*-
"""Trilha ep02 v3: musicas do usuario + 5 novas + 10 classicas instrumentais."""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, io, wave, time
from pathlib import Path
import numpy as np
import requests
from playwright.sync_api import sync_playwright
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
BANCO = ROOT / "banco_musicas"
USER = BANCO / "ninar_original"
NOVAS = ROOT / "assets" / "audio" / "youtube_music"
CLASSICAS = BANCO / "classicas_novas"
PRON = BANCO / "ep02_v3_prontas"
PROJ = ROOT / "projetos" / "ep02"
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"C:\videomaker\.chrome-gemini-profile"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
CHANNEL = "UCe69PXXhJdDEcKN-wCEhRqQ"
TITULOS_CLASSICOS = [
    "The Swan", "A New Adventure", "Across Seas And Lands", "Ripples In Time",
    "Spinning And Swirling", "The Wind", "My Dear One", "Silent Hymns",
    "Quiet Walks", "Temple Of Air",
]
SR, CROSS, GANHO, ALVO = 48000, 3.0, 0.55, 4020.0
CAP = {}
def on_request(req):
    if "creator_music/list_tracks" in req.url:
        CAP.setdefault("headers", {k:v for k,v in req.headers.items()
                      if k.lower() in ("content-type","x-youtube-client-name",
                                       "x-youtube-client-version","authorization")})
        CAP.setdefault("post", json.loads(req.post_data))
        CAP.setdefault("url", req.url)

def buscar_e_baixar_classicas():
    CLASSICAS.mkdir(parents=True, exist_ok=True)
    catalogo = json.loads((BANCO / "biblioteca_audio_youtube.json").read_text(encoding="utf-8"))
    desejados = [t for t in catalogo if t["title"] in TITULOS_CLASSICOS]
    print("CLASSICAS ENCONTRADAS:", len(desejados))
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(PROFILE, executable_path=CHROME, headless=True,
            user_agent=UA, args=["--no-first-run","--no-default-browser-check",
            "--disable-blink-features=AutomationControlled"], viewport={"width":1600,"height":1000})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("request", on_request)
        page.goto(f"https://studio.youtube.com/channel/{CHANNEL}/music", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(9000)
        if "url" not in CAP:
            print("ERRO: sem CAP"); ctx.close(); return []
        for i in range(0, len(desejados), 10):
            lote = desejados[i:i+10]
            payload = json.loads(json.dumps(CAP["post"]))
            payload.pop("filter", None)
            payload["pageInfo"] = {"pageSize": 30}
            payload["trackIds"] = [t["trackId"] for t in lote]
            payload["channelId"] = CHANNEL
            payload["mask"] = {"includeDownloadUrl": True}
            r = page.evaluate("""async (a) => {
              const resp = await fetch('https://studio.youtube.com/youtubei/v1/creator_music/get_tracks?alt=json',
                {method:'POST', headers:a.headers, body:JSON.stringify(a.post)});
              return {status:resp.status, body:await resp.text()};
            }""", {"headers":CAP["headers"], "post":payload})
            if r["status"] != 200:
                print("ERRO API:", r["status"], r["body"][:150]); continue
            for t in json.loads(r["body"]).get("tracks", []):
                url = t.get("downloadAudioUrl")
                if not url: continue
                nome = re.sub(r"[^a-zA-Z0-9]+","_",t["title"]).strip("_")[:70] + ".mp3"
                alvo = CLASSICAS / nome
                if not alvo.exists():
                    rr = requests.get(url, timeout=90); rr.raise_for_status(); alvo.write_bytes(rr.content)
                print("CLASSICA:", nome)
        ctx.close()
    return sorted(CLASSICAS.glob("*.mp3"))

def duracao(p):
    r = subprocess.run([str(FFPROBE),"-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(p)],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except Exception: return 0.0

def fontes_usuario():
    arquivos = sorted(USER.glob("*.mp3"))
    hashes = {}
    for p in arquivos:
        hashes.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(), p)
    out = list(hashes.values())
    out = [p for p in out if "vocal" not in p.name.lower()]
    inst = [p for p in out if "instrumental" in p.name.lower()]
    bases = set(re.sub(r"\s*\(instrumental\)","",p.name,flags=re.I).lower() for p in inst)
    out = [p for p in out if "instrumental" in p.name.lower() or p.name.lower() not in bases]
    return out

def normalizar(p):
    dest = PRON / (re.sub(r"[^a-zA-Z0-9]+","_",p.stem).strip("_")[:80] + ".wav")
    if not dest.exists():
        subprocess.run([str(FFMPEG),"-y","-loglevel","error","-i",str(p),
                        "-af","lowpass=f=8000,loudnorm=I=-19:TP=-3:LRA=7",
                        "-ar",str(SR),"-ac","2","-c:a","pcm_s16le",str(dest)],check=True)
    return dest

def ler(p):
    with wave.open(str(p),"rb") as w:
        x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
    return x.reshape(-1,2)

def main():
    PRON.mkdir(parents=True, exist_ok=True)
    cl = buscar_e_baixar_classicas()
    todas = fontes_usuario() + sorted(NOVAS.glob("*.mp3")) + cl
    print("FONTES TOTAIS:", len(todas), "| usuario:", len(fontes_usuario()),
          "| novas:", len(list(NOVAS.glob('*.mp3'))), "| classicas:", len(cl))
    prontas = [normalizar(p) for p in todas]
    print("DURACAO TOTAL DAS FAIXAS:", round(sum(duracao(p) for p in prontas)/60,1), "min")
    ordem = np.random.default_rng(261124).permutation(len(prontas)).tolist()
    bruto = PROJ / "_trilha_crossfade.wav"
    n_cross = int(CROSS*SR)
    with wave.open(str(bruto),"wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
        anterior=None; escrito=0.0; voltas=0
        while escrito < ALVO+2 and voltas < 5:
            for i in ordem:
                y=ler(prontas[i])
                if anterior is not None:
                    n=min(n_cross,len(y),len(anterior))
                    rp=np.linspace(0,1,n,dtype=np.float32)[:,None]
                    out.writeframes((np.clip(anterior[:n]*(1-rp)+y[:n]*rp,-1,1)*32767).astype(np.int16).tobytes())
                    rest=y[n:]
                else:
                    n=0; rest=y
                out.writeframes((np.clip(rest,-1,1)*32767).astype(np.int16).tobytes())
                escrito += (len(rest)+n)/SR
                anterior = y[-n_cross:]
                if escrito >= ALVO+2: break
            voltas+=1
    destino = PROJ / "trilha_final.m4a"
    subprocess.run([str(FFMPEG),"-y","-loglevel","error","-i",str(bruto),
                    "-t",f"{ALVO:.2f}",
                    "-af",f"afade=t=in:st=0:d=5,afade=t=out:st={ALVO-12:.2f}:d=12,volume={GANHO}",
                    "-c:a","aac","-b:a","128k","-ar",str(SR),str(destino)],check=True)
    (BANCO / "playlist_ep02_v3.json").write_text(json.dumps(
        [{"arquivo":str(p),"nome":p.name} for p in prontas],ensure_ascii=False,indent=1),encoding="utf-8")
    print("TRILHA FINAL:", destino, f"{destino.stat().st_size/1e6:.1f} MB")

if __name__ == "__main__":
    main()
