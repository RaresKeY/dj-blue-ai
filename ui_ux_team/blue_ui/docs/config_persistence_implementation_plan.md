# Unified Config Implementation Plan (Completed)

## Objective
Use a single runtime config file for all UI settings:
- `config/app_config.json` beside the running binary/script

## Scope
1. Merge theme + music settings into one JSON.
2. Initialize config at startup with defaults.
3. Keep migration from legacy split config files.
4. Keep runtime behavior non-fatal on IO/JSON errors.

## Planned JSON Contract
```json
{
  "selected_theme": "dark_theme",
  "music_folder": "/absolute/path/to/music_collection"
}
```

## Implementation Steps
1. Runtime path resolver
- Added `runtime_base_dir()` and config dir helper in:
  - `ui_ux_team/blue_ui/config/runtime_paths.py`

2. Unified settings store
- Added/updated:
  - `ui_ux_team/blue_ui/config/settings_store.py`
- API:
  - `ensure_config_initialized()`
  - `get_setting(key, default)`
  - `set_setting(key, value)`
- Unified file:
  - `CONFIG_FILE = "app_config.json"`

3. Startup initialization
- `AppComposer.__init__()` now calls:
  - `ensure_config_initialized()`
- File:
  - `ui_ux_team/blue_ui/app/composition.py`

4. Theme persistence migration
- Theme manager now reads/writes unified config keys:
  - `selected_theme`
- File:
  - `ui_ux_team/blue_ui/theme/manager.py`

5. Music folder persistence migration
- Main window now reads/writes unified config keys:
  - `music_folder`
- Folder default:
  - `<runtime_base_dir>/music_collection`
- File:
  - `ui_ux_team/blue_ui/views/main_window.py`

6. Legacy migration path
- On missing `app_config.json`, loader imports values from legacy:
  - `theme_config.json`
  - `audio_config.json`
- Checked both runtime `config/` and repo-local `ui_ux_team/blue_ui/config/`.

## Validation Checklist
1. Start app with no config:
- `config/app_config.json` is created with defaults.

2. Theme change:
- Restart app and verify persisted theme.

3. Music folder change:
- Restart app and verify persisted folder.

4. Empty music folder:
- Startup shows empty-folder user notice.
