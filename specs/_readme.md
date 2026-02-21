# dj-blue-ai - Specs Index

**Tech Stack**: Python 3.12 + PySide6 desktop app

---

**IMPORTANT** Before making changes or researching any part of the codebase, use the table below to find and read the relevant spec first. This ensures you understand existing patterns and constraints.

## Documentation

| Spec | Code | Purpose |
|------|------|---------|
| [Product Context](product_context.md) | `README.md`, `ui_ux_team/blue_ui/views/main_window.py`, `ui_ux_team/blue_ui/views/transcript_window.py`, `ui_ux_team/blue_ui/views/chat_window.py` | Product scope, active runtime path, and user-facing workflows. |
| [System Architecture](system_architecture.md) | `main.py`, `ui_ux_team/blue_ui/app/main.py`, `ui_ux_team/blue_ui/app/composition.py`, `ui_ux_team/blue_ui/views/` | Entrypoints, runtime composition, and module boundaries. |
| [Domain Logic](domain_logic.md) | `architects/helpers/transcription_manager.py`, `architects/helpers/api_utils.py`, `architects/helpers/gemini_chatbot.py`, `ui_ux_team/blue_ui/app/api_usage_guard.py` | Core behavior rules for transcription, chat, playback, and API guardrails. |
| [Data Model](data_model.md) | `architects/helpers/managed_mem.py`, `ui_ux_team/blue_ui/app/services.py` | Persisted config/state contracts and managed memory storage behavior. |
| [Quality & Testing](quality_testing.md) | `ui_ux_team/blue_ui/tests/test_button_clicks.py`, `architects/tests/test_logic.py`, `architects/tests/test_song.py`, `.github/workflows/build.yml` | Test coverage, CI checks, and known quality gaps. |
| [Operational Notes](operational_notes.md) | `AGENTS.md`, `ui_ux_team/blue_ui/docs/UI_WORKFLOW.md`, `architects/design_docs/TAGGING_GUIDE.md`, `build_*.py` | Runtime setup, UI iteration workflow, and release/build operations. |

## Templates

- [Specs Template Library](../specs_templates/README.md): Reusable templates kept separate from ground-truth specs.
