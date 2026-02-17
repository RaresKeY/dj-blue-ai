from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QLineEdit, QFrame

from ui_ux_team.blue_ui.app.secure_api_key import backend_display_name, clear_api_key, read_api_key, save_api_key
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.theme.native_window import apply_native_titlebar_for_theme


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


def _status_error_color(bg_color: str) -> str:
    # Keep warning/error copy readable on both bright and dark backgrounds.
    return "#B42318" if _is_light_color(bg_color, "#F3F3F3") else "#FF8A8A"


class APISettingsWindowView(QWidget):
    closed = Signal()
    api_key_saved = Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("API Settings")
        self.setMinimumSize(470, 360)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        title = QLabel("AI Studio API Key")
        title.setObjectName("apiSettingsTitle")

        subtitle = QLabel(
            "Store your key securely in your OS keychain backend. "
            "The app reads it automatically at runtime."
        )
        subtitle.setObjectName("apiSettingsSubtitle")
        subtitle.setWordWrap(True)

        backend = QLabel(f"Detected secure backend: {backend_display_name()}")
        backend.setObjectName("apiSettingsBackend")
        backend.setWordWrap(True)

        self.status = QLabel("")
        self.status.setObjectName("apiSettingsStatus")
        self.status.setWordWrap(True)

        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setPlaceholderText("Paste AI_STUDIO_API_KEY here")
        self.key_input.returnPressed.connect(self._save_key)

        save_btn = QPushButton("Save Securely")
        save_btn.clicked.connect(self._save_key)

        key_row.addWidget(self.key_input, 1)
        key_row.addWidget(save_btn, 0)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        clear_btn = QPushButton("Clear Stored Key")
        clear_btn.clicked.connect(self._clear_key)
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self.refresh_status)
        action_row.addWidget(clear_btn, 0)
        action_row.addWidget(refresh_btn, 0)
        action_row.addStretch(1)

        hints_card = QFrame()
        hints_card.setObjectName("apiSettingsHints")
        hints_layout = QVBoxLayout(hints_card)
        hints_layout.setContentsMargins(12, 10, 12, 10)
        hints_layout.setSpacing(6)

        hints_title = QLabel("Where to inspect stored credentials")
        hints_title.setObjectName("apiSettingsHintsTitle")
        hints_body = QLabel(
            "Linux: Seahorse (Passwords and Keys)\n"
            "macOS: Keychain Access\n"
            "Windows: Credential Manager\n\n"
            "Service name: dj-blue-ai\n"
            "Keys: AI_STUDIO_API_KEY, AI_STUDIO"
        )
        hints_body.setObjectName("apiSettingsHintsBody")
        hints_body.setWordWrap(True)
        hints_body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        hints_layout.addWidget(hints_title)
        hints_layout.addWidget(hints_body)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(backend)
        root.addLayout(key_row)
        root.addLayout(action_row)
        root.addWidget(self.status)
        root.addWidget(hints_card)
        root.addStretch(1)
        self.refresh_theme()
        self.refresh_status()

    def _set_status(self, message: str, is_error: bool = False):
        self.status.setText(message)
        accent = _status_error_color(getattr(tokens, "COLOR_BG_MAIN", "#1E1E1E")) if is_error else tokens.ACCENT
        self.status.setStyleSheet(
            f"color: {accent}; font-size: 12px; font-weight: 600; padding-top: 2px;"
        )

    def refresh_status(self):
        key, error = read_api_key()
        if key:
            masked = f"{key[:4]}...{key[-4:]}" if len(key) >= 8 else "***"
            self._set_status(f"Stored key detected ({masked}).")
            return
        if error:
            self._set_status(f"No key available. {error}", is_error=True)
            return
        self._set_status("No stored key found. Save one to enable transcription.", is_error=True)

    def _save_key(self):
        ok, message = save_api_key(self.key_input.text())
        self._set_status(message, is_error=not ok)
        if ok:
            self.api_key_saved.emit()
            self.key_input.clear()
        self.refresh_status()

    def _clear_key(self):
        ok, message = clear_api_key()
        self._set_status(message, is_error=not ok)
        self.refresh_status()

    def refresh_theme(self):
        bg_main = getattr(tokens, "COLOR_BG_MAIN", "#1E1E1E")
        accent = getattr(tokens, "ACCENT", "#FF9B54")
        text_primary = getattr(tokens, "TEXT_PRIMARY", "#D4D4D4")
        is_light_theme = _is_light_color(bg_main, "#1E1E1E")
        button_bg_idle = _color_with_alpha(accent, 0.11 if is_light_theme else 0.14, accent)
        button_bg_hover = _color_with_alpha(accent, 0.19 if is_light_theme else 0.24, accent)
        button_border = _color_with_alpha(accent, 0.66 if is_light_theme else 0.62, accent)
        hints_bg = _color_with_alpha(text_primary, 0.045 if is_light_theme else 0.03, text_primary)
        placeholder = _color_with_alpha(getattr(tokens, "TEXT_MUTED", "#A9B1BA"), 0.72, "#A9B1BA")

        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {bg_main};
                color: {text_primary};
            }}
            QLabel#apiSettingsTitle {{
                font-size: 21px;
                font-weight: 700;
            }}
            QLabel#apiSettingsSubtitle {{
                font-size: 13px;
                color: {tokens.TEXT_MUTED};
            }}
            QLabel#apiSettingsBackend {{
                font-size: 13px;
                color: {tokens.TEXT_PRIMARY};
                padding: 2px 0 4px 0;
            }}
            QLineEdit {{
                background: {tokens.BG_INPUT};
                color: {text_primary};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 8px 10px;
            }}
            QLineEdit::placeholder {{
                color: {placeholder};
            }}
            QPushButton {{
                background: {button_bg_idle};
                color: {accent};
                border: 1px solid {button_border};
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {button_bg_hover};
            }}
            QFrame#apiSettingsHints {{
                background: {hints_bg};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 10px;
            }}
            QLabel#apiSettingsHintsTitle {{
                font-size: 13px;
                font-weight: 700;
            }}
            QLabel#apiSettingsHintsBody {{
                font-size: 12px;
                color: {tokens.TEXT_MUTED};
            }}
            """
        )
        apply_native_titlebar_for_theme(self)
        self.refresh_status()

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)
