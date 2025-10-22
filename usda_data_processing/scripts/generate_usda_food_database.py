#!/usr/bin/env python
"""
usda_database/surveyDownload.jsonから食品データベースを生成（全データ版）

3つのカテゴリに分類：
1. 複合料理（Composite Dishes）: inputFoods >= 2
2. 調理済み食材（Prepared Ingredients）: inputFoods == 1 + 調理キーワード含む
3. 基本食材（Raw Ingredients）: inputFoods == 1 + 調理キーワード含まない

出力形式：
- TXT: 料理名リストのみ（プロンプト用）
- JSON: 含有食材・栄養素情報付き（API用）

注意: このバージョンでは除外ルール・統合ルールは適用されません（全データ出力）
"""

import json
from typing import List, Dict, Tuple
from collections import defaultdict
from pathlib import Path
from datetime import datetime


# 調理キーワード（熱調理 + 加工調理）
COOKING_KEYWORDS = [
    'cooked', 'toasted', 'baked', 'broiled', 'fried', 'roasted',
    'boiled', 'steamed', 'grilled', 'poached', 'sauteed', 'braised', 'stewed',
    'smoked', 'cured', 'dried', 'pickled'
]


def load_survey_data(file_path: str) -> List[Dict]:
    """surveyDownload.jsonを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('SurveyFoods', [])


def is_cooked_ingredient(description: str) -> bool:
    """調理済み食材かどうかを判定"""
    desc_lower = description.lower()
    return any(keyword in desc_lower for keyword in COOKING_KEYWORDS)


def extract_foods_by_three_types(
    foods: List[Dict]
) -> Tuple[Dict[str, List[Dict]], Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    """
    食品を3カテゴリに分類して抽出（完全なfoodオブジェクトを保持）

    Args:
        foods: 食品リスト

    Returns:
        (composite_dishes, prepared_ingredients, raw_ingredients)
        各辞書: {category_name: [food_objects...]}
    """
    composite_dishes = defaultdict(list)
    prepared_ingredients = defaultdict(list)
    raw_ingredients = defaultdict(list)

    for food in foods:
        food_name = food.get('description', '')

        # inputFoodsの数を取得
        input_foods = food.get('inputFoods', [])
        input_foods_count = len(input_foods)

        # カテゴリを取得
        wweia = food.get('wweiaFoodCategory', {})
        category_name = wweia.get('wweiaFoodCategoryDescription', 'Unknown Category')

        # 3カテゴリに分類
        if input_foods_count >= 2:
            # 複合料理
            composite_dishes[category_name].append(food)
        elif input_foods_count == 1:
            # 調理済みか基本食材かを判定
            if is_cooked_ingredient(food_name):
                prepared_ingredients[category_name].append(food)
            else:
                raw_ingredients[category_name].append(food)
        # input_foods_count == 0 の場合（例：Human milk）は除外

    return composite_dishes, prepared_ingredients, raw_ingredients


def generate_food_list_txt(
    foods_by_category: Dict[str, List[Dict]],
    output_path: str,
    title: str,
    item_label: str
) -> None:
    """
    食品リストを一つのtxtファイルに出力（料理名のみ）

    Args:
        foods_by_category: {category_name: [food_objects...]}
        output_path: 出力ファイルパス
        title: ファイルのタイトル
        item_label: アイテムのラベル（"dishes", "prepared", "raw"）
    """
    # カテゴリを食品数の多い順にソート
    sorted_categories = sorted(
        foods_by_category.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    total_items = sum(len(items) for items in foods_by_category.values())

    with open(output_path, 'w', encoding='utf-8') as f:
        # ヘッダー
        f.write(f"# {title}\n")
        f.write("# Source: usda_database/surveyDownload.json\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write("# Note: 全データ出力（除外・統合ルール未適用）\n")
        f.write("\n")
        f.write(f"# Total Categories: {len(foods_by_category)}\n")
        f.write(f"# Total {item_label.capitalize()}: {total_items}\n")
        f.write("\n")
        f.write("=" * 80)
        f.write("\n\n")

        # カテゴリごとに食品名を出力
        for category_name, food_objects in sorted_categories:
            f.write(f"## {category_name}\n")
            f.write(f"## ({len(food_objects)} {item_label})\n")
            f.write("\n")

            for food_obj in food_objects:
                food_name = food_obj.get('description', '')
                f.write(f"{food_name}\n")

            f.write("\n")
            f.write("-" * 80)
            f.write("\n\n")


def generate_food_database_json(
    foods_by_category: Dict[str, List[Dict]],
    output_path: str,
    title: str
) -> None:
    """
    食品データベースをJSONファイルに出力（含有食材・栄養素情報付き）

    Args:
        foods_by_category: {category_name: [food_objects...]}
        output_path: 出力ファイルパス
        title: データベースのタイトル
    """
    # カテゴリを食品数の多い順にソート
    sorted_categories = sorted(
        foods_by_category.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    total_items = sum(len(items) for items in foods_by_category.values())

    # JSON構造を作成
    database = {
        "metadata": {
            "title": title,
            "source": "usda_database/surveyDownload.json",
            "generated": datetime.now().isoformat(),
            "total_categories": len(foods_by_category),
            "total_foods": total_items,
            "note": "全データ出力（除外・統合ルール未適用）"
        },
        "categories": {}
    }

    # カテゴリごとにデータを追加
    for category_name, food_objects in sorted_categories:
        database["categories"][category_name] = {
            "count": len(food_objects),
            "foods": []
        }

        for food_obj in food_objects:
            # 必要な情報のみを抽出
            food_data = {
                "foodCode": food_obj.get('foodCode'),
                "description": food_obj.get('description'),
                "fdcId": food_obj.get('fdcId'),
                "inputFoods": food_obj.get('inputFoods', []),
                "foodNutrients": food_obj.get('foodNutrients', []),
                "wweiaFoodCategory": food_obj.get('wweiaFoodCategory', {})
            }

            database["categories"][category_name]["foods"].append(food_data)

    # JSON出力
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)


def main():
    """メイン実行"""
    # パス設定（usda_data_processing ディレクトリ）
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    survey_json_path = base_dir / "usda_database" / "surveyDownload.json"
    docs_dir = base_dir / "usda_data_processing" / "docs"

    # 出力ファイルパス
    composite_txt = docs_dir / "usda_composite_dishes_all.txt"
    composite_json = docs_dir / "usda_composite_dishes_all.json"

    prepared_txt = docs_dir / "usda_prepared_ingredients_all.txt"
    prepared_json = docs_dir / "usda_prepared_ingredients_all.json"

    raw_txt = docs_dir / "usda_raw_ingredients_all.txt"
    raw_json = docs_dir / "usda_raw_ingredients_all.json"

    print("📂 surveyDownload.json読み込み中...")
    foods = load_survey_data(str(survey_json_path))
    print(f"✅ 総食品数: {len(foods)}件\n")

    print("🔍 食品を3カテゴリに分類中...")
    composite_dishes, prepared_ingredients, raw_ingredients = extract_foods_by_three_types(foods)

    # 統計情報を計算
    stats = {
        "composite": {
            "categories": len(composite_dishes),
            "items": sum(len(dishes) for dishes in composite_dishes.values())
        },
        "prepared": {
            "categories": len(prepared_ingredients),
            "items": sum(len(items) for items in prepared_ingredients.values())
        },
        "raw": {
            "categories": len(raw_ingredients),
            "items": sum(len(items) for items in raw_ingredients.values())
        }
    }

    print(f"✅ 抽出完了:")
    print(f"   【複合料理】")
    print(f"   - カテゴリー数: {stats['composite']['categories']}")
    print(f"   - 複合料理数: {stats['composite']['items']}")
    print(f"   【調理済み食材】")
    print(f"   - カテゴリー数: {stats['prepared']['categories']}")
    print(f"   - 調理済み食材数: {stats['prepared']['items']}")
    print(f"   【基本食材】")
    print(f"   - カテゴリー数: {stats['raw']['categories']}")
    print(f"   - 基本食材数: {stats['raw']['items']}\n")

    # ========================================
    # 複合料理の出力
    # ========================================
    print("📝 複合料理リスト生成中...")
    generate_food_list_txt(
        composite_dishes,
        str(composite_txt),
        "USDA FNDDS Composite Dishes List (All Data)",
        "dishes"
    )
    print(f"✅ TXT生成完了: {composite_txt}")
    print(f"   - ファイルサイズ: {composite_txt.stat().st_size / 1024:.1f} KB")

    generate_food_database_json(
        composite_dishes,
        str(composite_json),
        "USDA FNDDS Composite Dishes Database (All Data)"
    )
    print(f"✅ JSON生成完了: {composite_json}")
    print(f"   - ファイルサイズ: {composite_json.stat().st_size / 1024:.1f} KB\n")

    # ========================================
    # 調理済み食材の出力
    # ========================================
    print("📝 調理済み食材リスト生成中...")
    generate_food_list_txt(
        prepared_ingredients,
        str(prepared_txt),
        "USDA FNDDS Prepared Ingredients List (All Data)",
        "prepared"
    )
    print(f"✅ TXT生成完了: {prepared_txt}")
    print(f"   - ファイルサイズ: {prepared_txt.stat().st_size / 1024:.1f} KB")

    generate_food_database_json(
        prepared_ingredients,
        str(prepared_json),
        "USDA FNDDS Prepared Ingredients Database (All Data)"
    )
    print(f"✅ JSON生成完了: {prepared_json}")
    print(f"   - ファイルサイズ: {prepared_json.stat().st_size / 1024:.1f} KB\n")

    # ========================================
    # 基本食材の出力
    # ========================================
    print("📝 基本食材リスト生成中...")
    generate_food_list_txt(
        raw_ingredients,
        str(raw_txt),
        "USDA FNDDS Raw Ingredients List (All Data)",
        "raw"
    )
    print(f"✅ TXT生成完了: {raw_txt}")
    print(f"   - ファイルサイズ: {raw_txt.stat().st_size / 1024:.1f} KB")

    generate_food_database_json(
        raw_ingredients,
        str(raw_json),
        "USDA FNDDS Raw Ingredients Database (All Data)"
    )
    print(f"✅ JSON生成完了: {raw_json}")
    print(f"   - ファイルサイズ: {raw_json.stat().st_size / 1024:.1f} KB\n")

    # ========================================
    # サマリー表示
    # ========================================
    print(f"{'='*80}")
    print(f"📊 生成サマリー")
    print(f"{'='*80}\n")

    print(f"📈 複合料理 Top 10 カテゴリー:")
    sorted_composite = sorted(
        composite_dishes.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    for i, (category, dishes) in enumerate(sorted_composite[:10], 1):
        print(f"   {i}. {category}: {len(dishes)}件")

    print(f"\n📈 調理済み食材 Top 10 カテゴリー:")
    sorted_prepared = sorted(
        prepared_ingredients.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    for i, (category, items) in enumerate(sorted_prepared[:10], 1):
        print(f"   {i}. {category}: {len(items)}件")

    print(f"\n📈 基本食材 Top 10 カテゴリー:")
    sorted_raw = sorted(
        raw_ingredients.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    for i, (category, items) in enumerate(sorted_raw[:10], 1):
        print(f"   {i}. {category}: {len(items)}件")


if __name__ == "__main__":
    main()
