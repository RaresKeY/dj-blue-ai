from __future__ import annotations

import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui_ux_team.blue_ui import settings as app_settings
from ui_ux_team.blue_ui.app.secure_api_key import runtime_api_key, read_api_key
from ui_ux_team.blue_ui.theme import tokens
from ui_ux_team.blue_ui.widgets.settings_section import SettingsSection
from architects.helpers.genai_client import GenAIClient


CHAT_MODELS = {
    "Gemma 3 27B": "models/gemma-3-27b-it",
    "Gemini 2.5 Flash": "models/gemini-2.5-flash",
    "Gemini 2.5 Pro": "models/gemini-2.5-pro",
    "Gemini 3 Pro": "models/gemini-3-pro-preview",
}

TRANSCRIPT_MODELS = {
    "Gemini 2.5 Flash Lite": "models/gemini-2.5-flash-lite",
    "Gemini 2.5 Flash": "models/gemini-2.5-flash",
    "Gemini 2 Flash": "models/gemini-2.0-flash",
}


class ModelSettingsForm(QWidget):
    model_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modelSettingsForm")

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(8)

        title = QLabel("Model Selection")
        title.setObjectName("modelSettingsTitle")
        subtitle = QLabel(
            "Choose which Gemini models to use for chat and transcription. "
            "Higher-tier models may provide better accuracy but consume more quota."
        )
        subtitle.setObjectName("modelSettingsSubtitle")
        subtitle.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(subtitle)

        self._chatbot_section = SettingsSection(
            "Chatbot Model",
            "Select the default model for BlueBird AI chat sessions.",
        )
        chatbot_form = QFormLayout()
        self._chatbot_combo = QComboBox()
        # Add curated chat models
        for label, model_id in CHAT_MODELS.items():
            self._chatbot_combo.addItem(label, model_id)
        chatbot_form.addRow("Default Model", self._chatbot_combo)
        self._chatbot_section.content_layout().addLayout(chatbot_form)

        self._transcription_section = SettingsSection(
            "Transcription Model",
            "Select the model used for audio transcription and analysis.",
        )
        transcription_form = QFormLayout()
        self._transcription_combo = QComboBox()
        # Add curated transcript models
        for label, model_id in TRANSCRIPT_MODELS.items():
            self._transcription_combo.addItem(label, model_id)
        transcription_form.addRow("Default Model", self._transcription_combo)
        self._transcription_section.content_layout().addLayout(transcription_form)

        root.addWidget(self._chatbot_section)
        root.addWidget(self._transcription_section)

        actions = QHBoxLayout()
        self._refresh_btn = QPushButton("Discover All Models")
        self._refresh_btn.setToolTip("Fetch full list of supported models from AI Studio")
        self._refresh_btn.clicked.connect(self._fetch_models)
        actions.addWidget(self._refresh_btn)
        actions.addStretch(1)
        root.addLayout(actions)

        self._status = QLabel("")
        self._status.setObjectName("modelSettingsStatus")
        root.addWidget(self._status)

        self._chatbot_combo.currentIndexChanged.connect(self._on_chatbot_changed)
        self._transcription_combo.currentIndexChanged.connect(self._on_transcription_changed)

        self._load_current_selection()
        self.refresh_theme()

    def _load_current_selection(self):
        cb_model = app_settings.chatbot_model()
        tr_model = app_settings.transcription_model()
        
        self._chatbot_combo.blockSignals(True)
        self._transcription_combo.blockSignals(True)
        
        # Try to find current ID in user data
        idx_cb = self._chatbot_combo.findData(cb_model)
        if idx_cb != -1:
            self._chatbot_combo.setCurrentIndex(idx_cb)
        else:
            # Add custom if not in curated list
            self._chatbot_combo.addItem(cb_model, cb_model)
            self._chatbot_combo.setCurrentText(cb_model)
            
        idx_tr = self._transcription_combo.findData(tr_model)
        if idx_tr != -1:
            self._transcription_combo.setCurrentIndex(idx_tr)
        else:
            # Add custom if not in curated list
            self._transcription_combo.addItem(tr_model, tr_model)
            self._transcription_combo.setCurrentText(tr_model)
        
        self._chatbot_combo.blockSignals(False)
        self._transcription_combo.blockSignals(False)

    def _on_chatbot_changed(self, index: int):
        model_id = self._chatbot_combo.itemData(index)
        if model_id:
            app_settings.set_chatbot_model(model_id)
            self._status.setText(f"Chatbot model set to: {model_id}")
            self.model_changed.emit()

    def _on_transcription_changed(self, index: int):
        model_id = self._transcription_combo.itemData(index)
        if model_id:
            app_settings.set_transcription_model(model_id)
            self._status.setText(f"Transcription model set to: {model_id}")
            self.model_changed.emit()

    def _fetch_models(self):
        api_key = runtime_api_key()
        if not api_key:
            api_key, _ = read_api_key()
        
        if not api_key:
            self._status.setText("API Key missing. Cannot refresh models.")
            return

        self._status.setText("Fetching latest models...")
        try:
            client = GenAIClient(api_key=api_key)
            models = client.list_models()
            
            # Filter for text generation models
            valid_names = []
            for m in models:
                if "generateContent" in getattr(m, "supported_generation_methods", []):
                    valid_names.append(m.name)
            
            valid_names.sort()
            
            current_cb = self._chatbot_combo.currentText()
            current_tr = self._transcription_combo.currentText()
            
            self._chatbot_combo.blockSignals(True)
            self._transcription_combo.blockSignals(True)
            
            self._chatbot_combo.clear()
            self._transcription_combo.clear()
            
            self._chatbot_combo.addItems(valid_names)
            self._transcription_combo.addItems(valid_names)
            
            self._chatbot_combo.setCurrentText(current_cb)
            self._transcription_combo.setCurrentText(current_tr)
            
            self._chatbot_combo.blockSignals(False)
            self._transcription_combo.blockSignals(False)
            
            self._status.setText(f"Loaded {len(valid_names)} models from AI Studio.")
        except Exception as e:
            self._status.setText(f"Error fetching models: {e}")

    def refresh_theme(self):
        accent = getattr(tokens, "ACCENT", "#FF9B54")
        self.setStyleSheet(
            f"""
            QWidget#modelSettingsForm {{ background: transparent; }}
            QLabel#modelSettingsTitle {{ font-size: 18px; font-weight: 700; color: {tokens.TEXT_PRIMARY}; }}
            QLabel#modelSettingsSubtitle {{ font-size: 12px; color: {tokens.TEXT_MUTED}; }}
            QLabel {{ color: {tokens.TEXT_PRIMARY}; }}
            QComboBox {{
                background: {tokens.BG_INPUT};
                color: {tokens.TEXT_PRIMARY};
                border: 1px solid {tokens.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 4px 10px;
            }}
            QPushButton {{
                background: rgba(255, 155, 84, 0.14);
                color: {accent};
                border: 1px solid rgba(255, 155, 84, 0.62);
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            QLabel#modelSettingsStatus {{ font-size: 12px; color: {accent}; padding-top: 4px; }}
            """
        )
        self._chatbot_section.refresh_theme()
        self._transcription_section.refresh_theme()
