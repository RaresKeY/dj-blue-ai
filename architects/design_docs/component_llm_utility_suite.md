# LLMUtilitySuite

- **Last Updated: 2026-02-18**
- **Path**: `architects/helpers/api_utils.py`
- **Purpose**: Singleton wrapper for Google Gemini API calls, now using the `google.genai` SDK via `GenAIClient`.

## Setup
- Requires `AI_STUDIO_API_KEY`.
- Initialized with a `GenAIClient` compatibility layer to ensure stable response normalization and metadata tracking.
- Integrated with `api_usage_guard` for request limits and budget enforcement.

## Common Calls
- **Transcription**: `transcribe_audio_bytes()` uses `GenAIClient.generate_content` with JSON response mode.
- **Chat**: `start_chat()` returns a `GenAIChatSession` that handles history and token tracking.
- **Embeddings**: `get_embedding()` and `get_batch_embeddings()` use the latest SDK embedding methods.

## Technical Notes
- **Compatibility Layer**: Uses `architects/helpers/genai_client.py` to shim the new SDK logic while preserving the old public interface.
- **Audio Thresholds**: Inline audio is capped at 20 MB (`INLINE_AUDIO_LIMIT_BYTES`); larger files are automatically uploaded via `GenAIClient.upload_file`.
- **Metadata**: Response usage metadata is normalized into a standard dictionary for consistent logging and budget tracking.

