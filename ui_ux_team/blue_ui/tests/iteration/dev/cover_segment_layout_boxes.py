from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


def _labeled_box(name: str, bg: str, border: str, min_h: int = 28) -> tuple[QFrame, QWidget]:
    frame = QFrame()
    frame.setObjectName(name)
    frame.setMinimumHeight(min_h)
    frame.setFrameShape(QFrame.NoFrame)
    frame.setStyleSheet(
        f"""
        QFrame#{name} {{
            background: {bg};
            border: 2px solid {border};
            border-radius: 7px;
        }}
        QLabel {{
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            background: transparent;
            border: none;
        }}
        QWidget {{
            background: transparent;
            border: none;
        }}
        """
    )

    root = QVBoxLayout(frame)
    root.setContentsMargins(6, 4, 6, 4)
    root.setSpacing(3)

    label = QLabel(name)
    label.setAlignment(Qt.AlignCenter)
    root.addWidget(label, 0, Qt.AlignTop)

    content = QWidget()
    root.addWidget(content, 1)
    return frame, content


class CoverSegmentLayoutBoxesTestComponent(QWidget):
    """Persistent layout scaffold for cover segment alignment iteration.

    Hierarchy:
    - COVER_SEGMENT_ROOT
      - COVER_COLUMNS_ROW
        - PREV_COLUMN_STRIP
          - PREV_COVER_SLOT
          - PREV_TITLE_SLOT
        - CURRENT_COLUMN_STRIP
          - CURRENT_COVER_SLOT
          - CURRENT_TITLE_SLOT
        - NEXT_COLUMN_STRIP
          - NEXT_COVER_SLOT
          - NEXT_TITLE_SLOT
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CoverSegmentLayoutBoxesTestComponent")
        self.setMinimumSize(900, 460)

        page = QVBoxLayout(self)
        page.setContentsMargins(16, 16, 16, 16)
        page.setSpacing(10)

        root_box, root_content = _labeled_box(
            "COVER_SEGMENT_ROOT",
            "#1E2432",
            border="#8392B5",
            min_h=390,
        )
        page.addWidget(root_box, 1)

        root_layout = QVBoxLayout(root_content)
        root_layout.setContentsMargins(2, 2, 2, 2)
        root_layout.setSpacing(0)
        root_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        columns_row_box, columns_row_content = _labeled_box(
            "COVER_COLUMNS_ROW",
            "#2A3348",
            border="#93B1E5",
            min_h=336,
        )
        root_layout.addWidget(columns_row_box, 0, Qt.AlignTop)

        columns_layout = QHBoxLayout(columns_row_content)
        columns_layout.setContentsMargins(8, 8, 8, 4)
        columns_layout.setSpacing(6)
        columns_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        prev_col, prev_col_content = _labeled_box("PREV_COLUMN_STRIP", "#334F70", border="#B7D9FF", min_h=256)
        current_col, current_col_content = _labeled_box("CURRENT_COLUMN_STRIP", "#5C4787", border="#DEC8FF", min_h=326)
        next_col, next_col_content = _labeled_box("NEXT_COLUMN_STRIP", "#334F70", border="#B7D9FF", min_h=256)
        prev_col.setFixedWidth(150)
        current_col.setFixedWidth(220)
        next_col.setFixedWidth(150)
        columns_layout.addWidget(prev_col, 0, Qt.AlignTop)
        columns_layout.addWidget(current_col, 0, Qt.AlignTop)
        columns_layout.addWidget(next_col, 0, Qt.AlignTop)

        prev_col_layout = QVBoxLayout(prev_col_content)
        prev_col_layout.setContentsMargins(0, 0, 0, 0)
        prev_col_layout.setSpacing(0)
        prev_col_layout.setAlignment(Qt.AlignTop)
        prev_cover, _ = _labeled_box("PREV_COVER_SLOT", "#365985", border="#B7D9FF", min_h=120)
        prev_cover.setFixedHeight(150)
        prev_title, _ = _labeled_box("PREV_TITLE_SLOT", "#2F4E2F", border="#B0EAB0", min_h=26)
        prev_title.setFixedHeight(34)
        prev_col_layout.addWidget(prev_cover, 0, Qt.AlignTop)
        prev_col_layout.addWidget(prev_title, 0, Qt.AlignTop)

        current_col_layout = QVBoxLayout(current_col_content)
        current_col_layout.setContentsMargins(0, 0, 0, 0)
        current_col_layout.setSpacing(0)
        current_col_layout.setAlignment(Qt.AlignTop)
        current_cover, _ = _labeled_box("CURRENT_COVER_SLOT", "#644998", border="#DEC8FF", min_h=180)
        current_cover.setFixedHeight(220)
        current_title, _ = _labeled_box("CURRENT_TITLE_SLOT", "#3A5E3A", border="#D2F9D2", min_h=26)
        current_title.setFixedHeight(34)
        current_col_layout.addWidget(current_cover, 0, Qt.AlignTop)
        current_col_layout.addWidget(current_title, 0, Qt.AlignTop)

        next_col_layout = QVBoxLayout(next_col_content)
        next_col_layout.setContentsMargins(0, 0, 0, 0)
        next_col_layout.setSpacing(0)
        next_col_layout.setAlignment(Qt.AlignTop)
        next_cover, _ = _labeled_box("NEXT_COVER_SLOT", "#365985", border="#B7D9FF", min_h=120)
        next_cover.setFixedHeight(150)
        next_title, _ = _labeled_box("NEXT_TITLE_SLOT", "#2F4E2F", border="#B0EAB0", min_h=26)
        next_title.setFixedHeight(34)
        next_col_layout.addWidget(next_cover, 0, Qt.AlignTop)
        next_col_layout.addWidget(next_title, 0, Qt.AlignTop)
