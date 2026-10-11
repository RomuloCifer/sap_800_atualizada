"""
Mapeamento local de coordenadas por id do passo.

mapa_passos.json  → nomes (versionar)
pontos_local.json → XY desta máquina (NÃO versionar)

Uso:
  - Clique do meio (roda) grava o ponto
  - Esc cancela
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tkinter as tk

from automation import kinds
from automation import mapa as catalog
from automation import win_mouse

ROOT = Path(__file__).resolve().parent.parent
LOCAL_FILE = ROOT / "pontos_local.json"


def load_pontos():
    # type: () -> Dict[str, dict]
    if not LOCAL_FILE.is_file():
        return {}
    with LOCAL_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    pontos = data.get("pontos") if isinstance(data, dict) else None
    if not isinstance(pontos, dict):
        return {}
    return {str(k): v for k, v in pontos.items() if isinstance(v, dict)}


def save_pontos(pontos):
    # type: (Dict[str, dict]) -> None
    payload = {
        "versao": 1,
        "descricao": "XY desta máquina, por id do passo. Não versionar / não compartilhar.",
        "pontos": pontos,
    }
    with LOCAL_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def resolve_xy(passo_id, pontos=None):
    # type: (str, Optional[Dict[str, dict]]) -> Tuple[int, int]
    data = pontos if pontos is not None else load_pontos()
    item = data.get(passo_id)
    if not item or "x" not in item or "y" not in item:
        raise KeyError(
            "Sem coordenada local para '{}'. Use Mapear nesta máquina.".format(passo_id)
        )
    return int(item["x"]), int(item["y"])


def _pedir_ponto(passo, indice, total):
    # type: (dict, int, int) -> Optional[Tuple[int, int]]
    """Abre janela e espera BOTÃO DO MEIO (roda) para gravar XY. Esc cancela."""
    win_mouse.ensure_dpi_awareness()
    cancelled = {"flag": False}

    # Preferir Toplevel se a tela principal já existe (evita segundo Tk).
    if tk._default_root is not None:
        root = tk.Toplevel(tk._default_root)
        root.transient(tk._default_root)
    else:
        root = tk.Tk()
    root.title("Mapear — {}/{}".format(indice, total))
    root.attributes("-topmost", True)
    root.configure(bg="#1e1e1e")
    root.geometry("+40+40")

    nome = passo.get("nome") or passo.get("id")
    obs = (passo.get("obs") or "").strip()
    kind = passo.get("kind") or ""

    tk.Label(
        root,
        text="Passo {}/{}".format(indice, total),
        font=("Segoe UI", 10),
        fg="#aaaaaa",
        bg="#1e1e1e",
    ).pack(anchor="w", padx=16, pady=(14, 0))

    tk.Label(
        root,
        text=str(nome),
        font=("Segoe UI", 14, "bold"),
        fg="#ffffff",
        bg="#1e1e1e",
    ).pack(anchor="w", padx=16, pady=(4, 0))

    tk.Label(
        root,
        text="id: {}   kind: {}".format(passo.get("id"), kind),
        font=("Consolas", 9),
        fg="#88cc88",
        bg="#1e1e1e",
    ).pack(anchor="w", padx=16, pady=(6, 0))

    if obs:
        tk.Label(
            root,
            text=obs,
            font=("Segoe UI", 10),
            fg="#ffcc66",
            bg="#1e1e1e",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(8, 0))

    tk.Label(
        root,
        text="GRAVAR = botão do MEIO do mouse (apertar a roda)\nEsc ou fechar a janela = cancelar",
        font=("Segoe UI", 11, "bold"),
        fg="#7CFC00",
        bg="#1e1e1e",
        justify="left",
    ).pack(anchor="w", padx=16, pady=(12, 0))

    coords = tk.Label(
        root,
        text="X: ----   Y: ----",
        font=("Consolas", 12, "bold"),
        fg="#7CFC00",
        bg="#1e1e1e",
    )
    coords.pack(anchor="w", padx=16, pady=(10, 14))

    def _tick():
        try:
            mx, my = win_mouse.position()
            coords.config(text="X: {:4d}   Y: {:4d}".format(mx, my))
            root.after(50, _tick)
        except tk.TclError:
            pass

    def _on_close():
        cancelled["flag"] = True

    root.protocol("WM_DELETE_WINDOW", _on_close)
    _tick()
    root.update_idletasks()
    root.update()

    def _cancel():
        if cancelled["flag"]:
            return True
        if win_mouse.escape_pressed():
            cancelled["flag"] = True
            return True
        try:
            root.update()
        except tk.TclError:
            cancelled["flag"] = True
            return True
        return False

    xy = win_mouse.wait_middle_click(cancel_check=_cancel)
    try:
        root.destroy()
    except Exception:
        pass

    if xy is None:
        return None
    time.sleep(0.15)
    return int(xy[0]), int(xy[1])


def mapear_parte(nome_parte, remapear_tudo=False):
    # type: (str, bool) -> Tuple[int, int]
    """
    Mapeia só passos que precisam de XY (click / click_and_type).
    Teclas, paste e user_action são ignorados no Mapear.
    Retorna (gravados_agora, total_que_precisam_xy).
    """
    todos = catalog.passos_da_parte(nome_parte)
    if not todos:
        raise RuntimeError(
            "A parte '{}' não tem passos em mapa_passos.json ainda.".format(nome_parte)
        )

    for passo in todos:
        catalog.validar_passo(passo)

    passos = catalog.passos_com_xy(nome_parte)
    if not passos:
        raise RuntimeError(
            "A parte '{}' não tem passos com clique para mapear "
            "(só teclas/ações automáticas ou do usuário).".format(nome_parte)
        )

    pontos = load_pontos()
    if remapear_tudo:
        for passo in passos:
            pontos.pop(str(passo["id"]), None)

    gravados = 0
    total = len(passos)
    for i, passo in enumerate(passos, start=1):
        pid = str(passo["id"])
        if pid in pontos and "x" in pontos[pid] and "y" in pontos[pid]:
            continue
        xy = _pedir_ponto(passo, i, total)
        if xy is None:
            save_pontos(pontos)
            raise RuntimeError("Mapeamento cancelado em '{}'.".format(pid))
        pontos[pid] = {"x": xy[0], "y": xy[1]}
        gravados += 1
        save_pontos(pontos)

    return gravados, total


def ids_faltando(nome_parte):
    # type: (str) -> List[str]
    """Só ids de passos que precisam de coordenada local."""
    passos = catalog.passos_com_xy(nome_parte)
    pontos = load_pontos()
    faltam = []
    for passo in passos:
        if not kinds.precisa_xy(passo.get("kind")):
            continue
        pid = str(passo["id"])
        item = pontos.get(pid)
        if not item or "x" not in item or "y" not in item:
            faltam.append(pid)
    return faltam
