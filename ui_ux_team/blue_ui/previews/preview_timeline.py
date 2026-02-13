import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.widgets.timeline import PlaybackTimeline


class TimelinePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timeline Preview")
        self.resize(620, 140)

        self._pos = 0.0
        self._dur = 180.0

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        self.info = QLabel("YouTube-style timeline preview")
        self.timeline = PlaybackTimeline()
        self.timeline.set_duration(self._dur)
        self.timeline.seek_requested.connect(self._on_seek)

        root.addWidget(self.info)
        root.addWidget(self.timeline)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._pos += 0.1
        if self._pos > self._dur:
            self._pos = 0.0
        self.timeline.set_position(self._pos)

    def _on_seek(self, seconds: float):
        self._pos = max(0.0, min(self._dur, seconds))
        self.timeline.set_position(self._pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimelinePreview()
    window.show()
    raise SystemExit(app.exec())
