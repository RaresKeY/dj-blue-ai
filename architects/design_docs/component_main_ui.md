# MainUI (App Shell)

- Path: `ui_ux_team/prototype_r/py_learn.py:879-1341`
- Purpose: Owns top-level window, layout, playback controls, transcript/chat toggles, and wiring to backend services (memory, audio capture, LLM transcription).

## Quick Use
- Instantiate inside a Qt app:  
  ```python
  app = QApplication(sys.argv)
  window = MainUI()
  window.show()
  sys.exit(app.exec())
  ```
- API key: loaded via `.env` (`AI_STUDIO_API_KEY`) in `load_api_key` (`ui_ux_team/prototype_r/py_learn.py:934-939`).

## Key Behaviors
- Recording/transcription: `record_transcript` toggles `AudioController` capture and spawns `transcript_worker` to write `temp.wav` and call `LLMUtilitySuite.transcribe_audio` (`ui_ux_team/prototype_r/py_learn.py:973-1023`).
- Transcript routing: `transcript_ready` signal feeds `TranscriptWindow.add_transcript_segment` on the UI thread (`ui_ux_team/prototype_r/py_learn.py:917-920,1015-1019`).
- Memory: session transcripts persisted via `ManagedMem.settr/gettr` (`ui_ux_team/prototype_r/py_learn.py:941-957`).
- Playback: `play_click/stop_click` drive `PlaybackController` over a bundled WAV (`ui_ux_team/prototype_r/py_learn.py:1151-1177`).
- Child windows: `open_transcript`, `open_bluebird_chat`, `settings_menu`, and `meet_type_menu` manage popups and stateful references (`ui_ux_team/prototype_r/py_learn.py:958-1058,1200-1227`).

## Extending
- Add new sidebar buttons via `build_sidebar` (`ui_ux_team/prototype_r/py_learn.py:1074-1123`); wire callbacks directly on the created `ImageButton`.
- To intercept transcripts before UI, hook into `transcript_ready` or wrap `_update_transcript_mem`.
- To constrain API rate, place gating logic inside `transcript_worker` before `transcribe_audio`.

