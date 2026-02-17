from PySide6.QtCore import Property, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QSlider, QToolButton, QWidget

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.theme import tokens


class IntegratedVolumeControl(QWidget):
    volume_changed = Signal(float)
    mute_toggled = Signal(bool)

    def __init__(self, parent=None, initial_volume=0.8):
        super().__init__(parent)

        self._volume = max(0.0, min(1.0, float(initial_volume)))
        self._muted = self._volume <= 0.0
        self._last_nonzero_volume = self._volume if self._volume > 0 else 0.8

        self._pad_x = 6
        self._pad_y = 4
        self._icon_size = 34
        self._gap = 6
        self._slider_h = 28
        self._slider_inner_pad_x = 10
        self._expanded_slider_w = 108

        self._slider_width = 0
        self._control_w = self._pad_x + self._icon_size + self._gap + self._expanded_slider_w + self._pad_x
        self._control_h = self._pad_y + self._icon_size + self._pad_y

        self._icon_paths = {
            "muted": resource_path("ui_ux_team/assets/volume_muted.png"),
            "low": resource_path("ui_ux_team/assets/volume_low.png"),
            "medium": resource_path("ui_ux_team/assets/volume_medium.png"),
            "high": resource_path("ui_ux_team/assets/volume_high.png"),
        }

        self.setObjectName("IntegratedVolumeControl")
        self.setAttribute(Qt.WA_Hover, True)
        self.setFixedSize(self._control_w, self._control_h)

        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.setInterval(180)
        self._collapse_timer.timeout.connect(self._collapse_slider)

        self.icon_button = QToolButton(self)
        self.icon_button.setObjectName("VolumeIcon")
        self.icon_button.setCursor(Qt.PointingHandCursor)
        self.icon_button.setFixedSize(self._icon_size, self._icon_size)
        self.icon_button.setIconSize(self.icon_button.size())
        self.icon_button.setAutoRaise(True)

        self.slider_wrap = QWidget(self)
        self.slider_wrap.setObjectName("VolumeSliderWrap")

        slider_layout = QHBoxLayout(self.slider_wrap)
        slider_layout.setContentsMargins(self._slider_inner_pad_x, 0, self._slider_inner_pad_x, 0)
        slider_layout.setSpacing(0)

        self.slider = QSlider(Qt.Horizontal, self.slider_wrap)
        self.slider.setRange(0, 100)
        self.slider.setSingleStep(2)
        self.slider.setPageStep(8)
        self.slider.setTracking(True)
        slider_layout.addWidget(self.slider)

        self._reveal_anim = QPropertyAnimation(self, b"slider_width", self)
        self._reveal_anim.setDuration(150)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.icon_button.clicked.connect(self._toggle_mute)

        self._apply_style()
        self._layout_children()
        self._sync_ui_from_state(emit=False)

    @staticmethod
    def _icon_tint_color() -> QColor:
        parsed = QColor(str(getattr(tokens, "TEXT_PRIMARY", "#D4D4D4")).strip())
        return parsed if parsed.isValid() else QColor("#D4D4D4")

    def _tinted_volume_icon(self, icon_path: str) -> QIcon:
        source = QPixmap(icon_path)
        if source.isNull():
            return QIcon()

        tinted = QPixmap(source.size())
        tinted.fill(Qt.transparent)
        painter = QPainter(tinted)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, source)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), self._icon_tint_color())
        painter.end()
        return QIcon(tinted)

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            QWidget#IntegratedVolumeControl {{
                background: transparent;
                border: none;
                border-radius: 14px;
            }}
            QToolButton#VolumeIcon {{
                border: none;
                background: transparent;
                padding: 0;
                margin: 0;
            }}
            QToolButton#VolumeIcon:hover {{
                border: none;
                background: transparent;
            }}
            QToolButton#VolumeIcon:pressed {{
                border: none;
                background: transparent;
                padding: 0;
                margin: 0;
            }}
            QWidget#VolumeSliderWrap {{
                background: transparent;
                border: none;
                border-radius: 10px;
            }}
            QSlider::groove:horizontal {{
                height: 5px;
                background: #0A0F18;
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {tokens.PRIMARY};
                border-radius: 3px;
            }}
            QSlider::add-page:horizontal {{
                background: #1C2740;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {tokens.TEXT_PRIMARY};
                border: 1px solid {tokens.SECONDARY};
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #ffffff;
                border-color: {tokens.ACCENT};
            }}
            """
        )

    def _layout_children(self):
        icon_x = self._pad_x
        icon_y = self._pad_y
        self.icon_button.move(icon_x, icon_y)

        slider_x = self._pad_x + self._icon_size + self._gap
        slider_y = self._pad_y + (self._icon_size - self._slider_h) // 2
        self.slider_wrap.setGeometry(slider_x, slider_y, self._slider_width, self._slider_h)
        self.slider_wrap.setVisible(self._slider_width > 0)

    def resizeEvent(self, event):
        self._layout_children()
        super().resizeEvent(event)

    def _icon_state_for_volume(self, vol: float) -> str:
        if self._muted or vol <= 0.0:
            return "muted"
        if vol <= 0.33:
            return "low"
        if vol <= 0.66:
            return "medium"
        return "high"

    def _sync_ui_from_state(self, *, emit: bool):
        slider_val = 0 if self._muted else int(round(self._volume * 100))
        blocked = self.slider.blockSignals(True)
        self.slider.setValue(slider_val)
        self.slider.blockSignals(blocked)

        state = self._icon_state_for_volume(self._volume)
        self.icon_button.setIcon(self._tinted_volume_icon(self._icon_paths[state]))

        if emit:
            effective = 0.0 if self._muted else self._volume
            self.volume_changed.emit(effective)
            self.mute_toggled.emit(self._muted)

    def _on_slider_changed(self, value: int):
        vol = max(0.0, min(1.0, value / 100.0))
        self._volume = vol
        self._muted = vol <= 0.0
        if vol > 0.0:
            self._last_nonzero_volume = vol
        self._sync_ui_from_state(emit=True)

    def _toggle_mute(self):
        if self._muted:
            restore = self._last_nonzero_volume if self._last_nonzero_volume > 0 else 0.8
            self._muted = False
            self._volume = restore
        else:
            if self._volume > 0:
                self._last_nonzero_volume = self._volume
            self._muted = True
        self._sync_ui_from_state(emit=True)

    def _expand_slider(self):
        self._collapse_timer.stop()
        self._reveal_anim.stop()
        self._reveal_anim.setStartValue(self._slider_width)
        self._reveal_anim.setEndValue(self._expanded_slider_w)
        self._reveal_anim.start()

    def _collapse_slider(self):
        self._reveal_anim.stop()
        self._reveal_anim.setStartValue(self._slider_width)
        self._reveal_anim.setEndValue(0)
        self._reveal_anim.start()

    def enterEvent(self, event):
        self._expand_slider()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._collapse_timer.start()
        super().leaveEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        step = 0.03
        current = 0.0 if self._muted else self._volume
        next_vol = current + (step if delta > 0 else -step)
        next_vol = max(0.0, min(1.0, next_vol))

        self._muted = next_vol <= 0.0
        self._volume = next_vol
        if next_vol > 0.0:
            self._last_nonzero_volume = next_vol
        self._sync_ui_from_state(emit=True)
        event.accept()

    def get_slider_width(self):
        return self._slider_width

    def set_slider_width(self, width):
        self._slider_width = max(0, min(self._expanded_slider_w, int(width)))
        self._layout_children()

    slider_width = Property(int, get_slider_width, set_slider_width)

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, float(volume)))
        self._muted = self._volume <= 0.0
        if self._volume > 0.0:
            self._last_nonzero_volume = self._volume
        self._sync_ui_from_state(emit=False)

    def volume(self) -> float:
        return 0.0 if self._muted else self._volume

    def set_muted(self, muted: bool):
        self._muted = bool(muted)
        if not self._muted and self._volume <= 0.0:
            self._volume = self._last_nonzero_volume if self._last_nonzero_volume > 0 else 0.8
        self._sync_ui_from_state(emit=False)

    def is_muted(self) -> bool:
        return self._muted
