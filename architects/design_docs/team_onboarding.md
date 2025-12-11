# Team Onboarding (py_learn)

## Setup
- Python 3.12+ recommended. Create a venv and install deps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Desktop requirements: Qt (PySide6 wheels), `pyaudio`, and PulseAudio/PipeWire `parec` for speaker capture (Linux).
- Secrets: add `.env` with `AI_STUDIO_API_KEY=<key>` (loaded in `ui_ux_team/prototype_r/py_learn.py:934-939`).

## Run the App
- Launch: `python ui_ux_team/prototype_r/py_learn.py`. The main window shows playback controls, mood marquee, and sidebar buttons.
- Transcript window: open via sidebar transcript icon; hit the record button to start/stop capture and remote transcription.
- BlueBird chat: open via the blue bird button; currently echoes input locally.

## Where Things Are
- Flow summary: `architects/design_docs/py_learn_flow.md`.
- Components:
  - `architects/design_docs/component_main_ui.md`
  - `architects/design_docs/component_transcript_window.md`
  - `architects/design_docs/component_bluebird_chat.md`
  - `architects/design_docs/component_audio_pipeline.md`
  - `architects/design_docs/component_llm_utility_suite.md`
  - `architects/design_docs/component_managed_mem.md`
  - `architects/design_docs/component_ui_widgets.md`

## Data & Limits
- Transcripts are persisted to `managed_mem.json` via `ManagedMem` (JSON file at repo root).
- API calls go through Gemini; keep TPM in mind (≈5K TPM mentioned). Audio uploads can be ~5 MB per chunk—consider downmixing/compression when experimenting.

## First Contributions
- Add UI features by extending `MainUI.build_sidebar` or bottom controls (`ui_ux_team/prototype_r/py_learn.py:1074-1198`).
- Adjust transcription cadence inside `transcript_worker` (`ui_ux_team/prototype_r/py_learn.py:991-1023`).
- For local processing experiments, swap `LLMUtilitySuite.transcribe_audio` with a local ASR call and keep the emission to `transcript_ready`.

