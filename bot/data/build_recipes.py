"""
Generates recipes.json from ingredient quantities + a small nutrition reference table.

Recipes are home-cook versions inspired by real dishes from Tirana healthy-food
spots: most from the Green & Protein menu (dish names/ingredients, no home
quantities/times/steps/nutrition given), plus a handful inspired by signature
dishes from Fit Food, Gjelber, Leaf, and Chia Healthy Bar (sourced from general
write-ups about each place, not their own menus, which are behind JS-driven
delivery apps). Quantities, steps, and macros are original either way. Macros
are estimates from standard per-100g nutrition figures, not lab values.

Run: python3 build_recipes.py   (writes ../recipes.json)
"""
import json
import os

# (kcal, protein_g, carbs_g, fat_g) per 100g, or per "piece" for unit=="piece"
NUTRITION = {
    "brown_rice_cooked":        ("g",     123, 2.7, 25.6, 1.0),
    "quinoa_cooked":            ("g",     120, 4.4, 21.3, 1.9),
    "chicken_breast_cooked":    ("g",     165, 31.0, 0.0, 3.6),
    "chicken_meatballs":        ("g",     190, 22.0, 5.0, 9.0),
    "marinated_salmon":         ("g",     208, 20.0, 0.0, 13.0),
    "tuna_mix":                 ("g",     150, 22.0, 3.0, 6.0),
    "tofu_marinated":           ("g",     90,  9.0, 2.5, 5.5),
    "vegan_lentil_patty":       ("g",     190, 10.0, 22.0, 7.5),
    "egg_boiled":               ("piece", 78,  6.3, 0.6, 5.3),
    "avocado":                  ("g",     160, 2.0, 8.5, 14.7),
    "sweet_potato_cooked":      ("g",     90,  2.0, 21.0, 0.1),
    "chickpeas_cooked":         ("g",     164, 8.9, 27.4, 2.6),
    "lentils_cooked":           ("g",     116, 9.0, 20.1, 0.4),
    "black_beans_cooked":       ("g",     132, 8.9, 23.7, 0.5),
    "edamame":                  ("g",     122, 11.0, 10.0, 5.0),
    "hummus":                   ("g",     166, 7.9, 14.3, 9.6),
    "broccoli":                 ("g",     34,  2.8, 6.6, 0.4),
    "spinach":                  ("g",     23,  2.9, 3.6, 0.4),
    "mushrooms":                ("g",     22,  3.1, 3.3, 0.3),
    "corn":                     ("g",     86,  3.2, 19.0, 1.2),
    "peas":                     ("g",     81,  5.4, 14.5, 0.4),
    "carrots":                  ("g",     41,  0.9, 9.6, 0.2),
    "pickled_radish":           ("g",     20,  0.7, 4.0, 0.1),
    "pickled_red_onion":        ("g",     32,  0.9, 7.0, 0.1),
    "sun_dried_tomato":         ("g",     258, 14.1, 55.8, 3.0),
    "pomegranate_arils":        ("g",     83,  1.7, 18.7, 1.2),
    "cucumber":                 ("g",     15,  0.7, 3.6, 0.1),
    "tomato":                   ("g",     18,  0.9, 3.9, 0.2),
    "red_onion":                ("g",     40,  1.1, 9.3, 0.1),
    "lettuce":                  ("g",     15,  1.4, 2.9, 0.2),
    "arugula":                  ("g",     25,  2.6, 3.7, 0.7),
    "radicchio":                ("g",     23,  1.4, 4.5, 0.2),
    "white_cheese":             ("g",     264, 14.0, 4.0, 21.0),
    "sesame_seeds":             ("g",     573, 17.7, 23.4, 49.7),
    "chia_seeds":               ("g",     486, 16.5, 42.1, 30.7),
    "spinach_flax_wrap":        ("piece", 180, 7.0, 30.0, 4.0),
    "aronia_chia_bun":          ("piece", 200, 6.5, 35.0, 3.5),
}

