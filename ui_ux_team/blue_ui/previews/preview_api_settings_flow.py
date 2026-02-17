import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.views.main_window import MainWindowView


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    window = MainWindowView()
    window.show()

    def open_api_settings():
        if window._btn_api is not None:
            QTest.mouseClick(window._btn_api, Qt.LeftButton)

    QTimer.singleShot(400, open_api_settings)
    raise SystemExit(app.exec())
