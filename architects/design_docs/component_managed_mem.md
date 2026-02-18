# ManagedMem

- **Last Updated: 2026-02-18**
- **Path**: `architects/helpers/managed_mem.py`
- **Purpose**: JSON-backed key/value store for persistent settings and session logging with optional async flushing.

## Usage
- **Basic access**:
  ```python
  from architects.helpers.managed_mem import ManagedMem
  mem = ManagedMem()
  mem.settr("key", {"a": 1})
  value = mem.gettr("key", default={})
  ```
- **Context Manager**: Batches writes and flushes automatically on exit.
- **Logging**: `mem.log("message")` appends to a capped list of events.
- **Async IO**: `mem.enable_async_io()` prevents blocking the UI thread during disk writes.

## Notes
- **Storage**: By default, data is stored in `managed_mem.json` at the project root.
- **Auto-Flush**: Enabled by default; use context manager for high-frequency updates.
- **Quota**: Logs are capped at 500 entries.

