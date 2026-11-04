# Excel — colunas relevantes

Planilha em `excel/` (não versionar).  
Módulo: `automation/excel_fila.py`

## Colunas (por nome do cabeçalho)

| Uso | Nome da coluna | Letra atual |
|-----|----------------|-------------|
| Filtro da fila | `Status` | **A** |
| Colaborador | `OBS` | **I** |
| Batch | `Batch` | **D** |
| Issuer Sap / Partner ID | `Issuer Id` | **R** |
| CBS and IBS (Taxes) | `CBS/IBS` | **K** |
| Valor (comparar com XML) | `Total Value` | **T** |

## Regra da fila (branch `geisie`)

- Pega a **primeira** linha com `Status` = **`Pendente relançar`** **e** `OBS` = **`geisie`** (case-insensitive).
- Não pega só `Pendente` nem outros textos com “pendente”.
- Padrão: **1 linha por vez** (`fluxo --excel`).
- Fila (`--fila`): sucesso → **`A-enviado`**; erro → **`A-erro`**. Feche o Excel ao gravar Status.

## Como rodar

```powershell
python main.py excel
python main.py fluxo --excel
```

Ou `rodar-fluxo.bat` sem argumentos.

Na tela: marcar **Usar Excel (1a linha Status = Pendente)** (já vem marcado).

## Relação com o XML

| Dado | Excel | XML |
|------|-------|-----|
| Batch | `Batch` | — |
| Issuer Sap | `Issuer Id` | — |
| Valor | `Total Value` | `vNF` |
| Business Place | — | filial do recipient (`0015`) |
