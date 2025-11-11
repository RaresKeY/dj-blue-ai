"""
Helpers for enumerating PyAudio devices and selecting defaults for recording.

These utilities centralize the logic for discovering microphone (SELF) and
speaker/loopback (OTHERS) device IDs so other modules only need to import
from here when wiring the recording worker.
"""

from __future__ import annotations

from typing import Dict, Iterator, Optional

import pyaudio

LOOPBACK_HINTS = ("loopback", "monitor", "stereo mix", "what u hear")


def _iter_devices(pa: pyaudio.PyAudio) -> Iterator[Dict]:
    """Yield each device info dict augmented with its index."""
    for idx in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(idx)
        info["index"] = idx
        yield info


def pick_default_mic(pa: pyaudio.PyAudio) -> Dict:
    """Return the best-guess microphone device info."""
    try:
        return pa.get_default_input_device_info()
    except OSError:
        pass

    for info in _iter_devices(pa):
        if info.get("maxInputChannels", 0) > 0:
            return info

    raise RuntimeError("No input devices available for microphone capture.")


def pick_default_speaker(pa: pyaudio.PyAudio) -> Optional[Dict]:
    """
    Return the best-guess speaker (loopback/monitor) device info.

    On Linux and other hosts where no loopback capture exists by default,
    this function will return None so that callers can gracefully skip the
    OTHERS channel instead of hammering ALSA with invalid devices.
    """
    loopback_candidate: Optional[Dict] = None

    for info in _iter_devices(pa):
        name = info.get("name", "").lower()
        has_input = info.get("maxInputChannels", 0) > 0

        if info.get("isLoopbackDevice"):
            loopback_candidate = info
            break

        if has_input and any(hint in name for hint in LOOPBACK_HINTS):
            loopback_candidate = info
            break

    return loopback_candidate


def resolve_device_params(duration: int) -> Dict[str, int | str | None]:
    """
    Inspect PyAudio devices and return IDs/names suitable for `RecordingWorker`.

    Returns:
        dict with mic_id, mic_name, speaker_id, speaker_name, duration
    """
    pa = pyaudio.PyAudio()
    try:
        mic_info = pick_default_mic(pa)
        speaker_info = pick_default_speaker(pa)

        params: Dict[str, int | str | None] = {
            "mic_id": int(mic_info["index"]),
            "mic_name": mic_info["name"],
            "duration": duration,
        }

        if speaker_info is not None:
            params["speaker_id"] = int(speaker_info["index"])
            params["speaker_name"] = speaker_info["name"]
        else:
            params["speaker_id"] = None
            params["speaker_name"] = ""

        return params
    finally:
        pa.terminate()
