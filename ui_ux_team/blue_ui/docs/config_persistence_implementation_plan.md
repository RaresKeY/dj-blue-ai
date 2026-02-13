# Config Persistence Implementation Plan (No-Code Plan)

## Objective
Implement robust persistence for both theme and music-folder settings in source and PyInstaller onefile builds, using a user-writable config location.

## Scope
1. Persist `selected_theme` in user config directory.
2. Persist `music_folder` in user config directory.
3. Migrate legacy repo-local config files when present.
4. Keep behavior safe/fallback-oriented if config read/write fails.

## Target Files (Planned)
1. `ui_ux_team/blue_ui/theme/manager.py`
2. `ui_ux_team/blue_ui/views/main_window.py`
3. New shared config helper module:
- `ui_ux_team/blue_ui/config/runtime_paths.py` (planned)
- `ui_ux_team/blue_ui/config/settings_store.py` (planned)
4. Optional docs update:
- `ui_ux_team/blue_ui/docs/config_persistence_binary_report.md`

## Planned Runtime Path Strategy
Use per-user app config path:
- Linux: `~/.config/dj-blue-ai/blue_ui/`
- macOS: `~/Library/Application Support/dj-blue-ai/blue_ui/`
- Windows: `%APPDATA%\\dj-blue-ai\\blue_ui\\`

Fallback read-only legacy source path (migration source):
- `ui_ux_team/blue_ui/config/`

Write policy:
- Always write only to user config dir.

## Planned JSON Contracts
1. `theme_config.json`
```json
{
  "selected_theme": "dark_theme"
}
```

2. `audio_config.json`
```json
{
  "music_folder": "/absolute/path/to/mood_music_collection"
}
```

## Implementation Steps
1. Add config-path resolver helpers:
- Detect OS and return user-writable app config dir.
- Ensure directory creation is centralized.

2. Add JSON settings-store helpers:
- `load_json(path) -> dict | None`
- `save_json(path, data) -> bool`
- Keep exception handling non-fatal.

3. Update theme persistence (`theme/manager.py`):
- Read from user config dir.
- If missing, attempt legacy repo-local read, then migrate.
- Save theme changes to user config dir only.

4. Add music-folder persistence in main UI:
- Load `music_folder` from `audio_config.json`.
- Validate existence; fallback to:
  - frozen: `<executable_dir>/mood_music_collection`
  - source: `<project_root>/mood_music_collection`
- Save when changed via settings UI folder picker.

5. Migration behavior:
- On first run, if repo-local config exists and user config missing:
  - copy keys into user config files
  - keep legacy files untouched.

6. Telemetry/logging (minimal):
- Use clear console logs for:
  - migration executed
  - fallback path selected
  - invalid folder path replaced.

## Edge Cases
1. Corrupt JSON: ignore and fallback to defaults.
2. Non-existent music folder: fallback path + overwrite stored value.
3. Permission-denied writing config: continue app without crash.
4. Unknown theme key: fallback to `DEFAULT_THEME_KEY`.

## Verification Checklist
1. Source run:
- Change theme, restart app, theme persists.
- Change music folder, restart app, folder persists.

2. Onefile binary run:
- Same persistence checks as above.
- Confirm files are written in OS user config dir, not temp extraction dir.

3. Migration test:
- Place legacy config in `ui_ux_team/blue_ui/config/`.
- Start app with empty user config dir.
- Verify user config files are created with migrated values.

4. Failure resilience:
- Corrupt JSON and confirm app still launches with defaults.

## Rollout Sequence
1. Implement helpers.
2. Wire theme manager.
3. Wire music folder load/save.
4. Add/verify settings folder picker tab behavior.
5. Manual verification in source and binary environments.
