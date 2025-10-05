#!/usr/bin/env python3
"""
最終統合データ (complete_scraping_data_1188_foods_final.json) の検証
"""

import json
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.nutrition_facts_extractor import NutritionFactsExtractor, NutrientExtractor
from src.manual_serving_data_loader import ManualServingDataLoader


def main():
    print("🎯 最終データ検証 (complete_scraping_data_1188_foods_final.json)")
    print("=" * 80)

    # マニュアルデータローダー
    manual_loader = ManualServingDataLoader()
    print(f"📋 マニュアルデータ: {len(manual_loader.manual_data)}件")
    print()

    # 最終データ読み込み
    final_file = Path('important_data/complete_scraping_data_1188_foods_final.json')
    with open(final_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']
    total = len(results)
    print(f"📊 総食材数: {total}個")
    print()

    # 検証統計
    stats = {
        'total': total,
        'has_select_serving': 0,
        'serving_size_success': 0,
        'serving_auto': 0,
        'serving_manual': 0,
        'serving_failed': 0,
        'essential_complete': 0,
        'calories_ok': 0,
        'total_fat_ok': 0,
        'total_carbs_ok': 0,
        'protein_ok': 0
    }

    failed_foods = []

    # 全食材を検証
    for i, item in enumerate(results, 1):
        food_name = item.get('food_name', '')
        comp_data = item.get('comprehensive_data', {})

        # 'Select Serving'確認
        serving_options = comp_data.get('serving_options', {})
        raw_serving_data = serving_options.get('raw_serving_data', [])

        if 'Select Serving' in raw_serving_data:
            stats['has_select_serving'] += 1

        # 栄養データ
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # Serving Size抽出
        serving_info = NutritionFactsExtractor.extract_serving_size_info(
            raw_nutrition,
            food_name=food_name,
            manual_loader=manual_loader
        )

        if serving_info:
            stats['serving_size_success'] += 1

            source = serving_info.get('source', 'unknown')
            if source == 'auto':
                stats['serving_auto'] += 1
            elif source == 'manual':
                stats['serving_manual'] += 1

            # 必須栄養素
            calories = serving_info.get('calories_per_unit')
            if calories is not None and calories >= 0:
                stats['calories_ok'] += 1

            # 栄養素抽出
            nutrients = NutrientExtractor.extract_all_nutrients(raw_nutrition)

            total_fat = nutrients.get('total_fat')
            if total_fat is not None and total_fat >= 0:
                stats['total_fat_ok'] += 1

            total_carbs = nutrients.get('total_carbs')
            if total_carbs is not None and total_carbs >= 0:
                stats['total_carbs_ok'] += 1

            protein = nutrients.get('protein')
            if protein is not None and protein >= 0:
                stats['protein_ok'] += 1

            # 全て揃っているか
            if (calories is not None and calories >= 0 and
                total_fat is not None and total_fat >= 0 and
                total_carbs is not None and total_carbs >= 0 and
                protein is not None and protein >= 0):
                stats['essential_complete'] += 1
        else:
            stats['serving_failed'] += 1
            if len(failed_foods) < 10:
                failed_foods.append({
                    'sequence': i,
                    'food_name': food_name,
                    'has_select_serving': 'Select Serving' in raw_serving_data
                })

    # 結果表示
    print("=" * 80)
    print("【検証結果】")
    print("=" * 80)
    print()

    print(f"📋 'Select Serving':")
    print(f"   存在: {stats['has_select_serving']}/{total} ({stats['has_select_serving']/total*100:.1f}%)")
    print()

    print(f"🍽️  Serving Size抽出:")
    print(f"   成功: {stats['serving_size_success']}/{total} ({stats['serving_size_success']/total*100:.1f}%)")
    print(f"   - 自動抽出: {stats['serving_auto']}個")
    print(f"   - マニュアル補完: {stats['serving_manual']}個")
    print(f"   失敗: {stats['serving_failed']}個 ({stats['serving_failed']/total*100:.1f}%)")
    print()

    print(f"🔋 必須栄養素:")
    print(f"   Calories:    {stats['calories_ok']}/{total} ({stats['calories_ok']/total*100:.1f}%)")
    print(f"   Total Fat:   {stats['total_fat_ok']}/{total} ({stats['total_fat_ok']/total*100:.1f}%)")
    print(f"   Total Carbs: {stats['total_carbs_ok']}/{total} ({stats['total_carbs_ok']/total*100:.1f}%)")
    print(f"   Protein:     {stats['protein_ok']}/{total} ({stats['protein_ok']/total*100:.1f}%)")
    print()
    print(f"   全て完備: {stats['essential_complete']}/{total} ({stats['essential_complete']/total*100:.1f}%)")
    print()

    # 失敗詳細
    if failed_foods:
        print("=" * 80)
        print("【Serving Size抽出失敗 (最初の10個)】")
        print("=" * 80)
        for item in failed_foods:
            print(f"{item['sequence']:4d}. {item['food_name']}")
            print(f"       'Select Serving': {'あり' if item['has_select_serving'] else 'なし'}")
        print()

    # 総合判定
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    if stats['serving_size_success'] >= total * 0.99:  # 99%以上
        print("🎉 優秀！ 99%以上の食材でServing Size抽出に成功しました")
        print(f"   成功率: {stats['serving_size_success']/total*100:.2f}%")

    if stats['essential_complete'] >= total * 0.99:  # 99%以上
        print("🎉 優秀！ 99%以上の食材で必須栄養素が完備されています")
        print(f"   完備率: {stats['essential_complete']/total*100:.2f}%")

    print()
    print(f"📊 最終統計:")
    print(f"   総食材数: {total}個")
    print(f"   'Select Serving'存在: {stats['has_select_serving']}個 ({stats['has_select_serving']/total*100:.1f}%)")
    print(f"   Serving Size抽出成功: {stats['serving_size_success']}個 ({stats['serving_size_success']/total*100:.1f}%)")
    print(f"   必須栄養素完備: {stats['essential_complete']}個 ({stats['essential_complete']/total*100:.1f}%)")


if __name__ == "__main__":
    main()
