"""
Helpers for enumerating PyAudio devices and selecting defaults for recording.

These utilities centralize the logic for discovering microphone (SELF) and
speaker/loopback (OTHERS) device IDs so other modules only need to import
from here when wiring the recording worker.
"""

from __future__ import annotations

import subprocess
from typing import Dict, Iterator, List, Optional

import pyaudio

from .alsa_suppres import suppress_alsa_warnings

suppress_alsa_warnings()
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


def detect_default_monitor() -> Optional[Dict[str, str]]:
    """Return metadata about the PulseAudio default sink monitor (if available)."""

    def _default_sink() -> Optional[str]:
        commands = (
            ["pactl", "get-default-sink"],
            ["pactl", "info"],
        )
        for cmd in commands:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            except FileNotFoundError:
                return None
            if cmd[-1] == "info":
                for line in proc.stdout.splitlines():
                    if line.lower().startswith("default sink:"):
                        value = line.split(":", 1)[1].strip()
                        if value:
                            return value
            else:
                value = proc.stdout.strip()
                if value:
                    return value
        return None

    sink_name = _default_sink()
    if not sink_name:
        return None

    monitor_name = f"{sink_name}.monitor"
    try:
        proc = subprocess.run(
            ["pactl", "list", "sources"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return None

    description: Optional[str] = None
    current_name: Optional[str] = None
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if line.startswith("Source #"):
            current_name = None
            continue
        if line.startswith("Name:"):
            current_name = line.split(":", 1)[1].strip()
        elif line.startswith("Description:") and current_name == monitor_name:
            description = line.split(":", 1)[1].strip()
            break

    return {"name": monitor_name, "description": description or monitor_name}


def list_all_devices() -> List[Dict[str, int | str | bool]]:
    """Return a snapshot of every audio device PyAudio reports."""
    pa = pyaudio.PyAudio()
    devices: List[Dict[str, int | str | bool]] = []
    monitor_info = detect_default_monitor()
    monitor_desc = monitor_info.get("description") if monitor_info else None
    try:
        for info in _iter_devices(pa):
            name = info.get("name", "")
            normalized_name = name.strip().lower()
            is_default_monitor = False
            if monitor_desc:
                monitor_norm = monitor_desc.strip().lower()
                is_default_monitor = bool(
                    monitor_norm
                    and (
                        normalized_name == monitor_norm
                        or monitor_norm in normalized_name
                        or normalized_name in monitor_norm
                    )
                )
            devices.append(
                {
                    "index": int(info["index"]),
                    "name": name,
                    "max_input_channels": int(info.get("maxInputChannels", 0)),
                    "max_output_channels": int(info.get("maxOutputChannels", 0)),
                    "host_api": int(info.get("hostApi", -1)),
                    "is_default_monitor": is_default_monitor,
                }
            )
        return devices
    finally:
        pa.terminate()


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

        if speaker_info is None:
            try:
                speaker_info = pa.get_default_output_device_info()
            except OSError:
                speaker_info = None

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
