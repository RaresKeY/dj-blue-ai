# ManagedMem

- Path: `architects/helpers/managed_mem.py:1-384`
- Purpose: Singleton JSON-backed key/value store with optional async flush and capped log entries.

## Usage
- Basic set/get:  
  ```python
  mem = ManagedMem()
  mem.settr("key", {"a": 1})
  value = mem.gettr("key", default={})
  ```
- Context manager batches writes and flushes on exit:  
  ```python
  with ManagedMem() as mem:
      mem.settr("k1", 1)
      mem.settr("k2", 2)
  ```
- Logging: `mem.log("message")` (`architects/helpers/managed_mem.py:152-166`).
- Async IO: `mem.enable_async_io()` to queue writes on a worker thread (`architects/helpers/managed_mem.py:88-125,295-322`).

## Notes
- `_auto_flush` defaults to True; reads (`gettr`) still mark dirty and flush, so repeated access can rewrite the JSON file frequently (`architects/helpers/managed_mem.py:126-150,295-334`).
- Stored log is capped at 500 entries and normalized on load (`architects/helpers/managed_mem.py:199-227`).
- Backing file is `managed_mem.json` at repo root; adjust `_file` if you need an alternate path.

