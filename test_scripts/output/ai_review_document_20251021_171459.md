# VLM食品認識テスト結果レビュー依頼

生成日時: 2025年10月21日 17:14:59

================================================================================

## 概要

現状下記の様なプロンプトで添付の5つの画像を3つのVLMで分析したのでそのresultを示す。
徹底レビューして、食品名リストの絞り込み、プロンプト、VLMモデルどの部分をどう修正すると良いと思う？

================================================================================

## [プロンプト]

```
You are an expert food analyst and nutritionist for a US‑based diet app.
Analyze ONE meal image and return ONE JSON object ONLY (no extra text).

PRIMARY GOALS
- Detect every visually separate food item (each is one "dish").
- For each dish, choose exactly ONE analysis_method from {USE_AS_IS, HYBRID_DECOMPOSITION, DECOMPOSE_TO_INGREDIENTS}.
- For every base_food.item_name and every ingredients[].ingredient_name, you MUST choose a string that exists VERBATIM in the EXACT_FOOD_LIST (CORE) given in this run.
  - If you cannot find a suitable match EVEN AFTER trying the closest NFS/NS item FROM THE LIST, set the name field to null AND use the fallback "unlisted" object described below. Never place out‑of‑list strings in item_name or ingredient_name; the ONLY place where free text is allowed is unlisted.display_name.

UNLISTED (CUSTOM) FALLBACK — WHEN AND HOW
- Use the "unlisted" object ONLY when a suitable CORE item truly does not exist.
- Structure:
  {
    "display_name": "<free text name>",
    "weight_g": <int>,
    "nutrition_per_100g": {
      "calorie": <number>,     // kcal per 100 g
      "protein_g": <number>,   // grams per 100 g
      "fat_g": <number>,       // grams per 100 g
      "carbs_g": <number>      // grams per 100 g
    }
  }
- If "unlisted" is present for a base or ingredient, the corresponding name field MUST be null.
- "unlisted.weight_g" MUST equal the sibling "weight_g" value for that base or ingredient.
- Nutrition sanity check (soft rule): calorie ≈ (4*protein_g + 9*fat_g + 4*carbs_g) within ±20%.

METHOD ORDER (HARD RULES)
A) Prefer canonical BASES with HYBRID only for visible extras:
   - Pizza / Pasta / Mac & Cheese / Sandwiches & Wraps / Mexican (taco/burrito/quesadilla) / Standard sides (rice pilaf, mashed potatoes, fries) → USE_AS_IS unless you clearly see extra toppings beyond the base; then use HYBRID_DECOMPOSITION and list ONLY the extras.
B) SALADS → If you see greens + ≥1 add-on (croutons, tomato, cheese, dressing, etc.), use DECOMPOSE_TO_INGREDIENTS. If dressing is visible but type is unclear → use exactly "Sauce, NFS".
C) POULTRY → If the part is not obvious, use:
   - "Chicken, NS as to part and cooking method, skin eaten" (skin visible) OR
   - "Chicken, NS as to part and cooking method, skin not eaten" (no skin visible).
   Do NOT guess breast/thigh/wing unless unmistakable.
D) SAUCES → Never output a sauce/dressing as its own dish unless it is served in a separate cup/bottle. Otherwise attach as a HYBRID ingredient or as a DECOMPOSE ingredient.
E) IDENTICAL UNITS → If multiple identical items exist (e.g., 2 tacos), return ONE dish with "unit_count" equal to the total and make weight_g the TOTAL. Do not duplicate identical dishes.

WEIGHTS
- Report weights in grams; use cooked-state entries if the food looks cooked.
- Scale by plate/bowl size (typical dinner plate 25–28 cm).
- For HYBRID/DECOMPOSE dishes, base_food.weight_g + sum(ingredients[].weight_g) should equal the total for that dish (implicit). Round weights to the nearest 5 g when estimating.

CONFIDENCE (GUIDE)
- 0.85–1.00: clear view, canonical base, exact CORE matches.
- 0.60–0.80: some occlusion and/or at least one NS/NFS mapping; portion size uncertain.
- 0.40–0.55: heavy occlusion or use of one or more unlisted items; item type uncertain.

OUTPUT JSON SHAPE (no comments):
{
  "dishes": [
    {
      "dish_name": "short human name",
      "unit_count": 1,
      "confidence": 0.0-1.0,
      "analysis_method": "USE_AS_IS | HYBRID_DECOMPOSITION | DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": "[EXACT from CORE or null]",
        "weight_g": <int>,
        "unlisted": null | {
          "display_name": "string",
          "weight_g": <int>,
          "nutrition_per_100g": {
            "calorie": <number>,
            "protein_g": <number>,
            "fat_g": <number>,
            "carbs_g": <number>
          }
        }
      },
      "ingredients": [
        {
          "ingredient_name": "[EXACT from CORE or null]",
          "weight_g": <int>,
          "unlisted": null | {
            "display_name": "string",
            "weight_g": <int>,
            "nutrition_per_100g": {
              "calorie": <number>,
              "protein_g": <number>,
              "fat_g": <number>,
              "carbs_g": <number>
            }
          }
        }
      ]
    }
  ]
}

HARD VALIDATION BEFORE RETURNING
1) For every base/ingredient, EITHER (a) name exists verbatim in CORE and unlisted is null, OR (b) name is null and unlisted is provided and complete. Never provide both.
2) If HYBRID, ingredients include ONLY extras not already implied by the base.
3) Sauces are attached, not standalone, unless clearly in a separate container.
4) Identical units are merged into a single dish with unit_count.
5) Weights reflect cooked vs raw state and total counts; for HYBRID/DECOMPOSE, base + ingredients weights sum consistently (nearest 5 g).
6) If any unlisted object exists, its weight_g equals the sibling weight_g and nutrition_per_100g values are realistic (see sanity check).
7) Output ONE JSON object ONLY. No trailing commentary.

---

## EXACT_FOOD_LIST (CORE)

You will receive a CORE list (below). Prefer CORE items. If an adequate match does not exist in CORE (including NS/NFS options), use the "unlisted" fallback as specified above; do not invent names in item_name or ingredient_name.
## Pizza & Italian — Bases

* Pizza, cheese, from restaurant or fast food, thin crust
* Pizza, cheese, from restaurant or fast food, medium crust
* Pizza, cheese, from restaurant or fast food, thick crust
* Pizza, cheese, stuffed crust
* Lasagna with meat
* Lasagna, meatless
* Pasta with sauce, NFS

## Pasta, Mac & Cheese, Pasta Salads

* Macaroni or noodles with cheese
* Pasta with tomato-based sauce and cheese

## Sandwiches, Burgers, Wraps & Hot Dogs

* Sandwich wrap, NFS
* Hamburger, NFS
* Chicken fillet sandwich, NFS
* Fish sandwich, NFS
* Sandwich, NFS
* Ham sandwich on white
* Turkey sandwich on white
* Roast beef sandwich on white
* Club sandwich on white
* Hot dog sandwich, NFS, on white bun

## Breakfast Sandwiches & Burritos

* Egg sandwich on English muffin
* Egg sandwich on biscuit
* Egg sandwich on bagel
* Egg burrito

## Mexican & Tex‑Mex

* Burrito, NFS
* Burrito bowl, NFS
* Quesadilla, NFS
* Enchilada, NFS
* Tamale, NFS
* Taco, NFS
* Enchilada, beef
* Enchilada, chicken
* Nachos, NFS
* Fajita, NFS

## Asian — Noodles & Mains

* Lo mein, NFS
* Pad Thai, NFS
* Ramen bowl, NFS
* General Tso chicken
* Orange chicken
* Sesame chicken
* Kung pao chicken
* Sweet and sour chicken or turkey
* Rice, fried, NFS
* Sushi, NFS

## Dumplings & Savory Pastries

* Empanada, no meat
* Empanada, beef
* Empanada, chicken

## Poultry — NS cuts & quick-serve

* Chicken nuggets, NFS
* Chicken tenders or strips, NFS

## Poultry — minimal cooking method set

* Chicken, NS as to part and cooking method, skin eaten
* Chicken, NS as to part and cooking method, skin not eaten
* Chicken, ground
* Turkey, ground

## Beef, pork & processed meats

* Beef, stew meat
* Sausage, NFS
* Italian sausage
* Pork sausage
* Pepperoni, NFS
* Salami, NFS
* Pastrami, NFS
* Canadian bacon, cooked
* Turkey or chicken sausage
* Beef sausage

## Beef, Pork & Other Meats

* Beef, NFS
* Beef, steak, NFS
* Beef, ground
* Beef, ground, patty
* Beef, roast
* Pork, NFS
* Pork, ground
* Pork, ribs
* Pork, tenderloin
* Ham
* Meat loaf, NS as to type of meat
* Salisbury steak with gravy

## Seafood & Fish

* Fish, salmon, NFS
* Fish, cod, NFS
* Fish, tilapia, NFS
* Fish, tuna, NFS
* Lobster
* Crab
* Shellfish, NFS
* Fish, white, mixed species, NFS
* Fish, NFS
* Fish, salmon, raw
* Clams, NFS
* Shrimp, NFS

## Breakfast Basics

* Pancakes, NFS
* Waffle, NFS
* French toast, NFS
* Crepe, NFS
* Cereal, cooked, NFS
* Pancakes, plain
* Waffle, plain
* French toast, plain
* Crepe, plain

## Eggs & Egg Dishes

* Egg, whole, cooked, NS as to cooking method
* Egg, deviled

## Breads, Wraps & Carriers

* Bread, white
* Bread, whole wheat
* Bread, multigrain
* Bread, sour dough
* Bread, pita
* Bread, pita, whole wheat
* Bagel
* Bagel, whole wheat
* Muffin, English
* Croissant
* Roll, white, hamburger bun
* Roll, white, hot dog bun
* Tortilla, corn
* Tortilla, flour
* Tortilla, whole wheat
* Taco shell, corn
* Garlic bread, NFS
* Biscuit, NFS
* Croutons
* Tortilla, NFS
* Taco shell, flour
* Biscuit, wheat
* Scone
* Muffin, plain
* Muffin, whole grain

## Grains, Rice & Porridge

* Noodles, cooked
* Rice noodles, cooked
* Pasta, cooked
* Grits, NFS
* Oatmeal, NFS
* Quinoa, no added fat
* Rice, white, cooked, no added fat
* Rice, brown, cooked, no added fat
* Rice pilaf

## Ready-to-eat Cereals

* Cereal, ready-to-eat, NFS
* Cereal, O's, plain
* Cereal, O's, honey nut
* Cereal, corn flakes, plain
* Cereal, rice crispy, plain
* Cereal, bran flakes, plain
* Cereal, shredded wheat, plain
* Cereal, granola
* Cereal, multigrain

## Potatoes & Starchy Sides & Roots

* Potato, baked, NFS
* Potato, roasted, NFS
* Potato, boiled, NFS
* Potato, french fries, NFS
* Potato, hash brown, NFS
* Potato tots, NFS
* Sweet potato, NFS
* Sweet potato fries, NFS
* Sweet potato, baked, no added fat
* Potato, mashed, from fresh, made with milk
* Potato, mashed, NFS

## Vegetables — Raw

* Romaine lettuce, raw
* Spinach, raw
* Kale, raw
* Cabbage, green, raw
* Cabbage, red, raw
* Broccoli, raw
* Cauliflower, raw
* Cucumber, raw
* Peppers, sweet, green, raw
* Peppers, sweet, red, raw
* Peppers, banana, raw
* Onions, raw
* Tomatoes, raw
* Avocado, raw
* Corn, raw
* Eggplant, raw
* Radish
* Cilantro, raw
* Parsley, raw
* Olives, black
* Pickles, dill
* Raw vegetable, NFS
* Lettuce, raw
* Lettuce, iceberg, raw
* Mixed salad greens, raw
* Coleslaw
* Lettuce, salad with assorted vegetables including tomatoes and/or carrots, no dressing

## Vegetables — Cooked

* Broccoli, NS as to form, cooked
* Carrots, NS as to form, cooked
* Corn, NS as to form, cooked
* Green peas, NS as to form, cooked
* Mushrooms, NS as to form, cooked
* Spinach, NS as to form, cooked
* Tomatoes, NS as to form, cooked
* Cauliflower, NS as to form, cooked
* Classic mixed vegetables, NS as to form, cooked
* Asparagus, NS as to form, cooked
* Bamboo shoots, cooked
* Brussels sprouts, NS as to form, cooked
* Beets, NS as to form, cooked
* Summer squash, yellow or green, NS as to form, cooked
* Okra, NS as to form, cooked
* Snowpeas, NS as to form, cooked
* Snowpeas, fresh, cooked, no added fat
* Green beans, fresh, cooked, no added fat
* Asparagus, fresh, cooked, no added fat
* Corn, fresh, cooked, no added fat
* Okra, fresh, cooked, no added fat
* Peppers, green, cooked
* Peppers, red, cooked
* Sauerkraut
* Vegetable curry

## Salads — Protein/Mayo Based

* Chicken or turkey salad, made with mayonnaise
* Tuna salad, made with mayonnaise

## Beans, Legumes & Tofu — Ingredients

* Black beans, NFS
* Pinto beans, NFS
* Kidney beans, NFS
* Chickpeas, NFS
* Lentils, NFS
* Baked beans
* Refried beans
* Hummus, plain
* Soybean curd
* Soybean curd, deep fried

## Beans, Legumes & Plant-based Mains

* Beans, NFS
* Edamame, cooked
* Soybeans, cooked
* Soup, bean
* Soup, split pea
* Soup, lentil
* Soup, miso or tofu
* Vegetarian stew

## Nuts, Seeds, Butters & Trail Mix

* Nuts, NFS
* Almonds, NFS
* Cashews, NFS
* Peanuts, roasted, salted
* Pistachio nuts, NFS
* Walnuts, excluding honey roasted
* Mixed nuts, NFS
* Sunflower seeds, plain, unsalted
* Pumpkin seeds, NFS
* Chia seeds
* Flax seeds
* Peanut butter
* Tahini
* Trail mix, NFS
* Coconut, fresh
* Almonds, unsalted
* Cashews, unsalted
* Mixed nuts, without peanuts, salted
* Peanuts, dry roasted, lightly salted
* Pecans, unsalted
* Pistachio nuts, salted
* Almond butter
* Pumpkin seeds, salted
* Sunflower seeds, plain, salted
* Mixed seeds
* Trail mix with nuts
* Trail mix with nuts and fruit
* Trail mix with chocolate

## Sauces, Dressings, Oils & Gravies

* Mustard
* Mayonnaise, regular
* Tartar sauce
* Barbecue sauce
* Ranch dressing
* Caesar dressing
* Thousand Island dressing
* Honey mustard dressing
* Blue or roquefort cheese dressing
* Soy sauce
* Wasabi
* Fish sauce
* Teriyaki sauce
* Hoisin sauce
* Oyster sauce
* Worcestershire sauce
* Hot pepper sauce
* Salsa, red
* Salsa verde or salsa, green
* Enchilada sauce, red
* Enchilada sauce, green
* Spaghetti sauce
* Gravy, beef
* Gravy, poultry
* Peanut sauce
* Gravy, NFS
* Sauce, NFS
* Ketchup
* Taco sauce
* Olive oil
* Vegetable oil, NFS
* Table fat, NFS
* Jam or jelly, NFS

## Snacks — Chips, Crackers, Popcorn & Salty

* Potato chips, plain
* Potato chips, barbecue flavored
* Potato chips, sour cream and onion flavored
* Potato chips, ruffled, plain
* Tortilla chips, plain
* Pita chips
* Popcorn, ready-to-eat, NFS
* Pretzels, hard, plain, salted
* Crackers, saltine
* Graham crackers
* Rice cake
* Bagel chips
* Cracker chips
* Onion flavored rings
* Corn nuts
* Crackers, flatbread
* Crackers, rice and nuts
* Crackers, wheat
* Corn chips, plain
* Pretzels, hard, plain, lightly salted

## Baked Goods & Cookies

* Cookie, NFS
* Cookie, chocolate chip
* Cookie, oatmeal
* Cookie, peanut butter
* Doughnut, yeast type
* Muffin, NFS
* Cake, pound
* Pie, NFS
* Tart, all types
* Cake or cupcake, NFS
* Cheesecake, plain
* Cake or cupcake, chocolate with chocolate icing, bakery
* Cake or cupcake, white with white icing, bakery
* Doughnut, NFS
* Doughnut, chocolate

## Ice Cream & Frozen Desserts

* Ice cream, vanilla
* Ice cream, chocolate
* Frozen yogurt, NFS
* Ice cream, NFS
* Ice cream cone, NFS

## Fruits & Fruit‑based

* Strawberries, raw
* Blueberries, raw
* Raspberries, raw
* Blackberries, raw
* Watermelon, raw
* Pineapple, raw
* Mango, raw
* Peach, raw
* Pear, Asian, raw
* Tangerine, raw
* Grapefruit, raw
* Kiwi fruit, raw
* Cantaloupe, raw
* Honeydew melon, raw
* Pomegranate, raw
* Papaya, raw
* Cherries, raw
* Raisins
* Cranberries, dried
* Date
* Prune, dried
* Fig, dried
* Applesauce, unsweetened
* Fruit, NFS
* Orange, raw
* Apple, raw
* Banana, raw
* Grapes, raw
* Pear, raw
* Berries, NFS
* Applesauce, regular
* Apple, baked
* Dried, fruit, NFS
* Guacamole, NFS
* Fruit juice, NFS
* Orange juice, 100%, NFS
* Apple juice, 100%
* Grape juice, 100%

## Beverages — Non‑alcoholic

* Water, NFS
* Water, tap
* Water, bottled, plain
* Water, carbonated, plain
* Water, carbonated, flavored
* Water, non-carbonated, flavored
* Coconut water, unsweetened
* Coffee, brewed
* Coffee, espresso
* Coffee, brewed, flavored
* Tea, iced, brewed, black, unsweetened
* Tea, hot, leaf, green
* Tea, hot, herbal
* Soft drink, NFS
* Soft drink, cola
* Soft drink, cola, diet
* Soft drink, ginger ale
* Soft drink, root beer
* Soft drink, fruit flavored, caffeine free
* Fruit juice blend, 100% juice
* Orange juice, 100%,  freshly squeezed
* Cranberry juice, 100%, not a blend
* Pineapple juice, 100%
* Grapefruit juice, 100%, freshly squeezed
* Sports drink, NFS
* Water beverage, fruit flavored

## Milks, Yogurts & Smoothies

* Milk, whole
* Milk, reduced fat (2%)
* Milk, low fat (1%)
* Milk, fat free (skim)
* Milk, NFS
* Non-dairy milk, NFS
* Soy milk, sweetened
* Soy milk, chocolate
* Almond milk, NFS
* Almond milk, sweetened
* Almond milk, chocolate
* Oat milk
* Yogurt, NS as to type of milk, plain
* Yogurt, Greek, NS as to type of milk, plain
* Yogurt, NS as to type of milk, fruit
* Yogurt, NFS
* Yogurt, whole milk, plain
* Yogurt, nonfat milk, plain
* Yogurt, Greek, low fat milk, plain
* Yogurt, low fat milk, fruit
* Yogurt, Greek, low fat milk, fruit
* Yogurt, low fat milk, flavors other than fruit
* Chocolate milk, NFS
* Hot chocolate / cocoa, NFS
* Fruit smoothie, NFS
* Fruit smoothie, bottled
* Fruit smoothie juice drink, with dairy

## Dairy — Cheeses & Fats

* Cheese, American
* Cheese, Cheddar
* Cheese, Feta
* Cheese, Mozzarella, NFS
* Cheese, Provolone
* Cheese, Swiss
* Cheese, cottage, NFS
* Cream cheese, regular, plain
* Sour cream, regular
* Butter, stick
* Cheese, NFS
* Cheese, Colby Jack
* Cheese, Parmesan, dry grated
* Cheese, Parmesan, hard
* Cheese, Ricotta
* Cheese sauce

## Alcoholic Beverages & Drinks

* Beer
* Beer, light
* Wine, red
* Wine, white
* Wine, rose
* Hard cider
* Cocktail, NFS
* Wine, sparkling
* Hard seltzer

## Soups & Stews — All

* Chili, NFS
* Soup, hot and sour
* Soup, egg drop
* Soup, chicken
* Soup, pork or ham
* Soup, broth
* Soup, bisque
* Soup, fish or shrimp
* Stew, beef
* Stew, chicken
* Chili with meat
* Chili with meat and beans
* Soup, NFS
* Soup, chicken noodle
* Soup, vegetable
* Soup, tomato
* Soup, potato

## Mixed Dishes — Asian / Latin / Italian etc.

* Beef curry
* Spaghetti sauce with meat
* Chicken curry
* Paella, NFS

## Pickled & Pickles

* Peppers, jalapenos

## Sweets & Candy

* Candy, NFS




```

