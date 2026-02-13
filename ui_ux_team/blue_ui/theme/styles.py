"""Style helpers for reusable widgets."""

from . import tokens


def textbox_ai_style() -> str:
    return f"""
    QTextBrowser#TextBox {{
        background-color: #0D1320;
        color: {tokens.TEXT_MUTED};
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
        background-color: #0D1320;
        color: {tokens.TEXT_MUTED};
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
