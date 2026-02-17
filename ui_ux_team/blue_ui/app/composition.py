import json
from pathlib import Path

from architects.helpers.gemini_chatbot import GeminiChatbot
from architects.helpers.managed_mem import ManagedMem
from architects.helpers.resource_path import resource_path
from architects.helpers.transcription_manager import TranscriptionManager
from ui_ux_team.blue_ui import settings as app_settings
from ui_ux_team.blue_ui.app.secure_api_key import (
    RUNTIME_SOURCE_DOTENV,
    RUNTIME_SOURCE_PROCESS_ENV,
    read_api_key as read_keyring_api_key,
    runtime_api_key,
    set_runtime_api_key,
)
from ui_ux_team.blue_ui.app.services import AppServices, default_player_factory
from ui_ux_team.blue_ui.config import ensure_config_initialized
from ui_ux_team.blue_ui.theme import ensure_default_theme
from ui_ux_team.blue_ui.views.main_window import MainWindowView


class AppComposer:
    def __init__(self, auto_bootstrap: bool = True):
        self.services = None
        self.window = None
        if auto_bootstrap:
            self.bootstrap()

    def bootstrap(self):
        self.prepare_config()
        self.prepare_theme()
        self.build_services()
        self.build_window()

    @staticmethod
    def prepare_config():
        ensure_config_initialized()

    @staticmethod
    def prepare_theme():
        ensure_default_theme()

    def build_services(self) -> AppServices:
        self.services = self._build_services()
        return self.services

    def build_window(self):
        self.window = MainWindowView()
        return self.window

    def _build_services(self) -> AppServices:
        api_key = runtime_api_key()
        if not api_key:
            api_key, _ = read_keyring_api_key()
        if not api_key:
            process_env_key = app_settings.read_process_api_key()
            if process_env_key:
                set_runtime_api_key(process_env_key, source=RUNTIME_SOURCE_PROCESS_ENV)
                api_key = process_env_key
        if not api_key:
            dotenv_key, _ = app_settings.read_dotenv_api_key_if_allowed()
            if dotenv_key:
                set_runtime_api_key(dotenv_key, source=RUNTIME_SOURCE_DOTENV)
                api_key = dotenv_key
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
        if self.window is None:
            self.build_window()
        self.window.show()
