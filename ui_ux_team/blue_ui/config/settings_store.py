"""Unified JSON settings store with legacy migration."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .runtime_paths import (
    default_music_folder,
    ensure_user_config_dir,
    legacy_repo_config_dir,
    runtime_base_dir,
    user_config_dir,
)

CONFIG_FILE = "app_config.json"
_LEGACY_THEME = "theme_config.json"
_LEGACY_AUDIO = "audio_config.json"


def config_path() -> Path:
    """Returns the path to the unified configuration file."""
    return user_config_dir() / CONFIG_FILE


def _legacy_paths(filename: str) -> list[Path]:
    """Returns a list of potential legacy paths for a configuration file."""
    return [
        user_config_dir() / filename,
        legacy_repo_config_dir() / filename,
    ]


def load_json(path: Path) -> dict[str, Any] | None:
    """Loads a JSON file and returns its content as a dictionary."""
    try:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_json(path: Path, payload: dict[str, Any]) -> bool:
    """Saves a dictionary as a JSON file."""
    try:
        ensure_user_config_dir()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception:
        return False


def default_config() -> dict[str, Any]:
    """Returns the default application configuration."""
    return {
        "selected_theme": "dark_theme",
        "music_folder": str(default_music_folder()),
        "api_env_fallback_preference": "",
        "api_usage_requests_per_minute": 20,
        "api_usage_requests_per_day": 1200,
        "api_usage_monthly_budget_usd": 5.0,
        "chatbot_model": "models/gemini-2.5-pro",
        "transcription_model": "models/gemini-2.5-flash-lite",
        # Persistent usage state metrics
        "api_usage_state_minute_bucket": "",
        "api_usage_state_minute_count": 0,
        "api_usage_state_day_bucket": "",
        "api_usage_state_day_count": 0,
        "api_usage_state_month_bucket": "",
        "api_usage_state_month_spend_usd": 0.0,
    }


def _normalized_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Normalizes and validates a raw configuration dictionary."""
    base = default_config()
    if not isinstance(raw, dict):
        return base

    out = dict(base)
    theme = raw.get("selected_theme")
    if isinstance(theme, str) and theme.strip():
        out["selected_theme"] = theme.strip()

    folder = raw.get("music_folder")
    if isinstance(folder, str) and folder.strip():
        out["music_folder"] = str(Path(folder).expanduser())

    pref = str(raw.get("api_env_fallback_preference", "")).strip().lower()
    if pref in {"allow", "deny"}:
        out["api_env_fallback_preference"] = pref

    # Limits normalization
    rpm = raw.get("api_usage_requests_per_minute")
    if isinstance(rpm, (int, float)):
        out["api_usage_requests_per_minute"] = max(1, min(int(rpm), 500))

    rpd = raw.get("api_usage_requests_per_day")
    if isinstance(rpd, (int, float)):
        out["api_usage_requests_per_day"] = max(10, min(int(rpd), 200000))

    monthly_budget = raw.get("api_usage_monthly_budget_usd")
    if isinstance(monthly_budget, (int, float)):
        out["api_usage_monthly_budget_usd"] = max(1.0, min(float(monthly_budget), 100000.0))

    for key in ["chatbot_model", "transcription_model"]:
        val = raw.get(key)
        if isinstance(val, str) and val.strip():
            out[key] = val.strip()

    # State metrics normalization
    for key in [
        "api_usage_state_minute_bucket",
        "api_usage_state_day_bucket",
        "api_usage_state_month_bucket",
    ]:
        val = raw.get(key)
        if isinstance(val, str):
            out[key] = val

    for key in ["api_usage_state_minute_count", "api_usage_state_day_count"]:
        val = raw.get(key)
        if isinstance(val, (int, float)):
            out[key] = int(val)

    spend = raw.get("api_usage_state_month_spend_usd")
    if isinstance(spend, (int, float)):
        out["api_usage_state_month_spend_usd"] = round(float(spend), 6)

    return out


def _load_legacy_split_config() -> dict[str, Any]:
    """Attempts to load and merge legacy split configuration files."""
    merged: dict[str, Any] = {}
    for p in _legacy_paths(_LEGACY_THEME):
        data = load_json(p)
        if isinstance(data, dict) and isinstance(data.get("selected_theme"), str):
            merged["selected_theme"] = data["selected_theme"]
            break

    for p in _legacy_paths(_LEGACY_AUDIO):
        data = load_json(p)
        if isinstance(data, dict) and isinstance(data.get("music_folder"), str):
            merged["music_folder"] = data["music_folder"]
            break
    return merged


def _migrate_frozen_config_if_needed() -> None:
    """Moves configuration from root/config to platform-specific directory if needed."""
    new_dir = user_config_dir()
    new_path = new_dir / CONFIG_FILE

    if new_path.exists():
        return

    # Old location was always runtime_base_dir() / "config"
    old_path = runtime_base_dir() / "config" / CONFIG_FILE

    if old_path.exists() and old_path.resolve() != new_path.resolve():
        try:
            ensure_user_config_dir()
            shutil.copy2(old_path, new_path)
        except Exception:
            pass


def ensure_config_initialized() -> dict[str, Any]:
    """Ensures the configuration is initialized and migrated if necessary."""
    _migrate_frozen_config_if_needed()
    path = config_path()
    current = load_json(path)
    if current is None:
        current = _load_legacy_split_config()

    cfg = _normalized_config(current)
    save_json(path, cfg)
    return cfg


def get_setting(key: str, default: Any = None) -> Any:
    """Retrieves a specific setting from the configuration."""
    cfg = ensure_config_initialized()
    return cfg.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Updates a specific setting in the configuration."""
    cfg = ensure_config_initialized()
    cfg[key] = value
    cfg = _normalized_config(cfg)
    return save_json(config_path(), cfg)
