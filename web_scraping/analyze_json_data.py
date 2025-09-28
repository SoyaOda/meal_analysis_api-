#!/usr/bin/env python3
"""
JSONデータの問題を分析し、正しい単位別栄養情報を生成する
"""

import json

def analyze_json_data():
    """JSONデータを分析して問題を特定"""

    with open('web_scraping/data/top3_nutrition_20250926_130415.json', 'r') as f:
        data = json.load(f)

    print('現在のデータ構造の問題:')
    print('=' * 50)
    food = data['foods'][0]
    print(f'食材名: {food["name"]}')
    print(f'基本カロリー: {food["calories"]}cal')
    print(f'基本重量: {food["weight_g"]}g')
    print()
    print('現在の単位別データ（問題のあるデータ）:')
    for unit, info in food['units'].items():
        print(f'  {unit}: {info["calories"]}cal / {info["weight_g"]}g')

    print()
    print('❌ 問題:')
    print('- カロリーと重量が各単位で同じ値になってしまっている')
    print('- 実際には単位ごとに重量とカロリーの比例関係が必要')
    print()

    # 正しいデータを生成
    print('✅ 期待される正しいデータ:')
    print('（デバッグ情報から得られた正しい値）')

    # 基準値（1 cupあたり）
    base_calories = 239  # 1 cup = 239cal
    base_weight = 254    # 1 cup = 254g

    correct_units = {
        'cup': {'calories': 239, 'weight_g': 254.0},
        'gram': {'calories': round(239/254, 2), 'weight_g': 1.0},
        'tablespoon': {'calories': 15, 'weight_g': 15.9},
        'oz': {'calories': 27, 'weight_g': 28.3},
        'ml': {'calories': 1, 'weight_g': 1.1},
        'teaspoon': {'calories': 5, 'weight_g': 5.3},
        'fl oz': {'calories': 30, 'weight_g': 31.8},
        'lb': {'calories': 426, 'weight_g': 453.6}
    }

    print()
    for unit, info in correct_units.items():
        print(f'  {unit}: {info["calories"]}cal / {info["weight_g"]}g')

    # 正しいデータで更新
    food['units'] = correct_units
    food['weight_g'] = 254  # 正しい重量に修正

    # 更新されたデータを保存
    output_file = 'web_scraping/data/corrected_nutrition_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print()
    print(f'✅ 修正されたデータを保存: {output_file}')

    print()
    print('📊 各単位の意味:')
    print('  cup: 1カップあたりの栄養値')
    print('  gram: 1グラムあたりの栄養値')
    print('  tablespoon: 大さじ1あたりの栄養値')
    print('  oz: 1オンスあたりの栄養値')
    print('  ml: 1ミリリットルあたりの栄養値')
    print('  teaspoon: 小さじ1あたりの栄養値')
    print('  fl oz: 1液量オンスあたりの栄養値')
    print('  lb: 1ポンドあたりの栄養値')

    return correct_units

if __name__ == "__main__":
    analyze_json_data()