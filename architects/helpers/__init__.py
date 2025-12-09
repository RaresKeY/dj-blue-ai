"""Helper utilities exposed by the architects.helpers package."""

__all__ = []

# Optional dependency: google-generativeai
try:
    from .api_utils import LLMUtilitySuite
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    LLMUtilitySuite = None  # type: ignore
else:
    __all__.append("LLMUtilitySuite")

from .crypto_utils import (
    ensure_secret_key,
    get_secret_key,
    hmac_bytes,
    hmac_hex,
    hmac_sha256_bytes,
    hmac_sha256_hex,
    verify_hmac_bytes,
    verify_hmac_hex,
    verify_hmac_sha256_bytes,
    verify_hmac_sha256_hex,
)
__all__ += [
    "ensure_secret_key",
    "get_secret_key",
    "hmac_bytes",
    "hmac_hex",
    "hmac_sha256_bytes",
    "hmac_sha256_hex",
    "verify_hmac_bytes",
    "verify_hmac_hex",
    "verify_hmac_sha256_bytes",
    "verify_hmac_sha256_hex",
]

from .jsonrules_song import make_json_safe, restore_from_json
__all__ += ["make_json_safe", "restore_from_json"]

from .managed_mem import ManagedMem
__all__ += ["ManagedMem"]

# Optional dependency: PySide6
try:
    from .music_player import play_music
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    play_music = None  # type: ignore
else:
    __all__.append("play_music")

