# Operations: Build & Release

## Scope
- Build scripts, CI workflow, and release/tag operations.
- Main files:
- `.github/workflows/build.yml`
- `build_binary.py`
- `build_appimage.py`
- `build_nuitka.py`
- `architects/design_docs/TAGGING_GUIDE.md`

## CI Trigger Contract
- GitHub Actions build workflow triggers on:
- tag pushes matching `v*`
- manual dispatch
- Build matrix targets Ubuntu, Windows, and macOS.

## CI Pipeline Behavior
- Sets up Python 3.12 and installs dependencies.
- Validates platform icon availability.
- Runs binary build steps and Linux AppImage packaging on Linux.
- Uploads build artifacts.
- Creates GitHub release for tag refs.

## Local Build Tooling
- `build_binary.py` for PyInstaller one-file GUI binary.
- `build_appimage.py` for Linux AppImage packaging (Linux-focused stage).
- `build_nuitka.py` for standalone Nuitka-based build path.

## Tagging Policy
- Release tagging guidance is documented in `architects/design_docs/TAGGING_GUIDE.md`.
- SemVer-like `v*` tags are treated as release automation entrypoints by CI workflow.

## Security-Relevant Build Notes
- Build/release processes avoid bundling local secret files.
- Runtime secret handling remains keyring/process/env based and outside packaged static config.

## Key Invariants
- Tag format drives automated release behavior.
- CI build outputs are platform-specific and published as release artifacts.
