# Product Context

## Scope
- `dj-blue-ai` is a desktop PySide6 app centered on:
- local music playback
- live meeting/audio transcription
- transcript-assisted chat ("BlueBird AI")
- mood-aware behavior that can drive music switching

Primary evidence:
- `README.md`
- `ui_ux_team/blue_ui/views/main_window.py`
- `ui_ux_team/blue_ui/views/transcript_window.py`
- `ui_ux_team/blue_ui/views/chat_window.py`

## Active vs Legacy Runtime
- Active production UI/runtime path: `ui_ux_team/blue_ui/`.
- Compatibility launcher: root `main.py` delegates to `ui_ux_team.blue_ui.app.main:run`.
- `ui_ux_team/prototype_r/` is legacy. It was a prototype/refactor source and substantial UI/runtime logic was copied or migrated into `ui_ux_team/blue_ui/`.
- `ui_ux_team/prototype_r/` is not a production runtime source of truth; it may contain:
- code copied into `blue_ui`
- code not imported by production modules
- partially implemented or exploratory code
- code paths that were not transferred into `blue_ui`
- Additional legacy standalone tools remain in repo:
- `transcribers/the_transcribers.py` (Tk batch transcription app)
- `the_listeners/dj_the_listeners.py` and `the_listeners/dj_the_transcribers.py` (older recorder/transcriber utilities)

## Core User Flows
- Main window: transport controls, timeline seek, volume control, cover carousel, and side actions (transcript/API/settings/chat/profile).
- Transcript window: separate top-level window with record toggle and rolling transcript text.
- Chat window: separate top-level window that initializes context from transcript and supports follow-up prompts.
- Settings popup: recording source list, theme selection, music folder selection, API usage limits, and model selection.

## Functional Preconditions
- Transcription requires API key resolution (runtime cache -> keyring -> process env -> optional local env-file fallback when explicitly allowed).
- Playback requires audio files in configured `music_folder`.
- Startup "Start cycle" preflight checks:
- API key configured
- music folder non-empty
- configured music library matches playlist filenames expected by `mood_readers/data/mood_playlists_organized.json`

## Non-Goals / Out of Scope (Current Ground Truth)
- No web service/backend deployment model in repository runtime path.
- No DB schema migration system; persistence is local JSON/keyring based.
