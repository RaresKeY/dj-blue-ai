import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.widgets.theme_chooser import ThemeChooserMenu


class ThemePreviewWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blue UI Theme Chooser Preview")
        self.resize(560, 360)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)

        self.chooser = ThemeChooserMenu()
        self.chooser.theme_selected.connect(lambda _key: self.apply_theme())

        self.sample = QFrame()
        self.sample_layout = QVBoxLayout(self.sample)
        self.sample_layout.setContentsMargins(16, 16, 16, 16)
        self.sample_layout.setSpacing(8)

        self.title = QLabel("Sample Panel")
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text = QLabel("Pastel-shifted variants for Blue UI")
        self.text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.sample_layout.addWidget(self.title)
        self.sample_layout.addWidget(self.text)

        self.layout.addWidget(self.chooser)
        self.layout.addWidget(self.sample, 1)

        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {tokens.COLOR_BG_MAIN};
            }}
            QLabel {{
                color: {tokens.TEXT_PRIMARY};
                font-size: 15px;
            }}
            QFrame {{
                background: {tokens.COLOR_CONTROLS_BG};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 12px;
            }}
            """
        )
        self.title.setStyleSheet(
            f"color: {tokens.PRIMARY}; font-size: 18px; font-weight: 700; background: transparent;"
        )
        self.text.setStyleSheet(
            f"color: {tokens.TEXT_MUTED}; font-size: 14px; background: transparent;"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ensure_default_theme()
    window = ThemePreviewWindow()
    window.show()
    raise SystemExit(app.exec())
