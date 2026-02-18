# Project Cleanup & Refactoring Plan 2026

- **Status**: Draft
- **Date**: 2026-02-18
- **Objective**: Eliminate legacy debt, enforce the Blue UI architecture, and prepare the codebase for long-term maintainability.

---

## 1. Deletion Strategy (The Purge)

We will aggressively remove files that are no longer referenced, deprecated prototypes, or temporary scripts.

### 1.1 Root Level
- [ ] **Remove**: `test_suite_1.py` (Move logic to `tests/integration/` or `scripts/ci/`).
- [ ] **Remove**: `build_appimage.py`, `build_binary.py`, `build_nuitka.py` (Consolidate into a single `scripts/build/` module).
- [ ] **Remove**: `setup_keys.py` (Logic now exists in `ui_ux_team/blue_ui/app/secure_api_key.py`).

### 1.2 Deprecated Directories
- [ ] **Delete**: `ui_ux_team/prototype_r/` (Entire folder is legacy).
- [ ] **Delete**: `architects/helpers_capture_app/` (Empty or unused).
- [ ] **Delete**: `music_librarians/` (Appears unused or needs explicit integration plan).
- [ ] **Delete**: `djs/`, `front_end_engineers/`, `gui_developers/` (Empty `.gitkeep` placeholders).

### 1.3 Redundant Helpers
- [ ] **Consolidate**: `architects/helpers/record_live_mix_linux.py` -> `the_listeners/recorders/linux_recorder.py`.
- [ ] **Consolidate**: `architects/helpers/jsonrules_song.py` -> `architects/core/models/song_rules.py`.

---

## 2. Structural Reorganization

We will adopt a domain-driven structure, moving away from "role-based" folder names (e.g., `architects`, `the_listeners`) towards "feature-based" names.

### 2.1 Proposed Directory Tree
```text
dj-blue-ai/
├── src/
│   ├── app/                 # Entry points (main.py, config)
│   ├── core/                # Core domain logic (LLM, Audio, State)
│   ├── ui/                  # Blue UI (Views, Widgets, Themes)
│   ├── infrastructure/      # OS integration (Platform, Hardware)
│   └── scripts/             # Build & Utility scripts
├── tests/                   # Unified test suite
│   ├── unit/
│   └── integration/
├── docs/                    # Design docs & plans
└── resources/               # Static assets (images, icons)
```

### 2.2 Mapping Old to New
| Current Path | New Path |
| :--- | :--- |
| `ui_ux_team/blue_ui` | `src/ui/` |
| `architects/helpers/genai_client.py` | `src/core/llm/client.py` |
| `architects/helpers/miniaudio_player.py` | `src/core/audio/player.py` |
| `the_listeners/` | `src/core/audio/recording/` |
| `mood_readers/` | `src/core/analysis/` |

---

## 3. Code Refactoring

### 3.1 LLM Standardization
- [ ] **Goal**: Ensure ALL LLM interactions go through `src/core/llm/LLMService`.
- [ ] **Action**: Deprecate direct usage of `GenAIClient` in views. Views should request data from a controller/service.

### 3.2 Configuration Management
- [ ] **Goal**: Unified Pydantic-based configuration.
- [ ] **Action**: Replace `settings_store.py` (dict-based) with a typed `AppConfig` model.
- [ ] **Action**: Strict validation for all user inputs (API keys, paths, limits).

### 3.3 Audio Pipeline
- [ ] **Goal**: Decouple UI from Audio Logic.
- [ ] **Action**: Extract `MiniaudioPlayer` logic from `MainWindow` into a global `AudioController` singleton or context provider.

---

## 4. Modularization Steps

### Phase 1: Isolation (Safe)
1. Move `ui_ux_team/blue_ui` to `src/ui`.
2. Update imports in `main.py`.
3. Verify application startup.

### Phase 2: Core Extraction (Low Risk)
1. Create `src/core`.
2. Move `architects/helpers` to `src/core/helpers`.
3. Refactor imports project-wide.

### Phase 3: Cleanup (Medium Risk)
1. Delete `prototype_r` and unused placeholders.
2. Verify build scripts still function.

### Phase 4: Architecture Shift (High Risk)
1. Implement `AudioController`.
2. Refactor `MainWindow` to use `AudioController`.
3. Implement `AppConfig` Pydantic model.

---

## 5. Timeline & Milestones

- **Week 1**: Phase 1 & Phase 2 (Structure & Imports).
- **Week 2**: Phase 3 (Deletions) & Phase 4 (Audio Controller).
- **Week 3**: Configuration Refactor & Final Verification.

---

## 6. Verification Strategy
- **Pre-Commit**: Run `test_suite_1.py` (renamed to `tests/run_all.py`).
- **Visual Audit**: Use `snap_gallery.py` to ensure UI refactors didn't break themes.
- **Build Test**: Verify `build_binary.py` (or new build script) produces a working artifact.
