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
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return str(valor or "")
    texto = "{:.10f}".format(v).rstrip("0").rstrip(".")
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


def executar_preenchimento(contexto, pontos, passo=None):
    # type: (Optional[Dict[str, Any]], Dict[str, dict], Optional[dict]) -> int
    """
    Preenche uma linha por item do XML.
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

    for idx, item in enumerate(itens):
        abort.check()
        linha = idx + 1  # grade SAP começa na 1ª linha visível
        if hasattr(item, "codigo"):
            material = item.codigo
            descricao = item.descricao
            qtd = item.quantidade
            preco = item.preco_unitario
            cfop = item.cfop
        else:
            material = item.get("codigo") or item.get("material") or ""
            descricao = item.get("descricao") or ""
            qtd = item.get("quantidade")
            preco = item.get("preco_unitario") or item.get("preco")
            cfop = item.get("cfop") or ""

        x, y = xy_nf_item(pontos, linha, dy=dy)
        win_mouse.click(x, y)
        time.sleep(0.15)

        # Ordem nesta máquina: NF → Material → Qtd → Preço → Desc → CFOP → impostos → Plant
        _digitar_campo("1")
        _tab()
        _digitar_campo(material)
        _tab()
        _digitar_campo(formatar_quantidade(qtd))
        _tab()
        _digitar_campo(formatar_preco(preco))
        _tab()
        # SAP: descrição do item ~40 chars; truncar para não vazar no CFOP
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

    # Após todos os itens: Enter (qtd produtos + 1), 0.6s entre cada
    n_enter = len(itens) + 1
    teclado.pressionar("enter", vezes=n_enter, pausa=0.6, hold=0.05)
    abort.sleep(0.25)

    return len(itens)
