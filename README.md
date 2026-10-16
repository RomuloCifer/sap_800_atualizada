# SAP 800 ATT

Automação do SAP em **partes** (abrir batch → XML → OJ1B1N → itens → taxes → NF-e data).  
O roteiro fica em `mapa_passos.json`; as coordenadas do mouse ficam **só na sua máquina** (`pontos_local.json`).

---

## Começar (primeira vez)

1. Coloque a planilha `.xlsx` na pasta `excel/`.
2. Dê dois cliques em **`iniciar.bat`**  
   (cria a `.venv` e abre a tela).
3. No SAP, deixe a tela pronta.
4. **Mapeie as partes na ordem abaixo** (tela → escolha a parte → **Mapear**; botão do **meio** do mouse grava).
5. Marque **Usar Excel** → **Iniciar tudo**.

### Ordem de mapear (mesma ordem das etapas)

Deixe o SAP na tela certa de cada parte antes de mapear. O Mapear só pede **cliques**; teclas/tabs são automáticos.

| # | Parte | O que mapear (botão do meio) |
|---|--------|------------------------------|
| 1 | `abrir_batch` | Antes do número batch → relógio → lápis azul |
| 2 | `pegar_xml` | Clique na área do XML (foco antes do Ctrl+A) |
| 3 | `abrir_oj1b1n` | Campo onde escrever o tcode (`/oj1b1n`) |
| 4 | `preencher_oj1b1n` | Célula **Nine-Digit No** |
| 5 | `preencher_itens` | NF Item **meio** das linhas **1, 2, 5, 10, 20** + **Plant** (final da célula, linha 1) |
| 6 | `preencher_taxes` | … → Other Base → Taxes II + CBS **só se** CBS/IBS no Excel → Taxes → **E matemático** |
| 7 | `preencher_nfe_data` | Valor **início** `<<` e **fim** `>>` → clique **NF-e Data** → clique **Protocol No.** |
| 8 | `salvar_e_fechar` | **Só sucesso:** Salvar → 3,5s → Alt+F4 → balança → X |

No `preencher_taxes`, mapeie Stat.TAX e Other Base 5/6 **mesmo em notas 2025** (usam em 2026+).

**Dicas**

- Feche o Excel na planilha enquanto a automação grava o Status (`A-enviado` / `A-erro` / motivo do Parar). A gravação é atômica (arquivo temp → troca): Ctrl+C no meio do save não deve corromper o `.xlsx`.
- **Esc** para a automação a qualquer momento (mesmo com o SAP em foco).
- Em pontos estratégicos aparece uma caixa **OK — continuar** / **Parar** (depois dos itens, Taxes e NF-e Data). Em **Parar**, digite o motivo — ele vai na coluna Status e a automação (e a fila) encerra.
- Se faltar um clique mapeado no meio do fluxo, a automação **pausa e pede o botão do meio** na hora (grava e segue). Não precisa mapear `salvar_e_fechar` antes.
- Se o **Ctrl+C do XML** falhar: diálogo **Tentar novamente** (recomeça em `pegar_xml`, sem abrir batch) ou **Sair** (não grava Status; fica `Pendente`).

---

## Tela (mais fácil)

| Botão | O que faz |
|-------|-----------|
| **Iniciar tudo** | Roda o fluxo completo |
| **Iniciar parte** | Roda só a parte selecionada |
| **Mapear** | Pede os cliques da parte (botão do meio) |

| Opção | O que faz |
|-------|-----------|
| **Usar Excel** | Lê a 1ª linha com Status = `Pendente` (Batch + Issuer Id + CBS/IBS…) |
| **Fila: um atrás do outro** | Depois de cada nota: salva/fecha no fluxo → grava Status → próximo Pendente |
| **Remapear tudo** | No Mapear, ignora pontos já gravados daquela parte |

Sem a fila marcada: processa **1 Pendente por vez** (você acompanha e decide).

Atalhos rápidos:

- `iniciar.bat` → abre a tela  
- `rodar-fluxo.bat` → fluxo com Excel no terminal  
- `rodar-fluxo.bat BATCH ISSUER` → fluxo manual  

---

## Terminal (erros e traceback bem visíveis)

