# Partes definidas (fonte humana)

Espelho do que está em `mapa_passos.json`. Se divergir, o JSON manda para o código; atualize os dois.

---

## ABRIR BATCH (`abrir_batch`)

1. Tecla **F3** duas vezes → `keys` + `pausa: 0.35` + `pausa_depois: 1.0`
2. **1 clique** antes do número batch → `click` + `pausa_depois: 1.0`
3. **Delete** 10x → `keys` + `repeat: 10`
4. **Colar** o batch → `paste` + `pausa_depois: 0.5` (texto da tela; depois Excel)
5. **1 clique** no relógio → `click` + `pausa_depois: 1.0`
6. **1 clique** no lápis azul → `click` + `pausa_depois: 1.0`

Pontos a mapear nesta máquina: `clique_antes_batch`, `clique_relogio`, `clique_lapis_azul`.

---

## PEGAR XML (`pegar_xml`)

1. Tecla **F6** → `keys` (auto)
2. **Ctrl+F6** abrir XML → `hotkey` + `pausa_depois: 1.0`
3. **1 clique** na informação do XML → `click` + `pausa_depois: 0.5` (**mapear**)
4. **Ctrl+A** selecionar tudo → `hotkey` (auto)
5. **Ctrl+C** copiar → `hotkey` (auto)
6. Tecla **F3** voltar → `keys` (auto)

Ponto a mapear: `pegar_xml.clique_info_xml`.
