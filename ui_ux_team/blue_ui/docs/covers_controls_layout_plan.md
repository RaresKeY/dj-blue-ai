# Covers and Controls Layout Plan

## Goals
- Center the song cover carousel in its area.
- Let the cover area resize within explicit min/max bounds using PySide6 layout constraints.
- Keep the existing visual size ratio between side and center covers.
- Add rounded corners to covers.
- Make middle transport controls live in a fixed-width box and align to the top of that box.

## Implementation Steps
1. Cover area constraints
- Update `build_cover_images` to use `QSizePolicy.Expanding` with min/max heights.
- Keep container transparent and centered in main panel.

2. Carousel sizing and centering
- Keep side:center ratio at `2:3`.
- Recompute sizes on resize so covers become as large as possible within available space.
- Center the row both horizontally and vertically.

3. Rounded corners
- Add optional corner radius support in `ImageButton` paint path clipping.
- Apply dynamic corner radius to side and center covers in `SongCoverCarousel`.

4. Controls layout constraints
- Set transport controls container to fixed width.
- Align controls layout and buttons to top within the controls box.

## Validation
- Run `.venv/bin/python -m py_compile` on touched files.
- Manual visual check in preview/main app for:
  - cover centering,
  - preserved side:center ratio,
  - rounded corners,
  - fixed-width top-aligned controls.

## Status
- Implemented in code.
