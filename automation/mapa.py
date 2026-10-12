"""Leitura do mapa_passos.json (catálogo versionado — sem coordenadas)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation import kinds

ROOT = Path(__file__).resolve().parent.parent
MAP_FILE = ROOT / "mapa_passos.json"


def load_mapa():
    # type: () -> dict
    if not MAP_FILE.is_file():
        raise FileNotFoundError("Arquivo não encontrado: {}".format(MAP_FILE))
    with MAP_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "partes" not in data:
        raise ValueError("mapa_passos.json inválido: falta chave 'partes'.")
    return data


def listar_partes(mapa=None):
    # type: (Optional[dict]) -> List[str]
    data = mapa if mapa is not None else load_mapa()
    return sorted(data.get("partes", {}).keys())


def listar_fluxo(mapa=None):
    # type: (Optional[dict]) -> List[str]
    """
    Ordem do fluxo completo (Iniciar tudo).
    Definido em mapa_passos.json → chave 'fluxo'.
    Partes novas: incluir nessa lista para entrarem no fluxo.
    """
    data = mapa if mapa is not None else load_mapa()
    fluxo = data.get("fluxo")
    if not fluxo:
        raise ValueError(
            "mapa_passos.json sem 'fluxo'. Adicione a lista de partes na ordem, "
            "ex.: [\"abrir_batch\", \"pegar_xml\", \"abrir_oj1b1n\"]."
        )
    if not isinstance(fluxo, list) or not all(isinstance(x, str) for x in fluxo):
        raise ValueError("mapa_passos.json: 'fluxo' deve ser lista de nomes de partes.")
    partes = data.get("partes") or {}
    faltando = [n for n in fluxo if n not in partes]
    if faltando:
        raise KeyError("fluxo referencia partes inexistentes: {}".format(", ".join(faltando)))
    return list(fluxo)


def passos_da_parte(nome_parte, mapa=None):
    # type: (str, Optional[dict]) -> List[Dict[str, Any]]
    data = mapa if mapa is not None else load_mapa()
    partes = data.get("partes") or {}
    if nome_parte not in partes:
        raise KeyError("Parte desconhecida: {}".format(nome_parte))
    passos = list(partes[nome_parte].get("passos") or [])
    passos.sort(key=lambda p: int(p.get("ordem") or 0))
    return passos


def passos_com_xy(nome_parte, mapa=None):
    # type: (str, Optional[dict]) -> List[Dict[str, Any]]
    return [p for p in passos_da_parte(nome_parte, mapa) if kinds.precisa_xy(p.get("kind"))]


def validar_passo(passo):
    # type: (dict) -> None
    if not passo.get("id"):
        raise ValueError("Passo sem 'id': {}".format(passo))
    kind = str(passo.get("kind") or "")
    if not kind:
        raise ValueError("Passo '{}' sem 'kind'.".format(passo.get("id")))
    if kind not in kinds.KINDS_TODOS:
        raise ValueError(
            "Passo '{}' com kind desconhecido {!r}. Use: {}.".format(
                passo.get("id"), kind, ", ".join(sorted(kinds.KINDS_TODOS))
            )
        )
    if kind in ("keys", "hotkey") and not passo.get("keys"):
        raise ValueError("Passo '{}' kind={} sem lista 'keys'.".format(passo.get("id"), kind))
