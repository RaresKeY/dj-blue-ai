from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.theme.native_window import apply_native_titlebar_for_theme
from ui_ux_team.blue_ui.widgets.image_button import ImageButton
from ui_ux_team.blue_ui.widgets.text_boxes import TextBox, SearchBar


class TranscriptWindowView(QWidget):
    closed = Signal()
    record_clicked = Signal()

    def __init__(self, parent=None):
        # Keep transcript as a separate top-level window (original py_learn behavior).
        super().__init__()
        self.setWindowTitle("Transcript")

        layout = QVBoxLayout(self)
        top_box = QHBoxLayout()

        self.record_button = ImageButton(resource_path("ui_ux_team/assets/record_black_off.png"), size=(65, 65))
        self.record_button.clicked.connect(self.record_clicked.emit)

        self.search_bar = SearchBar()
        self.text_box = TextBox()

        top_box.addWidget(self.record_button)
        top_box.addWidget(self.search_bar)

        self.recording_status = QLabel("")
        self.recording_status.setObjectName("recording_status")
        self.recording_status.hide()
        self._recording_status_base = "is recording"
        self._recording_status_dots = 3
        self._recording_status_timer = QTimer(self)
        self._recording_status_timer.setInterval(360)
        self._recording_status_timer.timeout.connect(self._tick_recording_status)

        layout.addLayout(top_box, 1)
        layout.addWidget(self.recording_status, 0)
        layout.addWidget(self.text_box, 9)
        self.refresh_theme()

    def append_segment(self, seg: str):
        self.text_box.appendPlainText(seg)

    def set_search_query(self, query: str):
        self.search_bar.setPlainText(query)

    def set_recording_active(self, is_active: bool):
        icon = "assets/record_black.png" if is_active else "assets/record_black_off.png"
        self.record_button.set_image(icon)
        if is_active:
            self._recording_status_dots = 3
            self.recording_status.setText(self._recording_status_text())
            self.recording_status.show()
            if not self._recording_status_timer.isActive():
                self._recording_status_timer.start()
        else:
            self._recording_status_timer.stop()
            self.recording_status.hide()

    def _recording_status_text(self) -> str:
        return f"{self._recording_status_base}{'.' * self._recording_status_dots}"

    def _tick_recording_status(self):
        self._recording_status_dots = (self._recording_status_dots + 1) % 4
        self.recording_status.setText(self._recording_status_text())

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {tokens.COLOR_BG_MAIN};
                color: {tokens.TEXT_PRIMARY};
            }}
            QLabel#recording_status {{
                color: {tokens.ACCENT};
                font-size: 13px;
                font-weight: 700;
                padding: 0 4px 2px 8px;
            }}
            """
        )
        apply_native_titlebar_for_theme(self)
        self.search_bar.refresh_theme()
        self.text_box.refresh_theme()

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)
