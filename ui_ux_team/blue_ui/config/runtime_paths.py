"""Runtime-safe paths for source and binary builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_appimage_runtime() -> bool:
    # AppImage executes from a read-only mount (APPIMAGE/APPDIR are usually set).
    return bool(os.environ.get("APPIMAGE") or os.environ.get("APPDIR"))


def _xdg_config_home() -> Path:
    raw = os.environ.get("XDG_CONFIG_HOME", "").strip()
    return Path(raw).expanduser() if raw else (Path.home() / ".config")


def _xdg_data_home() -> Path:
    raw = os.environ.get("XDG_DATA_HOME", "").strip()
    return Path(raw).expanduser() if raw else (Path.home() / ".local" / "share")


def runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    argv0 = Path(sys.argv[0]).expanduser() if sys.argv and sys.argv[0] else None
    if argv0:
        try:
            return argv0.resolve().parent
        except Exception:
            pass
    return Path.cwd()


def user_config_dir() -> Path:
    if _is_appimage_runtime():
        return _xdg_config_home() / "dj-blue-ai"
    # Kept for compatibility: config otherwise lives beside binary/script in ./config.
    return runtime_base_dir() / "config"


def legacy_repo_config_dir() -> Path:
    return Path(__file__).resolve().parent


def ensure_user_config_dir() -> Path:
    cfg = user_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg


def default_music_folder() -> Path:
    if _is_appimage_runtime():
        return _xdg_data_home() / "dj-blue-ai" / "music_collection"
    return runtime_base_dir() / "music_collection"
