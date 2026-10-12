"""
Fila do Excel: primeira linha com Status = Pendente.

Colunas por nome do cabeçalho (não pela letra):
  Status | Batch | Issuer Id | Total Value
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

ROOT = Path(__file__).resolve().parent.parent
EXCEL_DIR = ROOT / "excel"

STATUS_ALVO = "pendente"

# Nomes aceitos no cabeçalho (case-insensitive)
COL_STATUS = ("status",)
COL_BATCH = ("batch",)
COL_ISSUER = ("issuer id", "issuer_id", "issuerid")
COL_TOTAL = ("total value", "total_value", "totalvalue")
COL_CBS_IBS = ("cbs/ibs", "cbs ibs", "cbs_ibs", "cbsibs")


@dataclass
class LinhaFila:
    caminho: Path
    linha: int  # 1-based na planilha
    status: str
    batch: str
    issuer_id: str
    total_value: Optional[str] = None
    cbs_ibs: Optional[str] = None

    def to_contexto(self):
        # type: () -> dict
        ctx = {
            "batch": self.batch,
            "issuer_id": self.issuer_id,
            "excel_linha": self.linha,
            "excel_arquivo": str(self.caminho),
            "excel_status": self.status,
            "cbs_ibs": self.cbs_ibs or "",
        }
        if self.total_value is not None:
            ctx["excel_total_value"] = self.total_value
        return ctx


def _norm_header(valor):
    # type: (object) -> str
    if valor is None:
        return ""
    return " ".join(str(valor).strip().lower().split())


def _cell_str(valor):
    # type: (object) -> str
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, float):
        if valor == int(valor):
            return str(int(valor))
        return str(valor).strip()
    if isinstance(valor, int):
        return str(valor)
    return str(valor).strip()


def _achar_coluna(headers, candidatos):
    # type: (List[str], tuple) -> Optional[int]
    for i, h in enumerate(headers):
        if h in candidatos:
            return i
    return None


def resolver_arquivo_excel(caminho=None):
    # type: (Union[str, Path, None]) -> Path
    if caminho:
        p = Path(caminho)
        if not p.is_file():
            raise FileNotFoundError("Excel nao encontrado: {}".format(p))
        return p

    if not EXCEL_DIR.is_dir():
        raise FileNotFoundError("Pasta excel/ nao existe: {}".format(EXCEL_DIR))

    candidatos = sorted(
        list(EXCEL_DIR.glob("*.xlsx")) + list(EXCEL_DIR.glob("*.XLSX")),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    # Evita duplicata case-insensitive no Windows
    vistos = set()
    unicos = []
    for c in candidatos:
        key = str(c.resolve()).lower()
        if key in vistos:
            continue
        vistos.add(key)
        unicos.append(c)

    if not unicos:
        raise FileNotFoundError(
            "Nenhum .xlsx em {}. Coloque a planilha la.".format(EXCEL_DIR)
        )
    return unicos[0]


def primeira_pendente(caminho=None):
    # type: (Union[str, Path, None]) -> LinhaFila
    """
    Retorna a primeira linha cujo Status (normalizado) == 'pendente'.
    Nao pega 'Enviados ... pendente revisao' — so Status exatamente Pendente.
    """
    import openpyxl

    path = resolver_arquivo_excel(caminho)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            header_row = next(rows)
        except StopIteration:
            raise RuntimeError("Planilha vazia: {}".format(path))

        headers = [_norm_header(h) for h in header_row]
        i_status = _achar_coluna(headers, COL_STATUS)
        i_batch = _achar_coluna(headers, COL_BATCH)
        i_issuer = _achar_coluna(headers, COL_ISSUER)
        i_total = _achar_coluna(headers, COL_TOTAL)
        i_cbs = _achar_coluna(headers, COL_CBS_IBS)

        faltando = []
        if i_status is None:
            faltando.append("Status")
        if i_batch is None:
            faltando.append("Batch")
        if i_issuer is None:
            faltando.append("Issuer Id")
        if faltando:
            raise RuntimeError(
                "Cabecalhos nao encontrados em {}: {}. "
                "Cabecalhos lidos: {}".format(
                    path.name, ", ".join(faltando), ", ".join(headers[:25])
                )
            )

        for num, row in enumerate(rows, start=2):
            if row is None:
                continue
            status = _cell_str(row[i_status] if i_status < len(row) else None)
            if status.lower() != STATUS_ALVO:
                continue
            batch = _cell_str(row[i_batch] if i_batch < len(row) else None)
            issuer = _cell_str(row[i_issuer] if i_issuer < len(row) else None)
            if not batch:
                raise RuntimeError(
                    "Linha {} Status=Pendente sem Batch em {}.".format(num, path.name)
                )
            if not issuer:
                raise RuntimeError(
                    "Linha {} Status=Pendente sem Issuer Id em {}.".format(
                        num, path.name
                    )
                )
            total = None
            if i_total is not None and i_total < len(row):
                total = _cell_str(row[i_total]) or None
            cbs = None
            if i_cbs is not None and i_cbs < len(row):
                cbs = _cell_str(row[i_cbs]) or None
            return LinhaFila(
                caminho=path,
                linha=num,
                status=status,
                batch=batch,
                issuer_id=issuer,
                total_value=total,
                cbs_ibs=cbs,
            )
    finally:
        wb.close()

    raise RuntimeError(
        "Nenhuma linha com Status='Pendente' em {}.".format(path.name)
    )
