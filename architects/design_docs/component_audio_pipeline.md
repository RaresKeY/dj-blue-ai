# Audio Pipeline

- Path: `architects/helpers/audio_utils.py` (core `AudioController` at `:262-364,445-464`; writers at `:466-480`; playback/recording controllers at `:15-131` and `:133-260`).
- Purpose: Capture mic + speaker, package chunks, and hand off PCM/WAV for playback or API upload.

## Usage
- Basic capture:
  ```python
  controller = AudioController(chunk_seconds=30)
  controller.start()
  # ... later ...
  pcm = controller.pop_combined_stereo()  # mic mirrored to L/R, speaker stereo intact
  write_wav("out.wav", pcm, rate=controller.mic.rate, channels=2, sampwidth=controller.mic.sampwidth)
  controller.stop()
  controller.close()
  ```
- For dual-channel (mic left, speaker mono right) use `pop_combined_dual`.
- `RecordingController` and `PlaybackRecorderLinux` are started internally; avoid starting them directly unless you are bypassing `AudioController`.

## Operational Notes
- Dependencies: `pyaudio`, `parec` (PulseAudio/PipeWire) for speaker capture; ensure system packages are installed.
- Chunk timing is driven by a background thread; `stop()` forces a final chunk flush.
- PCM is raw 16-bit little-endian; resample/downmix before upload if you need smaller files.
- Playback of static WAVs uses `PlaybackController` (callback-based, supports pause/resume) (`architects/helpers/audio_utils.py:15-70`).

