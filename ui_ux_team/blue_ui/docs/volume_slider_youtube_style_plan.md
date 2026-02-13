# Volume Slider Modernization Plan (YouTube-Style Integrated Control)

## Goal
Replace the current popup-first volume UX with an integrated control that feels like YouTube desktop: speaker icon + inline horizontal slider reveal, smooth interaction, minimal visual noise.

## Current State
- `VolumeButton` + `VolumePopup` live in `ui_ux_team/blue_ui/widgets/volume.py`.
- Main integration is in `ui_ux_team/blue_ui/views/main_window.py` (`on_volume_start`, `on_volume_move`, `on_volume_end`).
- UX is currently vertical popup anchored above the icon.

## Target UX (YouTube-like)
1. Default compact state:
- Show only speaker icon near transport controls.
- Slider is collapsed (width 0 or hidden).

2. Expanded interaction state:
- On hover over volume zone, reveal a horizontal slider to the left of icon.
- Keep open while pointer is over icon/slider area.
- Optional short delay close (150-250ms) when leaving area.

3. Volume behavior:
- Drag on slider updates volume continuously.
- Mouse wheel on icon adjusts volume in small steps.
- Click icon toggles mute/unmute.
- Keep last non-zero volume for unmute restore.

4. Visual behavior:
- Filled track indicates current level.
- Muted icon when volume is 0 or muted.
- Subtle animation for slider reveal/hide (120-180ms).

## UI Component Design
Create a new composite widget in `ui_ux_team/blue_ui/widgets/volume.py`:
- `IntegratedVolumeControl(QWidget)`
  - contains:
    - `QLabel/QToolButton` icon hit target
    - `QSlider(Qt.Horizontal)`
  - public signal:
    - `volume_changed(float)`
    - `mute_toggled(bool)`
  - public API:
    - `set_volume(float)`
    - `volume() -> float`
    - `set_muted(bool)`
    - `is_muted() -> bool`

Keep backward compatibility temporarily:
- Keep `VolumeButton`/`VolumePopup` for one transition cycle.
- Switch `MainUI` to use `IntegratedVolumeControl`.

## Styling Direction
- Container:
  - rounded pill, dark neutral background, subtle border.
- Slider:
  - thin track (4-6px), brighter filled segment, soft handle.
- Icon:
  - monochrome white/gray set with mute/low/high states.
- Motion:
  - animate slider width or container max-width.
  - no bounce; use ease-out.

## Image/Icon Plan
Replace single static icon with 4 state assets:
- `volume_muted.png`
- `volume_low.png`
- `volume_medium.png`
- `volume_high.png`

Asset location:
- `ui_ux_team/prototype_r/assets/` (current runtime asset base)

Image style ideas:
1. Line icon set (recommended):
- 2px stroke, rounded joins, minimal glyph style.
- Best fit for modern dark transport bar.

2. Rounded filled glyph set:
- Slightly bolder, better visibility at small size.

3. Micro-animated sprite sheet (optional later):
- For subtle pulse on volume change (not in first pass).

Fallback plan:
- If new icons are not ready, use current `volume_button.png` and switch only slider UX first.

## Implementation Plan
1. Add integrated widget:
- Implement `IntegratedVolumeControl` in `widgets/volume.py`.
- Include hover region handling and reveal animation.

2. Main UI integration:
- Replace `VolumeButton` usage in `build_main_bottom_panel`.
- Remove popup event handlers from main view path:
  - `on_volume_start`, `on_volume_move`, `on_volume_end`.
- Connect `IntegratedVolumeControl.volume_changed` to existing `set_volume`.

3. Mute logic:
- Add `_muted` and `_last_nonzero_volume` in integrated widget.
- Map icon state by effective volume:
  - 0 -> muted
  - (0, 0.33] -> low
  - (0.33, 0.66] -> medium
  - (0.66, 1.0] -> high

4. Keyboard and wheel polish:
- Wheel over icon/slider adjusts by 2-5%.
- Optional keyboard left/right when slider focused.

5. Preview-only workflow:
- Update `ui_ux_team/blue_ui/previews/preview_volume.py` to host only integrated control.
- Add state labels for mute/volume for rapid tuning.

6. Cleanup:
- Deprecate old `VolumePopup` flow in code comments.
- Remove old volume handlers after validation.

## Acceptance Criteria
- No popup window is used for normal volume interaction.
- Slider reveal/hide feels smooth and deterministic.
- Mute toggle restores previous level correctly.
- Volume control remains usable on both desktop mouse and trackpad.
- Preview script validates full interaction without launching full app.

## Risks and Mitigation
- Risk: hover jitter closes slider too aggressively.
  - Mitigation: close delay timer + shared hover container.

- Risk: icon state drift vs actual player volume.
  - Mitigation: centralize state updates in `set_volume` and `set_muted`.

- Risk: asset mismatch/absence in packaged build.
  - Mitigation: keep fallback to existing icon and ensure build `datas` includes assets directory.

## Nice-to-Have Follow-ups
- Add tiny tooltip percentage while dragging.
- Add smooth audio fade when muting/unmuting.
- Add user setting for default startup volume in managed memory.
