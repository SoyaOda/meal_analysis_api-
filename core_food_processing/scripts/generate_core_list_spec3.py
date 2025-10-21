#!/usr/bin/env python3
"""
generate_core_list_spec3.py

spec3.md準拠のCORE食品リストを生成

出力形式:
## EXACT_FOOD_LIST (CORE) - spec3.md準拠

# BASE FOODS (DISHES) - 350-500項目

## [Category Name]
* food item name 1
* food item name 2

# INGREDIENTS - 600-900項目

## [Category Name]
* ingredient name 1
* ingredient name 2

Usage:
    python core_food_processing/scripts/generate_core_list_spec3.py
"""

import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent


def categorize_dish(label: str) -> str:
    """料理をカテゴリ分類（視覚アンカー重視）"""
    label_lower = label.lower()

    categories = {
        "Pizza & Pasta": ["pizza", "pasta", "spaghetti", "lasagna", "ravioli", "gnocchi", "noodle"],
        "Sandwiches & Burgers": ["sandwich", "burger", "panini", "sub"],
        "Breakfast": ["pancake", "waffle", "omelet"],
        "Rice & Asian": ["rice", "curry", "ramen", "dumpling", "sushi"],
        "Mexican": ["taco", "burrito", "quesadilla", "enchilada", "nachos"],
        "Soups & Stews": ["soup", "stew", "chowder", "bisque"],
        "Salads": ["salad"],
        "Snacks": ["popcorn", "chips", "crackers", "pretzels"],
        "Desserts": ["cake", "cookie", "brownie", "pudding", "ice cream", "pie", "tart"],
        "Dairy Products": ["yogurt", "cheese product"],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in label_lower:
                return category

    return "Other Dishes"


def categorize_ingredient(label: str) -> str:
    """食材をカテゴリ分類"""
    label_lower = label.lower()

    categories = {
        "Meat & Poultry": ["beef", "pork", "chicken", "turkey", "lamb", "duck", "meat", "poultry", "ham", "sausage"],
        "Seafood": ["fish", "salmon", "tuna", "shrimp", "crab", "lobster", "shellfish", "oyster", "clam", "mussel"],
        "Dairy & Eggs": ["milk", "cheese", "cream", "butter", "yogurt", "egg", "whey"],
        "Vegetables": ["lettuce", "tomato", "onion", "garlic", "pepper", "carrot", "potato", "vegetable"],
        "Fruits": ["apple", "banana", "orange", "fruit", "berry"],
        "Grains": ["rice", "wheat", "flour", "bread", "grain"],
        "Condiments": ["sauce", "dressing", "ketchup", "mayo", "mustard", "honey"],
        "Other": [],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in label_lower:
                return category

    return "Other Ingredients"


def main():
    """メイン処理"""
    print("="*80)
    print("CORE食品リスト生成スクリプト（spec3.md準拠）")
    print("="*80)
    print()

    # 入力ファイル
    dishes_json = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_core_spec3.json"
    ingredients_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_core_spec3.json"

    # データを読み込み
    print("📖 CORE候補を読み込み中...")
    with open(dishes_json, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    with open(ingredients_json, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  料理CORE: {len(dishes):,} 項目")
    print(f"  食材CORE: {len(ingredients):,} 項目")
    print()

    # カテゴリごとに分類
    print("📂 カテゴリごとに分類中...")
    dish_categories = defaultdict(list)
    for dish in dishes:
        category = categorize_dish(dish['label'])
        dish_categories[category].append(dish['label'])

    ingredient_categories = defaultdict(list)
    for ingredient in ingredients:
        category = categorize_ingredient(ingredient['label'])
        ingredient_categories[category].append(ingredient['label'])

    # カテゴリごとにソート
    for category in dish_categories:
        dish_categories[category].sort()
    for category in ingredient_categories:
        ingredient_categories[category].sort()

    print(f"  料理カテゴリ数: {len(dish_categories)}")
    print(f"  食材カテゴリ数: {len(ingredient_categories)}")
    print()

    # spec3.md形式で出力
    output_file = PROJECT_ROOT / "core_food_processing" / "output" / "foodon_core_list_spec3.txt"

    print(f"💾 spec3.md形式で保存中: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        # ヘッダー
        f.write("## EXACT_FOOD_LIST (CORE) - spec3.md準拠\n\n")
        f.write("Generated from FoodOn + Open Food Facts\n")
        f.write("仕様: core_food_processing/spec/spec3.md\n\n")
        f.write("特徴:\n")
        f.write("- ファセット語（加工・包装・品質属性）を除去\n")
        f.write("- 視覚アンカー重視（画像で区別できる名称のみ）\n")
        f.write("- 同義語を代表語に縮約\n")
        f.write("- OFF頻度でスコアリング\n\n")
        f.write(f"Total Base Foods (Dishes): {len(dishes):,}\n")
        f.write(f"Total Ingredients: {len(ingredients):,}\n\n")
        f.write("---\n\n")

        # 料理セクション
        f.write("# BASE FOODS (DISHES)\n\n")
        for category in sorted(dish_categories.keys()):
            items = dish_categories[category]
            f.write(f"## {category}\n\n")
            for item in items:
                f.write(f"* {item}\n")
            f.write("\n")

        # 食材セクション
        f.write("# INGREDIENTS\n\n")
        for category in sorted(ingredient_categories.keys()):
            items = ingredient_categories[category]
            f.write(f"## {category}\n\n")
            for item in items:
                f.write(f"* {item}\n")
            f.write("\n")

    print("✅ 保存完了!")
    print()

    # サマリー
    print("="*80)
    print("CORE食品リスト サマリー（spec3.md準拠）")
    print("="*80)
    print()
    print("料理カテゴリ別内訳:")
    for category in sorted(dish_categories.keys()):
        print(f"  {category:30s}: {len(dish_categories[category]):,} 項目")
    print()

    print("食材カテゴリ別内訳:")
    for category in sorted(ingredient_categories.keys()):
        print(f"  {category:30s}: {len(ingredient_categories[category]):,} 項目")
    print()

    print(f"出力ファイル: {output_file}")
    print(f"ファイルサイズ: {output_file.stat().st_size / 1024:.1f} KB")
    print("="*80)
    print()

    # spec3.md準拠の確認
    print("📋 spec3.md準拠チェック:")
    print(f"  料理数: {len(dishes)} / 目標: 350-500 → {'✅ OK' if 350 <= len(dishes) <= 500 else '⚠️ 範囲外'}")
    print(f"  食材数: {len(ingredients)} / 目標: 600-900 → {'✅ OK' if 600 <= len(ingredients) <= 900 else '⚠️ 範囲外'}")
    print()

    print("✅ 完了!")
    print()
    print("次のステップ:")
    print("  1. test_scripts/output/complete_prompt.txtのCOREリストを置き換え")
    print("  2. VLMでテストして精度を確認")
    print()


if __name__ == "__main__":
    main()
