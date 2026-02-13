"""Theme runtime manager for Blue UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import tokens
from .palettes import DEFAULT_THEME_KEY, THEMES

_CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
_CONFIG_FILE = _CONFIG_DIR / "theme_config.json"

# Migrate old keys if they exist in persisted config.
_KEY_MIGRATION = {
    "vscode_dark": "dark_theme",
    "vscode_light": "light_theme",
}


def list_themes() -> dict[str, dict[str, Any]]:
    return THEMES


def current_theme_key() -> str:
    return tokens.CURRENT_THEME_KEY


def theme_label(theme_key: str) -> str:
    return THEMES.get(theme_key, {}).get("label", theme_key)


def set_theme(theme_key: str) -> str:
    if theme_key not in THEMES:
        raise KeyError(f"Unknown theme: {theme_key}")

    theme_tokens = THEMES[theme_key]["tokens"]
    for name, value in theme_tokens.items():
        setattr(tokens, name, value)

    tokens.CURRENT_THEME_KEY = theme_key
    _save_theme_key(theme_key)
    return theme_key


def ensure_default_theme() -> str:
    saved = _load_theme_key()
    if saved in THEMES:
        return set_theme(saved)

    current = _KEY_MIGRATION.get(tokens.CURRENT_THEME_KEY, tokens.CURRENT_THEME_KEY)
    if current in THEMES:
        return set_theme(current)

    return set_theme(DEFAULT_THEME_KEY)


def _load_theme_key() -> str | None:
    try:
        if not _CONFIG_FILE.exists():
            return None
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        key = str(data.get("selected_theme", "")).strip()
        return _KEY_MIGRATION.get(key, key) if key else None
    except Exception:
        return None


def _save_theme_key(theme_key: str) -> None:
    try:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"selected_theme": theme_key}
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        # Theme persistence should never crash UI runtime.
        pass
