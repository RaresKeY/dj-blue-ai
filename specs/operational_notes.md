# Operational Notes

## Environment And Startup
- Recommended runtime uses project virtual environment and Python 3.12.
- App launch options:
- `python main.py` (compatibility entrypoint)
- `python ui_ux_team/blue_ui/app/main.py` (direct Blue UI entrypoint)
- API key resolution can use keyring, process environment variables, and optional local env-file fallback when explicitly enabled.

## Runtime Persistence Strategy
- Runtime path resolution is centralized in the Blue UI runtime-path module.
- Development mode uses repository-adjacent runtime storage locations.
- Frozen/AppImage mode uses OS-specific user directories for config/data.

## UI Iteration Workflow (Repository Contract)
- Canonical process is documented in:
- `AGENTS.md`
- `ui_ux_team/blue_ui/docs/UI_WORKFLOW.md`
- `ui_ux_team/blue_ui/tests/iteration/README.md`
- `ui_ux_team/blue_ui/docs/ui_complete_reference.md`
- Required pattern:
- scaffold preview/test component via `ui_iterate.py scaffold`
- iterate through preview runner
- capture deterministic snapshots via `ui_iterate.py snap`
- integrate into production views/widgets only after visual verification

## Debug/Utility Commands Reviewed
- Debug and utility scripts exist for model inspection, icon generation, and local keyring setup.

## Release And Tagging
- Canonical tagging policy: `architects/design_docs/TAGGING_GUIDE.md`.
- SemVer-like `v*` tags trigger CI release pipeline via `.github/workflows/build.yml`.

## Security-Relevant Operational Behavior
- Build processes avoid bundling local secret files.
- API settings surface secure backend and masking status.
- API usage guardrails are persisted/enforced locally.

## Legacy Boundary Notes
- `ui_ux_team/prototype_r/` is a legacy prototype/refactor source after migration/copy work into `ui_ux_team/blue_ui/`.
- Prototype paths may contain exploratory, unimported, partially implemented, or non-transferred code; treat as historical unless active runtime imports prove usage.
- Historical docs and diagnostic artifacts remain useful context, but implementation modules in the active Blue UI runtime are authoritative.
