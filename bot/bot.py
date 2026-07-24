"""
PersonalChef Telegram bot -- on-demand side.

Answers /dinner, /next, and /another whenever this process is running. The
automatic 07:00 CET daily push is handled separately and independently by
the GitHub Actions workflow (.github/workflows/daily-dinner.yml) via
send_daily.py, so it keeps working even when this process isn't running.

Run: python3 bot.py   (reads TELEGRAM_BOT_TOKEN from .env or the environment)
"""
import json
import logging
import os
import random
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from recipe_utils import RECIPES, TIMEZONE, format_recipe, recipe_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("personalchef-bot")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(BASE_DIR, "subscriber.json")


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH) as fh:
        return json.load(fh)


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as fh:
        json.dump(state, fh)


def save_chat_id(chat_id: int) -> None:
    state = load_state()
    state["chat_id"] = chat_id
    save_state(state)


def _today() -> date:
    return datetime.now(TIMEZONE).date()


def _shown_today(state: dict) -> list:
    shown = state.get("shown_today")
    if not shown or shown.get("date") != _today().isoformat():
        return []
    return shown.get("ids", [])


def _record_shown(state: dict, recipe_id: str) -> None:
    ids = _shown_today(state)
    if recipe_id not in ids:
        ids.append(recipe_id)
    state["shown_today"] = {"date": _today().isoformat(), "ids": ids}
    save_state(state)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "Hi! I'm your PersonalChef dinner bot.\n\n"
        "Every morning at 07:00 CET you'll get a dinner recipe with full macros "
        "(sent automatically by a separate scheduled job).\n"
        "You can also ask any time this bot is running:\n"
        "/dinner — today's dinner recipe\n"
        "/next — preview tomorrow's dinner recipe\n"
        "/another — not feeling today's suggestion? get a different one"
    )
    log.info("Registered subscriber chat_id=%s", update.effective_chat.id)


async def dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    recipe = recipe_for_date(_today())
    _record_shown(state, recipe["id"])
    await update.message.reply_markdown(format_recipe(recipe, "Today's Dinner"))


async def next_dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    recipe = recipe_for_date(_today() + timedelta(days=1))
    await update.message.reply_markdown(format_recipe(recipe, "Tomorrow's Dinner (Preview)"))


async def another(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    shown = _shown_today(state)
    candidates = [r for r in RECIPES if r["id"] not in shown]
    if not candidates:
        # Already cycled through every recipe today -- just avoid repeating
        # the very last one shown rather than refusing to answer.
        last = shown[-1] if shown else None
        candidates = [r for r in RECIPES if r["id"] != last] or RECIPES
    choice = random.choice(candidates)
    _record_shown(state, choice["id"])
    await update.message.reply_markdown(format_recipe(choice, "Here's Another Option"))


def main() -> None:
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Put it in bot/.env (see .env.example).")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dinner", dinner))
    app.add_handler(CommandHandler("next", next_dinner))
    app.add_handler(CommandHandler("another", another))

    log.info("Bot starting for on-demand commands. %d recipes loaded.", len(RECIPES))
    app.run_polling()


if __name__ == "__main__":
    main()
