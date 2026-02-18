# UI Widget Set

- **Last Updated: 2026-02-18**
- **Path**: `ui_ux_team/blue_ui/widgets/`
- **Purpose**: Reusable Qt widgets for buttons, marquees, carousels, and interactive UI components.

## Key Widgets
- **ImageButton** (`image_button.py`): QLabel-based image button with hover/press animations and optional tinting.
- **QueuedMarqueeLabel** (`marquee.py`): Scrolling text widget that cycles through a queue with fade transitions.
- **SongCoverCarousel** (`song_cover_carousel.py`): Interactive 3D-like carousel for selecting and playing music tracks.
- **PlaybackTimeline** (`timeline.py`): Seekable progress bar for music playback with duration/position display.
- **IntegratedVolumeControl** (`volume.py`): Combined volume button and slider popup for software volume adjustment.
- **FloatingToast** (`toast.py`): Animated notification that rises and fades from the bottom of the window.
- **OnboardingArrowGuide** (`onboarding_arrow_guide.py` / `transcript_hint_arrow.py`): Animated arrows to guide users through the initial setup (e.g., setting API key).
- **LoadingCircle** (`loading.py`): Animated spinner for indicating background API or processing tasks.
- **ThemeChooserMenu** (`theme_chooser.py`): Dropdown or grid menu for selecting application themes.
- **TextBox / TextBoxAI / SearchBar** (`text_boxes.py`): Styled text areas for chat, transcripts, and input.

## Usage Tips
- **Button Factory**: Use `MainUI.button("assets/icon.png", size=(40,40))` for consistent styling and fallbacks.
- **Theme Awareness**: Most widgets implement a `refresh_theme()` method to update colors and styles from `tokens.py`.
- **Global Positioning**: For popups like `FloatingMenu` or `SettingsPopup`, use `parent.mapToGlobal()` to anchor to specific UI elements.
- **Asset Paths**: Use `architects.helpers.resource_path.resource_path()` to resolve asset locations, especially for bundled applications.

