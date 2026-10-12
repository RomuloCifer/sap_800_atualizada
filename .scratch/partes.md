# Partes definidas (fonte humana)

Espelho do que está em `mapa_passos.json`. Se divergir, o JSON manda para o código; atualize os dois.

## Fluxo completo (`"fluxo"` no JSON)

Ordem atual do **Iniciar tudo**:

1. `abrir_batch`
2. `pegar_xml` → depois parse do clipboard (`recipient_filial`, invoice, serie, valor…)
3. `abrir_oj1b1n`
4. `preencher_oj1b1n`

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