================================================================================

## [Results]

### テスト画像: 5枚
- food1.jpg
- food2.jpg
- food3.jpg
- food4.jpg
- food5.jpg

### テストモデル: 4種類
- google/gemma-3-27b-it
- mistralai/Mistral-Small-3.2-24B-Instruct-2506
- Qwen/Qwen3-VL-235B-A22B-Thinking
- meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8

================================================================================

## 詳細結果

### モデル: google/gemma-3-27b-it

- テスト日時: 2025-10-21T17:05:16.514467
- 成功: 5/5画像
- 失敗: 0画像


#### 画像1: food1.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Caesar Salad",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": "Lettuce, salad with assorted vegetables including tomatoes and/or carrots, no dressing",
        "weight_g": 100,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Croutons",
          "weight_g": 20,
          "unlisted": null
        },
        {
          "ingredient_name": "Cheese, Parmesan, dry grated",
          "weight_g": 10,
          "unlisted": null
        },
        {
          "ingredient_name": "Sauce, NFS",
          "weight_g": 30,
          "unlisted": null
        }
      ]
    },
    {
      "dish_name": "Pasta with sauce",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Pasta with sauce, NFS",
        "weight_g": 250,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Iced Tea",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Tea, iced, brewed, black, unsweetened",
        "weight_g": 350,
        "unlisted": null
      },
      "ingredients": []
    }
  ]
}
```

#### 画像2: food2.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Meatloaf with Sides",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": "Meat loaf, NS as to type of meat",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Potato, mashed, from fresh, made with milk",
          "weight_g": 75,
          "unlisted": null
        },
        {
          "ingredient_name": "Macaroni or noodles with cheese",
          "weight_g": 75,
          "unlisted": null
        },
        {
          "ingredient_name": "Classic mixed vegetables, NS as to form, cooked",
          "weight_g": 75,
          "unlisted": null
        },
        {
          "ingredient_name": "Rice pilaf",
          "weight_g": 75,
          "unlisted": null
        }
      ]
    }
  ]
}
```

