"""CLI no terminal — erros e traceback aparecem no console."""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from typing import List, Optional

from automation import localmap
from automation import mapa as catalog
from automation import runner
from automation import win_mouse
from automation.app_ui import DELAY_FOCO_SAP_SEGUNDOS


def _countdown(segundos, label):
    # type: (int, str) -> None
    for resto in range(segundos, 0, -1):
        print("[{}] Foque o SAP! Comeca em {}s...".format(label, resto), flush=True)
        time.sleep(1)


def _contexto(batch, issuer):
    # type: (Optional[str], Optional[str]) -> dict
    ctx = {}
    if batch and str(batch).strip():
        ctx["batch"] = str(batch).strip()
    if issuer and str(issuer).strip():
        ctx["issuer_id"] = str(issuer).strip()
    return ctx


def _carregar_excel_se_pedido(args):
    # type: (argparse.Namespace) -> dict
    """
    Se --excel: pega 1a linha Status=Pendente.
    --batch / --issuer manuais sobrescrevem o Excel.
    """
    usar_excel = bool(getattr(args, "excel", False) or getattr(args, "excel_path", None))
    ctx = _contexto(getattr(args, "batch", None), getattr(args, "issuer", None))
    if not usar_excel:
        return ctx

    from automation.excel_fila import primeira_pendente

    caminho = getattr(args, "excel_path", None) or None
    linha = primeira_pendente(caminho)
    print("Excel:", linha.caminho.name)
    print("  linha:", linha.linha, "Status:", linha.status)
    print("  Batch:", linha.batch)
    print("  Issuer Id:", linha.issuer_id)
    if linha.total_value:
        print("  Total Value:", linha.total_value)

    excel_ctx = linha.to_contexto()
    # Manual ganha do Excel se informado
    if ctx.get("batch"):
        excel_ctx["batch"] = ctx["batch"]
        print("  (batch sobrescrito por --batch)")
    if ctx.get("issuer_id"):
        excel_ctx["issuer_id"] = ctx["issuer_id"]
        print("  (issuer sobrescrito por --issuer)")
    return excel_ctx


def cmd_listar(_args):
    # type: (argparse.Namespace) -> int
    print("Partes:", ", ".join(catalog.listar_partes()))
    print("Fluxo:", " -> ".join(catalog.listar_fluxo()))
    print()
    for nome in catalog.listar_fluxo():
        faltam = localmap.ids_faltando(nome)
        status = "OK" if not faltam else "FALTA MAPEAR: " + ", ".join(faltam)
        print("  [{}] {}".format(nome, status))
    return 0


def cmd_excel(args):
    # type: (argparse.Namespace) -> int
    from automation.excel_fila import primeira_pendente, resolver_arquivo_excel

    path = resolver_arquivo_excel(args.excel_path)
    print("Arquivo:", path)
    linha = primeira_pendente(path)
    print("Proxima Pendente:")
    print("  linha:", linha.linha)
    print("  Status:", linha.status)
    print("  Batch:", linha.batch)
    print("  Issuer Id:", linha.issuer_id)
    print("  Total Value:", linha.total_value)
    return 0


def cmd_fluxo(args):
    # type: (argparse.Namespace) -> int
    ctx = _carregar_excel_se_pedido(args)
    fluxo = catalog.listar_fluxo()
    if "abrir_batch" in fluxo and not ctx.get("batch"):
        print(
            "ERRO: informe --batch ou use --excel (Status=Pendente).",
            file=sys.stderr,
        )
        return 2
    if "abrir_oj1b1n" in fluxo and not ctx.get("issuer_id"):
        print(
            "ERRO: informe --issuer ou use --excel (Status=Pendente).",
            file=sys.stderr,
        )
        return 2

    print("Fluxo:", " -> ".join(fluxo))
    print("Batch:", ctx.get("batch"))
    print("Issuer Id:", ctx.get("issuer_id"))
    _countdown(args.delay, "Fluxo")

    def on_parte(nome):
        print(">>> Rodando parte: {}".format(nome), flush=True)

    resultado = runner.executar_fluxo(texto=None, contexto=ctx, on_parte=on_parte)
    print("OK - fluxo concluido.")
    print("  passos:", resultado.get("_total_passos"))
    print("  filial XML:", resultado.get("recipient_filial"))
    print("  invoice:", resultado.get("invoice"))
    print("  excel linha:", resultado.get("excel_linha"))
    return 0


