"""
SAP 800 ATT — entrada principal.

Sem argumentos: abre a tela.
Com subcomando: roda no terminal (melhor para ver erros).

Exemplos:
  .\\.venv\\Scripts\\python.exe main.py listar
  .\\.venv\\Scripts\\python.exe main.py fluxo --batch SEU_BATCH --issuer 513088
  .\\.venv\\Scripts\\python.exe main.py parte abrir_batch --batch SEU_BATCH
  .\\.venv\\Scripts\\python.exe main.py mapear abrir_oj1b1n --issuer 513088
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation import win_mouse


def main(argv=None):
    # type: (Optional[list]) -> int
    win_mouse.ensure_dpi_awareness()
    args = list(sys.argv[1:] if argv is None else argv)

    # Sem args → tela. Com args → CLI no terminal.
    if not args:
        from automation.app_ui import run_app

        run_app()
        return 0

    from automation.cli import run_cli

    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
