# CONTRATO DE TRABALHO — Canal Soninho

> Leia isto **antes** de qualquer alteração. Este projeto é uma linha nova,
> separada do `E:\videomaker\videomaker` (canal Frida & Luna). Aquele contrato
> **não se aplica aqui** — principalmente em `made_for_kids` e duração.

## 1. Regra de ouro

1. Ler `LEIA-ME.md`, `PLANO_SONINHO.md`, `AGENTS.md` e este contrato.
2. Rodar `graphify query "<pergunta>" --budget 1500` antes de perguntar sobre o sistema.
3. **Nunca reimplementar** o que já existe em `scripts/`. Usar os scripts prontos.
4. Antes de mexer em qualquer coisa: branch nova (`git checkout -b feature/...`).
5. Toda mudança de regra/script vai **no mesmo commit** da documentação e do grafo.

## 2. O que é o produto

11 vídeos de **60–90 min** para dormir, **sem narração falada**, com imagens do
acervo que trocam devagar, crossfade real, overlay marinho escuro e partículas suaves.

## 3. Regras duras

| # | Regra |
|---|---|
| 1 | **Nenhuma voz falada, sussurro, canto em vídeo estrangeiro ou CTA falado.** Música é 100% instrumental. |
| 2 | Publicar com **`selfDeclaredMadeForKids = false`** (posicionar como "música para dormir e relaxar", sem falar diretamente com crianças). |
| 3 | Duração alvo 60–90 min. A regra de 10–15 min do canal antigo **não vale aqui**. |
| 4 | Imagens **somente do acervo** (`E:\videomaker\banco de imagens\acervo.db`). Sem Flow/Gemini para imagem. |
| 5 | Uma cena por cluster visual; **nunca repetir** imagem/vídeo entre episódios (`clusters_usados.json`). |
| 6 | Sem stickman/boneco de palito, sem avatar, sem figuras humanas, sem cenas de cozinha/quarto. |
| 7 | Crossfade de 4 s entre todas as cenas. Nenhum corte seco, zoom ou blur. Overlay marinho `#050914` com opacidade 0,15 + vinheta + clamp de brilho. |
| 8 | Vídeos do acervo tocam **uma vez** (nunca `-stream_loop`); cada um na sua duração real. |
| 9 | Música **sem direito autoral**: Audio Library do YouTube Studio (via Chrome autenticado) ou domínio público >100 anos. Nunca YouTube Premium. |
| 10 | **Nunca usar faixas reprovadas** (`banco_musicas/audios_reprovados/`) nem músicas "espaciais". |
| 11 | Overlay de inscrição: `like-subscribe-sonoplastia.mp4` a cada 8 min + `joinha-like-subscribe.mp4` no final, chroma key `#00FF00`, 31% da largura, lower-third, fade 0,2 s, áudio do CTA a −14 dB. |
| 12 | Auditoria obrigatória antes de entregar: duração ≥ 3600 s, luma médio < 90, sem pico de áudio acima de −5 dB. |
| 13 | Nada de `.env`, tokens ou credenciais no git. Binários (MP4/WAV/MP3/PNG) ficam fora do repositório. |

## 4. Comandos

```powershell
python scripts/selecionar_cenas.py ...          # episódio indoors
python scripts/selecionar_cenas_outdoor_v2.py   # episódio outdoor com vídeos
python scripts/criar_ep03_videos.py             # só vídeos + fotos relacionadas
python scripts/preparar_trilha_ep03.py          # trilha com clássicos conhecidos
python scripts/render_sono.py --manifesto ... --playlist ...
python scripts/ajustar_final.py <video>
python scripts/adicionar_subscribe.py <video> --intervalo 480
python scripts/verificar_sono.py <video>
```

## 5. Antes do push

```powershell
python scripts/check_manual.py   # (se existir)
git status
git diff --stat
graphify . --update
```
