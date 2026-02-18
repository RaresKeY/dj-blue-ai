from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ui_ux_team.blue_ui.theme import tokens


def _parse_color(value: str, fallback: str) -> QColor:
    color = QColor((value or "").strip())
    if color.isValid():
        return color
    fallback_color = QColor(fallback)
    return fallback_color if fallback_color.isValid() else QColor("#FFFFFF")


def _color_with_alpha(value: str, alpha: float, fallback: str) -> str:
    c = _parse_color(value, fallback)
    a = max(0.0, min(1.0, float(alpha)))
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a:.3f})"


def _is_light_color(value: str, fallback: str = "#1E1E1E") -> bool:
    return _parse_color(value, fallback).lightnessF() >= 0.55


class SettingsSection(QFrame):
    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("settingsSection")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(6)

        self._title = QLabel(title)
        self._title.setObjectName("settingsSectionTitle")
        root.addWidget(self._title)

        self._description = QLabel(description)
        self._description.setObjectName("settingsSectionDescription")
        self._description.setWordWrap(True)
        self._description.setVisible(bool(description.strip()))
        root.addWidget(self._description)

        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(6)
        root.addLayout(self._content)
        self.refresh_theme()

    def content_layout(self) -> QVBoxLayout:
        return self._content

    def set_description(self, text: str) -> None:
        cleaned = str(text or "").strip()
        self._description.setText(cleaned)
        self._description.setVisible(bool(cleaned))

    def refresh_theme(self) -> None:
        bg_main = getattr(tokens, "COLOR_BG_MAIN", "#1E1E1E")
        text_primary = getattr(tokens, "TEXT_PRIMARY", "#D4D4D4")
        is_light_theme = _is_light_color(bg_main, "#1E1E1E")
        card_bg = _color_with_alpha(text_primary, 0.045 if is_light_theme else 0.03, text_primary)
        self.setStyleSheet(
            f"""
            QFrame#settingsSection {{
                background: {card_bg};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 10px;
            }}
            QLabel#settingsSectionTitle {{
                font-size: 14px;
                font-weight: 700;
                color: {tokens.TEXT_PRIMARY};
            }}
            QLabel#settingsSectionDescription {{
                font-size: 12px;
                color: {tokens.TEXT_MUTED};
            }}
            """
        )
