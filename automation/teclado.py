"""Ações de teclado via Win32 SendInput (mais estável no SAP que pynput)."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from typing import Iterable, List

import pyperclip

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_UNICODE = 0x0004
# Virtual-key codes
_VK = {
    "f3": 0x72,
    "f6": 0x75,
    "f9": 0x78,
    "f10": 0x79,
    "delete": 0x2E,
    "del": 0x2E,
    "enter": 0x0D,
    "tab": 0x09,
    "esc": 0x1B,
    "escape": 0x1B,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "shift": 0x10,
    "a": 0x41,
    "c": 0x43,
    "v": 0x56,
}

_EXTENDED = frozenset({"delete", "del"})


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT(ctypes.Structure):
    """Union completa + ULONG_PTR: necessário no Python 64-bit."""

    class _I(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("mi", MOUSEINPUT),
            ("hi", HARDWAREINPUT),
        ]

    _anonymous_ = ("i",)
    _fields_ = [("type", wintypes.DWORD), ("i", _I)]


def _vk(nome):
    # type: (str) -> int
    n = str(nome).strip().lower()
    if n in _VK:
        return _VK[n]
    if len(n) == 1:
        code = ctypes.windll.user32.VkKeyScanW(ord(n))
        if code == -1:
            raise ValueError("Tecla desconhecida: {!r}".format(nome))
        return code & 0xFF
    raise ValueError("Tecla desconhecida: {!r}".format(nome))


def _send_vk(vk, keyup=False, extended=False):
    # type: (int, bool, bool) -> None
    flags = 0
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if keyup:
        flags |= KEYEVENTF_KEYUP
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
    sent = ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    if sent != 1:
        raise RuntimeError(
            "SendInput falhou para vk=0x{:02X} (err={})".format(
                vk, ctypes.GetLastError()
            )
        )


def _tap(nome, hold=0.06):
    # type: (str, float) -> None
    """Pressiona e solta uma tecla (hold evita SAP ignorar o toque)."""
    n = str(nome).strip().lower()
    vk = _vk(n)
    extended = n in _EXTENDED
    _send_vk(vk, keyup=False, extended=extended)
    time.sleep(max(0.02, float(hold)))
    _send_vk(vk, keyup=True, extended=extended)


def pressionar(nome, vezes=1, pausa=0.04, hold=0.06):
    # type: (str, int, float, float) -> None
    for _ in range(max(1, int(vezes))):
        _tap(nome, hold=hold)
        time.sleep(max(0.0, float(pausa)))


def pressionar_lista(nomes, pausa=0.08, hold=0.06):
    # type: (Iterable[str], float, float) -> None
    for nome in nomes:
        pressionar(nome, vezes=1, pausa=pausa, hold=hold)


def hotkey(nomes, pausa=0.08, hold=0.06):
    # type: (List[str], float, float) -> None
    """Ex.: ['ctrl', 'f6'] ou ['ctrl', 'a']."""
    resolved = []
    for nome in nomes:
        n = str(nome).strip().lower()
        resolved.append((n, _vk(n), n in _EXTENDED))

    for _n, vk, ext in resolved:
        _send_vk(vk, keyup=False, extended=ext)
        time.sleep(0.02)

    time.sleep(max(0.02, float(hold)))

    for _n, vk, ext in reversed(resolved):
        _send_vk(vk, keyup=True, extended=ext)
        time.sleep(0.02)

    time.sleep(max(0.0, float(pausa)))


def digitar_texto(texto, pausa_char=0.03):
    # type: (str, float) -> None
    """Digita caractere a caractere (KEYEVENTF_UNICODE). Usado em kind=type."""
    if texto is None:
        return
    for ch in str(texto):
        code = ord(ch)
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.ki = KEYBDINPUT(0, code, KEYEVENTF_UNICODE, 0, 0)
        if ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) != 1:
            raise RuntimeError("Falha ao digitar {!r}".format(ch))
        inp2 = INPUT(type=INPUT_KEYBOARD)
        inp2.ki = KEYBDINPUT(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp2), ctypes.sizeof(INPUT))
        time.sleep(max(0.0, float(pausa_char)))


def colar_texto(texto):
    # type: (str) -> None
    anterior = None
    try:
        anterior = pyperclip.paste()
    except Exception:
        pass
    pyperclip.copy(texto if texto is not None else "")
    time.sleep(0.05)
    hotkey(["ctrl", "v"], pausa=0.08)
    if anterior is not None:
        try:
            pyperclip.copy(anterior)
        except Exception:
            pass


def limpar_campo_delete(vezes=10):
    # type: (int) -> None
    pressionar("delete", vezes=vezes, pausa=0.02, hold=0.03)
