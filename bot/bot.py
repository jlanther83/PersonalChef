"""
PersonalChef Telegram bot -- interactive/manual mode.

Answers /dinner, /next, and /another via continuous long-polling. Useful for
local testing, but do NOT run this at the same time as the scheduled
"Dinner Bot Commands" GitHub Actions workflow (poll_once.py) -- both talk to
the same bot token via Telegram's getUpdates, and running two pollers at
once causes them to intermittently conflict (HTTP 409).

The persistent, always-available path is the two GitHub Actions workflows:
- daily-dinner.yml (send_daily.py) -- automatic 07:00 CET push
- respond-commands.yml (poll_once.py) -- /dinner, /next, /another, ~5 min lag

Run: python3 bot.py   (reads TELEGRAM_BOT_TOKEN from .env or the environment)
"""
import logging
import os
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import recipe_utils
from recipe_utils import RECIPES, TIMEZONE, format_recipe, recipe_for_date
from state_store import load_state, save_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("personalchef-bot")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _today() -> date:
    return datetime.now(TIMEZONE).date()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm your PersonalChef dinner bot.\n\n"
        "Every morning at 07:00 CET you'll get a dinner recipe with full macros "
        "(sent automatically by a separate scheduled job).\n"
        "You can also ask any time:\n"
        "/dinner — today's dinner recipe\n"
        "/next — preview tomorrow's dinner recipe\n"
        "/another — not feeling today's suggestion? get a different one"
    )


async def dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    recipe = recipe_for_date(_today())
    recipe_utils.record_shown(state, _today(), recipe["id"])
    save_state(state)
    await update.message.reply_markdown(format_recipe(recipe, "Today's Dinner"))


async def next_dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    recipe = recipe_for_date(_today() + timedelta(days=1))
    await update.message.reply_markdown(format_recipe(recipe, "Tomorrow's Dinner (Preview)"))


async def another(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    choice = recipe_utils.pick_another(state, _today())
    save_state(state)
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
