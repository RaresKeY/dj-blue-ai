# py_learn.py Flow (Draft)

## Overview
- `MainUI` wires the Qt layout, playback controls, and transcript/chat affordances on launch (`ui_ux_team/prototype_r/py_learn.py:879-1044`), backed by helper widgets such as `ImageButton` for icon buttons (`ui_ux_team/prototype_r/py_learn.py:82-204`).
- Transcript window couples a record toggle with live transcript display (`ui_ux_team/prototype_r/py_learn.py:724-752`); a chat stub (`BlueBirdChat`) mirrors the text box/input pattern used elsewhere (`ui_ux_team/prototype_r/py_learn.py:840-878`).
- Audio capture combines mic + speaker into stereo chunks via `AudioController` (`architects/helpers/audio_utils.py:262-364,445-464`), persisting each chunk to a temp WAV before API transcription (`ui_ux_team/prototype_r/py_learn.py:991-1023`).
- Transcription uses `LLMUtilitySuite.transcribe_audio`, which uploads/streams files to Gemini and returns text + emotion metadata (`architects/helpers/api_utils.py:231-301`).
- Session transcripts and log-like data are cached through `ManagedMem`, which currently flushes to disk eagerly on get/set (`ui_ux_team/prototype_r/py_learn.py:941-957`, `architects/helpers/managed_mem.py:126-150,295-322`).

## End-to-End Flow
1) **Startup**: `MainUI.__init__` loads API key, builds UI, initializes `ManagedMem`, and lazily constructs child windows/menus (`ui_ux_team/prototype_r/py_learn.py:879-933`).
2) **User triggers recording**: Transcript window’s record button calls `record_transcript`, which starts `AudioController` chunking mic/speaker audio every 30s and spawns a worker thread (`ui_ux_team/prototype_r/py_learn.py:973-988`).
3) **Chunk handling**: The worker pops combined stereo PCM, writes `temp.wav`, and invokes `transcribe_audio` (Gemini) for text/translation/summary/emotion (`ui_ux_team/prototype_r/py_learn.py:991-1019`).
4) **Persistence + UI update**: Results are written into managed memory for the active session and emitted to the transcript UI via `transcript_ready` (`ui_ux_team/prototype_r/py_learn.py:941-957,1015-1019`).
5) **Playback controls**: Player buttons toggle a `PlaybackController` over a bundled demo WAV (`ui_ux_team/prototype_r/py_learn.py:1158-1176`); layout helpers manage marquee mood labels and sidebar actions (`ui_ux_team/prototype_r/py_learn.py:1045-1341`).

## Component Roles
- **UI shell**: `MainUI`, sidebar, and bottom controls coordinate navigation, playback, and child windows (`ui_ux_team/prototype_r/py_learn.py:879-1341`).
- **Transcript UX**: `TranscriptWindow` + `TextBox` display streaming transcript lines; `SearchBar` placeholder exists for filtering (`ui_ux_team/prototype_r/py_learn.py:680-838`).
- **Chat stub**: `BlueBirdChat` plus `InputBlueBird` mirror chat UX but currently only echoes text (`ui_ux_team/prototype_r/py_learn.py:755-878`).
- **Audio pipeline**: `AudioController` coordinates mic (`RecordingController`) and speaker tap (`PlaybackRecorderLinux`) capture, exposing combined PCM (`architects/helpers/audio_utils.py:262-364,445-464`). `write_wav` then persists to disk for API consumption (`architects/helpers/audio_utils.py:466-480`).
- **LLM/ASR**: `LLMUtilitySuite` handles transcription, inline upload, and response parsing with schema enforcement (`architects/helpers/api_utils.py:231-364,425-555`).
- **Stateful storage**: `ManagedMem` stores transcript sessions/logs but flushes on every `gettr`/`settr` when `_auto_flush` is True, leading to frequent disk writes (`architects/helpers/managed_mem.py:126-150,295-334`).
- **Visual elements**: `ImageButton`, `MarqueeLabel`, `FloatingToast`, and `SettingsPopup` provide animated buttons, marquee mood tags, transient toasts, and popup config panels (`ui_ux_team/prototype_r/py_learn.py:82-476`).

## Observations & Requirements
- **High TPM (≈5K TPM)**: Current worker calls `transcribe_audio` every chunk without any rate-governing state machine (`ui_ux_team/prototype_r/py_learn.py:991-1019`). Need a scheduler that batches intent (e.g., queue-next-song decision) and only hits the API at defined checkpoints; consider local/offline transcription for interim feedback, promoting only finalized segments.
- **Network spikes (≤5 MB WAV uploads)**: The pipeline writes full stereo WAVs and ships them to the API (`ui_ux_team/prototype_r/py_learn.py:999-1006`). Research front-end compression (downsample to 16 kHz mono, opus/flac), silence trimming before upload, and a local tiny ASR to gate whether to upload. Emotion analysis could be done locally with `librosa` to avoid sending emotion workloads.
- **Memory manager robustness**: `ManagedMem` flushes even on reads due to `_mark_dirty_locked` and `_auto_flush` defaults (`architects/helpers/managed_mem.py:126-150,295-322`); requirement: reduce disk churn (e.g., disable auto-flush for reads, coalesce writes, move to WAL/SQLite-lite or timed flush).

## Change Proposal
- **Introduce an API call state machine** that owns ASR/LLM cadence (e.g., per agenda event like “queue next song”) rather than per-chunk triggers. Buffer local transcripts and only send when the state machine requests an update; add backpressure to stay under 5K TPM (`ui_ux_team/prototype_r/py_learn.py:991-1019` + `architects/helpers/api_utils.py:231-301`).
- **Local-first transcription path**: Add optional tiny-model transcription (e.g., whisper-tiny or VAD+keyword) to decide whether remote transcription is needed; keep remote calls for final summaries/emotion rollups. This also shrinks network load from 5 MB uploads.
- **Adaptive audio pre-processing**: Before writing `temp.wav`, downmix to mono, resample, trim silence, and optionally compress to opus/flac to cut upload size by 3–5x (`ui_ux_team/prototype_r/py_learn.py:991-1006`, `architects/helpers/audio_utils.py:262-364,466-480`).
- **Stabilize managed memory**: Turn off auto-flush on read paths, batch `settr` writes on a timer/background worker, and consider moving to a small SQLite-backed cache to avoid constant JSON rewrites (`architects/helpers/managed_mem.py:126-150,295-334`).

## Additional Suggestions
- Add observability hooks (timers, bytes uploaded, TPM counters) around `transcribe_audio` to validate rate-limiting and surface spikes (`architects/helpers/api_utils.py:231-364`).
- Gate UI buttons while recording/Uploading to avoid overlapping threads; surface upload progress in the transcript window (`ui_ux_team/prototype_r/py_learn.py:973-1023`).
- Add error handling for missing API keys/UI feedback rather than console prints (`ui_ux_team/prototype_r/py_learn.py:925-932`).
- Provide a cache of recent transcripts in memory to avoid repeated writes/reads during a session; flush on session end.
