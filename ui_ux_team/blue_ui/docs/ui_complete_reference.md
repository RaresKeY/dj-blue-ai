# Blue UI Complete Technical UI Documentation

## Purpose
This document describes the current `ui_ux_team/blue_ui` interface in PySide6 terms:
- window/layer hierarchy
- layouts and widget containment
- sizing and alignment rules
- runtime behavior and signals
- functional ownership by component

It is intended as a maintenance handoff reference for developers/designers.

## Runtime Entry Points
1. App entry:
- `ui_ux_team/blue_ui/app/main.py`
- `run()` creates `QApplication`, builds `AppComposer`, shows `MainWindowView`.

2. Composition bootstrap:
- `ui_ux_team/blue_ui/app/composition.py`
- Calls `ensure_default_theme()` before creating `MainWindowView`.

3. Preview launcher:
- `ui_ux_team/blue_ui/previews/run_preview.py`
- Restarts selected preview on file changes.

## Top-Level Windows
1. Main window
- Class: `MainUI` (`MainWindowView` alias)
- File: `ui_ux_team/blue_ui/views/main_window.py`
- Base: `QWidget`
- Title: `DJ Blue UI`
- Initial size: `721x487`

2. Transcript window
- Class: `TranscriptWindowView`
- File: `ui_ux_team/blue_ui/views/transcript_window.py`
- Top-level separate window (not embedded)
- Open/close controlled from main sidebar transcript button

3. BlueBird chat window
- Class: `BlueBirdChatView`
- File: `ui_ux_team/blue_ui/views/chat_window.py`
- Separate floating window to the left of main window

4. Settings popup
- Class: `SettingsPopup`
- File: `ui_ux_team/blue_ui/views/settings_popup.py`
- Frameless popup overlay anchored within main-window bounds

5. Meet type popup
- Class: `FloatingMenu`
- File: `ui_ux_team/blue_ui/views/settings_popup.py`
- Small popup attached below meet-type button

## Main Window Layer/Layout Tree
Tree from outer to inner:

`MainUI (QWidget)`
- `root: QVBoxLayout` (`margins=0,0,0,0`)
  - `build_main_layout() -> container(QWidget)`
    - `h: QHBoxLayout` (`margins=0, spacing=0`)
      - `build_main_panel()` with stretch `4`
      - `build_sidebar()` with stretch `1`

### Main Panel (`build_main_panel`)
`main_box: QFrame` background from `theme_tokens.COLOR_BG_MAIN`
- `layout: QVBoxLayout` (`margins=0, spacing=4`)
  1. `mood_tag: QueuedMarqueeLabel`
     - label font size `20`
     - `maxHeight=30`
  2. `build_cover_images()` with stretch factor `1`
  3. `build_timeline_volume_section()` -> timeline
  4. `build_main_bottom_panel()` -> controls + volume + bird

### Sidebar (`build_sidebar`)
`sidebar: QFrame`
- Fixed width constraints:
  - `minWidth=70`
  - `maxWidth=70`
- `layout: QVBoxLayout`
  - `contentsMargins=(2,7,2,12)`
  - `spacing=10`
- Widgets top-to-bottom:
  1. transcript button `60x60`
  2. api button `50x50`
  3. info button `50x50`
  4. meet type button `50x50`
  5. stretch
  6. user button `60x60`
  7. settings button `50x50`
- All centered horizontally with `Qt.AlignHCenter`

## Cover Area and Carousel
### Cover container (`build_cover_images`)
- Wrapper: transparent `QFrame`
- `minimumHeight=220`
- `QSizePolicy(Expanding, Expanding)`
- Internal layout: `QHBoxLayout(margins=0, spacing=0)`
- Child: `SongCoverCarousel` aligned `Qt.AlignCenter`

### SongCoverCarousel widget
File: `ui_ux_team/blue_ui/widgets/song_cover_carousel.py`