#### 画像3: food3.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Chicken and Potato Salad",
      "unit_count": 1,
      "confidence": 0.75,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": null,
        "weight_g": 0,
        "unlisted": {
          "display_name": "Mixed Salad",
          "weight_g": 100,
          "nutrition_per_100g": {
            "calorie": 30,
            "protein_g": 2.0,
            "fat_g": 1.0,
            "carbs_g": 4.0
          }
        }
      },
      "ingredients": [
        {
          "ingredient_name": "Chicken, NS as to part and cooking method, skin eaten",
          "weight_g": 150,
          "unlisted": null
        },
        {
          "ingredient_name": "Potato, boiled, NFS",
          "weight_g": 150,
          "unlisted": null
        },
        {
          "ingredient_name": "Tomato, raw",
          "weight_g": 50,
          "unlisted": null
        },
        {
          "ingredient_name": "Corn, raw",
          "weight_g": 50,
          "unlisted": null
        },
        {
          "ingredient_name": "Sauce, NFS",
          "weight_g": 20,
          "unlisted": null
        }
      ]
    }
  ]
}
```

#### 画像4: food4.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Mashed Potatoes with Brussels Sprouts and Meatloaf",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": null,
        "weight_g": 0,
        "unlisted": {
          "display_name": "Plate with mixed foods",
          "weight_g": 400,
          "nutrition_per_100g": {
            "calorie": 150,
            "protein_g": 5,
            "fat_g": 5,
            "carbs_g": 20
          }
        }
      },
      "ingredients": [
        {
          "ingredient_name": "Potato, mashed, from fresh, made with milk",
          "weight_g": 120,
          "unlisted": null
        },
        {
          "ingredient_name": "Brussels sprouts, NS as to form, cooked",
          "weight_g": 100,
          "unlisted": null
        },
        {
          "ingredient_name": "Meat loaf, NS as to type of meat",
          "weight_g": 180,
          "unlisted": null
        }
      ]
    }
  ]
}
```

