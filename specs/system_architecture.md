# System Architecture

## Entrypoints
- Root `main.py` is a compatibility launcher that imports and runs `ui_ux_team.blue_ui.app.main:run`.
- Primary runtime bootstrap is `ui_ux_team/blue_ui/app/main.py`.
- Separate non-Blue-UI tools exist but are not wired into main runtime:
- `transcribers/the_transcribers.py`
- `the_listeners/dj_the_listeners.py`

## Startup Pipeline (`ui_ux_team/blue_ui/app/main.py`)
- Reads selected theme from runtime settings storage under runtime base dir.
- Builds a lightweight Tk bootstrap loader (fallback null loader if Tk unavailable).
- Initializes config via `ensure_config_initialized()`.
- Imports/creates Qt app and applies runtime app icon.
- Applies persisted/default theme via `ensure_default_theme()`.
- Composes app services + main window via `AppComposer`.
- Shows main window and enters Qt event loop.

## Composition Layer (`ui_ux_team/blue_ui/app/composition.py`)
- `AppComposer.prepare_config()` -> unified settings initialization.
- `AppComposer.prepare_theme()` -> theme token application.
- `AppComposer._build_services()` creates:
- `TranscriptionManager` (only if API key exists)
- `ManagedMem`
- `GeminiChatbot` factory
- mood repository from `mood_readers/data/mood_playlists_organized.json`
- `MainWindowView` is the UI root (`MainUI` alias).

## UI Layer Boundaries
- `views/main_window.py`: central coordinator for playback/transcription/chat/settings/profile windows.
- `views/transcript_window.py`: transcript display + record control.
- `views/chat_window.py`: BlueBird chat with worker threads for initialization and request handling.
- `views/settings_popup.py` + settings widgets: modal settings surface and sections.
- `widgets/`: reusable UI controls (timeline, volume, carousel, image buttons, text components, toast, onboarding arrow).
- `theme/`: palette registry, token state, style helpers, and platform-native titlebar adjustments.
- Preview/snapshot tooling is isolated under `ui_ux_team/blue_ui/previews/` and `ui_ux_team/blue_ui/tests/iteration/dev/` for UI iteration without touching production views directly.
- Additional structural reference for layout/ownership: `ui_ux_team/blue_ui/docs/ui_complete_reference.md`.
- Historical component notes reviewed: `architects/design_docs/component_main_ui.md`, `architects/design_docs/component_audio_pipeline.md`.

## Backend/Service Integration
- Playback: `architects/helpers/miniaudio_player.py` (miniaudio backend abstraction).
- Capture/mixing primitives: `architects/helpers/audio_utils.py` (AudioController, LiveMixerController, packet builder).
- Transcription orchestration: `architects/helpers/transcription_manager.py`.
- LLM utilities and prompt handling: `architects/helpers/api_utils.py`.
- Chat wrapper: `architects/helpers/gemini_chatbot.py`.
- Gemini SDK compatibility layer: `architects/helpers/genai_client.py`.
- API quota/cost guardrails: `ui_ux_team/blue_ui/app/api_usage_guard.py`.
- API key secure storage/runtime state: `ui_ux_team/blue_ui/app/secure_api_key.py`.
- Recording source enumeration: `architects/helpers/tabs_audio.py` (PipeWire/Pulse tooling on Linux).
- Legacy/auxiliary transcription endpoints exist outside the primary Blue UI startup path.
- Platform metadata utility: `architects/platform_detection/platform_detection.py`.

## Legacy and Diagnostic Utilities
- Legacy playback backends remain in repo but are not the Blue UI default runtime path:
- `architects/helpers/music_player.py` (Qt `QMediaPlayer` direct helper)
- additional CLI-oriented player helpers
- Legacy capture/transcribe demo script: `architects/helpers/play_record_transcribe.py`.
- Linux live-mix implementation backing the Linux transcription path: `architects/helpers/record_live_mix_linux.py`.
- Platform probe scripts (diagnostic/standalone) exist alongside the main platform detection module.
- Additional standalone transcript scraping utilities exist outside Blue UI startup/runtime path.
- `ui_ux_team/prototype_r/` contains exploratory prototypes (PySide layouts, Streamlit chat, sherpa-onnx speech tests, ad-hoc audio capture scripts) and is not wired into production startup.
- `ui_ux_team/prototype_r/` should be treated as legacy after the Blue UI refactor/copy effort:
- `ui_ux_team/blue_ui/` is authoritative for runtime behavior
- `prototype_r` may include stale, partial, or non-imported code
- some prototype code was copied into `blue_ui`, while other pieces were never transferred

## Runtime Path and Config Strategy
- Config/store paths are runtime-sensitive in `ui_ux_team.blue_ui.config.runtime_paths`.
- Dev mode defaults to repository-adjacent runtime config/data folders.
- Frozen/AppImage mode uses OS-specific user config/data locations.
- `ui_ux_team.blue_ui.config.settings_store` performs normalization and legacy migration of split config keys.
- Service dependency wiring is centralized via dataclass contracts in `ui_ux_team/blue_ui/app/services.py`.
