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

API_USAGE_REQUESTS_PER_MINUTE_KEY = "api_usage_requests_per_minute"
API_USAGE_REQUESTS_PER_DAY_KEY = "api_usage_requests_per_day"
API_USAGE_MONTHLY_BUDGET_USD_KEY = "api_usage_monthly_budget_usd"

API_USAGE_DEFAULT_REQUESTS_PER_MINUTE = 20
API_USAGE_DEFAULT_REQUESTS_PER_DAY = 1200
API_USAGE_DEFAULT_MONTHLY_BUDGET_USD = 5.0

API_USAGE_MIN_REQUESTS_PER_MINUTE = 1
API_USAGE_MAX_REQUESTS_PER_MINUTE = 500
API_USAGE_MIN_REQUESTS_PER_DAY = 10
API_USAGE_MAX_REQUESTS_PER_DAY = 200000
API_USAGE_MIN_MONTHLY_BUDGET_USD = 1.0
API_USAGE_MAX_MONTHLY_BUDGET_USD = 100000.0


def env_fallback_preference() -> str:
    raw = str(get_setting(ENV_FALLBACK_PREF_KEY, ENV_FALLBACK_UNSET)).strip().lower()
    if raw in {ENV_FALLBACK_ALLOW, ENV_FALLBACK_DENY}:
        return raw
    return ENV_FALLBACK_UNSET


def set_env_fallback_preference(allowed: bool) -> None:
    set_setting(ENV_FALLBACK_PREF_KEY, ENV_FALLBACK_ALLOW if allowed else ENV_FALLBACK_DENY)


def _clamp_int(raw: object, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(float(raw))
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _clamp_float(raw: object, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(raw)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def api_usage_defaults() -> dict[str, int | float]:
    return {
        "requests_per_minute": API_USAGE_DEFAULT_REQUESTS_PER_MINUTE,
        "requests_per_day": API_USAGE_DEFAULT_REQUESTS_PER_DAY,
        "monthly_budget_usd": API_USAGE_DEFAULT_MONTHLY_BUDGET_USD,
    }


def api_usage_limits() -> dict[str, int | float]:
    defaults = api_usage_defaults()
    rpm = _clamp_int(
        get_setting(API_USAGE_REQUESTS_PER_MINUTE_KEY, defaults["requests_per_minute"]),
        int(defaults["requests_per_minute"]),
        API_USAGE_MIN_REQUESTS_PER_MINUTE,
        API_USAGE_MAX_REQUESTS_PER_MINUTE,
    )
    rpd = _clamp_int(
        get_setting(API_USAGE_REQUESTS_PER_DAY_KEY, defaults["requests_per_day"]),
        int(defaults["requests_per_day"]),
        API_USAGE_MIN_REQUESTS_PER_DAY,
        API_USAGE_MAX_REQUESTS_PER_DAY,
    )
    monthly_budget_usd = _clamp_float(
        get_setting(API_USAGE_MONTHLY_BUDGET_USD_KEY, defaults["monthly_budget_usd"]),
        float(defaults["monthly_budget_usd"]),
        API_USAGE_MIN_MONTHLY_BUDGET_USD,
        API_USAGE_MAX_MONTHLY_BUDGET_USD,
    )
    return {
        "requests_per_minute": rpm,
        "requests_per_day": rpd,
        "monthly_budget_usd": round(monthly_budget_usd, 2),
    }


def set_api_usage_limits(
    *,
    requests_per_minute: object | None = None,
    requests_per_day: object | None = None,
    monthly_budget_usd: object | None = None,
) -> dict[str, int | float]:
    current = api_usage_limits()
    if requests_per_minute is not None:
        current["requests_per_minute"] = _clamp_int(
            requests_per_minute,
            int(current["requests_per_minute"]),
            API_USAGE_MIN_REQUESTS_PER_MINUTE,
            API_USAGE_MAX_REQUESTS_PER_MINUTE,
        )
    if requests_per_day is not None:
        current["requests_per_day"] = _clamp_int(
            requests_per_day,
            int(current["requests_per_day"]),
            API_USAGE_MIN_REQUESTS_PER_DAY,
            API_USAGE_MAX_REQUESTS_PER_DAY,
        )
    if monthly_budget_usd is not None:
        current["monthly_budget_usd"] = round(
            _clamp_float(
                monthly_budget_usd,
                float(current["monthly_budget_usd"]),
                API_USAGE_MIN_MONTHLY_BUDGET_USD,
                API_USAGE_MAX_MONTHLY_BUDGET_USD,
            ),
            2,
        )

    set_setting(API_USAGE_REQUESTS_PER_MINUTE_KEY, int(current["requests_per_minute"]))
    set_setting(API_USAGE_REQUESTS_PER_DAY_KEY, int(current["requests_per_day"]))
    set_setting(API_USAGE_MONTHLY_BUDGET_USD_KEY, float(current["monthly_budget_usd"]))
    return current


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
