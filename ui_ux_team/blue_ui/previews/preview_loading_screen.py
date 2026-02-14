import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.widgets.startup_loading import StartupLoadingScreen


class LoadingPreviewController:
    def __init__(self, screen: StartupLoadingScreen):
        self.screen = screen
        self.steps = [
            ("Loading configuration...", 14),
            ("Applying selected theme...", 33),
            ("Initializing services...", 66),
            ("Building main interface...", 88),
            ("Finalizing startup...", 100),
        ]
        self.idx = 0
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._next)

        self.screen.start(estimated_total_seconds=6.0, initial_status="Starting app bootstrap...")
        self.timer.start()

    def _next(self):
        if self.idx >= len(self.steps):
            self.timer.stop()
            return
        label, progress = self.steps[self.idx]
        if progress >= 100:
            self.screen.complete("Launch ready")
            QTimer.singleShot(1200, self._restart)
        else:
            self.screen.update_stage(label, progress)
        self.idx += 1

    def _restart(self):
        self.idx = 0
        self.screen.start(estimated_total_seconds=6.0, initial_status="Starting app bootstrap...")
        self.timer.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    widget = StartupLoadingScreen()
    widget.show()
    widget._controller = LoadingPreviewController(widget)
    raise SystemExit(app.exec())
