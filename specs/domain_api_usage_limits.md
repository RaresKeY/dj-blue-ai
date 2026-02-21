# Domain: API Usage Limits

## Scope
- Request-rate and budget guardrail behavior.
- Main implementation files:
- `ui_ux_team/blue_ui/app/api_usage_guard.py`
- `ui_ux_team/blue_ui/config/settings_store.py`

## Limit Dimensions
- Requests per minute (`api_usage_requests_per_minute`)
- Requests per day (`api_usage_requests_per_day`)
- Monthly budget USD (`api_usage_monthly_budget_usd`)

All limits are read from normalized settings via `app_settings.api_usage_limits()`.

## State Model
- Minute bucket key: `%Y-%m-%dT%H:%M`
- Day bucket key: `%Y-%m-%d`
- Month bucket key: `%Y-%m`
- Persisted counters:
- minute count
- day count
- month spend USD

Bucket changes reset the corresponding counter/spend in normalized state.

## Reserve Request Contract
- `reserve_request(scope, model_name)` performs:
- budget check first
- minute cap check second
- day cap check third
- On success, minute/day counts are incremented and persisted.
- On block, returns `(False, reason)` and does not mutate counters.

## Usage Cost Contract
- `record_usage(...)` computes token cost from response usage fields and model pricing table.
- If usage metadata is unavailable or zero, `fallback_cost_usd` can be applied.
- Cost is accumulated into monthly spend and rounded to 6 decimals.

## Model Price Resolution
- Model pricing lookup is substring-based after normalization.
- Known map includes:
- `gemini-2.5-flash-lite`
- `gemini-2.5-flash`
- `gemini-3-flash-preview`
- Unknown models use default input/output price constants.

## Concurrency & Persistence
- Guard operations are synchronized with a module-level thread lock.
- State persistence uses `set_setting(...)` keys in settings storage.
- `current_usage_state()` returns normalized live counters for UI display.

## Key Invariants
- Limit checks happen before request execution in chat/transcription flows.
- Guard state survives restarts via settings persistence.
- Bucket rollover behavior is deterministic and UTC-based.
