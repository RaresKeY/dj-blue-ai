"""Style helpers for reusable widgets."""

from .tokens import BG_INPUT, BORDER_SUBTLE, FONT_STACK, TEXT_MUTED, TEXT_PRIMARY


def textbox_ai_style() -> str:
    return f"""
    QTextBrowser#TextBox {{
        background-color: #0F0F0F;
        color: {TEXT_MUTED};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 10px;
        padding: 15px;
        font-size: 15px;
        font-weight: 400;
        font-family: {FONT_STACK};
        line-height: 1.4;
        selection-background-color: #3E6AFF;
    }}
    """


def textbox_style() -> str:
    return f"""
    QPlainTextEdit#TextBox {{
        background-color: #0F0F0F;
        color: {TEXT_MUTED};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 10px;
        padding: 10px;
        font-size: 15px;
        font-weight: 600;
        font-family: {FONT_STACK};
        selection-background-color: #3E6AFF;
    }}
    """


def input_style() -> str:
    return f"""
    QTextEdit#InputChat {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 10px;
        padding: 10px;
        font-size: 15px;
        font-family: {FONT_STACK};
        selection-background-color: #3E6AFF;
    }}
    """
