# Timeline Visual Consistency Plan

## Objective
Keep timeline visuals thematically consistent across all Blue UI themes while preserving seek behavior.

## Design Rules
1. Theme-first colors:
- No hardcoded timeline colors in widget logic.
- Use timeline-specific theme tokens (`TIMELINE_*`) for text, progress, remaining, preview, and handle.

2. Stable layer order:
- `preview_fill` at lowest layer.
- `hover_marker` above preview.
- `actual_handle` always top-most.

3. Interaction clarity:
- Handle only visible on hover/drag.
- Hover preview must not move real playback position.
- Drag remains authoritative for seek.

## Implementation Notes
1. Widget architecture:
- Keep native `QSlider` for value/seek mechanics.
- Render custom visual layers (`preview_fill`, `hover_marker`, `actual_handle`) as overlays.

2. Theme support:
- Ensure every palette provides `TIMELINE_PREVIEW` to avoid stale token carry-over after theme switches.

3. Visual tuning:
- Thin baseline groove with hover expansion.
- Subtle preview alpha to avoid fighting with actual progress fill.
- Marker color derived from theme accent/hover handle tone.

## QA Checklist
1. Switch through all themes and verify timeline readability.
2. Verify no z-fighting between preview, marker, and handle.
3. Confirm hover preview appears/disappears cleanly.
4. Confirm handle does not move on hover-only movement.
5. Confirm dragging updates label and seek target correctly.
