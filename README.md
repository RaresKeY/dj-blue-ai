# dj-blue-ai
<img width="762" height="568" alt="image" src="https://github.com/user-attachments/assets/0ff4d5f6-e1ce-4dba-8a35-2cb0b3f93436" />

PySide6 desktop app for mood-aware meeting assist, music playback, transcript capture, and BlueBird AI chat.

## Quick Start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ui_ux_team/blue_ui/app/main.py
```

Optional API key for transcription/chat (`.env` in repo root):
```bash
AI_STUDIO_API_KEY=your_key_here
```

API key resolution order in runtime:
- system keyring (`SERVICE_ID=dj-blue-ai`)
- `.env` fallback

On first run, the app creates:
- `config/app_config.json`
- `music_collection/`

If `music_collection/` has no audio files, the UI shows a Music Library popup.

## Table of Contents
- [What Is Active vs Legacy](#what-is-active-vs-legacy)
- [Basic Usage](#basic-usage)
- [Project Structure](#project-structure)
- [Configuration and Persistence](#configuration-and-persistence)
- [Preview Components](#preview-components)
- [Testing](#testing)
- [Build and Release](#build-and-release)
- [Architecture and UI Docs](#architecture-and-ui-docs)
- [Troubleshooting](#troubleshooting)

## What Is Active vs Legacy
- Active production UI path: `ui_ux_team/blue_ui/`
- Legacy prototype path: `ui_ux_team/prototype_r/`
- Primary app entrypoint: `ui_ux_team/blue_ui/app/main.py`

## Basic Usage
1. Launch app:
```bash
python ui_ux_team/blue_ui/app/main.py
```
2. Use sidebar:
- Transcript button opens a separate transcript window.
- Settings button opens tabs for recording sources, theme selection, and music library folder selection.
- Blue bird button opens BlueBird chat window.
3. Use center controls:
- Play/pause from center button.
- Timeline supports click/drag seek.
- Volume control expands on hover and updates playback in real time.
4. Theme changes apply across main window, settings popup, transcript, and chat.

## Project Structure
- `ui_ux_team/blue_ui/app/`: app startup and composition.
- `ui_ux_team/blue_ui/views/`: main, settings, transcript, chat windows.
- `ui_ux_team/blue_ui/widgets/`: timeline, volume, carousel, buttons, text widgets, toast.
- `ui_ux_team/blue_ui/theme/`: theme palettes, tokens, manager.
- `ui_ux_team/blue_ui/config/`: runtime path policy and unified settings store.
- `architects/helpers/`: shared backend helpers (audio, transcription, memory, LLM utilities).
- `.github/workflows/build.yml`: tag-triggered CI build and GitHub release flow.

## Configuration and Persistence
- Unified config file: `config/app_config.json`
- Config keys: `selected_theme`, `music_folder`
- Runtime path policy (source/binary-safe): `ui_ux_team/blue_ui/config/runtime_paths.py`
- Theme persistence integration: `ui_ux_team/blue_ui/theme/manager.py`
- Music folder persistence integration: `ui_ux_team/blue_ui/views/main_window.py`

Default behavior:
- Theme defaults to `dark_theme`.
- Music folder defaults to runtime-adjacent `music_collection`.

## Preview Components
Run a single preview:
```bash
python ui_ux_team/blue_ui/previews/preview_timeline.py
```

Run auto-restart preview (watches selected preview file):
```bash
python ui_ux_team/blue_ui/previews/run_preview.py timeline
```

Available `run_preview.py` targets:
- `main`
- `chat`
- `transcript`
- `widgets`
- `covers`
- `volume`
- `timeline`
- `theme`

## Testing
Current UI smoke tests:
```bash
.venv/bin/python -m unittest ui_ux_team.blue_ui.tests.test_button_clicks
```

## Build and Release
Local binary build:
```bash
python build_binary.py
```

CI/CD:
- Workflow: `.github/workflows/build.yml`
- Trigger: push tags matching `v*`
- Platforms: Ubuntu, Windows, macOS
- Artifacts: release binaries uploaded to GitHub Releases

Example tag flow:
```bash
git tag -s v0.2.1-alpha -m "v0.2.1-alpha"
git push origin v0.2.1-alpha
```

## Architecture and UI Docs
Core architecture docs:
- `architects/design_docs/team_onboarding.md` (setup and first contribution paths)
- `architects/design_docs/py_learn_flow.md` (end-to-end flow and system observations)
- `architects/design_docs/component_main_ui.md` (main app-shell behavior)
- `architects/design_docs/component_audio_pipeline.md` (capture/playback pipeline)
- `architects/design_docs/component_llm_utility_suite.md` (Gemini wrapper API)
- `architects/design_docs/component_managed_mem.md` (state persistence helper)
- `architects/design_docs/component_ui_widgets.md` (widget roles and usage)
- `architects/design_docs/audio_components.md` (audio stack map)

Blue UI docs:
- `ui_ux_team/blue_ui/docs/ui_complete_reference.md` (full layout/widget behavior reference)
- `ui_ux_team/blue_ui/docs/component_split_plan.md` (module split and composition direction)
- `ui_ux_team/blue_ui/docs/theme_system.md` and `ui_ux_team/blue_ui/docs/theme_templates.md` (theme model + palette set)
- `ui_ux_team/blue_ui/docs/timeline_component_plan.md` and `ui_ux_team/blue_ui/docs/timeline_visual_consistency_plan.md` (timeline UX rules)
- `ui_ux_team/blue_ui/docs/song_cover_carousel_plan.md` (cover carousel behavior contract)
- `ui_ux_team/blue_ui/docs/config_persistence_binary_report.md` (runtime config behavior in source/binary)
- `ui_ux_team/blue_ui/docs/miniplayer_playback_investigation.md` (playback fixes and rationale)
- `ui_ux_team/blue_ui/docs/button_functionality_audit.md` (legacy vs current control mapping)

## Troubleshooting
1. No audio but playback log appears:
- check system output device and system volume first
- check `MiniaudioPlayer` backend/device log line
2. Empty Music Library popup on launch:
- add files to configured `music_folder` or set a new folder from Settings > Music Library
3. AI chat/transcription unavailable:
- ensure `AI_STUDIO_API_KEY` is available via keyring or `.env`
