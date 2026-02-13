import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.widgets.image_button import ImageButton
from ui_ux_team.blue_ui.widgets.marquee import QueuedMarqueeLabel
from ui_ux_team.blue_ui.widgets.text_boxes import TextBoxAI, InputBlueBird


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)

    btn = ImageButton(resource_path("ui_ux_team/assets/play.png"), size=(60, 60))
    marquee = QueuedMarqueeLabel(["Preview mood A", "Preview mood B"], hold_ms=1200, fade_ms=150)
    text_box = TextBoxAI()
    text_box.append_message("system", "Widget preview mode")
    input_box = InputBlueBird()

    layout.addWidget(btn)
    layout.addWidget(marquee)
    layout.addWidget(text_box)
    layout.addWidget(input_box)

    window.resize(500, 600)
    window.show()
    raise SystemExit(app.exec())
