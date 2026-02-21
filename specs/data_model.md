# Data Model

This file is now the data-contract index. Detailed contracts are split into focused specs:

- [Data: Settings & Runtime Paths](data_settings_and_runtime_paths.md)
- [Data: Managed Memory](data_managed_memory.md)
- [Data: Legacy & Auxiliary Contracts](data_legacy_and_auxiliary_contracts.md)

## Scope Split Rationale
- Settings/runtime paths are a stable, app-wide schema and path policy.
- Managed memory is a separate singleton persistence subsystem.
- Song/transcriber/prototype artifacts are legacy or auxiliary contracts and should not be mixed with primary Blue UI runtime contracts.

## High-Level Invariants
- Source of truth for active runtime contracts is `ui_ux_team/blue_ui/` plus imported helpers.
- Local persistence is JSON/keyring based; there is no DB migration layer.
- Legacy contracts remain documented, but are explicitly marked non-primary runtime paths.
