# MainUI (App Shell)

- **Last Updated: 2026-02-18**
- **Path**: `ui_ux_team/blue_ui/views/main_window.py`
- **Purpose**: Owns the top-level window, playback controls, mood tagging, and wiring to background services (transcription, memory, audio).

## Quick Use
- Instantiate via `AppComposer` (recommended) or directly:
  ```python
  from ui_ux_team.blue_ui.views.main_window import MainWindowView
  app = QApplication(sys.argv)
  window = MainWindowView()
  window.show()
  sys.exit(app.exec())
  ```
- API Key: Loaded via `load_api_key()` which checks runtime cache, keyring, and `.env` (if allowed).

## Key Behaviors
- **Transcription**: Managed by `TranscriptionManager` (`architects/helpers/transcription_manager.py`). Toggled via `record_transcript()`.
- **Mood Tagging**: Receives `transcript_ready` signal, updates `QueuedMarqueeLabel` (mood tag), and triggers music changes based on `mood_map`.
- **Playback**: Uses `MiniaudioPlayer` for music and `PlaybackTimeline` for seeking/progress.
- **Child Windows**: Manages `TranscriptWindowView`, `BlueBirdChatView`, `APISettingsWindowView`, and `ProfileWindowView`.
- **Theme**: Supports dynamic theme switching via `set_theme()` and `ThemeChooserMenu`.

## Extending
- **New Sidebar Buttons**: Add to `build_sidebar()`.
- **Custom Transcription Logic**: Update `handle_transcript_data()` or modify `TranscriptionManager`.
- **New Popups**: Implement as a `QDialog` and add a trigger in `MainUI`.

