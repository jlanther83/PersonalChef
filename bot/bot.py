"""
PersonalChef Telegram bot.

Sends a daily dinner recipe (Power Bowl / High-Protein Wrap / House Burger)
every morning at 07:00 CET, and answers /dinner and /next on demand.

Run: python3 bot.py   (reads TELEGRAM_BOT_TOKEN from .env or the environment)
"""
import json
import logging
import os
import random
from datetime import date, time as dtime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("personalchef-bot")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECIPES_PATH = os.path.join(BASE_DIR, "recipes.json")
SUBSCRIBER_PATH = os.path.join(BASE_DIR, "subscriber.json")

TIMEZONE = ZoneInfo("Europe/Berlin")  # CET/CEST
SEND_TIME = dtime(hour=7, minute=0, tzinfo=TIMEZONE)
ROTATION_ANCHOR = date(2026, 1, 1)  # fixed reference point so the rotation is stable across restarts
ROTATION_SEED = 42  # fixed seed so the shuffled order never changes between runs

with open(RECIPES_PATH) as fh:
    RECIPES = json.load(fh)

_ids = sorted(r["id"] for r in RECIPES)
random.Random(ROTATION_SEED).shuffle(_ids)
ROTATION = _ids
RECIPES_BY_ID = {r["id"]: r for r in RECIPES}


def recipe_for_date(d: date) -> dict:
    idx = (d - ROTATION_ANCHOR).days % len(ROTATION)
    return RECIPES_BY_ID[ROTATION[idx]]


def load_chat_id() -> int | None:
    if not os.path.exists(SUBSCRIBER_PATH):
        return None
    with open(SUBSCRIBER_PATH) as fh:
        return json.load(fh).get("chat_id")


def save_chat_id(chat_id: int) -> None:
    with open(SUBSCRIBER_PATH, "w") as fh:
        json.dump({"chat_id": chat_id}, fh)


def format_recipe(recipe: dict, heading: str) -> str:
    m = recipe["macros"]
    lines = [
        f"*{heading}*",
        "",
        f"🍽️ *{recipe['name']}*  ({recipe['category']} · {recipe['diet']})",
        f"⏱️ Prep: {recipe['prep_min']} min · Cook: {recipe['cook_min']} min",
        "",
        "*Ingredients*",
    ]
    lines += [f"• {ing}" for ing in recipe["ingredients"]]
    for d in recipe.get("dressings", []):
        lines += ["", f"*{d['label']}* (mix together):"]
        lines += [f"  - {c}" for c in d["components"]]
    lines += ["", "*Instructions*"]
    lines += [f"{i}. {step}" for i, step in enumerate(recipe["instructions"], start=1)]
    lines += [
        "",
        "*Macros (per serving, estimated)*",
        f"Calories: {m['calories']} kcal   Protein: {m['protein_g']} g   "
        f"Carbs: {m['carbs_g']} g   Fat: {m['fat_g']} g",
    ]
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text(
        "Hi! I'm your PersonalChef dinner bot.\n\n"
        "Every morning at 07:00 CET I'll send you a dinner recipe with full macros.\n"
        "You can also ask any time:\n"
        "/dinner — today's dinner recipe\n"
        "/next — preview tomorrow's dinner recipe"
    )
    log.info("Registered subscriber chat_id=%s", update.effective_chat.id)


async def dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    recipe = recipe_for_date(_today())
    await update.message.reply_markdown(format_recipe(recipe, "Today's Dinner"))


async def next_dinner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from datetime import timedelta
    recipe = recipe_for_date(_today() + timedelta(days=1))
    await update.message.reply_markdown(format_recipe(recipe, "Tomorrow's Dinner (Preview)"))


def _today() -> date:
    from datetime import datetime
    return datetime.now(TIMEZONE).date()


async def send_daily_dinner(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = load_chat_id()
    if chat_id is None:
        log.warning("No subscriber registered yet; skipping daily send. Send /start to the bot first.")
        return
    recipe = recipe_for_date(_today())
    await context.bot.send_message(
        chat_id=chat_id,
        text=format_recipe(recipe, "Today's Dinner"),
        parse_mode="Markdown",
    )
    log.info("Sent daily dinner (%s) to chat_id=%s", recipe["id"], chat_id)


def main() -> None:
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Put it in bot/.env (see .env.example).")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dinner", dinner))
    app.add_handler(CommandHandler("next", next_dinner))

    app.job_queue.run_daily(send_daily_dinner, time=SEND_TIME, name="daily_dinner")

    log.info("Bot starting. Daily send scheduled for 07:00 %s. %d recipes loaded.", TIMEZONE, len(RECIPES))
    app.run_polling()


if __name__ == "__main__":
    main()
