"""Tela simples: Iniciar automação / Mapear."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from automation import localmap
from automation import mapa as catalog
from automation import runner
from automation import win_mouse

# Tempo para focar a tela do SAP antes da 1ª tecla/clique.
DELAY_INICIO_SEGUNDOS = 5


class App(tk.Tk):
    def __init__(self):
        # type: () -> None
        super(App, self).__init__()
        win_mouse.ensure_dpi_awareness()

        self.title("SAP 800 ATT")
        self.geometry("420x300")
        self.minsize(380, 280)
        self.configure(bg="#f4f4f4")

        self._busy = False
        self._cancel_run = False

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
        tk.Label(
            row_texto,
            text="Batch / texto (tela por enquanto; depois Excel)",
            bg="#f4f4f4",
        ).pack(anchor="w")
        self.texto_var = tk.StringVar()
        self.entry_texto = tk.Entry(row_texto, textvariable=self.texto_var, width=38)
        self.entry_texto.pack(anchor="w", pady=2)

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

        runner.set_user_action_handler(self._ask_user_action)

    def _ask_user_action(self, passo):
        # type: (dict) -> bool
        """Chamado pela thread do runner; mostra dialog na thread do Tk."""
        done = threading.Event()
        result = {"ok": False}
        nome = passo.get("nome") or passo.get("id")
        obs = (passo.get("obs") or "").strip()
        msg = obs or "Faça a ação necessária e clique em OK para continuar."

        def mostrar():
            try:
                self.attributes("-topmost", True)
                self.lift()
                result["ok"] = bool(
                    messagebox.askokcancel(
                        "Ação do usuário",
                        "{}\n\n{}".format(nome, msg),
                        parent=self,
                    )
                )
            finally:
                done.set()

        self.after(0, mostrar)
        done.wait()
        return bool(result["ok"])

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
        # type: (bool, Optional[str]) -> None
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

    def _parte_precisa_texto(self, parte):
        # type: (str) -> bool
        try:
            passos = catalog.passos_da_parte(parte)
        except Exception:
            return False
        return any(str(p.get("kind") or "") in ("paste", "click_and_type") for p in passos)

    def _on_iniciar(self):
        # type: () -> None
        if self._busy:
            return
        try:
            parte = self._parte_selecionada()
        except Exception as exc:
            messagebox.showerror("Iniciar", str(exc))
            return

        texto = (self.texto_var.get() or "").strip()
        if self._parte_precisa_texto(parte) and not texto:
            messagebox.showerror(
                "Iniciar",
                "Preencha o campo Batch / texto antes de iniciar.\n"
                "(Por enquanto vem da tela; depois virá do Excel.)",
            )
            self.entry_texto.focus_set()
            return

        self._cancel_run = False
        self._set_busy(
            True,
            "Foque o SAP! Começa em {}s…".format(DELAY_INICIO_SEGUNDOS),
        )

        def trabalho():
            try:
                import time

                for resto in range(DELAY_INICIO_SEGUNDOS, 0, -1):
                    if self._cancel_run:
                        self.after(0, lambda: self._set_busy(False, "Cancelado."))
                        return
                    self.after(
                        0,
                        lambda r=resto: self.status.config(
                            text="Foque o SAP! Começa em {}s…".format(r)
                        ),
                    )
                    time.sleep(1)
                if self._cancel_run:
                    self.after(0, lambda: self._set_busy(False, "Cancelado."))
                    return
                self.after(0, lambda: self.status.config(text="Rodando '{}'…".format(parte)))
                n = runner.executar_parte(parte, texto=texto if texto else None)
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
