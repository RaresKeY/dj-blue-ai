# PySide6 Component Split Plan

## 1) Goal and Non-Goals

### Goal
Refactor `ui_ux_team/prototype_r/py_learn.py` into separable, runnable layers so UI components can be launched independently for fast visual iteration.

### Non-Goals
- No migration to Qt Designer `.ui` files in this pass.
- No rewrite of existing backend logic in `architects/helpers`.
- No feature redesign; preserve current behavior while improving structure.

## 2) New Folder Structure

```text
ui_ux_team/blue_ui/
  app/
    main.py
    composition.py
    services.py
  views/
    main_window.py
    chat_window.py
    transcript_window.py
    settings_popup.py
  widgets/
    image_button.py
    marquee.py
    toast.py
    text_boxes.py
    volume.py
    loading.py
  theme/
    tokens.py
    styles.py
  previews/
    preview_main_window.py
    preview_chat_window.py
    preview_transcript_window.py
    preview_widgets.py
    run_preview.sh
  docs/
    component_split_plan.md
  py_learn.py  # compatibility launcher shim
```

## 3) Interfaces and Signals Contract

### App Services
Use an `AppServices` container/facade to inject:
- transcription service
- player service
- memory service
- chat service
- mood repository

### Main Window View Signals
- `record_toggled(bool)`
- `play_toggled()`
- `volume_changed(float)`
- `transcript_open_requested()`
- `chat_open_requested()`
- `settings_requested()`

### Chat Window View Signals
- `message_submitted(str)`
- `context_file_selected(str)`

### Transcript Window View API
- `append_segment(str)`
- `set_search_query(str)` (future hook)

### Composition Responsibilities
`AppComposer` owns wiring only:
- instantiate views/services
- connect view signals to services
- route service results back to views
- manage popup/child window lifecycle
- centralize error/fallback handling

## 4) Preview Run Commands

Code-first visual workflow with instant launch scripts.

### Preview Targets
- `main`
- `chat`
- `transcript`
- `widgets`

### Command Shape
```bash
cd ui_ux_team/blue_ui/previews
./run_preview.sh main
./run_preview.sh chat
./run_preview.sh transcript
./run_preview.sh widgets
```

### Preview Behavior Rules
- No external API key required.
- Use deterministic mock data/services.
- UI should always boot even without audio devices.

## 5) Migration Order and Rollback Point

1. Extract theme constants/styles from `py_learn.py` into `theme/`.
2. Extract reusable controls into `widgets/` (no backend imports).
3. Extract windows/popups into `views/` (UI and signals only).
4. Add `app/services.py` wrappers for existing helper modules.
5. Add `app/composition.py` and wire all UI/service interactions.
6. Add `app/main.py` as the canonical entrypoint.
7. Convert `py_learn.py` into a compatibility shim that calls `app.main`.
8. Add `previews/` scripts and `run_preview.sh`.

### Rollback Point
Until step 7, original `py_learn.py` remains executable as today. If issues appear, keep old entrypoint and disable new composition import path.

## 6) Known Risks and Mitigations

### Risk: Behavior regression during extraction
Mitigation: keep interfaces stable, move code in small slices, run smoke launch after each slice.

### Risk: Signal/slot breakage across modules
Mitigation: define signal contracts first and keep composer as the only cross-layer wiring point.

### Risk: Asset path failures after module moves
Mitigation: centralize path resolution in one theme/resource helper and keep image fallback logic.

### Risk: Service startup failures (API key/audio missing)
Mitigation: fail soft in composer; keep UI interactive and show status/toast/log message.

### Risk: Duplicate legacy widgets (`py_learn.py`, `visual_components.py`, `bluebird_chat_widget.py`)
Mitigation: declare `widgets/` + `views/` as source of truth and treat legacy files as transitional until removed.
