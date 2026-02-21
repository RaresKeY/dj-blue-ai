# Domain Logic

## Core Concepts
- **Transcription Cycle**: chunked audio capture -> optional audio analysis tags -> Gemini transcription -> UI updates + transcript persistence.
- **Chat Contexting**: BlueBird chat initializes with transcript-derived context before interactive Q/A.
- **Mood-Driven Playback**: emotion tags from transcription can trigger mood-mapped track selection.
- **Guarded API Usage**: request throughput and estimated spend are enforced and persisted locally.

## Invariants
- Transcription manager cannot initialize without API key.
- Chat send requires initialized chat session; otherwise returns explicit error payload.
- API requests are blocked when minute/day/budget guard limits are exceeded.
- Settings values are normalized/clamped before persistence (theme, folder, limits, models).
- Playback operations are no-op/fallback-safe when target file does not resolve.

## Main Behavioral Rules
- API key resolution order:
- runtime in-memory key
- keyring (`SERVICE_ID=dj-blue-ai`)
- process environment
- local env-file only if allowed by persisted preference
- `ui_ux_team/blue_ui/app/secure_api_key.py` keeps runtime API key/source in process globals and syncs keyring aliases (`AI_STUDIO_API_KEY`, `AI_STUDIO`) together on save/clear.
- Transcription:
- `TranscriptionManager` uses `LiveMixerController` on Linux and `AudioController` otherwise.
- Each chunk is converted to WAV and passed to `LLMUtilitySuite.transcribe_audio_bytes`.
- If transcription result includes `limit_blocked`, recording is stopped to avoid repeated blocked calls.
- `architects/helpers/audio_utils.py` preserves trailing partial chunks on stop (`force=True`) so final transcription chunk is not lost.
- Chat:
- `GeminiChatbot.load_context` seeds conversation history with transcript preamble.
- `GeminiChatbot.send_message` reserves request quota and records usage metadata after response.
- LLM utility behavior:
- `LLMUtilitySuite` is a singleton wrapper around `GenAIClient`.
- Inline audio threshold is 20 MB; larger payloads switch to upload path.
- Structured transcription mode requests JSON response format.
- `architects/helpers/genai_client.py` normalizes legacy dict parts (`data`/`mime_type`, `file_uri`/`mime_type`) into `google.genai.types.Part` and normalizes usage metadata in wrapper responses.
- Playback:
- `MiniaudioPlayer` supports start/pause/resume/stop/seek with position and duration reporting.
- Timeline seeks lock short-term synchronization to avoid visual feedback loops.
- Preflight "Start cycle" gate in main window requires API key + non-empty music folder + required playlist file match.

## Edge Cases Handled
- Missing audio track resolves to first available track in music folder where possible.
- Missing keyring support returns explicit backend error in API settings UI.
- Missing env-file key or denied fallback returns empty key (transcription/chat stay unavailable).
- Offscreen Qt mode suppresses startup modal prompts intended for interactive use.
- Legacy note: some design docs describe features no longer present in active code (for example cached-content chat behavior); implementation files are authoritative.
- Legacy boundary note: `ui_ux_team/prototype_r/` is historical and may diverge from `ui_ux_team/blue_ui/`; do not treat prototype behaviors as current runtime logic unless production imports prove usage.
- Example drift observed: `architects/design_docs/blue_ui_flow.md` describes CachedContent usage, while current `architects/helpers/gemini_chatbot.py` uses seeded chat history context.
- Example drift observed: `ui_ux_team/blue_ui/docs/button_functionality_audit.md` reports API/user buttons as unbound, but current `ui_ux_team/blue_ui/views/main_window.py` binds both.
- Legacy mood tooling includes environment-specific path assumptions in older scripts, so direct execution is machine-dependent.

## Validation Signals in Code
- UI errors are surfaced in transcript/chat windows and via toast/status labels.
- API usage state is queryable through `current_usage_state()` for live settings display.
- API usage limits are clamped and normalized to bounded ranges (RPM, RPD, monthly USD budget) in settings and guard logic.
- Design-note cross checks reviewed: `architects/design_docs/api_usage_limits_rules.md`, `architects/design_docs/component_llm_utility_suite.md`.
- Unit tests cover:
- settings/API usage logic
- managed memory persistence
- button-click smoke behavior for key UI controls
