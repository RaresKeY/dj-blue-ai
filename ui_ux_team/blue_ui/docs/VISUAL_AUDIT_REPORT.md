# Visual Audit Report & Fix Plan

- **Audit Date**: 2026-02-18
- **Snapshot Run**: `20260218_040122`
- **Scope**: All 8 themes across core windows and settings tabs.

---

## 🚩 Findings: Visual Inconsistencies

### 1. User Profile: Theme Adaptation Failure
- **Issue**: `ProfileWindowView` uses hardcoded `rgba(255, 255, 255, 0.04)` for avatar and card backgrounds.
- **Result**: In `light_theme`, these elements are invisible or "ghosted" against the bright background.
- **Impact**: Medium (Legibility).

### 2. Main Window: Sidebar vs. Main Content Muddiness
- **Issue**: In `midnight_pastel`, the `COLOR_SIDEBAR` and `COLOR_BG_MAIN` tokens are very similar.
- **Result**: Lack of clear spatial hierarchy; the app looks "flat" and confusing.
- **Impact**: Low (Aesthetic).

### 3. Settings: ScrollArea Backgrounds
- **Issue**: Some settings tabs show a default gray background in the `QScrollArea` before the theme-specific `BG_INPUT` fully covers it during render.
- **Result**: Flash of unstyled content or gray borders in snapshots.
- **Impact**: Low (Polish).

### 4. Transcript Window: Timeline Sync Logic
- **Issue**: The timeline in `MainUI` occasionally renders at 0.0% in snapshots even when dummy duration is set.
- **Result**: Inconsistent "empty" state in galleries.
- **Impact**: Low (Audit Accuracy).

---

## 🛠️ Fix Plan

### Phase 1: High-Contrast Tokens (Immediate)
- [ ] **Profile Window**: Replace hardcoded white alpha with a dynamic `_with_alpha` helper that uses `TEXT_PRIMARY` as the base color. This ensures the card is dark in light mode and light in dark mode.
- [ ] **Palettes**: Sharpen the difference between `COLOR_SIDEBAR` and `COLOR_BG_MAIN` in `midnight_pastel`.

### Phase 2: Widget Polish
- [ ] **SettingsPopup**: Update `refresh_theme` to force the `viewport()` background of `QScrollArea` to be transparent or match `stack_bg`.
- [ ] **MainWindow**: Ensure `PlaybackTimeline` receives a final sync signal before the snapshot capture delay expires.

### Phase 3: Verification
- [ ] Re-run `snap_gallery.py` and compare `gallery_light_theme.png` and `gallery_midnight_pastel.png`.

---

## Modular Progress Tracker
- [ ] Profile contrast fix
- [ ] Midnight Pastel hierarchy adjustment
- [ ] ScrollArea transparency fix
- [ ] Snapshot verification
