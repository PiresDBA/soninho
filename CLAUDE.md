# Biblioteca de Áudio (SFX e Trilhas) — canal Soninho

- Sempre que precisar de efeitos sonoros (cliques, sinos, transições) ou trilhas
  livres de royalties, consulte **primeiro** o índice local
  `./assets/audio/catalogo_youtube.json` e use os MP3 em `./assets/audio/youtube_sfx/`
  e `./assets/audio/youtube_music/`.
- Se faltar um efeito específico, use o Playwright/Chrome autenticado do projeto
  (perfil `C:\videomaker\.chrome-gemini-profile`) para entrar em
  `https://studio.youtube.com` → **Biblioteca de áudio**, baixar o MP3 e atualizar
  `catalogo_youtube.json` **antes** de renderizar o vídeo.
- Não existe API pública oficial na YouTube Data API v3 para a Audio Library;
  o acesso é via sessão autenticada do Studio (não depende de YouTube Premium).
- Faixas com licença `CREATOR_MUSIC_LICENSE_TYPE_YOUTUBE` não exigem atribuição.
- Nunca usar faixas com voz/canto neste canal (marcação do vídeo é `made_for_kids=false`
  e o público pode estar em qualquer país).
- Músicas reprovadas ficam em `banco_musicas/audios_reprovados/` — não voltar a usar.
