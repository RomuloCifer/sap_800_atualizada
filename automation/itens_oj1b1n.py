"""
Preenchimento das linhas de item no OJ1B1N.

Âncoras mapeadas (linhas 1/2/5/10/20 + Plant) → dy médio por linha.
Cada item do XML: clique NF Item → tabs → clique Plant.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from automation import abort
from automation import teclado
from automation import win_mouse

# Ids em mapa_passos.json (kind=map_only)
ANCORAS_NF_ITEM = (
    ("preencher_itens.ancor_linha_1", 1),
    ("preencher_itens.ancor_linha_2", 2),
    ("preencher_itens.ancor_linha_5", 5),
    ("preencher_itens.ancor_linha_10", 10),
    ("preencher_itens.ancor_linha_20", 20),
)
ID_PLANT = "preencher_itens.ancor_plant"

# Grade SAP: 1ª página linhas 1–25; depois do scroll a linha 1 fica com o último item
# e os novos vão da linha 2 até 25 (24 itens por página).
ITENS_PRIMEIRA_PAGINA = 25
ITENS_PAGINA_SEGUINTE = 24
LINHA_INICIO_APOS_SCROLL = 2

PLANT_PADRAO = "1502"
PLANT_POR_SUFIXO = {
    "0017-22": "1318",
}

CODIGOS_FIXOS = ("IC9", "I49", "C70", "P70")

# Campo descrição do item no OJ1B1N costuma ter 40 caracteres (SAP corta o resto).
DESC_MAX_CHARS = 40


def truncar_descricao(texto, max_chars=DESC_MAX_CHARS):
    # type: (str, int) -> str
    """
    Evita estourar o campo (40) e vazar digitação para o CFOP.
    Prioriza o xProd (antes de " / "); se sobrar espaço, inclui o sufixo cortado.
    Ex.: "... TE / 29-0337353-00000" → "... TE / 29-033735"
    """
    t = (texto or "").strip()
    lim = int(max_chars)
    if len(t) <= lim:
        return t
    sep = " / "
    if sep in t:
        base, extra = t.rsplit(sep, 1)
        base = base.strip()
        extra = extra.strip()
        # xProd já estoura sozinho: só ele, cortado
        if len(base) >= lim:
            return base[:lim]
        room = lim - len(base) - len(sep)
        if room <= 0:
            return base[:lim]
        out = "{}{}{}".format(base, sep, extra[:room])
        return out[:lim]
    return t[:lim]


def cfop_para_sap(cfop):
    # type: (str) -> str
    """5906 → 1906/AA; 6905 → 2905/AA."""
    c = "".join(ch for ch in str(cfop or "") if ch.isdigit())
    if not c:
        return ""
    if c[0] == "5":
        c = "1" + c[1:]
    elif c[0] == "6":
        c = "2" + c[1:]
    return "{}/AA".format(c)


def plant_para_recipient(sufixo):
    # type: (str) -> str
    """Default 1502; sufixo 0017-22 → 1318."""
    s = (sufixo or "").strip().replace(" ", "")
    if s in PLANT_POR_SUFIXO:
        return PLANT_POR_SUFIXO[s]
    # aceita CNPJ formatado terminando em 0017-22
    if s.endswith("0017-22") or s.endswith("/0017-22"):
        return "1318"
    return PLANT_PADRAO


def formatar_quantidade(valor):
    # type: (float) -> str
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return str(valor or "")
    texto = "{:.4f}".format(v).rstrip("0").rstrip(".")
    return texto if texto else "0"


def formatar_preco(valor):
    # type: (float) -> str
    """
    Preço unitário no OJ1B1N: no máximo 6 casas decimais
    (ex.: 11.611895). Mais que isso o SAP rejeita.
    """
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return str(valor or "")
    texto = "{:.6f}".format(v).rstrip("0").rstrip(".")
    return texto if texto else "0"


def _xy(pontos, pid):
    # type: (Dict[str, dict], str) -> Tuple[int, int]
    item = pontos.get(pid) or {}
    if "x" not in item or "y" not in item:
        raise KeyError("Sem coordenada para '{}'.".format(pid))
    return int(item["x"]), int(item["y"])


def calcular_dy(pontos, ancoras=None):
    # type: (Dict[str, dict], Optional[Sequence[Tuple[str, int]]]) -> float
    """Média do deslocamento Y por linha entre as âncoras mapeadas."""
    pares = list(ancoras or ANCORAS_NF_ITEM)
    ys = []  # type: List[Tuple[int, int]]
    for pid, row in pares:
        _x, y = _xy(pontos, pid)
        ys.append((int(row), y))
    ys.sort(key=lambda t: t[0])
    if len(ys) < 2:
        raise RuntimeError("Precisa de ao menos 2 âncoras de linha para calcular o espaçamento.")
    deltas = []
    for i in range(1, len(ys)):
        r0, y0 = ys[i - 1]
        r1, y1 = ys[i]
        if r1 == r0:
            continue
        deltas.append(float(y1 - y0) / float(r1 - r0))
    if not deltas:
        raise RuntimeError("Não foi possível calcular dy entre âncoras de linha.")
    return sum(deltas) / float(len(deltas))


def xy_nf_item(pontos, linha_1based, dy=None):
    # type: (Dict[str, dict], int, Optional[float]) -> Tuple[int, int]
    x0, y0 = _xy(pontos, ANCORAS_NF_ITEM[0][0])
    step = dy if dy is not None else calcular_dy(pontos)
    y = int(round(y0 + (int(linha_1based) - 1) * step))
    return x0, y


def xy_plant(pontos, linha_1based, dy=None):
    # type: (Dict[str, dict], int, Optional[float]) -> Tuple[int, int]
    """Plant mapeado na linha 1; demais linhas usam o mesmo dy."""
    x0, y0 = _xy(pontos, ID_PLANT)
    step = dy if dy is not None else calcular_dy(pontos)
    y = int(round(y0 + (int(linha_1based) - 1) * step))
    return x0, y


def _tab():
    # type: () -> None
    teclado.pressionar("tab", vezes=1, pausa=0.05, hold=0.04)
    time.sleep(0.12)


def _digitar_campo(valor):
    # type: (str) -> None
    teclado.digitar_texto(str(valor))
    time.sleep(0.08)


def _itens_do_contexto(contexto):
    # type: (Optional[Dict[str, Any]]) -> List[Any]
    ctx = contexto or {}
    itens = ctx.get("itens")
    if itens:
        return list(itens)
    nfe = ctx.get("_nfe")
    if nfe is not None and getattr(nfe, "itens", None):
        return list(nfe.itens)
    return []


def rolar_grade_itens_para_baixo(pontos=None):
    # type: (Optional[Dict[str, dict]]) -> None
    """
    Pausa e pede para a pessoa descer a grade no SAP.
    Evita drag automático da barra (travava em notas grandes).
    """
    from automation.verificacao import VerificacaoCancelada, dialogo_verificacao

    abort.check()
    msg = (
        "Desça a grade de itens no SAP (barra de rolagem) até aparecerem as próximas linhas.\n"
        "A linha 1 deve ficar com o último item já preenchido; as novas vão da linha 2 em diante.\n\n"
        "Quando estiver pronta, clique em OK para continuar."
    )
    ok, motivo = dialogo_verificacao(None, "Rolar grade de itens", msg)
    if not ok:
        raise VerificacaoCancelada(motivo or "parado", passo_id="preencher_itens")
    abort.sleep(0.2)


def _dados_item(item):
    # type: (Any) -> Tuple[str, str, Any, Any, str]
    if hasattr(item, "codigo"):
        return (
            item.codigo,
            item.descricao,
            item.quantidade,
            item.preco_unitario,
            item.cfop,
        )
    return (
        item.get("codigo") or item.get("material") or "",
        item.get("descricao") or "",
        item.get("quantidade"),
        item.get("preco_unitario") or item.get("preco"),
        item.get("cfop") or "",
    )


def _preencher_linha(pontos, dy, plant, linha, item, pausa_linha):
    # type: (Dict[str, dict], float, str, int, Any, float) -> None
    material, descricao, qtd, preco, cfop = _dados_item(item)
    x, y = xy_nf_item(pontos, linha, dy=dy)
    win_mouse.click(x, y)
    time.sleep(0.15)

    # Ordem: NF → Material → Qtd → Preço → Desc → CFOP → impostos → Plant
    _digitar_campo("1")
    _tab()
    _digitar_campo(material)
    _tab()
    _digitar_campo(formatar_quantidade(qtd))
    _tab()
    _digitar_campo(formatar_preco(preco))
    _tab()
    _digitar_campo(truncar_descricao(descricao))
    _tab()
    _digitar_campo(cfop_para_sap(cfop))
    for codigo in CODIGOS_FIXOS:
        _tab()
        _digitar_campo(codigo)

    px, py = xy_plant(pontos, linha, dy=dy)
    win_mouse.click(px, py)
    time.sleep(0.15)
    _digitar_campo(plant)
    abort.sleep(pausa_linha)


def _enter_apos_pagina(n_itens_pagina):
    # type: (int) -> None
    """Enter × (itens da página + 1), como no fluxo atual."""
    n_enter = int(n_itens_pagina) + 1
    teclado.pressionar("enter", vezes=n_enter, pausa=0.6, hold=0.05)
    abort.sleep(0.25)


def executar_preenchimento(contexto, pontos, passo=None):
    # type: (Optional[Dict[str, Any]], Dict[str, dict], Optional[dict]) -> int
    """
    Preenche itens do XML em páginas:
      - 1ª: linhas 1–25
      - Enter × (25+1) → diálogo (pessoa desce a grade) → linhas 2–25 (24 itens)
      - repete até acabar
    Retorna quantidade de linhas preenchidas.
    """
    ctx = contexto or {}
    itens = _itens_do_contexto(ctx)
    if not itens:
        raise RuntimeError(
            "Sem itens no contexto. Rode pegar_xml antes (ou informe itens)."
        )

    dy = calcular_dy(pontos)
    plant = plant_para_recipient(str(ctx.get("recipient_sufixo") or ""))
    pausa_linha = 0.35
    if passo and passo.get("pausa_depois") is not None:
        pausa_linha = float(passo["pausa_depois"])

    idx = 0
    pagina = 0
    total = len(itens)
    while idx < total:
        abort.check()
        if pagina == 0:
            linha_ini = 1
            capacidade = ITENS_PRIMEIRA_PAGINA
        else:
            rolar_grade_itens_para_baixo(pontos)
            linha_ini = LINHA_INICIO_APOS_SCROLL
            capacidade = ITENS_PAGINA_SEGUINTE

        chunk = itens[idx : idx + capacidade]
        for j, item in enumerate(chunk):
            abort.check()
            linha = linha_ini + j
            _preencher_linha(pontos, dy, plant, linha, item, pausa_linha)

        _enter_apos_pagina(len(chunk))
        idx += len(chunk)
        pagina += 1

    return total
