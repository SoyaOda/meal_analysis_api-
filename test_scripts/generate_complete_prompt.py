#!/usr/bin/env python
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
    # f-stringでの{}エスケープを避けるため、formatを使用
    prompt_template = """You are an expert food analyst and nutritionist for a US-based diet app.
Analyze ONE meal image and return ONE JSON object ONLY (no extra text).

PRIMARY GOALS
- Detect each visually separate food item as one "dish".
- For each dish, choose exactly ONE analysis_method from {USE_AS_IS, HYBRID_DECOMPOSITION, DECOMPOSE_TO_INGREDIENTS}.
- For every base_food and ingredient, check if the item exists in EXACT_FOOD_LIST (CORE).

ANALYSIS METHOD RULES (STRICT):
1) USE_AS_IS: 
   - base_food: ONE item (required)
   - ingredients: MUST be empty array []
   - Use when: The entire dish matches a single item in the list

2) DECOMPOSE_TO_INGREDIENTS: 
   - base_food: MUST be null
   - ingredients: ALL components listed (at least one required)
   - Use when: Breaking down into individual ingredients (e.g., salads, custom dishes)

3) HYBRID_DECOMPOSITION:
   - base_food: ONE base item (required)
   - ingredients: ONLY additional/extra items not implied by base (at least one required)
   - Use when: Standard dish with visible additions/toppings

FOOD ITEM STRUCTURE:
Each food item (base_food or ingredient) MUST follow this structure:
{
  "item_name": "[EXACT from CORE or null if not in list]",
  "weight_g": <integer>,
  "found_in_list": <boolean>,
  "nutrition_per_100g": null | {
    "calorie": <number>,
    "protein_g": <number>,
    "fat_g": <number>,
    "carbs_g": <number>
  }
}

IMPORTANT RULES:
- If found_in_list is true: nutrition_per_100g MUST be null
- If found_in_list is false: 
  - item_name MUST be a descriptive name (not from list)
  - nutrition_per_100g MUST be provided with estimated values
  - Nutrition sanity check: calorie ≈ 4*protein + 9*fat + 4*carbs (±20%)

METHOD SELECTION GUIDE:
1) SALADS with visible ingredients → DECOMPOSE_TO_INGREDIENTS
2) STANDARD DISHES in list → USE_AS_IS
3) STANDARD DISHES with extra toppings → HYBRID_DECOMPOSITION
4) CUSTOM/HOMEMADE dishes not in list → DECOMPOSE_TO_INGREDIENTS

IMPLICIT CONTENTS (don't list as separate ingredients in HYBRID):
- Pizza: dough, sauce, base cheese are implicit
- Pasta dishes: base pasta and standard sauce are implicit
- Sandwiches/Wraps: bread/tortilla is implicit
- Burgers: bun and standard toppings are implicit

OUTPUT JSON STRUCTURE:
{
  "dishes": [
    {
      "dish_name": "short descriptive name",
      "unit_count": 1,
      "confidence": 0.0-1.0,
      "analysis_method": "USE_AS_IS | HYBRID_DECOMPOSITION | DECOMPOSE_TO_INGREDIENTS",
      "base_food": null | {
        "item_name": "string",
        "weight_g": <int>,
        "found_in_list": <boolean>,
        "nutrition_per_100g": null | {
          "calorie": <number>,
          "protein_g": <number>,
          "fat_g": <number>,
          "carbs_g": <number>
        }
      },
      "ingredients": [
        {
          "item_name": "string",
          "weight_g": <int>,
          "found_in_list": <boolean>,
          "nutrition_per_100g": null | {
            "calorie": <number>,
            "protein_g": <number>,
            "fat_g": <number>,
            "carbs_g": <number>
          }
        }
      ]
    }
  ]
}

CONFIDENCE GUIDELINES:
- 0.85-1.00: Clear view, exact matches in list
- 0.60-0.84: Some uncertainty, using similar items from list
- 0.40-0.59: Items not in list, nutrition estimates required

VALIDATION CHECKLIST (must pass before returning):
1. USE_AS_IS: base_food exists, ingredients = []
2. DECOMPOSE_TO_INGREDIENTS: base_food = null, ingredients.length > 0
3. HYBRID_DECOMPOSITION: base_food exists, ingredients.length > 0
4. Each item with found_in_list=true has nutrition_per_100g=null
5. Each item with found_in_list=false has valid nutrition_per_100g
6. Weight values are reasonable integers (>0)
7. Return ONLY the JSON object, no extra text

EXACT_FOOD_LIST (CORE)
<<FOOD_NAMES_LIST>>
"""
    return prompt_template.replace("<<FOOD_NAMES_LIST>>", food_names_list)


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
