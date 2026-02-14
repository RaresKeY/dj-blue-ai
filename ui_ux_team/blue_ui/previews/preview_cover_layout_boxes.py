import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def labeled_box(name: str, bg: str, border: str = "#FFFFFF", min_h: int = 36) -> tuple[QFrame, QWidget]:
    box = QFrame()
    box.setMinimumHeight(min_h)
    box.setFrameShape(QFrame.NoFrame)
    box.setStyleSheet(
        f"""
        QFrame {{
            background: {bg};
            border: 2px solid {border};
            border-radius: 8px;
        }}
        QLabel {{
            color: #FFFFFF;
            background: transparent;
            border: none;
            font-weight: 700;
            font-size: 12px;
        }}
        QWidget {{
            background: transparent;
            border: none;
        }}
        """
    )

    outer = QVBoxLayout(box)
    outer.setContentsMargins(8, 6, 8, 6)
    outer.setSpacing(4)

    title = QLabel(name)
    title.setAlignment(Qt.AlignCenter)
    outer.addWidget(title, 0, Qt.AlignTop)

    content = QWidget()
    outer.addWidget(content, 1)
    return box, content


class CoverLayoutBoxesPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cover Segment Layout Boxes")
        self.resize(960, 560)
        self.setStyleSheet("QWidget { background: #181A20; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("Debug Preview: Cover Segment Layout Boundaries")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800;")
        root.addWidget(title)

        segment_root, segment_content = labeled_box(
            "SEGMENT_ROOT (covers area)",
            "#1F2430",
            border="#7B88A8",
            min_h=450,
        )
        root.addWidget(segment_root, 1)

        segment_layout = QVBoxLayout(segment_content)
        segment_layout.setContentsMargins(2, 2, 2, 2)
        segment_layout.setSpacing(0)
        segment_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        top_row, top_content = labeled_box(
            "TOP_ROW (cover images row)",
            "#2A3142",
            border="#8BA3D9",
            min_h=290,
        )
        segment_layout.addWidget(top_row, 0, Qt.AlignTop)

        top_layout = QHBoxLayout(top_content)
        top_layout.setContentsMargins(10, 8, 10, 0)
        top_layout.setSpacing(6)
        top_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        prev_cover, _ = labeled_box("PREV_COVER", "#3A5F8E", border="#B4D5FF", min_h=120)
        current_cover, _ = labeled_box("CURRENT_COVER", "#6D4B9E", border="#E2CCFF", min_h=170)
        next_cover, _ = labeled_box("NEXT_COVER", "#3A5F8E", border="#B4D5FF", min_h=120)
        prev_cover.setFixedSize(150, 150)
        current_cover.setFixedSize(220, 220)
        next_cover.setFixedSize(150, 150)
        top_layout.addWidget(prev_cover, 0, Qt.AlignVCenter)
        top_layout.addWidget(current_cover, 0, Qt.AlignVCenter)
        top_layout.addWidget(next_cover, 0, Qt.AlignVCenter)

        bottom_row, bottom_content = labeled_box(
            "BOTTOM_ROW (title labels row, directly below covers)",
            "#263327",
            border="#9AD19A",
            min_h=62,
        )
        segment_layout.addWidget(bottom_row, 0, Qt.AlignTop)

        bottom_layout = QHBoxLayout(bottom_content)
        bottom_layout.setContentsMargins(10, 0, 10, 2)
        bottom_layout.setSpacing(6)
        bottom_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        prev_title, _ = labeled_box("PREV_TITLE_SLOT", "#2F4F2F", border="#9EE59E", min_h=28)
        current_title, _ = labeled_box("CURRENT_TITLE_SLOT", "#3C5C3C", border="#C7F6C7", min_h=28)
        next_title, _ = labeled_box("NEXT_TITLE_SLOT", "#2F4F2F", border="#9EE59E", min_h=28)
        prev_title.setFixedWidth(150)
        current_title.setFixedWidth(220)
        next_title.setFixedWidth(150)
        bottom_layout.addWidget(prev_title, 0, Qt.AlignTop)
        bottom_layout.addWidget(current_title, 0, Qt.AlignTop)
        bottom_layout.addWidget(next_title, 0, Qt.AlignTop)

        note = QLabel(
            "Goal alignment: title slots are centered under their matching cover widths; "
            "BOTTOM_ROW should be visually tight under TOP_ROW."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #D7E3FF; font-size: 12px;")
        root.addWidget(note)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoverLayoutBoxesPreview()
    window.show()
    raise SystemExit(app.exec())
