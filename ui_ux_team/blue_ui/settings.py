from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

from ui_ux_team.blue_ui.app.secure_api_key import COMPAT_KEY, PRIMARY_KEY
from ui_ux_team.blue_ui.config import get_setting, set_setting
from ui_ux_team.blue_ui.config.runtime_paths import runtime_base_dir

ENV_FALLBACK_PREF_KEY = "api_env_fallback_preference"
ENV_FALLBACK_ALLOW = "allow"
ENV_FALLBACK_DENY = "deny"
ENV_FALLBACK_UNSET = ""


def env_fallback_preference() -> str:
    raw = str(get_setting(ENV_FALLBACK_PREF_KEY, ENV_FALLBACK_UNSET)).strip().lower()
    if raw in {ENV_FALLBACK_ALLOW, ENV_FALLBACK_DENY}:
        return raw
    return ENV_FALLBACK_UNSET


def set_env_fallback_preference(allowed: bool) -> None:
    set_setting(ENV_FALLBACK_PREF_KEY, ENV_FALLBACK_ALLOW if allowed else ENV_FALLBACK_DENY)


def dotenv_path() -> Path:
    return runtime_base_dir() / ".env"


def read_process_api_key() -> str:
    key = str(os.getenv(PRIMARY_KEY, "") or os.getenv(COMPAT_KEY, "")).strip()
    return key


def read_dotenv_api_key(path: Path | None = None) -> tuple[str | None, str | None]:
    env_file = Path(path) if path is not None else dotenv_path()
    if not env_file.exists():
        return None, f".env not found at {env_file}"

    try:
        values = dotenv_values(env_file)
    except Exception as exc:
        return None, f"Could not read .env: {exc}"

    key = str(values.get(PRIMARY_KEY, "") or values.get(COMPAT_KEY, "")).strip()
    if key:
        return key, None
    return None, f".env does not contain {PRIMARY_KEY}"


def read_dotenv_api_key_if_allowed() -> tuple[str | None, str | None]:
    if env_fallback_preference() != ENV_FALLBACK_ALLOW:
        return None, "dotenv fallback is disabled"
    return read_dotenv_api_key()
