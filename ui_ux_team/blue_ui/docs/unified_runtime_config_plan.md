# Unified Runtime Config Plan

## Goal
Create one runtime config file beside the binary/script in a `config` folder, initialize it with defaults on startup, and use it for both theme and music settings.

## Target Runtime Layout
- `<runtime_base_dir>/config/app_config.json`
- `<runtime_base_dir>/music_collection/`

## Default Config Payload
```json
{
  "selected_theme": "dark_theme",
  "music_folder": "<runtime_base_dir>/music_collection"
}
```

## Work Plan
1. Path foundation
- Resolve runtime base directory from executable/script.
- Resolve config dir as `<runtime_base_dir>/config`.

2. Unified store
- Replace split `theme_config.json` and `audio_config.json` reads with unified `app_config.json` accessors.
- Add `ensure_config_initialized()`, `get_setting()`, `set_setting()`.

3. Startup initialization
- Initialize config before theme/window composition.

4. Feature wiring
- Theme manager reads/writes `selected_theme`.
- Main window reads/writes `music_folder`.

5. Folder bootstrap + UX
- Ensure `music_collection` exists.
- If no audio files present, inform user with startup message/toast.

6. Migration
- If unified config absent, import values from legacy split files.

7. Documentation
- Update persistence report and implementation plan docs.

## Status
- Implemented.
