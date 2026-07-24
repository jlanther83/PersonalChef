# PersonalChef Telegram Bot

Sends a dinner recipe (Power Bowl / High-Protein Wrap / House Burger) every
morning at 07:00 CET, and answers `/dinner`, `/next`, and `/another` on demand
-- entirely through GitHub Actions, so nothing needs to stay running on your
own computer.

The 25 recipes in `recipes.json` are home-cook versions inspired by real
dishes from Tirana healthy-food spots:
- 19 inspired by the **Green & Protein** menu (dish names + ingredients, no
  home quantities, cook times, steps, or nutrition given).
- 6 more inspired by the signature-dish descriptions of **Fit Food**,
  **Gjelber**, **Leaf**, and **Chia Healthy Bar** (found via general
  write-ups about each place, since their own menus are behind JS-driven
  delivery apps that couldn't be scraped for exact ingredient lists).

In both cases only the dish concept/name and general ingredients came from
the real place — quantities, steps, and macros here are original, with
macros estimated from standard nutrition data (see `data/build_recipes.py`
for the numbers used). They are estimates, not lab-measured values.

Dressings/sauces are built from the master formulas provided by the user
(Lemon & Parsley, Strong Mustard, Japanese Soya, Smokey Soul, Beet & PB Sauce)
— see the `DRESSINGS` dict in `data/build_recipes.py`. "Soybean sauce" as
referenced in the original menu is treated as the Japanese Soya formula.
Sharp Vinaigrette and Greek Yogurt & Herb Sauce weren't part of the supplied
formulas, so those two are simple homemade versions — swap them in
`build_recipes.py` and re-run it if exact formulas become available.

## Two GitHub Actions workflows, both free forever

Telegram bots normally need a process running 24/7 to answer messages. A
GitHub Actions job can't do that directly — jobs are capped at 6 hours, and
using Actions to host a persistent service goes against GitHub's usage
policies. So instead, this uses the pattern Actions is actually built for:
short scheduled jobs.

1. **`daily-dinner.yml`** runs `send_daily.py` on a schedule and pushes the
   day's recipe at 07:00 CET, every morning, automatically.
2. **`respond-commands.yml`** runs `poll_once.py` every 5 minutes (the
   shortest interval GitHub allows) -- it checks Telegram for any new
   `/dinner`, `/next`, or `/another` message, answers it, and exits.
   **Replies land within roughly 5 minutes, not instantly** — that's the
   tradeoff for this being free and not requiring anything of yours to stay
   on.

Both scripts share the same recipe rotation (`recipe_utils.py`), so whichever
one answers on a given day always names the same dish, and `/another`'s
"don't repeat today" memory (`state.json`) is shared and committed back to
the repo by `respond-commands.yml` after each run that had new messages.

**Maintenance note:** GitHub automatically disables scheduled workflows after
60 days with no commits to the repository. If replies or the daily message
ever stop, check the repo's **Actions** tab for a "workflow disabled" banner
and re-enable it there (any small commit also resets the clock).

## One-time setup: GitHub repository secrets

Both workflows need your bot token and your Telegram chat ID, stored as
**repository secrets** (encrypted, never visible in logs or code):

1. On GitHub, open this repository → **Settings** → **Secrets and variables**
   → **Actions**.
2. Click **New repository secret**.
   - Name: `TELEGRAM_BOT_TOKEN` — Value: your bot token from @BotFather.
   - Click **Add secret**.
3. Click **New repository secret** again.
   - Name: `TELEGRAM_CHAT_ID` — Value: your Telegram chat ID.
   - Click **Add secret**.

Once both secrets exist, everything runs automatically — nothing else to do.
You can also trigger either workflow manually any time from the **Actions**
tab → pick the workflow → **Run workflow**, to test without waiting.

## Files
- `recipe_utils.py` — shared recipe rotation, "don't repeat today" picking
  logic, and message formatting
- `state_store.py` — tiny helper for reading/writing `state.json`
- `state.json` — committed state: Telegram update offset (so `poll_once.py`
  never re-reads an old message) and which recipes have been shown today.
  Contains no personal data or secrets — chat ID and token both come from
  repository secrets instead, since this repo is public.
- `send_daily.py` — sends today's recipe via the Telegram HTTP API directly
  (no dependencies); run by `daily-dinner.yml`
- `poll_once.py` — checks for and answers one batch of new commands, then
  exits; run by `respond-commands.yml`
- `bot.py` — optional interactive long-polling bot for local testing only
  (see below) — answers instantly, but **do not run it at the same time as
  `respond-commands.yml`**; two pollers on the same bot token intermittently
  conflict (Telegram returns HTTP 409 to whichever one is second)
- `recipes.json` — the 25-recipe database (generated file)
- `data/build_recipes.py` — regenerates `recipes.json` if you ever want to
  tweak an ingredient amount or nutrition figure

## Optional: running the interactive bot locally

Only useful for instant replies during local testing/development — the two
GitHub Actions workflows above already cover normal use for free, with no
machine of yours needing to stay on.
```
pip install -r requirements.txt
cp .env.example .env   # then paste your bot token into .env
python3 bot.py
```
