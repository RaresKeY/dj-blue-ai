from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .base import BaseSystemRecorder
from .linux import create_recorder as create_linux_recorder, supports_recording as linux_supports
from .mac import create_recorder as create_mac_recorder, supports_recording as mac_supports
from .windows import create_recorder as create_windows_recorder, supports_recording as windows_supports


def create_system_recorder(
    *,
    duration: int,
    output_path: Path,
    chunk_frames: int,
    rate: int,
    channels: int,
    monitor_source: Optional[str],
) -> Optional[BaseSystemRecorder]:
    platform_name = sys.platform
    if platform_name.startswith("linux"):
        return create_linux_recorder(
            duration=duration,
            output_path=output_path,
            chunk_frames=chunk_frames,
            rate=rate,
            channels=channels,
            monitor_source=monitor_source,
        )
    if platform_name.startswith("win"):
        return create_windows_recorder(
            duration=duration,
            output_path=output_path,
            chunk_frames=chunk_frames,
            rate=rate,
            channels=channels,
        )
    if platform_name == "darwin":
        return create_mac_recorder(
            duration=duration,
            output_path=output_path,
            chunk_frames=chunk_frames,
            rate=rate,
            channels=channels,
        )
    return None


def platform_supports_system_recording() -> bool:
    platform_name = sys.platform
    if platform_name.startswith("linux"):
        return linux_supports()
    if platform_name.startswith("win"):
        return windows_supports()
    if platform_name == "darwin":
        return mac_supports()
    return False


__all__ = [
    "BaseSystemRecorder",
    "create_system_recorder",
    "platform_supports_system_recording",
]
