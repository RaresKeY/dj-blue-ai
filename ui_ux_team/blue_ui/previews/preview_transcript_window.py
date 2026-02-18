import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.views.transcript_window import TranscriptWindowView


class TranscriptWindowPreview(TranscriptWindowView):
    def __init__(self):
        super().__init__()
        self.append_segment("[00:00:00 - 00:00:30] Preview transcript segment")
        self.resize(500, 700)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscriptWindowPreview()
    window.show()
    sys.exit(app.exec())
