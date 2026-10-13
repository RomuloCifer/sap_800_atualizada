"""Tela simples: Iniciar tudo / Iniciar parte / Mapear."""

from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from automation import abort
from automation import localmap
from automation import mapa as catalog
from automation import runner
from automation import win_mouse

# Tempo para focar a tela do SAP antes da 1ª tecla/clique.
DELAY_FOCO_SAP_SEGUNDOS = 3


class App(tk.Tk):
    def __init__(self):
        # type: () -> None
        super(App, self).__init__()
        win_mouse.ensure_dpi_awareness()

        self.title("SAP 800 ATT")
        self.geometry("460x470")
        self.minsize(420, 450)
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
            text="Parte (Mapear / Iniciar só esta)",
            font=("Segoe UI", 9),
            bg="#f4f4f4",
        ).pack(anchor="w", padx=16)

        self.parte_var = tk.StringVar()
        self.combo = ttk.Combobox(
            self, textvariable=self.parte_var, state="readonly", width=38
        )
        self.combo.pack(anchor="w", **pad)
        self._recarregar_partes()

        row_batch = tk.Frame(self, bg="#f4f4f4")
        row_batch.pack(fill="x", padx=16, pady=2)
        tk.Label(
            row_batch,
            text="Batch (depois: Excel col. D)",
            bg="#f4f4f4",
        ).pack(anchor="w")
        self.texto_var = tk.StringVar()
        self.entry_texto = tk.Entry(row_batch, textvariable=self.texto_var, width=40)
        self.entry_texto.pack(anchor="w", pady=2)

        row_issuer = tk.Frame(self, bg="#f4f4f4")
        row_issuer.pack(fill="x", padx=16, pady=2)
        tk.Label(
            row_issuer,
            text="Issuer Id (depois: Excel col. R)",
            bg="#f4f4f4",
        ).pack(anchor="w")
        self.issuer_var = tk.StringVar()
        self.entry_issuer = tk.Entry(row_issuer, textvariable=self.issuer_var, width=40)
        self.entry_issuer.pack(anchor="w", pady=2)

        self.excel_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self,
            text="Usar Excel (Status = Pendente)",
            variable=self.excel_var,
            bg="#f4f4f4",
            activebackground="#f4f4f4",
        ).pack(anchor="w", padx=16, pady=2)

        self.fila_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self,
            text="Fila: um atrás do outro (com verificação OK entre etapas)",
            variable=self.fila_var,
            bg="#f4f4f4",
            activebackground="#f4f4f4",
        ).pack(anchor="w", padx=16, pady=2)

        self.remapear_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self,
            text="Remapear tudo (ignora pontos já gravados)",
            variable=self.remapear_var,
            bg="#f4f4f4",
            activebackground="#f4f4f4",
        ).pack(anchor="w", padx=16, pady=2)

        btns = tk.Frame(self, bg="#f4f4f4")
        btns.pack(fill="x", padx=16, pady=8)

        self.btn_fluxo = tk.Button(
            btns,
            text="Iniciar tudo",
            width=14,
            height=2,
            command=self._on_iniciar_fluxo,
        )
        self.btn_fluxo.pack(side="left", padx=(0, 6))

        self.btn_iniciar = tk.Button(
            btns,
            text="Iniciar parte",
            width=12,
            height=2,
            command=self._on_iniciar,
        )
        self.btn_iniciar.pack(side="left", padx=(0, 6))

        self.btn_mapear = tk.Button(
            btns,
            text="Mapear",
            width=10,
            height=2,
            command=self._on_mapear,
        )
        self.btn_mapear.pack(side="left")

        fluxo_txt = ""
        try:
            fluxo_txt = " → ".join(catalog.listar_fluxo())
        except Exception:
            fluxo_txt = "(defina 'fluxo' no mapa_passos.json)"

        self.status = tk.Label(
            self,
            text="Fluxo: {}\nContagem de {}s antes de rodar.\nEsc = parar a automacao (mesmo com SAP em foco).".format(
                fluxo_txt, DELAY_FOCO_SAP_SEGUNDOS
            ),
            font=("Segoe UI", 9),
            fg="#333333",
            bg="#f4f4f4",
            wraplength=400,
            justify="left",
        )
        self.status.pack(anchor="w", padx=16, pady=(4, 12))

        runner.set_user_action_handler(self._ask_user_action)

    def _ask_user_action(self, passo):
        # type: (dict) -> object
        """Retorna True (OK) ou (False, motivo) se Parar."""
        from automation.verificacao import dialogo_verificacao

        done = threading.Event()
        result = {"ok": False, "motivo": None}
        nome = passo.get("nome") or passo.get("id")
        obs = (passo.get("obs") or "").strip()
        msg = obs or "Confira a tela e clique em OK para continuar."

        def mostrar():
            try:
                ok, motivo = dialogo_verificacao(self, str(nome), msg)
                result["ok"] = ok
                result["motivo"] = motivo
            finally:
                done.set()

        self.after(0, mostrar)
        done.wait()
        if result["ok"]:
            return True
        return (False, result["motivo"])

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
        self.btn_fluxo.config(state=state)
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

    def _parte_precisa_batch(self, parte):
        # type: (str) -> bool
        try:
            passos = catalog.passos_da_parte(parte)
        except Exception:
            return False
        return any(
            (str(p.get("kind") or "") in ("paste", "click_and_type", "type"))
            and (p.get("text_from") == "batch" or (not p.get("text") and not p.get("text_from") and str(p.get("kind")) == "paste"))
            for p in passos
        )

    def _countdown_thread_msgs(self, label):
        # type: (str) -> bool
        for resto in range(DELAY_FOCO_SAP_SEGUNDOS, 0, -1):
            if self._cancel_run or win_mouse.escape_pressed():
                return False
            self.after(
                0,
                lambda r=resto: self.status.config(
                    text="[{}] Foque o SAP! Começa em {}s… (Esc = parar)".format(
                        label, r
                    )
                ),
            )
            # Sleep em fatias para reagir ao Esc
            fim = time.time() + 1.0
            while time.time() < fim:
                if self._cancel_run or win_mouse.escape_pressed():
                    return False
                time.sleep(0.05)
        return not self._cancel_run

    def _countdown_foco_sap(self, contexto):
        # type: (str) -> bool
        for resto in range(DELAY_FOCO_SAP_SEGUNDOS, 0, -1):
            if self._cancel_run or win_mouse.escape_pressed():
                self._set_busy(False, "Cancelado (Esc).")
                return False
            self.status.config(
                text="[{}] Foque o SAP! Começa em {}s… (Esc = parar)".format(
                    contexto, resto
                )
            )
            self.update()
            fim = time.time() + 1.0
            while time.time() < fim:
                if self._cancel_run or win_mouse.escape_pressed():
                    self._set_busy(False, "Cancelado (Esc).")
                    return False
                time.sleep(0.05)
                self.update()
        return True

    def _contexto_base(self, usar_excel=False):
        # type: (bool) -> dict
        """
        Batch e Issuer Id em chaves separadas — nunca misturar.
        Se usar_excel: preenche pela 1a linha Status=Pendente (campos manuais sobrescrevem).
        """
        ctx = {}
        if usar_excel:
            from automation.excel_fila import primeira_pendente

            linha = primeira_pendente()
            ctx.update(linha.to_contexto())
            self.texto_var.set(linha.batch)
            self.issuer_var.set(linha.issuer_id)

        batch = (self.texto_var.get() or "").strip()
        issuer = (self.issuer_var.get() or "").strip()
        if batch:
            ctx["batch"] = batch
        if issuer:
            ctx["issuer_id"] = issuer
        return ctx

    def _on_mapear(self):
        # type: () -> None
        if self._busy:
            return
        try:
            parte = self._parte_selecionada()
        except Exception as exc:
            messagebox.showerror("Mapear", str(exc))
            return

        try:
            ctx = self._contexto_base(usar_excel=bool(self.excel_var.get()))
        except Exception as exc:
            messagebox.showerror("Mapear", str(exc))
            return
        if self._parte_precisa_batch(parte) and not ctx.get("batch"):
            messagebox.showerror(
                "Mapear",
                "Preencha o Batch ou marque Usar Excel.",
            )
            self.entry_texto.focus_set()
            return

        remapear = bool(self.remapear_var.get())
        self._cancel_run = False
        self._set_busy(True, "Mapear '{}'…".format(parte))
        self.update_idletasks()

        if not self._countdown_foco_sap("Mapear"):
            return

        self.status.config(text="Mapeando '{}': rodando passos…".format(parte))
        self.update_idletasks()
        try:
            gravados, total = localmap.mapear_parte(
                parte,
                remapear_tudo=remapear,
                texto=None,
                contexto=ctx,
            )
            msg = (
                "Mapear ok: {} novo(s) / {} clique(s) em '{}'.".format(
                    gravados, total, parte
                )
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
            messagebox.showerror("Iniciar parte", str(exc))
            return

        try:
            ctx = self._contexto_base(usar_excel=bool(self.excel_var.get()))
        except Exception as exc:
            messagebox.showerror("Iniciar parte", str(exc))
            return
        if self._parte_precisa_batch(parte) and not ctx.get("batch"):
            messagebox.showerror(
                "Iniciar parte",
                "Preencha o Batch ou marque Usar Excel.",
            )
            self.entry_texto.focus_set()
            return

        self._cancel_run = False
        self._set_busy(True, "Iniciar parte…")

        def trabalho():
            try:
                if not self._countdown_thread_msgs("Parte"):
                    self.after(0, lambda: self._set_busy(False, "Cancelado."))
                    return
                self.after(
                    0, lambda: self.status.config(text="Rodando '{}'… (Esc = parar)".format(parte))
                )
                with abort.sessao():
                    n = runner.executar_parte(parte, texto=None, contexto=ctx)
                msg = "Concluído: {} passo(s) em '{}'.".format(n, parte)
                self.after(0, lambda: self._fim_ok(msg))
            except abort.AbortError as exc:
                self.after(0, lambda: self._fim_abort(str(exc)))
            except Exception as exc:
                from automation.verificacao import VerificacaoCancelada

                if isinstance(exc, VerificacaoCancelada):
                    try:
                        from automation.excel_fila import marcar_resultado_do_contexto

                        marcar_resultado_do_contexto(
                            ctx, False, status_custom=exc.motivo
                        )
                    except Exception:
                        pass
                    msg_parar = "Parado: {}".format(exc.motivo)
                    self.after(0, lambda m=msg_parar: self._fim_abort(m))
                    return
                self.after(0, lambda: self._fim_erro("Iniciar parte", str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _on_iniciar_fluxo(self):
        # type: () -> None
        if self._busy:
            return
        try:
            fluxo = catalog.listar_fluxo()
        except Exception as exc:
            messagebox.showerror("Iniciar tudo", str(exc))
            return

        usar_excel = bool(self.excel_var.get())
        modo_fila = usar_excel and bool(self.fila_var.get())

        if modo_fila:
            self._iniciar_fila()
            return

        try:
            ctx = self._contexto_base(usar_excel=usar_excel)
        except Exception as exc:
            messagebox.showerror("Iniciar tudo", str(exc))
            return

        if "abrir_batch" in fluxo and not ctx.get("batch"):
            messagebox.showerror(
                "Iniciar tudo",
                "Preencha o Batch ou marque Usar Excel (Status=Pendente).",
            )
            self.entry_texto.focus_set()
            return

        if "abrir_oj1b1n" in fluxo and not ctx.get("issuer_id"):
            messagebox.showerror(
                "Iniciar tudo",
                "Preencha o Issuer Id ou marque Usar Excel (Status=Pendente).",
            )
            self.entry_issuer.focus_set()
            return

        self._cancel_run = False
        self._set_busy(
            True,
            "Iniciar tudo… Batch={} | Issuer={} | CBS/IBS={!r} | excel_linha={}".format(
                ctx.get("batch"),
                ctx.get("issuer_id"),
                ctx.get("cbs_ibs") or "",
                ctx.get("excel_linha") or "-",
            ),
        )

        def trabalho():
            try:
                if not self._countdown_thread_msgs("Fluxo"):
                    self.after(0, lambda: self._set_busy(False, "Cancelado."))
                    return

                def on_parte(nome):
                    self.after(
                        0,
                        lambda n=nome: self.status.config(
                            text="Fluxo: rodando '{}'… (batch={} issuer={})".format(
                                n, ctx.get("batch"), ctx.get("issuer_id")
                            )
                        ),
                    )

                with abort.sessao():
                    resultado = runner.executar_fluxo(
                        texto=None,
                        contexto=ctx,
                        on_parte=on_parte,
                    )
                status_excel = ""
                try:
                    from automation.excel_fila import marcar_resultado_do_contexto

                    st = marcar_resultado_do_contexto(resultado, True)
                    if st:
                        status_excel = "\nExcel Status: {}".format(st)
                except Exception as exc_mark:
                    status_excel = "\n(AVISO: nao gravou Status: {})".format(exc_mark)
                partes = " → ".join(resultado.get("_fluxo") or fluxo)
                msg = (
                    "Fluxo concluído.\n"
                    "Partes: {}\n"
                    "Passos: {}\n"
                    "Filial (XML): {}\n"
                    "Invoice: {}{}"
                ).format(
                    partes,
                    resultado.get("_total_passos"),
                    resultado.get("recipient_filial") or "—",
                    resultado.get("invoice") or "—",
                    status_excel,
                )
                self.after(0, lambda: self._fim_ok(msg))
            except abort.AbortError as exc:
                self.after(0, lambda: self._fim_abort(str(exc)))
            except Exception as exc:
                from automation.verificacao import VerificacaoCancelada
                from automation.xml_nfe import XmlClipboardFalhou

                if isinstance(exc, XmlClipboardFalhou):
                    # Ctrl+C XML falhou: para sem gravar Status
                    msg_xml = "Parado: Ctrl+C do XML falhou.\nStatus no Excel nao foi alterado.\n{}".format(
                        exc
                    )
                    self.after(0, lambda m=msg_xml: self._fim_abort(m))
                    return
                if isinstance(exc, VerificacaoCancelada):
                    aviso = ""
                    try:
                        from automation.excel_fila import marcar_resultado_do_contexto

                        st = marcar_resultado_do_contexto(
                            ctx, False, status_custom=exc.motivo
                        )
                        if st:
                            aviso = "\nExcel Status: {}".format(st)
                    except Exception as exc_mark:
                        aviso = "\n(AVISO: nao gravou Status: {})".format(exc_mark)
                    msg_parar = "Parado pelo usuário.\nMotivo: {}{}".format(
                        exc.motivo, aviso
                    )
                    self.after(0, lambda m=msg_parar: self._fim_abort(m))
                    return
                try:
                    from automation.excel_fila import marcar_resultado_do_contexto

                    marcar_resultado_do_contexto(ctx, False)
                except Exception:
                    pass
                self.after(0, lambda: self._fim_erro("Iniciar tudo", str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _iniciar_fila(self):
        # type: () -> None
        from automation import fila as fila_mod
        from automation.excel_fila import resolver_arquivo_excel

        try:
            path = resolver_arquivo_excel()
        except Exception as exc:
            messagebox.showerror("Fila", str(exc))
            return

        self._cancel_run = False
        self._set_busy(
            True,
            "Fila Excel… {} (Esc = parar). Feche o Excel na planilha.".format(path.name),
        )

        def trabalho():
            try:
                if not self._countdown_thread_msgs("Fila"):
                    self.after(0, lambda: self._set_busy(False, "Cancelado."))
                    return

                def on_item(linha, n):
                    self.after(
                        0,
                        lambda: self.status.config(
                            text="Fila #{} linha={} batch={}… (Esc = parar)".format(
                                n, linha.linha, linha.batch
                            )
                        ),
                    )

                def on_parte(nome):
                    self.after(
                        0,
                        lambda n=nome: self.status.config(
                            text="Fila: parte '{}'… (Esc = parar)".format(n)
                        ),
                    )

                with abort.sessao():
                    resumo = fila_mod.executar_fila(
                        caminho_excel=str(path),
                        on_item=on_item,
                        on_parte=on_parte,
                    )
                msg = (
                    "Fila encerrada.\n"
                    "OK (A-enviado): {}\n"
                    "Erro (A-erro): {}\n"
                    "Parado (motivo no Status): {}\n"
                    "Abortado (Esc): {}\n"
                    "Arquivo: {}"
                ).format(
                    resumo.get("ok"),
                    resumo.get("erro"),
                    resumo.get("motivo_parar") or ("sim" if resumo.get("parado") else "não"),
                    resumo.get("abortado"),
                    path.name,
                )
                if resumo.get("abortado") or resumo.get("parado"):
                    self.after(0, lambda: self._fim_abort(msg))
                else:
                    self.after(0, lambda: self._fim_ok(msg))
            except abort.AbortError as exc:
                self.after(0, lambda: self._fim_abort(str(exc)))
            except Exception as exc:
                self.after(0, lambda: self._fim_erro("Fila", str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _fim_ok(self, msg):
        # type: (str) -> None
        self._set_busy(False, msg)
        messagebox.showinfo("OK", msg)

    def _fim_erro(self, titulo, msg):
        # type: (str, str) -> None
        self._set_busy(False, msg)
        messagebox.showerror(titulo, msg)

    def _fim_abort(self, msg=None):
        # type: (Optional[str]) -> None
        texto = msg or "Automacao interrompida (Esc)."
        self._set_busy(False, texto)
        messagebox.showwarning("Parado", texto)


def run_app():
    # type: () -> None
    app = App()
    app.mainloop()
