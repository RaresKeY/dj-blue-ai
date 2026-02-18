# BlueBirdChat

- **Last Updated: 2026-02-18**
- **Path**: `ui_ux_team/blue_ui/views/chat_window.py`
- **Purpose**: AI chat assistant that uses the current transcript (or an uploaded file) as context for answering user queries.

## Usage
- Construct and show via `MainUI.open_bluebird_chat()`.
- Uses `GeminiChatbot` (`architects/helpers/gemini_chatbot.py`) for LLM interaction and context caching.
- Context is initialized with the current transcript from `TranscriptWindowView`.

## Key Features
- **Context Caching**: Uses Google GenAI's `CachedContent` for transcripts > 1000 characters to reduce latency and cost.
- **Background Workers**: `ChatInitWorker`, `ChatWorker`, and `ContextUpdateWorker` ensure the UI remains responsive during API calls.
- **File Loading**: Supports loading external `.txt` files to update the chat context via `open_file_picker()`.

## Notes
- **Models**: Defaults to `models/gemini-3-flash-preview` (configurable in `BlueBirdChatView`).
- **Styling**: Uses tokens from `ui_ux_team/blue_ui/theme/tokens.py`.
- **Loading State**: Displays a `LoadingCircle` while waiting for AI responses.

