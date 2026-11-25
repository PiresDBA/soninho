# -*- coding: utf-8 -*-
"""Baixa classicos conhecidos da Audio Library (copyright-safe)."""
from __future__ import annotations
import json, re, subprocess, sys, io, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"banco_musicas"/"compositores"
DEST.mkdir(parents=True,exist_ok=True)
FFPROBE=Path(r"C:\videomaker\ffmpeg\bin\ffprobe.exe")
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE=r"C:\videomaker\.chrome-gemini-profile"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
CHANNEL="UCe69PXXhJdDEcKN-wCEhRqQ"
IDS=["XKDKpFSCioE","69tdM79ZrHE","gAsrWTsWtPY","MnhL5-QrpOg","GxLc9T5o18c",
     "-P_4cB1aWyc","ss64e1A7Gos","S9NgUO81630"]
CAP={}
def on_request(req):
    if "creator_music/list_tracks" in req.url:
        CAP.setdefault("headers",{k:v for k,v in req.headers.items()
                     if k.lower() in ("content-type","x-youtube-client-name",
                                      "x-youtube-client-version","authorization")})
        CAP.setdefault("post",json.loads(req.post_data))
def main():
    with sync_playwright() as p:
        ctx=p.chromium.launch_persistent_context(PROFILE,executable_path=CHROME,headless=True,user_agent=UA,
            args=["--no-first-run","--no-default-browser-check","--disable-blink-features=AutomationControlled"],
            viewport={"width":1600,"height":1000})
        page=ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("request",on_request)
        page.goto(f"https://studio.youtube.com/channel/{CHANNEL}/music",wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(15000)
        if "headers" not in CAP:
            page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(12000)
        if "headers" not in CAP:
            print("ERRO CAP — pagina:",page.url,"|",page.title()); ctx.close(); return
        payload=json.loads(json.dumps(CAP["post"]))
        payload.pop("filter",None); payload["pageInfo"]={"pageSize":30}
        payload["trackIds"]=IDS; payload["channelId"]=CHANNEL
        payload["mask"]={"includeDownloadUrl":True}
        r=page.evaluate("""async (a)=>{const x=await fetch('https://studio.youtube.com/youtubei/v1/creator_music/get_tracks?alt=json',{method:'POST',headers:a.h,body:JSON.stringify(a.p)});return {status:x.status,body:await x.text()}}""",
                        {"h":CAP["headers"],"p":payload})
        print("API:",r["status"])
        if r["status"]!=200: print(r["body"][:200]); ctx.close(); return
        reg=[]
        for t in json.loads(r["body"]).get("tracks",[]):
            url=t.get("downloadAudioUrl")
            if not url: continue
            nome=re.sub(r"[^a-zA-Z0-9]+","_",t["title"]).strip("_")[:70]+".mp3"
            alvo=DEST/nome
            if not alvo.exists():
                rr=requests.get(url,timeout=120); rr.raise_for_status(); alvo.write_bytes(rr.content)
            print("BAIXADA:",nome)
            reg.append({"arquivo":str(alvo),"titulo":t["title"],"artista":t.get("artist",{}).get("name"),
                        "licenca":"YouTube Audio Library - Sem atribuicao"})
        ctx.close()
    (ROOT/"banco_musicas"/"compositores.json").write_text(json.dumps(reg,ensure_ascii=False,indent=1),encoding="utf-8")
    print("TOTAL:",len(reg))

if __name__=="__main__": main()
