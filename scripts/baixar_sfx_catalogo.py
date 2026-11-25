# -*- coding: utf-8 -*-
"""Cataloga e baixa SFX + 5 musicas novas da Audio Library via Chrome autenticado."""
from __future__ import annotations
import json, re, subprocess, sys, io, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "assets" / "audio"
SFX_DIR = AUDIO / "youtube_sfx"
MUS_DIR = AUDIO / "youtube_music"
FFPROBE = Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"C:\videomaker\.chrome-gemini-profile"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
CHANNEL = "UCe69PXXhJdDEcKN-wCEhRqQ"
CAP = {}

def on_request(req):
    if "creator_music/list_tracks" in req.url:
        try:
            CAP.setdefault("headers", {k:v for k,v in req.headers.items()
                          if k.lower() in ("content-type","x-youtube-client-name",
                                           "x-youtube-client-version","authorization")})
            CAP.setdefault("post", json.loads(req.post_data))
            CAP.setdefault("url", req.url)
        except Exception:
            pass

def fetch(page, payload, url=None):
    r = page.evaluate("""async (a) => {
      const resp = await fetch(a.url, {method:'POST', headers:a.headers, body:JSON.stringify(a.post)});
      return {status:resp.status, body:await resp.text()};
    }""", {"url":url or CAP["url"], "headers":CAP["headers"], "post":payload})
    if r["status"] != 200:
        raise RuntimeError(f"HTTP {r['status']}: {r['body'][:150]}")
    return json.loads(r["body"])

def listar(page, soundeffect: bool, limite=40):
    out = []
    token = None
    for _ in range(limite):
        p = json.loads(json.dumps(CAP["post"]))
        p["channelId"] = CHANNEL
        p["filter"] = ({"trackTypeIn":{"values":["CREATOR_MUSIC_TRACK_TYPE_SOUNDEFFECT"]}}
                       if soundeffect else {})
        if token: p["pageInfo"]["pageToken"] = token
        d = fetch(page, p)
        out += d.get("tracks", [])
        token = d.get("pageInfo",{}).get("nextPageToken")
        if not token or not d.get("tracks"): break
    return out

def baixar(page, tracks, destino, tags_por_faixa):
    destino.mkdir(parents=True, exist_ok=True)
    registros = []
    for i in range(0, len(tracks), 10):
        lote = tracks[i:i+10]
        p = json.loads(json.dumps(CAP["post"]))
        p.pop("filter", None)
        p["pageInfo"] = {"pageSize": 30}
        p["trackIds"] = [t["trackId"] for t in lote]
        p["channelId"] = CHANNEL
        p["mask"] = {"includeDownloadUrl": True}
        d = fetch(page, p, "https://studio.youtube.com/youtubei/v1/creator_music/get_tracks?alt=json")
        if not d.get("tracks") and i == 0:
            print("DEBUG_GET_TRACKS:", json.dumps(d, ensure_ascii=False)[:400])
        for t in d.get("tracks", []):
            url = t.get("downloadAudioUrl")
            if not url: continue
            nome = re.sub(r"[^a-zA-Z0-9]+", "_", t.get("title","")).strip("_")[:70] + ".mp3"
            alvo = destino / nome
            if not alvo.exists():
                r = requests.get(url, timeout=90)
                r.raise_for_status()
                alvo.write_bytes(r.content)
            dur = 0.0
            try:
                rr = subprocess.run([str(FFPROBE),"-v","error","-show_entries","format=duration",
                                     "-of","csv=p=0",str(alvo)],capture_output=True,text=True)
                dur = float(rr.stdout.strip())
            except Exception: pass
            registros.append({"arquivo": str(alvo.relative_to(ROOT)).replace("\\","/"),
                              "titulo": t.get("title"),
                              "categoria": "sfx" if destino == SFX_DIR else "musica",
                              "duracao_segundos": round(dur,1),
                              "tags": tags_por_faixa(t),
                              "licenca": "YouTube Audio Library - Sem atribuição"})
        time.sleep(0.3)
    return registros

