# Operations: UI Iteration Workflow

## Scope
- Required workflow for changing UI components with preview-driven iteration.
- Main docs/tools:
- `ui_ux_team/blue_ui/docs/UI_WORKFLOW.md`
- `ui_ux_team/blue_ui/tests/iteration/README.md`
- `ui_ux_team/blue_ui/previews/ui_iterate.py`
- `ui_ux_team/blue_ui/previews/run_preview.py`
- `ui_ux_team/blue_ui/docs/ui_complete_reference.md`

## Required Iteration Pattern
- Scaffold dev component and preview module through UI iteration tooling.
- Iterate visuals via preview runner rather than editing production view blindly.
- Capture deterministic snapshots (`ui_iterate.py snap`) before integration.
- Integrate verified component behavior back into production views/widgets.

## Iteration Directories
- Dev scaffolds: `ui_ux_team/blue_ui/tests/iteration/dev/`
- Preview scaffolds: `ui_ux_team/blue_ui/previews/iteration/`
- Visual audit snapshots and reports live under UI preview/testing docs and artifacts.

## QA Positioning
- Iteration workflow supports manual visual QA and geometry validation.
- Core automated UI tests remain smoke/click oriented; visual QA is workflow-driven rather than strict CI gate.

## Key Invariants
- UI workflow docs and iteration tooling are canonical for visual iteration.
- Production UI modules should only absorb changes validated through preview/snapshot cycle.
