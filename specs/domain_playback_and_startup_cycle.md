# Domain: Playback & Start Cycle

## Scope
- Playback controls, music source validation, and startup gating in the main window.
- Main implementation files:
- `ui_ux_team/blue_ui/views/main_window.py`
- `architects/helpers/miniaudio_player.py`
- `mood_readers/data/mood_playlists_organized.json`

## Playback Control Rules
- Playback uses `MiniaudioPlayer` via `default_player_factory` wiring in app services.
- `basic_music_play(...)` resolves a concrete path before starting playback; unresolved files fall back to play-icon reset and no-op.
- Start/pause/resume/seek interactions are coordinated by main window transport actions and timeline callbacks.
- Timeline synchronization uses a temporary seek lock window to prevent immediate UI feedback loops during user-initiated seeks.

## Music Folder Behavior
- Music folder value is loaded from normalized settings key `music_folder`.
- If configured folder does not exist, runtime falls back to `default_music_folder()` and persists that value.
- Audio existence checks are extension-based (`.wav`, `.mp3`, `.flac`, `.ogg`, `.m4a`, `.aac`).
- Missing or empty music folders surface startup prompts and disable full start-cycle readiness.

## Start-Cycle Preflight Contract
- Startup preflight evaluates three conditions:
- API key available.
- Music collection contains at least one supported audio file.
- Music collection filenames fully cover required filenames referenced by `mood_playlists_organized.json`.
- If any condition fails, preflight dialog explains unmet requirements and blocks cycle start.

## Playlist Match Semantics
- Required playlist filenames are derived from mood map values by normalizing entries and extracting basename.
- Runtime music collection filenames are compared against the derived required set.
- Missing filenames are surfaced in preflight detail text with sample listing.

## Key Invariants
- Playback actions are defensive against missing/unresolvable files.
- Start cycle requires API readiness plus both music non-empty and playlist coverage checks.
- Active behavior comes from Blue UI runtime modules, not legacy prototype scripts.
