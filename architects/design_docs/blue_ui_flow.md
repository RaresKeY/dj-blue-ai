# Blue UI Flow

- **Last Updated: 2026-02-18**

## Overview
- **AppComposer** (`ui_ux_team/blue_ui/app/composition.py`) handles the orchestration and initialization of application services and the main window.
- **MainWindowView** (`ui_ux_team/blue_ui/views/main_window.py`) provides the core user interface, coordinating playback, mood tracking, and child windows.
- **TranscriptionManager** (`architects/helpers/transcription_manager.py`) manages the background recording loop, local audio analysis (`librosa`), and API transcription calls.
- **GeminiChatbot** (`architects/helpers/gemini_chatbot.py`) provides an AI assistant powered by Gemini with context caching for long transcripts.
- **Audio Pipeline** (`architects/helpers/audio_utils.py`) captures microphone and system audio (speaker) as PCM chunks.

## End-to-End Flow
1. **Startup**: `AppComposer.bootstrap()` initializes configuration, themes, and `AppServices` (memory, transcription, chat, player). It then builds and shows `MainWindowView`.
2. **User Triggers Recording**: `MainUI.record_transcript()` calls `TranscriptionManager.start_recording()`, which spawns a background thread and starts an `AudioController` (or `LiveMixerController` on Linux).
3. **Chunk Processing**: Every 30 seconds (`T_CHUNK`), `TranscriptionManager` pops an audio chunk, performs local analysis with `librosa` (BPM, key, mood), and sends it to the Gemini API via `LLMUtilitySuite.transcribe_audio_bytes`.
4. **Mood & UI Update**: Transcription results (text, summary, emotion, translation) are emitted back to `MainUI`. The UI updates the marquee mood tag, saves the transcript, and optionally triggers a music change based on the detected emotion.
5. **Interactive Chat**: The user opens `BlueBirdChatView`, which initializes its context with the current transcript. `GeminiChatbot` sends user queries to the AI and displays responses, using context caching for efficiency.
6. **Music Playback**: `MiniaudioPlayer` handles music files. Users can interact with the `SongCoverCarousel` or `PlaybackTimeline` to navigate and seek through the music collection.

## Component Roles
- **UI Views**: `MainWindowView`, `TranscriptWindowView`, `BlueBirdChatView`, `APISettingsWindowView`, `ProfileWindowView`.
- **Services**: `AppServices` holds singletons for `TranscriptionManager`, `ManagedMem`, `GeminiChatbot` factory, and the `mood_repository`.
- **Helpers**: `api_utils.py` (LLM wrapper), `audio_utils.py` (capture), `miniaudio_player.py` (playback), `managed_mem.py` (persistence).
- **Widgets**: Reusable components like `ImageButton`, `QueuedMarqueeLabel`, `SongCoverCarousel`, `IntegratedVolumeControl`.

## Observations & Requirements
- **Rate Limiting**: `APIUsageGuard` ensures the app stays within configured TPM/RPD/USD limits.
- **Local Analysis**: Using `librosa` for BPM and mood hints locally reduces reliance on the API for basic audio metadata and provides context for the transcription prompt.
- **Context Caching**: For transcripts over 1000 characters, `GeminiChatbot` uses `CachedContent` to minimize cost and latency.
- **Cross-Platform**: The app detects the OS to choose between `AudioController` and `LiveMixerController` (Linux-specific with PipeWire/PulseAudio support).
