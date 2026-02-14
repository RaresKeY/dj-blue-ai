import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton, QHBoxLayout, QVBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.widgets.song_cover_carousel import SongCoverCarousel


class CoverCarouselPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Song Cover Carousel Preview")
        self.resize(760, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        title = QLabel("Song Cover Carousel [prev][current][next]")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        root.addWidget(title)

        self.carousel = SongCoverCarousel()
        self.carousel.set_song_items(
            [
                "queen_bohemian_rhapsody_live_at_wembley_1986.mp3",
                "fleetwood_mac_the_chain_2004_remaster.flac",
                "deep_purple_smoke_on_the_water_live_in_japan_1972.wav",
                "pink_floyd_comfortably_numb_pulse_1994_extended_version.mp3",
                "radiohead_everything_in_its_right_place_remastered_2025.ogg",
            ]
        )
        root.addWidget(self.carousel, alignment=Qt.AlignCenter)

        controls = QHBoxLayout()
        prev_btn = QPushButton("Prev")
        next_btn = QPushButton("Next")
        controls.addWidget(prev_btn)
        controls.addWidget(next_btn)
        root.addLayout(controls)

        self.current_label = QLabel("Current song: -")
        root.addWidget(self.current_label)

        self.list_widget = QListWidget()
        for p in self.carousel.song_paths():
            self.list_widget.addItem(Path(p).name)
        root.addWidget(self.list_widget, 1)

        prev_btn.clicked.connect(self.carousel.step_prev)
        next_btn.clicked.connect(self.carousel.step_next)
        self.carousel.prev_requested.connect(self.carousel.step_prev)
        self.carousel.next_requested.connect(self.carousel.step_next)
        self.carousel.current_song_changed.connect(self._on_song_changed)
        self._on_song_changed(self.carousel.current_song_path())

    def _on_song_changed(self, song_path: str):
        name = Path(song_path).name if song_path else "-"
        self.current_label.setText(f"Current song: {name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoverCarouselPreview()
    window.show()
    raise SystemExit(app.exec())
