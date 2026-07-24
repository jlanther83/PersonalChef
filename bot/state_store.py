"""
Tiny shared state file (bot/state.json), used by both bot.py (interactive)
and poll_once.py (GitHub Actions). Tracks:
- last_update_id: Telegram getUpdates offset, so poll_once.py never re-reads
  the same message twice (only meaningful for poll_once.py)
- shown_today: which recipes /dinner or /another has already shown today

No chat ID or token lives here -- those come from the TELEGRAM_BOT_TOKEN /
TELEGRAM_CHAT_ID secrets/env instead, since this file is committed to a
public repo by the GitHub Actions workflow.
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "state.json")


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH) as fh:
        return json.load(fh)


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
