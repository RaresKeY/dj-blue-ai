# Audio Pipeline

- **Last Updated: 2026-02-18**
- **Core Path**: `architects/helpers/audio_utils.py`
- **Purpose**: Capture mic and system audio (speaker), package chunks (PCM), and provide audio bytes for analysis and transcription.

## Key Controllers
- **AudioController**: Basic capture of mic and speaker using `pyaudio`.
- **LiveMixerController**: Specialized Linux controller for capturing from multiple sources using `pw-record` (PipeWire/PulseAudio) and blacklisting noise.
- **RecordingController**: Internal handler for `pyaudio` input streams.
- **PlaybackRecorderLinux**: Internal handler for capturing system audio on Linux.

## Usage
- Usually managed via `TranscriptionManager`:
  ```python
  from architects.helpers.transcription_manager import TranscriptionManager
  manager = TranscriptionManager(api_key, chunk_seconds=30)
  manager.start_recording()
  # manager collects chunks and calls API automatically
  ```

## MiniaudioPlayer
- **Path**: `architects/helpers/miniaudio_player.py`
- **Purpose**: Lightweight playback for music files (`.mp3`, `.wav`, `.flac`).
- **Features**: Software volume control (0.0 - 1.0), pause/resume, and position/duration reporting.

## Operational Notes
- **Linux Requirements**: `pw-record` for speaker capture.
- **Combined Audio**: Stereo output where left channel is usually mic (mono mirrored) and right channel is speaker (mono downmixed or original right).
- **Chunking**: Defaults to 30-second chunks (`T_CHUNK`).

