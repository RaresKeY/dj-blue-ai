# Nuitka Build Plan (DJ Blue AI)

- **Last Updated: 2026-02-18**

## Objective
Introduce a Nuitka-based build pipeline for Linux, Windows, and macOS while preserving current release behavior and icon/asset packaging.

## Current Baseline
- Current builders:
  - `build_binary.py` (PyInstaller, cross-platform binaries)
  - `build_appimage.py` (Linux AppImage packaging from PyInstaller output)
- Current CI release workflow: `.github/workflows/build.yml`.
- App entrypoint: `ui_ux_team/blue_ui/app/main.py`.
- Icon assets already committed under `ui_ux_team/assets/app_icons/`.

## Target Outcomes
- Produce distributable binaries for all 3 platforms via Nuitka.
- Preserve app icon behavior (packaged icon + runtime icon fallback).
- Preserve runtime assets/data access (`ui_ux_team/assets`, `mood_readers/data`).
- Keep rollback path to existing PyInstaller + AppImage release flow until Nuitka parity is verified.

## Scope
- In scope:
  - new Nuitka build script
  - CI job updates for Nuitka builds
  - artifact naming/collection updates
  - verification checklist and rollout plan
- Out of scope:
  - installer creation (`.msi`, `.dmg`, `.deb`) in first pass
  - code obfuscation tuning beyond default compilation

## Phase 0: PyInstaller + AppImage Stabilization (Current Track)
Keep current release outputs stable while Nuitka is developed:
- Linux raw binary from `build_binary.py`
- Linux AppImage from `build_appimage.py`
- Windows/macOS binaries from `build_binary.py`

Nuitka rollout starts only after these outputs remain stable in CI.

## Phase 1: Local Nuitka Build Script
Create `build_nuitka.py` with platform-aware arguments.

Recommended base command structure:
```bash
.venv/bin/python -m nuitka \
  --standalone \
  --assume-yes-for-downloads \
  --enable-plugin=pyside6 \
  --output-dir=dist_nuitka \
  --output-filename=dj-blue-ai \
  ui_ux_team/blue_ui/app/main.py
```

Add data directories:
- `--include-data-dir=ui_ux_team/assets=ui_ux_team/assets`
- `--include-data-dir=mood_readers/data=mood_readers/data`

Add platform icon flag:
- Windows: `--windows-icon-from-ico=ui_ux_team/assets/app_icons/windows/dj-blue-ai.ico`
- macOS: `--macos-app-icon=ui_ux_team/assets/app_icons/macos/dj-blue-ai.icns`
- Linux: keep runtime icon behavior + optional desktop file icon mapping in later phase

Optional compatibility flags (enable only if needed by runtime tests):
- `--include-module=google.generativeai`
- `--include-package=architects`
- `--include-package=mood_readers`
- `--include-package=ui_ux_team`

## Phase 2: CI Workflow Extension
Update `.github/workflows/build.yml` with a new parallel Nuitka job (do not remove PyInstaller yet).

Per OS steps:
1. Install Python + system dependencies (same base as existing job).
2. Install Nuitka toolchain:
   - `pip install nuitka`
   - Linux/macOS: ensure `patchelf`/`ccache`/compiler prerequisites if required.
3. Validate icon file for current OS (reuse current icon validation step).
4. Run `python build_nuitka.py`.
5. Upload artifacts from `dist_nuitka/`.

Artifact naming:
- `dj-blue-ai-nuitka-${{ runner.os }}`

## Phase 3: Runtime Parity Validation
For each OS artifact, validate:
1. App launches without missing module/data errors.
2. Window/taskbar/dock icon appears correctly.
3. Music mood JSON loads from packaged data path.
4. Core UI interactions: launch, playback controls, settings open, transcript window open.
5. No regressions in startup path.

## Phase 4: Release Switch
After parity is confirmed:
1. Switch release job inputs from PyInstaller artifacts to Nuitka artifacts.
2. Keep PyInstaller + AppImage jobs available for one release cycle behind manual trigger.
3. Remove PyInstaller/AppImage release path after one stable cycle.

## File Changes Plan
1. Add `build_nuitka.py`.
2. Add/adjust docs in `README.md` Build and Release section with Nuitka commands.
3. Extend `.github/workflows/build.yml` with Nuitka build matrix job.
4. Keep `build_binary.py` and `build_appimage.py` intact during migration.

## Risks and Mitigations
- Risk: missing dynamic imports at runtime.
  - Mitigation: add targeted `--include-module/--include-package` flags based on error logs.
- Risk: larger artifact sizes or slower CI.
  - Mitigation: compare artifact metrics for 2 releases, then optimize flags.
- Risk: OS-specific compiler dependency issues.
  - Mitigation: pin build prerequisites in CI and keep PyInstaller + AppImage fallback jobs.
- Risk: icon mismatch on Linux desktop launchers.
  - Mitigation: add `.desktop` packaging step in post-parity phase.

## Acceptance Criteria
- Nuitka artifacts are produced successfully on Ubuntu, Windows, macOS CI runners.
- Artifacts launch and pass runtime parity checks.
- Icons display correctly in packaged app contexts.
- Release can be published from Nuitka artifacts without manual patching.

## Rollback Strategy
- If Nuitka release candidate fails, continue release from PyInstaller + AppImage artifacts (`build_binary.py` + `build_appimage.py`) for that tag.
- Keep both build scripts versioned until two successful Nuitka releases are completed.