#### 画像5: food5.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Tacos",
      "unit_count": 2,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Taco, NFS",
        "weight_g": 200,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Beef, ground",
          "weight_g": 60,
          "unlisted": null
        },
        {
          "ingredient_name": "Cheese, Cheddar",
          "weight_g": 20,
          "unlisted": null
        },
        {
          "ingredient_name": "Tomatoes, raw",
          "weight_g": 30,
          "unlisted": null
        },
        {
          "ingredient_name": "Lettuce, iceberg, raw",
          "weight_g": 30,
          "unlisted": null
        },
        {
          "ingredient_name": "Tortilla, flour",
          "weight_g": 60,
          "unlisted": null
        }
      ]
    }
  ]
}
```

### モデル: mistralai/Mistral-Small-3.2-24B-Instruct-2506

- テスト日時: 2025-10-21T17:11:00.386084
- 成功: 5/5画像
- 失敗: 0画像


#### 画像1: food1.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with Tomato Sauce",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Pasta with tomato-based sauce and cheese",
        "weight_g": 200,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Salad",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": "Lettuce, salad with assorted vegetables including tomatoes and/or carrots, no dressing",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Croutons",
          "weight_g": 10,
          "unlisted": null
        },
        {
          "ingredient_name": "Sauce, NFS",
          "weight_g": 10,
          "unlisted": null
        }
      ]
    },
    {
      "dish_name": "Soft Drink",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Soft drink, NFS",
        "weight_g": 300,
        "unlisted": null
      },
      "ingredients": []
    }
  ]
}
```

