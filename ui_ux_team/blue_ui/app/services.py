from dataclasses import dataclass
from typing import Any, Optional

from architects.helpers.managed_mem import ManagedMem
from architects.helpers.miniaudio_player import MiniaudioPlayer
from architects.helpers.transcription_manager import TranscriptionManager


@dataclass
class AppServices:
    transcription: Optional[TranscriptionManager]
    player_factory: Any
    memory: ManagedMem
    chat_factory: Any
    mood_repository: dict


def default_player_factory(path: str) -> MiniaudioPlayer:
    return MiniaudioPlayer(path)
