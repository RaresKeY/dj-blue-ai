# DJ Blue UI Theme System

## 1. Theme Intent
This theme defines a coherent visual language for `ui_ux_team/blue_ui`:
- dark, high-contrast canvas for audio/chat focus
- electric blue primary actions
- magenta accent for emotional/music emphasis
- consistent component surfaces, borders, and typography

## 2. Source Palette
Based on `ui_ux_team/design_docs/palette.txt`.

### Core Tokens
- `PRIMARY`: `#1E90FF`
- `ACCENT`: `#FF69B4`
- `BACKGROUND`: `#0A0A12`
- `TEXT`: `#E0E6ED`
- `SECONDARY`: `#6C63FF`

### Supporting Tokens
- `TEXT_MUTED`: `#A8B3C8`
- `BG_INPUT`: `#111624`
- `BORDER_SUBTLE`: `#2A3550`
- `SURFACE_1`: `#0D0F18`
- `SURFACE_2`: `#0E101A`
- `SURFACE_3`: `#151A28`

## 3. Component Color Mapping

### App Shell
- Main background: `BACKGROUND`
- Sidebar background: deep-indigo variant of background (`#1A0F2A`)
- Bottom panel: `SURFACE_1`
- Cover area: `SURFACE_2`
- Timeline strip: `SURFACE_3`

### Buttons and Controls
- Primary interactive highlights: `PRIMARY`
- Emphasis/active media accent: `ACCENT`
- Neutral icon foreground: `TEXT`
- Disabled icon/text: `TEXT_MUTED` with lower alpha

### Text Inputs
- Input background: `BG_INPUT`
- Border: `BORDER_SUBTLE`
- Focus border: `PRIMARY`
- Body text: `TEXT`
- Placeholder/subtle text: `TEXT_MUTED`

### Popups and Overlays
- Popup background: `SURFACE_1`/`SURFACE_2`
- Popup border: `BORDER_SUBTLE`
- Toast background: `SURFACE_2`
- Toast border/accent line: `SECONDARY` or `PRIMARY`

### Volume Control
- Container: `SURFACE_1`
- Slider track base: `#111723`
- Slider fill: `PRIMARY`
- Handle: light neutral with `PRIMARY` border on hover
- Volume icon states: PNG assets in `ui_ux_team/assets`

## 4. Typography
- Base family: `Inter, Segoe UI, Ubuntu, sans-serif`
- Body size: `14-15px`
- Section/title size: `18-20px`
- Weights:
  - regular content: `400-500`
  - actionable labels: `600`
  - headings: `700`

## 5. Interaction States
- Hover:
  - subtle brighten (`+5%`) or border tint toward `PRIMARY`
- Active/Pressed:
  - stronger border/fill shift toward `PRIMARY` or `ACCENT`
- Focus:
  - always visible ring/border using `PRIMARY`
- Disabled:
  - reduce contrast + alpha, keep readable against dark backgrounds

## 6. Spacing, Radius, Elevation
- Radius scale:
  - small controls: `8px`
  - cards/panels: `10-14px`
  - floating popups: `14-16px`
- Spacing baseline: `4px` unit system (`4, 8, 12, 16, 24`)
- Borders:
  - standard: `1px solid BORDER_SUBTLE`
- Shadows:
  - subtle dark shadows for floating elements only

## 7. Accessibility Targets
- Normal text contrast target: `>= 4.5:1`
- Large text contrast target: `>= 3:1`
- Focus visibility must be explicit on keyboard navigation
- Do not rely on color alone for critical status changes

## 8. Asset Rules
- Canonical asset path: `ui_ux_team/assets`
- Preferred icon formats:
  - PNG for current runtime compatibility
  - SVG allowed for source/versioned design assets
- Naming convention:
  - `component_state_variant.ext` (e.g., `volume_high.png`)

## 9. Code Ownership and Files
- Theme tokens: `ui_ux_team/blue_ui/theme/tokens.py`
- Reusable style helpers: `ui_ux_team/blue_ui/theme/styles.py`
- Main shell color usage: `ui_ux_team/blue_ui/views/main_window.py`
- Widget local styling:
  - `ui_ux_team/blue_ui/widgets/volume.py`
  - `ui_ux_team/blue_ui/widgets/text_boxes.py`
  - `ui_ux_team/blue_ui/views/settings_popup.py`
  - `ui_ux_team/blue_ui/widgets/toast.py`

## 10. Theming Guidelines for New Components
- Consume tokens from `theme/tokens.py`; do not hardcode new palette values.
- Prefer helper style functions in `theme/styles.py` for shared patterns.
- Use `PRIMARY` for interaction and `ACCENT` for semantic emphasis only.
- Keep surfaces within the dark family (`BACKGROUND`, `SURFACE_1/2/3`) to avoid visual drift.

## 11. Migration Checklist
- Replace hardcoded hex colors with tokens where practical.
- Validate focus and hover states in keyboard + mouse flows.
- Confirm all popups and overlays match border/radius system.
- Verify icons and assets resolve from `ui_ux_team/assets`.
- Preview in:
  - `ui_ux_team/blue_ui/previews/preview_main_window.py`
  - `ui_ux_team/blue_ui/previews/preview_widgets.py`
  - `ui_ux_team/blue_ui/previews/preview_volume.py`
