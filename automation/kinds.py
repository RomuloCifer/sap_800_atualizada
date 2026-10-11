"""Classificação dos kinds de passo (mapa_passos.json)."""

from __future__ import annotations

# Precisam de XY em pontos_local.json → pedem clique do meio no Mapear.
KINDS_COM_XY = frozenset({"click", "click_and_type"})

# Rodam sozinhos (tecla / colar). Sem aviso e sem mapeamento.
KINDS_AUTO = frozenset({"keys", "hotkey", "paste"})

# Pausam e pedem ação do usuário (ex.: clicar no XML). Sem XY.
KINDS_USER = frozenset({"user_action"})

KINDS_TODOS = KINDS_COM_XY | KINDS_AUTO | KINDS_USER


def precisa_xy(kind):
    # type: (str) -> bool
    return str(kind or "") in KINDS_COM_XY


def precisa_usuario(kind):
    # type: (str) -> bool
    return str(kind or "") in KINDS_USER
