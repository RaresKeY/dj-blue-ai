# dj-blue-ai - Specs Index

**Tech Stack**: Python 3.12 + PySide6 desktop app

---

**IMPORTANT** Before making changes or researching any part of the codebase, use the table below to find and read the relevant spec first. This ensures you understand existing patterns and constraints.

## Documentation

| Spec | Code | Purpose |
|------|------|---------|
| [Product Context](product_context.md) | `README.md`, `ui_ux_team/blue_ui/views/main_window.py`, `ui_ux_team/blue_ui/views/transcript_window.py`, `ui_ux_team/blue_ui/views/chat_window.py` | Product scope, active runtime path, and user-facing workflows. |
| [System Architecture](system_architecture.md) | `main.py`, `ui_ux_team/blue_ui/app/main.py`, `ui_ux_team/blue_ui/app/composition.py`, `ui_ux_team/blue_ui/views/` | Entrypoints, runtime composition, and module boundaries. |
| [Domain Logic (Overview)](domain_logic.md) | `architects/helpers/transcription_manager.py`, `architects/helpers/api_utils.py`, `architects/helpers/gemini_chatbot.py`, `ui_ux_team/blue_ui/app/api_usage_guard.py`, `ui_ux_team/blue_ui/views/main_window.py` | Behavioral index linking to focused domain specs. |
| [Domain: Transcription & Chat](domain_transcription_and_chat.md) | `architects/helpers/transcription_manager.py`, `architects/helpers/api_utils.py`, `architects/helpers/gemini_chatbot.py`, `architects/helpers/genai_client.py` | Recording/transcription/chat behavior and guard interactions. |
| [Domain: Playback & Start Cycle](domain_playback_and_startup_cycle.md) | `ui_ux_team/blue_ui/views/main_window.py`, `architects/helpers/miniaudio_player.py`, `mood_readers/data/mood_playlists_organized.json` | Playback and startup gating behavior in active UI runtime. |
| [Domain: API Usage Limits](domain_api_usage_limits.md) | `ui_ux_team/blue_ui/app/api_usage_guard.py`, `ui_ux_team/blue_ui/config/settings_store.py` | Rate-limit and budget enforcement semantics and persistence. |
| [Data Model (Overview)](data_model.md) | `ui_ux_team/blue_ui/config/settings_store.py`, `architects/helpers/managed_mem.py`, `ui_ux_team/blue_ui/app/services.py` | Data-contract index linking to focused data specs. |
| [Data: Settings & Runtime Paths](data_settings_and_runtime_paths.md) | `ui_ux_team/blue_ui/config/settings_store.py`, `ui_ux_team/blue_ui/config/runtime_paths.py` | Normalized settings schema and runtime path policy. |
| [Data: Managed Memory](data_managed_memory.md) | `architects/helpers/managed_mem.py` | Managed memory singleton, persistence semantics, and log behavior. |
| [Data: Legacy & Auxiliary Contracts](data_legacy_and_auxiliary_contracts.md) | `architects/song.py`, `transcribers/the_transcribers.py`, `mood_readers/data/` | Non-primary runtime contracts and historical artifacts still present in repo. |
| [Quality & Testing](quality_testing.md) | `ui_ux_team/blue_ui/tests/test_button_clicks.py`, `architects/tests/test_logic.py`, `architects/tests/test_song.py`, `.github/workflows/build.yml` | Test coverage, CI checks, and known quality gaps. |
| [Operational Notes (Overview)](operational_notes.md) | `AGENTS.md`, `ui_ux_team/blue_ui/docs/UI_WORKFLOW.md`, `architects/design_docs/TAGGING_GUIDE.md`, `build_*.py` | Operations index linking to focused runtime/QA/release docs. |
| [Operations: Runtime & Environment](operations_runtime_and_env.md) | `main.py`, `ui_ux_team/blue_ui/app/main.py`, `ui_ux_team/blue_ui/app/composition.py`, `ui_ux_team/blue_ui/app/secure_api_key.py` | Startup/run commands, API key resolution, and runtime persistence behavior. |
| [Operations: UI Iteration Workflow](operations_ui_iteration.md) | `ui_ux_team/blue_ui/docs/UI_WORKFLOW.md`, `ui_ux_team/blue_ui/previews/`, `ui_ux_team/blue_ui/tests/iteration/` | Required workflow for preview-driven UI changes and snapshots. |
| [Operations: Build & Release](operations_build_release.md) | `.github/workflows/build.yml`, `build_binary.py`, `build_appimage.py`, `build_nuitka.py`, `architects/design_docs/TAGGING_GUIDE.md` | Build artifacts, CI release triggers, and release tagging policy. |
