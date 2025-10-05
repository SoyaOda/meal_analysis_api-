#!/usr/bin/env python3
"""
complete_scraping_data_1188_foods.jsonの栄養データ構造検証
"""

import json
import re
from pathlib import Path


def main():
    print("🔍 栄養データ構造検証")
    print("=" * 80)

    # データ読み込み
    data_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']
    total = len(results)

    print(f"総食材数: {total}個")
    print()

    # 検証1: Serving Size構造
    print("=" * 80)
    print("【検証1】Serving Size構造")
    print("=" * 80)

    serving_size_found = 0
    serving_size_samples = []
    no_serving_size_samples = []

    for i, item in enumerate(results, 1):
        comp_data = item.get('comprehensive_data', {})
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # Serving Sizeパターンを探す
        found = False
        serving_info = []

        for idx, item_text in enumerate(raw_nutrition):
            if isinstance(item_text, str):
                # "Serving Size" を探す
                if item_text.strip() == "Serving Size":
                    # 次の要素を確認（unit (Xg)パターン）
                    if idx + 1 < len(raw_nutrition):
                        next_item = raw_nutrition[idx + 1]
                        # "cup (128g)" のようなパターン
                        if re.match(r'^.+\s*\(\d+(?:\.\d+)?g\)$', str(next_item)):
                            # さらに"Amount per serving", "Calories", "Xcals"を確認
                            if idx + 4 < len(raw_nutrition):
                                if (raw_nutrition[idx + 2] == "Amount per serving" and
                                    raw_nutrition[idx + 3] == "Calories" and
                                    re.match(r'^\d+(?:\.\d+)?cals?$', str(raw_nutrition[idx + 4]))):
                                    found = True
                                    serving_info = [
                                        raw_nutrition[idx],      # Serving Size
                                        raw_nutrition[idx + 1],  # unit (Xg)
                                        raw_nutrition[idx + 2],  # Amount per serving
                                        raw_nutrition[idx + 3],  # Calories
                                        raw_nutrition[idx + 4]   # Xcals
                                    ]
                                    break

        if found:
            serving_size_found += 1
            if len(serving_size_samples) < 3:
                serving_size_samples.append({
                    'sequence': i,
                    'food_name': item.get('food_name', 'N/A'),
                    'serving_info': serving_info
                })
        else:
            if len(no_serving_size_samples) < 5:
                no_serving_size_samples.append({
                    'sequence': i,
                    'food_name': item.get('food_name', 'N/A')
                })

    print(f"Serving Size構造発見: {serving_size_found}/{total} ({serving_size_found/total*100:.1f}%)")
    print()

    if serving_size_samples:
        print("✅ 正常なサンプル:")
        for sample in serving_size_samples:
            print(f"   {sample['sequence']}. {sample['food_name']}")
            print(f"      構造: {' | '.join(sample['serving_info'])}")
            print()

    if no_serving_size_samples:
        print("❌ Serving Size構造不在サンプル:")
        for sample in no_serving_size_samples:
            print(f"   {sample['sequence']}. {sample['food_name']}")

    # 検証2: 主要栄養素
    print()
    print("=" * 80)
    print("【検証2】主要栄養素データ")
    print("=" * 80)

    # 検証対象の栄養素リスト
    required_nutrients = [
        ('Total Fat', r'^\d+(?:\.\d+)?g$'),
        ('Saturated Fat', r'^\d+(?:\.\d+)?g$'),
        ('Trans Fat', r'^\d+(?:\.\d+)?g$'),
        ('Total Carbs', r'^\d+(?:\.\d+)?g$'),
        ('Dietary Fiber', r'^\d+(?:\.\d+)?g$'),
        ('Total Sugars', r'^\d+(?:\.\d+)?g$'),
        ('Protein', r'^\d+(?:\.\d+)?g$'),
        ('Cholesterol', r'^\d+(?:\.\d+)?mg$'),
        ('Sodium', r'^\d+(?:\.\d+)?mg$'),
        ('Vitamin A', r'^\d+(?:\.\d+)?mcg$'),
        ('Vitamin C', r'^\d+(?:\.\d+)?mg$'),
        ('Calcium', r'^\d+(?:\.\d+)?mg$'),
        ('Iron', r'^\d+(?:\.\d+)?mg$'),
        ('Potassium', r'^\d+(?:\.\d+)?mg$')
    ]

    # 栄養素ごとの発見数を集計
    nutrient_stats = {name: 0 for name, _ in required_nutrients}
    missing_nutrients_samples = []

    for i, item in enumerate(results, 1):
        comp_data = item.get('comprehensive_data', {})
        nutrition_data = comp_data.get('nutrition_data', {})
        detailed_nutrients = nutrition_data.get('detailed_nutrients', {})
        raw_nutrition = detailed_nutrients.get('raw_nutrition_data', [])

        # 各栄養素を検索
        found_nutrients = set()

        for idx, item_text in enumerate(raw_nutrition):
            if isinstance(item_text, str):
                for nutrient_name, value_pattern in required_nutrients:
                    # パターン1: 栄養素名の次に値がある
                    if item_text.strip() == nutrient_name:
                        if idx + 1 < len(raw_nutrition):
                            next_item = str(raw_nutrition[idx + 1])
                            if re.match(value_pattern, next_item):
                                found_nutrients.add(nutrient_name)
                                break

                    # パターン2: "栄養素名 値" の形式
                    match = re.match(f'^{re.escape(nutrient_name)}\\s+({value_pattern[1:-1]})$', item_text.strip())
                    if match:
                        found_nutrients.add(nutrient_name)
                        break

        # 統計更新
        for nutrient_name in found_nutrients:
            nutrient_stats[nutrient_name] += 1

        # 欠けている栄養素を記録
        missing = set(name for name, _ in required_nutrients) - found_nutrients
        if missing and len(missing_nutrients_samples) < 3:
            missing_nutrients_samples.append({
                'sequence': i,
                'food_name': item.get('food_name', 'N/A'),
                'missing': list(missing)
            })

    # 栄養素統計表示
    print("栄養素発見率:")
    for nutrient_name, pattern in required_nutrients:
        count = nutrient_stats[nutrient_name]
        print(f"   {nutrient_name:20s}: {count:4d}/{total} ({count/total*100:5.1f}%)")

    if missing_nutrients_samples:
        print()
        print("⚠️  栄養素欠損サンプル:")
        for sample in missing_nutrients_samples:
            print(f"   {sample['sequence']}. {sample['food_name']}")
            print(f"      欠損: {', '.join(sample['missing'])}")
            print()

    # 総合判定
    print()
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    # 全栄養素が90%以上で見つかったか
    min_nutrient_rate = min(nutrient_stats.values()) / total * 100

    if serving_size_found >= total * 0.9 and min_nutrient_rate >= 90.0:
        print("✅ 栄養データ構造は良好です")
        print(f"   Serving Size構造: {serving_size_found/total*100:.1f}%")
        print(f"   最低栄養素発見率: {min_nutrient_rate:.1f}%")
    else:
        print("⚠️  一部のデータで問題があります:")
        if serving_size_found < total * 0.9:
            print(f"   Serving Size構造不足: {serving_size_found/total*100:.1f}%")
        if min_nutrient_rate < 90.0:
            print(f"   栄養素データ不足: 最低{min_nutrient_rate:.1f}%")


if __name__ == "__main__":
    main()
