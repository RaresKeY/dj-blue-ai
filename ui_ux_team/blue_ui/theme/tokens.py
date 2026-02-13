"""Shared mutable theme tokens for Blue UI."""

# Core palette (ui_ux_team/design_docs/palette.txt)
PRIMARY = "#1E90FF"
ACCENT = "#FF69B4"
BACKGROUND = "#0A0A12"
TEXT = "#E0E6ED"
SECONDARY = "#6C63FF"

COLOR_BG_MAIN = "#070B17"
COLOR_SETTINGS_BG = "#10182A"
COLOR_SIDEBAR = "#170A2A"
COLOR_COVERS_BG = "transparent"
COLOR_TIMELINE_BG = "rgba(44, 83, 140, 0.12)"
COLOR_BOTTOM_BG = "rgba(8, 15, 34, 0.22)"
COLOR_CONTROLS_BG = "transparent"
COLOR_CONTROL_BTN = ACCENT
TIMELINE_TEXT = TEXT
TIMELINE_PROGRESS = "rgba(198, 198, 198, 0.92)"
TIMELINE_REMAINING = "rgba(0, 0, 0, 0.74)"
TIMELINE_PREVIEW = "rgba(32, 32, 32, 0.58)"
TIMELINE_HANDLE_IDLE = "rgba(255, 255, 255, 0.0)"
TIMELINE_HANDLE = PRIMARY
TIMELINE_HANDLE_HOVER = SECONDARY

TEXT_PRIMARY = TEXT
TEXT_MUTED = "#A8B3C8"
BG_INPUT = "#111624"
BORDER_SUBTLE = "#2A3550"

FONT_STACK = '"Inter", "Segoe UI", "Ubuntu", sans-serif'

# Runtime theme state (updated by theme.manager.set_theme).
CURRENT_THEME_KEY = "dark_theme"
