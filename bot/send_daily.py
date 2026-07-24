"""
Sends today's dinner recipe via the raw Telegram HTTP API. No third-party
dependencies (stdlib only), so GitHub Actions can run it with a bare
Python install -- no pip install step needed.

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment
(GitHub Actions injects these from repository secrets).

The workflow runs this at both 05:00 and 06:00 UTC to cover CET and CEST
without needing to change the cron twice a year; this script only actually
sends when the current Europe/Berlin local time is 07:00, so exactly one
of those two runs does anything each day.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime

from recipe_utils import TIMEZONE, format_recipe, recipe_for_date


def main() -> int:
    now = datetime.now(TIMEZONE)
    forced = os.environ.get("FORCE_SEND") == "true"
    if now.hour != 7 and not forced:
        print(f"Local time is {now.isoformat()} (hour={now.hour}), not the 07:00 window; skipping.")
        return 0
    if forced:
        print(f"FORCE_SEND set (manual run) -- sending now regardless of local hour ({now.isoformat()}).")

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    recipe = recipe_for_date(now.date())
    text = format_recipe(recipe, "Today's Dinner")

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read().decode())
        if not body.get("ok"):
            print(f"Telegram API error: {body}", file=sys.stderr)
            return 1
        print(f"Sent recipe '{recipe['id']}' to chat_id={chat_id}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
