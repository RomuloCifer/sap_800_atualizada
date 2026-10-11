"""Tela simples: Iniciar automação / Mapear."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from automation import localmap
from automation import mapa as catalog
from automation import runner
from automation import win_mouse


class App(tk.Tk):
    def __init__(self):
        # type: () -> None
        super(App, self).__init__()
        win_mouse.ensure_dpi_awareness()

        self.title("SAP 800 ATT")
        self.geometry("420x280")
        self.minsize(380, 260)
        self.configure(bg="#f4f4f4")

        self._busy = False

        pad = {"padx": 16, "pady": 6}

        tk.Label(
            self,
            text="SAP 800 ATT",
            font=("Segoe UI", 16, "bold"),
            bg="#f4f4f4",
        ).pack(anchor="w", padx=16, pady=(16, 4))

        tk.Label(
            self,
            text="Parte",
            font=("Segoe UI", 9),
            bg="#f4f4f4",
        ).pack(anchor="w", padx=16)

        self.parte_var = tk.StringVar()
        self.combo = ttk.Combobox(
            self, textvariable=self.parte_var, state="readonly", width=36
        )
        self.combo.pack(anchor="w", **pad)
        self._recarregar_partes()

        row_texto = tk.Frame(self, bg="#f4f4f4")
        row_texto.pack(fill="x", padx=16, pady=4)
        tk.Label(row_texto, text="Texto (batch etc.)", bg="#f4f4f4").pack(anchor="w")
        self.texto_var = tk.StringVar()
        tk.Entry(row_texto, textvariable=self.texto_var, width=38).pack(anchor="w", pady=2)

        self.remapear_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self,
            text="Remapear tudo (ignora pontos já gravados)",
            variable=self.remapear_var,
            bg="#f4f4f4",
            activebackground="#f4f4f4",
        ).pack(anchor="w", padx=16, pady=4)

        btns = tk.Frame(self, bg="#f4f4f4")
        btns.pack(fill="x", padx=16, pady=12)

        self.btn_iniciar = tk.Button(
            btns,
            text="Iniciar automação",
            width=18,
            height=2,
            command=self._on_iniciar,
        )
        self.btn_iniciar.pack(side="left", padx=(0, 8))

        self.btn_mapear = tk.Button(
            btns,
            text="Mapear",
            width=14,
            height=2,
            command=self._on_mapear,
        )
        self.btn_mapear.pack(side="left")

        self.status = tk.Label(
            self,
            text="Pronto.",
            font=("Segoe UI", 9),
            fg="#333333",
            bg="#f4f4f4",
            wraplength=380,
            justify="left",
        )
        self.status.pack(anchor="w", padx=16, pady=(4, 12))

    def _recarregar_partes(self):
        # type: () -> None
        try:
            partes = catalog.listar_partes()
        except Exception as exc:
            partes = []
            self.status.config(text="Erro ao ler mapa: {}".format(exc))
        self.combo["values"] = partes
        if partes and not self.parte_var.get():
            self.parte_var.set(partes[0])

    def _set_busy(self, busy, msg=None):
        # type: (bool, str | None) -> None
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_iniciar.config(state=state)
        self.btn_mapear.config(state=state)
        if msg is not None:
            self.status.config(text=msg)

    def _parte_selecionada(self):
        # type: () -> str
        nome = (self.parte_var.get() or "").strip()
        if not nome:
            raise RuntimeError("Selecione uma parte.")
        return nome

    def _on_mapear(self):
        # type: () -> None
        if self._busy:
            return
        try:
            parte = self._parte_selecionada()
        except Exception as exc:
            messagebox.showerror("Mapear", str(exc))
            return

        remapear = bool(self.remapear_var.get())
        # Mapear roda na thread da UI (janelas Tk do capturador).
        self._set_busy(True, "Mapeando '{}'…".format(parte))
        self.update_idletasks()
        try:
            gravados, total = localmap.mapear_parte(parte, remapear_tudo=remapear)
            msg = "Mapear ok: {} novo(s) / {} passo(s) em '{}'.".format(
                gravados, total, parte
            )
            self._fim_ok(msg)
        except Exception as exc:
            self._fim_erro("Mapear", str(exc))

    def _on_iniciar(self):
        # type: () -> None
        if self._busy:
            return
        try:
            parte = self._parte_selecionada()
        except Exception as exc:
            messagebox.showerror("Iniciar", str(exc))
            return

        texto = self.texto_var.get()
        self._set_busy(True, "Rodando '{}' em 2s… foque o SAP.".format(parte))

        def trabalho():
            try:
                import time

                time.sleep(2)
                n = runner.executar_parte(parte, texto=texto or None)
                msg = "Concluído: {} passo(s) em '{}'.".format(n, parte)
                self.after(0, lambda: self._fim_ok(msg))
            except Exception as exc:
                self.after(0, lambda: self._fim_erro("Iniciar", str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _fim_ok(self, msg):
        # type: (str) -> None
        self._set_busy(False, msg)
        messagebox.showinfo("OK", msg)

    def _fim_erro(self, titulo, msg):
        # type: (str, str) -> None
        self._set_busy(False, msg)
        messagebox.showerror(titulo, msg)


def run_app():
    # type: () -> None
    app = App()
    app.mainloop()
