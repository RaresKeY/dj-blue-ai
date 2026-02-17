from PySide6.QtCore import Property, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from architects.helpers.resource_path import resource_path


class TranscriptHintArrow(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(96, 96)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._poke_offset = 0.0
        self._peck_angle = 0.0
        self._pixmap = QPixmap(resource_path("ui_ux_team/assets/arrow_1.png"))

    def get_poke_offset(self) -> float:
        return self._poke_offset

    def set_poke_offset(self, value: float):
        self._poke_offset = float(value)
        self.update()

    poke_offset = Property(float, get_poke_offset, set_poke_offset)

    def get_peck_angle(self) -> float:
        return self._peck_angle

    def set_peck_angle(self, value: float):
        self._peck_angle = float(value)
        self.update()

    peck_angle = Property(float, get_peck_angle, set_peck_angle)

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Keep size stable while preserving the source image shape.
        scaled = self._pixmap.scaled(
            int(self.width() * 0.90),
            int(self.height() * 0.90),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        dx = self._poke_offset
        dy = -0.22 * self._poke_offset
        x = (self.width() - scaled.width()) / 2.0 + dx
        y = (self.height() - scaled.height()) / 2.0 + dy

        # Tip pivot for woodpecker-like pecking toward transcript button.
        tip_x = x + scaled.width() * 0.865
        tip_y = y + scaled.height() * 0.225
        painter.translate(tip_x, tip_y)
        painter.rotate(self._peck_angle)
        painter.translate(-tip_x, -tip_y)
        painter.drawPixmap(int(x), int(y), scaled)

        return super().paintEvent(event)