# Dressings/sauces used across the recipes below, with their own sub-recipe and
# macros (computed from those exact components), so every dinner message can
# show "how to make the sauce" rather than just naming it.
#
# Lemon & Parsley, Strong Mustard, Japanese Soya, Smokey Soul, Beet & PB Sauce
# are the master formulas given by the user. "soybean sauce" (as referenced in
# the Green & Protein menu ingredient lists) is treated as the Japanese Soya
# formula, since that's the soy-based house dressing it corresponds to.
# Sharp Vinaigrette and Greek Yogurt & Herb Sauce were not part of the
# supplied master list, so those two are simple homemade versions -- flagged
# as such -- swap in the real formulas any time if you have them.
DRESSINGS = {
    "lemon_parsley": dict(
        label="Lemon & Parsley Dressing",
        components=["2 tbsp olive oil", "1 tbsp lemon juice", "2 tbsp chopped parsley"],
        macros=(244, 0.4, 1.6, 27.1),
    ),
    "strong_mustard": dict(
        label="Strong Mustard Dressing",
        components=["1 tbsp Dijon mustard", "1 tbsp apple cider vinegar", "1 tsp honey"],
        macros=(39, 0.9, 6.8, 1.0),
    ),
    "japanese_soya": dict(
        label="Japanese Soya Dressing",
        components=["2 tbsp light soy sauce", "1 tsp sesame oil", "a little grated ginger"],
        macros=(59, 2.6, 2.0, 4.5),
    ),
    "smokey_soul": dict(
        label="Smokey Soul Dressing",
        components=["2 tbsp Greek yogurt", "1/2 tsp smoked paprika", "a squeeze of lemon"],
        macros=(26, 3.1, 1.9, 0.7),
    ),
    "beet_pb": dict(
        label="Beet & PB Sauce",
        components=["2 tbsp beet puree", "1 tbsp peanut butter", "a splash of soy sauce"],
        macros=(110, 5.0, 6.3, 8.0),
    ),
    "sharp_vinaigrette": dict(
        label="Sharp Vinaigrette",
        components=["2 tbsp olive oil", "1 tbsp red wine vinegar", "1 tsp Dijon mustard"],
        macros=(246, 0.3, 0.4, 27.3),
    ),
    "greek_yogurt_herb": dict(
        label="Greek Yogurt & Herb Sauce",
        components=["3 tbsp Greek yogurt", "1 tbsp chopped dill or parsley",
                     "1 small garlic clove, grated", "a squeeze of lemon"],
        macros=(40, 4.9, 3.1, 0.9),
    ),
}

DISPLAY = {
    "brown_rice_cooked": "brown rice (cooked)",
    "quinoa_cooked": "quinoa (cooked)",
    "chicken_breast_cooked": "grilled chicken breast",
    "chicken_meatballs": "chicken meatballs",
    "marinated_salmon": "marinated salmon",
    "tuna_mix": "tuna mix",
    "tofu_marinated": "marinated tofu",
    "vegan_lentil_patty": "vegan lentil patty",
    "egg_boiled": "boiled egg",
    "avocado": "avocado",
    "sweet_potato_cooked": "sweet potato (roasted)",
    "chickpeas_cooked": "chickpeas (cooked)",
    "lentils_cooked": "lentils (cooked)",
    "black_beans_cooked": "black beans (cooked)",
    "edamame": "edamame",
    "hummus": "hummus",
    "broccoli": "broccoli",
    "spinach": "spinach",
    "mushrooms": "mushrooms",
    "corn": "sweet corn",
    "peas": "green peas",
    "carrots": "carrots",
    "pickled_radish": "pickled radishes",
    "pickled_red_onion": "pickled red onion",
    "sun_dried_tomato": "sun-dried tomatoes",
    "pomegranate_arils": "pomegranate arils",
    "cucumber": "cucumber",
    "tomato": "tomato",
    "red_onion": "red onion",
    "lettuce": "lettuce",
    "arugula": "arugula",
    "radicchio": "radicchio",
    "white_cheese": "white cheese",
    "sesame_seeds": "sesame seeds",
    "chia_seeds": "chia seeds",
    "spinach_flax_wrap": "spinach & flax-seed wrap",
    "aronia_chia_bun": "aronia & chia-seed bun",
}


def macro(name, qty):
    unit, kcal, p, c, f = NUTRITION[name]
    factor = qty if unit == "piece" else qty / 100.0
    return kcal * factor, p * factor, c * factor, f * factor


