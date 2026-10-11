# SAP 800 ATT

Automação por partes, com mapa de passos versionado e coordenadas **locais** por máquina.

## Como abrir

Dois cliques em `iniciar.bat`  
(na primeira vez cria a `.venv` e instala as dependências).

Na tela:

- **Iniciar automação** — espera **3s** para focar o SAP, depois roda a parte
- **Mapear** — também espera **3s**, **roda o fluxo** (F6, etc.) e só pausa nos cliques; grave com o **botão do meio** (roda). Esc cancela

## Arquivos importantes

| Arquivo | Vai pro Git? | Função |
|---------|--------------|--------|
| `mapa_passos.json` | Sim | Nomes / ids / kinds (**sem** x,y) |
| `pontos_local.json` | **Não** | Coordenadas desta máquina |
| `.scratch/` | Sim | Norte + decisões (não é código) |

## Organização (`automation/`)

| Módulo | Responsabilidade |
|--------|------------------|
| `app_ui.py` | Tela |
| `mapa.py` | Lê o catálogo |
| `kinds.py` | O que precisa XY / auto / usuário |
| `localmap.py` | Captura e grava XY local |
| `teclado.py` | Teclas / atalhos / colar |
| `runner.py` | Executa a parte |
| `win_mouse.py` | Mouse Win32 |

## Kinds

- `click` — mapear + clique automático
- `keys` / `hotkey` / `paste` — automáticos, sem aviso e sem mapear
- `user_action` — pede o usuário (ex.: clicar no XML) e espera OK

Tempos opcionais no passo: `pausa` (entre teclas do mesmo passo) e `pausa_depois` (após o passo; padrão `0.35`). Teclas vão por Win32 SendInput.

## Partes atuais

- `abrir_batch` — F3×2 → clique batch → delete×10 → colar → relógio → lápis
- `pegar_xml` — F6 → Ctrl+F6 → clique do usuário → Ctrl+A → Ctrl+C → F3

Detalhes: `.scratch/partes.md`.

## Observação

Não compartilhe `pontos_local.json` entre PCs (cada máquina mapeia a sua).
