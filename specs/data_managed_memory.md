# Data: Managed Memory

## Scope
- `ManagedMem` singleton storage contract and persistence behavior.
- Main implementation file:
- `architects/helpers/managed_mem.py`

## Core Contract
- Singleton instance (`ManagedMem._instance`) with thread-safe mutation (`RLock`).
- Backing file is resolved to `user_config_dir()/managed_mem.json`.
- If needed, old `runtime_base_dir()/managed_mem.json` is copied into new path during initialization.

## Data Access API
- `settr(key, value)` writes key/value and appends log entry.
- `gettr(key, default=None)` reads key and appends log entry.
- `log(message, persist=True, ensure_loaded=True)` appends structured log entry.
- `flush(wait=True)` forces persistence of dirty state.
- Context manager (`with ManagedMem() as mem`) disables auto flush during block, then flushes on exit.

## Logging Contract
- Log list key: `log`.
- Entry fields include:
- `date` (UTC ISO string, seconds precision)
- `command` (for example `SET`, `GET`, `LOG`)
- optional `message`, `key`, `value`
- Log is capped to `_log_cap = 500`; older entries are pruned.
- Legacy string log entries are normalized into dict entries on load.

## Persistence & IO Modes
- Default mode is synchronous writes.
- Async mode is optional via `enable_async_io()` and background queue/thread.
- `disable_async_io(wait=True)` flushes and joins worker resources.
- Serialization/deserialization uses `jsonrules_song.make_json_safe` and `restore_from_json`.

## Key Invariants
- Managed memory is process-wide singleton state.
- Mutation methods both update in-memory data and operational logs.
- Persistence path is user-config scoped in current architecture.
