"""
Checks Telegram once for any new /dinner, /next, or /another messages, replies
to them, and exits. Designed to be run every 5 minutes by the "Dinner Bot
Commands" GitHub Actions workflow (.github/workflows/respond-commands.yml) --
GitHub doesn't allow anything shorter than a 5-minute schedule interval, so
replies land within roughly that window rather than instantly.

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment (GitHub
Actions injects these from repository secrets). Only messages from that
chat ID are answered. No third-party dependencies (stdlib only).

State (the Telegram update offset, and which recipes /another has already
shown today) lives in state.json, committed back to the repo by the
workflow after each run -- see state_store.py.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime

from recipe_utils import TIMEZONE, format_recipe, pick_another, record_shown, recipe_for_date
from state_store import load_state, save_state

HELP_TEXT = (
    "Hi! I'm your PersonalChef dinner bot.\n\n"
    "Every morning at 07:00 CET you'll get a dinner recipe with full macros "
    "(sent automatically by a separate scheduled job).\n"
    "You can also ask any time (replies land within a few minutes):\n"
    "/dinner — today's dinner recipe\n"
    "/next — preview tomorrow's dinner recipe\n"
    "/another — not feeling today's suggestion? get a different one"
)


def api_call(token: str, method: str, params: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def send_message(token: str, chat_id: str, text: str) -> None:
    body = api_call(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    })
    if not body.get("ok"):
        print(f"Telegram sendMessage error: {body}", file=sys.stderr)


def main() -> int:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    today = datetime.now(TIMEZONE).date()

    state = load_state()
    offset = state.get("last_update_id", 0) + 1

    resp = api_call(token, "getUpdates", {"offset": offset, "timeout": 0})
    if not resp.get("ok"):
        print(f"Telegram getUpdates error: {resp}", file=sys.stderr)
        return 1

    updates = resp["result"]
    if not updates:
        print("No new messages.")
        return 0

    changed = False
    for update in updates:
        state["last_update_id"] = update["update_id"]
        changed = True

        message = update.get("message") or update.get("edited_message")
        if not message or "text" not in message:
            continue
        if str(message["chat"]["id"]) != str(chat_id):
            print(f"Ignoring message from unrecognized chat_id={message['chat']['id']}")
            continue

        command = message["text"].strip().split("@")[0].lower()

        if command == "/start":
            send_message(token, chat_id, HELP_TEXT)
        elif command == "/dinner":
            recipe = recipe_for_date(today)
            record_shown(state, today, recipe["id"])
            send_message(token, chat_id, format_recipe(recipe, "Today's Dinner"))
        elif command == "/next":
            from datetime import timedelta
            recipe = recipe_for_date(today + timedelta(days=1))
            send_message(token, chat_id, format_recipe(recipe, "Tomorrow's Dinner (Preview)"))
        elif command == "/another":
            choice = pick_another(state, today)
            send_message(token, chat_id, format_recipe(choice, "Here's Another Option"))
        elif command.startswith("/"):
            send_message(token, chat_id, "Try /dinner, /next, or /another.")
        else:
            print(f"Ignoring non-command message: {message['text']!r}")

    if changed:
        save_state(state)
        print(f"Processed {len(updates)} update(s); state saved.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
