import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.views.transcript_window import TranscriptWindowView


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscriptWindowView()
    window.append_segment("[00:00:00 - 00:00:30] Preview transcript segment")
    window.resize(500, 700)
    window.show()
    raise SystemExit(app.exec())
