# LLMUtilitySuite

- Path: `architects/helpers/api_utils.py:63-644`
- Purpose: Singleton wrapper for Gemini API calls (text, chat, embeddings, transcription).

## Setup
- Requires `AI_STUDIO_API_KEY` (loaded in `py_learn.py:934-939` via `.env`); first instantiation configures the SDK (`architects/helpers/api_utils.py:76-98`).

## Common Calls
- Transcription from file:  
  ```python
  llm = LLMUtilitySuite(api_key)
  result = llm.transcribe_audio("temp.wav")  # returns text/summary/emotion/translation
  ```
  Uses upload vs inline depending on size (`architects/helpers/api_utils.py:231-301`).
- Transcription from bytes: `transcribe_audio_bytes(audio_bytes, mime_type="audio/wav")` (`architects/helpers/api_utils.py:303-373`).
- Text generation: `generate_text(prompt, model_name="gemini-flash-latest", system_prompt=...)` (`architects/helpers/api_utils.py:100-126`).
- Chat: `chat = llm.start_chat(); chat.send_message("hi")` (`architects/helpers/api_utils.py:128-170`).
- Embeddings: `get_embedding(text)` or `get_batch_embeddings(texts)` (`architects/helpers/api_utils.py:173-228`).

## Notes
- Transcription prompts default to meet-type JSON schema; override `prompt` for custom shape.
- Large uploads (>20 MB) use the file upload path; inline limit is `INLINE_AUDIO_LIMIT_BYTES`.
- Structured parsing normalizes emotion casing and strips code fences (`architects/helpers/api_utils.py:425-555`).

