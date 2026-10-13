"""
Fila Excel: processa todos Status=Pendente em loop.

Ao sucesso: fluxo já inclui salvar_e_fechar → Status=A-enviado → próximo.
Ao erro: Status=A-erro → Alt+F4 + balança + X (sem salvar) → próximo.
Parar (verificação): grava o motivo no Status e encerra a fila.
Esc: para a fila (não altera Status se ainda Pendente).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from automation import abort
from automation import localmap
from automation import runner
from automation import teclado
from automation import win_mouse
from automation.excel_fila import (
    STATUS_ERRO,
    STATUS_OK,
    atualizar_status,
    primeira_pendente,
    resolver_arquivo_excel,
)
from automation.verificacao import VerificacaoCancelada

ID_BALANCA = "salvar_e_fechar.clique_balanca"
ID_X = "salvar_e_fechar.clique_x"


def _clique_id(pontos, pid, pausa_depois=1.2):
    # type: (dict, str, float) -> None
    abort.check()
    x, y = localmap.garantir_xy(pid, pontos, passo={"id": pid, "nome": pid})
    win_mouse.click(int(x), int(y))
    abort.sleep(float(pausa_depois))


def fechar_apos_erro(pontos=None):
    # type: (Optional[dict]) -> None
    """
    Sem salvar: Alt+F4 → balança → X (mesmos pontos de salvar_e_fechar).
    Usado quando o fluxo quebrou no meio e ainda precisa limpar a tela.
    """
    pts = pontos if pontos is not None else localmap.load_pontos()
    abort.check()
    teclado.hotkey(["alt", "f4"], pausa=0.15, hold=0.08)
    abort.sleep(1.2)
    _clique_id(pts, ID_BALANCA, pausa_depois=1.2)
    _clique_id(pts, ID_X, pausa_depois=2.0)


# Nome antigo (imports / docs): agora fecha sem o clique de foco
def fechar_janela_e_focar(pontos=None):
    # type: (Optional[dict]) -> None
    fechar_apos_erro(pontos)


def _marcar(caminho, linha, status):
    # type: (Any, Any, str) -> None
    if not caminho or not linha:
        return
    atualizar_status(caminho, int(linha), status)


def executar_fila(
    caminho_excel=None,
    pausa_entre=0.35,
    on_item=None,
    on_parte=None,
    max_itens=None,
):
    # type: (Optional[str], float, Optional[Callable], Optional[Callable], Optional[int]) -> Dict[str, Any]
    """
    Loop: pega 1a Pendente → fluxo completo (inclui salvar_e_fechar) → marca status → próximo.
    Retorna resumo {ok, erro, abortado, parado, processados}.
    """
    path = resolver_arquivo_excel(caminho_excel)
    pontos = localmap.load_pontos()
    # Pontos faltantes: pedidos na hora (botão do meio) ao chegar no clique.

    ok = 0
    erro = 0
    processados = []  # type: List[dict]
    abortado = False
    parado = False
    motivo_parar = None  # type: Optional[str]

    n = 0
    while True:
        if max_itens is not None and n >= int(max_itens):
            break
        abort.check()
        try:
            linha = primeira_pendente(path)
        except RuntimeError:
            break

        n += 1
        ctx = linha.to_contexto()
        if on_item is not None:
            on_item(linha, n)

        item_info = {
            "linha": linha.linha,
            "batch": linha.batch,
            "issuer_id": linha.issuer_id,
            "status": None,
            "erro": None,
        }
        try:
            resultado = runner.executar_fluxo(
                texto=None,
                contexto=ctx,
                pausa_entre=pausa_entre,
                on_parte=on_parte,
            )
            # Fluxo completo já salvou e fechou (salvar_e_fechar)
            _marcar(linha.caminho, linha.linha, STATUS_OK)
            item_info["status"] = STATUS_OK
            item_info["invoice"] = resultado.get("invoice")
            ok += 1
        except abort.AbortError:
            abortado = True
            item_info["status"] = "abortado"
            item_info["erro"] = "Esc"
            processados.append(item_info)
            break
        except VerificacaoCancelada as exc:
            # Parar: grava o motivo no Status e encerra a fila (não segue)
            parado = True
            motivo_parar = exc.motivo
            item_info["status"] = exc.motivo
            item_info["erro"] = "Parar: {}".format(exc.motivo)
            try:
                _marcar(linha.caminho, linha.linha, exc.motivo)
            except Exception as exc_mark:
                item_info["erro_mark"] = str(exc_mark)
            processados.append(item_info)
            break
        except Exception as exc:
            erro += 1
            item_info["status"] = STATUS_ERRO
            item_info["erro"] = str(exc)
            try:
                _marcar(linha.caminho, linha.linha, STATUS_ERRO)
            except Exception as exc_mark:
                item_info["erro_mark"] = str(exc_mark)
            try:
                fechar_apos_erro(pontos)
            except abort.AbortError:
                abortado = True
                processados.append(item_info)
                break
            except Exception:
                pass

        processados.append(item_info)
        abort.sleep(0.5)

    return {
        "ok": ok,
        "erro": erro,
        "abortado": abortado,
        "parado": parado,
        "motivo_parar": motivo_parar,
        "processados": processados,
        "excel": str(path),
    }
