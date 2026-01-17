# Changelog

## 2026-01-17

### Features
- **Volume Control UI**: Added `VolumeButton` and `VolumePopup` to the main interface (`ui_ux_team/prototype_r/py_learn.py`).
    - Implemented "phone-style" interaction: Click to toggle (future), Press & Drag to slide volume.
    - Added `MiniaudioPlayer` volume scaling via a generator wrapper in `architects/helpers/miniaudio_player.py`.
    - Fixed `miniaudio` generator startup issue by priming the generator with `next()`.

### Bug Fixes
- **Windows Transcript Saving**: Fixed `OSError` on Windows caused by colons (`:`) in filenames derived from session timestamps. Filenames now sanitize `:` to `-`.
