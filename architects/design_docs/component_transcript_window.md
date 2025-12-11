# Transcript Window

- Path: `ui_ux_team/prototype_r/py_learn.py:724-752` (+ helpers `TextBox` at `ui_ux_team/prototype_r/py_learn.py:680-722`, `SearchBar` at `ui_ux_team/prototype_r/py_learn.py:806-838`)
- Purpose: Secondary window that shows live transcript text and exposes a record toggle.

## Usage
- Created by `MainUI` and toggled via `open_transcript` (`ui_ux_team/prototype_r/py_learn.py:958-972`).
- Record button calls parent `record_transcript`; search bar is present but filtering is not implemented.
- Append transcript lines by emitting `MainUI.transcript_ready`, which calls `TranscriptWindow.add_transcript_segment`.

## Notes
- `_read_transcript` is stubbed; implement to pre-load saved sessions from `ManagedMem` if desired.
- The layout is vertical: record/search row (10%), text area (90%).
- The text box is read-only and styled for dark theme; modify CSS in `TextBox` if you change theming.

