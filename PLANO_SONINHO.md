# Canal Soninho — plano operacional (decisões fechadas em 24/11/2026)

## Decisões do usuário

| Item | Decisão |
|---|---|
| Canal | **Novo**, exclusivo para sono/relaxamento. Não é o canal Frida & Luna. |
| Marcação YouTube | **`made_for_kids = false` ("falsa")** — para não perder alcance/comentários/notificações. Posicionar o canal como "música para dormir e relaxar" (sem falar diretamente com crianças, sem personagens falantes), para que a marcação seja honesta e defensável. |
| Narração | **Nenhuma.** Sem voz falada, sem sussurro, sem CTA, sem texto de tela. |
| Versões | **100% instrumental** (decisão revisada): faixas com canto foram removidas para nunca sair canto em outro idioma. |
| Duração | **1h a 1h30** — regra dos 10–15 min do contrato antigo **não se aplica** a esta linha. |
| Imagens | **Somente o acervo existente** (`E:\videomaker\banco de imagens\acervo.db`). Sem Google Flow, sem Gemini para imagem, custo zero. |
| Música | **YouTube Audio Library** (via Studio, conta conectada) + domínio público/CC0 da Wikimedia Commons como reforço. |
| Contrato | O `CONTRATO.md` do projeto antigo continua valendo para o canal antigo; a linha Soninho tem este documento como regra própria e deve ser registrada no `MANUAL_GRAFOS.md` como §79 antes de virar commit. |

## O que já está pronto

- `banco_musicas/biblioteca_audio_youtube.json` — 1.200 faixas listadas da Audio Library (176 "Calmo", 52 Ambient, 104 Clássica, 34 Infantil).
- `banco_musicas/ninar_original/` — **31 MP3s de ninar adicionados pelo usuário**; 25 selecionados (sem versão vocal, sem duplicatas). Inclui *Bedtime*, *First Sleep*, *Sleeping Sheep*, *Rock-a-bye Baby*, *Are You Sleeping*, *Twinkle Twinkle Little Star*, *Snowfall*, Esther Abrami, etc.
- `banco_musicas/novas_prontas/` — versões normalizadas; `playlist_instrumental.json` é a fonte única da trilha dos próximos episódios.
- Trilha do episódio 1 gerada com **crossfade de 3 s** entre as 25 faixas, 65,8 min de música para 66,7 min de vídeo. Músicas antigas arquivadas em `arquivo_musicas_antigas/`.
- `banco_musicas/prontas/*.wav` — 7 faixas de domínio público/CC0 da Wikimedia (Brahms, caixa de música, vocal).
- `LICENCAS.md` e `LICENCAS_YOUTUBE.md` — procedência de cada faixa.
- `manifestos/ep01_soninho-da-lua.json` — 129 cenas únicas / 75,2 min, selecionadas do acervo sem repetição de cluster, sem stickman/avatar/humanos/cenas ensolaradas.
- `scripts/render_sono.py` — renderizador com crossfade real, overlay marinho, partículas suaves (folha/gota/coração/estrela/zzz) e trilha contínua, sem narração.
- ✅ **Episódio 1 pronto:** `projetos/ep01/ep01_soninho.mp4` — **66,7 min**, 204 MB.
  Auditoria final (`ep01_soninho.auditoria.json`): luma médio **36,8** (pico 80,6),
  áudio médio **−26,4 dB** (pico **−7,9 dB**) — escuro e sem picos que acordem.
  9 inserções de CTA: 8 a cada 8 min + 1 no final. Trilha 100% com as 25 músicas novas.
  A duração caiu de 75,2 para 66,7 min por causa dos crossfades de 4 s.

## Fluxo

```powershell
$py = "C:\OpenMontage\.venv\Scripts\python.exe"

# 1) atualizar catálogo da Audio Library (opcional)
& $py scripts\baixar_audio_library.py

# 2) selecionar cenas do episódio (60 a 90 min)
& $py scripts\selecionar_cenas.py --episodio 2 --tema "chuva calma" --minutos 75 --cena-s 35

# 3) conferir amostra de 3 cenas (24 s)
& $py scripts\render_sono.py --manifesto manifestos\ep02_....json --demo --workers 3

# 4) renderizar episódio completo (roda em background)
& $py scripts\render_sono.py --manifesto manifestos\ep02_....json --workers 4

# 5) auditoria
& $py scripts\verificar_sono.py projetos\ep02\ep02_soninho.mp4

# 6) publicar: thumbnail escura, título com duração, made_for_kids=false
```

## Episódio 2 (outdoor) — em produção

- Manifesto `manifestos/ep02_outdoor_passeio-no-parque.json`: **129 cenas outdoor**
  (parque, jardim, floresta, praia, praça, campo), animação, sem humanos, sem
  cluster já usado no episódio 1. Efeitos: folhas/chuva/sol/bolhas/cometa/zzz.
- Trilha **diferente do episódio 1**: 12 ninar originais novas (seed 20261125) +
  17 faixas sleep da Audio Library (`Somnia`, `Sleep Music`, `Moonlight Magic`...),
  crossfade de 3 s, playlist em `playlist_ep02.json`.
