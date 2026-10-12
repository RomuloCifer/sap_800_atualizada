# Excel — colunas relevantes

Planilha em `excel/` (não versionar).  
Módulo: `automation/excel_fila.py`

## Colunas (por nome do cabeçalho)

| Uso | Nome da coluna | Letra atual |
|-----|----------------|-------------|
| Filtro da fila | `Status` | **A** |
| Batch | `Batch` | **D** |
| Issuer Sap / Partner ID | `Issuer Id` | **R** |
| CBS and IBS (Taxes) | `CBS/IBS` | **K** |
| Valor (comparar com XML) | `Total Value` | **T** |

## Regra da fila

- Pega a **primeira** linha cujo `Status` (trim, case-insensitive) é exatamente **`Pendente`**.
- Não pega textos tipo `Enviados setembro - pendente revisão`.

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
