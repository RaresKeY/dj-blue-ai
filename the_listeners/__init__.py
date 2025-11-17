"""
DJ listeners package exports.

The recording worker is the primary API that other parts of the project use.
"""

from .audio_utils import suppress_alsa_warnings
from .device_helpers import (
    pick_default_mic,
    pick_default_speaker,
    resolve_device_params,
    list_all_devices,
    detect_default_monitor,
)
from .dj_the_listeners_final import (
    RECORDINGS_DIR,
    CONFIG_FILE,
    CHUNK,
    FORMAT,
    RATE,
    RECORD_SECONDS,
    RecordingWorker,
    create_worker_with_default_devices,
)

__all__ = [
    "RecordingWorker",
    "RECORDINGS_DIR",
    "CONFIG_FILE",
    "CHUNK",
    "FORMAT",
    "RATE",
    "RECORD_SECONDS",
    "pick_default_mic",
    "pick_default_speaker",
    "list_all_devices",
    "detect_default_monitor",
    "resolve_device_params",
    "create_worker_with_default_devices",
    "suppress_alsa_warnings",
]
