import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Ensure project root is importable when running directly.
if not getattr(sys, "frozen", False):
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.app.composition import AppComposer


def run() -> int:
    app = QApplication(sys.argv)
    composer = AppComposer()
    composer.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
