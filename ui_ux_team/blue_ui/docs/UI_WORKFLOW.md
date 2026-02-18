# Blue UI Iteration & Visual Audit Workflow

- **Status**: Production Ready
- **Last Updated**: 2026-02-18

This document describes the standardized workflow for creating, iterating on, and visually validating Blue UI components across multiple themes.

---

## Phase 1: Scaffolding
When creating a new UI feature or widget, start in the "iteration sandbox" to avoid polluting the main application logic.

### 1. Generate Boilerplate
Run the iteration tool to create a test component and a preview wrapper:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py scaffold <component_name>
```
- **Component**: `ui_ux_team/blue_ui/tests/iteration/dev/<name>.py`
- **Preview**: `ui_ux_team/blue_ui/previews/iteration/preview_<name>.py`

---

## Phase 2: Development & Live Preview
Build your component logic in the generated test file. Use the auto-reload runner to see changes in real-time.

### 1. Start Auto-Reload Runner
```bash
# Watch the specific preview file
.venv/bin/python ui_ux_team/blue_ui/previews/run_preview.py iteration/preview_<name>
```
The preview will restart automatically every time you save your code.

---

## Phase 3: Visual Validation (Snapshots)
Once the layout is stable, verify it across different themes using the snapshot tool.

### 1. Single Component Snapshot
Capture a specific widget in a specific theme:
```bash
.venv/bin/python ui_ux_team/blue_ui/previews/ui_iterate.py snap 
  --module ui_ux_team.blue_ui.previews.iteration.preview_<name> 
  --theme bluebird_soft 
  --width 800 --height 600 
  --offscreen
```

### 2. Automated Theme Gallery (The Audit)
To verify the entire UI suite across all 8 themes, use the batch gallery generator. This creates a vertical "strip" of the core windows for easy comparison.

```bash
# Run for ALL themes
.venv/bin/python ui_ux_team/blue_ui/previews/snap_gallery.py --subfolder audit_v1

# Run for a specific theme
.venv/bin/python ui_ux_team/blue_ui/previews/snap_gallery.py --theme light_theme
```
- **Output**: `ui_ux_team/blue_ui/previews/.snapshots/<subfolder>/gallery_<theme>.png`

---

## Technical Requirements for Previews
For a preview to be compatible with the **Snapshot** and **Gallery** tools, it must follow these rules:

1. **Class-Based**: The preview file must define a `QWidget` subclass (e.g., `class MyComponentPreview(QWidget):`).
2. **Naming Convention**: The class should ideally contain the word `Preview`.
3. **Standalone Initialization**: The `__init__` method should handle its own setup (adding segments, dummy data, etc.) so it looks complete upon instantiation.

**Example Pattern:**
```python
class MyFeaturePreview(MyFeatureView):
    def __init__(self):
        super().__init__()
        self.load_dummy_data() # Ensure visual completeness
        self.resize(600, 400)
```

---

## Pro-Tips
- **Theme Overrides**: Use the environment variable `DJ_BLUE_THEME_OVERRIDE=<theme_key>` to force a theme without changing your `app_config.json`.
- **Headless Captures**: Always use the `--offscreen` flag in CI or batch runs to prevent windows from stealing focus or requiring a display server.
- **Pillow Dependency**: Ensure `Pillow` is installed in your venv for the gallery stitching logic to work.
