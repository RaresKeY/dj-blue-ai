# Timeline Component Plan

## Goal
Build a reusable YouTube-style timeline bar for `blue_ui` that:
- shows playback progress
- shows elapsed/total time
- supports click/drag seek
- works in both preview and main player UI

## Scope
1. Add `PlaybackTimeline` widget under `ui_ux_team/blue_ui/widgets/`.
2. Add preview file under `ui_ux_team/blue_ui/previews/`.
3. Integrate timeline into `MainUI` under the cover area.
4. Extend `MiniaudioPlayer` with duration/progress/seek APIs.
5. Sync timeline with player using a timer.

## API Design
- `set_duration(seconds: float)`
- `set_position(seconds: float)`
- `set_playing(is_playing: bool)`
- `seek_requested = Signal(float)`  # target seconds

## Integration Notes
- Timeline is always transparent background.
- Mouse interaction emits `seek_requested`; main window maps this to player seek.
- If seek is unavailable for a format/runtime, keep UI responsive and continue normal playback.

## Validation
- Run timeline preview.
- Run main window and verify:
  - play updates progress
  - pause freezes progress
  - click/drag seeks
  - theme changes do not break timeline visibility
