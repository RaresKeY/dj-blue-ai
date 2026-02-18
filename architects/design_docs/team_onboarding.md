# Team Onboarding (Blue UI)

- **Last Updated: 2026-02-18**

## Setup
- **Python 3.12+** recommended. Create a venv and install deps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- **Desktop Requirements**: Qt (PySide6), `pyaudio`, `miniaudio`, and `pw-record` (Linux) for speaker capture.
- **Secrets**: Add `.env` with `AI_STUDIO_API_KEY=<key>` or use the app's settings window to save it to the system keyring.

## Run the App
- **Launch**: `python architects/main.py` (shim) or `python ui_ux_team/blue_ui/app/main.py`.
- **Main Window**: Shows music playback controls, interactive carousel, mood marquee, and sidebar buttons.
- **Transcript**: Open via sidebar; hit the record button to start/stop capture and transcription.
- **BlueBird Chat**: AI assistant that answers questions based on the current transcript.

## Where Things Are
- **Flow Summary**: `architects/design_docs/blue_ui_flow.md`
- **Components**:
  - `architects/design_docs/component_main_ui.md`
  - `architects/design_docs/component_transcript_window.md`
  - `architects/design_docs/component_bluebird_chat.md`
  - `architects/design_docs/component_audio_pipeline.md`
  - `architects/design_docs/component_llm_utility_suite.md`
  - `architects/design_docs/component_managed_mem.md`
  - `architects/design_docs/component_ui_widgets.md`

## Data & Limits
- **Persistence**: Managed via `architects/helpers/managed_mem.py`.
- **API Guard**: Usage limits and cost tracking in `ui_ux_team/blue_ui/app/api_usage_guard.py`.
- **Audio Chunks**: 30-second PCM chunks are analyzed locally with `librosa` before being sent to Gemini.

## First Contributions
- **UI Features**: Extend `MainWindowView` in `ui_ux_team/blue_ui/views/main_window.py`.
- **Backend Services**: Check `AppComposer` and `AppServices` in `ui_ux_team/blue_ui/app/composition.py`.
- **New Widgets**: Add to `ui_ux_team/blue_ui/widgets/`.

