from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.theme import tokens
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

        record_button = ImageButton(resource_path("ui_ux_team/assets/record_black.png"), size=(65, 65))
        record_button.clicked.connect(self.record_clicked.emit)

        self.search_bar = SearchBar()
        self.text_box = TextBox()

        top_box.addWidget(record_button)
        top_box.addWidget(self.search_bar)

        layout.addLayout(top_box, 1)
        layout.addWidget(self.text_box, 9)
        self.refresh_theme()

    def append_segment(self, seg: str):
        self.text_box.appendPlainText(seg)

    def set_search_query(self, query: str):
        self.search_bar.setPlainText(query)

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {tokens.COLOR_BG_MAIN};
                color: {tokens.TEXT_PRIMARY};
            }}
            """
        )
        self.search_bar.refresh_theme()
        self.text_box.refresh_theme()

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)
