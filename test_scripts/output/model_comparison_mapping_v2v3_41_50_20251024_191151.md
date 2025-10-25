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


# 📸 画像41-50のデータ

---

## 📸 画像41

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Pasta salad"
      "base_food": {"item_name": "Pasta salad", "weight_g": 150}
      "ingredients": [
        {"item_name": "Carrots (cooked)", "weight_g": 20},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 15},
        {"item_name": "Cucumber (Raw)", "weight_g": 10}
      ]
    },
    {
      "dish_name": "Cooked broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Chicken thigh"
      "base_food": {"item_name": "Chicken thigh", "weight_g": 120}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Pasta salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Pasta salad", "weight_g": 180, "found_in_list": true}
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
      "dish_name": "Cooked chicken"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken (unspecified cut/method)", "weight_g": 150, "found_in_list": true}
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
      "dish_name": "Macaroni salad"
      "base_food": {"item_name": "Pasta salad", "weight_g": 200}
      "ingredients": [
        {"item_name": "Carrots (cooked)", "weight_g": 50},
        {"item_name": "Cucumbers (cooked)", "weight_g": 30},
        {"item_name": "Ham", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Broccoli"
      "base_food": {"item_name": "Broccoli (cooked)", "weight_g": 150}
    },
    {
      "dish_name": "Grilled chicken"
      "base_food": {"item_name": "Chicken (unspecified cut/method)", "weight_g": 250}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Pasta salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Pasta salad", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Broccoli"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Broccoli (cooked)", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Chicken thigh"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken thigh", "weight_g": 200, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像42

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Green bean casserole"
      "base_food": {"item_name": "Green bean casserole", "weight_g": 150}
      "ingredients": [
        {"item_name": "Onions", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Mashed potatoes with gravy"
      "base_food": {"item_name": "Mashed potatoes", "weight_g": 150}
      "ingredients": [
        {"item_name": "Gravy", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Sliced turkey with gravy"
      "base_food": {"item_name": "Turkey (various cuts)", "weight_g": 120}
      "ingredients": [
        {"item_name": "Gravy", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Cooked carrots"
      "base_food": {"item_name": "Carrots (cooked)", "weight_g": 80}
    },
    {
      "dish_name": "Cornbread muffin"
      "base_food": {"item_name": "Cornbread Muffin", "weight_g": 70}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Mashed potatoes with gravy"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mashed potatoes", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Gravy", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Green bean casserole"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Green bean casserole", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Turkey with gravy"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Turkey with gravy meal", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cooked carrots"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Carrots (cooked)", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cornbread"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Cornbread (Loaf/Pan)", "weight_g": 80, "found_in_list": true}
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
      "dish_name": "Mashed potatoes with gravy"
      "base_food": {"item_name": "Mashed potatoes", "weight_g": 200}
      "ingredients": [
        {"item_name": "Gravy", "weight_g": 30}
      ]
    },
    {
      "dish_name": "Turkey with gravy"
      "base_food": {"item_name": "Turkey with gravy meal", "weight_g": 250}
    },
    {
      "dish_name": "Green bean casserole"
      "base_food": {"item_name": "Green bean casserole", "weight_g": 180}
    },
    {
      "dish_name": "Carrots (cooked)"
      "base_food": {"item_name": "Carrots (cooked)", "weight_g": 120}
    },
    {
      "dish_name": "Cornbread"
      "base_food": {"item_name": "Cornbread (Loaf/Pan)", "weight_g": 100}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Turkey meal with sides"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Turkey with gravy meal", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Mashed potatoes", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Green bean casserole", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cornbread (Loaf/Pan)", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像43

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Mac and cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 200}
    },
    {
      "dish_name": "Grilled zucchini"
      "ingredients": [
        {"item_name": "Zucchini", "weight_g": 100}
      ]
    },
    {
      "dish_name": "Grilled chicken breast"
      "base_food": {"item_name": "Chicken breast", "weight_g": 150}
    },
    {
      "dish_name": "Mixed greens salad with carrots"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 50}
      "ingredients": [
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
      "dish_name": "Mac and cheese"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed greens salad with carrots"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mixed salad greens", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (raw)", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Grilled chicken breast"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 140, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cooked zucchini"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Cooked zucchini", "weight_g": 80, "found_in_list": false}
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
      "base_food": {"item_name": "Chicken (unspecified cut/method)", "weight_g": 120}
    },
    {
      "dish_name": "Zucchini"
      "base_food": {"item_name": "Zucchini (cooked)", "weight_g": 100}
    },
    {
      "dish_name": "Carrots"
      "base_food": {"item_name": "Carrots (cooked)", "weight_g": 50}
    },
    {
      "dish_name": "Mixed salad greens"
      "base_food": {"item_name": "Mixed salad greens", "weight_g": 80}
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
      "dish_name": "Chicken breast"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Chicken breast", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Lettuce salad with carrots"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Lettuce salad", "weight_g": 120, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (raw)", "weight_g": 30, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Zucchini slices"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Zucchini slices", "weight_g": 100, "found_in_list": false}
      ]
    }
  ]
}
```

---

## 📸 画像44

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Baked pasta casserole"
      "base_food": {"item_name": "Pasta with Cream Sauce", "weight_g": 300}
    },
    {
      "dish_name": "Mixed vegetable salad"
      "ingredients": [
        {"item_name": "Cucumber (Raw)", "weight_g": 50},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 40},
        {"item_name": "Corn (Cooked)", "weight_g": 30},
        {"item_name": "Broccoli (raw)", "weight_g": 40},
        {"item_name": "Shredded cabbage", "weight_g": 80}
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
      "dish_name": "Baked pasta casserole"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pasta with Cream Sauce", "weight_g": 350, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (cooked)", "weight_g": 50, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Mixed vegetable salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Green cabbage", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cucumber (Raw)", "weight_g": 50, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Corn (Cooked)", "weight_g": 15, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (raw)", "weight_g": 5, "found_in_list": true}
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
      "dish_name": "Baked Mac and Cheese"
      "base_food": {"item_name": "Mac and cheese", "weight_g": 350}
      "ingredients": [
        {"item_name": "Broccoli", "weight_g": 50}
      ]
    },
    {
      "dish_name": "Vegetable Salad"
      "ingredients": [
        {"item_name": "Cucumber (Raw)", "weight_g": 100},
        {"item_name": "Onions", "weight_g": 50},
        {"item_name": "Green cabbage", "weight_g": 80},
        {"item_name": "Corn (Raw)", "weight_g": 30},
        {"item_name": "Broccoli (Raw)", "weight_g": 40}
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
      "dish_name": "Mixed vegetable salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Cucumber (raw)", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Onions", "weight_g": 20, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Corn (Raw)", "weight_g": 15, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (raw)", "weight_g": 25, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Shredded cabbage", "weight_g": 60, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Mac and cheese with broccoli"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Mac and cheese", "weight_g": 250, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Broccoli (raw)", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像45

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Sandwich with ham and arugula"
      "base_food": {"item_name": "Sandwich", "weight_g": 250}
      "ingredients": [
        {"item_name": "Ham", "weight_g": 50},
        {"item_name": "Arugula", "weight_g": 20}
      ]
    },
    {
      "dish_name": "Potato chips"
      "base_food": {"item_name": "Potato Chips", "weight_g": 100}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Italian sandwich"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Italian sandwich", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Arugula", "weight_g": 30, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Potato chips"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Potato Chips", "weight_g": 40, "found_in_list": true}
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
      "dish_name": "Ham sandwich with greens and cheese"
      "base_food": {"item_name": "Ham sandwich", "weight_g": 300}
      "ingredients": [
        {"item_name": "Arugula", "weight_g": 20},
        {"item_name": "American cheese", "weight_g": 20}
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
      "dish_name": "Ham Sandwich with Arugula"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Ham sandwich", "weight_g": 180, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Arugula", "weight_g": 20, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Potato Chips"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Potato Chips", "weight_g": 30, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像46

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Salisbury steak dinner"
      "base_food": {"item_name": "Salisbury steak", "weight_g": 150}
      "ingredients": [
        {"item_name": "Green beans", "weight_g": 100},
        {"item_name": "Carrots (cooked)", "weight_g": 80},
        {"item_name": "Baked potato", "weight_g": 150},
        {"item_name": "Sour cream", "weight_g": 30},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 10}
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
      "dish_name": "American dinner platter"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Salisbury steak", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Baked potato", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sour cream", "weight_g": 30, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 10, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Green beans", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Carrots (cooked)", "weight_g": 80, "found_in_list": true}
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
      "dish_name": "Beef with Gravy"
      "base_food": {"item_name": "Beef with sauce", "weight_g": 250}
    },
    {
      "dish_name": "Baked Potato with Toppings"
      "base_food": {"item_name": "Baked potato", "weight_g": 180}
      "ingredients": [
        {"item_name": "Sour cream", "weight_g": 30},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Green Beans"
      "base_food": {"item_name": "Green beans", "weight_g": 120}
    },
    {
      "dish_name": "Carrots (Cooked)"
      "base_food": {"item_name": "Carrots (cooked)", "weight_g": 100}
    }
  ]
}
```

### 30B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Beef with sauce"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef with sauce", "weight_g": 150, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Baked potato with toppings"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Baked potato", "weight_g": 100, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sour cream", "weight_g": 20, "found_in_list": false},
        {"role": "EXTRA", "item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 5, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Green beans"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Green beans", "weight_g": 100, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Carrots (cooked)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Carrots (cooked)", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像47

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Cheeseburger"
      "base_food": {"item_name": "Cheeseburger", "weight_g": 250}
      "ingredients": [
        {"item_name": "Tomatoes (raw)", "weight_g": 30},
        {"item_name": "Onions", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Roasted potato wedges"
      "base_food": {"item_name": "Roasted potatoes", "weight_g": 150}
    }
  ]
}
```

### 235B-Thinking-v3
```json
{
  "dishes": [
    {
      "dish_name": "Cheeseburger"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Cheeseburger", "weight_g": 220, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Roasted potatoes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Roasted potatoes", "weight_g": 180, "found_in_list": true}
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
      "dish_name": "Cheeseburger"
      "base_food": {"item_name": "Cheeseburger", "weight_g": 250}
      "ingredients": [
        {"item_name": "Tomato", "weight_g": 20},
        {"item_name": "Onion", "weight_g": 15}
      ]
    },
    {
      "dish_name": "Potato wedges"
      "ingredients": [
        {"item_name": "Potato", "weight_g": 150}
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
      "dish_name": "Cheeseburger"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Cheeseburger", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Roasted potatoes"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Roasted potatoes", "weight_g": 150, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像48

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Beef with rice and vegetables"
      "base_food": {"item_name": "Beef, rice & vegetables", "weight_g": 400}
      "ingredients": [
        {"item_name": "Dried herbs", "weight_g": 5}
      ]
    },
    {
      "dish_name": "Cucumber salad"
      "ingredients": [
        {"item_name": "Cucumber (raw)", "weight_g": 100},
        {"item_name": "Coleslaw Dressing", "weight_g": 30},
        {"item_name": "Alliums (onion/leek/shallot/scallion)", "weight_g": 20}
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
      "dish_name": "Beef, rice & vegetables plate"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Beef, rice & vegetables", "weight_g": 450, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Cucumber salad"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Cucumber Salad (Vinegar/Italian/Sour Cream/Namasu)", "weight_g": 150, "found_in_list": true}
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
      "dish_name": "Beef with Rice"
      "base_food": {"item_name": "Beef with rice", "weight_g": 450}
      "ingredients": [
        {"item_name": "Onions", "weight_g": 50},
        {"item_name": "Herbs", "weight_g": 5}
      ]
    },
    {
      "dish_name": "Coleslaw"
      "ingredients": [
        {"item_name": "Coleslaw Dressing", "weight_g": 100},
        {"item_name": "Cabbage", "weight_g": 70},
        {"item_name": "Carrots", "weight_g": 30}
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
      "dish_name": "Beef Rice with Herbs"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Beef, rice & vegetables", "weight_g": 280, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Herbs", "weight_g": 5, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Coleslaw"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Coleslaw", "weight_g": 100, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像49

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Personal pizza with meat and vegetables"
      "base_food": {"item_name": "Pizza (Meat & Vegetables)", "weight_g": 250}
      "ingredients": [
        {"item_name": "Olives", "weight_g": 25},
        {"item_name": "Basil", "weight_g": 10}
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
      "dish_name": "Vegetable pizza"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Pizza (Vegetable)", "weight_g": 220, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Olives", "weight_g": 25, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Basil", "weight_g": 8, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Water"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Water", "weight_g": 250, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Raspberry sparkling water"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Raspberry sparkling water", "weight_g": 500, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Hot pepper sauce"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Hot pepper sauce", "weight_g": 180, "found_in_list": true}
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
      "dish_name": "Vegetable Pizza"
      "base_food": {"item_name": "Pizza (Vegetable)", "weight_g": 250}
      "ingredients": [
        {"item_name": "Olives", "weight_g": 10},
        {"item_name": "Spinach", "weight_g": 10}
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
      "dish_name": "Pizza (Vegetable)"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Pizza (Vegetable)", "weight_g": 200, "found_in_list": true}
      ]
    }
  ]
}
```

---

## 📸 画像50

### 235B-Thinking-v2
```json
{
  "dishes": [
    {
      "dish_name": "Club sandwich"
      "base_food": {"item_name": "Club sandwich", "weight_g": 200}
    },
    {
      "dish_name": "Creamy vegetable soup"
      "base_food": {"item_name": "Vegetable soup family", "weight_g": 250}
      "ingredients": [
        {"item_name": "Chives", "weight_g": 2}
      ]
    },
    {
      "dish_name": "Avocado salad"
      "ingredients": [
        {"item_name": "Avocado", "weight_g": 80},
        {"item_name": "Lettuce", "weight_g": 50},
        {"item_name": "Sesame seeds", "weight_g": 5}
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
      "dish_name": "BLT sandwich"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "BLT sandwich", "weight_g": 220, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Tomato soup"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Tomato soup family", "weight_g": 280, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Avocado salad"
      "analysis_method": "FULL_DECOMPOSE"
      "items": [
        {"role": "EXTRA", "item_name": "Lettuce", "weight_g": 80, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 60, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Sesame seeds", "weight_g": 10, "found_in_list": true}
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
      "dish_name": "BLT sandwich"
      "base_food": {"item_name": "BLT sandwich", "weight_g": 200}
    },
    {
      "dish_name": "Tomato soup family"
      "base_food": {"item_name": "Tomato soup family", "weight_g": 250}
      "ingredients": [
        {"item_name": "Dill", "weight_g": 2}
      ]
    },
    {
      "dish_name": "Avocado lettuce salad"
      "ingredients": [
        {"item_name": "Lettuce", "weight_g": 30},
        {"item_name": "Avocado", "weight_g": 50}
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
      "dish_name": "BLT Sandwich with Cheese"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "BLT sandwich", "weight_g": 200, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Cheese", "weight_g": 20, "found_in_list": false}
      ]
    },
    {
      "dish_name": "Tomato Soup"
      "analysis_method": "SINGLE_BASE"
      "items": [
        {"role": "BASE", "item_name": "Tomato soup family", "weight_g": 200, "found_in_list": true}
      ]
    },
    {
      "dish_name": "Lettuce Salad with Avocado"
      "analysis_method": "BASE_PLUS_EXTRAS"
      "items": [
        {"role": "BASE", "item_name": "Lettuce salad", "weight_g": 150, "found_in_list": true},
        {"role": "EXTRA", "item_name": "Avocado", "weight_g": 50, "found_in_list": true}
      ]
    }
  ]
}
```

---
