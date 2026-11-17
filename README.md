# Telegram name clock

## Railway variables
Required: API_ID, API_HASH, SESSION

Optional:
- NAME_TEXT     (default Reza)
- TEMPLATE      (default "{name} | {time}")
- LAST_NAME_TEMPLATE (default empty)
- NAME_FONT     (default bold_italic) one name, a comma list to rotate, or "random"
- CLOCK_FONT    (default negative_circled) e.g. bold, monospace, persian_digits
- ROTATE_MINUTES (default 60) how often to switch when several fonts are listed
- CLOCK_FORMAT  24 or 12
- TIMEZONE      (default Asia/Tehran)

## Live commands (send in Saved Messages)
/help /fonts /preview /font <name> /clockfont <name> /name <text> /template <text> /pause /resume /status
Changes made by commands reset to the Railway variables when the service restarts.
