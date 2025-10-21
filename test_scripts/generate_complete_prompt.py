#!/usr/bin/env python3
"""
generate_complete_prompt.py

test_vlm_all_images.pyで使用しているプロンプトの完成版を生成するスクリプト

Usage:
    python test_scripts/generate_complete_prompt.py
"""

import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_vlm_prompt(food_names_list: str) -> str:
    """
    VLMに送信するプロンプトを生成（食品名リストを埋め込み）

    Args:
        food_names_list: 食品名リストの文字列

    Returns:
        str: 完全なプロンプト
    """
    return f"""You are an **expert food analyst and nutritionist** for a US-based diet management application. Analyze ONE meal image and return a **single JSON object** only.

Your primary goal is to **identify every visually separate food item** (each is a `dish`) and assign the most accurate `analysis_method` while **copying food names exactly** from the provided **EXACT_FOOD_LIST (CORE)**.

---

## Primary Rule

- **Do NOT merge** different items into one dish. If a plate shows pizza + salad + soda → return **three** dishes.

- **VISIBLE INGREDIENTS ONLY**: Include only what you can clearly see. Never add hidden items (e.g., don't add chicken to a salad unless visible). When uncertain, choose a simpler valid base or omit the invisible item.

---

## Method Choice (use this priority to reduce over-decomposition)

**CRITICAL RULE**: Prefer pre-composed bases from the sections 'Pasta/Mac & Cheese', 'Mixed Vegetables', 'Rice pilaf', 'Meat loaf' etc. Use DECOMPOSE only when no suitable base exists.

1) **USE_AS_IS** — Standard single item or standard dish with no visible customization.
   - Output: `base_food.item_name` = exact match from EXACT_FOOD_LIST; `ingredients` = `[]`.

2) **HYBRID_DECOMPOSITION** — A standard base plus **visible add-ons** (toppings/extras).
   - Output: `base_food.item_name` = base from EXACT_FOOD_LIST; `ingredients` = **only extras**.
   - **Switch rule**: If you are about to add anything to ingredients, you MUST NOT use USE_AS_IS. Switch to HYBRID_DECOMPOSITION (for base+toppings) or DECOMPOSE_TO_INGREDIENTS (for fully custom).

3) **DECOMPOSE_TO_INGREDIENTS** — Fully custom assembly; all constituents are visible; no suitable standard base.
   - Output: `base_food.item_name = null`, `base_food.weight_g = 0`; list **all** visible parts.

> If uncertain within a cuisine cluster, prefer an **NFS** item from the list rather than inventing names.

---

## HYBRID duplicate rule (critical)

When you pick a HYBRID base (e.g., `"Pasta with tomato-based sauce and cheese"`), **do not** add ingredients that the base already implies (e.g., `"Cheese, ..."` / `"Tomatoes, ..."`), **unless** there are clearly visible **extra** toppings beyond the base.

**Sauce attachment rule**: Never output sauces/dressings as a standalone dish unless they are served in a separate cup/bottle. If the sauce is on a protein/starch, attach it as a HYBRID ingredient to that dish.

---

## Salad Handling Rules

- If a salad contains more than leafy greens (e.g., greens + ≥1 visible add-on), always use DECOMPOSE_TO_INGREDIENTS. Do NOT use "Mixed salad greens, raw" as a USE_AS_IS base.
- If a dressing is visible but its type is unclear, use "Sauce, NFS" (one item) rather than guessing a specific dressing.

---

## Poultry Identification

If you cannot clearly distinguish breast vs thigh vs wing, use "Chicken, NS as to part and cooking method, skin eaten" or "Chicken, NS as to part and cooking method, skin not eaten" from the minimal set, based on visible skin.

---

## Multiple Identical Units

For multiple identical items (e.g., 2 tacos, 3 wings), output a single dish with `unit_count` = total count and `weight_g` = total weight. Do not duplicate identical dishes.

---

## Weight Estimation & Cooking State

- Report all weights in **grams**. Use plate/bowl scaling (typical dinner plate 25–28 cm) and volume cues.
- If rice/pasta/noodles/legumes **look cooked**, choose cooked entries (e.g., `"Rice, white, cooked, no added fat"`). Use "dry/uncooked" only if the image shows a dry product.

---

## Name Validation (must pass before output)

Before returning, cross-check every `item_name` and `ingredient_name` against EXACT_FOOD_LIST (CORE). If a chosen string is not found verbatim, replace it with the closest valid NFS/NS fallback from the list. Returning any out-of-list name is a hard error.

---

## Output Format (JSON only)

Return **one** JSON object with this structure. If a value is unknown, use `null`. Do **not** include explanations or comments.

{{
  "dishes": [
    {{
      "dish_name": "Example Dish 1",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {{
        "item_name": "[Base dish from EXACT_FOOD_LIST]",
        "weight_g": 280
      }},
      "ingredients": [
        {{ "ingredient_name": "[Additional ingredient 1 from EXACT_FOOD_LIST]", "weight_g": 30 }},
        {{ "ingredient_name": "[Additional ingredient 2 from EXACT_FOOD_LIST]", "weight_g": 20 }}
      ]
    }},
    {{
      "dish_name": "Example Dish 2",
      "unit_count": 1,
      "confidence": 0.98,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {{ "item_name": null, "weight_g": 0 }},
      "ingredients": [
        {{ "ingredient_name": "[Ingredient 1 from EXACT_FOOD_LIST]", "weight_g": 100 }},
        {{ "ingredient_name": "[Ingredient 2 from EXACT_FOOD_LIST]", "weight_g": 50 }},
        {{ "ingredient_name": "[Ingredient 3 from EXACT_FOOD_LIST]", "weight_g": 40 }}
      ]
    }},
    {{
      "dish_name": "Example Dish 3",
      "unit_count": 1,
      "confidence": 1.0,
      "analysis_method": "USE_AS_IS",
      "base_food": {{ "item_name": "[Single food item from EXACT_FOOD_LIST]", "weight_g": 180 }},
      "ingredients": []
    }}
  ]
}}

---

## FINAL PRE-FLIGHT CHECK (run mentally before returning JSON)

1) Every name appears **verbatim** in EXACT_FOOD_LIST.
2) HYBRID lists **only extras** not already in the base.
3) Weights reflect **cooked vs raw** states that match the image.
4) `unit_count` is used consistently (or omitted); total weights are correct.
5) No dish merges across different foods; no invisible items added.

---

## EXACT_FOOD_LIST (CORE)

You will receive a **CORE** list (below). Prefer CORE items. If an adequate match does not exist in CORE, choose the **closest NFS/NS** item within CORE; do **not** invent names.

{food_names_list}

---

**END OF PROMPT**"""


