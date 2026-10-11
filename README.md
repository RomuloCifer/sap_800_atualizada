# SAP 800 ATT

Automação por partes, com mapa de passos versionado e coordenadas **locais** por máquina.

## Como abrir

Dois cliques em `iniciar.bat`  
(na primeira vez cria a `.venv` e instala as dependências).

Na tela:

- **Iniciar automação** — roda a parte selecionada
- **Mapear** — pede clique do meio (roda) em cada passo ainda sem XY nesta máquina

## Arquivos importantes

| Arquivo | Vai pro Git? | Função |
|---------|--------------|--------|
| `mapa_passos.json` | Sim | Nomes / ids / ordem dos passos (**sem** x,y) |
| `pontos_local.json` | **Não** | Coordenadas desta máquina |

## Como adicionar um passo

Edite `mapa_passos.json`, dentro da parte, por exemplo:

```json
{
  "id": "abrir_batch.campo_batch",
  "ordem": 1,
  "kind": "click_and_type",
  "nome": "campo batch",
  "obs": "clicar e digitar o batch"
}
```

Kinds suportados agora: `click`, `click_and_type`.

Depois: abra o app → selecione a parte → **Mapear**.

## Observação

Não compartilhe `pontos_local.json` entre PCs (cada máquina mapeia a sua).
