import random
from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup


class FloatingToast(QLabel):
    def __init__(self, parent=None, bg="#1f1f1f", fg="#a3a3a3", font_size=25, border="#303030"):
        super().__init__(parent)
        self._bg = bg
        self._fg = fg
        self._font_size = font_size
        self._border = border
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setVisible(False)
        self._apply_style()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._current_anim = None

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLabel {{
                background: {self._bg};
                color: {self._fg};
                padding: 10px 14px;
                border-radius: 12px;
                border: 1px solid {self._border};
                font-weight: 600;
                letter-spacing: 0.3px;
                font-size: {self._font_size}px;
            }}
        """)

    def show_message(self, text, duration_ms=2200, bottom_band_ratio=0.3, top_band_ratio=0.25):
        parent = self.parentWidget()
        if parent is None:
            return

        if self._current_anim:
            self._current_anim.stop()

        self.setText(text)
        self.adjustSize()

        usable_width = max(1, parent.width() - self.width() - 20)
        start_x = random.randint(10, usable_width)
        end_x = start_x

        bottom_band_start = int(parent.height() * (1 - bottom_band_ratio))
        bottom_band_end = parent.height() - self.height() - 10
        bottom_band_end = max(bottom_band_start, bottom_band_end)
        start_y = random.randint(bottom_band_start, bottom_band_end) if bottom_band_end >= bottom_band_start else bottom_band_end

        top_band_end = int(parent.height() * top_band_ratio)
        top_band_end = max(10, top_band_end)
        end_y = random.randint(10, top_band_end)

        self.move(start_x, start_y)
        self._opacity.setOpacity(0.0)
        self.show()
        self.raise_()

        pos_anim = QPropertyAnimation(self, b"pos", self)
        pos_anim.setDuration(duration_ms)
        pos_anim.setStartValue(QPoint(start_x, start_y))
        pos_anim.setEndValue(QPoint(end_x, end_y))
        pos_anim.setEasingCurve(QEasingCurve.OutQuad)

        fade_anim = QPropertyAnimation(self._opacity, b"opacity", self)
        fade_anim.setDuration(duration_ms)
        fade_anim.setKeyValueAt(0.0, 0.0)
        fade_anim.setKeyValueAt(0.15, 1.0)
        fade_anim.setKeyValueAt(0.8, 1.0)
        fade_anim.setKeyValueAt(1.0, 0.0)

        group = QParallelAnimationGroup(self)
        group.addAnimation(pos_anim)
        group.addAnimation(fade_anim)
        group.finished.connect(self._on_finished)

        self._current_anim = group
        group.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_finished(self):
        self.hide()
        self._current_anim = None
