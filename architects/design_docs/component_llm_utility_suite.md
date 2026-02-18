# LLMUtilitySuite

- **Last Updated: 2026-02-18**
- **Path**: `architects/helpers/api_utils.py`
- **Purpose**: Singleton wrapper for Google Gemini API calls (text, chat, embeddings, transcription).

## Setup
- Requires `AI_STUDIO_API_KEY`.
- First instantiation configures the `google.generativeai` SDK.
- Integrated with `api_usage_guard` to respect rate limits and quotas.

## Common Calls
- **Transcription from Bytes**: `transcribe_audio_bytes(audio_bytes, mime_type="audio/wav", model_name="models/gemini-2.5-flash-lite", structured=True)`
  - Returns a dictionary with `text`, `summary`, `emotion`, `translation`, and `language_code`.
  - Uses `CUSTOM_TRANSCRIPTION_PROMPT_MEET_TYPE_SIMPLE` for structured JSON output.
- **Text Generation**: `generate_text(prompt, model_name="models/gemini-1.5-flash", system_prompt=...)`
- **Chat**: `chat = llm.start_chat(); chat.send_message("hi")`
- **Embeddings**: `get_embedding(text)` or `get_batch_embeddings(texts)`

## Notes
- **Audio Limits**: Inline audio limit is 20 MB (`INLINE_AUDIO_LIMIT_BYTES`). Files larger than this should be uploaded via the File API first.
- **Structured Parsing**: Normalizes JSON responses, strips markdown code fences, and ensures valid emotion tags.
- **Emotions**: Restricted to `positive|neutral|tense|unfocused|collaborative|creative|unproductive`.

