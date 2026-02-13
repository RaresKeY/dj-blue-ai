# Config Persistence Report (Unified Runtime Config)

## Implemented Model

Config now uses one unified JSON file:
- `config/app_config.json`

Location policy:
- always beside the running binary/script
- config directory is created automatically at startup

Examples:
- binary run: `<binary_dir>/config/app_config.json`
- source run: `<script_dir>/config/app_config.json`

## Defaults Created on First Run

On initialization, defaults are written if file is missing:
```json
{
  "selected_theme": "dark_theme",
  "music_folder": "<runtime_base_dir>/music_collection"
}
```

Runtime folders auto-created:
- `<runtime_base_dir>/config/`
- `<runtime_base_dir>/music_collection/`

## Migration Support

If unified config is absent, app attempts legacy import from:
- `config/theme_config.json`
- `config/audio_config.json`
- `ui_ux_team/blue_ui/config/theme_config.json`
- `ui_ux_team/blue_ui/config/audio_config.json`

Loaded values are normalized and saved into unified `app_config.json`.

## Code Ownership

1. Path and folder policy:
- `ui_ux_team/blue_ui/config/runtime_paths.py`

2. Unified settings store:
- `ui_ux_team/blue_ui/config/settings_store.py`

3. Theme persistence integration:
- `ui_ux_team/blue_ui/theme/manager.py`

4. Music folder persistence integration:
- `ui_ux_team/blue_ui/views/main_window.py`

5. Startup initialization:
- `ui_ux_team/blue_ui/app/composition.py`

## Binary Behavior

This model avoids module-relative temp extraction issues because config is resolved from runtime base directory, not from package source paths.

## User Feedback

If `music_collection` has no audio files, UI shows:
- console message
- toast notification in main window
