# Vision Language Model (VLM) 比較データ - Mapping Prompt v2/v3

## 目的

Mapping prompt（v2とv3）を用いて各VLMモデルに食事写真を分析させた結果を共有します。
食事写真（別途添付する）と各モデルの出力を比較し、モデルごとに栄養算出に必要な食品認識と量推定の精度を評価してください。

## 評価対象モデルと使用プロンプト

1. **Qwen/Qwen3-VL-235B-A22B-Thinking (v2)** - mapping_prompt_v2.txt使用
2. **Qwen/Qwen3-VL-235B-A22B-Thinking (v3)** - mapping_prompt_v3.txt使用
3. **Qwen/Qwen3-VL-30B-A3B-Thinking (v2)** - mapping_prompt_v2.txt使用
4. **Qwen/Qwen3-VL-30B-A3B-Thinking (v3)** - mapping_prompt_v3.txt使用

## 使用したプロンプト（先頭50行のみ表示）

### 235B-Thinking-v2

```
You are an expert food analyst for a US-based diet app.

TASK
- Analyze ONE meal image and return ONE JSON object ONLY (no extra text).
- Detect each visually separate dish on the plate/tray as one "dish".

MODE (implicit by JSON shape — do NOT output any analysis_method field)
- BASE_DISH mode → use when a standard dish from the list is recognized.
  - base_food ≠ null (must be from [IS_BASE] or [EITHER])
  - ingredients = only visible extras/toppings not implied by the base (can be empty if none)
- INGREDIENTS_ONLY mode → use when no clear standard dish applies (salads/bowls with visible parts, custom/home-made, etc.).
  - base_food = null
  - ingredients = list ALL visible components

FOOD LIST & ROLES (EXACT_FOOD_LIST = authoritative)
- Check every base_food and ingredient against EXACT_FOOD_LIST (CORE) with roles:
  [IS_BASE], [INGREDIENT_ONLY], [SAUCE_ONLY], [EITHER].
- Base dish MUST be from [IS_BASE] or [EITHER]. NEVER use [INGREDIENT_ONLY] or [SAUCE_ONLY] as base_food.
- Ingredients may use any category. [INGREDIENT_ONLY]/[SAUCE_ONLY] are allowed only in ingredients.
- Use the exact string from the list (case-insensitive match allowed; singular/plural normalization ok).
- If an item is NOT in the list: set found_in_list=false and use a concise descriptive item_name (do not force-match or invent a list label).

IMPLICIT CONTENTS (do NOT list these as ingredients in BASE_DISH mode)
- Pizza: dough + sauce + base cheese
- Pasta dishes: pasta + standard sauce
- Sandwiches/Wraps/Burgers: bread/tortilla/bun + standard toppings

OUTPUT — return valid JSON only (double quotes, no comments, no trailing commas)
{
  "dishes": [
    {
      "dish_name": "short descriptive name",
      "unit_count": <int>,
      "confidence": <0.0-1.0>,
      "base_food": null | {
        "item_name": "string",
        "weight_g": <int>,
        "found_in_list": <bool>
      },
      "ingredients": [
        {
          "item_name": "string",
          "weight_g": <int>,
          "found_in_list": <bool>
        }
      ]
    }
  ]
}


...(以下、食品リスト省略)
```

### 235B-Thinking-v3

```
You are an expert food analyst and nutritionist for a US-based diet app.
Analyze ONE meal image and return EXACTLY ONE JSON object (no extra text, no markdown, no comments).

========================
SCOPE & GOAL
========================
- Input: ONE meal image.
- Output: ONE JSON object that describes all visually distinct foods as one or more "dishes".
- Be conservative: do not hallucinate hidden items; only include what is visible or explicitly implicit-in-base (see below).
- Use grams for weights; energy in kcal.

========================
DISH SEGMENTATION (v2)
========================
- Split by visual separation: e.g., burger + fries + cola = 3 dishes.
- Mixed bowls/platters assembled together (e.g., tossed salad, poke bowl, curry-over-rice presented as one bowl) = 1 dish.
- Repeated identical items grouped as one dish with unit_count > 1 (e.g., two identical tacos → one dish with unit_count=2).

========================
CORE FOOD LIST (EXACT_FOOD_LIST) — ROLES
========================
Each EXACT_FOOD_LIST entry has a role tag:
  [IS_BASE]         : pre-defined complete dishes
  [INGREDIENT_ONLY] : raw/simple ingredients (not valid as a base)
  [SAUCE_ONLY]      : sauces/condiments (not valid as a base)
  [EITHER]          : can be used as base or ingredient
- Matching to CORE is case-insensitive, tolerant to singular/plural and ≤1 edit-distance typos.
- When a match is found, return the EXACT string as item_name.

EXACT_FOOD_LIST (CORE) - 1398 Unified Mappings

[IS_BASE - Base Dishes for HYBRID_DECOMPOSITION] (332 items)
These items are pre-defined dishes that should be used as base_food in HYBRID_DECOMPOSITION method.
Examples: 'Caesar salad', 'Mac and cheese', 'Pasta with Tomato Sauce'

1. Adobo
2. Almond butter & jelly sandwich
3. Almond butter sandwich
4. Ambrosia
5. Antipasto platter
6. Apple salad
7. Arepa Dominicana
8. Asian chicken salad (crispy noodles)
9. Asian chicken/turkey salad
10. BLT sandwich
11. Bacon biscuit sandwich
12. Baklava
13. Banana pudding
14. Banana split
15. Barbecue sandwich

...(以下、食品リスト省略)
```

