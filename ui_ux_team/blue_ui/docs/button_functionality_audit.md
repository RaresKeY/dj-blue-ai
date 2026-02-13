# Button Functionality Audit

Compared:
- Legacy: `ui_ux_team/prototype_r/py_learn.py`
- Current: `ui_ux_team/blue_ui/views/main_window.py` (+ related button views)

## Summary
- Main sidebar and playback button wiring is mostly preserved.
- Confirmed functional regression/change: legacy volume interaction model was removed and replaced.
- Some icons are intentionally visual-only in both versions (no click handler in either codebase).

## Main Window Buttons

| Button | Legacy (`py_learn.py`) | Current (`blue_ui`) | Status |
|---|---|---|---|
| Transcript | Opens/closes transcript window (`open_transcript`) | Same behavior (`open_transcript`) | Preserved |
| API icon | No `clicked.connect(...)` | No `clicked.connect(...)` | Unchanged (still unbound) |
| Info icon | Shows floating mood toast (`info_clicked`) | Same behavior (`info_clicked`) | Preserved |
| Meet type icon | Toggles floating menu (`meet_type_menu`) | Same behavior (`meet_type_menu`) | Preserved |
| User icon | No `clicked.connect(...)` | No `clicked.connect(...)` | Unchanged (still unbound) |
| Settings icon | Opens settings popup (`settings_menu`) | Same behavior (`settings_menu`) | Preserved |
| Play button | `play_click` toggles play/pause icon/state | Same behavior | Preserved |
| Prev button | Created, no handler attached | Same | Unchanged (still unbound) |
| Next button | Created, no handler attached | Same | Unchanged (still unbound) |
| Blue bird | Opens/closes chat window | Same behavior | Preserved |

## Transcript Window Button

| Button | Legacy | Current | Status |
|---|---|---|---|
| Record | Directly connected to `parent.record_transcript` | Emits `record_clicked`, connected in main window to `record_transcript` | Preserved (architecture changed, behavior kept) |

## Chat Window Buttons

| Button | Legacy | Current | Status |
|---|---|---|---|
| Send | Calls `input_field.send_message` | Same behavior | Preserved |
| Load transcript | Opens file picker | Same behavior | Preserved |

## Lost/Changed Functionality

1. Legacy volume button drag-popup interaction removed:
- Old flow: press volume icon -> show popup slider above button, drag moves volume, release closes popup.
- Legacy refs: `ui_ux_team/prototype_r/py_learn.py:1737`, `ui_ux_team/prototype_r/py_learn.py:1764`, `ui_ux_team/prototype_r/py_learn.py:1787`, `ui_ux_team/prototype_r/py_learn.py:1808`.
- New flow: inline hover-expand volume control widget (`IntegratedVolumeControl`) with icon + horizontal slider.
- New refs: `ui_ux_team/blue_ui/widgets/volume.py:9`, `ui_ux_team/blue_ui/views/main_window.py:435`.

## Notes
- `stop_click` exists in legacy (`ui_ux_team/prototype_r/py_learn.py:1642`) but is not wired to any button there, so no button regression.
- Current `set_volume` behavior is safer: stores volume even before player exists (`ui_ux_team/blue_ui/views/main_window.py:409`), whereas legacy skipped persistence when player was absent.