- ✅ **Episódio 2 final corrigido:** `projetos/ep02/ep02_soninho.mp4` — 67,0 min, 204 MB.
  Auditoria OK: luma médio 45,4 (pico 71,1), áudio −26,0 dB (pico −7,9 dB).
  20 vídeos outdoor aprovados visualmente, sem loop, zero stickman; 10 inserções de CTA.
  (Detalhes da correção abaixo.)
  - **20 vídeos reais intercalados** (1 a cada 6 imagens), cada um tocando **uma vez**
    (sem `-stream_loop`); selecionados por **auditoria visual** em `auditoria_todos_videos_p*.jpg`.
  - Zero stickman/boneco de palito, zero cenas de cozinha/quarto entre os vídeos.
  - Trilha v3: 25 músicas do usuário + 5 novas da Audio Library + 10 clássicas
    instrumentais (cordas/piano), com crossfade de 3 s — `playlist_ep02_v3.json`.
  - Catálogo local em `assets/audio/catalogo_youtube.json` (15 SFX: sino/clique/whoosh
    + 5 músicas), regra registrada em `CLAUDE.md`.
  - Áudios reprovados isolados em `banco_musicas/audios_reprovados/`.

## Episódio 3 (somente vídeos + 30 overframes) — PRONTO

`projetos/ep03/ep03_soninho.mp4` — 66,1 min, 204 MB. Auditoria OK: luma 47,4
(pico 65,7), áudio −27,0 dB (pico −7,9 dB), 9 CTAs. 37 vídeos + 123 fotos.

---

## Detalhes da produção do episódio 3

- 37 vídeos aprovados visualmente (jardim/parque/lua) com **123 fotos relacionadas**
  intercaladas — `manifestos/ep03_somente_videos.json`, 160 cenas, 66 min.
- Vídeos em sequência por tema; cada clipe toca uma vez.
- **30 novos overframes** em `efeitos/` (`movimentos.json`): estrela cadente, estrelinhas
  piscando, galho caindo, mosquinha, borboletas, folhas redemoinho, gotas, nuvens,
  lua, brilho, corações, bolhas, confete, neve, pétalas, sementes, espuma, onda,
  traços de luz, pó de estrelas, fagulhas, arco-íris, folha giro, pluminhas,
  pingos finos, lágrimas de luz, borboletas luz, zeco subindo, estrela giro, brisa.
- Trilha SEM músicas espaciais: 25 do usuário + 10 clássicas + 8 grandes compositores
  (Bach *Air on the G String*, Vivaldi *Four Seasons*, Mozart *Don Giovanni*,
  Offenbach *Barcarolle*, Schubert *Ave Maria*, Debussy, Lullabye No.108), todos da
  Audio Library (copyright-safe), intercalados 3 normais + 1 clássica.

## Os 11 episódios (fila)

1. Soninho da Lua · 2. Chuva Calma · 3. Jardim Adormecido · 4. Estrelinhas ·
5. Nave do Sonho · 6. Cobertor Quente · 7. Bichinhos Dormindo · 8. Maré Suave ·
9. Flocos de Neve · 10. Sonho da Frida e da Luna · 11. Amanhecer Tranquilo.

Cada episódio usa `clusters_usados.json` para não repetir imagem entre vídeos.
Com 35 s/cena, 11 × 75 min ≈ 1.419 cenas — o pool calmo animado tem 1.471 imagens
em 1.268 clusters; se faltar, o plano B é 40 s/cena ou abrir mais ambientes.

## Regras visuais/sonoras (revisadas 24/11 a pedido do usuário)

- **Crossfade real entre TODAS as cenas** (`xfade=transition=fade:duration=4s`).
  Não há corte seco nem "apagão" até o azul: a imagem seguinte dissolve sobre a anterior.
  Render em 2 passos: grupos de 6 cenas são fundidos (chunk) e depois os chunks são
  fundidos entre si — só 2 re-encodes, crossfade em toda parte.
- **Overlay que impede a TV de acender o quarto:** camada azul-marinho `0x050914`
  com opacidade 0,10 sobre cada cena + vinheta suave (`PI/7`) + `eq` de brilho/saturação.
  Medido na amostra: **luma médio 33/255, pico 44** (escuro, mas ainda dá para ver Frida e Luna).
  Ajustável com `--dim 0.05` (mais escuro) a `--dim 0.25` (mais claro).
- Sem branco puro, sem flash, sem zoom, sem blur (regra do projeto antigo mantida).
- **Overframes variados:** cometa, chuva, solzinho, passarinhos, bolhas, coração,
  zzz, folhas e estrelas — sorteados cena a cena, nunca repetidos em cenas
  consecutivas e com teto de 18% do total por efeito (`scripts/atualizar_efeitos.py`).
  PNGs extras criados em `efeitos/` (`cometa.png`, `solzinho.png`, `coracao_suave.png`).
- **Overlay de inscrição:** `like-subscribe-sonoplastia.mp4` **a cada 8 min** durante
  o vídeo + `joinha-like-subscribe.mp4` **nos últimos 10 s**. Chroma key
  `colorkey=0x00FF00:0.28:0.12` + `despill`, 400 px (31% da largura), lower-third
  centralizado com 5% de margem, fade in/out de 0,2 s. Áudio dos CTA mantido a
  −14 dB (`volume=0.20`), `amix` com `normalize=0` para não baixar a trilha.
  Render em 2 passagens (vídeo via `setpts`, áudio via `adelay`) — sem `-stream_loop`.
- Áudio: médio −25 dB, pico −5,5 dB (`volume=0.55`), sem picos que acordem.
- Sem narração e sem texto de tela além do overlay discreto de inscrição.
- Cenas `.mp4` do acervo são tratadas como vídeo (`-stream_loop`), não como imagem.
