# Blue UI Theme Templates

Default saved theme key: `bluebird_soft`

## Available Themes
- `bluebird_soft`: Current baseline soft dark blue/purple with pink accent.
- `pastel_dusk`: Lighter blue-lavender shift, soft panel contrast.
- `lavender_mist`: Slightly warmer lavender with muted blue backgrounds.
- `midnight_pastel`: Deeper but softer violet/indigo blend.
- `aurora_pastel`: Airier cyan/lilac blend with low-contrast surfaces.
- `sky_rose`: Soft sky-blue + rose accent variant.
- `dark_theme`: VS Code-inspired dark neutral theme with orange accent.
- `light_theme`: VS Code-inspired light theme with orange accent.

## Theme Chooser Component
- File: `ui_ux_team/blue_ui/widgets/theme_chooser.py`
- Class: `ThemeChooserMenu`
- Emits: `theme_selected(str)`
- Runtime apply API: `ui_ux_team/blue_ui/theme/manager.py`
  - `set_theme(theme_key)`
  - `list_themes()`

## Preview
- Run one-shot preview:
  - `python ui_ux_team/blue_ui/previews/preview_theme_chooser.py`
- Run with auto-restart:
  - `python ui_ux_team/blue_ui/previews/run_preview.py theme`
