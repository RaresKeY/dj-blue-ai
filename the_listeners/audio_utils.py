"""
Utilities for low-level audio integrations shared across listeners modules.
"""

from __future__ import annotations

import ctypes
import threading
import platform

if platform.system() == "Linux":
    from architects.helpers import record_live_mix_linux as live_mix
else:
    live_mix = None

_ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
)


def _py_error_handler(filename, line, function, err, fmt):  # noqa: D401
    """Dummy handler that swallows ALSA error messages."""
    return None


_c_error_handler = _ERROR_HANDLER_FUNC(_py_error_handler)
_alsa_handler_lock = threading.Lock()
_alsa_handler_set = False


def suppress_alsa_warnings() -> None:
    """
    Install a no-op ALSA error handler to silence noisy stderr messages.

    PortAudio/ALSA tends to emit warnings when probing devices that do not
    exist (common on desktop Linux setups). Suppressing those messages makes
    the CLI output significantly cleaner while keeping normal audio behavior.
    """
    global _alsa_handler_set  # noqa: PLW0603

    if _alsa_handler_set:
        return

    with _alsa_handler_lock:
        if _alsa_handler_set:
            return

        try:
            asound = ctypes.CDLL("libasound.so")
            asound.snd_lib_error_set_handler(_c_error_handler)
            _alsa_handler_set = True
        except OSError:
            # libasound not available; nothing to suppress.
            return
