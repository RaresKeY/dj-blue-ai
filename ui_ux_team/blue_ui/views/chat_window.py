import os
from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog

from architects.helpers.gemini_chatbot import GeminiChatbot
from architects.helpers.resource_path import resource_path
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.theme.native_window import apply_native_titlebar_for_theme
from ui_ux_team.blue_ui.widgets.image_button import ImageButton
from ui_ux_team.blue_ui.widgets.text_boxes import TextBoxAI, InputBlueBird
from ui_ux_team.blue_ui.widgets.loading import LoadingCircle


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
            self.init_finished.emit(bool(success), "Context loaded." if success else "Failed to load context.")
        except Exception as e:  # noqa: BLE001
            self.init_finished.emit(False, str(e))


class ContextUpdateWorker(QThread):
    update_finished = Signal(bool, str)

    def __init__(self, chatbot, file_path):
        super().__init__()
        self.chatbot = chatbot
        self.file_path = file_path

    def run(self):
        try:
            success = self.chatbot.update_context_with_file(self.file_path)
            self.update_finished.emit(bool(success), "Context loaded." if success else "Failed to load context.")
        except Exception as e:  # noqa: BLE001
            self.update_finished.emit(False, str(e))


class BlueBirdChatView(QWidget):
    closed = Signal()

    def __init__(self, api_key=None, initial_transcript=None):
        super().__init__()
        self.setWindowTitle("BlueBird AI")
        self.api_key = api_key
        self.chatbot = None
        self.initial_transcript = initial_transcript

        self.text_box = TextBoxAI()
        self.input_field = InputBlueBird()
        self.send_btn = ImageButton(resource_path("ui_ux_team/assets/send_black.png"), size=(63, 63))
        self.load_transcript = ImageButton(resource_path("ui_ux_team/assets/load_transcript.png"), size=(40, 40))
        self.load_transcript.setObjectName("LoadTranscriptButton")
        self.load_transcript.setStyleSheet("QLabel#LoadTranscriptButton { background: transparent; border: none; }")
        self.loader = LoadingCircle(self)

        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(self.input_field)
        row.addWidget(self.send_btn)
        layout.addWidget(self.text_box, 9)
        layout.addLayout(row, 1)

        self.send_btn.clicked.connect(self.input_field.send_message)
        self.input_field.message_sent.connect(self.handle_message)
        self.load_transcript.setParent(self)
        self.load_transcript.clicked.connect(self.open_file_picker)
        self.refresh_theme()

        if self.api_key:
            self.chatbot = GeminiChatbot(self.api_key)
            transcript = self.initial_transcript or "System: This is the start of the session."
            self.text_box.append_message("system", "*Initializing BlueBird AI context...*")
            self.set_input_enabled(False)
            self.loader.start()
            self.init_worker = ChatInitWorker(self.chatbot, transcript)
            self.init_worker.init_finished.connect(self.on_init_finished)
            self.init_worker.start()
        else:
            self.text_box.append_message("system", "**System:** API Key missing.")

    def refresh_theme(self):
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {tokens.COLOR_BG_MAIN};
                color: {tokens.TEXT_PRIMARY};
            }}
            QLabel#LoadTranscriptButton {{
                background: transparent;
                border: none;
            }}
            """
        )
        apply_native_titlebar_for_theme(self)
        self.text_box.refresh_theme()
        self.input_field.refresh_theme()

    def closeEvent(self, event):
        self.closed.emit()
        return super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.load_transcript.move(self.width() - self.load_transcript.width() - 22, 22)
        self.load_transcript.raise_()
        tb_geom = self.text_box.geometry()
        self.loader.move(tb_geom.x() + (tb_geom.width() - self.loader.width()) // 2, tb_geom.y() + (tb_geom.height() - self.loader.height()) // 2)
        self.loader.raise_()

    def set_input_enabled(self, enabled):
        self.input_field.setReadOnly(not enabled)
        self.send_btn.setEnabled(enabled)

    def on_init_finished(self, success, message):
        self.loader.stop()
        self.text_box.append_message("system", "*BlueBird AI Ready.*" if success else f"**Error initializing:** {message}")
        self.set_input_enabled(True)

    def on_context_updated(self, success, message):
        self.loader.stop()
        self.text_box.append_message("system", "*Context updated successfully.*" if success else f"**Error updating context:** {message}")

    def handle_message(self, text: str):
        self.text_box.append_message("user", text)
        if self.chatbot:
            self.loader.start()
            self.worker = ChatWorker(self.chatbot, text)
            self.worker.response_received.connect(self.handle_ai_response)
            self.worker.start()
        else:
            self.text_box.append_message("system", "**System:** API Key missing or Chatbot not initialized.")

    def handle_ai_response(self, response):
        self.loader.stop()
        if "error" in response:
            self.text_box.append_message("system", f"**Error:** {response['error']}")
        else:
            self.text_box.append_message("model", response.get("text", ""))

    def open_file_picker(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Transcript", "", "Text Files (*.txt);;All Files (*)")
        if not file_name:
            return
        if not self.chatbot:
            self.text_box.append_message("system", "**System:** Chatbot not initialized.")
            return
        self.text_box.append_message("system", f"*Loading context from: {os.path.basename(file_name)}...*")
        self.loader.start()
        self.reinit_worker = ContextUpdateWorker(self.chatbot, file_name)
        self.reinit_worker.update_finished.connect(self.on_context_updated)
        self.reinit_worker.start()
