"""
Fila Excel: processa todos Status=Pendente em loop.

Ao sucesso: Status=teste_ok → Alt+F4 → clique de foco → próximo.
Ao erro: Status=teste_erro → tenta Alt+F4 + foco → próximo.
Esc: para a fila (não altera Status se ainda Pendente).
"""

from __future__ import annotations

import time
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

ID_FOCO = "entre_batches.clique_foco"


def _clique_foco(pontos=None):
    # type: (Optional[dict]) -> None
    pts = pontos if pontos is not None else localmap.load_pontos()
    item = pts.get(ID_FOCO)
    if not item or "x" not in item or "y" not in item:
        raise RuntimeError(
            "Falta mapear '{}' (parte entre_batches). "
            "Use Mapear nessa parte uma vez.".format(ID_FOCO)
        )
    win_mouse.click(int(item["x"]), int(item["y"]))
    time.sleep(0.35)


def fechar_janela_e_focar(pontos=None):
    # type: (Optional[dict]) -> None
    """Alt+F4 na janela atual + clique para focar o SAP de novo."""
    abort.check()
    teclado.hotkey(["alt", "f4"], pausa=0.15, hold=0.08)
    abort.sleep(0.9)
    abort.check()
    _clique_foco(pontos)


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
    Loop: pega 1a Pendente → fluxo completo → marca status → fecha → próximo.
    Retorna resumo {ok, erro, abortado, processados}.
    """
    path = resolver_arquivo_excel(caminho_excel)
    pontos = localmap.load_pontos()
    if ID_FOCO not in pontos or "x" not in (pontos.get(ID_FOCO) or {}):
        raise RuntimeError(
            "Falta mapear a parte 'entre_batches' (clique de foco após Alt+F4)."
        )

    # valida coordenadas de todas as partes do fluxo uma vez
    from automation import mapa as catalog

    for nome in catalog.listar_fluxo():
        faltam = localmap.ids_faltando(nome)
        if faltam:
            raise RuntimeError(
                "Parte '{}': faltam coordenadas.\n  - {}".format(
                    nome, "\n  - ".join(faltam)
                )
            )

    ok = 0
    erro = 0
    processados = []  # type: List[dict]
    abortado = False

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
            # Se chegou ao fim, a conferência de valor passou
            _marcar(linha.caminho, linha.linha, STATUS_OK)
            item_info["status"] = STATUS_OK
            item_info["invoice"] = resultado.get("invoice")
            ok += 1
            try:
                fechar_janela_e_focar(pontos)
            except abort.AbortError:
                raise
            except Exception as exc_foco:
                # sucesso já marcado; falha ao fechar pode atrapalhar o próximo
                item_info["aviso_foco"] = str(exc_foco)
        except abort.AbortError:
            abortado = True
            item_info["status"] = "abortado"
            item_info["erro"] = "Esc"
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
                fechar_janela_e_focar(pontos)
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
        "processados": processados,
        "excel": str(path),
    }
