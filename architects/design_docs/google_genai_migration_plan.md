# Google GenAI Migration Plan (from `google.generativeai` to `google.genai`)

## Objective
Replace deprecated `google.generativeai` usage with the supported `google.genai` SDK while preserving existing chat/transcription behavior in Blue UI and helper modules.

## Baseline Check (2026-02-18)
Command run:
- `timeout 10 .venv/bin/python architects/main.py`

Observed output:
1. Deprecation warning from `google.generativeai` in `architects/helpers/api_utils.py`.
2. Startup failure unrelated to GenAI migration:
   - `ImportError: cannot import name 'RECORD_SECONDS' from 'the_listeners'`

## In-Scope Files (current deprecated SDK usage)
- `architects/helpers/api_utils.py`
- `architects/helpers/gemini_chatbot.py`

Secondary/demo usage (optional cleanup after core migration):
- `ui_ux_team/prototype_r/audio_transcript_test.py`
- docs/build references mentioning `google.generativeai`

## Target Architecture
Keep existing app-facing interfaces stable:
- `LLMUtilitySuite` public methods stay unchanged.
- `GeminiChatbot` public methods stay unchanged.

Replace only SDK internals via a compatibility layer:
- New module: `architects/helpers/genai_client.py`
- `api_utils.py` and `gemini_chatbot.py` call this layer instead of direct SDK APIs.

This limits blast radius and allows incremental cutover.

## API Mapping Plan
### Configuration
- Current: `genai.configure(api_key=...)`
- Target: instantiate `google.genai.Client(api_key=...)` once and inject/use per helper object.

### Text Generation
- Current: `GenerativeModel(...).generate_content(...)`
- Target: `client.models.generate_content(...)` equivalent path.

### Chat Sessions
- Current: `model.start_chat(...).send_message(...)`
- Target: session wrapper in compatibility layer that stores history and calls `client.models.generate_content(...)`.

### Embeddings
- Current: `genai.embed_content(...)`
- Target: `client.models.embed_content(...)` equivalent response normalization.

### File Upload / Polling
- Current: `genai.upload_file`, `genai.get_file`
- Target: files API in `google.genai` with ACTIVE polling shim in compatibility layer.

### Model Listing
- Current: `genai.list_models()`
- Target: model listing endpoint in `google.genai`, normalized to current return shape.

### Structured Output / Schemas
- Current: `genai.types.Schema`, `GenerationConfig(response_schema=...)`
- Target: `google.genai` schema/response config objects; keep JSON parse fallback if schema invocation differs.

## Migration Phases
1. Introduce dependency and compatibility layer.
2. Migrate `architects/helpers/api_utils.py` internals to compatibility layer.
3. Migrate `architects/helpers/gemini_chatbot.py` internals to compatibility layer.
4. Run app smoke tests (`main`, chat window preview, transcript flow).
5. Remove direct `google.generativeai` imports.
6. Update build/docs to include `google.genai` and remove deprecated module references.

## Validation Checklist
- No `FutureWarning` about `google.generativeai` at startup.
- Chat sends/receives messages normally.
- Transcript audio transcription still returns expected normalized payload keys:
  - `text`, `summary`, `emotion`, `translation`
- API usage guard still receives usage metadata and records limits correctly.
- Model list and embedding utilities still function.

## Risks
- SDK response/usage metadata shape differences may break cost accounting.
- Cache/context semantics differ between old and new SDKs.
- File upload state model may have different field names.

## Risk Mitigation
- Centralize response normalization in compatibility layer.
- Keep strict fallback parsing for structured JSON.
- Add focused tests around:
  - usage metadata extraction
  - transcript response normalization
  - chat response handling

## Out-of-Scope for this migration doc
- Fixing `architects/main.py` import error (`RECORD_SECONDS` export issue in `the_listeners`).
