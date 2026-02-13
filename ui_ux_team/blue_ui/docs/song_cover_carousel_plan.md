# Song Cover Carousel Plan

## Goal
Create a reusable song-cover carousel component for Blue UI, prepared to replace current `build_cover_images` later.

## Requirements
1. Load cover images from:
- `ui_ux_team/assets/song_covers_temp/`
2. Pick/display covers with randomized order.
3. Display template:
- `[prev][current][next]`
4. Clicking prev/next cover should trigger the same logical action as transport prev/next controls (shared signal path).
5. Prev/next side covers should have a fade effect.
6. Provide standalone preview with:
- carousel
- full list of all covers

## Component API
- Class: `SongCoverCarousel`
- Signals:
  - `prev_requested`
  - `next_requested`
  - `current_changed(str)`  # current cover path
- Methods:
  - `step_prev()`
  - `step_next()`
  - `cover_paths() -> list[str]`

## Preview Behavior
- Show carousel in `[prev][current][next]` layout.
- Show all cover filenames in a list view.
- Prev/next transport-like buttons invoke the same `step_prev/step_next` handlers as side-cover clicks.

## Notes
- Keep this component isolated so `MainUI` can swap from placeholder covers to this widget later.
- Use `ImageButton` to preserve consistent hover/click behavior.
