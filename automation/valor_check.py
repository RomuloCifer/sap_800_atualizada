"""
Conferência do valor na tela (drag + Ctrl+C) vs XML e Excel.
Tolerância padrão: 2 centavos.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Optional, Tuple

from automation import abort
from automation import teclado
from automation import win_mouse
from automation.itens_oj1b1n import ITENS_PRIMEIRA_PAGINA, _xy

ID_VALOR_INI = "preencher_nfe_data.valor_ini"
ID_VALOR_FIM = "preencher_nfe_data.valor_fim"

TOL_PADRAO = 0.02
# Mesma guarda das notas grandes em Taxes (Value ainda não apareceu).
ESPERA_VALOR_NOTA_GRANDE_S = 5.0


def parse_valor_flex(texto):
    # type: (str) -> Optional[float]
    """Aceita 1,730.36 / 1.730,36 / 1730.36 / R$ 1.730,36."""
    t = (texto or "").strip()
    if not t:
        return None
    t = t.replace("R$", "").replace("r$", "").strip()
    t = t.replace("\xa0", " ").replace(" ", "")
    # mantém dígitos, ponto, vírgula, sinal
    t = re.sub(r"[^\d,.\-]", "", t)
    if not t or t in (".", ",", "-", "-.", "-,"):
        return None
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _quase_igual(a, b, tol):
    # type: (float, float, float) -> bool
    return abs(float(a) - float(b)) <= float(tol) + 1e-9


def _n_itens(ctx):
    # type: (Dict[str, Any]) -> int
    itens = ctx.get("itens")
    if itens:
        return len(list(itens))
    nfe = ctx.get("_nfe")
    if nfe is not None and getattr(nfe, "itens", None):
        return len(list(nfe.itens))
    n = ctx.get("n_itens")
    if n is not None:
        return int(n)
    return 0


def _copiar_valor_tela(pontos, n_itens=0):
    # type: (Dict[str, dict], int) -> Tuple[str, float]
    import pyperclip

    if int(n_itens) >= ITENS_PRIMEIRA_PAGINA:
        abort.check()
        abort.sleep(ESPERA_VALOR_NOTA_GRANDE_S)

    x1, y1 = _xy(pontos, ID_VALOR_INI)
    x2, y2 = _xy(pontos, ID_VALOR_FIM)
    win_mouse.drag(x1, y1, x2, y2)
    abort.sleep(0.12)
    teclado.hotkey(["ctrl", "c"], pausa=0.1)
    abort.sleep(0.15)
    bruto = (pyperclip.paste() or "").strip()
    valor = parse_valor_flex(bruto)
    if valor is None:
        raise RuntimeError(
            "Nao consegui ler o valor da tela (clipboard={!r}). "
            "Remapeie valor_ini / valor_fim.".format(bruto)
        )
    return bruto, float(valor)


def _excel_valor(ctx):
    # type: (Dict[str, Any]) -> Optional[float]
    for key in ("excel_total_value", "total_value"):
        if key in ctx and ctx[key] is not None and str(ctx[key]).strip() != "":
            return parse_valor_flex(str(ctx[key]))
    return None


def _xml_valor(ctx):
    # type: (Dict[str, Any]) -> Optional[float]
    if ctx.get("valor") is not None and str(ctx.get("valor")).strip() != "":
        try:
            return float(ctx["valor"])
        except (TypeError, ValueError):
            return parse_valor_flex(str(ctx["valor"]))
    nfe = ctx.get("_nfe")
    if nfe is not None and getattr(nfe, "valor", None) is not None:
        return float(nfe.valor)
    return None


def verificar_valor(contexto, pontos, passo=None):
    # type: (Optional[Dict[str, Any]], Dict[str, dict], Optional[dict]) -> Dict[str, Any]
    """
    Drag no valor da tela, compara com XML e Excel (tol 0.02).
    Levanta RuntimeError se divergir.
    """
    ctx = contexto or {}
    tol = TOL_PADRAO
    if passo and passo.get("tol") is not None:
        tol = float(passo["tol"])

    abort.check()
    bruto, tela = _copiar_valor_tela(pontos, n_itens=_n_itens(ctx))
    xml_v = _xml_valor(ctx)
    excel_v = _excel_valor(ctx)

    if xml_v is None:
        raise RuntimeError(
            "Sem valor do XML no contexto. Rode pegar_xml antes da conferencia."
        )

    erros = []
    if not _quase_igual(tela, xml_v, tol):
        erros.append(
            "tela={:.2f} vs XML={:.2f} (diff={:.2f})".format(
                tela, xml_v, abs(tela - xml_v)
            )
        )
    if excel_v is not None and not _quase_igual(tela, excel_v, tol):
        erros.append(
            "tela={:.2f} vs Excel={:.2f} (diff={:.2f})".format(
                tela, excel_v, abs(tela - excel_v)
            )
        )
    if excel_v is not None and not _quase_igual(xml_v, excel_v, tol):
        erros.append(
            "XML={:.2f} vs Excel={:.2f} (diff={:.2f})".format(
                xml_v, excel_v, abs(xml_v - excel_v)
            )
        )

    resultado = {
        "valor_tela_bruto": bruto,
        "valor_tela": tela,
        "valor_xml": xml_v,
        "valor_excel": excel_v,
        "tol": tol,
        "ok": not erros,
    }
    ctx["valor_check"] = resultado

    if erros:
        raise RuntimeError(
            "Valor divergente (tol={:.2f}): {}. Clipboard={!r}.".format(
                tol, "; ".join(erros), bruto
            )
        )
    return resultado
