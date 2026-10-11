"""
SAP 800 ATT — entrada principal.

Abre a tela simples (Iniciar / Mapear).
Prefira dar dois cliques em iniciar.bat.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.app_ui import run_app
from automation import win_mouse


def main():
    # type: () -> None
    win_mouse.ensure_dpi_awareness()
    run_app()


if __name__ == "__main__":
    main()
