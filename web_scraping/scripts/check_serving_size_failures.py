#!/usr/bin/env python3
"""
Serving Size抽出失敗食材の特定
"""

import json
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.nutrition_facts_extractor import NutritionFactsExtractor


def main():
    print("🔍 Serving Size抽出失敗食材の確認")
    print("=" * 80)

    # データ読み込み
    data_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']
    total = len(results)

    failed_foods = []

    for i, item in enumerate(results, 1):
        food_name = item.get('food_name', 'N/A')
        catalog_category = item.get('catalog_category', 'N/A')

        comp_data = item.get('comprehensive_data', {})
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # Serving Size抽出
        serving_info = NutritionFactsExtractor.extract_serving_size_info(raw_nutrition)

        if not serving_info:
            failed_foods.append({
                'sequence': i,
                'food_name': food_name,
                'category': catalog_category,
                'raw_nutrition_length': len(raw_nutrition)
            })

    print(f"失敗食材数: {len(failed_foods)}/{total} ({len(failed_foods)/total*100:.1f}%)")
    print()

    # カテゴリ別集計
    category_stats = {}
    for item in failed_foods:
        cat = item['category']
        if cat not in category_stats:
            category_stats[cat] = []
        category_stats[cat].append(item)

    print("=" * 80)
    print("【カテゴリ別失敗数】")
    print("=" * 80)
    for cat in sorted(category_stats.keys()):
        print(f"{cat}: {len(category_stats[cat])}個")

    print()
    print("=" * 80)
    print("【失敗食材リスト（全て）】")
    print("=" * 80)

    for item in failed_foods:
        print(f"{item['sequence']:4d}. {item['food_name']}")
        print(f"       カテゴリ: {item['category']}")
        print(f"       raw_nutrition要素数: {item['raw_nutrition_length']}")
        print()

    # 最初の2つの詳細を表示
    print("=" * 80)
    print("【詳細調査: 最初の2食材のraw_nutrition_data】")
    print("=" * 80)

    for i, fail_item in enumerate(failed_foods[:2], 1):
        # 元データから再取得
        item = results[fail_item['sequence'] - 1]
        comp_data = item.get('comprehensive_data', {})
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        print(f"\n{i}. {fail_item['food_name']}")
        print("-" * 80)
        print("raw_nutrition_data (最初の50要素):")
        for idx, val in enumerate(raw_nutrition[:50]):
            print(f"  [{idx:3d}] {val}")


if __name__ == "__main__":
    main()
