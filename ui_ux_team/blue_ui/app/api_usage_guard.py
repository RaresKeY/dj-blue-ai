from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Mapping, Tuple

from ui_ux_team.blue_ui import settings as app_settings
from ui_ux_team.blue_ui.config import get_setting, set_setting

_STATE_MINUTE_BUCKET_KEY = "api_usage_state_minute_bucket"
_STATE_MINUTE_COUNT_KEY = "api_usage_state_minute_count"
_STATE_DAY_BUCKET_KEY = "api_usage_state_day_bucket"
_STATE_DAY_COUNT_KEY = "api_usage_state_day_count"
_STATE_MONTH_BUCKET_KEY = "api_usage_state_month_bucket"
_STATE_MONTH_SPEND_USD_KEY = "api_usage_state_month_spend_usd"

_DEFAULT_INPUT_PRICE_PER_1M = 0.35
_DEFAULT_OUTPUT_PRICE_PER_1M = 1.05

_MODEL_PRICES_USD_PER_1M: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-3-flash-preview": (0.35, 1.05),
}

_LOCK = threading.Lock()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _minute_bucket(now: datetime) -> str:
    return now.strftime("%Y-%m-%dT%H:%M")


def _day_bucket(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")


def _month_bucket(now: datetime) -> str:
    return now.strftime("%Y-%m")


def _as_int(raw: Any, default: int = 0) -> int:
    try:
        return int(raw)
    except Exception:
        return default


def _as_float(raw: Any, default: float = 0.0) -> float:
    try:
        return float(raw)
    except Exception:
        return default


def _model_prices(model_name: str) -> tuple[float, float]:
    normalized = str(model_name or "").strip().lower()
    if normalized.startswith("models/"):
        normalized = normalized.split("/", 1)[1]
    for key, prices in _MODEL_PRICES_USD_PER_1M.items():
        if key in normalized:
            return prices
    return (_DEFAULT_INPUT_PRICE_PER_1M, _DEFAULT_OUTPUT_PRICE_PER_1M)


def _normalized_state(now: datetime) -> dict[str, Any]:
    minute_key = _minute_bucket(now)
    day_key = _day_bucket(now)
    month_key = _month_bucket(now)

    state = {
        "minute_bucket": str(get_setting(_STATE_MINUTE_BUCKET_KEY, minute_key) or ""),
        "minute_count": _as_int(get_setting(_STATE_MINUTE_COUNT_KEY, 0), 0),
        "day_bucket": str(get_setting(_STATE_DAY_BUCKET_KEY, day_key) or ""),
        "day_count": _as_int(get_setting(_STATE_DAY_COUNT_KEY, 0), 0),
        "month_bucket": str(get_setting(_STATE_MONTH_BUCKET_KEY, month_key) or ""),
        "month_spend_usd": round(_as_float(get_setting(_STATE_MONTH_SPEND_USD_KEY, 0.0), 0.0), 6),
    }

    if state["minute_bucket"] != minute_key:
        state["minute_bucket"] = minute_key
        state["minute_count"] = 0
    if state["day_bucket"] != day_key:
        state["day_bucket"] = day_key
        state["day_count"] = 0
    if state["month_bucket"] != month_key:
        state["month_bucket"] = month_key
        state["month_spend_usd"] = 0.0
    return state


def _persist_state(state: Mapping[str, Any]) -> None:
    set_setting(_STATE_MINUTE_BUCKET_KEY, str(state["minute_bucket"]))
    set_setting(_STATE_MINUTE_COUNT_KEY, int(state["minute_count"]))
    set_setting(_STATE_DAY_BUCKET_KEY, str(state["day_bucket"]))
    set_setting(_STATE_DAY_COUNT_KEY, int(state["day_count"]))
    set_setting(_STATE_MONTH_BUCKET_KEY, str(state["month_bucket"]))
    set_setting(_STATE_MONTH_SPEND_USD_KEY, float(state["month_spend_usd"]))


def _extract_usage_counts(usage: Any) -> tuple[int, int]:
    if usage is None:
        return (0, 0)

    def _pick(names: list[str]) -> int:
        for name in names:
            raw = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
            if raw is None:
                continue
            try:
                return max(0, int(raw))
            except Exception:
                continue
        return 0

    input_tokens = _pick(["input_token_count", "prompt_token_count", "prompt_tokens"])
    output_tokens = _pick(["output_token_count", "candidates_token_count", "candidates_tokens"])

    if input_tokens == 0 and output_tokens == 0:
        total = _pick(["total_token_count", "total_tokens"])
        input_tokens = total
    return (input_tokens, output_tokens)


def _usage_cost_usd(*, usage: Any = None, model_name: str = "") -> float:
    input_tokens, output_tokens = _extract_usage_counts(usage)
    in_price, out_price = _model_prices(model_name)
    cost = (float(input_tokens) / 1_000_000.0) * in_price
    cost += (float(output_tokens) / 1_000_000.0) * out_price
    return max(0.0, cost)


def reserve_request(scope: str, model_name: str = "") -> Tuple[bool, str]:
    limits = app_settings.api_usage_limits()
    max_per_min = int(limits["requests_per_minute"])
    max_per_day = int(limits["requests_per_day"])
    budget_usd = float(limits["monthly_budget_usd"])
    now = _utc_now()

    with _LOCK:
        state = _normalized_state(now)
        if state["month_spend_usd"] >= budget_usd:
            return (
                False,
                f"API usage limit reached ({scope}): monthly budget ${budget_usd:.2f} exhausted.",
            )
        if state["minute_count"] >= max_per_min:
            return (
                False,
                f"API usage limit reached ({scope}): requests/minute cap ({max_per_min}) exceeded.",
            )
        if state["day_count"] >= max_per_day:
            return (
                False,
                f"API usage limit reached ({scope}): requests/day cap ({max_per_day}) exceeded.",
            )

        state["minute_count"] += 1
        state["day_count"] += 1
        _persist_state(state)
        return (True, "")


def record_usage(
    *,
    scope: str,
    model_name: str = "",
    usage: Any = None,
    fallback_cost_usd: float = 0.0,
) -> float:
    now = _utc_now()
    applied_cost = _usage_cost_usd(usage=usage, model_name=model_name)
    if applied_cost <= 0.0:
        applied_cost = max(0.0, float(fallback_cost_usd))

    with _LOCK:
        state = _normalized_state(now)
        state["month_spend_usd"] = round(max(0.0, float(state["month_spend_usd"])) + applied_cost, 6)
        _persist_state(state)
    return applied_cost


def current_usage_state() -> dict[str, float | int | str]:
    now = _utc_now()
    with _LOCK:
        state = _normalized_state(now)
    return {
        "minute_bucket": str(state["minute_bucket"]),
        "minute_count": int(state["minute_count"]),
        "day_bucket": str(state["day_bucket"]),
        "day_count": int(state["day_count"]),
        "month_bucket": str(state["month_bucket"]),
        "month_spend_usd": round(float(state["month_spend_usd"]), 6),
    }
