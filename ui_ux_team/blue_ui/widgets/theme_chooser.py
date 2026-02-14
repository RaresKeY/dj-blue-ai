from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenu, QPushButton, QWidget, QVBoxLayout

from ui_ux_team.blue_ui.theme import current_theme_key, list_themes, set_theme, theme_label
from ui_ux_team.blue_ui.theme import tokens


def _with_alpha(color: str, alpha: float) -> str:
    c = (color or "").strip()
    a = max(0.0, min(1.0, float(alpha)))
    if c.startswith("#") and len(c) in (4, 7):
        if len(c) == 4:
            r = int(c[1] * 2, 16)
            g = int(c[2] * 2, 16)
            b = int(c[3] * 2, 16)
        else:
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
        return f"rgba({r}, {g}, {b}, {a:.3f})"
    return c


class ThemeChooserMenu(QWidget):
    theme_selected = Signal(str)

    def __init__(self, parent=None, title: str = "Theme"):
        super().__init__(parent)
        self._button = QPushButton(title, self)
        self._menu = QMenu(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._button)

        self._button.setMenu(self._menu)
        self._build_menu()
        self.refresh_theme()
        self._refresh_button_text()

    def _build_menu(self):
        self._menu.clear()
        for key, data in list_themes().items():
            action = self._menu.addAction(data.get("label", key))
            action.triggered.connect(lambda _checked=False, theme_key=key: self.select_theme(theme_key))

    def _refresh_button_text(self):
        key = current_theme_key()
        self._button.setText(f"Theme: {theme_label(key)}")

    def select_theme(self, theme_key: str):
        set_theme(theme_key)
        self.refresh_theme()
        self._refresh_button_text()
        self.theme_selected.emit(theme_key)

    def refresh_theme(self):
        button_bg = _with_alpha(tokens.BG_INPUT, 1.0)
        menu_bg = _with_alpha(tokens.BG_INPUT, 1.0)
        selected_bg = _with_alpha(tokens.PRIMARY, 0.22)
        selected_text = tokens.TEXT_PRIMARY

        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {button_bg};
                color: {tokens.TEXT_PRIMARY};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {tokens.PRIMARY};
            }}
            QMenu {{
                background: {menu_bg};
                color: {tokens.TEXT_PRIMARY};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 10px;
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background: {selected_bg};
                color: {selected_text};
            }}
            """
        )
