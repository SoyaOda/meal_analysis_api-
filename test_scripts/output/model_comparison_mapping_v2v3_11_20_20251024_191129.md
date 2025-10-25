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


# 📸 画像11-20のデータ

---

## 📸 画像11

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Lasagna with meat"
      "base_food": {"item_name": "Lasagna with meat", "weight_g": 350}
    },
    {
      "dish_name": "Mixed green salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 60},
        {"item_name": "Arugula", "weight_g": 30},
        {"item_name": "Cucumber (Raw)", "weight_g": 40},
        {"item_name": "Avocado", "weight_g": 30},
        {"item_name": "Fig", "weight_g": 20}
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
      "dish_name": "Lasagna with meat"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Lasagna with meat", "weight_g": 350, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed green salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Fig", "weight_g": 20, "found_in_list": true}
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
      "dish_name": "Lasagna with meat"
      "base_food": {"item_name": "Lasagna with meat", "weight_g": 300}
    },
    {
      "dish_name": "Mixed greens salad"
      "ingredients": [
        {"item_name": "Mixed salad greens", "weight_g": 80},
        {"item_name": "Cucumber", "weight_g": 20},
        {"item_name": "Avocado", "weight_g": 15},
        {"item_name": "Fig", "weight_g": 5}
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
      "dish_name": "Lasagna with meat"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Lasagna with meat", "weight_g": 250, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Lettuce salad"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Lettuce salad", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 25, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Fig", "weight_g": 15, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Ham", "weight_g": 10, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像12

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Omelet with salsa and vegetable sides"
      "base_food": {"item_name": "Omelet or scrambled eggs", "weight_g": 200}
      "ingredients": [
        {"item_name": "Salsa", "weight_g": 50},
        {"item_name": "Lettuce", "weight_g": 60},
        {"item_name": "Tomatoes (raw)", "weight_g": 30},
        {"item_name": "Broccoli (cooked)", "weight_g": 70},
        {"item_name": "Corn (Cooked)", "weight_g": 40}
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
      "dish_name": "Omelet with salsa"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Omelet or scrambled eggs", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Salsa", "weight_g": 30, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed salad greens"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Broccoli and corn side"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Corn (Cooked)", "weight_g": 50, "found_in_list": true}
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
      "dish_name": "Scrambled eggs"
      "base_food": {"item_name": "Omelet or scrambled eggs", "weight_g": 200}
      "ingredients": [
        {"item_name": "Tomato sauce for vegetables", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Lettuce salad"
      "base_food": {"item_name": "Lettuce salad", "weight_g": 150}
      "ingredients": [
        {"item_name": "Tomato", "weight_g": 20},
        {"item_name": "Onion", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Broccoli and corn"
      "ingredients": [
        {"item_name": "Broccoli (cooked)", "weight_g": 60},
        {"item_name": "Corn (Cooked)", "weight_g": 40}
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
      "dish_name": "Scrambled eggs with red sauce"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Omelet or scrambled eggs", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Spaghetti sauce (red)", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Lettuce salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Lettuce salad", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Broccoli and corn"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 80, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Corn (Cooked)", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像13

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Tacos"
      "base_food": {"item_name": "Taco", "weight_g": 300}
      "ingredients": [
        {"item_name": "Bell peppers (mixed)", "weight_g": 90},
        {"item_name": "Onions", "weight_g": 30},
        {"item_name": "Queso (Mexican cheese)", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Corn on the cob"
      "ingredients": [
        {"item_name": "Corn (Cooked)", "weight_g": 100}
      ]
    },
    {
      "dish_name": "Grapes"
      "ingredients": [
        {"item_name": "Grapes", "weight_g": 100}
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
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Taco", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Corn on the cob"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Corn (Cooked)", "weight_g": 175, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Red grapes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Grapes", "weight_g": 100, "found_in_list": true}
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
      "dish_name": "Tacos"
      "base_food": {"item_name": "Taco", "weight_g": 100}
      "ingredients": [
        {"item_name": "Red pepper", "weight_g": 25},
        {"item_name": "Green pepper", "weight_g": 20},
        {"item_name": "Cheese", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Corn"
      "base_food": {"item_name": "Corn (Cooked)", "weight_g": 150}
    },
    {
      "dish_name": "Grapes"
      "base_food": {"item_name": "Grapes", "weight_g": 100}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Tacos"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Taco", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Corn on the cob"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Corn (Cooked)", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Grapes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Grapes", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像14

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mixed greens salad"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 150}
      "ingredients": [
        {"item_name": "Broccoli (raw)", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Mashed sweet potatoes"
      "base_food": {"item_name": "Mashed/candied sweet potato", "weight_g": 120}
    },
    {
      "dish_name": "Chicken and rice"
      "base_food": {"item_name": "Chicken or turkey with rice", "weight_g": 300}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Chicken and sides platter"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Mixed salad greens", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mashed/candied sweet potato", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Yellow rice (cooked)", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Chicken breast", "weight_g": 180, "found_in_list": true}
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
      "dish_name": "Mixed greens salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 80},
        {"item_name": "Broccoli", "weight_g": 40}
      ]
    },
    {
      "dish_name": "Chicken (unspecified cut/method)"
      "base_food": {"item_name": "Chicken (unspecified cut/method)", "weight_g": 200}
    },
    {
      "dish_name": "Rice (cooked)"
      "base_food": {"item_name": "Rice (cooked)", "weight_g": 150}
      "ingredients": [
        {"item_name": "Tomato", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Mashed/candied sweet potato"
      "base_food": {"item_name": "Mashed/candied sweet potato", "weight_g": 100}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Broccoli Salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Broccoli salads", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken (unspecified cut/method)", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Dirty Rice"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Dirty Rice", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mashed Sweet Potato"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mashed/candied sweet potato", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像15

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Cheese quiche with vegetable sides"
      "base_food": {"item_name": "Cheese quiche", "weight_g": 300}
      "ingredients": [
        {"item_name": "Tomatoes (cooked)", "weight_g": 80},
        {"item_name": "Broccoli (cooked)", "weight_g": 120}
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
      "dish_name": "Cheese quiche"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Cheese quiche", "weight_g": 220, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cooked broccoli"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Broccoli (cooked)", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Tomato mixture"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Tomatoes (cooked)", "weight_g": 90, "found_in_list": true}
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
      "dish_name": "Mac and cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 250}
    },
    {
      "dish_name": "Broccoli"
      "ingredients": [
        {"item_name": "Broccoli (cooked)", "weight_g": 50}
      ]
    },
    {
      "dish_name": "Tomato-based dish"
      "ingredients": [
        {"item_name": "Tomatoes (cooked)", "weight_g": 40},
        {"item_name": "Cooked meat", "weight_g": 30}
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
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 250, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Broccoli"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Tomato-based vegetable dish"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Tomato-based vegetable dish", "weight_g": 150, "found_in_list": false}
      ]
    }
  ]
}
```

---

## 📸 画像16

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mac and cheese with breaded cutlet and vegetables"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 180}
      "ingredients": [
        {"item_name": "Breaded cutlet", "weight_g": 150},
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Green cabbage", "weight_g": 60},
        {"item_name": "Broccoli (raw)", "weight_g": 40},
        {"item_name": "Carrots (raw)", "weight_g": 70}
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
      "dish_name": "Dinner platter"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Mac and cheese", "weight_g": 180, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Green cabbage", "weight_g": 80, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (raw)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (raw)", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Breaded cutlet", "weight_g": 150, "found_in_list": false}
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
      "dish_name": "Mac and cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 150}
    },
    {
      "dish_name": "Chicken"
      "base_food": {"item_name": "Chicken", "weight_g": 120}
    },
    {
      "dish_name": "Vegetable salad"
      "base_food": {"item_name": "Vegetable salad", "weight_g": 100}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Breaded chicken breast"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Breading", "weight_g": 30, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Broccoli"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Carrots"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Carrots (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cucumber and cabbage salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Cucumber (raw)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cabbage (raw)", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Corn (cooked)", "weight_g": 30, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像17

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mixed plate with vegetables and egg"
      "ingredients": [
        {"item_name": "Broccoli (cooked)", "weight_g": 100},
        {"item_name": "Tomatoes (raw)", "weight_g": 50},
        {"item_name": "Fried rice", "weight_g": 150},
        {"item_name": "Corn", "weight_g": 20},
        {"item_name": "Fried eggs", "weight_g": 60},
        {"item_name": "Roasted potatoes", "weight_g": 80},
        {"item_name": "Carrots (roasted)", "weight_g": 50},
        {"item_name": "Mushrooms", "weight_g": 30},
        {"item_name": "Hollandaise sauce", "weight_g": 20}
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
      "dish_name": "Divided plate meal with vegetables, rice, and egg"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Fried rice", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Baked potato", "weight_g": 80, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mushrooms", "weight_g": 50, "found_in_list": true},
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
      "dish_name": "Broccoli salad"
      "base_food": {"item_name": "Broccoli salads", "weight_g": 150}
      "ingredients": [
        {"item_name": "Tomato", "weight_g": 50},
        {"item_name": "Butter", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Beef and potatoes"
      "base_food": {"item_name": "Beef and potatoes", "weight_g": 200}
      "ingredients": [
        {"item_name": "Carrot", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Beef and rice"
      "base_food": {"item_name": "Beef and rice", "weight_g": 180}
      "ingredients": [
        {"item_name": "Corn", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Fried egg"
      "base_food": {"item_name": "Fried eggs", "weight_g": 90}
      "ingredients": [
        {"item_name": "Pepper", "weight_g": 1}
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
      "dish_name": "Vegetable salad with sauce"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Vegetable salad", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mayonnaise", "weight_g": 15, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Beef with potatoes & vegetables"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef with potatoes & vegetables", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Fried rice with corn and meat"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Fried rice", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Corn (Cooked)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Meat (unspecified)", "weight_g": 30, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Fried egg"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Fried eggs", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像18

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Roasted chicken with vegetables and pearl couscous"
      "ingredients": [
        {"item_name": "Carrots (cooked)", "weight_g": 100},
        {"item_name": "Broccoli (cooked)", "weight_g": 80},
        {"item_name": "Breaded chicken", "weight_g": 120},
        {"item_name": "Pearl couscous", "weight_g": 150}
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
      "dish_name": "Plated protein with vegetables and grain"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Breaded chicken breast", "weight_g": 120, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Couscous (Plain, Cooked)", "weight_g": 150, "found_in_list": true}
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
      "dish_name": "Roasted Carrots"
      "base_food": {"item_name": "Carrots (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 80}
    },
    {
      "dish_name": "Breaded Chicken"
      "base_food": {"item_name": "Chicken", "weight_g": 120}
      "ingredients": [
        {"item_name": "breaded coating", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Couscous"
      "base_food": {"item_name": "Couscous (Plain, Cooked)", "weight_g": 150}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Cooked Broccoli"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cooked Carrots"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Carrots (cooked)", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Breaded Chicken Breast"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Breaded coating", "weight_g": 30, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Couscous (Plain, Cooked)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Couscous (Plain, Cooked)", "weight_g": 130, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像19

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Meat with sauce, couscous and green beans"
      "ingredients": [
        {"item_name": "Meat (unspecified)", "weight_g": 150},
        {"item_name": "Couscous (Plain, Cooked)", "weight_g": 100},
        {"item_name": "Green beans", "weight_g": 80},
        {"item_name": "Hollandaise sauce", "weight_g": 30}
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
      "dish_name": "Stuffed beef rolls with couscous and green beans"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef rolls (stuffed)", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Couscous", "weight_g": 120, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Green beans", "weight_g": 90, "found_in_list": true}
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
      "dish_name": "Beef with Sauce and Couscous"
      "base_food": {"item_name": "Beef with sauce", "weight_g": 150}
      "ingredients": [
        {"item_name": "Couscous (Plain, Cooked)", "weight_g": 100},
        {"item_name": "Green beans", "weight_g": 50}
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
      "dish_name": "Beef with Sauce"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef with sauce", "weight_g": 150, "found_in_list": true}
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
      "dish_name": "Green Beans"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Green beans", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Raspberries"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Raspberries", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像20

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Beef stew with potatoes"
      "base_food": {"item_name": "Beef stew with potatoes (PR style)", "weight_g": 500}
    },
    {
      "dish_name": "Mixed greens salad with figs and prosciutto"
      "ingredients": [
        {"item_name": "Mixed salad greens", "weight_g": 150},
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Fig", "weight_g": 60},
        {"item_name": "prosciutto", "weight_g": 40}
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
      "dish_name": "Beef, potatoes & vegetables"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef, potatoes & vegetables", "weight_g": 400, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed greens salad with figs and prosciutto"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Fig", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Prosciutto", "weight_g": 30, "found_in_list": false}
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
      "base_food": {"item_name": "Beef stew with potatoes (PR style)", "weight_g": 400}
      "ingredients": [
        {"item_name": "Cream (Liquid)", "weight_g": 20},
        {"item_name": "herbs", "weight_g": 5}
      ]
    },
    {
      "dish_name": "Fig and prosciutto salad"
      "ingredients": [
        {"item_name": "Mixed salad greens", "weight_g": 150},
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Fig", "weight_g": 30},
        {"item_name": "prosciutto", "weight_g": 20}
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
      "dish_name": "Beef Stew with Potatoes and Sour Cream"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef stew with potatoes (PR style)", "weight_g": 500, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sour cream", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Fig and Prosciutto Salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Figs", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Prosciutto", "weight_g": 30, "found_in_list": false}
      ]
    }
  ]
}
```

---
