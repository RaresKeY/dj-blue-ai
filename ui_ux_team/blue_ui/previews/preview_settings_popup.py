import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from architects.helpers.tabs_audio import get_display_names
from ui_ux_team.blue_ui.config import default_music_folder
from ui_ux_team.blue_ui.theme import ensure_default_theme, set_theme
from ui_ux_team.blue_ui.views.settings_popup import SettingsPopup
from ui_ux_team.blue_ui.widgets.api_usage_limits_form import APIUsageLimitsForm
from ui_ux_team.blue_ui.widgets.theme_chooser import ThemeChooserMenu


def _apply_preview_theme() -> None:
    ensure_default_theme()
    requested = str(os.getenv("BLUE_UI_PREVIEW_THEME", "")).strip()
    if not requested:
        return
    try:
        set_theme(requested)
    except Exception:
        pass


def _build_music_tab() -> QWidget:
    music_tab = QWidget()
    layout = QVBoxLayout(music_tab)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(10)
    title = QLabel("Music folder")
    title.setStyleSheet("font-size: 14px; font-weight: 600;")
    path_edit = QLineEdit(str(default_music_folder()))
    path_edit.setReadOnly(True)
    pick_btn = QPushButton("Choose folder")
    layout.addWidget(title)
    layout.addWidget(path_edit)
    layout.addWidget(pick_btn, alignment=Qt.AlignLeft)
    layout.addStretch(1)
    return music_tab


def _build_theme_tab() -> QWidget:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(8)
    chooser = ThemeChooserMenu()
    layout.addWidget(chooser)
    layout.addStretch(1)
    return tab


class SettingsPopupPreview(SettingsPopup):
    def __init__(self):
        _apply_preview_theme()
        recording_tabs = QListWidget()
        recording_tabs.addItems(
            [f"{x} | {(y[:30].rstrip() + '...') if len(y) > 30 else y}" for x, y in get_display_names()]
        )
        recording_tabs.setObjectName("settingsPreviewRecordingSources")

        super().__init__(
            {
                "Recording Sources": recording_tabs,
                "Theme Selection": _build_theme_tab(),
                "Music Library": _build_music_tab(),
                "API Usage Limits": APIUsageLimitsForm(),
            },
            parent=None,
            margin=24,
        )
        for idx in range(self.list.count()):
            if self.list.item(idx).text() == "API Usage Limits":
                self.list.setCurrentRow(idx)
                break
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowTitle("Settings Popup Preview")
        self.resize(940, 620)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    _apply_preview_theme()
    window = SettingsPopupPreview()
    window.show()
    raise SystemExit(app.exec())
