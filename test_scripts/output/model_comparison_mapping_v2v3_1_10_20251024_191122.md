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


# 📸 画像1-10のデータ

---

## 📸 画像1

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mixed greens salad"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 120}
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 50},
        {"item_name": "Carrots (raw)", "weight_g": 30},
        {"item_name": "Cucumber (Raw)", "weight_g": 40}
      ]
    },
    {
      "dish_name": "Beef with vegetables and mac and cheese"
      "ingredients": [
        {"item_name": "Beef steak", "weight_g": 150},
        {"item_name": "Zucchini", "weight_g": 80},
        {"item_name": "Yellow squash", "weight_g": 80},
        {"item_name": "Pasta", "weight_g": 100},
        {"item_name": "Cheese sauce", "weight_g": 50}
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
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 140, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (raw)", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Steak with vegetables"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Beef steak", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Yellow squash", "weight_g": 80, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Zucchini", "weight_g": 70, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 200, "found_in_list": true}
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
      "dish_name": "Lettuce Salad"
      "base_food": {"item_name": "Lettuce salad", "weight_g": 200}
      "ingredients": [
        {"item_name": "Tomato", "weight_g": 50},
        {"item_name": "Cucumber", "weight_g": 30},
        {"item_name": "Carrot", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Mac and Cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 150}
      "ingredients": [
        {"item_name": "Beef steak", "weight_g": 100},
        {"item_name": "Zucchini", "weight_g": 50}
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
        {"role": "BASE", "item_name": "Lettuce salad", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomato", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mac and Cheese with Steak and Zucchini"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Beef steak", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Zucchini", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像2

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mac and cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 150}
    },
    {
      "dish_name": "Broccoli"
      "ingredients": [
        {"item_name": "Broccoli (cooked)", "weight_g": 80}
      ]
    },
    {
      "dish_name": "Yellow squash"
      "ingredients": [
        {"item_name": "Yellow squash", "weight_g": 100}
      ]
    },
    {
      "dish_name": "Chicken breast"
      "ingredients": [
        {"item_name": "Chicken breast", "weight_g": 120}
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
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 200, "found_in_list": true}
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
      "dish_name": "Yellow squash"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Yellow squash (sliced, cooked)", "weight_g": 100, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Chicken breast"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Chicken breast", "weight_g": 150, "found_in_list": true}
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
      "base_food": {"item_name": "Mac and cheese", "weight_g": 200}
    },
    {
      "dish_name": "Broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 150}
    },
    {
      "dish_name": "Chicken breast"
      "base_food": {"item_name": "Chicken breast", "weight_g": 180}
    },
    {
      "dish_name": "Yellow squash"
      "ingredients": [
        {"item_name": "Yellow squash", "weight_g": 120}
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
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 150, "found_in_list": true}
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
      "dish_name": "Yellow squash"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Yellow squash (cooked)", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken breast"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 120, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像3

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Steak dinner with roasted sides"
      "base_food": {"item_name": "Beef steak with onions (PR style)", "weight_g": 180}
      "ingredients": [
        {"item_name": "Roasted potatoes", "weight_g": 120},
        {"item_name": "Asparagus (cooked)", "weight_g": 80},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 5},
        {"item_name": "Dip (Unspecified)", "weight_g": 20}
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
      "dish_name": "Steak with roasted potatoes and asparagus"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef, potatoes & vegetables", "weight_g": 340, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Onion relish topping", "weight_g": 35, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Creamy sauce", "weight_g": 25, "found_in_list": false}
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
      "dish_name": "Beef steak with onions"
      "base_food": {"item_name": "Beef steak with onions (PR style)", "weight_g": 200}
      "ingredients": [
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 10},
        {"item_name": "Sauce", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Roasted potatoes"
      "base_food": {"item_name": "Roasted potatoes", "weight_g": 150}
    },
    {
      "dish_name": "Asparagus (cooked)"
      "base_food": {"item_name": "Asparagus (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Sour cream"
      "ingredients": [
        {"item_name": "Sour cream", "weight_g": 20}
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
      "dish_name": "Roasted potatoes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Roasted potatoes", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Asparagus"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Asparagus", "weight_g": 120, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Beef with sauce"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef with sauce", "weight_g": 180, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 5, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mayonnaise"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Mayonnaise", "weight_g": 30, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像4

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mac and cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 180}
    },
    {
      "dish_name": "Mixed greens salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 40},
        {"item_name": "Tomatoes (raw)", "weight_g": 30},
        {"item_name": "Cucumber (Raw)", "weight_g": 25},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 15},
        {"item_name": "Carrots (raw)", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Sliced cooked meat"
      "ingredients": [
        {"item_name": "Meat (unspecified)", "weight_g": 160}
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
      "dish_name": "Garden salad with vegetables"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 70, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 25, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 15, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (raw)", "weight_g": 10, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Grilled meat slices"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Grilled meat", "weight_g": 150, "found_in_list": false}
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
      "dish_name": "Macaroni and cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 200}
    },
    {
      "dish_name": "Sliced chicken"
      "base_food": {"item_name": "Chicken (unspecified cut/method)", "weight_g": 150}
    },
    {
      "dish_name": "Vegetable salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 50},
        {"item_name": "Tomatoes (raw)", "weight_g": 30},
        {"item_name": "Cucumbers (raw)", "weight_g": 20},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 15},
        {"item_name": "Carrots (raw)", "weight_g": 10}
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
      "dish_name": "Vegetable salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Vegetable salad", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken breast"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 150, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像5

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Grilled chicken with asparagus and garlic bread"
      "ingredients": [
        {"item_name": "Chicken breast", "weight_g": 150},
        {"item_name": "Garlic bread", "weight_g": 60},
        {"item_name": "Asparagus (cooked)", "weight_g": 80},
        {"item_name": "cooking juices/sauce", "weight_g": 15}
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
      "dish_name": "Chicken with asparagus and garlic bread platter"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Chicken breast", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Asparagus (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Garlic bread", "weight_g": 80, "found_in_list": true}
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
      "dish_name": "Chicken with gravy"
      "base_food": {"item_name": "Chicken with gravy", "weight_g": 150}
      "ingredients": [
        {"item_name": "Herbs", "weight_g": 5}
      ]
    },
    {
      "dish_name": "Asparagus"
      "base_food": {"item_name": "Asparagus", "weight_g": 100}
    },
    {
      "dish_name": "Garlic bread"
      "base_food": {"item_name": "Garlic bread", "weight_g": 100}
      "ingredients": [
        {"item_name": "Herbs", "weight_g": 5}
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
      "dish_name": "Chicken with Vegetables"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken or turkey with vegetables", "weight_g": 250, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Garlic Bread"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Garlic bread", "weight_g": 120, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像6

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Creamy meatball and vegetable soup"
      "ingredients": [
        {"item_name": "Meatballs", "weight_g": 150},
        {"item_name": "Broccoli (cooked)", "weight_g": 100},
        {"item_name": "Carrots (cooked)", "weight_g": 50},
        {"item_name": "Boiled potatoes", "weight_g": 100},
        {"item_name": "creamy broth", "weight_g": 300}
      ]
    },
    {
      "dish_name": "Dinner rolls"
      "ingredients": [
        {"item_name": "Bread rolls & buns", "weight_g": 200}
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
      "dish_name": "Creamy meatball and vegetable soup"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Meatballs", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cooked potato (ingredient)", "weight_g": 75, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Creamy broth", "weight_g": 225, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Bread rolls"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Bread rolls", "weight_g": 150, "found_in_list": false}
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
      "dish_name": "Creamy Chicken Soup"
      "base_food": {"item_name": "Chicken soup family", "weight_g": 450}
      "ingredients": [
        {"item_name": "Broccoli", "weight_g": 50},
        {"item_name": "Carrots", "weight_g": 30},
        {"item_name": "Potatoes", "weight_g": 40}
      ]
    },
    {
      "dish_name": "Bread Rolls"
      "ingredients": [
        {"item_name": "Bread rolls", "weight_g": 100}
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
      "dish_name": "Chicken Soup with Vegetables"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Chicken soup family", "weight_g": 300, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Potatoes (cooked)", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Biscuits (plain/variants)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Biscuits (plain/variants)", "weight_g": 200, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像7

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Beef, potatoes & vegetables"
      "base_food": {"item_name": "Beef, potatoes & vegetables", "weight_g": 450}
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
        {"role": "BASE", "item_name": "Beef, potatoes & vegetables", "weight_g": 425, "found_in_list": true}
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
      "dish_name": "Beef steak"
      "base_food": {"item_name": "Beef steak", "weight_g": 150}
    },
    {
      "dish_name": "Broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Mashed potatoes"
      "base_food": {"item_name": "Mashed potatoes", "weight_g": 120}
    },
    {
      "dish_name": "Potato salad"
      "base_food": {"item_name": "Potato salad", "weight_g": 180}
      "ingredients": [
        {"item_name": "Bacon (cooked)", "weight_g": 20}
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
      "dish_name": "Beef steak"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef steak", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Broccoli (cooked)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mashed potatoes with ham"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mashed potatoes", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Ham", "weight_g": 20, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像8

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Breaded protein with vegetables and couscous"
      "ingredients": [
        {"item_name": "Broccoli (cooked)", "weight_g": 100},
        {"item_name": "Carrots (cooked)", "weight_g": 80},
        {"item_name": "Couscous (Plain, Cooked)", "weight_g": 120},
        {"item_name": "Breaded protein", "weight_g": 150},
        {"item_name": "Lemon", "weight_g": 20}
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
      "dish_name": "Baked fish with vegetables and couscous"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "White fish fillet", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 80, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Couscous (Plain, Cooked)", "weight_g": 120, "found_in_list": true},
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
      "dish_name": "Broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Roasted carrots"
      "base_food": {"item_name": "Carrots (cooked)", "weight_g": 120}
    },
    {
      "dish_name": "Couscous"
      "base_food": {"item_name": "Couscous (Plain, Cooked)", "weight_g": 130}
    },
    {
      "dish_name": "Baked dish"
      "ingredients": [
        {"item_name": "chicken", "weight_g": 150},
        {"item_name": "breadcrumb topping", "weight_g": 30},
        {"item_name": "lemon wedge", "weight_g": 15}
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
      "dish_name": "Broccoli"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Carrots"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Couscous"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Couscous (Plain, Cooked)", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Baked dish"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Baked dish", "weight_g": 150, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Lemon wedge"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lemon", "weight_g": 20, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像9

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Corn on the cob"
      "base_food": {"item_name": "Corn (Cooked)", "weight_g": 175}
    },
    {
      "dish_name": "Mixed greens salad with figs and prosciutto"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 100}
      "ingredients": [
        {"item_name": "Fig", "weight_g": 90},
        {"item_name": "prosciutto", "weight_g": 50}
      ]
    },
    {
      "dish_name": "Barbecue ribs"
      "base_food": {"item_name": "Ribs", "weight_g": 200}
      "ingredients": [
        {"item_name": "Barbecue sauce", "weight_g": 30}
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
      "dish_name": "Corn on the cob"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Corn (Cooked)", "weight_g": 180, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Glazed ribs"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Ribs", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed greens salad with figs and prosciutto"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Fig", "weight_g": 40, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cured meat (prosciutto)", "weight_g": 20, "found_in_list": false}
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
      "dish_name": "Corn on the cob"
      "base_food": {"item_name": "Corn (Cooked)", "weight_g": 150}
    },
    {
      "dish_name": "Salad with figs and prosciutto"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 100},
        {"item_name": "Fig", "weight_g": 50},
        {"item_name": "Prosciutto", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Barbecued ribs"
      "base_food": {"item_name": "Ribs", "weight_g": 200}
      "ingredients": [
        {"item_name": "Barbecue sauce", "weight_g": 50}
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
      "dish_name": "Corn on the cob"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Corn (Cooked)", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Fig and prosciutto salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Fig", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Prosciutto", "weight_g": 50, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Barbecued ribs"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Barbecue meat", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Barbecue sauce", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像10

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mac and cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 150}
    },
    {
      "dish_name": "Cooked broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Mixed green salad"
      "ingredients": [
        {"item_name": "Mixed salad greens", "weight_g": 60},
        {"item_name": "Cucumber (Raw)", "weight_g": 40},
        {"item_name": "Carrots (raw)", "weight_g": 30},
        {"item_name": "Red bell pepper", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Cooked beef"
      "base_food": {"item_name": "Beef (NFS)", "weight_g": 200}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cooked broccoli"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed greens salad"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 80, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Tomatoes (raw)", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Beef steak"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Beef steak", "weight_g": 180, "found_in_list": true}
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
        {"item_name": "Broccoli (cooked)", "weight_g": 100}
      ]
    },
    {
      "dish_name": "Beef steak"
      "base_food": {"item_name": "Beef steak", "weight_g": 200}
      "ingredients": [
        {"item_name": "Beef steak sauce", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Vegetable salad"
      "ingredients": [
        {"item_name": "Cucumber (raw)", "weight_g": 50},
        {"item_name": "Tomato (raw)", "weight_g": 50},
        {"item_name": "Avocado", "weight_g": 30},
        {"item_name": "Lettuce", "weight_g": 40},
        {"item_name": "Carrot (raw)", "weight_g": 20},
        {"item_name": "Onion (raw)", "weight_g": 15}
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
      "dish_name": "Macaroni with cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Beef steak with sauce"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef steak", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sauce", "weight_g": 20, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mixed vegetables", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---
