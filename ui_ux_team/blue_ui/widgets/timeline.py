import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from ui_ux_team.blue_ui.theme import tokens


def _with_alpha(color: str, alpha: float) -> str:
    a = max(0.0, min(1.0, float(alpha)))
    c = (color or "").strip()
    if c.startswith("#") and len(c) in (4, 7):
        if len(c) == 4:
            r = int(c[1] * 2, 16)
            g = int(c[2] * 2, 16)
            b = int(c[3] * 2, 16)
        else:
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
        return f"rgba({r}, {g}, {b}, {a:.3f})"

    match = re.match(r"rgba?\(([^)]+)\)", c)
    if match:
        parts = [p.strip() for p in match.group(1).split(",")]
        if len(parts) >= 3:
            return f"rgba({parts[0]}, {parts[1]}, {parts[2]}, {a:.3f})"
    return c


class PreciseSeekSlider(QSlider):
    hover_ratio_changed = Signal(float)
    hover_left = Signal()

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)

    def _value_from_x(self, x: float) -> int:
        width = max(1, self.width())
        ratio = max(0.0, min(1.0, x / width))
        return int(round(ratio * self.maximum()))

    def _ratio_from_x(self, x: float) -> float:
        width = max(1, self.width())
        return max(0.0, min(1.0, x / width))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.sliderPressed.emit()
            self.setValue(self._value_from_x(event.position().x()))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        ratio = self._ratio_from_x(event.position().x())
        self.hover_ratio_changed.emit(ratio)
        if event.buttons() & Qt.LeftButton:
            self.setValue(self._value_from_x(event.position().x()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setValue(self._value_from_x(event.position().x()))
            self.sliderReleased.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self.hover_left.emit()
        super().leaveEvent(event)


class PlaybackTimeline(QWidget):
    seek_requested = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0.0
        self._position = 0.0
        self._is_dragging = False
        self._hovered = False
        self._hover_preview_active = False
        self._hover_ratio = 0.0
        self._groove_h = 4
        self._handle_size = 14
        self._vertical_pad = 10

        self.elapsed_label = QLabel("0:00")
        self.total_label = QLabel("0:00")
        self.slider = PreciseSeekSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setValue(0)
        self.slider.setTracking(True)
        self.slider.setMouseTracking(True)
        self.slider.setMinimumHeight(20)
        self.slider.setMaximumHeight(20)
        self._slider_wrap = QWidget()
        self._slider_wrap_layout = QVBoxLayout(self._slider_wrap)
        self._slider_wrap_layout.setContentsMargins(0, self._vertical_pad, 0, self._vertical_pad)
        self._slider_wrap_layout.setSpacing(0)
        self._slider_wrap_layout.addWidget(self.slider)

        labels = QHBoxLayout()
        labels.setContentsMargins(0, 0, 0, 0)
        labels.setSpacing(8)
        labels.addWidget(self.elapsed_label, 0, Qt.AlignLeft)
        labels.addStretch(1)
        labels.addWidget(self.total_label, 0, Qt.AlignRight)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        root.addLayout(labels)
        root.addWidget(self._slider_wrap, 1)

        # Overlay layers for timeline visuals:
        # preview fill (lowest), hover marker (middle), actual handle (top).
        self._preview_fill = QWidget(self.slider)
        self._preview_fill.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._preview_fill.hide()

        self._hover_marker = QWidget(self.slider)
        self._hover_marker.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._hover_marker.hide()

        self._actual_handle = QWidget(self.slider)
        self._actual_handle.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._actual_handle.hide()

        self.slider.sliderPressed.connect(self._on_drag_start)
        self.slider.sliderReleased.connect(self._on_drag_end)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.hover_ratio_changed.connect(self._on_hover_ratio)
        self.slider.hover_left.connect(self._on_hover_leave)
        self.refresh_theme()

    def refresh_theme(self):
        self._groove_h = 9 if self._hovered else 5
        self._handle_size = 14
        # Keep layout geometry stable to avoid hover jiggle.
        self._slider_wrap_layout.setContentsMargins(0, self._vertical_pad, 0, self._vertical_pad)

        self.setStyleSheet(
            f"""
            QLabel {{
                color: {tokens.TIMELINE_TEXT};
                font-size: 14px;
                font-weight: 600;
                min-width: 44px;
            }}
            QSlider::groove:horizontal {{
                height: {self._groove_h}px;
                background: {tokens.TIMELINE_REMAINING};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {tokens.TIMELINE_PROGRESS};
                border-radius: 2px;
            }}
            QSlider::add-page:horizontal {{
                background: {tokens.TIMELINE_REMAINING};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: transparent;
                border: none;
                width: 1px;
                margin: -8px 0;
            }}
            """
        )

        preview_color = getattr(tokens, "TIMELINE_PREVIEW", _with_alpha(tokens.TIMELINE_PROGRESS, 0.38))
        marker_color = getattr(tokens, "TIMELINE_MARKER", _with_alpha(tokens.TIMELINE_HANDLE_HOVER, 0.72))
        handle_color = tokens.TIMELINE_PROGRESS
        handle_border = _with_alpha(tokens.TIMELINE_TEXT, 0.62)

        self._preview_fill.setStyleSheet(f"background: {preview_color}; border-radius: 2px;")
        self._hover_marker.setStyleSheet(f"background: {marker_color}; border-radius: 1px;")
        self._hover_marker.setFixedWidth(2)
        self._hover_marker.setFixedHeight(max(8, self._groove_h + 6))
        self._actual_handle.setStyleSheet(
            f"background: {handle_color}; border: 1px solid {handle_border}; border-radius: {self._handle_size // 2}px;"
        )
        self._actual_handle.setFixedSize(self._handle_size, self._handle_size)

        self._update_visual_layers()

    def set_duration(self, seconds: float):
        self._duration = max(0.0, float(seconds))
        self.total_label.setText(self._fmt(self._duration))
        self._update_slider_from_position()

    def set_position(self, seconds: float):
        self._position = max(0.0, min(float(seconds), self._duration if self._duration > 0 else float(seconds)))
        if self._is_dragging:
            return
        self.elapsed_label.setText(self._fmt(self._position))
        self._update_slider_from_position()

    def _update_slider_from_position(self):
        if self._duration <= 0:
            blocked = self.slider.blockSignals(True)
            self.slider.setValue(0)
            self.slider.blockSignals(blocked)
            self._update_visual_layers()
            return

        ratio = self._position / self._duration
        slider_val = int(max(0.0, min(1.0, ratio)) * self.slider.maximum())
        blocked = self.slider.blockSignals(True)
        self.slider.setValue(slider_val)
        self.slider.blockSignals(blocked)
        self._update_visual_layers()

    def _on_drag_start(self):
        self._is_dragging = True
        self._hover_preview_active = False
        self.refresh_theme()

    def _on_drag_end(self):
        self._is_dragging = False
        self.refresh_theme()
        if self._duration <= 0:
            return
        ratio = self.slider.value() / self.slider.maximum()
        self.seek_requested.emit(ratio * self._duration)

    def _on_value_changed(self, value: int):
        if self._duration > 0:
            ratio = value / self.slider.maximum()
            preview_pos = ratio * self._duration
            self.elapsed_label.setText(self._fmt(preview_pos if self._is_dragging else self._position))
        self._update_visual_layers()

    def _on_hover_ratio(self, ratio: float):
        self._hover_ratio = max(0.0, min(1.0, ratio))
        if not self._is_dragging:
            self._hover_preview_active = True
        self._update_visual_layers()

    def _on_hover_leave(self):
        self._hover_preview_active = False
        self._update_visual_layers()

    def _update_visual_layers(self):
        w = max(1, self.slider.width())
        h = self.slider.height()
        max_val = max(1, self.slider.maximum())
        actual_ratio = self.slider.value() / max_val
        actual_x = int(actual_ratio * w)
        groove_y = (h - self._groove_h) // 2

        # Handle appears only while hovered or dragging.
        show_handle = self._hovered or self._is_dragging
        if show_handle:
            hx = max(0, min(w - self._actual_handle.width(), actual_x - self._actual_handle.width() // 2))
            hy = (h - self._actual_handle.height()) // 2
            self._actual_handle.move(hx, hy)
            self._actual_handle.show()
        else:
            self._actual_handle.hide()

        if self._hover_preview_active and not self._is_dragging:
            preview_x = int(self._hover_ratio * w)
            marker_x = max(0, min(w - self._hover_marker.width(), preview_x - self._hover_marker.width() // 2))
            marker_y = (h - self._hover_marker.height()) // 2
            self._hover_marker.move(marker_x, marker_y)
            self._hover_marker.show()

            fill_w = max(0, min(w, preview_x))
            self._preview_fill.setGeometry(0, groove_y, fill_w, self._groove_h)
            self._preview_fill.show()
        else:
            self._hover_marker.hide()
            self._preview_fill.hide()

        # Stable z-order.
        self._preview_fill.lower()
        self._hover_marker.raise_()
        self._actual_handle.raise_()

    @staticmethod
    def _fmt(seconds: float) -> str:
        total = int(max(0, round(seconds)))
        m, s = divmod(total, 60)
        return f"{m}:{s:02d}"

    def enterEvent(self, event):
        self._hovered = True
        self.refresh_theme()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._hover_preview_active = False
        self.refresh_theme()
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_visual_layers()

    def is_interacting(self) -> bool:
        return self._is_dragging