def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(PROFILE, executable_path=CHROME, headless=True,
            user_agent=UA, args=["--no-first-run","--no-default-browser-check",
            "--disable-blink-features=AutomationControlled"], viewport={"width":1600,"height":1000})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("request", on_request)
        page.goto(f"https://studio.youtube.com/channel/{CHANNEL}/music", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(9000)
        try: page.get_by_text("Ok", exact=True).first.click(timeout=4000); page.wait_for_timeout(1000)
        except Exception: pass
        if "url" not in CAP:
            print("FALHA: nao capturou a API"); ctx.close(); return
        print("LISTANDO SFX...")
        sfx = listar(page, True, 30)
        print("SFX no catalogo:", len(sfx))
        alvo_tags = {
          "sino": ["bell","chime","ding","tinkle","sleigh","music box","xylophone"],
          "clique": ["click","pop","button","tap","tick","blip","select","switch"],
          "transicao": ["whoosh","swoosh","swish","soft","slide","air","breeze"],
        }
        escolhidos = []
        for cat, chaves in alvo_tags.items():
            achados = [t for t in sfx if any(k in t.get("title","").lower() for k in chaves)]
            achados = [t for t in achados if float(t.get("duration",{}).get("seconds",0)) <= 30]
            print(f"  {cat}: {len(achados)}")
            escolhidos += achados[:5]
        # dedup
        vistos = set(); sfx_sel = []
        for t in escolhidos:
            if t["trackId"] in vistos: continue
            vistos.add(t["trackId"]); sfx_sel.append(t)
        print("SFX SELECIONADOS:", len(sfx_sel))

        print("LISTANDO MUSICAS...")
        musicas = listar(page, False, 40)
        print("Musicas no catalogo:", len(musicas))
        def tags_musica(t):
            a=t.get("attributes",{})
            return ["ninar","suave","instrumental"] + [g.split("_")[-1].lower() for g in a.get("genres",[])]
        candidatas = []
        for t in musicas:
            a = t.get("attributes",{})
            d = int(t.get("duration",{}).get("seconds","0"))
            genres = set(a.get("genres",[]))
            inst = set(a.get("instruments",[]))
            if "CREATOR_MUSIC_MOOD_CALM" not in a.get("moods",[]): continue
            if not (genres & {"CREATOR_MUSIC_GENRE_AMBIENT","CREATOR_MUSIC_GENRE_CHILDRENS"}): continue
            if not 90 <= d <= 300: continue
            if inst & {"CREATOR_MUSIC_INSTRUMENT_DRUMS","CREATOR_MUSIC_INSTRUMENT_ELECTRIC_GUITAR"}: continue
            if t.get("licenseType") != "CREATOR_MUSIC_LICENSE_TYPE_YOUTUBE": continue
            candidatas.append(t)
        # evita as 25 musicas ja usadas no episodio 1
        usadas = set()
        pl1 = ROOT / "banco_musicas" / "playlist_instrumental.json"
        if pl1.exists():
            usadas = set(Path(i["arquivo"]).stem.lower() for i in json.loads(pl1.read_text(encoding="utf-8")))
        candidatas = [t for t in candidatas if re.sub(r"[^a-z0-9]+","",t["title"].lower()) not in usadas]
        print("Candidatas novas:", len(candidatas))
        mus_sel = candidatas[:5]
        print("MUSICAS SELECIONADAS:", [t["title"] for t in mus_sel])

        reg = baixar(page, sfx_sel, SFX_DIR,
                     lambda t: ["sfx"] + [k for k in ["bell","chime","click","pop","whoosh","soft"]
                                          if k in t.get("title","").lower()])
        reg += baixar(page, mus_sel, MUS_DIR, tags_musica)
        ctx.close()
    (AUDIO / "catalogo_youtube.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    print("CATALOGO:", AUDIO / "catalogo_youtube.json", len(reg), "arquivos")

if __name__ == "__main__":
    main()
