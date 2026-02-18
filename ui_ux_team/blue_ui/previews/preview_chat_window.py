import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.views.chat_window import BlueBirdChatView


class BlueBirdChatPreview(BlueBirdChatView):
    def __init__(self):
        super().__init__(api_key=None, initial_transcript="Preview transcript context.")
        self.text_box.append_message("user", "Hello, how is the context?")
        self.text_box.append_message("model", "The context is **loaded** and ready for *analysis*.")
        self.resize(420, 640)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BlueBirdChatPreview()
    window.show()
    sys.exit(app.exec())
