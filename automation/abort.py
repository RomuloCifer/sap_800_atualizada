"""
Parada da automação por tecla global (Esc).

Funciona mesmo com o SAP em foco (GetAsyncKeyState).
Só fica ativo enquanto a automação está armada.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from automation import win_mouse

_DEPTH = 0


class AbortError(RuntimeError):
    """Usuário pediu para parar (Esc)."""


def armar():
    # type: () -> None
    global _DEPTH
    if _DEPTH == 0:
        while win_mouse.escape_pressed():
            time.sleep(0.02)
    _DEPTH += 1


def desarmar():
    # type: () -> None
    global _DEPTH
    _DEPTH = max(0, _DEPTH - 1)


def armado():
    # type: () -> bool
    return _DEPTH > 0


@contextmanager
def sessao():
    # type: () -> Iterator[None]
    armar()
    try:
        yield
    finally:
        desarmar()


def check():
    # type: () -> None
    """Levanta AbortError se Esc estiver pressionado e a automação estiver armada."""
    if _DEPTH > 0 and win_mouse.escape_pressed():
        raise AbortError("Automacao interrompida (Esc).")


def sleep(segundos):
    # type: (float) -> None
    """time.sleep que verifica Esc a cada ~50ms."""
    fim = time.time() + max(0.0, float(segundos))
    while True:
        check()
        restante = fim - time.time()
        if restante <= 0:
            return
        time.sleep(min(0.05, restante))
