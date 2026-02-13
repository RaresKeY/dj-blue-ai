# Config Persistence Report (Theme + Music Folder)

## Current State

1. Theme config currently writes to:
- `ui_ux_team/blue_ui/config/theme_config.json`
- Source: `ui_ux_team/blue_ui/theme/manager.py`
  - `_CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"`

2. Music folder config:
- Not implemented yet as a persisted JSON setting in current code.
- Current runtime music folder logic is hardcoded in main UI:
  - `ui_ux_team/blue_ui/views/main_window.py:91`
  - `get_project_root() / "mood_music_collection"`

## Binary Build Behavior (Important)

Build config uses PyInstaller `--onefile`:
- `build_binary.py` includes `--onefile`

In onefile mode, app code/resources are extracted to a temporary runtime location.
Writing config relative to module `__file__` is unreliable because:
- path may be temporary and reset each run
- path may be read-only
- writes can silently fail (theme manager currently catches exceptions)

Result:
- Theme persistence may appear to work in source runs but fail or reset in packaged binaries.

## Recommended Persistence Location

Use per-user writable config directory (OS standard), not repo-relative paths.

Recommended app namespace:
- `dj-blue-ai` / `blue_ui`

Suggested files:
- `theme_config.json`
- `audio_config.json` (for music folder)

Examples by OS:
- Linux: `~/.config/dj-blue-ai/blue_ui/`
- macOS: `~/Library/Application Support/dj-blue-ai/blue_ui/`
- Windows: `%APPDATA%\\dj-blue-ai\\blue_ui\\`

## Recommended JSON Schemas

`theme_config.json`
```json
{
  "selected_theme": "dark_theme"
}
```

`audio_config.json`
```json
{
  "music_folder": "/absolute/path/to/mood_music_collection"
}
```

## Migration Plan

1. On startup:
- Try reading user config dir first.
- If missing, fallback-read existing repo-local `ui_ux_team/blue_ui/config/*.json`.
- If fallback exists, copy/migrate to user config dir.

2. On save:
- Always write to user config dir only.

3. Validation:
- If `music_folder` path does not exist, fallback to:
  - `<executable_dir>/mood_music_collection` (frozen)
  - `<project_root>/mood_music_collection` (source)

## Practical Risk If Not Changed

- Binary users lose saved theme after restart.
- Future music-folder setting will also fail persistence in onefile builds if saved module-relative.
