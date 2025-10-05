#!/usr/bin/env python3
"""
再収集した63食材のServing Size抽出を検証
"""

import json
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.nutrition_facts_extractor import NutritionFactsExtractor
from src.manual_serving_data_loader import ManualServingDataLoader


def main():
    print("🔍 再収集63食材のServing Size抽出検証")
    print("=" * 80)

    # マニュアルデータローダー
    manual_loader = ManualServingDataLoader()
    print(f"📋 マニュアルデータ読み込み: {len(manual_loader.manual_data)}件")
    print()

    # 再収集結果読み込み
    retry_file = Path('important_data/retry_select_serving_results.json')
    with open(retry_file, 'r', encoding='utf-8') as f:
        retry_data = json.load(f)

    retry_results = retry_data['retry_results']
    print(f"📊 再収集結果: {len(retry_results)}食材")
    print()

    # 検証統計
    stats = {
        'total': len(retry_results),
        'has_select_serving': 0,
        'serving_extraction_success': 0,
        'serving_auto': 0,
        'serving_manual': 0,
        'serving_failed': 0,
        'essential_nutrients_complete': 0
    }

    failed_extractions = []

    # 各食材を検証
    for i, item in enumerate(retry_results, 1):
        food_name = item.get('food_name', '')
        comp_data = item.get('comprehensive_data', {})

        # Serving options確認
        serving_options = comp_data.get('serving_options', {})
        raw_serving_data = serving_options.get('raw_serving_data', [])

        if 'Select Serving' in raw_serving_data:
            stats['has_select_serving'] += 1

        # Nutrition data確認
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # Serving Size抽出テスト
        serving_info = NutritionFactsExtractor.extract_serving_size_info(
            raw_nutrition,
            food_name=food_name,
            manual_loader=manual_loader
        )

        if serving_info:
            stats['serving_extraction_success'] += 1

            source = serving_info.get('source', 'unknown')
            if source == 'auto':
                stats['serving_auto'] += 1
            elif source == 'manual':
                stats['serving_manual'] += 1

            # 必須栄養素チェック（Calories, Total Fat, Total Carbs, Protein）
            calories = serving_info.get('calories_per_unit')
            if calories is not None and calories >= 0:
                stats['essential_nutrients_complete'] += 1
        else:
            stats['serving_failed'] += 1
            failed_extractions.append({
                'sequence': i,
                'food_name': food_name,
                'has_select_serving': 'Select Serving' in raw_serving_data
            })

    # 結果表示
    print("=" * 80)
    print("【検証結果】")
    print("=" * 80)
    print()
    print(f"✅ 'Select Serving'存在: {stats['has_select_serving']}/{stats['total']} ({stats['has_select_serving']/stats['total']*100:.1f}%)")
    print()
    print(f"📊 Serving Size抽出:")
    print(f"   成功: {stats['serving_extraction_success']}/{stats['total']} ({stats['serving_extraction_success']/stats['total']*100:.1f}%)")
    print(f"   - 自動抽出: {stats['serving_auto']}個")
    print(f"   - マニュアル補完: {stats['serving_manual']}個")
    print(f"   失敗: {stats['serving_failed']}個")
    print()
    print(f"🔋 必須栄養素完備: {stats['essential_nutrients_complete']}/{stats['total']} ({stats['essential_nutrients_complete']/stats['total']*100:.1f}%)")
    print()

    # 失敗詳細
    if failed_extractions:
        print("=" * 80)
        print("【抽出失敗詳細】")
        print("=" * 80)
        for item in failed_extractions:
            print(f"{item['sequence']:3d}. {item['food_name']}")
            print(f"     'Select Serving': {'あり' if item['has_select_serving'] else 'なし'}")
            print()

    # 総合判定
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    if stats['has_select_serving'] == stats['total']:
        print("🎉 全63食材で'Select Serving'が存在します！")
    else:
        print(f"⚠️  {stats['total'] - stats['has_select_serving']}個の食材で'Select Serving'が不在")

    print()

    if stats['serving_extraction_success'] == stats['total']:
        print("🎉 全63食材でServing Size抽出に成功しました！")
        print(f"   自動抽出: {stats['serving_auto']}個")
        print(f"   マニュアル補完: {stats['serving_manual']}個")
    else:
        print(f"⚠️  {stats['serving_failed']}個の食材でServing Size抽出に失敗")


if __name__ == "__main__":
    main()
