# Data: Settings & Runtime Paths

## Scope
- Unified settings schema, normalization, and runtime path policy.
- Main implementation files:
- `ui_ux_team/blue_ui/config/settings_store.py`
- `ui_ux_team/blue_ui/config/runtime_paths.py`

## Primary Settings Schema
- `selected_theme: str`
- `music_folder: str`
- `api_env_fallback_preference: "" | "allow" | "deny"`
- `api_usage_requests_per_minute: int`
- `api_usage_requests_per_day: int`
- `api_usage_monthly_budget_usd: float`
- `chatbot_model: str`
- `transcription_model: str`
- `api_usage_state_minute_bucket: str`
- `api_usage_state_minute_count: int`
- `api_usage_state_day_bucket: str`
- `api_usage_state_day_count: int`
- `api_usage_state_month_bucket: str`
- `api_usage_state_month_spend_usd: float`

## Normalization Rules
- Theme and model values must be non-empty strings to override defaults.
- `music_folder` is expanded via `Path(...).expanduser()`.
- Fallback preference only accepts `allow` or `deny`; otherwise empty/default.
- Clamp ranges:
- RPM: `1..500`
- RPD: `10..200000`
- Monthly budget USD: `1.0..100000.0`
- Usage state counts are coerced to ints; month spend is rounded to 6 decimals.

## Storage & Migration
- Primary config file name: `app_config.json`.
- Unified settings can be bootstrapped from legacy split files:
- `theme_config.json`
- `audio_config.json`
- Frozen/runtime migration copies legacy `runtime_base_dir()/config/app_config.json` into current user config dir when needed.

## Runtime Path Policy
- Development mode:
- config in `runtime_base_dir()/config`
- default music in `runtime_base_dir()/music_collection`
- Frozen/AppImage mode:
- config in platform user config dir (`APPDATA`, macOS Application Support, or XDG config)
- default music in user music/data locations by platform

## Key Invariants
- `ensure_config_initialized()` always writes normalized unified config.
- Runtime path decisions are mode/platform dependent and handled centrally.
- Settings store is tolerant of malformed or missing JSON input by falling back to defaults.
