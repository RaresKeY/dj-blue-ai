# Onboarding Arrow Guide

## Behavior

The onboarding arrow uses `arrow_1` animation and runs this staged flow:

1. Start at `api` stage:
- Arrow points to the sidebar API button.
2. After API key is set successfully:
- Arrow switches to `transcript` stage and points to the transcript button.
3. When transcript is clicked during transcript stage:
- Arrow is dismissed (`done` stage) and no longer appears.

## Component

- `ui_ux_team/blue_ui/widgets/onboarding_arrow_guide.py`
  - Reusable stateful controller for API -> Transcript -> Done
  - Uses `ui_ux_team/blue_ui/widgets/transcript_hint_arrow.py` for animation rendering

## Main App Wiring

- `ui_ux_team/blue_ui/views/main_window.py`
  - API key save event triggers stage progression.
  - Transcript click dismisses arrow only when stage is `transcript`.

## Preview

- Logic preview with two buttons + mock API setup window:
  - `.venv/bin/python ui_ux_team/blue_ui/previews/preview_onboarding_arrow_logic.py`
- Run preview runner target:
  - `.venv/bin/python ui_ux_team/blue_ui/previews/run_preview.py onboarding_arrow_logic`