def cmd_parte(args):
    # type: (argparse.Namespace) -> int
    ctx = _carregar_excel_se_pedido(args)
    nome = args.parte
    print("Parte:", nome)
    print("Contexto batch/issuer:", ctx.get("batch"), ctx.get("issuer_id"))
    faltam = localmap.ids_faltando(nome)
    if faltam:
        print("ERRO: faltam coordenadas. Use mapear {}.".format(nome), file=sys.stderr)
        for f in faltam:
            print("  -", f, file=sys.stderr)
        return 2
    _countdown(args.delay, "Parte")
    print(">>> Rodando parte: {}".format(nome), flush=True)
    n = runner.executar_parte(nome, texto=None, contexto=ctx)
    print("OK - {} passo(s).".format(n))
    return 0


def cmd_mapear(args):
    # type: (argparse.Namespace) -> int
    ctx = _carregar_excel_se_pedido(args)
    nome = args.parte
    print("Mapear parte:", nome)
    print("Remapear tudo:", bool(args.remapear_tudo))
    print("Contexto batch/issuer:", ctx.get("batch"), ctx.get("issuer_id"))
    _countdown(args.delay, "Mapear")
    gravados, total = localmap.mapear_parte(
        nome,
        remapear_tudo=bool(args.remapear_tudo),
        texto=None,
        contexto=ctx,
    )
    print("OK - mapear: {} novo(s) / {} clique(s).".format(gravados, total))
    return 0


def _add_run_args(parser):
    # type: (argparse.ArgumentParser) -> None
    parser.add_argument(
        "--delay",
        type=int,
        default=DELAY_FOCO_SAP_SEGUNDOS,
        help="Segundos para focar o SAP (padrao: {})".format(DELAY_FOCO_SAP_SEGUNDOS),
    )
    parser.add_argument("--batch", default=None, help="Batch manual (sobrescreve Excel)")
    parser.add_argument(
        "--issuer", default=None, help="Issuer Id manual (sobrescreve Excel)"
    )
    parser.add_argument(
        "--excel",
        action="store_true",
        help="Usa a 1a linha com Status=Pendente da pasta excel/",
    )
    parser.add_argument(
        "--excel-path",
        default=None,
        help="Caminho de um .xlsx (implica leitura da fila Pendente)",
    )


def build_parser():
    # type: () -> argparse.ArgumentParser
    p = argparse.ArgumentParser(
        description="SAP 800 ATT - terminal (erros e traceback no console)."
    )

    sub = p.add_subparsers(dest="cmd")

    s_list = sub.add_parser("listar", help="Lista partes, fluxo e pontos faltando")
    s_list.set_defaults(func=cmd_listar)

    s_excel = sub.add_parser("excel", help="Mostra a proxima linha Status=Pendente")
    s_excel.add_argument("--excel-path", default=None, help="Caminho do .xlsx")
    s_excel.set_defaults(func=cmd_excel)

    s_fluxo = sub.add_parser("fluxo", help="Roda o fluxo completo")
    _add_run_args(s_fluxo)
    s_fluxo.set_defaults(func=cmd_fluxo)

    s_parte = sub.add_parser("parte", help="Roda uma parte")
    s_parte.add_argument("parte", help="Nome da parte (ex.: abrir_batch)")
    _add_run_args(s_parte)
    s_parte.set_defaults(func=cmd_parte)

    s_map = sub.add_parser("mapear", help="Mapeia uma parte (roda o fluxo e pede cliques)")
    s_map.add_argument("parte", help="Nome da parte")
    s_map.add_argument(
        "--remapear-tudo",
        action="store_true",
        help="Ignora pontos ja gravados e remapeia",
    )
    _add_run_args(s_map)
    s_map.set_defaults(func=cmd_mapear)

    return p


def run_cli(argv=None):
    # type: (Optional[List[str]]) -> int
    win_mouse.ensure_dpi_awareness()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0

    try:
        return int(args.func(args))
    except Exception as exc:
        print()
        print("========== ERRO ==========", file=sys.stderr)
        print(type(exc).__name__ + ":", exc, file=sys.stderr)
        print("---------- traceback ----------", file=sys.stderr)
        traceback.print_exc()
        print("===========================", file=sys.stderr)
        return 1
