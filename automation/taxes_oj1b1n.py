"""
Preencher Taxes no OJ1B1N após os itens.

Seleciona N itens (dy das âncoras), abre Taxes, preenche tax types
(2025 vs 2026+), copia Value por drag, cola em Other Base, Taxes II + CBS/IBS.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from automation import abort
from automation import teclado
from automation import win_mouse
from automation.itens_oj1b1n import calcular_dy, _xy

ANCORAS_SEL = (
    ("preencher_taxes.ancor_sel_1", 1),
    ("preencher_taxes.ancor_sel_2", 2),
    ("preencher_taxes.ancor_sel_5", 5),
    ("preencher_taxes.ancor_sel_10", 10),
    ("preencher_taxes.ancor_sel_20", 20),
)

ID_TAXES = "preencher_taxes.clique_taxes"
ID_TAX_TYPE = "preencher_taxes.tax_type_1"
ID_STAT_TAX = "preencher_taxes.stat_tax"
ID_VALUE_INI = "preencher_taxes.value_ini"
ID_VALUE_FIM = "preencher_taxes.value_fim"
IDS_OTHER_BASE = (
    "preencher_taxes.other_base_1",
    "preencher_taxes.other_base_2",
    "preencher_taxes.other_base_3",
    "preencher_taxes.other_base_4",
    "preencher_taxes.other_base_5",
    "preencher_taxes.other_base_6",
)
ID_TAXES_II = "preencher_taxes.clique_taxes_ii"
ID_CBS_IBS = "preencher_taxes.clique_cbs_ibs"
ID_TAXES_ANTES_MATEMATICO = "preencher_taxes.clique_taxes_antes_matematico"
ID_E_MATEMATICO = "preencher_taxes.clique_e_matematico"

TAXES_BASE = ("ICOF", "ICM0", "IPIS", "IPI0")


def issue_date_2026_plus(issue_date):
    # type: (str) -> bool
    """True se issue date >= 01.01.2026 (aceita DD.MM.YYYY ou ISO)."""
    raw = (issue_date or "").strip()
    if not raw:
        return False
    if "T" in raw:
        raw = raw.split("T", 1)[0]
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw[:10], fmt) >= datetime(2026, 1, 1)
        except ValueError:
            continue
    return False


def xy_sel_item(pontos, linha_1based, dy=None):
    # type: (Dict[str, dict], int, Optional[float]) -> Tuple[int, int]
    x0, y0 = _xy(pontos, ANCORAS_SEL[0][0])
    step = dy if dy is not None else calcular_dy(pontos, ANCORAS_SEL)
    y = int(round(y0 + (int(linha_1based) - 1) * step))
    return x0, y


def _clicar(pid, pontos, espera=0.2):
    # type: (str, Dict[str, dict], float) -> None
    x, y = _xy(pontos, pid)
    win_mouse.click(x, y)
    time.sleep(espera)


def _enter2(pausa=0.4):
    # type: (float) -> None
    teclado.pressionar("enter", vezes=2, pausa=pausa, hold=0.05)


def _escrever(texto):
    # type: (str) -> None
    teclado.digitar_texto(str(texto))
    time.sleep(0.1)


def _n_itens(contexto):
    # type: (Optional[Dict[str, Any]]) -> int
    ctx = contexto or {}
    itens = ctx.get("itens")
    if itens:
        return len(list(itens))
    nfe = ctx.get("_nfe")
    if nfe is not None and getattr(nfe, "itens", None):
        return len(list(nfe.itens))
    n = ctx.get("n_itens")
    if n is not None:
        return int(n)
    raise RuntimeError("Sem itens no contexto para selecionar em Taxes.")


def _selecionar_itens(pontos, n_itens):
    # type: (Dict[str, dict], int) -> None
    dy = calcular_dy(pontos, ANCORAS_SEL)
    for i in range(1, int(n_itens) + 1):
        abort.check()
        x, y = xy_sel_item(pontos, i, dy=dy)
        win_mouse.click(x, y)
        abort.sleep(0.18)


def _preencher_tax_types(pontos, ano_2026):
    # type: (Dict[str, dict], bool) -> None
    if ano_2026:
        _clicar(ID_TAX_TYPE, pontos, 0.25)
        _escrever("IB2S")
        _clicar(ID_STAT_TAX, pontos, 0.25)
        _enter2(0.4)
        _escrever("CBS1")
        _clicar(ID_STAT_TAX, pontos, 0.25)
        _enter2(0.4)
        # Em seguida os 4 códigos (sem novo clique em Tax Type)
        for i, codigo in enumerate(TAXES_BASE):
            _escrever(codigo)
            _enter2(0.4)
        return

    _clicar(ID_TAX_TYPE, pontos, 0.25)
    for codigo in TAXES_BASE:
        _escrever(codigo)
        _enter2(0.4)


def _copiar_value(pontos):
    # type: (Dict[str, dict]) -> str
    import pyperclip

    x1, y1 = _xy(pontos, ID_VALUE_INI)
    x2, y2 = _xy(pontos, ID_VALUE_FIM)
    win_mouse.drag(x1, y1, x2, y2)
    time.sleep(0.12)
    teclado.hotkey(["ctrl", "c"], pausa=0.1)
    time.sleep(0.15)
    valor = (pyperclip.paste() or "").strip()
    if not valor:
        raise RuntimeError(
            "Clipboard vazio apos selecionar Value. Remapeie value_ini/value_fim."
        )
    return valor


def _colar_other_base(pontos, valor, n_celulas):
    # type: (Dict[str, dict], str, int) -> None
    """De baixo pra cima: 2025 → 4..1; 2026+ → 6..1 (evita popup cobrindo a próxima célula)."""
    celulas = list(IDS_OTHER_BASE[: int(n_celulas)])
    for pid in reversed(celulas):
        abort.check()
        _clicar(pid, pontos, 0.2)
        _escrever(valor)
        time.sleep(0.08)
    # Após todos os Other Base
    _enter2(0.4)


def executar_preenchimento(contexto, pontos, passo=None):
    # type: (Optional[Dict[str, Any]], Dict[str, dict], Optional[dict]) -> int
    """
    fase no passo:
      - ate_other_base: seleção → tax types → Value → Other Base (para checkpoint humano)
      - fim: Taxes II → CBS/IBS → Taxes → E matemático
      - tudo (padrão): as duas fases sem pausa humana
    """
    ctx = contexto or {}
    fase = str((passo or {}).get("fase") or "tudo").strip().lower()
    n = _n_itens(ctx)
    ano_2026 = issue_date_2026_plus(str(ctx.get("issue_date") or ""))

    if fase in ("tudo", "ate_other_base"):
        abort.check()
        _selecionar_itens(pontos, n)
        abort.check()
        _clicar(ID_TAXES, pontos, 0.6)

        abort.check()
        _preencher_tax_types(pontos, ano_2026)

        abort.check()
        valor = _copiar_value(pontos)
        n_other = 6 if ano_2026 else 4
        _colar_other_base(pontos, valor, n_other)

    if fase in ("tudo", "fim"):
        abort.check()
        _clicar(ID_TAXES_II, pontos, 0.4)
        cbs = _resolver_cbs_ibs(ctx)
        _clicar(ID_CBS_IBS, pontos, 0.45)
        if cbs:
            abort.sleep(0.2)
            _escrever(cbs)
            abort.sleep(0.1)

        abort.check()
        _clicar(ID_TAXES_ANTES_MATEMATICO, pontos, 0.5)
        abort.check()
        _clicar(ID_E_MATEMATICO, pontos, 0.4)

    return n


def _resolver_cbs_ibs(ctx):
    # type: (Dict[str, Any]) -> str
    """CBS/IBS do contexto; se vazio e houver Excel, relê a linha."""
    cbs = str(ctx.get("cbs_ibs") or "").strip()
    if cbs:
        return cbs
    caminho = ctx.get("excel_arquivo")
    linha = ctx.get("excel_linha")
    if not caminho or not linha:
        return ""
    try:
        from automation.excel_fila import ler_cbs_ibs_linha

        relido = ler_cbs_ibs_linha(caminho, int(linha))
        if relido:
            ctx["cbs_ibs"] = relido
            return relido
    except Exception:
        pass
    return ""
