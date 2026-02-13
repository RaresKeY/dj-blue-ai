# Settings Button Investigation

Compared:
- Legacy: `ui_ux_team/prototype_r/py_learn.py`
- Current: `ui_ux_team/blue_ui/views/main_window.py`
- Popup view: `ui_ux_team/blue_ui/views/settings_popup.py`

## Findings

1. Settings button click binding is still present.
- Legacy: `ui_ux_team/prototype_r/py_learn.py:1601` to `ui_ux_team/prototype_r/py_learn.py:1603`
- Current: `ui_ux_team/blue_ui/views/main_window.py:316` to `ui_ux_team/blue_ui/views/main_window.py:318`

2. `settings_menu()` content is functionally the same.
- Legacy builds:
  - `"Recording Sources"` list from `get_display_names()`
  - `"Test Tab"` static list
  - then calls `SettingsPopup(...).show_pos_size(...)`
  - refs: `ui_ux_team/prototype_r/py_learn.py:1535` to `ui_ux_team/prototype_r/py_learn.py:1547`
- Current does the same:
  - refs: `ui_ux_team/blue_ui/views/main_window.py:265` to `ui_ux_team/blue_ui/views/main_window.py:273`

3. `SettingsPopup` layout and behavior are effectively parity.
- Both versions:
  - frameless popup (`Qt.FramelessWindowHint | Qt.Popup`)
  - left `QListWidget` category nav
  - right `QStackedWidget` content
  - drag-enabled title bar with close button
  - computed in-window geometry via `show_pos_size`
- Legacy refs: `ui_ux_team/prototype_r/py_learn.py:488` to `ui_ux_team/prototype_r/py_learn.py:603`
- Current refs: `ui_ux_team/blue_ui/views/settings_popup.py:74` to `ui_ux_team/blue_ui/views/settings_popup.py:186`

## Conclusion
- No clear settings-button functionality loss was found in code parity.
- Main differences are visual theming and minor margin values, not behavior.

## Likely Runtime Causes (If It Feels "Broken")
- `Qt.Popup` behavior: popup auto-closes when focus changes/clicks outside (same behavior as legacy, but can feel more sensitive depending on window manager/theme).
- Window positioning sensitivity: `show_pos_size()` depends on current parent geometry and titlebar height calculations; desktop environment differences can make placement feel off.
