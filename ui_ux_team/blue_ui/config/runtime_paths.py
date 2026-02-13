"""Runtime-safe paths for source and binary builds."""

from __future__ import annotations

import sys
from pathlib import Path


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
    # Kept for compatibility: config now lives beside binary/script in ./config.
    return runtime_base_dir() / "config"


def legacy_repo_config_dir() -> Path:
    return Path(__file__).resolve().parent


def ensure_user_config_dir() -> Path:
    cfg = user_config_dir()
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg


def default_music_folder() -> Path:
    return runtime_base_dir() / "music_collection"
