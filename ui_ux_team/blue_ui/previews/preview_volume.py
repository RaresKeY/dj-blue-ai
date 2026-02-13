import sys
from pathlib import Path

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.views.main_window import MainUI
from ui_ux_team.blue_ui.widgets.image_button import IMAGE_NOT_FOUND
from ui_ux_team.blue_ui.widgets.volume import VolumeButton, VolumePopup


class VolumePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Volume Component Preview")
        self.resize(320, 240)

        self._volume_popup = None
        self._current_volume = 0.80

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Volume Control")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 700;")

        self.value_label = QLabel(self._format_volume(self._current_volume))
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 14px; color: #dbe3f4;")

        row = QHBoxLayout()
        row.addStretch(1)

        self.volume_button = VolumeButton(
            path=MainUI.build_path("assets/volume_button.png"),
            size=(56, 56),
            fallback=IMAGE_NOT_FOUND,
        )
        self.volume_button.interaction_start.connect(self.on_volume_start)
        self.volume_button.interaction_move.connect(self.on_volume_move)
        self.volume_button.interaction_end.connect(self.on_volume_end)

        row.addWidget(self.volume_button)
        row.addStretch(1)

        hint = QLabel("Click or drag on the icon")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #8f97aa;")

        root.addWidget(title)
        root.addWidget(self.value_label)
        root.addLayout(row)
        root.addWidget(hint)
        root.addStretch(1)

    def _format_volume(self, volume: float) -> str:
        return f"Volume: {int(volume * 100)}%"

    def set_volume(self, volume: float):
        self._current_volume = volume
        self.value_label.setText(self._format_volume(volume))

    def on_volume_start(self):
        current_vol = self._current_volume

        if not self._volume_popup:
            self._volume_popup = VolumePopup(parent=self.volume_button, current_volume=current_vol)
            self._volume_popup.volume_changed.connect(self.set_volume)
            self._volume_popup.closed.connect(lambda: setattr(self, "_volume_popup", None))

        self._volume_popup.show()

        popup_w = self._volume_popup.width()
        popup_h = self._volume_popup.height()
        button = self.volume_button
        local_offset = QPoint((button.width() - popup_w) // 2 + button.width() // 2, -popup_h - 10)
        self._volume_popup.move(button.mapToGlobal(local_offset))

    def on_volume_move(self, global_pos):
        if self._volume_popup and self._volume_popup.isVisible():
            slider = self._volume_popup.slider
            local_pos = slider.mapFromGlobal(global_pos)
            h = slider.height()
            y = max(0, min(h, local_pos.y()))
            ratio = 1.0 - (y / h) if h > 0 else 0.0
            slider.setValue(int(ratio * slider.maximum()))

    def on_volume_end(self):
        if self._volume_popup:
            self._volume_popup.close()
            self._volume_popup = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VolumePreview()
    win.show()
    raise SystemExit(app.exec())
