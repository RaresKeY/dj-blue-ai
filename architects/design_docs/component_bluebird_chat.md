# BlueBirdChat

- Path: `ui_ux_team/prototype_r/py_learn.py:840-878` (`InputBlueBird` at `ui_ux_team/prototype_r/py_learn.py:755-803`, `TextBoxAI` at `ui_ux_team/prototype_r/py_learn.py:544-573`)
- Purpose: Simple chat stub with send button + input box; currently echoes messages locally.

## Usage
- Construct and show via `MainUI.open_bluebird_chat` (`ui_ux_team/prototype_r/py_learn.py:1200-1217`).
- Wire outbound messages by connecting `InputBlueBird.message_sent` to a handler; default handler appends to `TextBoxAI`.
- To integrate with an LLM, replace `handle_message` to call your API and render the response to `text_box`.

## Notes
- Styling is dark-themed; adjust in `InputBlueBird.style_settings` and `TextBoxAI` CSS blocks if needed.
- The widget is independent of transcript flow; it can be reused in other windows if you pass a target text box.

