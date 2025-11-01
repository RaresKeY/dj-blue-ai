from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QSlider
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QLinearGradient, QColor
from PySide6.QtCore import Qt, QTimer, QElapsedTimer
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
GRANULARITY = 1000  # ms-level precision


# --- Smooth clickable slider ---
class SmoothSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(Qt.Horizontal, *args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.position().x()
            vmin, vmax = self.minimum(), self.maximum()
            w = max(1, self.width() - 1)
            value = vmin + round((x / w) * (vmax - vmin))
            self.setValue(value)
            event.accept()
        super().mousePressEvent(event)


# --- Fade helper ---
def apply_fade(pixmap: QPixmap, side: str):
    faded = QPixmap(pixmap.size())
    faded.fill(Qt.transparent)
    painter = QPainter(faded)
    painter.drawPixmap(0, 0, pixmap)
    gradient = QLinearGradient(0, 0, pixmap.width(), 0)

    if side == "right":
        gradient.setColorAt(0, QColor(26, 34, 53, 255))
        gradient.setColorAt(0.8, QColor(26, 34, 53, 0))
    else:
        gradient.setColorAt(0.2, QColor(26, 34, 53, 0))
        gradient.setColorAt(1, QColor(26, 34, 53, 255))

    painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
    painter.fillRect(faded.rect(), gradient)
    painter.end()
    return faded


# --- Main UI ---
class MusicPlayerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ Blue AI")
        self.setStyleSheet("background-color: #1a2235; color: white; border-radius: 10px;")
        self.setFixedSize(400, 320)

        # === Top bar ===
        title = QLabel("Deep Purple - Smoke on the Water")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 10px; margin-top: 10px; margin-bottom: 10px")

        top_bar = QHBoxLayout()
        top_bar.addWidget(title)
        top_bar.addStretch()

        # === Album art row with fades ===
        album_layout = QHBoxLayout()
        for i in range(3):
            album = QLabel()
            pix = QPixmap(str(ALBUM_ART))
            if i == 0:
                pix = apply_fade(pix.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation), "left")
            elif i == 2:
                pix = apply_fade(pix.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation), "right")
            else:
                pix = pix.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            album.setPixmap(pix)
            album.setAlignment(Qt.AlignCenter)
            album_layout.addWidget(album)

        # === Progress bar + times ===
        self.total_seconds = 3 * 60 + 58
        self.current_time = 65

        self.time_left = QLabel(self.format_time(self.current_time))
        self.time_right = QLabel(self.format_time(self.total_seconds))

        self.slider = SmoothSlider()
        self.slider.setRange(0, self.total_seconds * GRANULARITY)
        self.slider.setValue(self.current_time * GRANULARITY)
        self.slider.valueChanged.connect(
            lambda v: self.time_left.setText(self.format_time(v // GRANULARITY))
        )

        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #23345b;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                                            stop:0 #ff0080, stop:1 #7a00ff);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ff0080;
                border: 2px solid #1a2235;
                width: 12px;
                height: 18px;
                border-radius: 7px;
                margin: -6px 0;
                box-shadow: 0px 0px 4px #ff00aa;
            }
        """)

        time_layout = QHBoxLayout()
        time_layout.addWidget(self.time_left)
        time_layout.addStretch()
        time_layout.addWidget(self.time_right)

        # === Controls ===
        btn_prev = QPushButton()
        self.btn_play = QPushButton()
        btn_next = QPushButton()

        btn_prev.clicked.connect(self.prev_song)
        self.btn_play.clicked.connect(self.toggle_play)
        self.is_playing = True
        btn_next.clicked.connect(self.next_song)

        self.setup_icon_button(btn_prev, ICON_PREV, 25)
        self.setup_icon_button(self.btn_play, ICON_PAUSE, 60)
        self.setup_icon_button(btn_next, ICON_NEXT, 25)

        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(btn_prev)
        controls.addWidget(self.btn_play)
        controls.addWidget(btn_next)
        controls.addStretch()

        # === Layout ===
        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addLayout(album_layout)
        layout.addLayout(time_layout)
        layout.addWidget(self.slider)
        layout.addLayout(controls)

        # === Timer ===
        self._tick = QTimer(self)
        self._tick.setInterval(16)
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._tick.timeout.connect(self.advance_time)
        self._tick.start()

    # --- Helpers ---
    def setup_icon_button(self, button, path, size):
        pix = QPixmap(str(path)).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        button.setIcon(QIcon(pix))
        button.setIconSize(pix.rect().size())
        button.setFixedSize(size + 10, size + 10)
        button.setFlat(True)
        button.setStyleSheet("border: none;")

    @staticmethod
    def format_time(sec):
        m, s = divmod(int(sec), 60)
        return f"{m}:{s:02d}"

    def advance_time(self):
        if self.slider.value() >= self.slider.maximum():
            return
        dt_s = self._elapsed.restart() / 1000.0
        inc = int(dt_s * GRANULARITY)
        if inc > 0:
            self.slider.setValue(min(self.slider.value() + inc, self.slider.maximum()))

    def toggle_play(self):
        print("Play/Pause pressed!")
        self.is_playing = not self.is_playing

        if self.is_playing:
            self.setup_icon_button(self.btn_play, ICON_PAUSE, 60)
            self._elapsed.restart()
            self._tick.start()
        else:
            self.setup_icon_button(self.btn_play, ICON_PLAY, 60)
            self._tick.stop()

    def next_song(self):
        print("Next pressed!")

    def prev_song(self):
        print("Prev pressed!")


# --- Entry point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicPlayerUI()
    window.show()
    sys.exit(app.exec())
