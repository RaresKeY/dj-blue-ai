# <project_name> - Specs Index

**Tech Stack**: <language/framework/runtime>

---

**IMPORTANT** Before making changes or researching any part of the codebase, use the table below to find and read the relevant spec first. This ensures you understand existing patterns and constraints.

## Documentation

| Spec | Code | Purpose |
|------|------|---------|
| [Product Context](product_context.template.md) | `<app entrypoints>` | Product goals, personas, constraints, and non-goals. |
| [System Architecture](system_architecture.template.md) | `<root modules>` | Entry point, module boundaries, and runtime data flow. |
| [Domain Logic](domain_logic.template.md) | `<core domain files>` | Business/game/domain rules and invariants. |
| [Data Model](data_model.template.md) | `<schema/models>` | Data entities, relationships, storage format, and migrations. |
| [Quality & Testing](quality_testing.template.md) | `<tests/, ci, tooling>` | Test strategy, quality gates, and release confidence checks. |
| [Operational Notes](operational_notes.template.md) | `<deploy/runtime config>` | Environment setup, observability, and runbook notes. |
