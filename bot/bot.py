"""
PersonalChef Telegram bot -- on-demand side.

Answers /dinner and /next whenever this process is running. The automatic
07:00 CET daily push is handled separately and independently by the
GitHub Actions workflow (.github/workflows/daily-dinner.yml) via
send_daily.py, so it keeps working even when this process isn't running.

Run: python3 bot.py   (reads TELEGRAM_BOT_TOKEN from .env or the environment)
"""
import json
import logging
import os
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from recipe_utils import RECIPES, TIMEZONE, format_recipe, recipe_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("personalchef-bot")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBSCRIBER_PATH = os.path.join(BASE_DIR, "subscriber.json")


def save_chat_id(chat_id: int) -> None:
    with open(SUBSCRIBER_PATH, "w") as fh:
        json.dump({"chat_id": chat_id}, fh)


def _today() -> date:
    return datetime.now(TIMEZONE).date()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "Hi! I'm your PersonalChef dinner bot.\n\n"
        "Every morning at 07:00 CET you'll get a dinner recipe with full macros "
        "(sent automatically by a separate scheduled job).\n"
        "You can also ask any time this bot is running:\n"
        "/dinner — today's dinner recipe\n"
        "/next — preview tomorrow's dinner recipe"
    )
    log.info("Registered subscriber chat_id=%s", update.effective_chat.id)


async def dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    recipe = recipe_for_date(_today())
    await update.message.reply_markdown(format_recipe(recipe, "Today's Dinner"))


async def next_dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    recipe = recipe_for_date(_today() + timedelta(days=1))
    await update.message.reply_markdown(format_recipe(recipe, "Tomorrow's Dinner (Preview)"))


def main() -> None:
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Put it in bot/.env (see .env.example).")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dinner", dinner))
    app.add_handler(CommandHandler("next", next_dinner))

    log.info("Bot starting for on-demand commands. %d recipes loaded.", len(RECIPES))
    app.run_polling()


if __name__ == "__main__":
    main()
