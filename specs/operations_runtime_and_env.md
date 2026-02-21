# Operations: Runtime & Environment

## Scope
- Day-to-day runtime entrypoints, environment assumptions, and key material handling.
- Main implementation/docs:
- `main.py`
- `ui_ux_team/blue_ui/app/main.py`
- `ui_ux_team/blue_ui/app/composition.py`
- `ui_ux_team/blue_ui/app/secure_api_key.py`
- `README.md`

## Runtime Entry Options
- Compatibility entrypoint: `python main.py` delegates to Blue UI runtime `run()`.
- Direct entrypoint: `python ui_ux_team/blue_ui/app/main.py`.
- Recommended development interpreter target is project Python 3.12 environment.

## Startup Composition Sequence
- Initialize config (`ensure_config_initialized()`).
- Apply persisted/default theme (`ensure_default_theme()`).
- Compose services and main window through `AppComposer`.
- Show main window and enter Qt event loop.

## API Key Resolution Order
- Runtime in-memory key (`runtime_api_key()`).
- Keyring lookup for `SERVICE_ID = dj-blue-ai`, key names `AI_STUDIO_API_KEY` then `AI_STUDIO`.
- Process environment (`app_settings.read_process_api_key()`).
- Optional dotenv fallback only when allowed by settings (`read_dotenv_api_key_if_allowed()`).

## Runtime Persistence Behavior
- Config and music default paths are runtime-mode aware via `runtime_paths`.
- Development mode uses repo-adjacent config/music locations.
- Frozen/AppImage mode uses user config/data directories by platform.
- Keyring is the primary persisted secret store; runtime key state is mirrored in process globals.

## Operational Utility Scripts
- `scripts/debug_models.py` inspects available model metadata/methods through `GenAIClient`.
- `scripts/generate_app_icons.py` regenerates platform app icon assets from source image.

## Key Invariants
- Active runtime behavior is defined by Blue UI startup/composition modules.
- API-key-dependent features remain unavailable when no key resolves.
- Secret persistence is keyring-centric with explicit fallback behavior controls.
