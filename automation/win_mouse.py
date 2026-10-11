"""
Mouse via Win32 (GetCursorPos / SetCursorPos / SendInput).

Mesmo sistema de coordenadas na captura e no clique, com DPI awareness.
"""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

_DPI_DONE = False

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("i",)
    _fields_ = [("type", wintypes.DWORD), ("i", _I)]


def ensure_dpi_awareness():
    # type: () -> None
    global _DPI_DONE
    if _DPI_DONE:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    _DPI_DONE = True


def position():
    # type: () -> tuple
    ensure_dpi_awareness()
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)


def move_to(x, y):
    # type: (int, int) -> None
    ensure_dpi_awareness()
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    time.sleep(0.03)


def _virtual_screen_metrics():
    # type: () -> tuple
    user32 = ctypes.windll.user32
    return (
        user32.GetSystemMetrics(76),
        user32.GetSystemMetrics(77),
        user32.GetSystemMetrics(78),
        user32.GetSystemMetrics(79),
    )


def _to_absolute(x, y):
    # type: (int, int) -> tuple
    vx, vy, vw, vh = _virtual_screen_metrics()
    if vw <= 0 or vh <= 0:
        return 0, 0
    abs_x = int(round((int(x) - vx) * 65535 / (vw - 1)))
    abs_y = int(round((int(y) - vy) * 65535 / (vh - 1)))
    return abs_x, abs_y


def _send_mouse(flags, x=0, y=0):
    # type: (int, int, int) -> None
    extra = ctypes.c_ulong(0)
    mi = MOUSEINPUT(x, y, 0, flags, 0, ctypes.pointer(extra))
    inp = INPUT(type=INPUT_MOUSE, mi=mi)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def click(x, y, clicks=1, interval=0.08):
    # type: (int, int, int, float) -> None
    ensure_dpi_awareness()
    move_to(x, y)
    abs_x, abs_y = _to_absolute(x, y)
    flags_move = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    _send_mouse(flags_move, abs_x, abs_y)
    time.sleep(0.02)
    for i in range(clicks):
        _send_mouse(
            MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
            abs_x,
            abs_y,
        )
        time.sleep(0.02)
        _send_mouse(
            MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
            abs_x,
            abs_y,
        )
        if i + 1 < clicks:
            time.sleep(interval)


# Virtual-key codes
VK_MBUTTON = 0x04  # botão do meio (roda)
VK_ESCAPE = 0x1B


def _key_down(vk):
    # type: (int) -> bool
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def wait_middle_click(cancel_check=None, poll=0.02):
    # type: (object, float) -> tuple
    """
    Espera clique do botão do meio (roda).
    Retorna (x, y) ou None se cancel_check() for True (ex.: Esc).
    """
    ensure_dpi_awareness()
    # Espera soltar se já estiver pressionado
    while _key_down(VK_MBUTTON):
        if cancel_check and cancel_check():
            return None
        time.sleep(poll)
    while True:
        if cancel_check and cancel_check():
            return None
        if _key_down(VK_MBUTTON):
            x, y = position()
            while _key_down(VK_MBUTTON):
                if cancel_check and cancel_check():
                    return None
                time.sleep(poll)
            return int(x), int(y)
        time.sleep(poll)


def escape_pressed():
    # type: () -> bool
    return _key_down(VK_ESCAPE)
