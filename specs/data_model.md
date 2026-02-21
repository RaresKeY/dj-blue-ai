# Data Model

## Persisted Settings Contract
Primary schema is normalized in `ui_ux_team.blue_ui.config.settings_store`.

Key fields:
- `selected_theme: str`
- `music_folder: str`
- `api_env_fallback_preference: "" | "allow" | "deny"`
- `api_usage_requests_per_minute: int` (clamped)
- `api_usage_requests_per_day: int` (clamped)
- `api_usage_monthly_budget_usd: float` (clamped)
- `chatbot_model: str`
- `transcription_model: str`
- usage bucket/count/spend state fields for minute/day/month accounting

## Settings Storage And Migration
- Runtime settings path is resolved dynamically by the runtime-path layer.
- Unified settings are migrated from older split-key layouts when needed.
- Settings values are normalized and clamped before persistence.

## Managed Memory Contract
- Implemented by singleton `ManagedMem` in `architects/helpers/managed_mem.py`.
- Default storage path is user-config scoped, with migration from older runtime-base locations.
- Supports:
- key/value storage (`settr`, `gettr`)
- capped log list (`_log_cap = 500`)
- synchronous or async disk flushing
- JSON-safe serialization via `jsonrules_song`
- Typical entries include log events and transcript session payloads with `text`, `summary`, `segments`, `emotion`, and optional `translation`.

## Legacy Song Object Contract
- `architects/song.py` defines `Song` persistence keyed by normalized filepath.
- Required metadata fields exist (`mood_tags`, `camelot_tags`, `tempo`) and enrichment methods remain placeholders in current implementation.

## Transcript Output Contract
- Session transcript output uses chunk-window blocks:
- header line `[HH:MM:SS - HH:MM:SS]`
- free-form transcript text
- blank separator between blocks
- Legacy/prototype transcript corpora and scraper outputs exist as historical artifacts; Blue UI runtime behavior is authoritative.

## Mood/Metadata Artifact Contract
- Mood datasets include playlist mappings, mood-tag vocab fixtures, prompt fixtures, and analyzed metadata tables used by mood tooling workflows.
- Some of these artifacts are legacy or local-workflow oriented; runtime reads should be validated against active import paths.

## Prototype Model Asset Notes
- Legacy prototype-local ASR model bundle was removed from `prototype_r`.
- Prototype sherpa-onnx scripts now require externally configured model paths through environment variables.
- `ui_ux_team/prototype_r/` remains legacy; runtime-authoritative data contracts live under Blue UI modules.

## Legacy Transcriber Output Contract
- Legacy standalone transcriber docs specify JSON payload with:
- `version`, `timestamp`, `source_file`, `duration_sec`, `language`, `text`, `segments[]`, `metadata`.

## Secret Storage Contract
- API key canonical identifiers:
- service: `dj-blue-ai`
- key names: `AI_STUDIO_API_KEY`, `AI_STUDIO`
- Stored via OS keychain (`keyring`) and held in runtime memory; optional local env-file fallback may be enabled by preference.
- Runtime-only secret state is managed in `ui_ux_team/blue_ui/app/secure_api_key.py`.

## Service Composition Contract
- `ui_ux_team/blue_ui/app/services.py` defines `AppServices`:
- `transcription`, `player_factory`, `memory`, `chat_factory`, `mood_repository`
- Default player factory currently binds `MiniaudioPlayer`.
