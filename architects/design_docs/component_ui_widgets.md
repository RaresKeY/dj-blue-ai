# UI Widget Set

- Path: `ui_ux_team/prototype_r/py_learn.py`
- Purpose: Reusable Qt widgets for buttons, marquees, popups, and notifications.

## Key Widgets
- `ImageButton` (`ui_ux_team/prototype_r/py_learn.py:82-204`): QLabel-based image button with hover/press animations. Use `ImageButton(path, size=(w,h), fallback=IMAGE_NOT_FOUND)` and connect `clicked`.
- `MarqueeLabel` / `QueuedMarqueeLabel` (`ui_ux_team/prototype_r/py_learn.py:206-323`): Scrolling text; `QueuedMarqueeLabel` cycles through a queue with fade transitions. Configure `step`, `interval_ms`, `gap`, `hold_ms`.
- `FloatingToast` (`ui_ux_team/prototype_r/py_learn.py:324-419`): Animated toast that rises and fades. Call `show_message(text, duration_ms=2200, bottom_band_ratio=0.3)`.
- `PopupTitleBar` + `SettingsPopup` (`ui_ux_team/prototype_r/py_learn.py:421-477`): Frameless popup scaffold with category list and stacked content; populate with dict of tab widgets.
- `FloatingMenu` (`ui_ux_team/prototype_r/py_learn.py:606-656`): Simple popup menu anchored to a parent position; emits `closed`.
- Styled text boxes: `TextBoxAI` (`ui_ux_team/prototype_r/py_learn.py:544-573`), `TextBox` (`ui_ux_team/prototype_r/py_learn.py:680-722`), `SearchBar` (`ui_ux_team/prototype_r/py_learn.py:806-838`).

## Usage Tips
- Button factory: `MainUI.button("assets/icon.png", size=(40,40))` returns an `ImageButton` with fallbacks (`ui_ux_team/prototype_r/py_learn.py:1298-1310`).
- For popups anchored to another widget, map the global position (`parent.mapToGlobal`) similar to `MainUI.meet_type_menu` (`ui_ux_team/prototype_r/py_learn.py:1025-1044`).
- Keep asset paths relative to `ui_ux_team/prototype_r/` or pass absolute paths to avoid missing icons.

