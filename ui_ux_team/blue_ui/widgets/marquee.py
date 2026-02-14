from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtGui import QColor, QPainter
from PySide6.QtCore import QTimer, QEvent, QPropertyAnimation

from ui_ux_team.blue_ui.theme import tokens as theme_tokens


def _parse_color(value: str, fallback: str) -> QColor:
    color = QColor(value or "")
    if color.isValid():
        return color
    fallback_color = QColor(fallback)
    if fallback_color.isValid():
        return fallback_color
    return QColor("#FFFFFF")


def _contrast_ratio(fg: QColor, bg: QColor) -> float:
    def channel(v: int) -> float:
        c = float(v) / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    def luminance(color: QColor) -> float:
        return (
            0.2126 * channel(color.red())
            + 0.7152 * channel(color.green())
            + 0.0722 * channel(color.blue())
        )

    l1 = luminance(fg)
    l2 = luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class MarqueeLabel(QLabel):
    def __init__(self, text="", parent=None, step=1, interval_ms=30, gap=50):
        super().__init__(parent)
        self._offset = 0
        self._text_width = 0
        self._gap = gap
        self._step = step
        self._text_color = QColor("#FFFFFF")

        self.setText(text)
        self.setContentsMargins(10, 0, 10, 0)
        self.refresh_theme()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(interval_ms)

    def setText(self, text):
        super().setText(text)
        fm = self.fontMetrics()
        self._text_width = fm.horizontalAdvance(text) if text else 0

    def _tick(self):
        if self._text_width <= 0:
            return
        span = self._text_width + self._gap
        self._offset = (self._offset + self._step) % span
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self._text_color)
        fm = self.fontMetrics()
        text = self.text()
        y = (self.height() + fm.ascent() - fm.descent()) / 2
        if self._text_width <= 0:
            return

        span = self._text_width + self._gap
        x = -self._text_width + self._offset
        while x < self.width():
            painter.drawText(x, y, text)
            x += span

    def refresh_theme(self):
        bg = _parse_color(getattr(theme_tokens, "COLOR_BG_MAIN", "#1E1E1E"), "#1E1E1E")
        preferred = _parse_color(getattr(theme_tokens, "TEXT_PRIMARY", "#D4D4D4"), "#D4D4D4")
        if _contrast_ratio(preferred, bg) >= 4.5:
            self._text_color = preferred
        else:
            white = QColor("#FFFFFF")
            black = QColor("#000000")
            self._text_color = white if _contrast_ratio(white, bg) >= _contrast_ratio(black, bg) else black
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.FontChange:
            self.setText(self.text())
        elif event.type() in (QEvent.PaletteChange, QEvent.StyleChange):
            self.refresh_theme()
        super().changeEvent(event)


class QueuedMarqueeLabel(QWidget):
    def __init__(self, items=None, parent=None, hold_ms=3000, fade_ms=200, **marquee_kwargs):
        super().__init__(parent)
        self._queue = list(items) if items else []
        self._idx = 0
        self._hold_ms = hold_ms
        self._fade_ms = fade_ms

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = MarqueeLabel("", **marquee_kwargs)
        self._opacity = QGraphicsOpacityEffect(self.label)
        self._opacity.setOpacity(1.0)
        self.label.setGraphicsEffect(self._opacity)
        layout.addWidget(self.label)

        if self._queue:
            self.label.setText(self._queue[0])

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_text)
        if self._queue:
            self._timer.start(self._hold_ms)

    def set_queue(self, items):
        self._queue = list(items) if items else []
        self._idx = 0
        if self._queue:
            self.label.setText(self._queue[0])
            self._timer.start(self._hold_ms)
        else:
            self._timer.stop()

    def _next_text(self):
        if not self._queue:
            return
        self._idx = (self._idx + 1) % len(self._queue)
        self._fade_to(self._queue[self._idx])

    def _fade_to(self, text):
        self._timer.stop()
        anim_out = QPropertyAnimation(self._opacity, b"opacity", self)
        anim_out.setDuration(self._fade_ms)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.finished.connect(lambda: self._on_faded(text))
        anim_out.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_faded(self, text):
        self.label.setText(text)
        anim_in = QPropertyAnimation(self._opacity, b"opacity", self)
        anim_in.setDuration(self._fade_ms)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.finished.connect(lambda: self._timer.start(self._hold_ms))
        anim_in.start(QPropertyAnimation.DeleteWhenStopped)

    def refresh_theme(self):
        self.label.refresh_theme()
