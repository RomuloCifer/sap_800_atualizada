"""Executa os passos de uma parte (teclado, cliques mapeados, ação do usuário)."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

import tkinter as tk
from tkinter import messagebox, simpledialog

from automation import kinds
from automation import localmap
from automation import mapa as catalog
from automation import teclado
from automation import win_mouse

# Opcional: a UI registra um handler thread-safe (askokcancel na thread do Tk).
_user_action_handler = None  # type: Optional[Callable[[dict], bool]]


def set_user_action_handler(handler):
    # type: (Optional[Callable[[dict], bool]]) -> None
    global _user_action_handler
    _user_action_handler = handler


def _resolver_texto(passo, texto=None, contexto=None, pedir_se_faltar=False):
    # type: (dict, Optional[str], Optional[Dict[str, Any]], bool) -> str
    """
    Ordem:
    1) passo['text'] fixo (ex.: /oj1b1n, X0)
    2) passo['text_from'] no contexto (ex.: recipient_filial, issuer_id)
    3) texto da tela (batch etc.)
    4) se pedir_se_faltar (Mapear): pergunta na UI
    """
    pid = passo.get("id")
    fixo = passo.get("text")
    if fixo is not None and str(fixo) != "":
        return str(fixo)

    tf = (passo.get("text_from") or "").strip()
    ctx = contexto or {}
    if tf:
        if tf in ctx and ctx[tf] is not None and str(ctx[tf]) != "":
            return str(ctx[tf])
        if pedir_se_faltar:
            root = tk._default_root
            valor = simpledialog.askstring(
                "Valor para mapear",
                "Digite o valor de '{}' (passo {}).\n"
                "Depois virá do XML/Excel automaticamente.".format(tf, pid),
                parent=root,
            )
            if valor is None or not str(valor).strip():
                raise RuntimeError(
                    "Passo '{}' precisa de '{}' para continuar o Mapear.".format(pid, tf)
                )
            return str(valor).strip()
        raise RuntimeError(
            "Passo '{}' espera contexto['{}'] (ainda não ligado ao XML/Excel)."
            .format(pid, tf)
        )

    if texto is not None and str(texto).strip():
        return str(texto).strip()

    raise RuntimeError(
        "Passo '{}' sem texto (preencha a tela ou contexto).".format(pid)
    )


def _pedir_acao_usuario(passo):
    # type: (dict) -> None
    nome = passo.get("nome") or passo.get("id")
    obs = (passo.get("obs") or "").strip()
    msg = obs or "Faça a ação necessária e clique em OK para continuar."
    payload = {"id": passo.get("id"), "nome": nome, "msg": msg}

    if _user_action_handler is not None:
        ok = bool(_user_action_handler(passo))
    else:
        root = tk._default_root
        if root is not None:
            try:
                root.attributes("-topmost", True)
                root.lift()
            except Exception:
                pass
        ok = messagebox.askokcancel(
            "Ação do usuário",
            "{}\n\n{}".format(payload["nome"], payload["msg"]),
        )
    if not ok:
        raise RuntimeError("Usuário cancelou em '{}'.".format(passo.get("id")))

def _pausa_do_passo(passo, padrao):
    # type: (dict, float) -> float
    """pausa = intervalo entre teclas/repetições deste passo."""
    if "pausa" not in passo or passo.get("pausa") is None:
        return float(padrao)
    return float(passo["pausa"])


def pausa_depois_do_passo(passo, padrao=0.35):
    # type: (dict, float) -> float
    """pausa_depois = espera após o passo, antes do próximo."""
    if "pausa_depois" not in passo or passo.get("pausa_depois") is None:
        return float(padrao)
    return float(passo["pausa_depois"])


def executar_passo(passo, texto=None, pontos=None, contexto=None, pedir_texto=False):
    # type: (dict, Optional[str], Optional[dict], Optional[Dict[str, Any]], bool) -> None
    """Executa um único passo (tecla, paste/type, click com XY já resolvido, etc.)."""
    pts = pontos if pontos is not None else localmap.load_pontos()
    _executar_passo(passo, texto, pts, contexto=contexto, pedir_texto=pedir_texto)


def _executar_passo(passo, texto, pontos, contexto=None, pedir_texto=False):
    # type: (dict, Optional[str], dict, Optional[Dict[str, Any]], bool) -> None
    pid = str(passo["id"])
    kind = str(passo.get("kind") or "")

    if kind == "keys":
        lista = list(passo.get("keys") or [])
        if not lista:
            raise RuntimeError("Passo '{}' kind=keys sem 'keys'.".format(pid))
        repeat = int(passo.get("repeat") or 1)
        pausa = _pausa_do_passo(passo, 0.08)
        if len(lista) == 1 and repeat > 1:
            teclado.pressionar(lista[0], vezes=repeat, pausa=pausa)
        else:
            teclado.pressionar_lista(lista, pausa=pausa)
        return

    if kind == "hotkey":
        lista = list(passo.get("keys") or [])
        if len(lista) < 2:
            raise RuntimeError("Passo '{}' kind=hotkey precisa de 2+ teclas.".format(pid))
        teclado.hotkey(lista, pausa=_pausa_do_passo(passo, 0.08))
        return

    if kind == "paste":
        valor = _resolver_texto(passo, texto=texto, contexto=contexto, pedir_se_faltar=pedir_texto)
        teclado.colar_texto(valor)
        return

    if kind == "type":
        valor = _resolver_texto(passo, texto=texto, contexto=contexto, pedir_se_faltar=pedir_texto)
        teclado.digitar_texto(valor)
        return

    if kind == "user_action":
        _pedir_acao_usuario(passo)
        return

    if kind in kinds.KINDS_COM_XY:
        x, y = localmap.resolve_xy(pid, pontos)
        if kind == "click":
            win_mouse.click(x, y)
            return
        if kind == "click_and_type":
            win_mouse.click(x, y)
            time.sleep(0.12)
            teclado.limpar_campo_delete(int(passo.get("limpar") or 10))
            valor = _resolver_texto(
                passo, texto=texto, contexto=contexto, pedir_se_faltar=pedir_texto
            )
            teclado.colar_texto(valor)
            return

    raise RuntimeError("kind desconhecido '{}' no passo '{}'.".format(kind, pid))


def executar_parte(nome_parte, texto=None, pausa_entre=0.35, contexto=None):
    # type: (str, Optional[str], float, Optional[Dict[str, Any]]) -> int
    """
    Roda todos os passos da parte.
    contexto: dict com chaves text_from (recipient_filial, issuer_id, …).
    """
    win_mouse.ensure_dpi_awareness()
    passos = catalog.passos_da_parte(nome_parte)
    if not passos:
        raise RuntimeError(
            "A parte '{}' não tem passos em mapa_passos.json ainda.".format(nome_parte)
        )

    faltam = localmap.ids_faltando(nome_parte)
    if faltam:
        raise RuntimeError(
            "Faltam coordenadas locais ({}). Use Mapear antes.\n  - {}".format(
                len(faltam), "\n  - ".join(faltam)
            )
        )

    pontos = localmap.load_pontos()
    executados = 0
    for passo in passos:
        catalog.validar_passo(passo)
        _executar_passo(passo, texto, pontos, contexto=contexto, pedir_texto=False)
        executados += 1
        time.sleep(pausa_depois_do_passo(passo, pausa_entre))

    return executados
