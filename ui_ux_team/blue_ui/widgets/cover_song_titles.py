from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from ui_ux_team.blue_ui.theme import tokens as theme_tokens


class HoverMarqueeTitle(QLabel):
    def __init__(self, text: str = "", parent=None, step: int = 1, interval_ms: int = 24, gap: int = 42):
        super().__init__(text, parent)
        self._offset = 0
        self._text_width = 0
        self._gap = int(gap)
        self._step = int(step)
        self._hovered = False

        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignCenter)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(int(interval_ms))

        self._recompute_metrics()

    def setText(self, text: str):
        super().setText(text)
        self._recompute_metrics()

    def _recompute_metrics(self):
        fm = self.fontMetrics()
        self._text_width = fm.horizontalAdvance(self.text()) if self.text() else 0
        self._offset = 0
        self.update()

    def _is_overflowing(self) -> bool:
        rect = self.contentsRect()
        return self._text_width > max(1, rect.width())

    def _should_marquee(self) -> bool:
        return bool(self._hovered and self.text() and self._is_overflowing())

    def _tick(self):
        if self._should_marquee():
            span = self._text_width + self._gap
            self._offset = (self._offset + self._step) % max(1, span)
            self.update()
        elif self._offset != 0:
            self._offset = 0
            self.update()

    def enterEvent(self, event):
        self._hovered = True
        self._offset = 0
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._offset = 0
        self.update()
        super().leaveEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.FontChange:
            self._recompute_metrics()
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recompute_metrics()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(self.palette().windowText().color())

        fm = self.fontMetrics()
        text = self.text()
        rect = self.contentsRect()
        if not text:
            return

        baseline = rect.y() + ((rect.height() + fm.ascent() - fm.descent()) / 2.0)
        if self._should_marquee():
            # Keep idle text centered, but start marquee from the slot's left edge
            # to avoid off-screen jumps for long titles.
            span = self._text_width + self._gap
            start_x = rect.x()
            x0 = start_x - self._offset

            x = x0
            while x < (rect.right() + self._text_width):
                painter.drawText(int(x), int(baseline), text)
                x += span

            x = x0 - span
            while (x + self._text_width) > (rect.x() - self._text_width):
                painter.drawText(int(x), int(baseline), text)
                x -= span
            return

        elided = fm.elidedText(text, Qt.ElideRight, max(1, rect.width()))
        painter.drawText(rect, Qt.AlignCenter, elided)


class CoverSongTitlesRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        self._prev = HoverMarqueeTitle("")
        self._prev.setObjectName("CoverSongTitlePrev")
        self._current = HoverMarqueeTitle("")
        self._current.setObjectName("CoverSongTitleCurrent")
        self._next = HoverMarqueeTitle("")
        self._next.setObjectName("CoverSongTitleNext")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._layout.addWidget(self._prev)
        self._layout.addWidget(self._current)
        self._layout.addWidget(self._next)

        self.setFixedHeight(34)
        self.refresh_theme()

    def set_titles(self, prev_title: str, current_title: str, next_title: str):
        self._prev.setText(prev_title or "")
        self._current.setText(current_title or "")
        self._next.setText(next_title or "")

    def set_slot_widths(self, prev_w: int, current_w: int, next_w: int):
        self._prev.setFixedWidth(max(36, int(prev_w)))
        self._current.setFixedWidth(max(36, int(current_w)))
        self._next.setFixedWidth(max(36, int(next_w)))

    def set_spacing(self, spacing: int):
        self._layout.setSpacing(max(0, int(spacing)))

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QLabel#CoverSongTitlePrev {{
                color: {theme_tokens.TEXT_MUTED};
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }}
            QLabel#CoverSongTitleCurrent {{
                color: {theme_tokens.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }}
            QLabel#CoverSongTitleNext {{
                color: {theme_tokens.TEXT_MUTED};
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }}
            """
        )
