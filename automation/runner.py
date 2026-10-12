"""Executa os passos de uma parte (teclado, cliques mapeados, ação do usuário)."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

import tkinter as tk
from tkinter import messagebox, simpledialog

from automation import abort
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
    2) passo['text_from'] no contexto — só essa chave (batch ≠ issuer_id)
    3) se pedir_se_faltar (Mapear): pergunta na UI pela chave text_from
    4) legado: parâmetro texto só se NÃO houver text_from
    """
    pid = passo.get("id")
    fixo = passo.get("text")
    if fixo is not None and str(fixo) != "":
        return str(fixo)

    tf = (passo.get("text_from") or "").strip()
    ctx = contexto or {}
    if tf:
        if tf in ctx and ctx[tf] is not None and str(ctx[tf]).strip() != "":
            return str(ctx[tf]).strip()
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
            # Guarda no contexto para não pedir de novo / não misturar com outro campo
            ctx[tf] = str(valor).strip()
            return str(valor).strip()
        raise RuntimeError(
            "Passo '{}' espera contexto['{}'] "
            "(Batch→batch, Issuer Id→issuer_id; não misturar)."
            .format(pid, tf)
        )

    # Sem text_from: só então usa o parâmetro legado `texto`
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
        hold = float(passo["hold"]) if passo.get("hold") is not None else 0.06
        if len(lista) == 1 and repeat > 1:
            teclado.pressionar(lista[0], vezes=repeat, pausa=pausa, hold=hold)
        else:
            teclado.pressionar_lista(lista, pausa=pausa, hold=hold)
        return

    if kind == "hotkey":
        lista = list(passo.get("keys") or [])
        if len(lista) < 2:
            raise RuntimeError("Passo '{}' kind=hotkey precisa de 2+ teclas.".format(pid))
        teclado.hotkey(lista, pausa=_pausa_do_passo(passo, 0.08))
        return

    if kind in ("paste", "type"):
        # Digita caractere a caractere (Ctrl+V costuma falhar no SAP nesta máquina).
        valor = _resolver_texto(passo, texto=texto, contexto=contexto, pedir_se_faltar=pedir_texto)
        teclado.digitar_texto(valor)
        return

    if kind == "user_action":
        _pedir_acao_usuario(passo)
        return

    if kind == "map_only":
        # Calibração: XY só no Mapear; no fluxo não clica.
        return

    if kind == "fill_itens":
        from automation import itens_oj1b1n

        itens_oj1b1n.executar_preenchimento(contexto, pontos, passo=passo)
        return

    if kind == "fill_taxes":
        from automation import taxes_oj1b1n

        taxes_oj1b1n.executar_preenchimento(contexto, pontos, passo=passo)
        return

    if kind == "verify_valor":
        from automation import valor_check

        valor_check.verificar_valor(contexto, pontos, passo=passo)
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
            teclado.digitar_texto(valor)
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
        abort.check()
        catalog.validar_passo(passo)
        _executar_passo(passo, texto, pontos, contexto=contexto, pedir_texto=False)
        executados += 1
        abort.sleep(pausa_depois_do_passo(passo, pausa_entre))

    return executados


def _apos_parte(nome_parte, contexto):
    # type: (str, Dict[str, Any]) -> None
    """Ganchos após cada parte do fluxo (ex.: parse do XML no clipboard)."""
    if nome_parte == "pegar_xml":
        from automation.xml_nfe import parse_nfe_clipboard

        dados = parse_nfe_clipboard()
        invoice_digitos = "".join(c for c in str(dados.invoice or "") if c.isdigit())
        serie_digitos = "".join(c for c in str(dados.serie or "") if c.isdigit())
        contexto["recipient_filial"] = dados.recipient_filial
        contexto["recipient_sufixo"] = dados.recipient_sufixo
        contexto["invoice"] = dados.invoice
        contexto["invoice_9"] = invoice_digitos.zfill(9)  # 3319 → 000003319
        contexto["serie"] = dados.serie
        contexto["serie_3"] = serie_digitos.zfill(3)  # 4 → 004
        contexto["valor"] = dados.valor
        contexto["valor_fmt"] = dados.valor_fmt
        contexto["cfop"] = dados.cfop
        contexto["chave_acesso"] = dados.chave_acesso
        contexto["protocol_number"] = dados.protocol_number
        contexto["protocol_date"] = dados.protocol_date
        contexto["protocol_time"] = dados.protocol_time
        contexto["protocol_line"] = dados.protocol_line
        contexto["issue_date"] = dados.issue_date
        # Random No + DV: últimos 9 dígitos da chave → 8 + 1 (ex.: …140033194 → 14003319 / 4)
        chave_dig = "".join(c for c in str(dados.chave_acesso or "") if c.isdigit())
        if len(chave_dig) >= 9:
            contexto["random_no"] = chave_dig[-9:-1]
            contexto["random_dv"] = chave_dig[-1]
        else:
            contexto["random_no"] = ""
            contexto["random_dv"] = ""
        contexto["itens"] = list(dados.itens)
        contexto["_nfe"] = dados


def executar_fluxo(texto=None, contexto=None, pausa_entre=0.35, on_parte=None):
    # type: (Optional[str], Optional[Dict[str, Any]], float, Optional[Callable]) -> Dict[str, Any]
    """
    Roda o fluxo completo na ordem de mapa_passos.json → 'fluxo'.
    Novas partes: basta acrescentar o nome em 'fluxo'.
    Retorna o contexto acumulado (XML parseado, etc.).

    Batch e Issuer Id só via contexto['batch'] e contexto['issuer_id']
    (o parâmetro texto, se vier, só preenche batch se ainda não existir).
    """
    win_mouse.ensure_dpi_awareness()
    fluxo = catalog.listar_fluxo()
    ctx = dict(contexto or {})

    # Garante batch no contexto sem sobrescrever issuer_id
    if texto is not None and str(texto).strip():
        if not str(ctx.get("batch") or "").strip():
            ctx["batch"] = str(texto).strip()

    for nome in fluxo:
        faltam = localmap.ids_faltando(nome)
        if faltam:
            raise RuntimeError(
                "Parte '{}': faltam coordenadas. Use Mapear nessa parte.\n  - {}".format(
                    nome, "\n  - ".join(faltam)
                )
            )

    total_passos = 0
    for nome in fluxo:
        abort.check()
        if on_parte is not None:
            on_parte(nome)
        # Não passa mais `texto` solto — evita colar batch/issuer no campo errado
        n = executar_parte(nome, texto=None, pausa_entre=pausa_entre, contexto=ctx)
        total_passos += n
        _apos_parte(nome, ctx)

    ctx["_fluxo"] = fluxo
    ctx["_total_passos"] = total_passos
    return ctx
