import os
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QCursor, QPainter, QPainterPath, QColor
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property

from architects.helpers.resource_path import resource_path

BASE = resource_path("ui_ux_team/assets")
IMAGE_NOT_FOUND = os.path.join(BASE, "image_not_found_white.png")


class ImageButton(QLabel):
    clicked = Signal()

    def __init__(self, path, size=(40, 40), fallback=None):
        super().__init__()
        self.setFixedSize(*size)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAlignment(Qt.AlignCenter)
        self._corner_radius = 0

        self.HOVER_SCALE = 1.10
        self.PRESS_SCALE = 0.94
        margin_factor = 0.06

        margins = [max(size[0], size[1]) * margin_factor] * 4
        self.setContentsMargins(*margins)

        self.base_pixmap = QPixmap(path)
        if self.base_pixmap.isNull() and fallback:
            self.base_pixmap = QPixmap(fallback)

        self._scale = 1.0
        self._tint_color = None
        self.anim = QPropertyAnimation(self, b"scale_factor", self)
        self.anim.setDuration(120)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def set_image(self, path, fallback=IMAGE_NOT_FOUND):
        resolved = path
        if not os.path.isabs(resolved):
            if resolved.startswith("assets/"):
                resolved = resolved.split("assets/", 1)[1]
            resolved = os.path.join(BASE, resolved)

        pm = QPixmap(resolved)
        if pm.isNull():
            pm = QPixmap(fallback or IMAGE_NOT_FOUND)

        self.base_pixmap = pm
        self.update()

    def set_tint_color(self, color):
        if color is None:
            self._tint_color = None
            self.update()
            return

        candidate = QColor(color) if not isinstance(color, QColor) else QColor(color)
        self._tint_color = candidate if candidate.isValid() else None
        self.update()

    def _resolved_source_pixmap(self):
        if self._tint_color is None:
            return self.base_pixmap
        if self.base_pixmap.isNull():
            return self.base_pixmap

        tinted = QPixmap(self.base_pixmap.size())
        tinted.fill(Qt.transparent)

        painter = QPainter(tinted)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self.base_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), self._tint_color)
        painter.end()
        return tinted

    def set_corner_radius(self, radius: int):
        self._corner_radius = max(0, int(radius))
        self.update()

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale_factor = Property(float, get_scale, set_scale)

    def paintEvent(self, event):
        source_pixmap = self._resolved_source_pixmap()
        if source_pixmap.isNull():
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)

        m = self.contentsMargins()
        inner_w = self.width() - (m.left() + m.right())
        inner_h = self.height() - (m.top() + m.bottom())

        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)

        scaled = source_pixmap.scaled(inner_w, inner_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = m.left() + (inner_w - scaled.width()) // 2
        y = m.top() + (inner_h - scaled.height()) // 2

        if self._corner_radius > 0:
            path = QPainterPath()
            path.addRoundedRect(float(x), float(y), float(scaled.width()), float(scaled.height()), float(self._corner_radius), float(self._corner_radius))
            painter.setClipPath(path)
        painter.drawPixmap(x, y, scaled)

    def enterEvent(self, event):
        self.animate_to(self.HOVER_SCALE)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_to(1.00)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.animate_to(self.PRESS_SCALE, fast=True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            inside = self.rect().contains(event.position().toPoint())
            self.animate_to(self.HOVER_SCALE if inside else 1.00)
            if inside:
                self.clicked.emit()
        super().mouseReleaseEvent(event)

    def animate_to(self, value, fast=False):
        self.anim.stop()
        self.anim.setDuration(80 if fast else 140)
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(value)
        self.anim.start()
