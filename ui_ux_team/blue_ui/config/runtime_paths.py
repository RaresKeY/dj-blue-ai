"""Runtime-safe config paths for source and binary builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def user_config_dir() -> Path:
    app_name = "dj-blue-ai"
    subdir = "blue_ui"
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / app_name / subdir
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name / subdir
    return Path.home() / ".config" / app_name / subdir


def legacy_repo_config_dir() -> Path:
    return Path(__file__).resolve().parent


def ensure_user_config_dir() -> Path:
    cfg = user_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg


def default_music_folder() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "mood_music_collection"
    return Path(__file__).resolve().parents[3] / "mood_music_collection"
