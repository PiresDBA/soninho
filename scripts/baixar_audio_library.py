# -*- coding: utf-8 -*-
"""
Baixa em lote as faixas calmas da Audio Library do YouTube Studio.

Como funciona:
  1) abre a Biblioteca de Audio com o perfil do Chrome do projeto;
  2) captura o payload da API interna creator_music/get_tracks;
  3) pede os trackIds em lotes com mask.includeDownloadUrl=true;
  4) baixa os MP3 assinados e normaliza para M4A -20 LUFS / lowpass 8 kHz.

Uso: python scripts/baixar_audio_library.py
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
BANCO = ROOT / "banco_musicas"
ORIG = BANCO / "youtube_audio_library"
PRON = BANCO / "prontas"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"C:\videomaker\.chrome-gemini-profile"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
FFMPEG = Path(r"C:\videomaker\ffmpeg\bin\ffmpeg.exe")
CHANNEL = "UCe69PXXhJdDEcKN-wCEhRqQ"

GEN_OK = {
    "CREATOR_MUSIC_GENRE_AMBIENT": 5,
    "CREATOR_MUSIC_GENRE_CHILDRENS": 5,
    "CREATOR_MUSIC_GENRE_CLASSICAL": 4,
    "CREATOR_MUSIC_GENRE_CINEMATIC": 3,
    "CREATOR_MUSIC_GENRE_COUNTRY_AND_FOLK": 2,
    "CREATOR_MUSIC_GENRE_JAZZ_AND_BLUES": 1,
}
RUIM = {
    "CREATOR_MUSIC_INSTRUMENT_DRUMS",
    "CREATOR_MUSIC_INSTRUMENT_ELECTRIC_GUITAR",
    "CREATOR_MUSIC_INSTRUMENT_BASS",
    "CREATOR_MUSIC_INSTRUMENT_SYNTH_DRUM",
}
BOM = {
    "CREATOR_MUSIC_INSTRUMENT_PIANO",
    "CREATOR_MUSIC_INSTRUMENT_STRINGS",
    "CREATOR_MUSIC_INSTRUMENT_ACOUSTIC_GUITAR",
}


def score(t: dict) -> int:
    a = t.get("attributes", {})
    d = int(t.get("duration", {}).get("seconds", "0"))
    if "CREATOR_MUSIC_MOOD_CALM" not in a.get("moods", []) or not 80 <= d <= 330:
        return -1
    s = max([GEN_OK.get(g, 0) for g in a.get("genres", [])] or [0])
    if not s:
        return -1
    inst = set(a.get("instruments", []))
    s += 2 if not (inst & RUIM) else -2
    s += 1 if inst & BOM else 0
    return s


def slug(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:70]


def main() -> None:
    ORIG.mkdir(parents=True, exist_ok=True)
    PRON.mkdir(parents=True, exist_ok=True)
    tracks = json.loads((BANCO / "biblioteca_audio_youtube.json").read_text(encoding="utf-8"))
    selecionadas = sorted((t for t in tracks if score(t) > 0), key=lambda t: (-score(t), t["title"]))
    print(f"Selecionadas {len(selecionadas)} faixas = {sum(int(t['duration']['seconds']) for t in selecionadas)/60:.0f} min")

    cap: dict = {}

    def on_request(req):
        if "creator_music/list_tracks" in req.url:
            cap.setdefault("list_headers", {k: v for k, v in req.headers.items()
                           if k.lower() in ("content-type", "x-youtube-client-name",
                                            "x-youtube-client-version", "authorization")})
            try:
                cap.setdefault("list_post", json.loads(req.post_data))
            except Exception:
                pass
        if "creator_music/get_tracks" in req.url:
            cap["url"] = req.url
            cap["post"] = json.loads(req.post_data)
            cap["headers"] = {k: v for k, v in req.headers.items()
                              if k.lower() in ("content-type", "x-youtube-client-name",
                                               "x-youtube-client-version", "authorization")}

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, executable_path=CHROME, headless=True, user_agent=UA,
            args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("request", on_request)
        page.goto(f"https://studio.youtube.com/channel/{CHANNEL}/music",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(9000)
        try:
            page.get_by_text("Ok", exact=True).first.click(timeout=4000)
            page.wait_for_timeout(1000)
        except Exception:
            pass
        if "url" not in cap:
            # fallback: monta o pedido get_tracks a partir do payload de list_tracks
            if "list_post" not in cap or "list_headers" not in cap:
                print("FALHA: nao capturou a API do Studio"); ctx.close(); return
            cap["url"] = f"https://studio.youtube.com/youtubei/v1/creator_music/get_tracks?alt=json"
            cap["headers"] = cap["list_headers"]
            cap["post"] = {"context": cap["list_post"]["context"],
                           "trackIds": [], "channelId": CHANNEL,
                           "mask": {"includeDownloadUrl": True}}
            print("API get_tracks montada via fallback")

        registros = []
        for i in range(0, len(selecionadas), 10):
            lote = selecionadas[i:i + 10]
            payload = json.loads(json.dumps(cap["post"]))
            payload["trackIds"] = [t["trackId"] for t in lote]
            payload["channelId"] = CHANNEL
            payload["mask"] = {"includeDownloadUrl": True}
            resp = page.evaluate("""async (a) => {
              const r = await fetch(a.url, {method:'POST', headers:a.headers, body:JSON.stringify(a.post)});
              return {status:r.status, body:await r.text()};
            }""", {"url": cap["url"], "headers": cap["headers"], "post": payload})
            if resp["status"] != 200:
                print("API ERRO", resp["status"], resp["body"][:200]); continue
            dados = json.loads(resp["body"])
            for track in dados.get("tracks", []):
                url = track.get("downloadAudioUrl")
                if not url:
                    print("SEM URL:", track.get("title")); continue
                nome = slug(f"{track.get('title','')} - {track.get('artist',{}).get('name','')}")
                mp3 = ORIG / f"{nome}.mp3"
                m4a = PRON / f"yt_{nome}.m4a"
                if not mp3.exists():
                    try:
                        r = requests.get(url, timeout=120)
                        r.raise_for_status()
                        mp3.write_bytes(r.content)
                    except Exception as e:
                        print("DOWNLOAD FALHOU:", track.get("title"), type(e).__name__); continue
                if not m4a.exists():
                    cmd = [str(FFMPEG), "-y", "-loglevel", "error", "-i", str(mp3),
                           "-af", "lowpass=f=8000,loudnorm=I=-20:TP=-2:LRA=7",
                           "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "128k", str(m4a)]
                    subprocess.run(cmd, check=True)
                registros.append({
                    "titulo": track.get("title"), "artista": track.get("artist", {}).get("name"),
                    "trackId": track.get("trackId"), "duracao_s": int(track.get("duration", {}).get("seconds", 0)),
                    "genero": track.get("attributes", {}).get("genres", []),
                    "clima": track.get("attributes", {}).get("moods", []),
                    "licenca": track.get("licenseType"), "origem": "YouTube Audio Library",
                    "mp3": str(mp3), "pronto": str(m4a),
                })
            print(f"lote {i//10+1}: {len(registros)} faixas prontas")
            time.sleep(0.5)
        ctx.close()

    (BANCO / "musicas_youtube.json").write_text(
        json.dumps(registros, ensure_ascii=False, indent=1), encoding="utf-8")
    linhas = ["# Licenças — YouTube Audio Library (canal Soninho)", "",
              "Faixas obtidas pela Biblioteca de Áudio do YouTube Studio, conta conectada.",
              "Licença: `CREATOR_MUSIC_LICENSE_TYPE_YOUTUBE` (copyright-safe no YouTube).",
              "Se alguma faixa aparecer como Creative Commons no Studio, copie o crédito",
              "para a descrição do vídeo antes de publicar.", ""]
    for r in registros:
        linhas.append(f"- **{r['titulo']}** — {r['artista']} ({r['duracao_s']}s) · {r['licenca']} · `{r['pronto']}`")
    (ROOT / "LICENCAS_YOUTUBE.md").write_text("\n".join(linhas), encoding="utf-8")
    print(f"TOTAL: {len(registros)} faixas, {sum(r['duracao_s'] for r in registros)/60:.0f} min")


if __name__ == "__main__":
    main()
