# Proper Visual Audit Report

- **Audit Date**: 2026-02-18
- **Snapshot Run**: `20260218_040122` (Transparent RGBA)
- **Scope**: Full Theme Set (8) across Core UI and all Settings Tabs.

---

## 📸 Executive Summary
The visual audit reveals that while the core layout is stable across all themes, there are systemic issues with **transparency handling in light mode** and **token-specific hierarchy** in certain pastel themes. The "standalone settings" transition was successful, but requires CSS refinement for scroll areas.

---

## 🎨 Theme-by-Theme Analysis

| Theme | Status | Critical Observations |
|:---|:---|:---|
| `bluebird_soft` | ✅ Stable | Primary dark reference. Excellent contrast. |
| `light_theme` | 🚩 Issues | **Major ghosting** in User Profile. Avatar and cards use hardcoded white-alpha, becoming invisible against white BG. |
| `midnight_pastel` | ⚠️ Muddy | Background and sidebar are too close in value. The "Search" bar in transcripts feels slightly disconnected. |
| `sky_rose` | ✅ Good | The accent pink pop is effective. Text legibility is high. |
| `aurora_pastel` | ✅ Good | Background depth is well-maintained. |
| `lavender_mist`| ⚠️ Vibrant | Sidebar is very high-saturation compared to the main panel. |

---

## 🧩 Component Specific Findings

### 1. Main Window (MainWindowView)
- **Alignment**: The "BlueBird" icon in the bottom-left is slightly inconsistent in its vertical alignment across some themes.
- **Carousel**: Song covers render correctly, but the "dummy" text labels are sometimes cut off in narrower windows.

### 2. User Profile (ProfileWindowView)
- **Transparency**: Hardcoded `rgba(255, 255, 255, 0.04)` causes failures in `light_theme`. 
- **Icons**: The user icon tint doesn't always match the `ACCENT` token.

### 3. Settings (SettingsPopup)
- **QScrollArea**: The "gray border" issue is visible in snapshots. The viewport needs a `background: transparent` or `match parent` rule.
- **Tab Selection**: In `light_theme`, the selected tab (orange) is clear, but the hover state is too subtle.

### 4. BlueBird Chat (BlueBirdChatView)
- **Markdown**: rendering is perfect, but bubble padding feels tight on longer messages.

---

## 🛠️ Detailed Fix Plan

### Phase 1: High Priority (Theme Legibility)
- **[ ] Fix Profile Transparency**: Update `ProfileWindowView.refresh_theme` to use `TEXT_PRIMARY` with low alpha instead of hardcoded white.
- **[ ] Sharpen `midnight_pastel`**: Adjust `COLOR_SIDEBAR` in `palettes.py` to be ~10% darker than `COLOR_BG_MAIN`.

### Phase 2: Widget Polish
- **[ ] Global ScrollArea Fix**: Add a global CSS rule in `theme/manager.py` or individual views to force `QScrollArea { border: none; background: transparent; }`.
- **[ ] Button Tints**: Ensure `MainWindowView` sidebar buttons use the `PRIMARY` token for their icon color instead of hardcoded paths where possible.

### Phase 3: Final Verification
- **[ ] Re-run Gallery**: Execute `snap_gallery.py` again and verify the `light_theme` profile card visibility.

---

## 📝 Documented Origin Map
*Reference `GALLERY_MAP.md` for full component-to-source mapping.*
