# Excel — colunas relevantes (só documentação)

Planilha de trabalho fica em `excel/` (não versionar).  
Lógica de leitura **ainda não implementada**.

## Colunas atuais (NEW ERA / notas não escrituradas)

| Uso na automação | Nome da coluna | Letra atual | Observação |
|------------------|----------------|-------------|------------|
| Batch | `Batch` | **D** | Identifica o lançamento; hoje também pode vir do campo da tela |
| Issuer Sap | `Issuer Id` | **R** | Ex.: `513088` — **não vem do XML** |
| Valor (comparar com XML) | `Total Value` | **T** | Comparar com `vNF` do XML (`1,730.36`) |

Letras podem mudar se a planilha ganhar/remover colunas — preferir casar pelo **nome** do cabeçalho quando for implementar.

## Relação com o XML

| Dado | Excel | XML |
|------|-------|-----|
| Batch | coluna D `Batch` | — |
| Issuer Sap | coluna R `Issuer Id` | — (ausente no NF-e) |
| Valor | coluna T `Total Value` | `total/ICMSTot/vNF` |

Ver também: [xml-campos.md](xml-campos.md).
