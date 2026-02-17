# API Settings Component

## Goal

Add a dedicated API settings UI that opens from the sidebar API button and lets users securely store the `AI_STUDIO_API_KEY` in the OS keychain backend:

- Linux: Secret Service (Seahorse UI)
- macOS: Keychain Access
- Windows: Credential Manager

## UX Contract

1. Clicking the API sidebar button opens/closes an API settings window.
2. On first-run guidance arrow flow:
- arrow points API button while key is missing
- after successful key save, arrow points Transcript button
- clicking Transcript at that stage dismisses arrow
3. The window contains:
- API key input (masked)
- Save button (stores key in keyring and updates runtime env)
- Clear button (removes key from keyring and runtime env)
- Status message (success/error + key present/missing)
- OS backend guidance text (Seahorse / Keychain Access / Credential Manager)
4. If a key is saved successfully, transcription setup can be reinitialized without restarting the app.
5. The component supports theme refresh and window focus behavior like other auxiliary windows.

## Technical Design

- Add `ui_ux_team/blue_ui/app/secure_api_key.py`:
  - keyring read/write/delete helpers
  - backend description helper by platform
  - safe fallback when `keyring` is unavailable
- Add `ui_ux_team/blue_ui/views/api_settings_window.py`:
  - `APISettingsWindowView` with signals:
    - `closed`
    - `api_key_saved`
- Update `ui_ux_team/blue_ui/views/main_window.py`:
  - wire `_btn_api` to open/close API settings window
  - refresh transcription manager after API key save
  - include window in focus/theme management
- Add previews:
  - `ui_ux_team/blue_ui/previews/preview_api_settings_window.py`
  - `ui_ux_team/blue_ui/previews/preview_api_settings_flow.py` (auto-click API button in main view)
  - register in `ui_ux_team/blue_ui/previews/run_preview.py`
- Update tests:
  - API button click now asserts API settings window toggles open/closed

## Notes

- Keep `.env` fallback behavior intact.
- Do not hard-fail when keyring backend is unavailable; show actionable UI message.

## Preview Commands

- API settings window preview:
  - `.venv/bin/python ui_ux_team/blue_ui/previews/preview_api_settings_window.py`
- Main flow preview (auto-click API button):
  - `.venv/bin/python ui_ux_team/blue_ui/previews/preview_api_settings_flow.py`
- Runner shortcuts:
  - `.venv/bin/python ui_ux_team/blue_ui/previews/run_preview.py api`
  - `.venv/bin/python ui_ux_team/blue_ui/previews/run_preview.py api_flow`
  - `.venv/bin/python ui_ux_team/blue_ui/previews/run_preview.py iter_api_keyring`
