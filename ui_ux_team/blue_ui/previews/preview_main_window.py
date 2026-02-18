import os
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme, set_theme
from ui_ux_team.blue_ui.views.main_window import MainWindowView


class MainWindowPreview(MainWindowView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindowPreview")
        if str(os.getenv("BLUE_UI_PREVIEW_OPEN_SETTINGS", "")).strip().lower() in {"1", "true", "yes"}:
            QTimer.singleShot(260, self.settings_menu)


def _apply_preview_theme() -> None:
    ensure_default_theme()
    requested = str(os.getenv("BLUE_UI_PREVIEW_THEME", "")).strip()
    if not requested:
        return
    try:
        set_theme(requested)
    except Exception:
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    _apply_preview_theme()
    window = MainWindowPreview()
    window.show()
    raise SystemExit(app.exec())
