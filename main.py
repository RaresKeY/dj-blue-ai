"""Compatibility launcher that forwards to Blue UI app entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui_ux_team.blue_ui.app.main import run


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
