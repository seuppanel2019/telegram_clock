import asyncio
import os
import random
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events
from telethon.errors import (
    AuthKeyUnregisteredError,
    FloodWaitError,
    SessionRevokedError,
    UserDeactivatedError,
)
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest

import fonts

# ---------------------------------------------------------------- config ----
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION")

TIMEZONE = os.environ.get("TIMEZONE", "Asia/Tehran")
NAME_TEXT = os.environ.get("NAME_TEXT", os.environ.get("NAME_PREFIX", "Reza"))
# Template. Placeholders: {name} {time}
TEMPLATE = os.environ.get("TEMPLATE", "{name} | {time}")
# Optional last name (leave empty to keep it blank). Same placeholders.
LAST_NAME_TEMPLATE = os.environ.get("LAST_NAME_TEMPLATE", "")

# Fonts. Use one name, or a comma list to rotate, e.g. "bold,script,fraktur".
# Special value "random" picks any font every time.
NAME_FONT = os.environ.get("NAME_FONT", "bold_italic")
CLOCK_FONT = os.environ.get("CLOCK_FONT", "negative_circled")
# How often (minutes) to switch to the next font when several are listed.
ROTATE_MINUTES = int(os.environ.get("ROTATE_MINUTES", "60"))
# 12 or 24 hour clock.
CLOCK_FORMAT = os.environ.get("CLOCK_FORMAT", "24")
CHECK_SECONDS = 15

missing = [k for k, v in
           {"API_ID": API_ID, "API_HASH": API_HASH, "SESSION": SESSION}.items()
           if not v]
if missing:
    print("Missing environment variables:", ", ".join(missing), flush=True)
    sys.exit(1)

tz = ZoneInfo(TIMEZONE)
client = TelegramClient(StringSession(SESSION), int(API_ID), API_HASH)


def log(*args):
    print(*args, flush=True)


# ----------------------------------------------------------------- state ----
class State:
    """Live settings. Telegram commands change these; env vars are the defaults."""

    def __init__(self):
        self.name = NAME_TEXT
        self.template = TEMPLATE
        self.last_template = LAST_NAME_TEMPLATE
        self.name_fonts = self.parse(NAME_FONT)
        self.clock_fonts = self.parse(CLOCK_FONT)
        self.paused = False

    @staticmethod
    def parse(value):
        value = value.strip().lower()
        if value == "random":
            return ["random"]
        items = [v.strip() for v in value.split(",") if v.strip()]
        items = [v for v in items if v in fonts.FONTS]
        return items or ["normal"]


state = State()


def pick(font_list, slot):
    if font_list == ["random"]:
        return random.Random(slot).choice(fonts.available())
    return font_list[slot % len(font_list)]


def render():
    now = datetime.now(tz)
    slot = int(now.timestamp() // (max(ROTATE_MINUTES, 1) * 60))

    fmt = "%I:%M" if CLOCK_FORMAT == "12" else "%H:%M"
    time_text = now.strftime(fmt)

    name_font = pick(state.name_fonts, slot)
    clock_font = pick(state.clock_fonts, slot)

    def build(template):
        if not template:
            return ""
        text = template.replace("{name}", "\x00").replace("{time}", "\x01")
        # Style only the literal text around the placeholders as plain, then
        # insert the styled name/time so fonts never touch each other's text.
        text = text.replace("\x00", fonts.apply(state.name, name_font))
        text = text.replace("\x01", fonts.apply(time_text, clock_font))
        return text

    first = build(state.template)[:64]
    last = build(state.last_template)[:64]
    key = (first, last)
    return key, time_text, name_font, clock_font


# -------------------------------------------------------------- commands ----
HELP = (
    "Commands (send in Saved Messages):\n"
    "/fonts - list all fonts\n"
    "/preview - preview your name in every font\n"
    "/font <name[,name2,...]|random> - set the name font(s)\n"
    "/clockfont <name[,name2,...]|random> - set the clock font(s)\n"
    "/name <text> - change the name text\n"
    "/template <text> - e.g. /template {name} • {time}\n"
    "/pause - stop updating, /resume - continue\n"
    "/status - show current settings"
)


@client.on(events.NewMessage(chats="me", outgoing=True, pattern=r"^/(\w+)(?:\s+(.*))?$"))
async def commands(event):
    global last_key
    cmd = event.pattern_match.group(1).lower()
    arg = (event.pattern_match.group(2) or "").strip()
    reply = None

    if cmd in ("help", "start"):
        reply = HELP
    elif cmd == "fonts":
        reply = "Fonts:\n" + "\n".join(f"- {n}" for n in fonts.available()) + "\n- random"
    elif cmd == "preview":
        sample = state.name
        lines = [f"{n}: {fonts.apply(sample, n)}  {fonts.apply('09:41', n)}" for n in fonts.available()]
        reply = "\n".join(lines)
    elif cmd == "font":
        if not arg:
            reply = "Usage: /font bold  or  /font bold,script,fraktur  or  /font random"
        else:
            parsed = State.parse(arg)
            state.name_fonts = parsed
            reply = f"Name font: {', '.join(parsed)}"
    elif cmd == "clockfont":
        if not arg:
            reply = "Usage: /clockfont bold  or  /clockfont persian_digits"
        else:
            parsed = State.parse(arg)
            state.clock_fonts = parsed
            reply = f"Clock font: {', '.join(parsed)}"
    elif cmd == "name":
        if arg:
            state.name = arg[:30]
            reply = f"Name text: {state.name}"
        else:
            reply = "Usage: /name Reza"
    elif cmd == "template":
        if arg and ("{time}" in arg or "{name}" in arg):
            state.template = arg
            reply = f"Template: {arg}"
        else:
            reply = "Usage: /template {name} | {time}"
    elif cmd == "pause":
        state.paused = True
        reply = "Paused."
    elif cmd == "resume":
        state.paused = False
        reply = "Resumed."
    elif cmd == "status":
        _, t, nf, cf = render()
        reply = (
            f"name: {state.name}\ntemplate: {state.template}\n"
            f"name font: {nf}\nclock font: {cf}\ntimezone: {TIMEZONE}\n"
            f"paused: {state.paused}"
        )

    if reply:
        await event.reply(reply)
        # Force an immediate refresh after a change.
        last_key = None


# ------------------------------------------------------------------ main ----
last_key = None


async def main():
    global last_key
    await client.connect()

    if not await client.is_user_authorized():
        log("Session is not valid. Generate a new SESSION with generate_session.py")
        sys.exit(1)

    me = await client.get_me()
    log(f"Logged in as: {me.first_name} (id={me.id})")
    log("Send /help in your Saved Messages to see the commands.")

    while True:
        if not state.paused:
            key, time_text, name_font, clock_font = render()
            if key != last_key and key[0]:
                try:
                    await client(UpdateProfileRequest(first_name=key[0], last_name=key[1] or None))
                    last_key = key
                    log(f"Profile updated: {key[0]} {key[1]} [{name_font}/{clock_font}]")
                except FloodWaitError as e:
                    log(f"FloodWait: sleeping {e.seconds}s")
                    await asyncio.sleep(e.seconds + 1)
                    continue
                except (AuthKeyUnregisteredError, SessionRevokedError, UserDeactivatedError):
                    log("Session was revoked or account deactivated. Generate a new SESSION.")
                    sys.exit(1)
                except Exception as e:
                    log("Update failed, retrying:", repr(e))
                    await asyncio.sleep(10)
                    continue

        await asyncio.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    finally:
        client.loop.run_until_complete(client.disconnect())
