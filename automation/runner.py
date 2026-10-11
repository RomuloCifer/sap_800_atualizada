"""Executa os passos de uma parte usando XY de pontos_local.json."""

from __future__ import annotations

import time
from typing import Optional

import pyperclip
from pynput.keyboard import Controller, Key

from automation import localmap
from automation import mapa as catalog
from automation import win_mouse

_keyboard = Controller()


def _digitar_texto(texto):
    # type: (str) -> None
    """Cola texto via clipboard (mais estável com caracteres especiais)."""
    anterior = None
    try:
        anterior = pyperclip.paste()
    except Exception:
        pass
    pyperclip.copy(texto if texto is not None else "")
    time.sleep(0.05)
    with _keyboard.pressed(Key.ctrl):
        _keyboard.press("v")
        _keyboard.release("v")
    time.sleep(0.08)
    if anterior is not None:
        try:
            pyperclip.copy(anterior)
        except Exception:
            pass


def _limpar_campo(vezes=10):
    # type: (int) -> None
    for _ in range(vezes):
        _keyboard.press(Key.delete)
        _keyboard.release(Key.delete)
        time.sleep(0.02)


def executar_parte(nome_parte, texto=None, pausa_entre=0.35):
    # type: (str, Optional[str], float) -> int
    """
    Roda todos os passos da parte.
    Retorna quantidade de passos executados.
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
        pid = str(passo["id"])
        kind = str(passo.get("kind") or "click")
        x, y = localmap.resolve_xy(pid, pontos)

        if kind == "click":
            win_mouse.click(x, y)
        elif kind == "click_and_type":
            win_mouse.click(x, y)
            time.sleep(0.12)
            _limpar_campo(int(passo.get("limpar") or 10))
            valor = texto if texto is not None else (passo.get("text") or "")
            if valor:
                _digitar_texto(str(valor))
        else:
            raise RuntimeError(
                "kind desconhecido '{}' no passo '{}'.".format(kind, pid)
            )

        executados += 1
        time.sleep(pausa_entre)

    return executados
