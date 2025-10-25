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


# 📸 画像31-40のデータ

---

## 📸 画像31

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Fish plate with salad and sweet potatoes"
      "ingredients": [
        {"item_name": "White fish fillet", "weight_g": 150},
        {"item_name": "Lettuce", "weight_g": 30},
        {"item_name": "Arugula", "weight_g": 25},
        {"item_name": "Strawberries", "weight_g": 45},
        {"item_name": "Cucumber (Raw)", "weight_g": 35},
        {"item_name": "Pecans", "weight_g": 15},
        {"item_name": "Baked sweet potato", "weight_g": 110},
        {"item_name": "Lemon", "weight_g": 15}
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
      "dish_name": "Plated fish with salad and sweet potatoes"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "White fish fillet", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Strawberries", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Pecans", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Baked sweet potato", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Lemon", "weight_g": 20, "found_in_list": true}
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
      "dish_name": "Breaded chicken pieces"
      "base_food": {"item_name": "Chicken (unspecified cut/method)", "weight_g": 450}
    },
    {
      "dish_name": "Fruit and vegetable salad"
      "base_food": {"item_name": "Salad", "weight_g": 200}
      "ingredients": [
        {"item_name": "Strawberries", "weight_g": 50},
        {"item_name": "Cucumbers", "weight_g": 50},
        {"item_name": "Pecans", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Baked sweet potato cubes"
      "base_food": {"item_name": "Baked sweet potato", "weight_g": 200}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Salad with strawberries, cucumber, mixed greens"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Strawberries", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Baked sweet potato with lemon wedge"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Baked sweet potato", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Lemon wedge", "weight_g": 15, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Breaded chicken"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken", "weight_g": 150, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像32

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Beef stroganoff with rice"
      "base_food": {"item_name": "Beef stroganoff", "weight_g": 250}
      "ingredients": [
        {"item_name": "Cooked rice", "weight_g": 150},
        {"item_name": "Dried herbs", "weight_g": 5}
      ]
    },
    {
      "dish_name": "Mixed green salad"
      "ingredients": [
        {"item_name": "Mixed salad greens", "weight_g": 100},
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Bell peppers (mixed)", "weight_g": 30}
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
      "dish_name": "Beef, rice & vegetables"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef, rice & vegetables", "weight_g": 450, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed green salad"
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
      "dish_name": "Beef Stroganoff with Rice"
      "base_food": {"item_name": "Beef stroganoff", "weight_g": 250}
      "ingredients": [
        {"item_name": "White rice (cooked)", "weight_g": 150}
      ]
    },
    {
      "dish_name": "Green Salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 100},
        {"item_name": "Cucumber", "weight_g": 50},
        {"item_name": "Tomato", "weight_g": 50},
        {"item_name": "Red pepper", "weight_g": 50},
        {"item_name": "Arugula", "weight_g": 30},
        {"item_name": "Spinach", "weight_g": 20}
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
      "dish_name": "Beef stroganoff"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef stroganoff", "weight_g": 350, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Tomato cucumber salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Tomato cucumber salad", "weight_g": 150, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像33

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chicken with vegetables and couscous"
      "ingredients": [
        {"item_name": "Chicken thigh", "weight_g": 150},
        {"item_name": "Carrots (cooked)", "weight_g": 60},
        {"item_name": "Bell peppers (mixed)", "weight_g": 50},
        {"item_name": "Zucchini", "weight_g": 40},
        {"item_name": "Onions", "weight_g": 50},
        {"item_name": "Couscous (Plain, Cooked)", "weight_g": 150}
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
      "dish_name": "Chicken with vegetables and couscous"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken or turkey with vegetables", "weight_g": 260, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Couscous (Plain, Cooked)", "weight_g": 110, "found_in_list": true}
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
      "dish_name": "Chicken thigh with toppings"
      "base_food": {"item_name": "Chicken thigh", "weight_g": 150}
      "ingredients": [
        {"item_name": "Garlic", "weight_g": 5},
        {"item_name": "Almonds", "weight_g": 5}
      ]
    },
    {
      "dish_name": "Couscous (Plain, Cooked)"
      "base_food": {"item_name": "Couscous (Plain, Cooked)", "weight_g": 120}
    },
    {
      "dish_name": "Stir-fry vegetables"
      "base_food": {"item_name": "Stir-fry vegetables", "weight_g": 160}
      "ingredients": [
        {"item_name": "Pickles", "weight_g": 20}
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
      "dish_name": "Chicken thigh with almonds"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken thigh", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Almonds", "weight_g": 10, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Couscous (Plain, Cooked)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Couscous (Plain, Cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed vegetables"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mixed vegetables", "weight_g": 120, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像34

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Roasted chicken thigh"
      "base_food": {"item_name": "Chicken thigh", "weight_g": 150}
    },
    {
      "dish_name": "Baked potatoes"
      "base_food": {"item_name": "Baked potato", "weight_g": 120}
    },
    {
      "dish_name": "Mixed greens salad"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 70}
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 20},
        {"item_name": "Carrots (raw)", "weight_g": 10}
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
      "dish_name": "Hash browns"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Hash browns", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken thigh"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken thigh", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed salad greens"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 120, "found_in_list": true}
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
      "dish_name": "Scalloped potatoes"
      "base_food": {"item_name": "Scalloped potatoes", "weight_g": 180}
      "ingredients": [
        {"item_name": "Bacon bits", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Grilled chicken thigh"
      "base_food": {"item_name": "Chicken thigh", "weight_g": 120}
    },
    {
      "dish_name": "Mixed vegetable salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 60},
        {"item_name": "Tomato", "weight_g": 30},
        {"item_name": "Carrot", "weight_g": 25},
        {"item_name": "Onion", "weight_g": 15}
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
      "dish_name": "Scalloped potatoes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Scalloped potatoes", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken breast"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Vegetable salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Vegetable salad", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像35

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Plated dinner with steak, rice, vegetables and salad"
      "ingredients": [
        {"item_name": "Beef steak", "weight_g": 120},
        {"item_name": "Cooked rice", "weight_g": 80},
        {"item_name": "Broccoli (cooked)", "weight_g": 40},
        {"item_name": "Baked potato", "weight_g": 70},
        {"item_name": "Lettuce", "weight_g": 50},
        {"item_name": "Tomatoes (raw)", "weight_g": 25},
        {"item_name": "Cucumber (Raw)", "weight_g": 20},
        {"item_name": "Grilled cheese", "weight_g": 15}
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
      "dish_name": "Plated steak dinner with sides"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 40, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumbers (raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Grilled item", "weight_g": 60, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Yellow rice (cooked)", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Roasted potatoes", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Beef steak", "weight_g": 150, "found_in_list": true}
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
      "base_food": {"item_name": "Cobb salad", "weight_g": 150}
    },
    {
      "dish_name": "Yellow rice"
      "base_food": {"item_name": "Yellow rice", "weight_g": 120}
    },
    {
      "dish_name": "Broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 80}
    },
    {
      "dish_name": "Potato wedges"
      "base_food": {"item_name": "Potato", "weight_g": 100}
    },
    {
      "dish_name": "Beef steak"
      "base_food": {"item_name": "Beef steak", "weight_g": 150}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bacon (cooked)", "weight_g": 10, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Yellow rice"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Yellow rice (cooked)", "weight_g": 150, "found_in_list": true}
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
      "dish_name": "Beef steak"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef steak", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Potato wedges"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Potato", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像36

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Grilled chicken with broccoli, salad and couscous"
      "ingredients": [
        {"item_name": "Chicken (unspecified cut/method)", "weight_g": 150},
        {"item_name": "Broccoli (cooked)", "weight_g": 100},
        {"item_name": "Spinach (raw)", "weight_g": 50},
        {"item_name": "Bell peppers (mixed)", "weight_g": 50},
        {"item_name": "Cucumber (Raw)", "weight_g": 30},
        {"item_name": "Couscous (Plain, Cooked)", "weight_g": 100}
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
      "dish_name": "Balanced meal platter"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Chicken breast", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Couscous (Plain, Cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bell peppers (mixed)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Salad dressing (generic)", "weight_g": 10, "found_in_list": true}
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
      "dish_name": "Chicken thigh"
      "base_food": {"item_name": "Chicken thigh", "weight_g": 150}
    },
    {
      "dish_name": "Vegetable salad"
      "ingredients": [
        {"item_name": "Spinach (raw)", "weight_g": 80},
        {"item_name": "Bell peppers (mixed)", "weight_g": 30},
        {"item_name": "Cucumber (Raw)", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Broccoli (cooked)"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Couscous (Plain, Cooked)"
      "base_food": {"item_name": "Couscous (Plain, Cooked)", "weight_g": 120}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Chicken thighs"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken thigh", "weight_g": 300, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Couscous"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Couscous (Plain, Cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed salad greens"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Red pepper (cooked, ingredient)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Salad dressing (generic)", "weight_g": 10, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像37

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Chicken with garlic"
      "base_food": {"item_name": "Chicken or turkey with sauces/starches", "weight_g": 180}
      "ingredients": [
        {"item_name": "Garlic", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Pasta with pesto"
      "ingredients": [
        {"item_name": "Pasta", "weight_g": 120},
        {"item_name": "Pesto Sauce", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Sliced tomatoes"
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 100}
      ]
    },
    {
      "dish_name": "Coleslaw"
      "base_food": {"item_name": "Coleslaw", "weight_g": 100}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Sliced tomatoes"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Garlic chicken"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Chicken breast", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Garlic", "weight_g": 10, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Coleslaw"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Coleslaw", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Penne with pesto"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Pasta", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Pesto Sauce", "weight_g": 30, "found_in_list": true}
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
      "dish_name": "Tomato slices"
      "base_food": {"item_name": "Tomatoes (raw)", "weight_g": 100}
    },
    {
      "dish_name": "Chicken with nuts"
      "base_food": {"item_name": "Chicken", "weight_g": 150}
      "ingredients": [
        {"item_name": "Peanuts", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Coleslaw"
      "ingredients": [
        {"item_name": "Cabbage (raw)", "weight_g": 80},
        {"item_name": "Mayonnaise", "weight_g": 40}
      ]
    },
    {
      "dish_name": "Pasta with pesto"
      "base_food": {"item_name": "Pasta", "weight_g": 150}
      "ingredients": [
        {"item_name": "Pesto Sauce", "weight_g": 30}
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
      "dish_name": "Sliced Tomatoes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Tomato (raw)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken Breast with Nuts"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Nuts (unspecified)", "weight_g": 10, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Coleslaw"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Coleslaw", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Pasta with Pesto"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pasta", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Pesto Sauce", "weight_g": 10, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像38

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Beef stew with potatoes"
      "base_food": {"item_name": "Beef stew with potatoes (PR style)", "weight_g": 400}
    },
    {
      "dish_name": "Mixed vegetable salad"
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 100},
        {"item_name": "Cucumber (raw)", "weight_g": 80},
        {"item_name": "Avocado", "weight_g": 60},
        {"item_name": "Spinach (raw)", "weight_g": 50}
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
      "dish_name": "Beef stew with potatoes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef stew with potatoes (PR style)", "weight_g": 450, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Tomato cucumber salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Tomato cucumber salad", "weight_g": 250, "found_in_list": true}
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
      "dish_name": "Beef stew with potatoes (PR style)"
      "base_food": {"item_name": "Beef stew with potatoes (PR style)", "weight_g": 450}
      "ingredients": [
        {"item_name": "sour cream", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Vegetable salad"
      "ingredients": [
        {"item_name": "tomato", "weight_g": 100},
        {"item_name": "cucumber", "weight_g": 80},
        {"item_name": "avocado", "weight_g": 50},
        {"item_name": "spinach", "weight_g": 30}
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
      "dish_name": "Beef Curry"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef curry", "weight_g": 400, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cream", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Vegetable Salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomato (raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像39

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pasta with asparagus and bacon"
      "base_food": {"item_name": "Pasta with Cream Sauce", "weight_g": 200}
      "ingredients": [
        {"item_name": "Asparagus (cooked)", "weight_g": 50},
        {"item_name": "Bacon (cooked)", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "ingredients": [
        {"item_name": "Cucumber (Raw)", "weight_g": 40},
        {"item_name": "Avocado", "weight_g": 30},
        {"item_name": "Bell peppers (mixed)", "weight_g": 30},
        {"item_name": "Lettuce", "weight_g": 50}
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
      "dish_name": "Pasta with asparagus and meat"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Pasta", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Asparagus", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bacon (cooked)", "weight_g": 30, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bell peppers (mixed)", "weight_g": 10, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 100, "found_in_list": true}
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
      "dish_name": "Pasta with Cream Sauce"
      "base_food": {"item_name": "Pasta with Cream Sauce", "weight_g": 200}
      "ingredients": [
        {"item_name": "Asparagus", "weight_g": 50},
        {"item_name": "Bacon", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Vegetable Salad"
      "base_food": {"item_name": "Vegetable salad", "weight_g": 150}
      "ingredients": [
        {"item_name": "Avocado", "weight_g": 50},
        {"item_name": "Cucumber", "weight_g": 40},
        {"item_name": "Tomatoes", "weight_g": 30},
        {"item_name": "Lettuce", "weight_g": 20}
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
      "dish_name": "Pasta with Asparagus and Bacon"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pasta", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Asparagus", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bacon (cooked)", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Salad with Avocado, Tomato, Cucumber, and Lettuce"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomato (raw)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (raw)", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像40

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mixed greens salad"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 150}
      "ingredients": [
        {"item_name": "Cucumber (Raw)", "weight_g": 30},
        {"item_name": "Bell peppers (mixed)", "weight_g": 20},
        {"item_name": "Carrots (raw)", "weight_g": 15},
        {"item_name": "Avocado", "weight_g": 25}
      ]
    },
    {
      "dish_name": "Meat & vegetable pizza"
      "base_food": {"item_name": "Pizza (Meat & Vegetables)", "weight_g": 300}
      "ingredients": [
        {"item_name": "Ham", "weight_g": 40},
        {"item_name": "Olives", "weight_g": 20}
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
      "dish_name": "Mixed greens salad with vegetables"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Bell peppers (mixed)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (raw)", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Pizza with meat and vegetables"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Pizza (Meat & Vegetables)", "weight_g": 180, "found_in_list": true}
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
      "dish_name": "Pizza with meat and vegetables"
      "base_food": {"item_name": "Pizza (Meat & Vegetables)", "weight_g": 450}
      "ingredients": [
        {"item_name": "Olives", "weight_g": 30},
        {"item_name": "Bacon (cooked)", "weight_g": 40},
        {"item_name": "Prosciutto", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "ingredients": [
        {"item_name": "Mixed salad greens", "weight_g": 80},
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Avocado", "weight_g": 70},
        {"item_name": "Bell peppers (mixed)", "weight_g": 40},
        {"item_name": "Carrots (raw)", "weight_g": 30}
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
      "dish_name": "Pizza (Meat & Vegetables)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Pizza (Meat & Vegetables)", "weight_g": 300, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 70, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Cucumber", "weight_g": 30, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Red pepper", "weight_g": 20, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 20, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Carrot", "weight_g": 10, "found_in_list": false}
      ]
    }
  ]
}
```

---
