import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

project_root = Path(__file__).resolve()
while project_root.name != "ui_ux_team" and project_root != project_root.parent:
    project_root = project_root.parent
project_root = project_root.parent if project_root.name == "ui_ux_team" else Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.tests.iteration.dev.cover_segment_vertical_slips_layout import (
    CoverSegmentVerticalSlipsLayoutTestComponent,
)


class CoverSegmentVerticalSlipsLayoutPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cover Segment Vertical Slips Layout")
        self.resize(930, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)
        root.addWidget(CoverSegmentVerticalSlipsLayoutTestComponent(), 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    window = CoverSegmentVerticalSlipsLayoutPreview()
    window.show()
    raise SystemExit(app.exec())

