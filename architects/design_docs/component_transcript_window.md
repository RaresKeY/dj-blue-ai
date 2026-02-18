# Transcript Window

- **Last Updated: 2026-02-18**
- **Path**: `ui_ux_team/blue_ui/views/transcript_window.py`
- **Purpose**: Secondary window that shows live transcript text and provides search and recording controls.

## Key Features
- **Real-time Updates**: Segments are appended as they arrive from `TranscriptionManager` via `MainUI`.
- **Recording Toggle**: Controls the global recording state; updates icon and displays a "is recording..." status label with animated dots.
- **Search**: `SearchBar` widget for filtering or finding specific terms within the transcript (uses `TextBox`).
- **Persistence**: Transcripts are progressively saved to `ui_ux_team/transcripts/` by `MainUI`.

## Usage
- Created by `MainUI` and toggled via `open_transcript()`.
- Record button emits `record_clicked` signal to the parent `MainUI`.
- Append transcript lines via `append_segment(text)`.

## Notes
- **Styling**: Uses `COLOR_BG_MAIN` and `ACCENT` tokens from `ui_ux_team/blue_ui/theme/tokens.py`.
- **Native Titlebar**: Uses `apply_native_titlebar_for_theme` for a consistent OS look.
- **Layout**: Vertical layout with recording/search row on top, followed by the main text area.

