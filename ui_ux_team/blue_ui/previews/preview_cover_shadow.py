import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


def _cover_tile(
    name: str,
    *,
    size: int,
    bg: str,
    border: str,
    radius: int,
) -> QFrame:
    tile = QFrame()
    tile.setFixedSize(size, size)
    tile.setFrameShape(QFrame.NoFrame)
    tile.setStyleSheet(
        f"""
        QFrame {{
            background: {bg};
            border: 2px solid {border};
            border-radius: {radius}px;
        }}
        QLabel {{
            color: rgba(255, 255, 255, 220);
            background: transparent;
            border: none;
            font-weight: 800;
            font-size: 12px;
        }}
        """
    )

    layout = QVBoxLayout(tile)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(0)

    label = QLabel(name)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label, 1)
    return tile


class CoverShadowPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preview: Cover Shadow")
        self.resize(960, 560)
        self.setStyleSheet("QWidget { background: #181A20; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 24)
        root.setSpacing(14)

        title = QLabel("Preview: soft shadow under center cover")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 900;")
        root.addWidget(title)

        row = QHBoxLayout()
        row.setContentsMargins(0, 28, 0, 10)
        row.setSpacing(28)
        row.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        root.addLayout(row, 1)

        prev_cover = _cover_tile(
            "PREV",
            size=150,
            bg="#2B466A",
            border="#B4D5FF",
            radius=12,
        )
        current_cover = _cover_tile(
            "CURRENT",
            size=220,
            bg="#6D4B9E",
            border="#E2CCFF",
            radius=14,
        )
        next_cover = _cover_tile(
            "NEXT",
            size=150,
            bg="#2B466A",
            border="#B4D5FF",
            radius=12,
        )

        shadow = QGraphicsDropShadowEffect(current_cover)
        shadow.setBlurRadius(38)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(0, 0, 0, 140))
        current_cover.setGraphicsEffect(shadow)

        row.addWidget(prev_cover)
        row.addWidget(current_cover)
        row.addWidget(next_cover)

        note = QLabel("Shadow: blur=38, offset=(0, 18), color=rgba(0,0,0,140)")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet("color: rgba(215, 227, 255, 210); font-size: 12px;")
        root.addWidget(note)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoverShadowPreview()
    window.show()
    raise SystemExit(app.exec())
