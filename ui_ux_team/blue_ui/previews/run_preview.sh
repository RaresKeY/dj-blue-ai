#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-main}"

case "$TARGET" in
  main)
    ./.venv/bin/python ui_ux_team/blue_ui/previews/preview_main_window.py
    ;;
  chat)
    ./.venv/bin/python ui_ux_team/blue_ui/previews/preview_chat_window.py
    ;;
  transcript)
    ./.venv/bin/python ui_ux_team/blue_ui/previews/preview_transcript_window.py
    ;;
  widgets)
    ./.venv/bin/python ui_ux_team/blue_ui/previews/preview_widgets.py
    ;;
  volume)
    ./.venv/bin/python ui_ux_team/blue_ui/previews/preview_volume.py
    ;;
  *)
    echo "Usage: $0 {main|chat|transcript|widgets|volume}"
    exit 1
    ;;
esac
