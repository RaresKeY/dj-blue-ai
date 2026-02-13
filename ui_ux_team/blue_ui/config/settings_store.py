"""JSON-backed settings store with legacy migration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .runtime_paths import ensure_user_config_dir, legacy_repo_config_dir, user_config_dir

THEME_FILE = "theme_config.json"
AUDIO_FILE = "audio_config.json"


def config_path(filename: str) -> Path:
    return user_config_dir() / filename


def _legacy_path(filename: str) -> Path:
    return legacy_repo_config_dir() / filename


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_json(path: Path, payload: dict[str, Any]) -> bool:
    try:
        ensure_user_config_dir()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception:
        return False


def load_with_legacy_migration(filename: str) -> dict[str, Any] | None:
    primary = config_path(filename)
    data = load_json(primary)
    if data is not None:
        return data

    legacy = _legacy_path(filename)
    legacy_data = load_json(legacy)
    if legacy_data is None:
        return None

    save_json(primary, legacy_data)
    return legacy_data
