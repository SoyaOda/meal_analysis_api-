#!/usr/bin/env python3
"""
1,185食材の完全な栄養情報を抽出して保存
Serving Size + 全ての有効な栄養素を取得
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.nutrition_facts_extractor import NutritionFactsExtractor, NutrientExtractor
from src.manual_serving_data_loader import ManualServingDataLoader


def main():
    print("🥗 完全栄養情報抽出 (1,185食材)")
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
    print(f"📊 総食材数: {len(results)}個")
    print()

    # 栄養情報抽出
    complete_nutrition_data = []
    success_count = 0
    failed_foods = []

    for i, item in enumerate(results, 1):
        food_name = item.get('food_name', '')
        comp_data = item.get('comprehensive_data', {})

        # 栄養データ取得
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # Serving Size抽出
        serving_info = NutritionFactsExtractor.extract_serving_size_info(
            raw_nutrition,
            food_name=food_name,
            manual_loader=manual_loader
        )

        if not serving_info:
            failed_foods.append({
                'sequence': i,
                'food_name': food_name,
                'reason': 'No serving info'
            })
            continue

        # 全栄養素抽出
        nutrients = NutrientExtractor.extract_all_nutrients(raw_nutrition)

        # 必須栄養素チェック
        calories = serving_info.get('calories_per_unit')
        total_fat = nutrients.get('total_fat')
        total_carbs = nutrients.get('total_carbs')
        protein = nutrients.get('protein')

        # 必須栄養素が揃っているかチェック
        if (calories is None or calories < 0 or
            total_fat is None or total_fat < 0 or
            total_carbs is None or total_carbs < 0 or
            protein is None or protein < 0):
            failed_foods.append({
                'sequence': i,
                'food_name': food_name,
                'reason': 'Incomplete essential nutrients'
            })
            continue

        # 有効な栄養素のみを抽出（None以外、かつ0以上）
        valid_nutrients = {}
        for key, value in nutrients.items():
            if value is not None and value >= 0:
                valid_nutrients[key] = value

        # カタログ情報
        catalog_category = item.get('catalog_category', 'unknown')

        # 完全な栄養情報を構築
        food_nutrition_data = {
            'sequence': i,
            'food_name': food_name,
            'catalog_category': catalog_category,
            'serving_info': {
                'unit': serving_info.get('unit'),
                'grams_per_unit': serving_info.get('grams_per_unit'),
                'calories_per_unit': serving_info.get('calories_per_unit'),
                'source': serving_info.get('source', 'auto')
            },
            'essential_nutrients': {
                'calories': calories,
                'total_fat': total_fat,
                'total_carbs': total_carbs,
                'protein': protein
            },
            'all_nutrients': valid_nutrients,
            'total_nutrients_found': len(valid_nutrients)
        }

        complete_nutrition_data.append(food_nutrition_data)
        success_count += 1

        # 進捗表示（100食材ごと）
        if i % 100 == 0:
            print(f"  処理中... {i}/{len(results)} ({i/len(results)*100:.1f}%)")

    print(f"\n✅ 抽出完了: {success_count}食材")
    print(f"❌ 失敗: {len(failed_foods)}食材")
    print()

    # 栄養素の統計
    print("=" * 80)
    print("【栄養素統計】")
    print("=" * 80)

    nutrient_counts = {}
    for food_data in complete_nutrition_data:
        for nutrient_key in food_data['all_nutrients'].keys():
            if nutrient_key not in nutrient_counts:
                nutrient_counts[nutrient_key] = 0
            nutrient_counts[nutrient_key] += 1

    print(f"\n発見された栄養素の種類: {len(nutrient_counts)}種類")
    print()

    # 栄養素を出現頻度順にソート
    sorted_nutrients = sorted(nutrient_counts.items(), key=lambda x: x[1], reverse=True)

    print("栄養素の出現頻度:")
    for nutrient_key, count in sorted_nutrients:
        percentage = count / success_count * 100
        print(f"  {nutrient_key:30s}: {count:4d}/{success_count} ({percentage:5.1f}%)")

    # 保存データ構築
    output_data = {
        'extraction_summary': {
            'timestamp': datetime.now().isoformat(),
            'source_file': 'complete_scraping_data_1188_foods_final.json',
            'total_foods': len(results),
            'successful_extractions': success_count,
            'failed_extractions': len(failed_foods),
            'unique_nutrients_found': len(nutrient_counts),
            'nutrient_statistics': dict(sorted_nutrients)
        },
        'nutrition_data': complete_nutrition_data,
        'failed_foods': failed_foods
    }

    # JSON保存
    output_file = Path('important_data/complete_nutrition_1185_foods.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 80)
    print("【保存完了】")
    print("=" * 80)
    print(f"💾 ファイル: {output_file}")
    print(f"📊 データサイズ: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    # サンプルデータ表示（最初の3食材）
    print("=" * 80)
    print("【サンプルデータ（最初の3食材）】")
    print("=" * 80)

    for i, food_data in enumerate(complete_nutrition_data[:3], 1):
        print(f"\n{i}. {food_data['food_name']}")
        print(f"   カテゴリ: {food_data['catalog_category']}")
        print(f"   Serving: {food_data['serving_info']['unit']} = {food_data['serving_info']['grams_per_unit']}g")
        print(f"   カロリー: {food_data['serving_info']['calories_per_unit']} kcal")
        print(f"   必須栄養素:")
        print(f"     - Total Fat: {food_data['essential_nutrients']['total_fat']}g")
        print(f"     - Total Carbs: {food_data['essential_nutrients']['total_carbs']}g")
        print(f"     - Protein: {food_data['essential_nutrients']['protein']}g")
        print(f"   全栄養素: {food_data['total_nutrients_found']}種類")

        # その他の栄養素（最初の5個）
        other_nutrients = {k: v for k, v in food_data['all_nutrients'].items()
                          if k not in ['total_fat', 'total_carbs', 'protein']}
        if other_nutrients:
            print(f"   その他の栄養素（サンプル）:")
            for key, value in list(other_nutrients.items())[:5]:
                print(f"     - {key}: {value}")

    # 失敗詳細
    if failed_foods:
        print()
        print("=" * 80)
        print("【抽出失敗詳細】")
        print("=" * 80)
        for item in failed_foods:
            print(f"{item['sequence']:4d}. {item['food_name']}")
            print(f"       理由: {item['reason']}")

    print()
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)
    print(f"🎉 {success_count}食材の完全な栄養情報を抽出しました！")
    print(f"   - 必須栄養素（Calories, Fat, Carbs, Protein）: 100%")
    print(f"   - 全栄養素平均: {sum(f['total_nutrients_found'] for f in complete_nutrition_data) / len(complete_nutrition_data):.1f}種類/食材")
    print(f"   - 栄養素の種類: {len(nutrient_counts)}種類")


if __name__ == "__main__":
    main()
