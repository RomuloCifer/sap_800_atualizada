# Ideia — novo projeto (do zero)

Copie esta pasta `.scratch/ideia-novo-projeto` para o repositório/pasta nova.  
Isto **não** é implementação. É só o norte.

Referência de fluxo (o que já existia e funcionava, porém lento): projeto `sap_800` na Área de Trabalho.  
**Não copiar** o motor de coordenadas desse projeto.

---

## Problema que queremos evitar

No `sap_800`, o `mapa_passos.json` misturava **nomes dos passos** com **XY do PC de quem criou** (até coordenada negativa / 2 monitores).  
Em outra máquina quebrava ou exigia remapear tudo. Além disso: muitos `sleep`, OCR e cliques → lento.

---

## Ideia central

1. **Excel** com linhas a processar (`Status` = pendente, etc. — colunas detalhamos depois).
2. Automação pega **um batch por vez**, atualiza status conforme anda (erro → marca e vai ao próximo).
3. Existe um **mapa de passos só com nomes** (checklist / roteiro), sem posição de mouse no arquivo compartilhado.
4. Fluxo típico de um item:
   - voltar 2x → limpar/preencher batch atual  
   - obter **XML dentro do SAP**  
   - ler o ano no XML → ramo **2025** ou **2026** (roteiros diferentes)  
   - script/roteiro vai até certo ponto  
   - automação completa com dados do XML (+ checagens, ex. valor do Excel vs valor final)  
   - salvar → próximo pendente  

---

## Mapa de passos (o que queremos)

Arquivo versionado, algo como:

```text
# só nomes / intenção — sem x,y
parte1:
  - voltar
  - voltar
  - preencher_batch          # valor vem do Excel
  - abrir_fluxo / lapis
parte2:
  - ...
ramo_2025:
  - ...
ramo_2026:
  - ...
pos_xml:
  - preencher_chave_protocolo_etc
  - validar_valor
  - salvar
```

- Serve para a pessoa **acompanhar e marcar** o que já foi definido.
- A implementação de cada nome (Scripting SAP, etc.) vem depois.
- **Não** gravar XY absoluto no mapa compartilhado.

---

## Decisões já combinadas

| Tema | Decisão |
|------|---------|
| Erro no meio | Marca erro na linha e segue o próximo |
| XML | Pegado pela automação **dentro do SAP** |
| 2025 vs 2026 | Ano vem do **XML** (em princípio) |
| Colunas Excel / textos de Status | Definir depois |
| Projeto | Começar **do zero** (ideia limpa) |

---

## Fora de escopo desta ideia (por enquanto)

- Detalhar todas as colunas do Excel  
- Implementar código  
- Copiar `pontos_local` / XY do `sap_800`  
- Discutir infraestrutura de máquina remota neste documento  

---

## Próximo quando for construir

1. Criar pasta/repo novo.  
2. Colar este scratch.  
3. Escrever o primeiro mapa **só com nomes** (mesmo incompleto).  
4. Só então escolher como cada passo roda (ex.: SAP GUI Scripting nos cliques estáveis).
