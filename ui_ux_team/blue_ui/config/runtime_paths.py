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
    """Returns the directory containing the executable or script."""
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
    """Returns a writable directory for application configuration."""
    if getattr(sys, "frozen", False) or _is_appimage_runtime():
        if sys.platform.startswith("win"):
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / "dj-blue-ai"
            return Path.home() / "AppData" / "Roaming" / "dj-blue-ai"
        
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "dj-blue-ai"
            
        return _xdg_config_home() / "dj-blue-ai"

    # Development mode: config lives beside source in ./config
    return runtime_base_dir() / "config"


def legacy_repo_config_dir() -> Path:
    """Returns the legacy config directory within the repository."""
    return Path(__file__).resolve().parent


def ensure_user_config_dir() -> Path:
    """Ensures the user configuration directory exists."""
    cfg = user_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg


def default_music_folder() -> Path:
    """Returns the default directory for the music collection."""
    if getattr(sys, "frozen", False) or _is_appimage_runtime():
        if sys.platform.startswith("win"):
            # Use My Music or fallback to local app data
            return Path.home() / "Music" / "DJ Blue AI"
        
        if sys.platform == "darwin":
            return Path.home() / "Music" / "DJ Blue AI"

        return _xdg_data_home() / "dj-blue-ai" / "music_collection"

    # Development mode: use local music_collection folder
    return runtime_base_dir() / "music_collection"