### 30B-Thinking-v2

```
You are an expert food analyst for a US-based diet app.

TASK
- Analyze ONE meal image and return ONE JSON object ONLY (no extra text).
- Detect each visually separate dish on the plate/tray as one "dish".

MODE (implicit by JSON shape — do NOT output any analysis_method field)
- BASE_DISH mode → use when a standard dish from the list is recognized.
  - base_food ≠ null (must be from [IS_BASE] or [EITHER])
  - ingredients = only visible extras/toppings not implied by the base (can be empty if none)
- INGREDIENTS_ONLY mode → use when no clear standard dish applies (salads/bowls with visible parts, custom/home-made, etc.).
  - base_food = null
  - ingredients = list ALL visible components

FOOD LIST & ROLES (EXACT_FOOD_LIST = authoritative)
- Check every base_food and ingredient against EXACT_FOOD_LIST (CORE) with roles:
  [IS_BASE], [INGREDIENT_ONLY], [SAUCE_ONLY], [EITHER].
- Base dish MUST be from [IS_BASE] or [EITHER]. NEVER use [INGREDIENT_ONLY] or [SAUCE_ONLY] as base_food.
- Ingredients may use any category. [INGREDIENT_ONLY]/[SAUCE_ONLY] are allowed only in ingredients.
- Use the exact string from the list (case-insensitive match allowed; singular/plural normalization ok).
- If an item is NOT in the list: set found_in_list=false and use a concise descriptive item_name (do not force-match or invent a list label).

IMPLICIT CONTENTS (do NOT list these as ingredients in BASE_DISH mode)
- Pizza: dough + sauce + base cheese
- Pasta dishes: pasta + standard sauce
- Sandwiches/Wraps/Burgers: bread/tortilla/bun + standard toppings

OUTPUT — return valid JSON only (double quotes, no comments, no trailing commas)
{
  "dishes": [
    {
      "dish_name": "short descriptive name",
      "unit_count": <int>,
      "confidence": <0.0-1.0>,
      "base_food": null | {
        "item_name": "string",
        "weight_g": <int>,
        "found_in_list": <bool>
      },
      "ingredients": [
        {
          "item_name": "string",
          "weight_g": <int>,
          "found_in_list": <bool>
        }
      ]
    }
  ]
}


...(以下、食品リスト省略)
```

### 30B-Thinking-v3

```
You are an expert food analyst and nutritionist for a US-based diet app.
Analyze ONE meal image and return EXACTLY ONE JSON object (no extra text, no markdown, no comments).

========================
SCOPE & GOAL
========================
- Input: ONE meal image.
- Output: ONE JSON object that describes all visually distinct foods as one or more "dishes".
- Be conservative: do not hallucinate hidden items; only include what is visible or explicitly implicit-in-base (see below).
- Use grams for weights; energy in kcal.

========================
DISH SEGMENTATION (v2)
========================
- Split by visual separation: e.g., burger + fries + cola = 3 dishes.
- Mixed bowls/platters assembled together (e.g., tossed salad, poke bowl, curry-over-rice presented as one bowl) = 1 dish.
- Repeated identical items grouped as one dish with unit_count > 1 (e.g., two identical tacos → one dish with unit_count=2).

========================
CORE FOOD LIST (EXACT_FOOD_LIST) — ROLES
========================
Each EXACT_FOOD_LIST entry has a role tag:
  [IS_BASE]         : pre-defined complete dishes
  [INGREDIENT_ONLY] : raw/simple ingredients (not valid as a base)
  [SAUCE_ONLY]      : sauces/condiments (not valid as a base)
  [EITHER]          : can be used as base or ingredient
- Matching to CORE is case-insensitive, tolerant to singular/plural and ≤1 edit-distance typos.
- When a match is found, return the EXACT string as item_name.

EXACT_FOOD_LIST (CORE) - 1398 Unified Mappings

[IS_BASE - Base Dishes for HYBRID_DECOMPOSITION] (332 items)
These items are pre-defined dishes that should be used as base_food in HYBRID_DECOMPOSITION method.
Examples: 'Caesar salad', 'Mac and cheese', 'Pasta with Tomato Sauce'

1. Adobo
2. Almond butter & jelly sandwich
3. Almond butter sandwich
4. Ambrosia
5. Antipasto platter
6. Apple salad
7. Arepa Dominicana
8. Asian chicken salad (crispy noodles)
9. Asian chicken/turkey salad
10. BLT sandwich
11. Bacon biscuit sandwich
12. Baklava
13. Banana pudding
14. Banana split
15. Barbecue sandwich

...(以下、食品リスト省略)
```