def amount_label(name, qty):
    unit = NUTRITION[name][0]
    if unit == "piece":
        n = int(qty)
        return f"{n} {DISPLAY[name]}{'s' if n > 1 and not DISPLAY[name].endswith('s') else ''}"
    return f"{int(qty)} g {DISPLAY[name]}"


RECIPES = [
    # ---------------- BOWLS ----------------
    dict(
        id="bowl-protein-beast", name="Protein Beast", category="Power Bowl", diet="Omnivore",
        prep_min=15, cook_min=20,
        items=[("brown_rice_cooked", 150), ("chicken_breast_cooked", 130), ("avocado", 60),
               ("corn", 50), ("pickled_radish", 30), ("egg_boiled", 1), ("sesame_seeds", 5)],
        dressings=["lemon_parsley"],
        instructions=[
            "Cook the brown rice according to package directions; keep warm.",
            "Season the chicken breast with salt and pepper, then grill or pan-sear over medium-high heat, ~5-6 minutes per side, until cooked through (internal temp 74°C). Slice.",
            "Boil the egg for 8-9 minutes, cool in cold water, peel, and halve.",
            "Slice the avocado and drain the corn and pickled radishes.",
            "Whisk together the Lemon & Parsley Dressing (recipe below).",
            "Layer rice in a bowl, arrange chicken, avocado, corn, pickled radishes and egg on top.",
            "Sprinkle with sesame seeds and drizzle with the dressing just before serving.",
        ],
    ),
    dict(
        id="bowl-sweet-tasty", name="Sweet & Tasty", category="Power Bowl", diet="Omnivore",
        prep_min=15, cook_min=25,
        items=[("brown_rice_cooked", 150), ("chicken_breast_cooked", 130), ("sweet_potato_cooked", 100),
               ("egg_boiled", 1), ("peas", 50), ("pickled_red_onion", 25), ("pomegranate_arils", 30),
               ("sesame_seeds", 5)],
        dressings=["strong_mustard"],
        instructions=[
            "Cube the sweet potato, toss with a little oil and salt, and roast at 200°C for 20-22 minutes until tender.",
            "Whisk together the Strong Mustard Dressing (recipe below); marinate the chicken breast briefly in a splash of it, then grill 5-6 minutes per side until cooked through. Slice.",
            "Cook the brown rice; boil the egg for 8-9 minutes, cool, peel and halve.",
            "Steam or microwave the peas for 2-3 minutes.",
            "Build the bowl: rice, chicken, roasted sweet potato, peas, pickled red onion and egg.",
            "Top with pomegranate arils and sesame seeds, then drizzle with strong mustard dressing.",
        ],
    ),
    dict(
        id="bowl-tofu-mushroom", name="Tofu & Mushroom Fix", category="Power Bowl", diet="Vegan",
        prep_min=15, cook_min=20,
        items=[("brown_rice_cooked", 150), ("tofu_marinated", 150), ("mushrooms", 100),
               ("sweet_potato_cooked", 100), ("chickpeas_cooked", 80), ("broccoli", 60),
               ("spinach", 40), ("sesame_seeds", 5)],
        dressings=["smokey_soul"],
        instructions=[
            "Press and cube the tofu, marinate 10 minutes in soy sauce, garlic and a little oil.",
            "Roast the cubed sweet potato at 200°C for 20 minutes; roast or pan-fry the mushrooms for 6-8 minutes until golden.",
            "Pan-fry the marinated tofu 6-8 minutes, turning, until browned on most sides.",
            "Steam the broccoli and spinach 3-4 minutes, then roughly mash together.",
            "Warm the chickpeas and cook the rice.",
            "Assemble rice, tofu, mushrooms, sweet potato, chickpeas and the mashed broccoli-spinach in a bowl.",
            "Sprinkle sesame seeds and finish with Smokey Soul Dressing (recipe below).",
        ],
    ),
    dict(
        id="bowl-bodybuilder-plus", name="Bodybuilder +", category="Power Bowl", diet="Omnivore",
        prep_min=15, cook_min=20,
        items=[("brown_rice_cooked", 150), ("chicken_breast_cooked", 150), ("avocado", 60),
               ("broccoli", 60), ("carrots", 50), ("corn", 50), ("sesame_seeds", 5)],
        dressings=["lemon_parsley"],
        instructions=[
            "Cook the brown rice according to package directions.",
            "Season and grill the chicken breast, ~5-6 minutes per side, until cooked through. Slice.",
            "Steam the broccoli and julienne or grate the carrots.",
            "Drain the corn; slice the avocado.",
            "Assemble rice topped with chicken, broccoli, carrots, corn and avocado.",
            "Sprinkle with sesame seeds and drizzle with Lemon & Parsley Dressing (recipe below).",
        ],
    ),
    dict(
        id="bowl-chickens-joy", name="Chicken's Joy", category="Power Bowl", diet="Omnivore",
        prep_min=20, cook_min=20,
        items=[("brown_rice_cooked", 150), ("chicken_meatballs", 150), ("egg_boiled", 1),
               ("carrots", 60), ("tomato", 60), ("peas", 40), ("corn", 40), ("sesame_seeds", 5)],
        dressings=["sharp_vinaigrette"],
        instructions=[
            "Form ground chicken into small meatballs, season, and pan-fry or bake at 200°C for 15-18 minutes until cooked through.",
            "Cook the brown rice; boil the egg for 8-9 minutes, cool, peel and halve.",
            "Shred the carrots, dice the tomato, and steam the peas 2-3 minutes.",
            "Assemble rice with meatballs, egg, carrots, tomato, peas and corn.",
            "Sprinkle with sesame seeds and finish with the Sharp Vinaigrette (recipe below).",
        ],
    ),
    dict(
        id="bowl-autumn-harvest", name="Autumn Harvest", category="Power Bowl", diet="Omnivore",
        prep_min=15, cook_min=25,
        items=[("brown_rice_cooked", 150), ("chicken_breast_cooked", 130), ("broccoli", 60),
               ("lentils_cooked", 80), ("pickled_radish", 30), ("sun_dried_tomato", 15),
               ("egg_boiled", 1), ("corn", 40), ("sesame_seeds", 5)],
        dressings=["strong_mustard"],
        instructions=[
            "Cook the lentils (or warm pre-cooked lentils) and the brown rice.",
            "Season and grill the chicken breast 5-6 minutes per side until cooked through. Slice.",
            "Steam the broccoli; boil the egg for 8-9 minutes, cool, peel and halve.",
            "Roughly chop the sun-dried tomatoes.",
            "Assemble rice, lentils, chicken, broccoli, pickled radishes, sun-dried tomatoes, egg and corn.",
            "Sprinkle sesame seeds and finish with Strong Mustard Dressing (recipe below).",
        ],
    ),
    dict(
        id="bowl-vegan-joy", name="Vegan Joy", category="Power Bowl", diet="Vegan",
        prep_min=20, cook_min=20,
        items=[("quinoa_cooked", 150), ("vegan_lentil_patty", 120), ("edamame", 50),
               ("sweet_potato_cooked", 80), ("hummus", 40), ("pickled_red_onion", 25),
               ("arugula", 20), ("radicchio", 20), ("sesame_seeds", 5)],
        dressings=["strong_mustard"],
        instructions=[
            "Cook the quinoa according to package directions.",
            "Form lentil-based patties (cooked lentils, breadcrumbs, spices, egg or flax binder) and pan-fry 3-4 minutes per side until golden.",
            "Roast the cubed sweet potato at 200°C for 18-20 minutes.",
            "Steam or boil the edamame for 3-4 minutes.",
            "Assemble quinoa with the lentil patties, edamame, sweet potato, hummus, pickled onion, arugula and radicchio.",
            "Sprinkle sesame seeds and finish with Strong Mustard Dressing (recipe below).",
        ],
    ),

    # ---------------- WRAPS ----------------
    dict(
        id="wrap-chicken-delight", name="Chicken Delight", category="High-Protein Wrap", diet="Omnivore",
        prep_min=10, cook_min=12,
        items=[("spinach_flax_wrap", 1), ("chicken_breast_cooked", 120), ("white_cheese", 25),
               ("corn", 40), ("tomato", 50), ("lettuce", 30)],
        dressings=["smokey_soul"],
        instructions=[
            "Season and grill or pan-sear the chicken breast, ~5-6 minutes per side, until cooked through. Slice thin.",
            "Warm the spinach & flax wrap briefly in a dry pan for pliability.",
            "Dice the tomato and crumble the white cheese.",
            "Lay lettuce on the wrap, then add chicken, cheese, corn and tomato.",
            "Drizzle with Smokey Soul Dressing (recipe below), fold in the sides, and roll tightly.",
        ],
    ),
    dict(
        id="wrap-cool-egg", name="Cool Egg", category="High-Protein Wrap", diet="Vegetarian",
        prep_min=10, cook_min=10,
        items=[("spinach_flax_wrap", 1), ("egg_boiled", 2), ("white_cheese", 25),
               ("tomato", 50), ("lettuce", 30)],
        instructions=[
            "Boil the eggs for 8-9 minutes, cool in cold water, peel and chop; toss with a pinch of dry dill.",
            "Warm the wrap briefly for pliability.",
            "Dice the tomato and crumble the white cheese.",
            "Layer lettuce, chopped egg, cheese and tomato on the wrap.",
            "Fold in the sides and roll tightly.",
        ],
    ),
    dict(
        id="wrap-chicken-charm", name="Chicken Charm", category="High-Protein Wrap", diet="Omnivore",
        prep_min=15, cook_min=20,
        items=[("spinach_flax_wrap", 1), ("brown_rice_cooked", 80), ("chicken_breast_cooked", 100),
               ("black_beans_cooked", 60), ("carrots", 40), ("corn", 40), ("lettuce", 30)],
        dressings=["greek_yogurt_herb"],
        instructions=[
            "Cook the brown rice; season and grill the chicken breast 5-6 minutes per side, then slice.",
            "Warm the black beans and shred the carrots.",
            "Warm the wrap briefly for pliability.",
            "Layer lettuce, rice, chicken, black beans, carrots and corn on the wrap.",
            "Drizzle with Greek Yogurt & Herb Sauce (recipe below), fold in the sides, and roll tightly.",
        ],
    ),
    dict(
        id="wrap-avocado-egg", name="Avocado & Egg", category="High-Protein Wrap", diet="Vegetarian",
        prep_min=10, cook_min=10,
        items=[("spinach_flax_wrap", 1), ("avocado", 80), ("egg_boiled", 2),
               ("tomato", 50), ("lettuce", 30)],
        dressings=["japanese_soya"],
        instructions=[
            "Boil the eggs for 8-9 minutes, cool, peel and slice.",
            "Slice the avocado and dice the tomato.",
            "Warm the wrap briefly for pliability.",
            "Layer lettuce, avocado, egg and tomato on the wrap.",
            "Drizzle with Japanese Soya Dressing (recipe below), fold in the sides, and roll tightly.",
        ],
    ),
    dict(
        id="wrap-gut-power", name="Gut Power", category="High-Protein Wrap", diet="Vegan",
        prep_min=15, cook_min=15,
        items=[("spinach_flax_wrap", 1), ("vegan_lentil_patty", 100), ("carrots", 40),
               ("broccoli", 40), ("red_onion", 20), ("cucumber", 40), ("lettuce", 30)],
        dressings=["japanese_soya"],
        instructions=[
            "Form and pan-fry the lentil patty, 3-4 minutes per side, until golden; roughly crumble.",
            "Steam the broccoli 3-4 minutes; shred the carrots and slice the cucumber and red onion.",
            "Warm the wrap briefly for pliability.",
            "Layer lettuce, lentil patty, carrots, broccoli, red onion and cucumber on the wrap.",
            "Drizzle with Japanese Soya Dressing (recipe below), fold in the sides, and roll tightly.",
        ],
    ),
    dict(
        id="wrap-tuna-turner", name="Tuna Turner", category="High-Protein Wrap", diet="Omnivore",
        prep_min=10, cook_min=5,
        items=[("spinach_flax_wrap", 1), ("tuna_mix", 100), ("corn", 40), ("cucumber", 40),
               ("black_beans_cooked", 50), ("red_onion", 20), ("lettuce", 30)],
        dressings=["smokey_soul"],
        instructions=[
            "Mix drained tuna with a little light mayo or Greek yogurt to make the tuna mix.",
            "Dice the cucumber and red onion; warm the black beans.",
            "Warm the wrap briefly for pliability.",
            "Layer lettuce, tuna mix, corn, cucumber, black beans and red onion on the wrap.",
            "Drizzle with Smokey Soul Dressing (recipe below), fold in the sides, and roll tightly.",
        ],
    ),

    # ---------------- BURGERS ----------------
    dict(
        id="burger-queen-premium", name="Queen Premium", category="House Burger", diet="Omnivore",
        prep_min=15, cook_min=18,
        items=[("aronia_chia_bun", 1), ("chicken_meatballs", 130), ("egg_boiled", 1),
               ("white_cheese", 20), ("tomato", 40), ("cucumber", 30), ("lettuce", 20)],
        dressings=["japanese_soya", "greek_yogurt_herb"],
        instructions=[
            "Form the chicken meatball mixture into one flat patty and pan-fry or grill 5-6 minutes per side until cooked through.",
            "Boil the egg for 8-9 minutes, cool, peel and slice.",
            "Toast the bun cut-side down for 1-2 minutes.",
            "Slice the tomato, pickled cucumber and shred the lettuce; slice the white cheese.",
            "Build the burger: bun base, lettuce, patty, cheese, egg, tomato, cucumber.",
            "Drizzle with Japanese Soya Dressing and Greek Yogurt & Herb Sauce (recipes below), then close with the top bun.",
        ],
    ),
    dict(
        id="burger-duplex-day", name="Duplex Day", category="House Burger", diet="Vegetarian",
        prep_min=10, cook_min=10,
        items=[("aronia_chia_bun", 1), ("avocado", 80), ("egg_boiled", 2), ("cucumber", 30),
               ("tomato", 40), ("lettuce", 20)],
        dressings=["japanese_soya", "greek_yogurt_herb"],
        instructions=[
            "Boil the eggs for 8-9 minutes, cool, peel and slice.",
            "Slice the avocado, tomato and pickled cucumber.",
            "Toast the bun cut-side down for 1-2 minutes.",
            "Build the burger: bun base, lettuce, avocado, egg, tomato, cucumber.",
            "Drizzle with Japanese Soya Dressing and Greek Yogurt & Herb Sauce (recipes below), then close with the top bun.",
        ],
    ),
    dict(
        id="burger-salmon-taste", name="Salmon Taste", category="House Burger", diet="Omnivore",
        prep_min=15, cook_min=10,
        items=[("aronia_chia_bun", 1), ("marinated_salmon", 120), ("tomato", 40),
               ("cucumber", 30), ("red_onion", 20), ("lettuce", 20)],
        dressings=["japanese_soya"],
        instructions=[
            "Whisk together the Japanese Soya Dressing (recipe below); marinate the salmon fillet briefly in it, then pan-sear 3-4 minutes per side until just cooked through.",
            "Slice the tomato, cucumber and red onion.",
            "Toast the bun cut-side down for 1-2 minutes.",
            "Build the burger: bun base, lettuce, salmon, tomato, cucumber, red onion.",
            "Drizzle with any remaining Japanese Soya Dressing and close with the top bun.",
        ],
    ),
    dict(
        id="burger-queen-deluxe-xl", name="Queen Deluxe XL", category="House Burger", diet="Omnivore",
        prep_min=15, cook_min=18,
        items=[("aronia_chia_bun", 1), ("chicken_meatballs", 150), ("tomato", 40), ("cucumber", 30),
               ("lettuce", 20)],
        dressings=["japanese_soya", "greek_yogurt_herb"],
        instructions=[
            "Form the chicken meatball mixture into one large flat patty and grill or pan-fry 6-7 minutes per side until cooked through.",
            "Slice the tomato and pickled cucumber.",
            "Toast the bun cut-side down for 1-2 minutes.",
            "Build the burger: bun base, lettuce, patty, tomato, cucumber.",
            "Drizzle with Japanese Soya Dressing and Greek Yogurt & Herb Sauce (recipes below), then close with the top bun.",
        ],
    ),
    dict(
        id="burger-leading-light", name="Leading Light", category="House Burger", diet="Omnivore",
        prep_min=15, cook_min=15,
        items=[("aronia_chia_bun", 1), ("chicken_breast_cooked", 130), ("white_cheese", 25),
               ("egg_boiled", 1), ("tomato", 40), ("lettuce", 20)],
        dressings=["japanese_soya", "greek_yogurt_herb"],
        instructions=[
            "Season and grill the chicken breast 5-6 minutes per side until cooked through.",
            "Boil the egg for 8-9 minutes, cool, peel and slice.",
            "Toast the bun cut-side down for 1-2 minutes; slice the tomato and white cheese.",
            "Build the burger: bun base, lettuce, chicken, cheese, egg, tomato.",
            "Drizzle with Japanese Soya Dressing and Greek Yogurt & Herb Sauce (recipes below), then close with the top bun.",
        ],
    ),
    dict(
        id="burger-gorgeous-gang", name="Gorgeous Gang", category="House Burger", diet="Vegan",
        prep_min=15, cook_min=12,
        items=[("aronia_chia_bun", 1), ("vegan_lentil_patty", 130), ("tomato", 40),
               ("cucumber", 30), ("red_onion", 20), ("lettuce", 20)],
        dressings=["japanese_soya", "beet_pb"],
        instructions=[
            "Form and pan-fry the lentil patty, 3-4 minutes per side, until golden and heated through.",
            "Slice the tomato, cucumber and red onion.",
            "Toast the bun cut-side down for 1-2 minutes.",
            "Build the burger: bun base, lettuce, lentil patty, tomato, cucumber, red onion.",
            "Drizzle with Japanese Soya Dressing and Beet & PB Sauce (recipes below), then close with the top bun.",
        ],
    ),

    # ---------------- INSPIRED BY OTHER TIRANA HEALTHY-FOOD SPOTS ----------------
    # Fit Food, Gjelber, Leaf, and Chia Healthy Bar publish general style/signature
    # dish descriptions rather than detailed recipes (see build_recipes.py history
    # for sourcing notes), so these are original recipes built around each place's
    # known specialty rather than a copied dish.
    dict(
        id="bowl-fit-food-fuel", name="Fit Food Fuel Bowl", category="Power Bowl", diet="Omnivore",
        prep_min=15, cook_min=20,
        items=[("brown_rice_cooked", 150), ("chicken_breast_cooked", 140), ("broccoli", 60),
               ("chickpeas_cooked", 70), ("cucumber", 40), ("white_cheese", 25), ("sesame_seeds", 5)],
        dressings=["sharp_vinaigrette"],
        instructions=[
            "Cook the brown rice according to package directions.",
            "Season and grill the chicken breast, ~5-6 minutes per side, until cooked through. Slice.",
            "Steam the broccoli 3-4 minutes; warm the chickpeas; dice the cucumber.",
            "Assemble rice topped with chicken, broccoli, chickpeas, cucumber and crumbled white cheese.",
            "Sprinkle with sesame seeds and finish with the Sharp Vinaigrette (recipe below).",
        ],
    ),
    dict(
        id="bowl-chia-power", name="Chia Power Bowl", category="Power Bowl", diet="Vegan",
        prep_min=15, cook_min=15,
        items=[("quinoa_cooked", 130), ("avocado", 60), ("edamame", 50), ("cucumber", 40),
               ("hummus", 40), ("chia_seeds", 15)],
        dressings=["beet_pb"],
        instructions=[
            "Cook the quinoa according to package directions.",
            "Steam or boil the edamame for 3-4 minutes.",
            "Slice the avocado and dice the cucumber.",
            "Assemble quinoa topped with avocado, edamame, cucumber and a scoop of hummus.",
            "Sprinkle generously with chia seeds and finish with the Beet & PB Sauce (recipe below).",
        ],
    ),
    dict(
        id="wrap-muscle-builder", name="Muscle Builder Wrap", category="High-Protein Wrap", diet="Omnivore",
        prep_min=15, cook_min=15,
        items=[("spinach_flax_wrap", 1), ("chicken_breast_cooked", 130), ("quinoa_cooked", 60),
               ("hummus", 40), ("arugula", 20), ("cucumber", 30)],
        dressings=["sharp_vinaigrette"],
        instructions=[
            "Cook the quinoa; season and grill the chicken breast 5-6 minutes per side, then slice.",
            "Slice the cucumber and warm the wrap briefly for pliability.",
            "Spread hummus over the wrap, then layer arugula, quinoa, chicken and cucumber.",
            "Drizzle with Sharp Vinaigrette (recipe below), fold in the sides, and roll tightly.",
        ],
    ),
    dict(
        id="wrap-fit-wrap", name="Fit Wrap", category="High-Protein Wrap", diet="Omnivore",
        prep_min=10, cook_min=12,
        items=[("spinach_flax_wrap", 1), ("chicken_breast_cooked", 120), ("spinach", 30),
               ("tomato", 50), ("white_cheese", 20), ("lettuce", 20)],
        dressings=["strong_mustard"],
        instructions=[
            "Season and grill or pan-sear the chicken breast, ~5-6 minutes per side, until cooked through. Slice thin.",
            "Dice the tomato and crumble the white cheese; warm the wrap briefly for pliability.",
            "Layer lettuce, spinach, chicken, tomato and white cheese on the wrap.",
            "Drizzle with Strong Mustard Dressing (recipe below), fold in the sides, and roll tightly.",
        ],
    ),
    dict(
        id="burger-gjelber-garden", name="Gjelber Garden Burger", category="House Burger", diet="Vegan",
        prep_min=15, cook_min=12,
        items=[("aronia_chia_bun", 1), ("vegan_lentil_patty", 130), ("avocado", 50),
               ("tomato", 40), ("cucumber", 30), ("lettuce", 20)],
        dressings=["beet_pb"],
        instructions=[
            "Form and pan-fry the lentil patty, 3-4 minutes per side, until golden and heated through.",
            "Slice the avocado, tomato and cucumber.",
            "Toast the bun cut-side down for 1-2 minutes.",
            "Build the burger: bun base, lettuce, lentil patty, avocado, tomato, cucumber.",
            "Drizzle with the Beet & PB Sauce (recipe below), then close with the top bun.",
        ],
    ),
    dict(
        id="burger-leaf-avocado-toast", name="Leaf Avocado Toast Burger", category="House Burger", diet="Vegetarian",
        prep_min=10, cook_min=10,
        items=[("aronia_chia_bun", 1), ("avocado", 80), ("egg_boiled", 2), ("white_cheese", 20),
               ("tomato", 40), ("spinach", 20)],
        dressings=["greek_yogurt_herb"],
        instructions=[
            "Boil the eggs for 8-9 minutes, cool, peel and slice.",
            "Slice the avocado and tomato; crumble the white cheese.",
            "Toast the bun cut-side down for 1-2 minutes.",
            "Build the burger: bun base, spinach, mashed avocado, egg, tomato, white cheese.",
            "Drizzle with the Greek Yogurt & Herb Sauce (recipe below), then close with the top bun.",
        ],
    ),
]


def build():
    out = []
    for r in RECIPES:
        kcal = p = c = f = 0.0
        ingredients = []
        for name, qty in r["items"]:
            k, pp, cc, ff = macro(name, qty)
            kcal += k; p += pp; c += cc; f += ff
            ingredients.append(amount_label(name, qty))

        dressings_out = []
        for key in r.get("dressings", []):
            d = DRESSINGS[key]
            dk, dp, dc, df = d["macros"]
            kcal += dk; p += dp; c += dc; f += df
            dressings_out.append({"label": d["label"], "components": d["components"]})

        out.append({
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "diet": r["diet"],
            "prep_min": r["prep_min"],
            "cook_min": r["cook_min"],
            "ingredients": ingredients,
            "dressings": dressings_out,
            "instructions": r["instructions"],
            "macros": {
                "calories": round(kcal),
                "protein_g": round(p, 1),
                "carbs_g": round(c, 1),
                "fat_g": round(f, 1),
            },
        })
    return out


if __name__ == "__main__":
    recipes = build()
    out_path = os.path.join(os.path.dirname(__file__), "..", "recipes.json")
    with open(out_path, "w") as fh:
        json.dump(recipes, fh, indent=2)
    print(f"Wrote {len(recipes)} recipes to {out_path}")
