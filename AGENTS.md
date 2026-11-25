# AGENTS.md — Soninho (resumo para agentes)

## Comece aqui

1. Leia `CONTRATO.md`, `LEIA-ME.md` e `PLANO_SONINHO.md`.
2. Consulte o grafo: `graphify query "sua pergunta" --budget 1500`.
3. Use os scripts existentes — **não reescreva** pipeline de seleção/render/CTA.
4. Branch nova antes de mexer; documentação + grafo no mesmo commit.

## Estado atual (resumo)

| Episódio | Tema | Cenas | Vídeos | Trilha | Arquivo |
|---|---|---|---|---|---|
| 1 | Soninho da lua | 129 imagens | — | 25 MP3 do usuário | `projetos/ep01/ep01_soninho.mp4` |
| 2 | Passeio no parque (outdoor) | 128 imagens | 20 aprovados visualmente | 25 + 5 + 10 clássicas | `projetos/ep02/ep02_soninho.mp4` |
| 3 | Somente vídeos + 30 overframes | 37 vídeos + 123 fotos | 37 (uma vez cada) | 25 + 10 + 8 grandes compositores | `projetos/ep03/ep03_soninho.mp4` |

Todos: 66–67 min, CTA a cada 8 min + final, auditoria OK.

## Regras que quebram tudo se esquecidas

- **Sem voz/canto/narração.** Música 100% instrumental.
- `made_for_kids=false`.
- **Sem stickman**, sem humano, sem cozinha/quarto, sem repetição de cluster.
- Vídeo **não pode** entrar em loop (`-stream_loop` é proibido nas cenas).
- **Sem músicas espaciais** e sem faixas de `audios_reprovados/`.
- Overlay do CTA: chroma key `#00FF00:0.28:0.12`, 400 px, lower-third, fade 0,2 s.
- Áudio do CTA a −14 dB; `amix` com `normalize=0` (senão a trilha cai).
- Render longo: usar **1 worker** se der erro de memória; chunks de 4 cenas com 4 partículas.

## Estrutura

- `scripts/` — seleção, trilha, render, CTA, auditoria, efeitos.
- `manifestos/` — cenas de cada episódio (sem repetição).
- `efeitos/` — 30+ PNGs transparentes + `movimentos.json`.
- `banco_musicas/` — fontes, playlists, `audios_reprovados/`.
- `assets/audio/` — `catalogo_youtube.json` (SFX + músicas da Audio Library).
- `clusters_usados.json` — memória anti-repetição entre episódios.
- `PLANO_SONINHO.md` — decisões e fluxo completo.

## Auditoria

```powershell
python scripts/verificar_sono.py projetos/epNN/epNN_soninho.mp4
```
Critérios: duração ≥ 3600 s, luma médio < 90, pico de áudio ≤ −5 dB.