#### 画像2: food2.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Meatloaf",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Meat loaf, NS as to type of meat",
        "weight_g": 150
      },
      "ingredients": []
    },
    {
      "dish_name": "Mixed Vegetables",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Classic mixed vegetables, NS as to form, cooked",
        "weight_g": 100
      },
      "ingredients": []
    },
    {
      "dish_name": "Mashed Potatoes",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Potato, mashed, NFS",
        "weight_g": 120
      },
      "ingredients": []
    },
    {
      "dish_name": "Macaroni and Cheese",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Macaroni or noodles with cheese",
        "weight_g": 100
      },
      "ingredients": []
    },
    {
      "dish_name": "Rice Pilaf",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Rice pilaf",
        "weight_g": 100
      },
      "ingredients": []
    }
  ]
}
```

#### 画像3: food3.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Grilled Chicken with Salad and Potatoes",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "Chicken, NS as to part and cooking method, skin not eaten",
        "weight_g": 150
      },
      "ingredients": [
        {
          "ingredient_name": "Potato, boiled, NFS",
          "weight_g": 100
        },
        {
          "ingredient_name": "Sweet potato, NFS",
          "weight_g": 50
        },
        {
          "ingredient_name": "Romaine lettuce, raw",
          "weight_g": 30
        },
        {
          "ingredient_name": "Tomatoes, raw",
          "weight_g": 20
        },
        {
          "ingredient_name": "Corn, raw",
          "weight_g": 15
        },
        {
          "ingredient_name": "Sauce, NFS",
          "weight_g": 10
        }
      ]
    }
  ]
}
```

