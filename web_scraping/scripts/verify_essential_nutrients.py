#!/usr/bin/env python3
"""
1,185食材の必須栄養素（Calories, Total Fat, Total Carbs, Protein）を検証
"""

import json
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.nutrition_facts_extractor import NutritionFactsExtractor, NutrientExtractor
from src.manual_serving_data_loader import ManualServingDataLoader


def main():
    print("🔍 必須栄養素検証（Serving Size成功1,185食材）")
    print("=" * 80)

    # マニュアルデータローダー
    manual_loader = ManualServingDataLoader()

    # データ読み込み
    data_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']

    # Serving Size成功食材のみを対象
    target_foods = []
    for item in results:
        food_name = item.get('food_name', '')
        comp_data = item.get('comprehensive_data', {})
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # Serving Size取得
        serving_info = NutritionFactsExtractor.extract_serving_size_info(
            raw_nutrition,
            food_name=food_name,
            manual_loader=manual_loader
        )

        if serving_info:
            target_foods.append({
                'food_name': food_name,
                'serving_info': serving_info,
                'raw_nutrition': raw_nutrition
            })

    print(f"対象食材数: {len(target_foods)}個")
    print()

    # 必須栄養素チェック
    essential_nutrients = ['total_fat', 'total_carbs', 'protein']

    all_complete = 0
    issues_by_nutrient = {
        'calories': [],
        'total_fat': [],
        'total_carbs': [],
        'protein': []
    }

    for i, food_data in enumerate(target_foods, 1):
        food_name = food_data['food_name']
        serving_info = food_data['serving_info']
        raw_nutrition = food_data['raw_nutrition']

        # Calories
        calories = serving_info.get('calories_per_unit')
        if calories is None or calories < 0:
            issues_by_nutrient['calories'].append({
                'sequence': i,
                'food_name': food_name,
                'value': calories
            })

        # 栄養素
        nutrients = NutrientExtractor.extract_all_nutrients(raw_nutrition)

        for nutrient in essential_nutrients:
            value = nutrients.get(nutrient)
            if value is None or value < 0:
                issues_by_nutrient[nutrient].append({
                    'sequence': i,
                    'food_name': food_name,
                    'value': value
                })

        # 全て揃っているか
        if (calories is not None and calories >= 0 and
            all(nutrients.get(n) is not None and nutrients.get(n) >= 0
                for n in essential_nutrients)):
            all_complete += 1

    # 結果表示
    print("=" * 80)
    print("【検証結果】")
    print("=" * 80)

    print(f"\n✅ 全必須栄養素が揃っている食材: {all_complete}/{len(target_foods)} ({all_complete/len(target_foods)*100:.1f}%)")
    print()

    # 各栄養素の状況
    for nutrient_name in ['calories', 'total_fat', 'total_carbs', 'protein']:
        issues = issues_by_nutrient[nutrient_name]
        success_count = len(target_foods) - len(issues)

        if len(issues) == 0:
            print(f"✅ {nutrient_name:15s}: {success_count}/{len(target_foods)} (100.0%)")
        else:
            print(f"⚠️  {nutrient_name:15s}: {success_count}/{len(target_foods)} ({success_count/len(target_foods)*100:.1f}%)")
            print(f"   問題のある食材: {len(issues)}個")

    # 問題のある食材をリスト表示
    print()
    print("=" * 80)
    print("【問題のある食材詳細】")
    print("=" * 80)

    for nutrient_name in ['calories', 'total_fat', 'total_carbs', 'protein']:
        issues = issues_by_nutrient[nutrient_name]
        if issues:
            print(f"\n❌ {nutrient_name} 不在/不正な値:")
            for issue in issues[:10]:  # 最初の10個
                print(f"   {issue['sequence']:4d}. {issue['food_name']}")
                print(f"         値: {issue['value']}")

    # 総合判定
    print()
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    if all_complete == len(target_foods):
        print("🎉 全1,185食材で必須栄養素が完璧に揃っています！")
        print("   - Calories: 100%")
        print("   - Total Fat: 100%")
        print("   - Total Carbs: 100%")
        print("   - Protein: 100%")
    else:
        missing_count = len(target_foods) - all_complete
        print(f"⚠️  {missing_count}個の食材で必須栄養素が不足しています")
        print()
        print("不足している栄養素:")
        for nutrient_name in ['calories', 'total_fat', 'total_carbs', 'protein']:
            issues = issues_by_nutrient[nutrient_name]
            if issues:
                print(f"   {nutrient_name}: {len(issues)}個")


if __name__ == "__main__":
    main()
