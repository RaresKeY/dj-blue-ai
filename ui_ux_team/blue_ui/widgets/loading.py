from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QTimer, Qt


class LoadingCircle(QWidget):
    def __init__(self, parent=None, size=50):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_angle)
        self.hide()

    def _update_angle(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def start(self):
        self._timer.start(80)
        self.show()
        self.raise_()

    def stop(self):
        self._timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        radius = min(cx, cy) - 6

        painter.translate(cx, cy)
        painter.rotate(self._angle)

        pen = painter.pen()
        pen.setWidth(5)
        pen.setCapStyle(Qt.RoundCap)

        for i in range(8):
            opacity = int(255 * (i + 1) / 8)
            pen.setColor(QColor(62, 106, 255, opacity))
            painter.setPen(pen)
            painter.drawLine(0, int(-radius), 0, int(-radius + 10))
            painter.rotate(45)