Structure:
- Root `QVBoxLayout` centered
- One centered `QHBoxLayout` row with 3 `ImageButton` widgets:
  - prev cover
  - current cover
  - next cover
- Row spacing: `6`

Sizing model:
- Ratio rule: `side = 2/3 * center`
- Preferred center size: `230`
- Minimum center reference: `96` (for `minimumSizeHint`)
- Dynamic recompute on `resizeEvent`
- Computation:
  - available width = `self.width() - 2*spacing`
  - `max_center_by_w = available_w / (1 + 2*ratio)`
  - `max_center_by_h = available_h`
  - `center = min(preferred_center, max_center_by_w, max_center_by_h)`
  - lower clamp currently `56`
- Rounded corners scale with cover size
- Hover scale on covers: `1.06`
- Side fade opacity animation on content refresh (prev/next)

Behavior:
- Loads random-ordered PNG set from:
  - `ui_ux_team/assets/song_covers_temp/*.png`
- Emits:
  - `prev_requested`
  - `next_requested`
  - `current_changed(str)`
- In main window:
  - `prev_requested -> MainUI.prev_action`
  - `next_requested -> MainUI.next_action`

## Timeline Layer
### Main timeline wrapper (`build_main_timeline`)
- Transparent `QFrame`
- `QVBoxLayout(margins=0, spacing=0)`
- Child: `PlaybackTimeline`
- Fixed height in main UI: `52`

### PlaybackTimeline widget
File: `ui_ux_team/blue_ui/widgets/timeline.py`

Layout:
- Root `QVBoxLayout(margins=0, spacing=2)`
  1. Label row (`QHBoxLayout`) with elapsed/total labels
  2. Slider wrapper row (`QVBoxLayout`) with no top padding and bottom pad `4`

Key size/alignment rules:
- Slider height fixed min/max `18`
- Elapsed label gets left text margin via `setContentsMargins(8,0,0,0)`
- Timeline bar groove thickness changes by hover state:
  - idle: `5`
  - hovered: `9`

Interaction model:
- Uses custom `PreciseSeekSlider`:
  - click-to-seek by x position
  - drag emits direct value updates
  - hover ratio tracking via `hover_ratio_changed`
- Overlay layers inside slider (same parent for z-order control):
  1. preview fill (lowest)
  2. hover marker line
  3. actual handle (top)
- Handle appears only when hovered or dragging
- Seek signal:
  - `seek_requested(float seconds)` emitted on drag release when duration > 0

Main-window integration:
- `_timeline_timer` refresh interval `120ms`
- If no player, timeline uses dummy duration (`240s`) and dummy seek position
- During user seek, short lock window prevents immediate position snap-back

## Bottom Panel (Transport + Volume + Bird)
Built by `build_main_bottom_panel`.

Container:
- transparent frame
- `QVBoxLayout(contentsMargins=10,10,10,10, spacing=4)`

### Top row layout
- `QHBoxLayout(margins=0, spacing=0)`
- Symmetric stretches on both sides keep center block stable on resize
- Deterministic widget sequence in middle block:
  - left placeholder widget `180x100`
  - controls widget
  - volume slot `180x100`

#### Controls widget (`build_main_controls`)
- transparent frame
- Fixed width: `290`
- Height behavior: `maxHeight=100`; also set to fixed height `100` by caller
- SizePolicy: `Fixed, Fixed`
- Internal layout:
  - `QHBoxLayout(contentsMargins=10,0,10,10)`
  - layout alignment `AlignTop|AlignHCenter`
  - child alignment for prev/play/next: `AlignVCenter`
- Buttons:
  - prev `35x35`
  - play `80x80`
  - next `35x35`

#### Volume slot
- Slot widget fixed `180x100`
- `QHBoxLayout` with `AlignLeft|AlignTop`
- Contains `IntegratedVolumeControl` pinned left-top

### Bottom row layout
- `QHBoxLayout(margins=0, spacing=0)`
- Left: Blue Bird button (`70x70`) aligned left-bottom
- Right: stretch

