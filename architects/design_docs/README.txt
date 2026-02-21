Design Docs Directory Guide

Purpose
- This folder stores design-time documentation, plans, historical notes, and diagram artifacts.
- These documents are useful for context and planning, but they are not the canonical source for current runtime behavior.

Canonical Source of Truth
- Runtime and implementation truth is maintained in specs:
  - specs/_readme.md
  - specs/product_context.md
  - specs/system_architecture.md
  - specs/domain_logic.md
  - specs/data_model.md
  - specs/quality_testing.md
  - specs/operational_notes.md
- When design docs disagree with specs/code, treat specs (and code) as authoritative.

Folder Structure
- architects/design_docs/
  - Current non-plan design docs and references
- architects/design_docs/plan/
  - Forward-looking plans and proposals (roadmaps, migration plans, build plans, visual plans)
- architects/design_docs/legacy/
  - Historical/deduplicated docs kept for traceability

How To Use This Folder
- For implementation changes:
  1. Read specs first.
  2. Use design docs for rationale/intent and alternatives.
  3. Validate against code before treating any design statement as current behavior.
- For new design proposals:
  - Add proposal docs under architects/design_docs/plan/.
  - Keep assumptions explicit and mark non-implemented ideas clearly.

Diagrams and Images
- Image/diagram files in this folder may be exported from Excalidraw.
- Some images are drag-and-drop exports where scene/state metadata is embedded in the file.

Maintenance Notes
- Prefer moving obsolete docs to architects/design_docs/legacy/ instead of deleting them.
- Keep docs concise and avoid duplicating full runtime behavior that already exists in specs.
