import json
import os
from pathlib import Path

from architects.helpers.gemini_chatbot import GeminiChatbot
from architects.helpers.managed_mem import ManagedMem
from architects.helpers.resource_path import resource_path
from architects.helpers.transcription_manager import TranscriptionManager
from ui_ux_team.blue_ui.app.services import AppServices, default_player_factory
from ui_ux_team.blue_ui.views.main_window import MainWindowView


class AppComposer:
    def __init__(self):
        self.services = self._build_services()
        self.window = MainWindowView()

    def _build_services(self) -> AppServices:
        api_key = os.getenv("AI_STUDIO_API_KEY")
        transcription = TranscriptionManager(api_key, chunk_seconds=30) if api_key else None

        mood_data_path = Path(resource_path("mood_readers/data/mood_playlists_organized.json"))
        if mood_data_path.exists():
            with open(mood_data_path, "r", encoding="utf-8") as f:
                mood_repository = json.load(f)
        else:
            mood_repository = {}

        return AppServices(
            transcription=transcription,
            player_factory=default_player_factory,
            memory=ManagedMem(),
            chat_factory=GeminiChatbot,
            mood_repository=mood_repository,
        )

    def show(self):
        self.window.show()