#### 画像4: food4.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Mashed Potatoes with Brussels Sprouts and Meat",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "Potato, mashed, NFS",
        "weight_g": 150
      },
      "ingredients": [
        {
          "ingredient_name": "Brussels sprouts, NS as to form, cooked",
          "weight_g": 100
        },
        {
          "ingredient_name": "Chicken, NS as to part and cooking method, skin not eaten",
          "weight_g": 120
        }
      ]
    }
  ]
}
```

#### 画像5: food5.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Tacos",
      "unit_count": 2,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Taco, NFS",
        "weight_g": 250,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Tomatoes, raw",
          "weight_g": 50,
          "unlisted": null
        },
        {
          "ingredient_name": "Lettuce, iceberg, raw",
          "weight_g": 30,
          "unlisted": null
        },
        {
          "ingredient_name": "Cheese, Cheddar",
          "weight_g": 20,
          "unlisted": null
        },
        {
          "ingredient_name": "Sauce, NFS",
          "weight_g": 10,
          "unlisted": null
        }
      ]
    }
  ]
}
```

### モデル: Qwen/Qwen3-VL-235B-A22B-Thinking

- テスト日時: 2025-10-21T17:14:36.105840
- 成功: 4/5画像
- 失敗: 1画像


#### 画像1: food1.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Penne pasta",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Pasta with tomato-based sauce and cheese",
        "weight_g": 225,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Caesar salad",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": "Romaine lettuce, raw",
        "weight_g": 120,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Croutons",
          "weight_g": 20,
          "unlisted": null
        },
        {
          "ingredient_name": "Caesar dressing",
          "weight_g": 30,
          "unlisted": null
        },
        {
          "ingredient_name": "Cheese, Parmesan, dry grated",
          "weight_g": 10,
          "unlisted": null
        }
      ]
    },
    {
      "dish_name": "Cola",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Soft drink, cola",
        "weight_g": 245,
        "unlisted": null
      },
      "ingredients": []
    }
  ]
}
```

#### 画像2: food2.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Meatloaf with ketchup",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "Meat loaf, NS as to type of meat",
        "weight_g": 145,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Ketchup",
          "weight_g": 15,
          "unlisted": null
        }
      ]
    },
    {
      "dish_name": "Mashed potatoes",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Potato, mashed, NFS",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Macaroni and cheese",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Macaroni or noodles with cheese",
        "weight_g": 125,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Rice pilaf",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Rice pilaf",
        "weight_g": 145,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Mixed vegetables",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Classic mixed vegetables, NS as to form, cooked",
        "weight_g": 100,
        "unlisted": null
      },
      "ingredients": []
    }
  ]
}
```

