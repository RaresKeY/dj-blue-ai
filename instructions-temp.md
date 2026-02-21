## UI Iteration Protocol (Blue UI)

Use this workflow for any layout/alignment-heavy UI change before integrating into core views.

1. Scaffold a test component + preview:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py scaffold <component_name>
```

2. Run the preview and iterate quickly:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/iteration/preview_<component_name>.py
```

3. Capture a deterministic screenshot for visual review:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_<component_name> \
  --class-name <ComponentNamePreview>
```

4. If needed, capture a specific child widget by `objectName`:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_<component_name> \
  --class-name <ComponentNamePreview> \
  --object-name <WidgetObjectName>
```

5. Keep iterating until screenshot confirms:
- horizontal alignment is correct
- vertical spacing is intentional
- slot widths/heights are explicit and stable
- no clipping/teleport/jump behavior on hover/animation
- screenshot is visually reviewed (for coding agents: open the PNG with `view_image`)

## Persistent Iteration Paths

Default scaffold targets are permanent reference folders:
- components: `ui_ux_team/blue_ui/tests/iteration/dev/`
- previews: `ui_ux_team/blue_ui/previews/iteration/`

Current permanent scaffolds:
- component: `ui_ux_team/blue_ui/tests/iteration/dev/cover_segment_layout_boxes.py`
- preview: `ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_layout_boxes.py`
- component: `ui_ux_team/blue_ui/tests/iteration/dev/cover_segment_vertical_slips_layout.py`
- preview: `ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_vertical_slips_layout.py`

## Cover Segment Alignment Contract

Use `cover_segment_vertical_slips_layout` when validating cover/title geometry.

Required structure:
- exactly 3 vertical strips: `PREV_COLUMN_STRIP`, `CURRENT_COLUMN_STRIP`, `NEXT_COLUMN_STRIP`
- each strip contains `COVER_SLOT` on top and `TITLE_SLOT` below
- side covers are vertically centered against current cover using a shared cover-track height
- title slots must be present but must not influence cover vertical centering math
- test scaffold is color-only (no in-box text labels) for clean visual alignment checks

Quick run:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/iteration/preview_cover_segment_vertical_slips_layout.py
```

Auto-reload run:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/run_preview.py iter_cover_vertical_slips
```

Quick snapshot:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py snap \
  --module ui_ux_team.blue_ui.previews.iteration.preview_cover_segment_vertical_slips_layout \
  --class-name CoverSegmentVerticalSlipsLayoutPreview \
  --offscreen
```

## UI Helper Script

File: `ui_ux_team/blue_ui/previews/ui_iterate.py`

Interpreter:
- always run with `.venv/bin/python` to ensure Qt/PySide dependencies are available

Commands:
- `scaffold`: creates boilerplate test component + preview
- `snap`: renders a QWidget and writes a screenshot to `ui_ux_team/blue_ui/previews/.snapshots/`

Useful options:
- `--delay-ms 350` to wait longer before capture
- `--width 900 --height 560` to force capture size
- `--offscreen` for headless capture
- `--no-theme` to skip theme application

## Integration Rule

Only move changes into `views/` or production widgets after:
- test preview behavior is correct
- screenshot evidence is checked
- size/alignment rules are explicit in code

## Tagging Guide

For any release/version tag operation, use:
- `architects/design_docs/TAGGING_GUIDE.md`

This is the canonical tagging policy for:
- SemVer format
- annotated vs lightweight tag usage
- release tagging workflow
- tag correction/deletion process
- CI/CD trigger behavior (`v*` tags)
