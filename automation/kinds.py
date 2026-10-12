"""Classificação dos kinds de passo (mapa_passos.json)."""

from __future__ import annotations

# Precisam de XY em pontos_local.json → pedem clique do meio no Mapear.
# map_only: só calibração (Mapear grava; fluxo normal ignora).
KINDS_COM_XY = frozenset({"click", "click_and_type", "map_only"})

# Rodam sozinhos (tecla / colar / lógica). Sem mapeamento de XY próprio.
KINDS_AUTO = frozenset({"keys", "hotkey", "paste", "type", "fill_itens", "fill_taxes"})

# Pausam e pedem ação do usuário (ex.: clicar no XML). Sem XY.
KINDS_USER = frozenset({"user_action"})

KINDS_TODOS = KINDS_COM_XY | KINDS_AUTO | KINDS_USER


def precisa_xy(kind):
    # type: (str) -> bool
    return str(kind or "") in KINDS_COM_XY


def precisa_usuario(kind):
    # type: (str) -> bool
    return str(kind or "") in KINDS_USER


def so_mapear(kind):
    # type: (str) -> bool
    """Âncora de calibração: Mapear grava XY; execução do fluxo pula."""
    return str(kind or "") == "map_only"