#### 画像3: food3.jpg
- ステータス: ❌ 失敗
- エラー: 予期せぬエラーが発生しました: APIからのレスポンスが空です。

#### 画像4: food4.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Mashed Potatoes",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Potato, mashed, from fresh, made with milk",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Brussels Sprouts",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Brussels sprouts, NS as to form, cooked",
        "weight_g": 100,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Meat Loaf with Gravy",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "Meat loaf, NS as to type of meat",
        "weight_g": 120,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Gravy, NFS",
          "weight_g": 30,
          "unlisted": null
        }
      ]
    }
  ]
}
```

#### 画像5: food5.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Tacos",
      "unit_count": 2,
      "confidence": 0.85,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "Taco, NFS",
        "weight_g": 240,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Lettuce, iceberg, raw",
          "weight_g": 40,
          "unlisted": null
        },
        {
          "ingredient_name": "Tomatoes, raw",
          "weight_g": 50,
          "unlisted": null
        },
        {
          "ingredient_name": "Cheese, NFS",
          "weight_g": 30,
          "unlisted": null
        }
      ]
    }
  ]
}
```

### モデル: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8

- テスト日時: 2025-10-21T17:10:11.004010
- 成功: 5/5画像
- 失敗: 0画像


#### 画像1: food1.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with sauce and cheese",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Pasta with tomato-based sauce and cheese",
        "weight_g": 350,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Salad",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": "Lettuce, salad with assorted vegetables including tomatoes and/or carrots, no dressing",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Croutons",
          "weight_g": 20,
          "unlisted": null
        },
        {
          "ingredient_name": "Caesar dressing",
          "weight_g": 50,
          "unlisted": null
        }
      ]
    },
    {
      "dish_name": "Iced tea",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Tea, iced, brewed, black, unsweetened",
        "weight_g": 300,
        "unlisted": null
      },
      "ingredients": []
    }
  ]
}
```

#### 画像2: food2.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Meatloaf",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Meat loaf, NS as to type of meat",
        "weight_g": 200,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Mixed Vegetables",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Classic mixed vegetables, NS as to form, cooked",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Rice Pilaf",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Rice pilaf",
        "weight_g": 200,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Mashed Potatoes",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Potato, mashed, from fresh, made with milk",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Macaroni and Cheese",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Macaroni or noodles with cheese",
        "weight_g": 200,
        "unlisted": null
      },
      "ingredients": []
    }
  ]
}
```

