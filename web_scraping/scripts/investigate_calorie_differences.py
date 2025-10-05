#!/usr/bin/env python3
"""
20%超過の栄養値差分の原因を詳細調査
"""

import json
from pathlib import Path


def main():
    print("🔍 20%超過の栄養値差分 - 原因調査")
    print("=" * 80)

    # Complete版（Final JSON）
    with open('processed_data/all_foods_final_1125_complete.json', 'r', encoding='utf-8') as f:
        complete_data = json.load(f)

    # Stemmed DB
    with open('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json', 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    # Complete 1to1 mappings
    with open('processed_data/complete_1to1_mappings.json', 'r', encoding='utf-8') as f:
        mappings_data = json.load(f)

    # Dict化
    complete_by_id = {f['food_id']: f for f in complete_data['foods']}
    complete_by_name = {}
    for f in complete_data['foods']:
        name_normalized = f['food_name'].replace(',', '').lower().strip()
        complete_by_name[name_normalized] = f

    stemmed_dict = {str(s['id']): s for s in stemmed_data}

    # 20%超過のサンプルを収集
    over_20pct_details = []

    for mapping in mappings_data['mappings']:
        stemmed_id = mapping['stemmed_id']
        final_food_id = mapping.get('final_food_id')
        final_name = mapping['final_food_name']

        # Stemmed DBのカロリー（100g）
        stemmed_food = stemmed_dict.get(stemmed_id)
        if not stemmed_food:
            continue

        stemmed_cal_100g = stemmed_food['nutrition']['calories']

        # Final JSONを取得
        final_food = None
        if final_food_id:
            final_food = complete_by_id.get(final_food_id)
        if not final_food:
            final_name_normalized = final_name.replace(',', '').lower().strip()
            final_food = complete_by_name.get(final_name_normalized)

        if not final_food:
            continue

        # 100g計算
        essential = final_food['essential_nutrition']
        final_cal = essential['calories']['value']
        final_grams = essential['serving_size']['grams']

        if final_grams <= 0:
            continue

        final_cal_100g = (final_cal / final_grams) * 100

        # 差分パーセンテージ
        if stemmed_cal_100g == 0:
            continue

        diff_pct = abs(stemmed_cal_100g - final_cal_100g) / stemmed_cal_100g * 100

        if diff_pct > 20.0:
            # 詳細情報を収集
            over_20pct_details.append({
                'stemmed_name': mapping['stemmed_name'],
                'final_name': final_name,
                'stemmed_cal_100g': stemmed_cal_100g,
                'final_cal_100g': final_cal_100g,
                'diff_pct': diff_pct,
                # Stemmed詳細
                'stemmed_serving_info': stemmed_food.get('serving_info', 'N/A'),
                # Final詳細
                'final_calories': final_cal,
                'final_serving_size': essential['serving_size'],
                'final_data_source': final_food.get('data_source', 'N/A'),
                # 計算式
                'calculation': f"({final_cal} / {final_grams}) * 100 = {final_cal_100g:.1f}"
            })

    # 差分が大きい順にソート
    over_20pct_details.sort(key=lambda x: x['diff_pct'], reverse=True)

    print(f"20%超過の食材数: {len(over_20pct_details)}個\n")
    print("=" * 80)

    # 上位20個を詳細表示
    for i, item in enumerate(over_20pct_details[:20], 1):
        print(f"\n{i}. {item['stemmed_name']}")
        print(f"   Final name: {item['final_name']}")
        print(f"   Data source: {item['final_data_source']}")
        print()
        print(f"   📊 カロリー比較 (100g):")
        print(f"      Stemmed DB: {item['stemmed_cal_100g']:.1f} kcal/100g")
        print(f"      Final JSON: {item['final_cal_100g']:.1f} kcal/100g")
        print(f"      差分: {item['diff_pct']:.1f}%")
        print()
        print(f"   📝 Stemmed Serving Info:")
        print(f"      {item['stemmed_serving_info']}")
        print()
        print(f"   📝 Final Serving Size:")
        print(f"      Unit: {item['final_serving_size'].get('unit', 'N/A')}")
        print(f"      Grams: {item['final_serving_size'].get('grams', 'N/A')}g")
        print(f"      Calories: {item['final_calories']} kcal")
        print(f"      計算: {item['calculation']}")
        print()

        # 原因推定
        reasons = []

        # Serving size単位の違い
        stemmed_serving = str(item['stemmed_serving_info']).lower()
        final_unit = str(item['final_serving_size'].get('unit', '')).lower()

        if 'tbsp' in final_unit or 'tablespoon' in final_unit:
            if 'cup' in stemmed_serving:
                reasons.append("❓ Serving単位の違い: Stemmed=cup, Final=tablespoon")

        if 'gram' in final_unit and item['final_serving_size'].get('grams', 0) == 1:
            reasons.append("⚠️  Final serving_sizeがgram=1の可能性（不正確）")

        # カロリー値の極端な違い
        if item['final_cal_100g'] < item['stemmed_cal_100g'] * 0.5:
            reasons.append("⚠️  Final値が極端に低い（serving_size過大の可能性）")
        elif item['final_cal_100g'] > item['stemmed_cal_100g'] * 2:
            reasons.append("⚠️  Final値が極端に高い（serving_size過小の可能性）")

        # Data sourceチェック
        if item['final_data_source'] == 'manual':
            reasons.append("ℹ️  Manual由来データ")

        if reasons:
            print(f"   🔍 推定原因:")
            for reason in reasons:
                print(f"      {reason}")
        print()
        print("-" * 80)

    # 結果保存
    output_data = {
        'total_over_20pct': len(over_20pct_details),
        'details': over_20pct_details
    }

    output_file = Path('processed_data/calorie_diff_over_20pct_analysis.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, ensure_ascii=False, indent=2, fp=f)

    print(f"\n💾 詳細結果保存: {output_file}")


if __name__ == "__main__":
    main()
