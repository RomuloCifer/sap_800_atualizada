# Estado do projeto (atualizado)

Última atualização relevante: Excel documentado — Batch (D), Issuer Id (R), Total Value (T); sem lógica ainda.

## Organização

```text
sap_800_att/
  iniciar.bat              # abrir a tela (cria venv se precisar)
  main.py                  # entrada
  mapa_passos.json         # GIT — só nomes/ids/kinds (sem x,y)
  pontos_local.json        # LOCAL — XY da máquina (.gitignore)
  automation/
    app_ui.py              # tela (Iniciar / Mapear)
    mapa.py                # lê mapa_passos.json
    kinds.py               # o que precisa XY / auto / usuário
    localmap.py            # mapear e gravar pontos_local
    teclado.py             # teclas / hotkeys / colar
    runner.py              # executa uma parte
    win_mouse.py           # mouse Win32
  .scratch/                # norte + decisões (não é código)
  fixtures/exemplo_nfe.xml # XML de exemplo para o parser
  excel/                   # planilhas locais
```

Excel (doc): [excel-colunas.md](excel-colunas.md) — Batch **D**, Issuer Id **R**, Total Value **T**.

## Regras importantes

1. **Mapa no Git, XY só local** — nunca gravar coordenadas em `mapa_passos.json`.
2. **Passos diferentes do `sap_800`** — não copiar sequência de lá.
3. **Mapear só pede clique** — kinds `keys` / `hotkey` / `paste` / `user_action` não pedem coordenada.
4. **Gravar XY = botão do meio** (apertar a roda). Esc cancela. Captura via Win32 (`GetAsyncKeyState`).
5. **Antes de Iniciar e Mapear** — contagem de **3s** para focar o SAP.
6. **Mapear** — executa a parte em ordem (teclas/hotkeys/paste); só pausa nos `click` sem XY (ou remapear). Depois grava e clica para o fluxo seguir.
7. **Na execução** — teclas e paste rodam sem aviso; `user_action` pausa e pede o usuário.
8. Ao mudar algo estrutural (kinds, partes, contrato dos arquivos), **atualizar este scratch**.

## Kinds

| kind | Mapear? | Na execução |
|------|---------|-------------|
| `click` | Sim (roda do mouse) | Clique automático no XY local |
| `click_and_type` | Sim | Clique + limpar + colar |
| `keys` | Não | Teclas em sequência (`keys`, opcional `repeat`) |
| `hotkey` | Não | Atalho (`ctrl`+`f6`, etc.) |
| `paste` | Não | Cola o texto da tela (batch); Excel depois |
| `user_action` | Não | Mostra aviso e espera OK |

## Tempos no passo (opcional)

| Campo | O que faz | Padrão |
|-------|-----------|--------|
| `pausa` | Intervalo entre teclas/`repeat` do mesmo passo | `0.08` |
| `pausa_depois` | Espera depois do passo, antes do próximo | `0.35` |

Ex.: F3 duas vezes com 0.2s entre elas → `"keys": ["f3","f3"], "pausa": 0.2`.

## Partes atuais

Ver detalhes em [partes.md](partes.md) e o arquivo oficial `mapa_passos.json`.
