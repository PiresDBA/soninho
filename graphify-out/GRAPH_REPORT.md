# Graph Report - soninho  (2026-11-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 185 nodes · 552 edges · 9 communities
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8

## God Nodes (most connected - your core abstractions)
1. `main()` - 10 edges
2. `main()` - 9 edges
3. `main()` - 9 edges
4. `main()` - 8 edges
5. `baixar()` - 8 edges
6. `gerar()` - 8 edges
7. `gerar()` - 8 edges
8. `main()` - 8 edges
9. `main()` - 8 edges
10. `main()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `rodar()` --calls--> `subprocess`  [EXTRACTED]
  scripts/adicionar_subscribe.py →   _Bridges community 6 → community 4_
- `main()` --calls--> `argparse`  [EXTRACTED]
  scripts/adicionar_subscribe.py →   _Bridges community 6 → community 3_
- `rodar()` --calls--> `subprocess`  [EXTRACTED]
  scripts/ajustar_final.py →   _Bridges community 2 → community 4_
- `norm()` --calls--> `re`  [EXTRACTED]
  scripts/atualizar_efeitos.py →   _Bridges community 2 → community 3_
- `main()` --calls--> `json`  [EXTRACTED]
  scripts/atualizar_efeitos.py →   _Bridges community 2 → community 0_

## Import Cycles
- None detected.

## Communities (9 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (15): main(), score(), slug(), main(), main(), on_request(), info(), limpar() (+7 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (16): desenhar(), main(), cometa(), coracao_extras(), salvar(), solzinho(), gerar(), main() (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (11): main(), rodar(), main(), norm(), main(), main(), norm(), tokens() (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.20
Nodes (12): main(), rodar(), base_nome(), escolher_efeito(), main(), norm(), base_nome(), main() (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.19
Nodes (13): duracao(), fontes(), ler(), main(), normalizar(), dur(), ler(), main() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (7): duracao_video(), main(), tarefa(), montar_audio(), png_do_efeito(), render_chunk(), run()

### Community 6 - "Community 6"
Cohesion: 0.31
Nodes (5): audio_do_clipe(), duracao(), main(), rodar(), main()

### Community 7 - "Community 7"
Cohesion: 0.38
Nodes (5): duracao(), ler_wav(), main(), normalizar(), selecionar()

### Community 8 - "Community 8"
Cohesion: 0.39
Nodes (7): buscar_e_baixar_classicas(), duracao(), fontes_usuario(), ler(), main(), normalizar(), on_request()

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 5` to `Community 0`, `Community 3`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.14516129032258066 - nodes in this community are weakly interconnected._
- **Why does `main()` connect `Community 0` to `Community 4`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.12701612903225806 - nodes in this community are weakly interconnected._
- **Why does `ler()` connect `Community 4` to `Community 1`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.10804597701149425 - nodes in this community are weakly interconnected._