---


# 📸 画像21-30のデータ

---

## 📸 画像21

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Tacos"
      "base_food": {"item_name": "Taco", "weight_g": 210}
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 125},
        {"item_name": "Tomatoes (raw)", "weight_g": 80},
        {"item_name": "Cheddar", "weight_g": 95},
        {"item_name": "Sour cream", "weight_g": 50}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Tacos"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Taco", "weight_g": 240, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bell peppers (mixed)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Ground beef", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sour cream", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cheddar", "weight_g": 45, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Taco"
      "base_food": {"item_name": "Taco", "weight_g": 450}
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 60},
        {"item_name": "Tomato", "weight_g": 45},
        {"item_name": "Cheddar", "weight_g": 75},
        {"item_name": "Sour cream", "weight_g": 30},
        {"item_name": "Taco sauce", "weight_g": 15}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Taco"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Taco", "weight_g": 300, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cheddar", "weight_g": 45, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sour cream", "weight_g": 15, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像22

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with shrimp and broccoli"
      "base_food": {"item_name": "Pasta with Cream Sauce", "weight_g": 250}
      "ingredients": [
        {"item_name": "Shrimp", "weight_g": 100},
        {"item_name": "Broccoli (cooked)", "weight_g": 75}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 100},
        {"item_name": "Carrots (raw)", "weight_g": 50},
        {"item_name": "Red bell pepper", "weight_g": 40},
        {"item_name": "Green cabbage", "weight_g": 60}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with shrimp and broccoli"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Pasta", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Shrimp", "weight_g": 90, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed greens salad with vegetables"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (shredded)", "weight_g": 30, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Red peppers", "weight_g": 30, "found_in_list": false}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with Shrimp and Broccoli"
      "base_food": {"item_name": "Pasta", "weight_g": 120}
      "ingredients": [
        {"item_name": "Shrimp", "weight_g": 75},
        {"item_name": "Broccoli (cooked)", "weight_g": 50}
      ]
    },
    {
      "dish_name": "Vegetable Salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 30},
        {"item_name": "Carrots (raw)", "weight_g": 20},
        {"item_name": "Red bell pepper", "weight_g": 15},
        {"item_name": "Green cabbage", "weight_g": 10}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with Shrimp and Broccoli"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pasta", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Shrimp", "weight_g": 100, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Vegetable Salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cabbage", "weight_g": 20, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像23

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mixed plate with salad, rice, beef, egg and broccoli"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 100},
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Tomatoes (raw)", "weight_g": 50},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 20},
        {"item_name": "Broccoli (cooked)", "weight_g": 80},
        {"item_name": "Cooked rice", "weight_g": 150},
        {"item_name": "Beef (for use with vegetables)", "weight_g": 100},
        {"item_name": "Fried eggs", "weight_g": 60},
        {"item_name": "Mayonnaise", "weight_g": 20}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Beef and rice platter with salad and sides"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Beef and rice", "weight_g": 250, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Fried eggs", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mayonnaise", "weight_g": 20, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Bibimbap"
      "base_food": {"item_name": "Bibimbap", "weight_g": 250}
    },
    {
      "dish_name": "Vegetable salad"
      "ingredients": [
        {"item_name": "Cucumber", "weight_g": 50},
        {"item_name": "Tomato", "weight_g": 30},
        {"item_name": "Carrot", "weight_g": 20},
        {"item_name": "Lettuce", "weight_g": 40},
        {"item_name": "Broccoli", "weight_g": 30}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Beef and rice"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef and rice", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Fried egg"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Fried eggs", "weight_g": 70, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Broccoli"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Broccoli (cooked)", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (Raw)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Onions", "weight_g": 15, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (Raw)", "weight_g": 35, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像24

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chicken garden salad with egg and sesame seeds"
      "base_food": {"item_name": "Chicken or turkey garden salad", "weight_g": 300}
      "ingredients": [
        {"item_name": "Boiled or poached egg", "weight_g": 100},
        {"item_name": "Sesame seeds", "weight_g": 5},
        {"item_name": "Tomatoes (raw)", "weight_g": 50},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 20},
        {"item_name": "Cranberries (fresh)", "weight_g": 15}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Chicken garden salad bowl"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken or turkey garden salad", "weight_g": 265, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Boiled or poached egg", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sesame seeds", "weight_g": 5, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Cobb salad"
      "base_food": {"item_name": "Cobb salad", "weight_g": 495}
      "ingredients": [
        {"item_name": "Sesame seeds", "weight_g": 5}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Asian chicken/turkey salad with hard-boiled eggs and tomatoes"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Asian chicken/turkey salad", "weight_g": 250, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Boiled or poached egg", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像25

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chili dog with cheese"
      "base_food": {"item_name": "Chili hot dog", "weight_g": 220}
      "ingredients": [
        {"item_name": "Cheddar", "weight_g": 15},
        {"item_name": "Monterey Jack", "weight_g": 5}
      ]
    },
    {
      "dish_name": "Ridged potato chips"
      "base_food": {"item_name": "Potato Chips", "weight_g": 50}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Chili hot dog with cheese"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chili hot dog", "weight_g": 180, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Shredded cheese", "weight_g": 30, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Potato chips"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Potato Chips", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chili hot dog with cheese"
      "base_food": {"item_name": "Chili hot dog", "weight_g": 300}
      "ingredients": [
        {"item_name": "Shredded cheese", "weight_g": 50}
      ]
    },
    {
      "dish_name": "Potato chips"
      "base_food": {"item_name": "Potato Chips", "weight_g": 50}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Chili hot dog with cheese"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chili hot dog", "weight_g": 230, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Shredded cheese", "weight_g": 20, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Potato chips"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Potato Chips", "weight_g": 30, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像26

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with tomato sauce and toppings"
      "base_food": {"item_name": "Pasta with Tomato Sauce", "weight_g": 200}
      "ingredients": [
        {"item_name": "Pepperoni", "weight_g": 50},
        {"item_name": "Green pepper (ingredient)", "weight_g": 30},
        {"item_name": "Parmesan", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 40},
        {"item_name": "Green cabbage", "weight_g": 60},
        {"item_name": "Carrots (raw)", "weight_g": 50}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Spaghetti with meatballs and sausage"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pasta with Tomato Sauce", "weight_g": 300, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Meatballs", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Italian sausage", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bell peppers (mixed)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Parmesan", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 80, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (raw)", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mixed vegetables", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with Tomato Sauce"
      "base_food": {"item_name": "Pasta with Tomato Sauce", "weight_g": 350}
      "ingredients": [
        {"item_name": "Sausage", "weight_g": 50},
        {"item_name": "Green pepper", "weight_g": 20},
        {"item_name": "Parmesan", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Vegetable salad bowl"
      "ingredients": [
        {"item_name": "Papaya", "weight_g": 100},
        {"item_name": "Carrots", "weight_g": 50},
        {"item_name": "Green pepper", "weight_g": 30},
        {"item_name": "Tomatoes", "weight_g": 40}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with Tomato Sauce"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pasta with Tomato Sauce", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Beef sausage", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Green pepper", "weight_g": 15, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 15, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Parmesan", "weight_g": 5, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Vegetable salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Vegetable salad", "weight_g": 150, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像27

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chicken salad"
      "base_food": {"item_name": "Chicken or turkey salad", "weight_g": 100}
    },
    {
      "dish_name": "Beef and vegetables"
      "base_food": {"item_name": "Beef and vegetables", "weight_g": 120}
    },
    {
      "dish_name": "Beef, rice & vegetables with dumpling"
      "base_food": {"item_name": "Beef, rice & vegetables", "weight_g": 250}
      "ingredients": [
        {"item_name": "Dumpling (no meat)", "weight_g": 30}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Chicken salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken or turkey salad", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Beef and pepper stir fry"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef with vegetables", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Beef, rice & vegetables"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef, rice & vegetables", "weight_g": 350, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chicken salad"
      "ingredients": [
        {"item_name": "chicken", "weight_g": 150},
        {"item_name": "mayonnaise", "weight_g": 50}
      ]
    },
    {
      "dish_name": "Beef and rice"
      "base_food": {"item_name": "Beef and rice", "weight_g": 250}
      "ingredients": [
        {"item_name": "cabbage", "weight_g": 30},
        {"item_name": "red pepper", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Beef and vegetables"
      "base_food": {"item_name": "Beef and vegetables", "weight_g": 200}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Chicken salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken salad", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Beef and vegetables"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef and vegetables", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sauce", "weight_g": 20, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Beef and rice"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef and rice", "weight_g": 250, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像28

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mixed salad greens"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 150}
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 50},
        {"item_name": "Cucumber (Raw)", "weight_g": 50}
      ]
    },
    {
      "dish_name": "Pizza (Meat & Vegetables)"
      "base_food": {"item_name": "Pizza (Meat & Vegetables)", "weight_g": 300}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Pizza (Meat & Vegetables)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Pizza (Meat & Vegetables)", "weight_g": 360, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed salad greens"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 150, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pizza slices"
      "base_food": {"item_name": "Pizza (Meat & Vegetables)", "weight_g": 300}
      "ingredients": [
        {"item_name": "Pepperoni", "weight_g": 20},
        {"item_name": "Mushrooms", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Salad"
      "ingredients": [
        {"item_name": "Cucumbers", "weight_g": 50},
        {"item_name": "Tomatoes", "weight_g": 30},
        {"item_name": "Mixed greens", "weight_g": 120}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Meat pizza"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Pizza (Meat)", "weight_g": 300, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Vegetable salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Vegetable salad", "weight_g": 150, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像29

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with chicken and cucumber"
      "base_food": {"item_name": "Chicken or turkey with noodles", "weight_g": 350}
      "ingredients": [
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Shredded cheese", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Mixed greens salad with tomatoes and cucumber"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 150}
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 70},
        {"item_name": "Cucumber (Raw)", "weight_g": 30}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with chicken"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken or turkey with noodles", "weight_g": 300, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Zucchini", "weight_g": 50, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Parmesan", "weight_g": 15, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed greens salad"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chicken Noodles"
      "base_food": {"item_name": "Chicken or turkey with noodles", "weight_g": 300}
      "ingredients": [
        {"item_name": "zucchini", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Vegetable Salad"
      "ingredients": [
        {"item_name": "lettuce", "weight_g": 50},
        {"item_name": "tomatoes", "weight_g": 30},
        {"item_name": "cucumbers", "weight_g": 20}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Lettuce Salad with Tomatoes and Cucumbers"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Lettuce salad", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomato", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken with Noodles and Zucchini"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken or turkey with noodles", "weight_g": 180, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Zucchini", "weight_g": 20, "found_in_list": false}
      ]
    }
  ]
}
```

---

## 📸 画像30

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Plated dinner with mixed greens, pasta, and chicken"
      "ingredients": [
        {"item_name": "Arugula", "weight_g": 50},
        {"item_name": "Lettuce", "weight_g": 50},
        {"item_name": "Tomatoes (raw)", "weight_g": 80},
        {"item_name": "Cucumber (For Sandwich)", "weight_g": 60},
        {"item_name": "Pasta", "weight_g": 120},
        {"item_name": "Pesto Sauce", "weight_g": 30},
        {"item_name": "Chicken (unspecified cut/method)", "weight_g": 150},
        {"item_name": "White sauce or gravy", "weight_g": 50}
      ]
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Mixed greens salad"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cheese tortellini with pesto"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Cheese tortellini", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Pesto Sauce", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Meat with sauce"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Meat with sauce", "weight_g": 180, "found_in_list": true}
      ]
    }
  ]
}
```

### 30B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Green salad"
      "base_food": {"item_name": "Lettuce salad", "weight_g": 150}
      "ingredients": [
        {"item_name": "Tomato", "weight_g": 30},
        {"item_name": "Cucumber", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Pasta with pesto"
      "base_food": {"item_name": "Pasta", "weight_g": 120}
      "ingredients": [
        {"item_name": "Pesto Sauce", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Chicken with cream sauce"
      "base_food": {"item_name": "Chicken", "weight_g": 150}
      "ingredients": [
        {"item_name": "Cream Sauce (for Vegetables)", "weight_g": 30}
      ]
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Vegetable Salad"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Tomato cucumber salad", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Pesto Tortellini"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pasta", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Pesto Sauce", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken with Sauce"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken or turkey with sauce", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---
