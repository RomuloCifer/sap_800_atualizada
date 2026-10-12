# Partes definidas (fonte humana)

Espelho do que está em `mapa_passos.json`. Se divergir, o JSON manda para o código; atualize os dois.

## Fluxo completo (`"fluxo"` no JSON)

Ordem atual do **Iniciar tudo**:

1. `abrir_batch`
2. `pegar_xml` → depois parse do clipboard (`recipient_filial`, invoice, serie, itens…)
3. `abrir_oj1b1n`
4. `preencher_oj1b1n`
5. `preencher_itens`
6. `preencher_taxes`
7. `preencher_nfe_data`

Para incluir uma parte nova no fim-a-fim: defina em `partes` **e** acrescente o nome em `fluxo`.

---

## ABRIR BATCH (`abrir_batch`)

1. Tecla **F3** duas vezes → `keys` + `pausa: 0.35` + `pausa_depois: 1.0`
2. **1 clique** antes do número batch → `click` + `pausa_depois: 1.0`
3. **Delete** 10x → `keys` + `repeat: 10`
4. **Colar** o batch → `paste` + `pausa_depois: 0.5` (texto da tela; depois Excel col. D)
5. **1 clique** no relógio → `click` + `pausa_depois: 1.0`
6. **1 clique** no lápis azul → `click` + `pausa_depois: 1.0`

Pontos a mapear: `clique_antes_batch`, `clique_relogio`, `clique_lapis_azul`.

---

## PEGAR XML (`pegar_xml`)

1. Tecla **F6** → `keys` (auto)
2. **Ctrl+F6** abrir XML → `hotkey` + `pausa_depois: 1.0`
3. **1 clique** na informação do XML → `click` + `pausa_depois: 0.5` (**mapear**)
4. **Ctrl+A** selecionar tudo → `hotkey` (auto)
5. **Ctrl+C** copiar → `hotkey` (auto)
6. Tecla **F3** voltar → `keys` (auto)

Ponto a mapear: `pegar_xml.clique_info_xml`.

---

## ABRIR OJ1B1N (`abrir_oj1b1n`)

Navegação por **Tab** (sem cliques nos campos da tela OJ1B1N):

1. **1 clique** em campo onde escrever → `click` (`abrir_oj1b1n.clique_campo_escrever`)
2. Escrever `/oj1b1n` → `type`
3. **Enter** → espera **1s**
4. Escrever `X0` → `type` (foco já no NF Type)
5. **Tab×2** → Business Place
6. Escrever **filial** → `text_from: recipient_filial` (ex.: `0015`)
7. **Tab** → escrever `V` (Partner Function)
8. **Tab** → Partner ID
9. Escrever **Issuer Id** → `text_from: issuer_id` (Excel col. R)
10. **Enter** → fim da parte

Ponto a mapear: só `clique_campo_escrever`.

---

## PREENCHER OJ1B1N (`preencher_oj1b1n`)

1. **1 clique** Nine-Digit No → `click`
2. Escrever **invoice 9 dígitos** → `text_from: invoice_9` (3319 → `000003319`)
3. **Tab** → série
4. Escrever **série 3 dígitos** → `text_from: serie_3` (XML `serie` 4 → `004`)
5. **Tab** → Issue Date
6. Escrever **issue_date** → `text_from: issue_date` (`DD.MM.YYYY`, ex.: `13.11.2025`)

Ponto a mapear: `preencher_oj1b1n.clique_nine_digit`.

---

## PREENCHER ITENS (`preencher_itens`)

### Mapear (calibração — `map_only`)

Clique no **meio** da célula NF Item nas linhas **1, 2, 5, 10, 20** + Plant no **final** da célula (linha 1).  
O código calcula a **média do dy** entre linhas e usa isso para todas as linhas do XML.

### Automação (por item do XML)

1. Clique NF Item (linha N) → escreve sempre **`1`**
2. Tab → Material (`cProd`)
3. Tab → Description (`xProd`)
4. Tab → Quantity (`qCom`)
5. Tab → Price (`vUnCom`)
6. Tab → CFOP SAP: 1º dígito `5→1`, `6→2` + `/AA` (ex.: `5906` → `1906/AA`)
7. Tab → `IC9` → Tab → `I49` → Tab → `C70` → Tab → `P70`
8. Clique Plant → `1502` (ou `1318` se recipient sufixo `0017-22`)
9. Próxima linha
10. Ao fim de todos os itens: **Enter** × (quantidade de produtos + 1)

Pontos: 5 âncoras NF Item + 1 Plant.

---

## PREENCHER TAXES (`preencher_taxes`)

### Mapear (sempre mapear Stat.TAX e Other Base 5/6 mesmo em notas 2025)

1. Selecionar item linhas **1, 2, 5, 10, 20** (dy)
2. Botão **Taxes**
3. **Tax Type** célula 1 + **Stat.TAX**
4. Value **início** `<` e **fim** `>` (drag + Ctrl+C)
5. Other Base **1–6**
6. **Taxes II** + **CBS and IBS**
7. **Taxes** (antes do E matemático — ponto separado)
8. **E matemático**

### Automação

1. Clica seleção nos **N** itens preenchidos
2. Clique Taxes
3. Se **issue date ≥ 01.01.2026**: Tax Type → `IB2S` → Stat.TAX → Enter×2 → `CBS1` → Stat.TAX → Enter×2 → depois `ICOF`/`ICM0`/`IPIS`/`IPI0` (sem novo clique Tax Type)
4. Se **2025-**: Tax Type → `ICOF` → Enter×2 → `ICM0` → … → `IPI0`
5. Drag Value → Ctrl+C → cola Other Base **de baixo pra cima** (2025: 4→1; 2026+: 6→1) → Enter×2
6. Taxes II → CBS and IBS (Excel col. **K** `CBS/IBS`; vazio = só clique)
7. Clique **Taxes** (ponto mapeado à parte) → clique **E matemático** → fim da parte

---

## PREENCHER NF-e DATA (`preencher_nfe_data`)

1. Clique **NF-e Data**
2. Clique **Protocol No.** → `protocol_number` (nProt)
3. Tab → **Proc Date** (`protocol_date`)
4. Tab → Backspace×8 → **Proc Time** (`protocol_time`)
5. Tab×3 → **Random No.** = 8 dígitos do fim da chave (`…140033194` → `14003319`)
6. Tab → Delete → último dígito da chave (`4`)

Pontos a mapear: `clique_nfe_data`, `clique_protocol_no`.
