# Blue UI Iteration Scaffolds

This folder stores persistent visual scaffolds for layout iteration.

Purpose:
- isolate UI geometry work before touching production widgets
- keep reusable reference components when context resets
- enable fast screenshot-based alignment checks

## Current Scaffolds

Component:
- `ui_ux_team/blue_ui/tests/iteration/dev/cover_segment_layout_boxes.py`
- class: `CoverSegmentLayoutBoxesTestComponent`
- `ui_ux_team/blue_ui/tests/iteration/dev/cover_segment_vertical_slips_layout.py`
- class: `CoverSegmentVerticalSlipsLayoutTestComponent`

Preview:
- `ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_layout_boxes.py`
- class: `CoverSegmentLayoutBoxesPreview`
- `ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_vertical_slips_layout.py`
- class: `CoverSegmentVerticalSlipsLayoutPreview`

Run:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_layout_boxes.py
```

or:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_vertical_slips_layout.py
```

or:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/run_preview.py iter_cover_vertical_slips
```

## Snapshot Workflow

Use the helper script:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_cover_segment_layout_boxes \
  --class-name CoverSegmentLayoutBoxesPreview
```

Capture specific scaffold region by object name:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_cover_segment_layout_boxes \
  --class-name CoverSegmentLayoutBoxesPreview \
  --object-name CURRENT_COLUMN_STRIP
```

Vertical slips scaffold snapshot:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_cover_segment_vertical_slips_layout \
  --class-name CoverSegmentVerticalSlipsLayoutPreview \
  --offscreen
```

## Object Name Map

- `COVER_SEGMENT_ROOT`
- `PREV_COLUMN_STRIP`
- `CURRENT_COLUMN_STRIP`
- `NEXT_COLUMN_STRIP`
- `PREV_COLUMN_STRIP_COVER_TRACK`
- `CURRENT_COLUMN_STRIP_COVER_TRACK`
- `NEXT_COLUMN_STRIP_COVER_TRACK`
- `PREV_COVER_SLOT`
- `CURRENT_COVER_SLOT`
- `NEXT_COVER_SLOT`
- `PREV_TITLE_SLOT`
- `CURRENT_TITLE_SLOT`
- `NEXT_TITLE_SLOT`
