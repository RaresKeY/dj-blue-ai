# Quality & Testing

## Test Scope Boundary
- Production runtime test target is `ui_ux_team/blue_ui/` plus active shared helpers used by Blue UI runtime.
- `ui_ux_team/prototype_r/` is legacy and is not part of the active production test baseline.
- Code in `prototype_r` may be copied, stale, partial, or non-imported; failures there should not be interpreted as production regressions unless production imports prove dependency.
- Legacy standalone tool paths (`transcribers/`, `the_listeners/`) are outside the primary Blue UI regression target unless explicitly covered by dedicated tests.

## Automated Tests In Repository
- UI smoke tests: `ui_ux_team/blue_ui/tests/test_button_clicks.py`.
- UI smoke coverage includes sidebar actions, transport controls, and BlueBird window toggling with patched fake player.
- Core logic tests: `architects/tests/test_logic.py`.
- Core logic coverage includes `ManagedMem`, API usage guard state accounting, mocked LLM calls, and optional real API checks.
- Domain object persistence tests: `architects/tests/test_song.py`.
- Persistence coverage verifies `Song` serialization/roundtrip via managed memory storage.
- Test package support file: `architects/tests/__init__.py`.
- Manual audio graph listing helpers exist under the test namespace.
- UI iteration scaffold modules for manual geometry/alignment validation:
- `ui_ux_team/blue_ui/tests/iteration/dev/api_settings_keyring_setup.py`
- `ui_ux_team/blue_ui/tests/iteration/dev/cover_segment_layout_boxes.py`
- `ui_ux_team/blue_ui/tests/iteration/dev/cover_segment_vertical_slips_layout.py`
- `ui_ux_team/blue_ui/tests/iteration/dev/transcript_hint_arrow_peck.py`

## CI Build Workflow
- Workflow file: `.github/workflows/build.yml`.
- Triggers are tag pushes matching `v*` and manual dispatch.
- Matrix builds run on Ubuntu, Windows, and macOS.
- CI installs Python 3.12 and dependencies, validates platform icon, builds binary, builds Linux AppImage (Linux only), uploads artifacts, and creates GitHub release for tag refs.

## Build Tooling
- PyInstaller one-file GUI build: `build_binary.py`.
- Linux AppImage packaging: `build_appimage.py`.
- Nuitka standalone build path: `build_nuitka.py`.
- Optional pre-build logic-test runner script: `test_suite_1.py` (invokes `architects/tests/test_logic.py` with timeout).
- Visual preview tooling for manual QA:
- `ui_ux_team/blue_ui/previews/run_preview.py`
- `ui_ux_team/blue_ui/previews/snap_gallery.py`
- `ui_ux_team/blue_ui/previews/ui_iterate.py`

## Current Gaps / Risks (From Read Evidence)
- No broad end-to-end integration test for full record/transcribe/chat/playback cycle in CI.
- Real API tests exist but are conditional on key availability and may be skipped.
- UI tests emphasize click/no-crash behavior over visual/geometry assertions in core test suite (visual checks are handled via preview snapshot workflow).
- Visual QA is documented and screenshot-driven (`snap_gallery.py`, visual audit reports), but it is not a strict CI gate.
- Legacy modules in `transcribers/`, `the_listeners/`, and `ui_ux_team/prototype_r/` are not covered by the active Blue UI smoke tests and may drift.
