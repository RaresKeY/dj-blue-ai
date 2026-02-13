import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.views.main_window import MainWindowView


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindowView()
    window.show()
    raise SystemExit(app.exec())
