import sys
import markdown
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QTextEdit
)
from PySide6.QtGui import (
    QPalette, QColor, QFont
)
from PySide6.QtCore import (
    Qt, Signal, QThread
)

from pathlib import Path
# Ensure project root is importable when running the script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from architects.helpers.gemini_chatbot import GeminiChatbot
from .visual_components import ImageButton

class TextBoxAI(QTextBrowser):
    def __init__(self):
        super().__init__()

        self.setObjectName("TextBox") 
        # self.setReadOnly(True) # QTextBrowser is read-only by default
        self.setOpenExternalLinks(True)

        # padding + border
        self.setStyleSheet("""
            QTextBrowser#TextBox {
                background-color: #0F0F0F;
                color: #B8B8B8;

                border: 1px solid #2A2D31;
                border-radius: 10px;
                padding: 15px;

                font-size: 15px;
                font-weight: 400;
                font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;
                line-height: 1.4;

                selection-background-color: #3E6AFF;
            }
        """)

    def append_message(self, role: str, text: str):
        """Formats and appends a message with markdown support and role-based styling."""
        html_content = markdown.markdown(text)
        
        if role == "user":
            sender = "You"
            color = "#5EA2FF"  # Soft Blue
        elif role == "model":
            sender = "BlueBird"
            color = "#2ECC71"  # Soft Green
        else:
            sender = "System"
            color = "#95A5A6"  # Gray

        # Construct HTML block
        # Note: QT's HTML subset is limited. Simple inline styles work best.
        html_block = f"""
        <div style="margin-top: 10px; margin-bottom: 5px;">
            <span style="color: {color}; font-weight: bold; font-size: 16px;">{sender}</span>
        </div>
        <div style="color: #E0E0E0; margin-bottom: 10px;">
            {html_content}
        </div>
        <hr style="background-color: #2A2D31; height: 1px; border: none; margin: 10px 0;">
        """
        
        self.append("") # Ensure separation from previous block
        self.insertHtml(html_block)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class InputBlueBird(QTextEdit):
    message_sent = Signal(str)

    def __init__(self, text_box):
        super().__init__()

        self.style_settings()
        self.text_box: TextBoxAI = text_box

    def keyPressEvent(self, e):
        # Send on Ctrl+Space
        if e.key() == Qt.Key_Space and (e.modifiers() & Qt.ControlModifier):
            self.send_message()
            return
        # Allow default behavior (newline on Enter)
        super().keyPressEvent(e)

    def send_message(self):
        text = self.toPlainText().strip()
        if not text:
            return

        self.clear()
        self.message_sent.emit(text)

    def style_settings(self):
        self.setObjectName("InputChat")

        font = QFont()
        font.setPointSize(13)
        self.setFont(font)

        self.setFixedHeight(70)
        self.setPlaceholderText("Type a message to BlueBird AI (Ctrl+Space to send)")

        # padding + border
        self.setStyleSheet("""
            QTextEdit#InputChat {
                background-color: #161616;
                color: #E6E6E6;

                border: 1px solid #2A2D31;
                border-radius: 10px;
                padding: 10px;

                font-size: 15px;
                font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif;

                selection-background-color: #3E6AFF;
            }
        """)


class ChatWorker(QThread):
    response_received = Signal(dict)

    def __init__(self, chatbot, message):
        super().__init__()
        self.chatbot = chatbot
        self.message = message

    def run(self):
        if self.chatbot:
            response = self.chatbot.send_message(self.message)
            self.response_received.emit(response)
        else:
             self.response_received.emit({"error": "Chatbot not initialized"})


class ChatInitWorker(QThread):
    init_finished = Signal(bool, str)

    def __init__(self, chatbot, transcript):
        super().__init__()
        self.chatbot = chatbot
        self.transcript = transcript

    def run(self):
        try:
            success = self.chatbot.load_context(self.transcript)
            if success:
                self.init_finished.emit(True, "Context loaded.")
            else:
                self.init_finished.emit(False, "Failed to load context.")
        except Exception as e:
            self.init_finished.emit(False, str(e))


class BlueBirdChat(QWidget):
    closed = Signal()

    def __init__(self, api_key=None, initial_transcript=None):
        super().__init__()
        self.setWindowTitle("BlueBird AI")
        self.api_key = api_key
        self.chatbot = None
        self.initial_transcript = initial_transcript
        
        self.text_box = None
        self.input_field = None
        self.send_btn = None
        self.root_layout = self.build_layout()

        if self.api_key:
             self.chatbot = GeminiChatbot(self.api_key)
             
             transcript_to_load = self.initial_transcript if self.initial_transcript else "System: This is the start of the session."
             
             self.text_box.append_message("system", "*Initializing BlueBird AI context...*")
             self.set_input_enabled(False)

             self.init_worker = ChatInitWorker(self.chatbot, transcript_to_load)
             self.init_worker.init_finished.connect(self.on_init_finished)
             self.init_worker.start()
        else:
             self.text_box.append_message("system", "**System:** API Key missing.")

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)

    def set_input_enabled(self, enabled):
        if self.input_field:
            self.input_field.setReadOnly(not enabled)
        if self.send_btn:
            self.send_btn.setEnabled(enabled)

    def on_init_finished(self, success, message):
        if success:
            self.text_box.append_message("system", "*BlueBird AI Ready.*")
            self.set_input_enabled(True)
        else:
            self.text_box.append_message("system", f"**Error initializing:** {message}")

    def handle_message(self, text: str):
        """Receive text from input widget and append to the chat box."""
        # Display user message
        self.text_box.append_message("user", text)
        
        # Send to AI
        if self.chatbot:
             self.worker = ChatWorker(self.chatbot, text)
             self.worker.response_received.connect(self.handle_ai_response)
             self.worker.start()
        else:
             self.text_box.append_message("system", "**System:** API Key missing or Chatbot not initialized.")

    def handle_ai_response(self, response):
        if "error" in response:
             self.text_box.append_message("system", f"**Error:** {response['error']}")
        else:
             self.text_box.append_message("model", response['text'])

    def build_layout(self):
        layout = QVBoxLayout(self)

        self.text_box = TextBoxAI()

        user_input_layout = QHBoxLayout()

        self.input_field = InputBlueBird(self.text_box)
        self.input_field.message_sent.connect(self.handle_message)

        # Use ImageButton directly
        self.send_btn = ImageButton("assets/send_black.png", size=(63, 63))
        self.send_btn.clicked.connect(self.input_field.send_message)

        user_input_layout.addWidget(self.input_field)
        user_input_layout.addWidget(self.send_btn)

        layout.addWidget(self.text_box, 9)
        layout.addLayout(user_input_layout, 1)
