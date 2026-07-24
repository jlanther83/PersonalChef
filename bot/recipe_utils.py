"""
Shared recipe-rotation and message-formatting logic, used by both the
interactive bot (bot.py) and the GitHub Actions daily sender (send_daily.py)
so the two never disagree on "today's recipe".
"""
import json
import os
import random
from datetime import date

from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECIPES_PATH = os.path.join(BASE_DIR, "recipes.json")

TIMEZONE = ZoneInfo("Europe/Berlin")  # CET/CEST
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
