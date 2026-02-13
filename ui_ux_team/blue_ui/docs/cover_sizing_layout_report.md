# Cover Carousel Sizing and Layout Report

## Scope
- Investigate cover clipping/sizing/alignment instability.
- Compare current implementation against working Qt layout patterns.
- Apply a durable fix in `ui_ux_team/blue_ui/widgets/song_cover_carousel.py`.

## Online Reference Baseline (Qt/PySide)
1. Qt Layout Management
- Layouts should control widget geometry and adapt to available space.
- Ref: https://doc.qt.io/qt-6/layout.html

2. QSizePolicy and size hints
- `QSizePolicy`, `sizeHint()`, and `minimumSizeHint()` are the intended contract for responsive sizing under layouts.
- Ref: https://doc.qt.io/qt-6/qsizepolicy.html
- Ref: https://doc.qt.io/qt-6/qwidget.html#sizeHint-prop

3. QBoxLayout spacing/stretch/alignment behavior
- Spacing and alignment must be accounted for in explicit geometry math.
- Ref: https://doc.qt.io/qt-6/qboxlayout.html

4. Qt official layout example (working pattern)
- Example demonstrates layout-driven resize behavior with hints and stretch instead of hard pixel assumptions.
- Ref: https://doc.qt.io/qt-6/qtwidgets-layouts-basiclayouts-example.html

## Findings in Previous Carousel Code
1. Artificial usable-space floors caused overflow risk
- Code used `max(260, width - spacing*2)` and `max(170, height)`.
- At small window sizes this overestimated available space and could compute cover sizes larger than actual geometry.

2. No size-hint contract for the carousel widget
- Missing `sizeHint()`/`minimumSizeHint()` reduced layout predictability.

3. Hover scaling pressure at tight sizes
- Cover buttons scale on hover.
- Without explicit internal breathing room, zoom could visually look clipped.

## Implemented Fix
1. Removed hard geometry floors
- Replaced with true available-space bounds:
  - `usable_w = max(1, self.width() - spacing*2)`
  - `usable_h = max(1, self.height())`

2. Added proper size hints
- Implemented:
  - `sizeHint()` based on preferred center size and side ratio.
  - `minimumSizeHint()` based on minimum center size and side ratio.
- This gives parent layouts stable constraints and expected scaling behavior.

3. Preserved ratio while bounding to real geometry
- Side/center ratio remains `2/3`.
- Center size now computed from `min(preferred, max_center_by_w, max_center_by_h)` so it cannot exceed real box limits.

4. Improved hover visual stability
- Reduced hover scale to `1.06` for carousel covers.
- Added dynamic internal margins proportional to cover size to avoid clipped look during hover.

5. Kept center alignment
- Row/root alignment stays centered, so the carousel remains in the middle of its bounding box during resize.

## Files Changed
- `ui_ux_team/blue_ui/widgets/song_cover_carousel.py`

## Expected Outcome
- Covers stay large in normal sizes.
- Covers shrink correctly when the window is reduced.
- Middle cover no longer gets cut off due to overestimated geometry.
- Alignment remains centered and responsive.
