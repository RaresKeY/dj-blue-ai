"""Best-effort native title bar appearance sync for light/dark themes.

This intentionally avoids custom title bars; it only applies OS-level hints where available.
"""

from __future__ import annotations

import ctypes
import platform

from PySide6.QtWidgets import QWidget

from .manager import current_theme_key, is_theme_dark


def apply_native_titlebar_for_theme(widget: QWidget | None, theme_key: str | None = None) -> bool:
    dark = is_theme_dark(theme_key or current_theme_key())
    system = platform.system()
    if system == "Windows":
        return _apply_windows_titlebar(widget, dark)
    if system == "Darwin":
        return _apply_macos_appearance(dark)
    # Linux/other: keep default behavior.
    return False


def _apply_windows_titlebar(widget: QWidget | None, dark: bool) -> bool:
    if widget is None:
        return False
    try:
        hwnd = int(widget.winId())
    except Exception:
        return False
    if hwnd <= 0:
        return False
    try:
        value = ctypes.c_int(1 if dark else 0)
        attrs = (20, 19)  # DWMWA_USE_IMMERSIVE_DARK_MODE + fallback
        dwm = ctypes.windll.dwmapi
        ok = False
        for attr in attrs:
            res = int(
                dwm.DwmSetWindowAttribute(
                    ctypes.c_void_p(hwnd),
                    ctypes.c_uint(attr),
                    ctypes.byref(value),
                    ctypes.sizeof(value),
                )
            )
            ok = ok or (res == 0)
        return ok
    except Exception:
        return False


def _apply_macos_appearance(dark: bool) -> bool:
    try:
        libobjc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        ctypes.cdll.LoadLibrary("/System/Library/Frameworks/AppKit.framework/AppKit")

        objc_getClass = libobjc.objc_getClass
        objc_getClass.restype = ctypes.c_void_p
        objc_getClass.argtypes = [ctypes.c_char_p]

        sel_registerName = libobjc.sel_registerName
        sel_registerName.restype = ctypes.c_void_p
        sel_registerName.argtypes = [ctypes.c_char_p]

        objc_msgSend = libobjc.objc_msgSend
        objc_msgSend.restype = ctypes.c_void_p

        def _send(receiver, selector, *args):
            return objc_msgSend(receiver, selector, *args)

        def _nsstring(text: str):
            nsstring_cls = objc_getClass(b"NSString")
            sel = sel_registerName(b"stringWithUTF8String:")
            return _send(nsstring_cls, sel, ctypes.c_char_p(text.encode("utf-8")))

        app_cls = objc_getClass(b"NSApplication")
        shared_app = _send(app_cls, sel_registerName(b"sharedApplication"))
        if not shared_app:
            return False

        appearance_cls = objc_getClass(b"NSAppearance")
        appearance_name = "NSAppearanceNameDarkAqua" if dark else "NSAppearanceNameAqua"
        appearance_obj = _send(
            appearance_cls,
            sel_registerName(b"appearanceNamed:"),
            _nsstring(appearance_name),
        )
        if not appearance_obj:
            return False

        _send(shared_app, sel_registerName(b"setAppearance:"), appearance_obj)
        return True
    except Exception:
        return False

