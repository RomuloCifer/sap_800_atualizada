# Campos extraídos do XML NF-e

Exemplo: `fixtures/exemplo_nfe.xml`  
Parser: `automation/xml_nfe.py`

## Confirmados neste exemplo

| Campo pedido | Valor esperado | Origem XML |
|--------------|----------------|------------|
| invoice | `3319` | `ide/nNF` |
| recipient (completo) | `00.907.845/0015-60` | `dest/CNPJ` formatado |
| recipient (sufixo) | `0015-60` | últimos 6 dígitos do CNPJ |
| recipient (filial) | `0015` | 4 dígitos da filial (`BBBB` em `…/BBBB-CC`) — **Business Place** em OJ1B1N |
| Issue date | `13.11.2025` | `ide/dhEmi` |
| protocol number | `135253475578265` | `protNFe/nProt` |
| protocol date | `13.11.2025` | `dhRecbto` |
| protocol time | `14:09:16` | `dhRecbto` |
| protocol line | `135253475578265 13.11.2025 14:09:16` | montado |
| CFOP | `5906` | `det/prod/CFOP` (1º / comum) |
| valor | `1,730.36` (`1730.36`) | `total/ICMSTot/vNF` |
| chave | `352511…33194` | `chNFe` |

Também disponíveis (ainda não pedidos na lógica): série, emit CNPJ/nome, 3 itens (cProd, xProd, qCom, vUnCom).

## Faltando no XML

| Campo | Exemplo seu | Situação |
|-------|-------------|----------|
| **Issuer Sap** | `513088` | **Não existe** neste XML. Vem do Excel: coluna **R** `Issuer Id` (ver [excel-colunas.md](excel-colunas.md)). |

## Uso futuro

Depois do `pegar_xml` (Ctrl+C), chamar `parse_nfe_clipboard()` e seguir a lógica que você definir nos próximos passos.  
Comparar `valor` do XML com Excel coluna **T** `Total Value`. Batch na coluna **D** `Batch`.
