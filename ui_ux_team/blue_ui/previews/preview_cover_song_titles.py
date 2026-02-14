import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.widgets.cover_song_titles import CoverSongTitlesRow


class CoverSongTitlesPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cover Song Titles Preview")
        self.resize(760, 170)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        self.row = CoverSongTitlesRow()
        self.row.set_slot_widths(150, 220, 150)
        root.addWidget(self.row, alignment=Qt.AlignCenter)

        self._items = [
            (
                "my very long previous song title that should marquee on hover",
                "deep purple smoke on the water remastered live 1972",
                "another very long upcoming title to test right-side marquee",
            ),
            (
                "queen bohemian rhapsody",
                "fleetwood mac dreams",
                "pink floyd comfortably numb pulse version",
            ),
            (
                "massive attack teardrop",
                "metallica nothing else matters s and m",
                "radiohead everything in its right place",
            ),
        ]
        self._idx = 0
        self._apply_titles()

        self._timer = QTimer(self)
        self._timer.setInterval(1800)
        self._timer.timeout.connect(self._next_titles)
        self._timer.start()

    def _apply_titles(self):
        prev_title, current_title, next_title = self._items[self._idx]
        self.row.set_titles(prev_title, current_title, next_title)

    def _next_titles(self):
        self._idx = (self._idx + 1) % len(self._items)
        self._apply_titles()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    window = CoverSongTitlesPreview()
    window.show()
    raise SystemExit(app.exec())
