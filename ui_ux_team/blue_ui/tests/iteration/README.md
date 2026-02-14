# Blue UI Iteration Scaffolds

This folder stores persistent visual scaffolds for layout iteration.

Purpose:
- isolate UI geometry work before touching production widgets
- keep reusable reference components when context resets
- enable fast screenshot-based alignment checks

## Current Scaffold

Component:
- `ui_ux_team/blue_ui/tests/iteration/dev/cover_segment_layout_boxes.py`
- class: `CoverSegmentLayoutBoxesTestComponent`

Preview:
- `ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_layout_boxes.py`
- class: `CoverSegmentLayoutBoxesPreview`

Run:
```bash
python3 ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_layout_boxes.py
```

or:
```bash
python3 ui_ux_team/blue_ui/previews/run_preview.py iter_cover_layout
```

## Snapshot Workflow

Use the helper script:
```bash
python3 ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_cover_segment_layout_boxes \
  --class-name CoverSegmentLayoutBoxesPreview
```

Capture specific scaffold region by object name:
```bash
python3 ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_cover_segment_layout_boxes \
  --class-name CoverSegmentLayoutBoxesPreview \
  --object-name CURRENT_COLUMN_STRIP
```

## Object Name Map

- `COVER_SEGMENT_ROOT`
- `COVER_COLUMNS_ROW`
- `PREV_COLUMN_STRIP`
- `CURRENT_COLUMN_STRIP`
- `NEXT_COLUMN_STRIP`
- `PREV_COVER_SLOT`
- `CURRENT_COVER_SLOT`
- `NEXT_COVER_SLOT`
- `PREV_TITLE_SLOT`
- `CURRENT_TITLE_SLOT`
- `NEXT_TITLE_SLOT`