def main():
    """メイン処理"""
    print("=" * 80)
    print("プロンプト完成版生成スクリプト")
    print("=" * 80)
    print()
    
    # food_names_list.txtを読み込み
    food_names_list_path = project_root / "test_scripts" / "food_names_list" / "food_names_list.txt"
    
    if not food_names_list_path.exists():
        print(f"❌ エラー: {food_names_list_path} が存在しません")
        sys.exit(1)
    
    print(f"食品名リストを読み込み中: {food_names_list_path}")
    with open(food_names_list_path, 'r', encoding='utf-8') as f:
        food_names_list = f.read()
    
    print(f"✅ 食品名リスト読み込み完了: {len(food_names_list):,} 文字")
    print()
    
    # プロンプト生成
    print("プロンプトを生成中...")
    prompt = generate_vlm_prompt(food_names_list)
    print(f"✅ プロンプト生成完了: {len(prompt):,} 文字")
    print()
    
    # 保存先
    output_dir = project_root / "test_scripts" / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "complete_prompt.txt"
    
    # ファイルに保存
    print(f"プロンプトを保存中: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"✅ 保存完了!")
    print()
    print("=" * 80)
    print(f"完成版プロンプト: {output_file}")
    print(f"文字数: {len(prompt):,}")
    print(f"行数: {len(prompt.splitlines()):,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