## Integrated Volume Control
File: `ui_ux_team/blue_ui/widgets/volume.py`

Widget geometry contract:
- Fixed outer size (`_control_w`, `_control_h`)
- Icon is always fixed-position at left
- Slider width animates between `0` and `_expanded_slider_w` (`108`)
- Expansion direction: to the right of icon

Layout internals:
- No Qt layout for outer arrangement; manual geometry via `_layout_children()`
- `icon_button` at `(pad_x, pad_y)`
- `slider_wrap` starts immediately after icon+gap

Behavior:
- Hover enter: expand slider
- Hover leave: delayed collapse (`180ms` timer)
- Click icon: mute/unmute with last non-zero restore
- Scroll wheel: volume +/- `0.03`
- Emits:
  - `volume_changed(float)`
  - `mute_toggled(bool)`

Main integration:
- `volume_changed -> MainUI.set_volume`
- If player exists, applies volume directly to player

## Sidebar Button Functional Map
File: `ui_ux_team/blue_ui/views/main_window.py`

1. Transcript
- Opens/closes `TranscriptWindowView`.
- On open, positions transcript to the right of main window and sizes to match main height.

2. Info
- Shows mood toast (`FloatingToast`) random from mood list.

3. Meet Type
- Toggles `FloatingMenu` popup under the button.

4. Settings
- Opens `SettingsPopup` with tabs:
  - Recording Sources (`QListWidget`)
  - Theme Selection (`ThemeChooserMenu`)
  - Music Library (`QLineEdit` + `Choose folder` button)
  - Test Tab (`QListWidget`)

## Settings Popup Layout and Behavior
File: `ui_ux_team/blue_ui/views/settings_popup.py`

Container:
- Frameless popup, minimum size `560x350`
- Main structure:
  1. `PopupTitleBar` fixed height `34`
  2. content row (`QHBoxLayout`)
     - left nav `QListWidget` fixed width `190`
     - right `QStackedWidget`

Behavior:
- Selecting nav item changes stacked page index
- Popup geometry computed relative to parent window by `show_pos_size(...)`
- Uses theme tokens + orange selection accent

Title bar behavior:
- Drag support implemented via mouse press/move/release
- Close button closes popup

## Transcript Window Layout
File: `ui_ux_team/blue_ui/views/transcript_window.py`

Structure:
- `QVBoxLayout`
  - top row `QHBoxLayout`
    - record button `65x65`
    - search bar fixed height `48`
  - transcript text area

Stretch ratios:
- top row stretch factor `1`
- text box stretch factor `9`

Signals:
- `record_clicked` emitted when record icon clicked
- `closed` emitted on close event

## BlueBird Chat Window Layout
File: `ui_ux_team/blue_ui/views/chat_window.py`

Structure:
- `QVBoxLayout`
  - `TextBoxAI` stretch `9`
  - input row (`QHBoxLayout`) stretch `1`
    - `InputBlueBird` fixed height `70`
    - send button `63x63`

Overlay widget:
- `load_transcript` button `40x40` parented directly to window and positioned in `resizeEvent`

Loading state:
- `LoadingCircle` overlay centered over text area during async operations

Async workers:
- `ChatInitWorker` for initial context load
- `ChatWorker` for message response
- `ContextUpdateWorker` for loading transcript files

## Shared Widget Contracts
### ImageButton
File: `ui_ux_team/blue_ui/widgets/image_button.py`
- Base: clickable `QLabel`
- Fixed size at creation
- Hover and press scale animation
- Optional rounded-rect clipping via `set_corner_radius(radius)`
- Emits `clicked`

### Text widgets
File: `ui_ux_team/blue_ui/widgets/text_boxes.py`
- `TextBoxAI`: markdown-formatted chat history (`QTextBrowser`)
- `InputBlueBird`: message input (`Ctrl+Enter` send)
- `TextBox`: transcript output (`QPlainTextEdit`, read-only)
- `SearchBar`: transcript search input (`QTextEdit`, fixed height `48`)

