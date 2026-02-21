# Domain: Transcription & Chat

## Scope
- Recording, transcription, and chat flows in active runtime.
- Main implementation files:
- `architects/helpers/transcription_manager.py`
- `architects/helpers/api_utils.py`
- `architects/helpers/gemini_chatbot.py`
- `architects/helpers/genai_client.py`

## Transcription Flow
- `TranscriptionManager` requires an API key at construction and raises `ValueError` if empty.
- On Linux, recording uses `LiveMixerController`; on other platforms it uses `AudioController`.
- Worker loop polls recorder chunks (`pop_combined_stereo()`), converts PCM to WAV, optionally adds audio analysis tags, and calls `LLMUtilitySuite.transcribe_audio_bytes(...)`.
- Structured transcription is requested with `response_mime_type = application/json` in `LLMUtilitySuite.transcribe_audio(...)`.

## Limit-Blocked Behavior
- Before transcription requests, `LLMUtilitySuite.transcribe_audio(...)` calls `reserve_request("transcript", ...)`.
- If blocked, the transcription response includes:
- `error`
- `limit_blocked = True`
- `source = "api_usage_limits"`
- `TranscriptionManager` stops recording when `limit_blocked` is present, preventing repeated blocked API calls.

## Audio Payload Handling
- Inline audio threshold is `INLINE_AUDIO_LIMIT_BYTES = 20 * 1024 * 1024`.
- If a file payload exceeds threshold and upload is enabled, `GenAIClient.upload_file(...)` is used and `file_uri` is sent instead of inline bytes.
- For byte payloads passed directly (`transcribe_audio_bytes`), audio is sent inline.

## Chat Context & Messaging
- `GeminiChatbot.load_context(...)` seeds chat history with transcript context by inserting user/model turns before interactive messaging.
- `GeminiChatbot.send_message(...)` requires initialized `chat_session`; otherwise returns an explicit error payload.
- Chat requests call `reserve_request("chat", ...)` before sending.
- Successful responses record usage via `record_usage(scope="chat", ...)`.

## Response Normalization
- `GenAIClient` and `GenAIChatSession` normalize SDK responses to dict form with:
- `text`
- `usage` token counts
- optional `raw_response` (client wrapper path)
- Legacy audio dict parts (`data` + `mime_type`, `file_uri` + `mime_type`) are converted to SDK `types.Part`.

## Key Invariants
- No transcription manager without API key.
- No chat send without initialized chat context/session.
- API usage limits are enforced before network request execution paths.
