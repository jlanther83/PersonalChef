# PersonalChef Telegram Bot

Sends a dinner recipe (Power Bowl / High-Protein Wrap / House Burger) every
morning at 07:00 CET, and answers `/dinner` and `/next` on demand.

The 19 recipes in `recipes.json` are home-cook versions inspired by real dish
names and ingredients from the Green & Protein (Tirana) menu. That menu lists
dishes and prices only — no home quantities, cook times, steps, or nutrition —
so the quantities, steps, and macros here are original, with macros estimated
from standard nutrition data (see `data/build_recipes.py` for the numbers
used). They are estimates, not lab-measured values.

Dressings/sauces are built from the master formulas provided by the user
(Lemon & Parsley, Strong Mustard, Japanese Soya, Smokey Soul, Beet & PB Sauce)
— see the `DRESSINGS` dict in `data/build_recipes.py`. "Soybean sauce" as
referenced in the original menu is treated as the Japanese Soya formula.
Sharp Vinaigrette and Greek Yogurt & Herb Sauce weren't part of the supplied
formulas, so those two are simple homemade versions — swap them in
`build_recipes.py` and re-run it if exact formulas become available.

## Two independent halves

This is split into two pieces that don't depend on each other:

1. **Automatic 07:00 CET daily message** — a GitHub Actions workflow
   (`.github/workflows/daily-dinner.yml`) that runs `send_daily.py` on a
   schedule. This runs on GitHub's servers, for free, forever, with nothing
   of yours needing to stay on. This is the part covered by this setup.
2. **On-demand `/dinner` and `/next`** — handled by `bot.py`, which only
   answers while it's actually running somewhere (see "Running the on-demand
   bot" below). It is **not** running continuously right now; start it
   whenever you want to use those commands.

Both sides share the same recipe rotation (`recipe_utils.py`), so whichever
one you use on a given day always names the same dish.

## One-time setup: GitHub repository secrets

The workflow needs your bot token and your Telegram chat ID, stored as
**repository secrets** (encrypted, never visible in logs or code):

1. On GitHub, open this repository → **Settings** → **Secrets and variables**
   → **Actions**.
2. Click **New repository secret**.
   - Name: `TELEGRAM_BOT_TOKEN` — Value: your bot token from @BotFather.
   - Click **Add secret**.
3. Click **New repository secret** again.
   - Name: `TELEGRAM_CHAT_ID` — Value: your Telegram chat ID.
   - Click **Add secret**.

Once both secrets exist, the workflow sends the message automatically every
morning — nothing else to do. You can also trigger it manually any time from
the **Actions** tab → **Daily Dinner Reminder** → **Run workflow**, to test it
without waiting for 07:00.

## Files
- `recipe_utils.py` — shared recipe rotation + message formatting
- `send_daily.py` — sends today's recipe via the Telegram HTTP API directly
  (no dependencies); this is what the GitHub Actions workflow runs
- `bot.py` — the on-demand bot: `/start`, `/dinner`, `/next`
- `recipes.json` — the 19-recipe database (generated file)
- `data/build_recipes.py` — regenerates `recipes.json` if you ever want to
  tweak an ingredient amount or nutrition figure
- `subscriber.json` — created automatically the first time you send `/start`
  to the bot; stores your Telegram chat ID (same value as the
  `TELEGRAM_CHAT_ID` secret above)

## Running the on-demand bot

Only needed for `/dinner` and `/next` — the daily 07:00 message works without
this.
```
pip install -r requirements.txt
cp .env.example .env   # then paste your bot token into .env
python3 bot.py
```
This needs to be running and connected to the internet for those commands to
answer. Leave it running in a terminal (`nohup python3 bot.py &` to background
it), on any machine that's on — your own computer, a spare Raspberry Pi, or a
small always-on host. Ask any time if you'd like help setting that up.
