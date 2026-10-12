# Partes definidas (fonte humana)

Espelho do que está em `mapa_passos.json`. Se divergir, o JSON manda para o código; atualize os dois.

## Fluxo completo (`"fluxo"` no JSON)

Ordem atual do **Iniciar tudo**:

1. `abrir_batch`
2. `pegar_xml` → depois parse do clipboard (`recipient_filial`, invoice, valor…)
3. `abrir_oj1b1n`

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

1. **1 clique** em campo onde escrever → `click` (`abrir_oj1b1n.clique_campo_escrever`)
2. Escrever `/oj1b1n` → `type` + `text: /oj1b1n`
3. **Enter** → `keys`
4. **1 clique** Nota Fiscal Type → `click`
5. Escrever `X0` → `type` + `text: X0`
6. **1 clique** Business Place → `click`
7. Escrever **filial do recipient** → `type` + `text_from: recipient_filial`  
   Ex.: CNPJ `00.907.845/0015-60` → escreve **`0015`** (4 dígitos da filial; pode ser 0001, 0016, etc.)
8. **1 clique** NF Partner Function → `click`
9. Tecla **V** → `keys`
10. **Enter** → `keys`
11. **1 clique** Partner ID → `click`
12. Escrever **Issuer Id** → `type` + `text_from: issuer_id` (Excel col. R; lógica ainda não ligada)
13. **Enter** → `keys`

Pontos a mapear: campo onde escrever, NF Type, Business Place, Partner Function, Partner ID.

No **Mapear**, se `recipient_filial` / `issuer_id` ainda não estiverem no contexto, a tela pergunta o valor na hora.
