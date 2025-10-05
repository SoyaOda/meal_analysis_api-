#!/usr/bin/env python3
"""
シンプルな100g栄養素計算システム
serving_options.servings[0]とnutrition_factsから直接計算
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def calculate_100g_nutrition_simple(food_data: Dict) -> Optional[Dict]:
    """serving_optionsとnutrition_factsから100g栄養素を計算（シンプル版）"""

    # serving_options.servings[0]を取得
    servings = food_data.get("comprehensive_data", {}).get("serving_options", {}).get("servings", [])
    if not servings:
        return None

    base_serving = servings[0]
    grams = base_serving.get("grams_per_unit", 0)
    if grams == 0:
        return None

    # nutrition_factsから主要4栄養素を取得
    nutrition_facts = food_data.get("comprehensive_data", {}).get("nutrition_facts", {})

    def get_nutrient_value(name: str) -> float:
        nutrient = nutrition_facts.get(name, {})
        return float(nutrient.get("value", 0))

    calories = get_nutrient_value("Calories")
    protein = get_nutrient_value("Protein")
    fat = get_nutrient_value("Total Fat")
    carbs = get_nutrient_value("Total Carbs")

    # 100g換算
    factor = 100 / grams

    return {
        "calories": calories * factor,
        "protein": protein * factor,
        "fat": fat * factor,
        "carbs": carbs * factor,
        "source_serving": base_serving.get("unit", ""),
        "source_grams": grams
    }


def check_nutrition_match_strict(stemmed_nutrition: Dict, calculated_nutrition: Dict) -> Dict:
    """栄養情報の厳密マッチ（全て0.2%以内）"""

    def calc_diff_pct(stemmed_val: float, calc_val: float) -> float:
        """差分パーセンテージを計算"""
        if stemmed_val == 0 and calc_val == 0:
            return 0.0
        if stemmed_val == 0:
            return 100.0
        return abs(stemmed_val - calc_val) / stemmed_val * 100

    cal_diff_pct = calc_diff_pct(stemmed_nutrition['calories'], calculated_nutrition['calories'])
    protein_diff_pct = calc_diff_pct(stemmed_nutrition['protein'], calculated_nutrition['protein'])
    fat_diff_pct = calc_diff_pct(stemmed_nutrition['fat'], calculated_nutrition['fat'])
    carbs_diff_pct = calc_diff_pct(stemmed_nutrition['carbs'], calculated_nutrition['carbs'])

    # 全て0.2%以内かチェック
    all_match = (cal_diff_pct <= 0.2 and
                 protein_diff_pct <= 0.2 and
                 fat_diff_pct <= 0.2 and
                 carbs_diff_pct <= 0.2)

    return {
        'match': all_match,
        'calories_diff_pct': cal_diff_pct,
        'protein_diff_pct': protein_diff_pct,
        'fat_diff_pct': fat_diff_pct,
        'carbs_diff_pct': carbs_diff_pct
    }


def main():
    print("🔍 シンプル100g栄養素計算＆マッチングシステム")
    print("=" * 80)
    print("計算方式: serving_options.servings[0] + nutrition_facts")
    print("マッチング基準: カロリー・タンパク質・脂質・炭水化物 全て0.2%以内")
    print("=" * 80)

    # ファイル読み込み
    stemmed_file = Path('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json')

    # 処理済みデータを使用（1,124食材）
    processed_file = Path('processed_data/processed_foods_20251003_135128.json')

    with open(stemmed_file, 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    with open(processed_file, 'r', encoding='utf-8') as f:
        processed_data = json.load(f)

    # foods配列を取得
    if isinstance(processed_data, dict) and 'foods' in processed_data:
        foods = processed_data['foods']
    elif isinstance(processed_data, list):
        foods = processed_data
    else:
        print("❌ エラー: 処理済みデータのフォーマットが不正です")
        return

    print(f"\n📋 Stemmed Database: {len(stemmed_data)}個")
    print(f"📋 処理済み食材: {len(foods)}個")

    # 100g栄養素を計算
    print(f"\n🔄 100g栄養素を計算中（シンプル方式）...")

    nutrition_list = []
    failed_count = 0

    for food in foods:
        nutrition_100g = calculate_100g_nutrition_simple(food)

        if nutrition_100g:
            nutrition_list.append({
                'food': food,
                'nutrition_100g': nutrition_100g
            })
        else:
            failed_count += 1

    print(f"✅ {len(nutrition_list)}個の食材で100g栄養素を計算完了")
    print(f"❌ 計算失敗: {failed_count}個")

    # マッチング実行
    print(f"\n🔍 Stemmed DBとの厳密マッチング実行中...")

    results = []

    for i, stemmed_food in enumerate(stemmed_data):
        if (i + 1) % 100 == 0:
            print(f"   進行状況: {i + 1}/{len(stemmed_data)}")

        stemmed_nutrition = stemmed_food['nutrition']
        candidates = []

        # 全ての処理済み食材と比較
        for item in nutrition_list:
            match_result = check_nutrition_match_strict(
                stemmed_nutrition,
                item['nutrition_100g']
            )

            if match_result['match']:
                candidates.append({
                    'final_food': item['food'],
                    'nutrition_100g': item['nutrition_100g'],
                    'diff': match_result
                })

        results.append({
            'stemmed_id': stemmed_food['id'],
            'stemmed_name': stemmed_food['original_name'],
            'stemmed_nutrition': stemmed_nutrition,
            'candidates_count': len(candidates),
            'candidates': candidates
        })

    print(f"\n✅ マッチング完了!")

    # 統計表示
    with_candidates = sum(1 for r in results if r['candidates_count'] > 0)
    without_candidates = sum(1 for r in results if r['candidates_count'] == 0)

    print(f"\n📊 マッチング結果:")
    print(f"   ✅ 候補あり: {with_candidates}個 ({with_candidates/len(stemmed_data)*100:.1f}%)")
    print(f"   ❌ 候補なし: {without_candidates}個 ({without_candidates/len(stemmed_data)*100:.1f}%)")

    # 候補数の分布
    from collections import Counter
    candidate_counts = [r['candidates_count'] for r in results]
    count_dist = Counter(candidate_counts)

    print(f"\n📈 候補数の分布:")
    for count in sorted(count_dist.keys()):
        print(f"   候補{count}個: {count_dist[count]}食材")

    # サンプル表示（0カロリー以外）
    non_zero_samples = [r for r in results if r['candidates_count'] > 0 and r['stemmed_nutrition']['calories'] > 0][:10]
    if non_zero_samples:
        print(f"\n✅ マッチ成功サンプル（0カロリー以外、最初の10個）:")
        for i, item in enumerate(non_zero_samples, 1):
            print(f"\n{i}. {item['stemmed_name']} ({item['candidates_count']}個の候補)")
            print(f"   Stemmed 100g: カロリー {item['stemmed_nutrition']['calories']:.1f}, "
                  f"タンパク質 {item['stemmed_nutrition']['protein']:.1f}g, "
                  f"脂質 {item['stemmed_nutrition']['fat']:.1f}g, "
                  f"炭水化物 {item['stemmed_nutrition']['carbs']:.1f}g")

            if item['candidates']:
                candidate = item['candidates'][0]
                print(f"   → 候補: {candidate['final_food']['food_name']}")
                print(f"      Final 100g: カロリー {candidate['nutrition_100g']['calories']:.1f}, "
                      f"タンパク質 {candidate['nutrition_100g']['protein']:.1f}g, "
                      f"脂質 {candidate['nutrition_100g']['fat']:.1f}g, "
                      f"炭水化物 {candidate['nutrition_100g']['carbs']:.1f}g")
                print(f"      差分: カロリー {candidate['diff']['calories_diff_pct']:.3f}%, "
                      f"タンパク質 {candidate['diff']['protein_diff_pct']:.3f}%, "
                      f"脂質 {candidate['diff']['fat_diff_pct']:.3f}%, "
                      f"炭水化物 {candidate['diff']['carbs_diff_pct']:.3f}%")

    # 結果保存
    output_file = 'processed_data/simple_nutrition_match_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_stemmed': len(stemmed_data),
                'total_processed_foods': len(foods),
                'calculated_100g_count': len(nutrition_list),
                'with_candidates': with_candidates,
                'without_candidates': without_candidates,
                'match_rate': with_candidates / len(stemmed_data) * 100,
                'candidate_distribution': dict(count_dist)
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n" + "=" * 80)
    print(f"💾 結果保存: {output_file}")
    print(f"\n📈 マッチング成功率: {with_candidates}/{len(stemmed_data)} ({with_candidates/len(stemmed_data)*100:.1f}%)")
    print(f"   新規追加が必要: {without_candidates}個")


if __name__ == "__main__":
    main()
