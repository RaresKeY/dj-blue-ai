from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QSlider, QHBoxLayout, QVBoxLayout
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
import sys
from pathlib import Path

# === CONSTANTS ===
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICON_PLAY = ASSETS_DIR / "play.png"
ICON_PAUSE = ASSETS_DIR / "pause.png"
ICON_NEXT = ASSETS_DIR / "next.png"
ICON_PREV = ASSETS_DIR / "prev.png"
ICON_MINIMIZE = ASSETS_DIR / "minimize.png"
ICON_CLOSE = ASSETS_DIR / "close.png"
ALBUM_ART = ASSETS_DIR / "album.png"

class MusicPlayerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player Mockup")
        self.setStyleSheet("background-color: #1a2235; color: white; border-radius: 10px;")
        self.setFixedSize(400, 320)

        # Top bar
        title = QLabel("Playing from...")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 10px;")

        btn_minimize = QPushButton()
        btn_close = QPushButton()
        self.setup_icon_button(btn_minimize, ICON_MINIMIZE, 30)
        self.setup_icon_button(btn_close, ICON_CLOSE, 30)

        top_bar = QHBoxLayout()
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(btn_minimize)
        top_bar.addWidget(btn_close)

        # Album art row
        album_layout = QHBoxLayout()
        for i in range(3):
            album = QLabel()
            pix = QPixmap(str(ALBUM_ART))
            album.setPixmap(pix.scaled(90 if i != 1 else 120, 90 if i != 1 else 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            album.setAlignment(Qt.AlignCenter)
            album_layout.addWidget(album)

        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {height: 4px; background: #23345b;}
            QSlider::handle:horizontal {background: #ff0080; width: 14px; margin: -5px 0;}
        """)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("1:05"))
        time_layout.addStretch()
        time_layout.addWidget(QLabel("3:58"))

        # Controls
        btn_prev = QPushButton()
        btn_play = QPushButton()
        btn_next = QPushButton()

        self.setup_icon_button(btn_prev, ICON_PREV, 50)
        self.setup_icon_button(btn_play, ICON_PLAY, 60)
        self.setup_icon_button(btn_next, ICON_NEXT, 50)

        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(btn_prev)
        controls.addWidget(btn_play)
        controls.addWidget(btn_next)
        controls.addStretch()

        # Main layout
        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addLayout(album_layout)
        layout.addLayout(time_layout)
        layout.addWidget(slider)
        layout.addLayout(controls)

    def setup_icon_button(self, button, path, size):
        pix = QPixmap(str(path)).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        button.setIcon(QIcon(pix))
        button.setIconSize(pix.rect().size())
        button.setFixedSize(size + 10, size + 10)
        button.setFlat(True)
        button.setStyleSheet("border: none;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicPlayerUI()
    window.show()
    sys.exit(app.exec())
