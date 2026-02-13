import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.widgets.volume import IntegratedVolumeControl


class VolumePreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Volume Component Preview")
        self.resize(420, 220)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        title = QLabel("Integrated Volume Control")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 700;")

        self.value_label = QLabel("Volume: 80% | Muted: False")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 13px; color: #dbe3f4;")

        hint = QLabel("Hover to reveal slider | Click icon to mute | Wheel to adjust")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #8f97aa;")

        self.control = IntegratedVolumeControl(initial_volume=0.80)
        self.control.volume_changed.connect(self._on_volume_changed)
        self.control.mute_toggled.connect(self._on_mute_toggled)

        root.addWidget(title)
        root.addWidget(self.value_label)
        root.addWidget(self.control, alignment=Qt.AlignCenter)
        root.addWidget(hint)
        root.addStretch(1)

        self._muted = False

    def _on_volume_changed(self, volume: float):
        self.value_label.setText(f"Volume: {int(volume * 100)}% | Muted: {self._muted}")

    def _on_mute_toggled(self, muted: bool):
        self._muted = muted
        self.value_label.setText(f"Volume: {int(self.control.volume() * 100)}% | Muted: {muted}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VolumePreview()
    win.show()
    raise SystemExit(app.exec())
