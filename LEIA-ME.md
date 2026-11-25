# Soninho — canal de vídeos para dormir

Workspace independente do repositório antigo (`E:\videomaker\videomaker`).
Projeto publicado em: **https://github.com/PiresDBA/soninho**

## O que é

Vídeos de 60–90 min para dormir: imagens/vídeos do acervo trocando devagar,
crossfade real, cor azul-marinho escura, 30 overframes de movimento, música
instrumental copyright-safe e um CTA discreto (a cada 8 min + final).

## Documentação

| Arquivo | Conteúdo |
|---|---|
| `CONTRATO.md` | regras duras do projeto |
| `AGENTS.md` | resumo para agentes + estado atual |
| `PLANO_SONINHO.md` | decisões, fluxo e histórico de produção |
| `LICENCAS.md`, `LICENCAS_YOUTUBE.md` | origem de cada faixa |
| `assets/audio/catalogo_youtube.json` | SFX + músicas da Audio Library |
| `CLAUDE.md` | regra para consultar o catálogo antes de renderizar |

## Estado atual

| Episódio | Descrição | Arquivo |
|---|---|---|
| 1 | Soninho da lua — 129 imagens | `projetos/ep01/ep01_soninho.mp4` (66,7 min) |
| 2 | Outdoor — 128 imagens + 20 vídeos | `projetos/ep02/ep02_soninho.mp4` (67 min) |
| 3 | 37 vídeos + 123 fotos + 30 overframes | `projetos/ep03/ep03_soninho.mp4` (66,1 min) |

Todos auditados: duração > 60 min, luma escuro, áudio sem picos, CTA correto.

## Como usar

```powershell
$py = "C:\OpenMontage\.venv\Scripts\python.exe"

& $py scripts\selecionar_cenas.py --episodio N --tema "..." --minutos 75 --cena-s 35
& $py scripts\selecionar_cenas_outdoor_v2.py --episodio N --tema "..."
& $py scripts\criar_ep03_videos.py
& $py scripts\preparar_trilha_ep03.py
& $py scripts\render_sono.py --manifesto manifestos\epNN_....json --workers 1 --cenas-por-chunk 4
& $py scripts\ajustar_final.py projetos\epNN\epNN_soninho.mp4
& $py scripts\adicionar_subscribe.py projetos\epNN\epNN_soninho.mp4 --intervalo 480
& $py scripts\verificar_sono.py projetos\epNN\epNN_soninho.mp4
```

> Vídeos, áudios e PNGs **não são versionados** (ver `.gitignore`); estão no disco local.

## Estrutura versionada

- `scripts/` — seleção, trilha, render, CTA, auditoria, efeitos.
- `efeitos/movimentos.json` — catálogo dos 30 overframes.
- `manifestos/` — cenas de cada episódio (sem repetição de cluster).
- `banco_musicas/*.json` — playlists e licenças (áudios ficam fora do git).
- `clusters_usados.json` — memória anti-repetição.
- `graphify-out/` — grafo de conhecimento do projeto.
