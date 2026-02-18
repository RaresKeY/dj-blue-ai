# PyInstaller + AppImage Plan (Linux)

- **Last Updated: 2026-02-18**

## Goal
Add Linux AppImage packaging on top of the current PyInstaller flow, without removing existing release artifacts.

## Current Baseline
- Existing local builder: `build_binary.py` (PyInstaller onefile).
- Existing CI workflow: `.github/workflows/build.yml`.
- Existing Linux release artifact: raw binary `dj-blue-ai-linux`.

## Strategy
1. Keep current PyInstaller build unchanged for all platforms.
2. Add a Linux-only post-build packaging step that wraps the PyInstaller binary into AppImage.
3. Publish both Linux artifacts in releases:
   - raw binary (existing)
   - `.AppImage` (new)

## Implementation Plan

### 1. Add local AppImage packager script
Create `build_appimage.py` that:
- uses `dist/dj-blue-ai` as input (from `build_binary.py`)
- constructs `build/appimage/AppDir` with:
  - `AppRun`
  - `dj-blue-ai.desktop`
  - icon (`dj-blue-ai.png`) from `ui_ux_team/assets/app_icons/linux/512.png`
  - executable copied to `AppDir/usr/bin/dj-blue-ai`
- calls `appimagetool` to produce:
  - `dist/dj-blue-ai-linux-<arch>.AppImage`

### 2. CI integration (Linux only)
In `.github/workflows/build.yml`:
- after `python build_binary.py`, download `appimagetool` in Linux job
- run `python build_appimage.py` with `APPIMAGETOOL` env path
- keep existing artifact upload rule and add AppImage path

### 3. Release integration
In release job:
- keep copying current Linux binary to `artifacts/dj-blue-ai-linux`
- additionally copy Linux AppImage to `artifacts/dj-blue-ai-linux.AppImage`
- include AppImage in release files list

## Local Usage
```bash
.venv/bin/python build_binary.py
APPIMAGETOOL=tools/appimagetool.AppImage .venv/bin/python build_appimage.py
```

## Verification Checklist
- AppImage is generated under `dist/`.
- Running AppImage launches the same app behavior as the binary.
- Desktop launcher metadata is present (`Name`, `Icon`, `Categories`).
- Existing artifacts for Windows/macOS/Linux binary remain unchanged.

## Risks and Mitigations
- Risk: `appimagetool` execution issues in CI due FUSE/runtime.
  - Mitigation: run with `APPIMAGE_EXTRACT_AND_RUN=1`.
- Risk: missing input binary if build step changes.
  - Mitigation: explicit pre-check for `dist/dj-blue-ai` in script.
- Risk: icon mismatch.
  - Mitigation: force icon source path to committed `app_icons/linux/512.png`.
