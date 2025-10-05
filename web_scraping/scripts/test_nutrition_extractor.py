#!/usr/bin/env python3
"""
NutritionFactsExtractorの実データテスト
"""

import json
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.nutrition_facts_extractor import NutritionFactsExtractor, NutrientExtractor
from src.manual_serving_data_loader import ManualServingDataLoader


def main():
    print("🧪 NutritionFactsExtractor 実データテスト（マニュアルデータ統合版）")
    print("=" * 80)

    # マニュアルデータローダー初期化
    manual_loader = ManualServingDataLoader()
    print(f"📋 マニュアルデータ読み込み: {len(manual_loader.manual_data)}件")
    print()

    # 実データ読み込み
    data_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']

    # テスト対象：最初の5食材
    test_count = 5
    success_count = 0
    partial_success_count = 0
    failed_count = 0

    for i, item in enumerate(results[:test_count], 1):
        food_name = item.get('food_name', 'N/A')
        comp_data = item.get('comprehensive_data', {})
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        print(f"\n{i}. {food_name}")
        print("-" * 80)

        # Serving Size抽出（マニュアルデータも使用）
        serving_info = NutritionFactsExtractor.extract_serving_size_info(
            raw_nutrition,
            food_name=food_name,
            manual_loader=manual_loader
        )

        if serving_info:
            print(f"✅ Serving Size:")
            print(f"   Unit: {serving_info['unit']}")
            print(f"   Grams per unit: {serving_info['grams_per_unit']}g")
            print(f"   Calories per unit: {serving_info['calories_per_unit']} kcal")

            # 栄養素抽出
            nutrients = NutrientExtractor.extract_all_nutrients(raw_nutrition)

            # 存在する栄養素のみ表示
            found_nutrients = {k: v for k, v in nutrients.items() if v is not None}

            print(f"\n✅ 栄養素 ({len(found_nutrients)}個発見):")
            for key, value in found_nutrients.items():
                print(f"   {key}: {value}")

            if len(found_nutrients) >= 10:
                success_count += 1
            else:
                partial_success_count += 1
        else:
            print("❌ Serving Size情報が見つかりませんでした")
            failed_count += 1

    # サマリー
    print()
    print("=" * 80)
    print("📊 テスト結果サマリー")
    print("=" * 80)
    print(f"成功（10個以上の栄養素）: {success_count}/{test_count}")
    print(f"部分成功（10個未満）: {partial_success_count}/{test_count}")
    print(f"失敗（Serving Size不在）: {failed_count}/{test_count}")

    # 全データでの成功率を確認
    print()
    print("=" * 80)
    print("📊 全1,188食材での成功率確認")
    print("=" * 80)

    total = len(results)
    serving_success = 0
    serving_auto = 0
    serving_manual = 0
    nutrient_stats = {}

    for item in results:
        food_name = item.get('food_name', '')
        comp_data = item.get('comprehensive_data', {})
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # Serving Size（マニュアルデータも使用）
        serving_info = NutritionFactsExtractor.extract_serving_size_info(
            raw_nutrition,
            food_name=food_name,
            manual_loader=manual_loader
        )
        if serving_info:
            serving_success += 1
            if serving_info.get('source') == 'auto':
                serving_auto += 1
            elif serving_info.get('source') == 'manual':
                serving_manual += 1

        # 栄養素
        nutrients = NutrientExtractor.extract_all_nutrients(raw_nutrition)
        for key, value in nutrients.items():
            if key not in nutrient_stats:
                nutrient_stats[key] = 0
            if value is not None:
                nutrient_stats[key] += 1

    print(f"Serving Size抽出成功: {serving_success}/{total} ({serving_success/total*100:.1f}%)")
    print(f"   自動抽出: {serving_auto}個")
    print(f"   マニュアル補完: {serving_manual}個")
    print()
    print("栄養素抽出成功率:")
    for key in sorted(nutrient_stats.keys()):
        count = nutrient_stats[key]
        print(f"   {key:25s}: {count:4d}/{total} ({count/total*100:5.1f}%)")


if __name__ == "__main__":
    main()
