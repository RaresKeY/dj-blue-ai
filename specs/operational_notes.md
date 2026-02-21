# Operational Notes

This file is now the operations index. Detailed operational specs are split into focused docs:

- [Operations: Runtime & Environment](operations_runtime_and_env.md)
- [Operations: UI Iteration Workflow](operations_ui_iteration.md)
- [Operations: Build & Release](operations_build_release.md)

## Scope Split Rationale
- Runtime startup/env behavior changes for day-to-day development and support.
- UI iteration has a dedicated workflow with preview/snapshot requirements.
- Build/release behavior is CI/tag/pipeline specific and should stay isolated.

## High-Level Invariants
- Production runtime entry is the Blue UI path; root `main.py` is compatibility shim.
- Build/release automation is tag-driven (`v*`) in GitHub Actions.
- Legacy prototype directories are not operational source of truth for production behavior.
