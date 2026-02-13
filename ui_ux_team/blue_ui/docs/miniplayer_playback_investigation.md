# Miniplayer Playback Investigation and Fix Report

## Scope
Investigated `MiniaudioPlayer` + `MainUI` playback integration for startup/play/pause path failures and UI state drift.

## Files Reviewed
- `architects/helpers/miniaudio_player.py`
- `ui_ux_team/blue_ui/views/main_window.py`
- `ui_ux_team/blue_ui/tests/test_button_clicks.py`

## Issues Found

0. Callback frame-size mismatch (primary runtime bug)
- `PlaybackDevice` sends requested frame counts to callback generator.
- Previous player code ignored these requests and iterated decoder with fixed default chunk size (`1024`).
- This can exceed callback max frames and break/stop playback callback flow.
- Symptom pattern:
  - console prints \"Playing ...\"\n
  - no audible output\n
  - timeline position remains static

0b. Silent `NULL` backend fallback
- miniaudio can initialize `PlaybackDevice` with backend `null` if no usable backend is found.
- If not explicitly rejected, app may report \"playing\" while producing no sound.
- This reproduces a \"playing log + static timeline + silence\" profile in device/backend failure cases.

1. Silent-start failure left UI in incorrect state
- `MainUI` set play icon to pause before start success was confirmed.
- On missing/invalid files, player object could be created but not actually playing.
- Result: play button and internal state could diverge.

2. Path resolution could return a non-existent path
- Resolver previously returned fallback probe paths even when none existed.
- Result: `MiniaudioPlayer` received invalid file paths and failed at runtime.

3. No deterministic success contract from player start
- `MiniaudioPlayer.start()` returned `None`, making upstream success detection ambiguous.

4. Recovery from failed start was weak
- After failure, `_player` could remain set in some flows.
- Subsequent clicks could hit pause/resume branches instead of clean restart.

## Fixes Implemented

0. Callback-correct stream generation
- Updated `_volume_generator` to honor `required_frames` sent by miniaudio callback.
- Uses `stream.send(required_frames)` instead of fixed-size `next(stream)` reads.
- Keeps volume scaling while guaranteeing frame-sized callback compatibility.

0b. Backend enforcement
- `MiniaudioPlayer` now requests preferred OS backends explicitly:
  - Linux: PulseAudio -> ALSA -> JACK
  - macOS: CoreAudio
  - Windows: WASAPI -> DSOUND -> WINMM
- If backend resolves to `null`, startup fails with explicit error instead of fake success.
- Playback log now includes selected backend for quick diagnosis.

1. Explicit start success/failure contract
- `MiniaudioPlayer.start()` now returns `True` on success and `False` on failure.
- Resume path also returns `True`.

2. Hardened main-window player bootstrap
- Added `_start_player(real_path)` in `MainUI`:
  - stops old player safely
  - creates new player
  - applies volume
  - starts player and validates actual playing state
  - only stores `_player` on successful start

3. Safe path resolution
- `_resolve_music_path(...)` now returns:
  - first existing probe path, or
  - first audio file in configured music folder, or
  - `None`
- Removed non-existent path fallback return.

4. UI state consistency
- On failed start/path missing, play icon is set to `play`.
- On success, icon is set to `pause`.

5. Test stabilization for transport flow
- `test_button_clicks` now creates a temporary music folder with a dummy `.wav` file and points `MainUI` to it.
- Keeps tests deterministic without relaxing runtime playback checks.

## Behavioral Outcome
- Playback starts only when a resolvable audio file exists.
- Failed starts no longer leave stale player/UI state.
- Play/pause behavior recovers cleanly from previous failures.

## Validation
- `py_compile` passed for changed playback files.
- Button click tests pass with deterministic temp music input.