#### 画像3: food3.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Grilled Chicken with Potatoes and Salad",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": null,
      "ingredients": [
        {
          "ingredient_name": "Chicken, NS as to part and cooking method, skin not eaten",
          "weight_g": 150,
          "unlisted": null
        },
        {
          "ingredient_name": "Potatoes, boiled, NFS",
          "weight_g": 200,
          "unlisted": null
        },
        {
          "ingredient_name": "Lettuce, salad with assorted vegetables including tomatoes and/or carrots, no dressing",
          "weight_g": 250,
          "unlisted": null
        }
      ]
    }
  ]
}
```

#### 画像4: food4.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Mashed Potatoes",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Potato, mashed, NFS",
        "weight_g": 250,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Roasted Brussels Sprouts",
      "unit_count": 1,
      "confidence": 0.9,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Brussels sprouts, NS as to form, cooked",
        "weight_g": 200,
        "unlisted": null
      },
      "ingredients": []
    },
    {
      "dish_name": "Meatloaf",
      "unit_count": 1,
      "confidence": 0.8,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "Meat loaf, NS as to type of meat",
        "weight_g": 150,
        "unlisted": null
      },
      "ingredients": []
    }
  ]
}
```

#### 画像5: food5.jpg
- ステータス: ✅ 成功
- VLMレスポンス:
```json
{
  "dishes": [
    {
      "dish_name": "Tacos",
      "unit_count": 2,
      "confidence": 0.9,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "Taco, NFS",
        "weight_g": 240,
        "unlisted": null
      },
      "ingredients": [
        {
          "ingredient_name": "Lettuce, raw",
          "weight_g": 60,
          "unlisted": null
        },
        {
          "ingredient_name": "Tomatoes, raw",
          "weight_g": 100,
          "unlisted": null
        },
        {
          "ingredient_name": "Cheese, NFS",
          "weight_g": 40,
          "unlisted": null
        }
      ]
    }
  ]
}
```

================================================================================

## レビュー観点

以下の観点でレビューをお願いします：

1. **食品名リストの最適化**
   - 不要な重複項目の特定
   - 誤認を招く類似項目の統合提案
   - 追加すべき重要な食品名

2. **プロンプトの改善**
   - 曖昧な指示の明確化
   - ルールの優先順位の調整
   - エラーを減らすための追加ルール
   - 具体例でなく、より本質的・一般的な指示への修正（過学習的になあらない様にするため）

3. **VLMモデルの評価**
   - 各モデルの強み・弱みの分析
   - 最適なモデルの推奨
   - モデル固有の問題点

4. **共通エラーパターン**
   - 頻繁に発生する誤認識
   - weight推定の精度問題
   - analysis_methodの選択ミス
