"""
Simple example:
----------------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from architects.helpers.managed_mem import ManagedMem

with ManagedMem() as mem:
    mem.settr("key", "value")
    read_value = mem.gettr("key")
"""

import ast
import json
import os
import queue
import threading
from datetime import datetime
from typing import Any, List, Optional

from .jsonrules_song import make_json_safe, restore_from_json

""" 
Complex Usage:
---------------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from architects.helpers.managed_mem import ManagedMem

# Synchronous usage
mem = ManagedMem()
mem.settr("session_id", "abc123")
value = mem.gettr("session_id")
mem.log("manual entry")

# Batched updates with explicit flush
with ManagedMem() as mem_ctx:
    for i in range(5):
        mem_ctx.settr(f"key_{i}", i)
    mem_ctx.log("batch done", persist=False)
# exiting the context flushes pending updates

# Enable async persistence if logging becomes frequent
mem.enable_async_io()
mem.settr("heavy_key", {"payload": "value"})
mem.flush()  # ensure background writes complete
mem.close()  # stop the worker thread

The `log` list is capped at 500 entries; older entries are pruned automatically.
"""

class ManagedMem:
    _instance: Optional["ManagedMem"] = None
    _lock: threading.RLock = threading.RLock()
    _file: str = "managed_mem.json"
    _log_cap: int = 500

    _mem: dict
    _is_loaded: bool
    _dirty: bool
    _auto_flush: bool
    _use_async_io: bool
    _write_queue: Optional[queue.Queue]
    _writer_thread: Optional[threading.Thread]
    _async_exception: Optional[BaseException]
    _context_stack: List[bool]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mem = {}
            cls._instance._is_loaded = False
            cls._instance._dirty = False
            cls._instance._auto_flush = True
            cls._instance._use_async_io = False
            cls._instance._write_queue = None
            cls._instance._writer_thread = None
            cls._instance._async_exception = None
            cls._instance._context_stack = []
            cls._instance._load()
        return cls._instance

    def set_auto_flush(self, enabled: bool) -> None:
        """Enable or disable automatic flushing after mutations."""
        with self._lock:
            self._auto_flush = bool(enabled)

    def enable_async_io(self) -> None:
        """Switch persistence to use the background writer thread."""
        with self._lock:
            if not self._use_async_io:
                self._use_async_io = True
                self._ensure_async_writer_locked()

    def disable_async_io(self, wait: bool = True) -> None:
        """Stop using the background writer and optionally wait for completion."""
        if not self._use_async_io and self._write_queue is None:
            return

        self.flush(wait=True)

        queue_ref = None
        worker = None
        with self._lock:
            queue_ref = self._write_queue
            worker = self._writer_thread
            self._use_async_io = False
        if queue_ref is not None:
            queue_ref.put(None)
            if wait:
                queue_ref.join()
        if worker and wait:
            worker.join()
        with self._lock:
            if queue_ref is not None:
                self._write_queue = None
                self._writer_thread = None
        if wait:
            self._check_async_exception()

    def settr(self, key, value):
        """Store a value in the managed memory."""
        queue_to_wait = None
        with self._lock:
            self._load()
            self._mem[key] = value
            self._append_log_unlocked(command="SET", key=key, value=value)
            queue_to_wait = self._mark_dirty_locked(wait=not self._use_async_io)
        if queue_to_wait:
            queue_to_wait.join()
            self._check_async_exception()
        return value

    def gettr(self, key, default=None):
        """Retrieve a value from managed memory."""
        queue_to_wait = None
        with self._lock:
            self._load()
            value = self._mem.get(key, default)
            self._append_log_unlocked(command="GET", key=key, value=value)
            queue_to_wait = self._mark_dirty_locked(wait=not self._use_async_io)
        if queue_to_wait:
            queue_to_wait.join()
            self._check_async_exception()
        return value

    def log(self, message, *, persist=True, ensure_loaded=True):
        """Append a log entry safely and optionally persist."""
        queue_to_wait = None
        with self._lock:
            if ensure_loaded:
                self._load()
            entries = self._append_log_unlocked(command="LOG", message=message)
            queue_to_wait = self._mark_dirty_locked(
                flush=persist, wait=True
            )
        if queue_to_wait:
            queue_to_wait.join()
            self._check_async_exception()
        return entries

    def flush(self, wait: bool = True) -> None:
        """Persist pending changes to disk, blocking until complete when requested."""
        queue_to_wait = None
        with self._lock:
            queue_to_wait = self._flush_locked(wait=wait)
        if queue_to_wait:
            queue_to_wait.join()
        if wait:
            self._check_async_exception()

    def close(self) -> None:
        """Flush any pending changes and stop async resources."""
        self.flush(wait=True)
        self.disable_async_io(wait=True)

    def __enter__(self):
        with self._lock:
            self._context_stack.append(self._auto_flush)
            self._auto_flush = False
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.flush(wait=True)
        finally:
            with self._lock:
                if self._context_stack:
                    self._auto_flush = self._context_stack.pop()
        return False

    # --- Internal helpers -------------------------------------------------

    def _append_log_unlocked(self, *, command: str, message: Optional[str] = None, **fields: Any):
        """Internal helper: caller must hold `_lock` before calling."""
        log_entries: list = self._mem.setdefault("log", [])
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        entry = {"date": timestamp, "command": command}
        if message is not None:
            entry["message"] = message
        if fields:
            entry.update(fields)
        log_entries.append(entry)
        if len(log_entries) > self._log_cap:
            del log_entries[:-self._log_cap]
        return log_entries

    def _normalize_log_entries_locked(self) -> None:
        log_entries = self._mem.get("log")
        if log_entries is None:
            self._mem["log"] = []
            return
        if not isinstance(log_entries, list):
            self._mem["log"] = [self._convert_legacy_log_entry(log_entries)]
            return
        if not log_entries:
            return
        normalized = [self._convert_legacy_log_entry(entry) for entry in log_entries]
        if len(normalized) > self._log_cap:
            normalized = normalized[-self._log_cap :]
        self._mem["log"] = normalized

    def _convert_legacy_log_entry(self, entry: Any) -> dict:
        if isinstance(entry, dict):
            entry = dict(entry)  # copy to avoid mutations on shared refs
            entry.setdefault("date", None)
            if "command" not in entry:
                entry["command"] = "LOG" if "message" in entry else None
            return entry
        if isinstance(entry, str):
            return self._parse_legacy_log_string(entry)
        return {"date": None, "command": "UNKNOWN", "message": repr(entry)}

    def _parse_legacy_log_string(self, raw: str) -> dict:
        raw = raw.strip()
        if not raw:
            return {"date": None, "command": "LOG"}

        timestamp = None
        command = "LOG"
        message = ""
        key: Optional[str] = None
        value: Any = None

        parts = raw.split(" ", 2)
        if len(parts) >= 2 and self._looks_like_iso_timestamp(parts[0]):
            timestamp = parts[0]
            potential_command = parts[1].upper()
            remainder = parts[2] if len(parts) > 2 else ""
            if potential_command in {"SET", "GET"}:
                command = potential_command
                if remainder and " -> " in remainder:
                    key_part, raw_value = remainder.split(" -> ", 1)
                    key = key_part.strip()
                    raw_value = raw_value.strip()
                    value = self._safe_literal_eval(raw_value)
                else:
                    message = remainder.strip()
            elif potential_command == "LOG":
                command = potential_command
                message = remainder.strip()
            else:
                message = f"{potential_command.lower()} {remainder}".strip()
        else:
            message = raw

        entry = {"date": timestamp, "command": command}
        if key is not None:
            entry["key"] = key
        if value is not None:
            entry["value"] = value
        if message:
            entry["message"] = message
        return entry

    def _safe_literal_eval(self, value: str) -> Any:
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    @staticmethod
    def _looks_like_iso_timestamp(value: str) -> bool:
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

    def _mark_dirty_locked(self, *, flush=None, wait=True):
        """Mark the in-memory state as dirty and optionally flush."""
        self._dirty = True
        if flush is None:
            flush = self._auto_flush
        if flush:
            return self._flush_locked(wait=wait)
        return None

    def _flush_locked(self, *, wait=True):
        """Flush while holding the internal lock."""
        queue_to_wait = None
        if not self._dirty and wait and self._use_async_io and self._write_queue:
            return self._write_queue

        if not self._dirty:
            return None

        snapshot = self._serialize_mem_locked()
        if self._use_async_io:
            self._ensure_async_writer_locked()
            self._write_queue.put(snapshot)
            if wait:
                queue_to_wait = self._write_queue
        else:
            self._write_snapshot(snapshot)
        self._dirty = False
        return queue_to_wait

    def _serialize_mem_locked(self) -> str:
        snapshot = make_json_safe(self._mem)
        return json.dumps(snapshot, indent=2, ensure_ascii=False)

    def _write_snapshot(self, snapshot: str) -> None:
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                f.write(snapshot)
        except Exception as exc:
            raise RuntimeError("ManagedMem failed to write to disk") from exc

    def _ensure_async_writer_locked(self) -> None:
        if self._write_queue is None:
            self._write_queue = queue.Queue()
            self._writer_thread = threading.Thread(
                target=self._async_writer_loop,
                args=(self._write_queue,),
                daemon=True,
            )
            self._writer_thread.start()

    def _async_writer_loop(self, work_queue: queue.Queue) -> None:
        while True:
            snapshot = work_queue.get()
            if snapshot is None:
                work_queue.task_done()
                break
            try:
                self._write_snapshot(snapshot)
            except Exception as exc:
                with self._lock:
                    self._async_exception = exc
            finally:
                work_queue.task_done()

    def _check_async_exception(self) -> None:
        with self._lock:
            exc = self._async_exception
            self._async_exception = None
        if exc:
            raise RuntimeError("ManagedMem async writer failure") from exc

    def _load(self):
        """Load managed memory from disk if present."""
        if not getattr(self, "_is_loaded", False):
            if os.path.exists(self._file):
                try:
                    with open(self._file, "r", encoding="utf-8") as f:
                        raw_mem = json.load(f)
                        self._mem = restore_from_json(raw_mem, mem_ref=self)
                except json.JSONDecodeError:
                    print(
                        "[ManagedMem] Warning: corrupted JSON file — resetting memory."
                    )
                    self._mem = {}
            else:
                self._mem = {}
            self._normalize_log_entries_locked()
            self._dirty = False
            self._is_loaded = True
        return self._mem