Na pasta do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py listar
```

### Comandos (`python main.py …`)

| Comando | Para quê |
|---------|----------|
| `listar` | Mostra partes, ordem do fluxo e o que ainda falta mapear |
| `excel` | Mostra a próxima linha `Pendente` (batch, issuer, CBS/IBS…) |
| `fluxo` | Roda o fluxo completo |
| `parte NOME` | Roda só uma parte (ex.: `abrir_batch`) |
| `mapear NOME` | Mapeia os cliques de uma parte |

### Opções (`--`) mais usadas

| Opção | Onde vale | O que faz |
|-------|-----------|-----------|
| `--excel` | `fluxo`, `parte`, `mapear` | Usa a 1ª linha **Pendente** da pasta `excel/` |
| `--excel-path CAMINHO` | idem + `excel` | Aponta um `.xlsx` específico (também lê Pendente) |
| `--fila` | só `fluxo` | Com `--excel`: processa **todos** os Pendente em sequência |
| `--batch X` | `fluxo`, `parte`, `mapear` | Batch manual (sobrescreve o Excel) |
| `--issuer Y` | idem | Issuer Id manual (sobrescreve o Excel) |
| `--delay N` | idem | Segundos para focar o SAP antes de começar (padrão: 3) |
| `--remapear-tudo` | só `mapear` | Refaz todos os cliques da parte, mesmo já gravados |

### Exemplos práticos

```powershell
# Ver o que falta mapear
python main.py listar

# Ver a próxima Pendente
python main.py excel

# 1 nota do Excel (padrão — você acompanha + caixas de OK)
python main.py fluxo --excel

# Várias Pendente em fila (OK entre etapas; Status A-enviado / A-erro)
python main.py fluxo --excel --fila

# Sem Excel: batch e issuer na mão
python main.py fluxo --batch 1355271 --issuer 513088

# Só uma parte
python main.py parte abrir_batch --excel
python main.py parte preencher_taxes --excel

# Mapear (ex.: salvar / balança / X)
python main.py mapear salvar_e_fechar
python main.py mapear preencher_itens --remapear-tudo
```

---

## Excel em resumo

1. Status exatamente **`Pendente`** → entra na fila.  
2. Fluxo ok (valor conferido + todos os OK humanos) → Status **`A-enviado`**.  
3. Erro técnico / valor divergente → **`A-erro`**.  
4. **Parar** numa verificação → Status = **texto que você digitar** (e a fila para).  
5. **Esc** no meio → deixa **Pendente**.

Colunas principais (pelo **nome** do cabeçalho): `Status`, `Batch`, `Issuer Id`, `CBS/IBS`, `Total Value`.  
Detalhes: `.scratch/excel-colunas.md`.

---

## Partes do fluxo

Ordem em `mapa_passos.json` → chave `"fluxo"`:

1. `abrir_batch` — F3, limpa/digita batch, relógio, lápis  
2. `pegar_xml` — abre XML, Ctrl+A/C, parse  
3. `abrir_oj1b1n` — tcode + X0 + filial + V + Partner ID  
4. `preencher_oj1b1n` — Nine-Digit, série, issue date  
5. `preencher_itens` — NF→Material→Qtd→Preço→Desc→CFOP→impostos→Plant + Enter×(n+1) + **verificação humana**  
6. `preencher_taxes` — taxes / Other Base + **verificação** + Taxes II/CBS **só se** houver CBS/IBS no Excel → E matemático  
7. `preencher_nfe_data` — confere valor (±2¢) + protocolo / random + **verificação**
8. `salvar_e_fechar` — Salvar → Alt+F4 → balança → X (só no sucesso; em erro: Alt+F4 + X)
Roteiro humano: `.scratch/partes.md`.

---

## Arquivos importantes

| Arquivo | Git? | Função |
|---------|------|--------|
| `mapa_passos.json` | Sim | Passos / ids (sem x,y) |
| `pontos_local.json` | **Não** | Coordenadas desta máquina |
| `excel/*.xlsx` | Não | Planilha da fila |
| `.scratch/` | Sim | Notas e decisões |

**Não compartilhe** `pontos_local.json` entre PCs — cada máquina mapeia a sua.