### QueuedMarqueeLabel
File: `ui_ux_team/blue_ui/widgets/marquee.py`
- Cycles mood strings with fade out/in
- Internal scrolling `MarqueeLabel` continuously scrolls long text horizontally

### FloatingToast
File: `ui_ux_team/blue_ui/widgets/toast.py`
- Temporary animated message label
- Starts lower band, drifts upward, fades in/out

### LoadingCircle
File: `ui_ux_team/blue_ui/widgets/loading.py`
- Fixed-size spinner using custom paint
- Used in chat window only

## Theme and Styling System
Theme tokens:
- `ui_ux_team/blue_ui/theme/tokens.py`

Theme registry:
- `ui_ux_team/blue_ui/theme/palettes.py`
- Includes multiple themes, default is `dark_theme`

Theme manager:
- `ui_ux_team/blue_ui/theme/manager.py`
- `set_theme`, `ensure_default_theme`, persistence load/save

Per-widget style helpers:
- `ui_ux_team/blue_ui/theme/styles.py`

Theme application behavior:
- On theme select:
  - set new theme tokens
  - refresh transcript/chat/floating menu if open
  - rebuild main layout
  - refresh timeline styling

## Audio and Music Pathing
Main logic in `MainUI`:
- Music folder persisted in `audio_config.json`
- Folder selected in settings tab (folder picker)
- Resolver probes in order:
  1. `resource_path(clean)`
  2. `resource_path(ui_ux_team/assets/clean)`
  3. `<music_folder>/<basename>`
  4. `<music_folder>/<relative_path>`
  5. `<cwd>/<relative_path>`
  6. `<project_root>/<relative_path>`

Volume-to-player contract:
- `MainUI.set_volume` stores current volume always
- Applies to active player if present

## Config Persistence (UI-relevant)
Files:
- `ui_ux_team/blue_ui/config/runtime_paths.py`
- `ui_ux_team/blue_ui/config/settings_store.py`

Persisted JSON:
- theme: `theme_config.json`
- audio folder: `audio_config.json`

Storage location:
- user config path per OS (`~/.config/dj-blue-ai/blue_ui` on Linux)
- legacy repo config auto-migrated when present

## Signals and Event Wiring Summary
Main event links:
1. `PlaybackTimeline.seek_requested -> MainUI._on_timeline_seek`
2. `IntegratedVolumeControl.volume_changed -> MainUI.set_volume`
3. `SongCoverCarousel.prev_requested -> MainUI.prev_action`
4. `SongCoverCarousel.next_requested -> MainUI.next_action`
5. Transport button clicks -> `prev_action` / `play_click` / `next_action`
6. Transcript record button -> `MainUI.record_transcript`
7. Theme chooser `theme_selected -> MainUI._apply_theme_and_rebuild`

## Known Layout Constraints and Tradeoffs
1. Sidebar is strictly fixed-width at `70`.
2. Transport area uses fixed slots (`180/290/180`) for stable alignment.
3. Timeline is fixed-height (`52`) in main panel.
4. Cover area is expanding and takes the only explicit vertical stretch in main panel.
5. Volume control is fixed-size and manually laid out internally for stable icon anchor during slider animation.

## Quick Maintenance Guide
1. Want to change global spacing proportions?
- Edit `build_main_panel` and `build_main_bottom_panel` in `main_window.py`.

2. Want to change cover scaling behavior?
- Edit `_preferred_center`, ratio, and `_update_cover_sizes()` in `song_cover_carousel.py`.

3. Want to change timeline UX?
- Edit `PlaybackTimeline` and `PreciseSeekSlider` in `widgets/timeline.py`.

4. Want to add a settings page?
- Create tab widget in `MainUI.settings_menu()` and pass into `SettingsPopup` categories dict.

5. Want theme consistency on a new widget?
- Use `tokens.*` for colors; implement `refresh_theme()` and call it when windows are rebuilt.
