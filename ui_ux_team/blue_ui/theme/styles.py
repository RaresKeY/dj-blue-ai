"""Style helpers for reusable widgets."""

import re

from . import tokens


def _with_alpha(color: str, alpha: float) -> str:
    a = max(0.0, min(1.0, float(alpha)))
    c = (color or "").strip()
    if c.startswith("#") and len(c) in (4, 7):
        if len(c) == 4:
            r = int(c[1] * 2, 16)
            g = int(c[2] * 2, 16)
            b = int(c[3] * 2, 16)
        else:
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
        return f"rgba({r}, {g}, {b}, {a:.3f})"

    match = re.match(r"rgba?\(([^)]+)\)", c)
    if match:
        parts = [p.strip() for p in match.group(1).split(",")]
        if len(parts) >= 3:
            return f"rgba({parts[0]}, {parts[1]}, {parts[2]}, {a:.3f})"
    return c


def textbox_ai_style() -> str:
    return f"""
    QTextBrowser#TextBox {{
        background-color: {_with_alpha(tokens.BG_INPUT, 0.96)};
        color: {tokens.TEXT_PRIMARY};
        border: 1px solid {tokens.BORDER_SUBTLE};
        border-radius: 10px;
        padding: 15px;
        font-size: 15px;
        font-weight: 400;
        font-family: {tokens.FONT_STACK};
        line-height: 1.4;
        selection-background-color: {tokens.PRIMARY};
    }}
    """


def textbox_style() -> str:
    return f"""
    QPlainTextEdit#TextBox {{
        background-color: {_with_alpha(tokens.BG_INPUT, 0.96)};
        color: {tokens.TEXT_PRIMARY};
        border: 1px solid {tokens.BORDER_SUBTLE};
        border-radius: 10px;
        padding: 10px;
        font-size: 15px;
        font-weight: 600;
        font-family: {tokens.FONT_STACK};
        selection-background-color: {tokens.PRIMARY};
    }}
    """


def input_style() -> str:
    return f"""
    QTextEdit#InputChat {{
        background-color: {tokens.BG_INPUT};
        color: {tokens.TEXT_PRIMARY};
        border: 1px solid {tokens.BORDER_SUBTLE};
        border-radius: 10px;
        padding: 10px;
        font-size: 15px;
        font-family: {tokens.FONT_STACK};
        selection-background-color: {tokens.PRIMARY};
    }}
    """
