from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QWidget, QSlider, QVBoxLayout, QLabel

from .image_button import ImageButton


class VolumeButton(ImageButton):
    interaction_start = Signal()
    interaction_move = Signal(QPoint)
    interaction_end = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.interaction_start.emit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.interaction_move.emit(event.globalPosition().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.interaction_end.emit()
        super().mouseReleaseEvent(event)


class VolumePopup(QWidget):
    volume_changed = Signal(float)
    closed = Signal()

    def __init__(self, parent=None, current_volume=1.0):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(74, 248)

        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(current_volume * 100))
        self.slider.setSingleStep(2)
        self.slider.setPageStep(8)
        self.slider.setInvertedAppearance(False)
        self.slider.setTracking(True)

        self.value_label = QLabel(self)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setObjectName("VolumeValue")

        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.value_label)
        layout.addWidget(self.slider)
        self._on_value_changed(self.slider.value())
        self.slider.valueChanged.connect(self._on_value_changed)

    def _apply_style(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #14161b;
                border: 1px solid #2a2f3a;
                border-radius: 16px;
            }
            QLabel#VolumeValue {
                background: #1d2230;
                color: #dbe3f4;
                border: 1px solid #323a4a;
                border-radius: 10px;
                padding: 4px 0;
                font-size: 11px;
                font-weight: 600;
                min-height: 18px;
            }
            QSlider::groove:vertical {
                background: #1f2530;
                border: 1px solid #2d3645;
                border-radius: 6px;
                width: 10px;
                margin: 6px 0;
            }
            QSlider::sub-page:vertical {
                background: #5f8cff;
                border-radius: 6px;
            }
            QSlider::add-page:vertical {
                background: #161b25;
                border-radius: 6px;
            }
            QSlider::handle:vertical {
                background: #f5f8ff;
                border: 1px solid #b7c9f7;
                height: 16px;
                width: 16px;
                margin: -2px -6px;
                border-radius: 8px;
            }
            QSlider::handle:vertical:hover {
                background: #ffffff;
                border-color: #8eb0ff;
            }
            """
        )

    def _on_value_changed(self, value: int):
        self.value_label.setText(f"{value}%")
        self.volume_changed.emit(value / 100.0)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
