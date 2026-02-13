import markdown
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTextBrowser, QTextEdit, QPlainTextEdit

from ui_ux_team.blue_ui.theme.styles import textbox_ai_style, input_style, textbox_style
from ui_ux_team.blue_ui.theme import tokens


class TextBoxAI(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setObjectName("TextBox")
        self.setOpenExternalLinks(True)
        self.refresh_theme()

    def refresh_theme(self):
        self.setStyleSheet(textbox_ai_style())

    def append_message(self, role: str, text: str):
        processed_text = text.replace("\n*", "\n\n*").replace("\n-", "\n\n-")
        html_content = markdown.markdown(processed_text, extensions=["extra", "sane_lists"])

        if role == "user":
            sender = "You"
            color = tokens.PRIMARY
        elif role == "model":
            sender = "BlueBird"
            color = tokens.ACCENT
        else:
            sender = "System"
            color = tokens.TEXT_MUTED

        html_block = f"""
        <div style=\"margin-top: 10px; margin-bottom: 5px;\">
            <span style=\"color: {color}; font-weight: bold; font-size: 16px;\">{sender}</span>
        </div>
        <div style=\"color: {tokens.TEXT_PRIMARY}; margin-bottom: 10px;\">{html_content}</div>
        <hr style=\"background-color: #2A3550; height: 1px; border: none; margin: 10px 0;\">
        """

        self.append("")
        self.insertHtml(html_block)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class InputBlueBird(QTextEdit):
    message_sent = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("InputChat")
        font = QFont()
        font.setPointSize(13)
        self.setFont(font)
        self.setFixedHeight(70)
        self.setPlaceholderText("Type a message to BlueBird AI (Ctrl+Enter to send)")
        self.refresh_theme()

    def refresh_theme(self):
        self.setStyleSheet(input_style())

    def keyPressEvent(self, e):
        if (e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter) and (e.modifiers() & Qt.ControlModifier):
            self.send_message()
            return
        super().keyPressEvent(e)

    def send_message(self):
        text = self.toPlainText().strip()
        if not text:
            return
        self.clear()
        self.message_sent.emit(text)


class TextBox(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setObjectName("TextBox")
        self.setReadOnly(True)
        self.refresh_theme()

    def refresh_theme(self):
        self.setStyleSheet(textbox_style())


class SearchBar(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setObjectName("SearchBar")
        self.setFixedHeight(48)
        self.setPlaceholderText("Search transcript...")
        self.setFont(QFont("Inter", 13))
        self.refresh_theme()

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QTextEdit#SearchBar {{
                background-color: {tokens.BG_INPUT};
                color: {tokens.TEXT_PRIMARY};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;
            }}
            QTextEdit#SearchBar:focus {{
                border: 2px solid {tokens.PRIMARY};
                background-color: {tokens.BG_INPUT};
            }}
            """
        )
