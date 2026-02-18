# API Usage Limits Rules (Blue UI)

## Overview
Blue UI stores API usage limits in app config and uses strict normalization to prevent invalid values from being persisted or loaded.

## Config Keys
- `api_usage_requests_per_minute`
- `api_usage_requests_per_day`
- `api_usage_monthly_budget_usd`

## Defaults
- Requests per minute: `20`
- Requests per day: `1200`
- Monthly budget (USD): `5.0`

Defaults are defined in:
- `ui_ux_team/blue_ui/settings.py`
- `ui_ux_team/blue_ui/config/settings_store.py`

## Bounds (Hard Clamps)
- Requests per minute: min `1`, max `500`
- Requests per day: min `10`, max `200000`
- Monthly budget (USD): min `1.0`, max `100000.0`

## Normalization Rules
1. Any read/write value is normalized through clamps.
2. Numeric coercion is applied (invalid input falls back to current/default).
3. Monthly budget is rounded to 2 decimals.
4. Persisted payload is rewritten normalized via settings store.

## UI Behavior
The settings tab (`API Usage Limits`) uses bounded spinboxes:
- `QSpinBox` for request limits.
- `QDoubleSpinBox` for monthly budget.
- “Reset to Defaults” sets all three fields to defaults above.

Form component:
- `ui_ux_team/blue_ui/widgets/api_usage_limits_form.py`

## Current Scope
These limits are runtime-enforced in core API paths:
- Transcript logic: `LLMUtilitySuite.transcribe_audio*` (used by `TranscriptionManager`)
- Chat logic: `GeminiChatbot.send_message` and cache-context setup in `GeminiChatbot.load_context`

Enforcement and accounting are implemented in:
- `ui_ux_team/blue_ui/app/api_usage_guard.py`

Runtime state (minute/day counters and month spend) is persisted in app settings:
- `api_usage_state_minute_bucket`
- `api_usage_state_minute_count`
- `api_usage_state_day_bucket`
- `api_usage_state_day_count`
- `api_usage_state_month_bucket`
- `api_usage_state_month_spend_usd`

## Monthly Budget Usage Calculation ($)
To avoid ambiguity, this is the calculation rule for dollar usage:

1. Track usage per request in USD:
- `request_cost_usd = input_cost_usd + output_cost_usd`
- `input_cost_usd = (input_tokens / 1_000_000) * model_input_price_per_1m`
- `output_cost_usd = (output_tokens / 1_000_000) * model_output_price_per_1m`

2. Track month-to-date spend:
- `spent_month_usd = sum(request_cost_usd for all requests in current calendar month)`

3. Compare against configured budget:
- `budget_limit_usd = api_usage_monthly_budget_usd`
- `budget_used_percent = (spent_month_usd / budget_limit_usd) * 100`
- Remaining budget:
  - `budget_remaining_usd = max(0, budget_limit_usd - spent_month_usd)`

4. Threshold decisions (recommended):
- Warn at `>= 80%`
- Soft block / confirmation at `>= 100%`

### Important Current-State Note
Monthly spend is now tracked in runtime paths for transcript/chat API calls.
Cost accounting uses token usage metadata when available; if metadata is absent in a path, fallback cost may be zero unless explicitly set by that caller.
