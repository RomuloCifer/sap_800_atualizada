"""Verificação humana: OK continua; Parar pede motivo (Status Excel) e encerra."""

from __future__ import annotations

import threading
import tkinter as tk
from typing import Optional, Tuple


class VerificacaoCancelada(Exception):
    """Usuário clicou Parar e informou motivo para o Status do Excel."""

    def __init__(self, motivo, passo_id=None):
        # type: (str, Optional[str]) -> None
        self.motivo = (motivo or "").strip() or "parado"
        self.passo_id = passo_id
        super(VerificacaoCancelada, self).__init__(
            "Verificacao cancelada: {}".format(self.motivo)
        )


def pedir_motivo_parar(parent=None):
    # type: (Optional[tk.Misc]) -> str
    """Caixa para digitar o motivo (vai para a coluna Status)."""
    created = False
    root = parent
    if root is None:
        root = tk._default_root
    if root is None:
        root = tk.Tk()
        root.withdraw()
        created = True

    win = tk.Toplevel(root)
    win.title("Motivo da parada")
    win.configure(bg="#1e1e1e")
    win.attributes("-topmost", True)
    win.resizable(False, False)
    win.grab_set()
    out = {"motivo": ""}

    tk.Label(
        win,
        text="Motivo (vai no Status do Excel)",
        font=("Segoe UI", 12, "bold"),
        fg="#ffffff",
        bg="#1e1e1e",
    ).pack(anchor="w", padx=20, pady=(16, 6))

    tk.Label(
        win,
        text="Ex.: valor divergente, item faltando, CFOP errado…",
        font=("Segoe UI", 9),
        fg="#aaaaaa",
        bg="#1e1e1e",
    ).pack(anchor="w", padx=20)

    entry = tk.Entry(win, width=48, font=("Segoe UI", 11))
    entry.pack(fill="x", padx=20, pady=12)
    entry.focus_set()

    row = tk.Frame(win, bg="#1e1e1e")
    row.pack(fill="x", padx=20, pady=(0, 16))

    def confirmar():
        out["motivo"] = (entry.get() or "").strip()
        win.destroy()

    def cancelar_sem_motivo():
        out["motivo"] = "parado"
        win.destroy()

    tk.Button(
        row,
        text="Confirmar e parar",
        width=18,
        height=2,
        font=("Segoe UI", 10, "bold"),
        command=confirmar,
    ).pack(side="left", padx=(0, 10))
    tk.Button(row, text="Parar sem texto", width=14, height=2, command=cancelar_sem_motivo).pack(
        side="left"
    )

    win.protocol("WM_DELETE_WINDOW", cancelar_sem_motivo)
    win.bind("<Return>", lambda _e: confirmar())
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    sx, sy = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry("+{}+{}".format(max(40, (sx - w) // 2), max(40, (sy - h) // 3)))
    win.wait_window()

    if created:
        try:
            root.destroy()
        except Exception:
            pass
    return out["motivo"] or "parado"


def _dialogo_verificacao_impl(parent, titulo, mensagem):
    # type: (Optional[tk.Misc], str, str) -> Tuple[bool, Optional[str]]
    """
    Retorna (True, None) se OK.
    Retorna (False, motivo) se Parar (motivo digitado pelo usuário).
    """
    created = False
    root = parent
    if root is None:
        root = tk._default_root
    if root is None:
        root = tk.Tk()
        root.withdraw()
        created = True

    win = tk.Toplevel(root)
    win.title("Verificação humana")
    win.configure(bg="#1e1e1e")
    win.attributes("-topmost", True)
    win.resizable(False, False)
    win.grab_set()
    escolha = {"ok": False, "motivo": None}  # type: dict

    tk.Label(win, text="Verificação", font=("Segoe UI", 11), fg="#aaaaaa", bg="#1e1e1e").pack(
        anchor="w", padx=20, pady=(16, 0)
    )
    tk.Label(
        win,
        text=titulo,
        font=("Segoe UI", 14, "bold"),
        fg="#ffffff",
        bg="#1e1e1e",
        wraplength=420,
        justify="left",
    ).pack(anchor="w", padx=20, pady=(6, 0))
    tk.Label(
        win,
        text=mensagem,
        font=("Segoe UI", 10),
        fg="#ffcc66",
        bg="#1e1e1e",
        wraplength=420,
        justify="left",
    ).pack(anchor="w", padx=20, pady=(10, 0))

    row = tk.Frame(win, bg="#1e1e1e")
    row.pack(fill="x", padx=20, pady=18)

    def ok():
        escolha["ok"] = True
        escolha["motivo"] = None
        win.destroy()

    def parar():
        win.grab_release()
        win.destroy()
        escolha["ok"] = False
        escolha["motivo"] = pedir_motivo_parar(parent=root)

    btn_ok = tk.Button(
        row,
        text="OK — continuar",
        width=18,
        height=2,
        font=("Segoe UI", 10, "bold"),
        command=ok,
    )
    btn_ok.pack(side="left", padx=(0, 10))
    tk.Button(row, text="Parar", width=12, height=2, command=parar).pack(side="left")

    win.protocol("WM_DELETE_WINDOW", parar)
    win.bind("<Return>", lambda _e: ok())
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    sx, sy = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry("+{}+{}".format(max(40, (sx - w) // 2), max(40, (sy - h) // 3)))
    btn_ok.focus_set()
    win.wait_window()

    if created:
        try:
            root.destroy()
        except Exception:
            pass

    return bool(escolha["ok"]), escolha.get("motivo")


def dialogo_verificacao(parent, titulo, mensagem):
    # type: (Optional[tk.Misc], str, str) -> Tuple[bool, Optional[str]]
    """
    Diálogo thread-safe: (True, None) = OK; (False, motivo) = Parar.
    Se a UI principal já existe e parent é None, agenda no thread do Tk.
    """
    root = parent if parent is not None else tk._default_root
    if root is not None and parent is None:
        try:
            done = threading.Event()
            out = {"ok": False, "motivo": None}  # type: dict

            def mostrar():
                try:
                    ok, motivo = _dialogo_verificacao_impl(root, titulo, mensagem)
                    out["ok"] = ok
                    out["motivo"] = motivo
                finally:
                    done.set()

            root.after(0, mostrar)
            done.wait()
            return bool(out["ok"]), out.get("motivo")
        except Exception:
            pass
    return _dialogo_verificacao_impl(parent, titulo, mensagem)


def _dialogo_xml_falhou_impl(parent, mensagem):
    # type: (Optional[tk.Misc], str) -> bool
    """True = tentar novamente (pegar_xml); False = sair."""
    created = False
    root = parent
    if root is None:
        root = tk._default_root
    if root is None:
        root = tk.Tk()
        root.withdraw()
        created = True

    win = tk.Toplevel(root)
    win.title("XML não copiado")
    win.configure(bg="#1e1e1e")
    win.attributes("-topmost", True)
    win.resizable(False, False)
    win.grab_set()
    escolha = {"retry": False}

    tk.Label(
        win,
        text="Ctrl+C do XML falhou",
        font=("Segoe UI", 14, "bold"),
        fg="#ffffff",
        bg="#1e1e1e",
        wraplength=440,
        justify="left",
    ).pack(anchor="w", padx=20, pady=(16, 6))
    tk.Label(
        win,
        text=(mensagem or "").strip()
        or "O clipboard não trouxe o XML. Ajuste a tela do SAP e tente de novo.",
        font=("Segoe UI", 10),
        fg="#ffcc66",
        bg="#1e1e1e",
        wraplength=440,
        justify="left",
    ).pack(anchor="w", padx=20, pady=(0, 4))
    tk.Label(
        win,
        text="Tentar novamente = recomeça em pegar_xml (sem abrir batch de novo).",
        font=("Segoe UI", 9),
        fg="#aaaaaa",
        bg="#1e1e1e",
        wraplength=440,
        justify="left",
    ).pack(anchor="w", padx=20, pady=(0, 8))

    row = tk.Frame(win, bg="#1e1e1e")
    row.pack(fill="x", padx=20, pady=16)

    def tentar():
        escolha["retry"] = True
        win.destroy()

    def sair():
        escolha["retry"] = False
        win.destroy()

    btn = tk.Button(
        row,
        text="Tentar novamente",
        width=18,
        height=2,
        font=("Segoe UI", 10, "bold"),
        command=tentar,
    )
    btn.pack(side="left", padx=(0, 10))
    tk.Button(row, text="Sair", width=12, height=2, command=sair).pack(side="left")

    win.protocol("WM_DELETE_WINDOW", sair)
    win.bind("<Return>", lambda _e: tentar())
    win.bind("<Escape>", lambda _e: sair())
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    sx, sy = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry("+{}+{}".format(max(40, (sx - w) // 2), max(40, (sy - h) // 3)))
    btn.focus_set()
    win.wait_window()

    if created:
        try:
            root.destroy()
        except Exception:
            pass
    return bool(escolha["retry"])


def dialogo_xml_falhou(mensagem, parent=None):
    # type: (str, Optional[tk.Misc]) -> bool
    """
    Diálogo thread-safe: True = tentar de novo a partir de pegar_xml;
    False = sair (sem gravar Status).
    """
    root = parent if parent is not None else tk._default_root
    # Se a UI principal já existe, agenda no thread do Tk
    if root is not None and parent is None:
        try:
            done = threading.Event()
            out = {"retry": False}

            def mostrar():
                try:
                    out["retry"] = _dialogo_xml_falhou_impl(root, mensagem)
                finally:
                    done.set()

            root.after(0, mostrar)
            done.wait()
            return bool(out["retry"])
        except Exception:
            pass
    return _dialogo_xml_falhou_impl(parent, mensagem)
