"""Utilities for encoding and decoding Song objects for JSON persistence.

This module provides two helpers that ManagedMem can use when writing its
snapshot to disk and when loading it back. The helpers walk the managed
memory structure and replace any Song instances with a JSON-friendly payload
that captures their state, and later recreate Song objects from that payload.

The functions are written to avoid circular imports: the Song class is only
imported the first time it is actually needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Type

TYPE_KEY = "__type__"
SONG_TYPE = "Song"
_SONG_CLASS: Optional[Type[Any]] = None
_SKIP_ATTRS = {"mem_man"}


def make_json_safe(value: Any) -> Any:
    """Return a JSON-serializable representation of ``value``.

    The function walks the object tree and replaces Song instances with a
    tagged dictionary so the default ``json`` module can persist them.
    """

    song_cls = _get_song_class()
    if song_cls and isinstance(value, song_cls):
        return _song_to_payload(value)
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def restore_from_json(value: Any, *, mem_ref: Any = None) -> Any:
    """Recreate Song objects from JSON payloads produced by ``make_json_safe``."""

    if isinstance(value, dict):
        if value.get(TYPE_KEY) == SONG_TYPE:
            return _payload_to_song(value, mem_ref=mem_ref)
        return {k: restore_from_json(v, mem_ref=mem_ref) for k, v in value.items()}
    if isinstance(value, list):
        return [restore_from_json(item, mem_ref=mem_ref) for item in value]
    return value


def _song_to_payload(song: Any) -> Dict[str, Any]:
    state: Dict[str, Any] = {}
    for key, val in getattr(song, "__dict__", {}).items():
        if key in _SKIP_ATTRS:
            continue
        state[key] = make_json_safe(val)
    return {TYPE_KEY: SONG_TYPE, "state": state}


def _payload_to_song(payload: Dict[str, Any], *, mem_ref: Any = None) -> Any:
    song_cls = _get_song_class()
    if song_cls is None:
        # Song cannot be imported (likely due to early import order). Give the
        # caller the raw payload so nothing is lost.
        return payload

    song = song_cls.__new__(song_cls)
    state = payload.get("state", {})
    for key, val in state.items():
        restored = restore_from_json(val, mem_ref=mem_ref)
        if key == "filepath" and isinstance(restored, str):
            restored = Path(restored)
        setattr(song, key, restored)

    if getattr(song, "mem_man", None) is None and mem_ref is not None:
        song.mem_man = mem_ref
    return song


def _get_song_class() -> Optional[Type[Any]]:
    global _SONG_CLASS
    if _SONG_CLASS is None:
        try:
            from architects.song import Song as SongClass  # type: ignore

            _SONG_CLASS = SongClass
        except Exception:
            return None
    return _SONG_CLASS
