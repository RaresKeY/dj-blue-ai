"""Architect helpers package exports."""

from .audio_capture_base import BaseAudioCaptureHelper, DeviceInfo
try:  # Optional dependency
    from .audio_capture_gstreamer import GStreamerAudioCaptureHelper
except ModuleNotFoundError:  # pragma: no cover - optional import
    GStreamerAudioCaptureHelper = None  # type: ignore
from .audio_capture_linux import LinuxAudioCaptureHelper
from .audio_capture_macos import MacOSAudioCaptureHelper
from .audio_capture_sounddevice import SoundDeviceCaptureHelper
from .audio_capture_windows import WindowsAudioCaptureHelper

__all__ = [
    "BaseAudioCaptureHelper",
    "DeviceInfo",
    "LinuxAudioCaptureHelper",
    "MacOSAudioCaptureHelper",
    "SoundDeviceCaptureHelper",
    "WindowsAudioCaptureHelper",
]

__all__ = [name for name in __all__ if globals().get(name) is not None]
