# App Icon Cross-Platform Plan (logo_margins.png)

## Goal
Use `ui_ux_team/assets/logo_margins.png` as the single icon source and ensure consistent icon behavior on all 3 platforms:
- packaged app icon
- window/title-bar icon
- taskbar/dock icon
- system tray / menu bar icon (when tray is used)

## Current State (from build files)
- `build_binary.py` runs PyInstaller with `--onefile --windowed`, but does not pass `--icon`.
- `.github/workflows/build.yml` builds on `ubuntu-latest`, `windows-latest`, `macos-latest` and calls `python build_binary.py`.
- Runtime code currently does not set `QApplication`/main window icon globally.

## Plan

### 1. Add generated platform icon assets from one source PNG
Create `scripts/generate_app_icons.py` that reads:
- `ui_ux_team/assets/logo_margins.png`

And writes:
- `ui_ux_team/assets/app_icons/windows/dj-blue-ai.ico`
- `ui_ux_team/assets/app_icons/macos/dj-blue-ai.icns`
- `ui_ux_team/assets/app_icons/linux/` PNG sizes: `16, 24, 32, 48, 64, 128, 256, 512`
- `ui_ux_team/assets/app_icons/tray/` PNG sizes for Qt tray use (16/20/22/24/32)

Rules:
- keep transparent background
- use high-quality resampling (Lanczos/smooth)
- no manual per-platform source editing; always regenerate from `logo_margins.png`

### 2. Build-time icon wiring in `build_binary.py`
Add platform-specific `--icon`:
- Windows: `--icon=ui_ux_team/assets/app_icons/windows/dj-blue-ai.ico`
- macOS: `--icon=ui_ux_team/assets/app_icons/macos/dj-blue-ai.icns`
- Linux: `--icon=ui_ux_team/assets/app_icons/linux/512.png` (used where supported)

Also ensure icon folders are bundled via `--add-data`:
- `ui_ux_team/assets/app_icons`

### 3. CI workflow updates in `.github/workflows/build.yml`
Before `Build Binary`, add step:
- run icon generator script on each OS

Then keep existing `python build_binary.py` step.

Validation step per OS:
- assert expected icon file exists before build (`.ico` on Windows, `.icns` on macOS, `512.png` on Linux).

### 4. Runtime Qt icon wiring (taskbar/titlebar/dock)
In startup path (`ui_ux_team/blue_ui/app/main.py`):
- load `QIcon` from packaged `resource_path(...)` path
- call `app.setWindowIcon(icon)` right after QApplication creation

In main window init (`ui_ux_team/blue_ui/views/main_window.py`):
- call `self.setWindowIcon(icon)` to guarantee per-window icon

This covers:
- Windows taskbar icon
- Linux taskbar/window icon
- macOS dock/app icon fallback at runtime

### 5. Tray / menu bar icon support
If/when `QSystemTrayIcon` is used:
- load icon from `ui_ux_team/assets/app_icons/tray/`
- set explicit tray icon with platform-sized asset

Notes:
- macOS menu bar status icon should use template/monochrome variant if design requires native appearance.
- keep this as a controlled follow-up if tray feature is introduced.

### 6. Optional Linux desktop launcher icon
For packaged Linux app delivery:
- add `.desktop` file generation that points to installed PNG icon (typically 256/512).
- verify launcher icon appears in GNOME/KDE app grid.

## Implementation Order
1. Add icon generator script + output directories.
2. Update `build_binary.py` (`--icon` + add-data for app_icons).
3. Update GitHub workflow to run generator + pre-build checks.
4. Add runtime `app.setWindowIcon(...)` and `MainWindow.setWindowIcon(...)`.
5. Verify on all 3 OS artifacts.

## Verification Checklist
- Windows:
  - `.exe` shows custom icon in Explorer.
  - running app shows custom taskbar icon.
- macOS:
  - built app/binary shows custom dock icon.
  - app window icon is consistent where shown.
- Linux:
  - window/taskbar icon matches logo.
  - launcher icon matches when `.desktop` integration is used.
- No missing-resource errors in frozen mode (`sys._MEIPASS` paths).

## Risks and Mitigations
- Risk: icon format generation differs across OS tools.
  - Mitigation: use one script and deterministic output checks in CI.
- Risk: PyInstaller onefile behavior differs for macOS icon embedding.
  - Mitigation: keep runtime `app.setWindowIcon` as fallback, and validate macOS artifact manually.
- Risk: blurry small tray icons.
  - Mitigation: generate dedicated small tray sizes and test at 100% and HiDPI scaling.
