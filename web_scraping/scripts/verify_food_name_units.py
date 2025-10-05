#!/usr/bin/env python3
"""
全食材のfood_nameから単位を抽出し、serving_optionsに含まれているか確認
"""

import json
import re
from pathlib import Path


def extract_unit_from_food_name(food_name):
    """食材名から単位を抽出

    例: "Arrowroot flour, cup 457cals" → "cup"
        "Baking powder, tsp 2cals" → "tsp"
    """
    # パターン: "単位名 数値cals" の形式
    # 一般的な単位リスト
    common_units = [
        'cup', 'cups',
        'tablespoon', 'tablespoons', 'tbsp', 'tbs',
        'teaspoon', 'teaspoons', 'tsp',
        'oz', 'ounce', 'ounces',
        'fl oz', 'fluid ounce',
        'gram', 'grams', 'g',
        'lb', 'lbs', 'pound', 'pounds',
        'ml', 'milliliter',
        'serving', 'servings',
        'piece', 'pieces',
        'slice', 'slices',
        'can', 'cans',
        'block',
        'fillet',
        'breast',
        'cracker', 'crackers',
        'cake',
        'packet',
        'bottle',
        'container',
        'portion'
    ]

    # カンマで分割して後半部分を見る
    parts = food_name.split(',')
    if len(parts) < 2:
        return None

    # 最後の部分（単位とカロリーを含む）
    last_part = parts[-1].strip().lower()

    # "cup 457cals" のような形式から単位を抽出
    # 数値付きのパターン（例: "0.5 cup 55cals"）
    match = re.match(r'^(\d+(?:\.\d+)?)\s+([\w\s]+?)\s+\d+cals?', last_part)
    if match:
        quantity = match.group(1)
        unit = match.group(2).strip()
        return f"{quantity} {unit}"

    # 通常のパターン（例: "cup 457cals"）
    match = re.match(r'^([\w\s]+?)\s+\d+cals?', last_part)
    if match:
        unit = match.group(1).strip()
        return unit

    return None


def normalize_unit(unit):
    """単位を正規化"""
    if not unit:
        return None

    unit_lower = unit.lower().strip()

    # 複数形を単数形に
    unit_lower = re.sub(r's$', '', unit_lower)

    # 略語の標準化
    unit_mapping = {
        'tbsp': 'tablespoon',
        'tbs': 'tablespoon',
        'tsp': 'teaspoon',
        'oz': 'oz',
        'fl oz': 'fl oz',
        'g': 'gram',
        'lb': 'lb',
        'lbs': 'lb',
        'ml': 'ml'
    }

    return unit_mapping.get(unit_lower, unit_lower)


def main():
    print("🔍 食材名の単位とserving_options対応確認")
    print("=" * 80)

    # Complete版を読み込み
    with open('processed_data/all_foods_final_1125_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_foods = len(data['foods'])
    unit_extracted = 0
    unit_not_extracted = 0
    unit_found_in_servings = 0
    unit_not_found_in_servings = 0

    no_unit_samples = []
    not_found_samples = []

    for food in data['foods']:
        food_id = food['food_id']
        food_name = food['food_name']

        # 単位を抽出
        unit = extract_unit_from_food_name(food_name)

        if unit:
            unit_extracted += 1
            unit_normalized = normalize_unit(unit)

            # serving_optionsに含まれているか確認
            servings = food.get('serving_options', {}).get('servings', [])

            # serving unitと照合
            found = False
            for serving in servings:
                serving_unit = serving.get('unit', '').lower().strip()

                # 完全一致または部分一致
                if unit_normalized and unit_normalized in serving_unit:
                    found = True
                    break
                elif unit.lower() in serving_unit:
                    found = True
                    break

            if found:
                unit_found_in_servings += 1
            else:
                unit_not_found_in_servings += 1
                if len(not_found_samples) < 10:
                    not_found_samples.append({
                        'food_id': food_id,
                        'food_name': food_name,
                        'extracted_unit': unit,
                        'available_units': [s.get('unit', 'N/A') for s in servings[:5]]
                    })
        else:
            unit_not_extracted += 1
            if len(no_unit_samples) < 10:
                no_unit_samples.append({
                    'food_id': food_id,
                    'food_name': food_name
                })

    print(f"📊 検証結果:")
    print(f"   総食材数: {total_foods}個")
    print()
    print(f"単位抽出:")
    print(f"   ✅ 抽出成功: {unit_extracted}個 ({unit_extracted/total_foods*100:.1f}%)")
    print(f"   ❌ 抽出失敗: {unit_not_extracted}個 ({unit_not_extracted/total_foods*100:.1f}%)")
    print()
    print(f"Serving options対応:")
    print(f"   ✅ 単位一致: {unit_found_in_servings}個 ({unit_found_in_servings/unit_extracted*100:.1f}%)")
    print(f"   ❌ 単位不一致: {unit_not_found_in_servings}個 ({unit_not_found_in_servings/unit_extracted*100:.1f}%)")
    print()

    if no_unit_samples:
        print(f"❌ 単位抽出失敗サンプル（最初の10個）:")
        for i, item in enumerate(no_unit_samples, 1):
            print(f"   {i}. {item['food_id']}: {item['food_name']}")
        print()

    if not_found_samples:
        print(f"⚠️  Serving options不一致サンプル（最初の10個）:")
        for i, item in enumerate(not_found_samples, 1):
            print(f"   {i}. {item['food_id']}: {item['food_name']}")
            print(f"      抽出単位: {item['extracted_unit']}")
            print(f"      利用可能単位: {', '.join(item['available_units'])}")
            print()

    # 結果保存
    result = {
        'total_foods': total_foods,
        'unit_extracted': unit_extracted,
        'unit_not_extracted': unit_not_extracted,
        'unit_found_in_servings': unit_found_in_servings,
        'unit_not_found_in_servings': unit_not_found_in_servings,
        'no_unit_samples': no_unit_samples,
        'not_found_samples': not_found_samples
    }

    output_file = Path('processed_data/food_name_unit_verification.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 結果保存: {output_file}")


if __name__ == "__main__":
    main()
