# SAP 800 ATT

Automação por partes, com mapa de passos versionado e coordenadas **locais** por máquina.

## Como abrir

**Tela:** dois cliques em `iniciar.bat` (cria a `.venv` na 1ª vez).

**Terminal** (melhor para ver erros / traceback):

```powershell
cd "caminho\para\sap_800_att"
.\.venv\Scripts\Activate.ps1

python main.py listar
python main.py excel                          # proxima linha Status=Pendente
python main.py fluxo --excel                  # fluxo com Batch + Issuer Id do Excel
python main.py fluxo --batch X --issuer Y     # manual
python main.py parte abrir_batch --excel
```

Ou: `rodar-fluxo.bat` (Excel) / `rodar-fluxo.bat BATCH ISSUER`

Na tela:

- **Iniciar tudo** — fluxo completo (`mapa_passos.json` → `fluxo`)
- **Iniciar parte** — só a parte selecionada
- **Mapear** — 3s de foco, executa a parte e pausa nos cliques (botão do meio)

Novas partes no fluxo: acrescente o nome em `"fluxo"` no `mapa_passos.json`.

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
- `map_only` — só calibração no Mapear (fluxo ignora)
- `fill_itens` — preenche linhas de item a partir do XML
- `fill_taxes` — seleção de itens + Taxes / Other Base / CBS-IBS
- `keys` / `hotkey` / `paste` / `type` — automáticos, sem mapear
- `user_action` — pede o usuário e espera OK

Tempos opcionais no passo: `pausa` (entre teclas do mesmo passo) e `pausa_depois` (após o passo; padrão `0.35`). Teclas vão por Win32 SendInput.

## Partes atuais

- `abrir_batch` — F3×2 → clique batch → delete×10 → colar → relógio → lápis
- `pegar_xml` — F6 → Ctrl+F6 → clique XML → Ctrl+A → Ctrl+C → F3
- `abrir_oj1b1n` — `/oj1b1n` → Enter → X0 → Tab×2 → filial → Tab → V → Tab → Partner ID → Enter
- `preencher_oj1b1n` — Nine-Digit No (`000003319`) → Tab → série (`004`) → Tab → issue date
- `preencher_itens` — âncoras de linha (Mapear) → por item: `1` + material/desc/qtd/preço + CFOP/AA + impostos + Plant
- `preencher_taxes` — seleciona N itens → Taxes → Value → Other Base → Taxes II → CBS/IBS → E matemático
- `preencher_nfe_data` — Protocol No/Date/Time + Random No (da chave) + DV

Detalhes: `.scratch/partes.md`.

## Parar a automação

Durante o fluxo ou uma parte: aperte **Esc** (funciona mesmo com o SAP em foco).

## Observação

Não compartilhe `pontos_local.json` entre PCs (cada máquina mapeia a sua).
