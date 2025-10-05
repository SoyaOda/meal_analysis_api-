#!/usr/bin/env python3
"""
1,126個の対応ペアについて100gカロリーの差が5%以内か検証
"""

import json
import re
from typing import Dict, Optional, Tuple


def extract_unit_and_grams(food_name: str) -> Optional[Tuple[str, float]]:
    """food_nameから単位とグラム数を推定"""

    # 一般的な単位とそのグラム換算
    unit_to_grams = {
        'cup': 240,  # 一般的な液体1カップ
        'tbsp': 15,
        'tablespoon': 15,
        'tsp': 5,
        'teaspoon': 5,
        'oz': 28.35,
        'fl oz': 30,
        'gram': 1,
        'g': 1,
        'ml': 1,
        'lb': 453.6,
        'piece': 50,  # 推定
        'serving': 100,  # 推定
        'can': 240,  # 推定
    }

    # パターン: "unit (size) Xcals" または "unit Xcals"
    # 例: "cup (8 fl oz) 7cals", "cup 240cals"

    food_lower = food_name.lower()

    # 単位を探す
    for unit, grams in unit_to_grams.items():
        if unit in food_lower:
            # 単位の後にサイズ指定があるか確認
            # 例: "cup (8 fl oz)" → 8 fl oz = 240ml
            size_match = re.search(rf'{unit}\s*\(([^)]+)\)', food_lower)
            if size_match:
                size_str = size_match.group(1)
                # サイズから数値を抽出
                num_match = re.search(r'(\d+(?:\.\d+)?)', size_str)
                if num_match:
                    size_num = float(num_match.group(1))
                    # サイズ内の単位を確認
                    if 'oz' in size_str or 'fl oz' in size_str:
                        return (unit, size_num * 28.35)
                    elif 'g' in size_str:
                        return (unit, size_num)
                    elif 'ml' in size_str:
                        return (unit, size_num)

            # サイズ指定がない場合はデフォルト値
            return (unit, grams)

    return None


def calculate_100g_calories_from_final(food_data: Dict) -> Optional[float]:
    """Final JSONから100gカロリーを計算（3つのパターンに対応）"""

    essential = food_data.get("essential_nutrition", {})
    if not essential:
        return None

    calories_dict = essential.get("calories", {})
    calories = float(calories_dict.get("value", 0))

    # パターン1: serving_sizeがある場合（最優先）
    serving_size = essential.get("serving_size")

    if serving_size:
        grams = serving_size.get("grams", 0)
        if grams > 0:
            # 100g換算
            calories_100g = (calories / grams) * 100
            return calories_100g

    # パターン2: food_nameから単位とグラムを推定
    food_name = food_data.get("food_name", "")
    unit_info = extract_unit_and_grams(food_name)

    if unit_info:
        unit, grams = unit_info
        if grams > 0:
            # 100g換算
            calories_100g = (calories / grams) * 100
            return calories_100g

    # パターン3: どうしても無理な場合はNone
    return None


def main():
    print("🔍 1,126ペアのカロリー差分検証（5%基準）")
    print("=" * 80)

    # ファイル読み込み
    with open('processed_data/complete_1to1_mappings.json', 'r', encoding='utf-8') as f:
        mappings_data = json.load(f)

    with open('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json', 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    with open('processed_data/all_foods_final_1152.json', 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    final_foods = final_data['foods']

    # IDでインデックス作成（stemmed_idを文字列に統一）
    stemmed_dict = {str(s['id']): s for s in stemmed_data}
    final_dict = {f['food_id']: f for f in final_foods}

    print(f"📂 データ読み込み完了")
    print(f"   対応ペア: {len(mappings_data['mappings'])}個")
    print(f"   Stemmed DB: {len(stemmed_data)}個")
    print(f"   Final JSON: {len(final_foods)}個")
    print()

    # 検証
    within_5pct = 0
    over_5pct = 0
    calculation_failed = 0
    failed_samples = []
    over_5pct_samples = []

    for mapping in mappings_data['mappings']:
        stemmed_id = mapping['stemmed_id']
        final_id = mapping['final_food_id']

        # Stemmed DBのカロリー（100g）
        stemmed_food = stemmed_dict.get(stemmed_id)
        if not stemmed_food:
            calculation_failed += 1
            continue

        stemmed_cal_100g = stemmed_food['nutrition']['calories']

        # Final JSONのカロリー（100g）を計算
        final_food = final_dict.get(final_id)
        if not final_food:
            calculation_failed += 1
            continue

        final_cal_100g = calculate_100g_calories_from_final(final_food)

        if final_cal_100g is None:
            calculation_failed += 1
            failed_samples.append({
                'stemmed_name': mapping['stemmed_name'],
                'final_name': mapping['final_food_name']
            })
            continue

        # 差分パーセンテージを計算
        if stemmed_cal_100g == 0 and final_cal_100g == 0:
            diff_pct = 0.0
        elif stemmed_cal_100g == 0:
            diff_pct = 100.0
        else:
            diff_pct = abs(stemmed_cal_100g - final_cal_100g) / stemmed_cal_100g * 100

        if diff_pct <= 5.0:
            within_5pct += 1
        else:
            over_5pct += 1
            over_5pct_samples.append({
                'stemmed_name': mapping['stemmed_name'],
                'final_name': mapping['final_food_name'],
                'stemmed_cal': stemmed_cal_100g,
                'final_cal': final_cal_100g,
                'diff_pct': diff_pct
            })

    # 結果表示
    total_checked = within_5pct + over_5pct

    print(f"📊 検証結果:")
    print(f"   ✅ 5%以内: {within_5pct}個 ({within_5pct/total_checked*100:.1f}%)")
    print(f"   ❌ 5%超過: {over_5pct}個 ({over_5pct/total_checked*100:.1f}%)")
    print(f"   ⚠️  計算失敗: {calculation_failed}個")
    print()

    # 計算失敗サンプル
    if failed_samples:
        print(f"⚠️  計算失敗サンプル（最初の10個）:")
        for i, item in enumerate(failed_samples[:10], 1):
            print(f"   {i}. {item['stemmed_name']} → {item['final_name']}")
        print()

    # 5%超過サンプル
    if over_5pct_samples:
        print(f"❌ 5%超過サンプル（最初の20個、差分が大きい順）:")
        over_5pct_samples.sort(key=lambda x: x['diff_pct'], reverse=True)
        for i, item in enumerate(over_5pct_samples[:20], 1):
            print(f"   {i}. {item['stemmed_name']}")
            print(f"      Stemmed 100g: {item['stemmed_cal']:.1f} kcal")
            print(f"      Final 100g: {item['final_cal']:.1f} kcal")
            print(f"      差分: {item['diff_pct']:.1f}%")
            print()

    # 結果保存
    result_output = {
        'total_checked': total_checked,
        'within_5pct': within_5pct,
        'over_5pct': over_5pct,
        'calculation_failed': calculation_failed,
        'within_5pct_rate': within_5pct / total_checked * 100 if total_checked > 0 else 0,
        'over_5pct_details': over_5pct_samples
    }

    with open('processed_data/calorie_diff_verification.json', 'w', encoding='utf-8') as f:
        json.dump(result_output, f, ensure_ascii=False, indent=2)

    print(f"=" * 80)
    print(f"💾 結果保存: processed_data/calorie_diff_verification.json")


if __name__ == "__main__":
    main()
