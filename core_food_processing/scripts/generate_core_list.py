#!/usr/bin/env python3
"""
generate_core_list.py

CORE食品リストをcomplete_prompt.txt形式で生成するスクリプト

出力形式:
## EXACT_FOOD_LIST (CORE) - FoodOn Ontology + Open Food Facts

## [Category Name]

* Food item name 1
* Food item name 2
...

Usage:
    python core_food_processing/scripts/generate_core_list.py
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent.parent


def categorize_dish(label: str) -> str:
    """料理をカテゴリ分類"""
    label_lower = label.lower()

    categories = {
        "Pizza & Italian": ["pizza", "lasagna", "pasta", "spaghetti", "ravioli", "gnocchi", "panettone"],
        "Sandwiches & Burgers": ["sandwich", "burger", "wrap", "panini", "sub"],
        "Breakfast Foods": ["pancake", "waffle", "oatmeal", "cereal", "muesli", "granola"],
        "Mexican & Tex-Mex": ["burrito", "taco", "quesadilla", "enchilada", "nachos", "tamale", "fajita"],
        "Asian Dishes": ["ramen", "sushi", "curry", "stir fry", "noodle", "dumpling", "pho"],
        "Soups & Stews": ["soup", "stew", "chowder", "bisque", "broth", "consommé"],
        "Salads": ["salad", "coleslaw"],
        "Snacks & Appetizers": ["popcorn", "chips", "crackers", "pretzels"],
        "Beverages": ["juice", "smoothie", "shake", "coffee", "tea", "soda", "beer", "wine", "kefir"],
        "Desserts & Sweets": ["cake", "cookie", "brownie", "pudding", "ice cream", "pie", "tart"],
        "Dairy Products": ["yogurt", "cheese", "milk"],
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
        "Meat & Poultry": ["beef", "pork", "chicken", "turkey", "lamb", "veal", "duck", "goose", "meat"],
        "Seafood": ["fish", "salmon", "tuna", "shrimp", "crab", "lobster", "oyster", "clam", "mussel", "scallop", "squid", "octopus", "anchovy", "sardine", "mackerel", "herring", "cod", "halibut", "trout", "bass", "perch", "pike", "catfish", "tilapia", "sole", "flounder", "haddock", "pollock", "snapper", "swordfish"],
        "Dairy & Eggs": ["milk", "cheese", "cream", "butter", "yogurt", "egg", "whey"],
        "Vegetables": ["lettuce", "tomato", "onion", "garlic", "pepper", "carrot", "potato", "broccoli", "spinach", "kale", "cabbage", "cauliflower", "celery", "cucumber", "zucchini", "squash", "pumpkin", "eggplant", "mushroom", "asparagus", "bean", "pea"],
        "Fruits": ["apple", "banana", "orange", "grape", "berry", "melon", "peach", "pear", "plum", "cherry", "apricot", "mango", "pineapple", "papaya", "kiwi", "fig", "date", "lemon", "lime", "grapefruit"],
        "Grains & Cereals": ["rice", "wheat", "oat", "barley", "corn", "flour", "bread", "grain", "cereal"],
        "Nuts & Seeds": ["almond", "walnut", "peanut", "cashew", "pistachio", "hazelnut", "pecan", "seed", "sago"],
        "Oils & Fats": ["oil", "fat", "lard", "shortening"],
        "Herbs & Spices": ["basil", "oregano", "thyme", "rosemary", "sage", "parsley", "cilantro", "mint", "dill", "spice", "herb"],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in label_lower:
                return category

    return "Other Ingredients"


def main():
    """メイン処理"""
    print("="*80)
    print("CORE食品リスト生成スクリプト（complete_prompt.txt形式）")
    print("="*80)
    print()

    # 入力ファイル
    dishes_json = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_core.json"
    ingredients_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_core.json"

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

    # complete_prompt.txt形式で出力
    output_file = PROJECT_ROOT / "core_food_processing" / "output" / "foodon_core_list.txt"

    print(f"💾 complete_prompt.txt形式で保存中: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        # ヘッダー
        f.write("## EXACT_FOOD_LIST (CORE) - FoodOn Ontology + Open Food Facts\n\n")
        f.write(f"Generated from FoodOn (multi-component food + food by organism)\n")
        f.write(f"Filtered by Open Food Facts frequency data\n\n")
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
    print("CORE食品リスト サマリー")
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

    print("✅ 完了!")
    print()
    print("次のステップ:")
    print("  1. test_scripts/output/complete_prompt.txtのCOREリストを置き換え")
    print("  2. VLMでテストして精度を確認")
    print()


if __name__ == "__main__":
    main()
