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

## Files
- `bot.py` — the bot: commands, daily scheduler, message formatting
- `recipes.json` — the 19-recipe database (generated file)
- `data/build_recipes.py` — regenerates `recipes.json` if you ever want to
  tweak an ingredient amount or nutrition figure
- `subscriber.json` — created automatically the first time you send `/start`;
  stores your Telegram chat ID so the 07:00 job knows where to send

## Running it
```
pip install -r requirements.txt
cp .env.example .env   # then paste your bot token into .env
python3 bot.py
```

## Important: this needs to keep running

Both the on-demand replies (`/dinner`, `/next`) and the 07:00 push only work
while `bot.py` is actually running and connected to the internet — Telegram
bots don't run "in the cloud" by themselves once you close it.

**Your options, simplest first:**

1. **Leave it running on your computer.** Start it (`python3 bot.py`) in a
   terminal and leave that terminal open, with the computer on, awake, and
   online. You can run it in the background so you don't need to keep the
   window visible (e.g. `nohup python3 bot.py &` on Mac/Linux), but the
   machine itself still needs to be on and connected at 07:00 for the daily
   message to go out.
2. **Move it to a small always-on host** if you want it independent of your
   own computer (e.g. a cheap VPS for a few dollars a month, or a spare
   Raspberry Pi at home). Nothing in the code needs to change — just copy
   this `bot/` folder there, install requirements, and run it the same way
   (ideally as a background service so it restarts itself if the machine
   reboots). Happy to help set this up if you want it later.

There is no in-between free option that requires zero ongoing setup — some
machine, somewhere, needs to keep this process alive.
