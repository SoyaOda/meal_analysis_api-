#!/usr/bin/env python3
"""
essential_nutrition.serving_sizeを使って正しく100g栄養素を計算
基準: カロリー・タンパク質・脂質・炭水化物 全て0.2%以内
"""

import json
from pathlib import Path
from typing import Dict, Optional


def calculate_100g_from_essential(essential_nutrition: Dict) -> Optional[Dict]:
    """essential_nutritionから100gあたりの栄養素を計算"""

    if 'serving_size' not in essential_nutrition or not essential_nutrition['serving_size']:
        return None

    serving_size = essential_nutrition['serving_size']
    grams = serving_size.get('grams', 0)

    if grams == 0:
        return None

    # カロリー
    calories = serving_size.get('calories', 0)
    cal_per_100g = (calories / grams) * 100

    # マクロ栄養素
    macros = essential_nutrition.get('macros', {})

    def get_macro_value(macro_dict):
        if macro_dict and isinstance(macro_dict, dict):
            return float(macro_dict.get('value', 0))
        return 0.0

    protein_per_serving = get_macro_value(macros.get('protein'))
    fat_per_serving = get_macro_value(macros.get('total_fat'))
    carbs_per_serving = get_macro_value(macros.get('total_carbs'))

    # 100g換算
    factor = 100 / grams

    return {
        'calories': cal_per_100g,
        'protein': protein_per_serving * factor,
        'fat': fat_per_serving * factor,
        'carbs': carbs_per_serving * factor,
        'source_serving': serving_size.get('raw_text', '')
    }


def check_nutrition_match_strict(stemmed_nutrition: Dict, final_nutrition: Dict) -> Dict:
    """栄養情報の厳密マッチ（全て0.2%以内）"""

    def calc_diff_pct(stemmed_val: float, final_val: float) -> float:
        """差分パーセンテージを計算"""
        if stemmed_val == 0 and final_val == 0:
            return 0.0
        if stemmed_val == 0:
            return 100.0
        return abs(stemmed_val - final_val) / stemmed_val * 100

    cal_diff_pct = calc_diff_pct(stemmed_nutrition['calories'], final_nutrition['calories'])
    protein_diff_pct = calc_diff_pct(stemmed_nutrition['protein'], final_nutrition['protein'])
    fat_diff_pct = calc_diff_pct(stemmed_nutrition['fat'], final_nutrition['fat'])
    carbs_diff_pct = calc_diff_pct(stemmed_nutrition['carbs'], final_nutrition['carbs'])

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
    print("🔍 栄養情報厳密マッチングシステム（修正版）")
    print("=" * 80)
    print("基準: カロリー・タンパク質・脂質・炭水化物 全て0.2%以内")
    print("計算: essential_nutrition.serving_size を使用")
    print("=" * 80)

    # ファイル読み込み
    stemmed_file = Path('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json')
    final_file = Path('processed_data/processed_foods_20251003_135128.json')

    with open(stemmed_file, 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    with open(final_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    # フォーマット対応（'foods'キーがあればそれを、なければリスト全体を使用）
    if isinstance(final_data, dict) and 'foods' in final_data:
        final_foods = final_data['foods']
    elif isinstance(final_data, list):
        final_foods = final_data
    else:
        final_foods = []

    print(f"\n📋 Stemmed Database: {len(stemmed_data)}個")
    print(f"📋 Final JSON: {len(final_foods)}個")

    # Final食材の100g栄養情報を事前計算
    print(f"\n🔄 Final食材の100g栄養情報を計算中（essential_nutrition使用）...")
    final_nutrition_list = []

    for final_food in final_foods:
        nutrition_100g = calculate_100g_from_essential(
            final_food.get('essential_nutrition', {})
        )

        if nutrition_100g:
            final_nutrition_list.append({
                'food': final_food,
                'nutrition_100g': nutrition_100g
            })

    print(f"✅ {len(final_nutrition_list)}個の食材で100g栄養情報を計算完了")

    # マッチング実行
    print(f"\n🔍 厳密マッチング実行中...")

    results = []
    no_candidates_count = 0

    for i, stemmed_food in enumerate(stemmed_data):
        if (i + 1) % 100 == 0:
            print(f"   進行状況: {i + 1}/{len(stemmed_data)}")

        stemmed_nutrition = stemmed_food['nutrition']
        candidates = []

        # 全てのFinal食材と比較
        for final_item in final_nutrition_list:
            match_result = check_nutrition_match_strict(
                stemmed_nutrition,
                final_item['nutrition_100g']
            )

            if match_result['match']:
                candidates.append({
                    'final_food': final_item['food'],
                    'nutrition_100g': final_item['nutrition_100g'],
                    'diff': match_result
                })

        if len(candidates) == 0:
            no_candidates_count += 1

        results.append({
            'stemmed_id': stemmed_food['id'],
            'stemmed_name': stemmed_food['original_name'],
            'stemmed_nutrition': stemmed_nutrition,
            'candidates_count': len(candidates),
            'candidates': candidates
        })

    print(f"\n✅ 完了!")

    # 統計表示
    candidate_counts = [r['candidates_count'] for r in results]
    with_candidates = sum(1 for c in candidate_counts if c > 0)
    without_candidates = sum(1 for c in candidate_counts if c == 0)

    print(f"\n📊 マッチング結果:")
    print(f"   ✅ 候補あり: {with_candidates}個 ({with_candidates/len(stemmed_data)*100:.1f}%)")
    print(f"   ❌ 候補なし: {without_candidates}個 ({without_candidates/len(stemmed_data)*100:.1f}%)")

    # 候補数の分布
    print(f"\n📈 候補数の分布:")
    from collections import Counter
    count_dist = Counter(candidate_counts)
    for count in sorted(count_dist.keys()):
        print(f"   候補{count}個: {count_dist[count]}食材")

    # 候補なしサンプル表示
    if without_candidates > 0:
        print(f"\n❌ 候補なし食材サンプル（最初の10個）:")
        no_candidate_samples = [r for r in results if r['candidates_count'] == 0][:10]
        for i, item in enumerate(no_candidate_samples, 1):
            print(f"\n{i}. {item['stemmed_name']}")
            print(f"   100g栄養: カロリー {item['stemmed_nutrition']['calories']:.1f}, "
                  f"タンパク質 {item['stemmed_nutrition']['protein']:.1f}g, "
                  f"脂質 {item['stemmed_nutrition']['fat']:.1f}g, "
                  f"炭水化物 {item['stemmed_nutrition']['carbs']:.1f}g")

    # 候補ありサンプル表示（0カロリー以外）
    non_zero_samples = [r for r in results if r['candidates_count'] > 0 and r['stemmed_nutrition']['calories'] > 0][:10]
    if non_zero_samples:
        print(f"\n✅ 候補あり食材サンプル（0カロリー以外、最初の10個）:")
        for i, item in enumerate(non_zero_samples, 1):
            print(f"\n{i}. {item['stemmed_name']} ({item['candidates_count']}個の候補)")
            print(f"   Stemmed 100g: カロリー {item['stemmed_nutrition']['calories']:.1f}, "
                  f"タンパク質 {item['stemmed_nutrition']['protein']:.1f}g, "
                  f"脂質 {item['stemmed_nutrition']['fat']:.1f}g, "
                  f"炭水化物 {item['stemmed_nutrition']['carbs']:.1f}g")

            if item['candidates']:
                candidate = item['candidates'][0]
                print(f"\n   → 候補: {candidate['final_food']['food_name']}")
                print(f"      Final 100g: カロリー {candidate['nutrition_100g']['calories']:.1f}, "
                      f"タンパク質 {candidate['nutrition_100g']['protein']:.1f}g, "
                      f"脂質 {candidate['nutrition_100g']['fat']:.1f}g, "
                      f"炭水化物 {candidate['nutrition_100g']['carbs']:.1f}g")
                print(f"      差分: カロリー {candidate['diff']['calories_diff_pct']:.3f}%, "
                      f"タンパク質 {candidate['diff']['protein_diff_pct']:.3f}%, "
                      f"脂質 {candidate['diff']['fat_diff_pct']:.3f}%, "
                      f"炭水化物 {candidate['diff']['carbs_diff_pct']:.3f}%")

    # 結果保存
    output_file = 'processed_data/nutrition_match_candidates_corrected.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_stemmed': len(stemmed_data),
                'with_candidates': with_candidates,
                'without_candidates': without_candidates,
                'match_rate': with_candidates / len(stemmed_data) * 100,
                'candidate_distribution': dict(count_dist)
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n" + "=" * 80)
    print(f"💾 結果保存: {output_file}")
    print(f"\n📈 目標達成度: {with_candidates}/{len(stemmed_data)} ({with_candidates/len(stemmed_data)*100:.1f}%)")
    print(f"   新規追加が必要な食材: {without_candidates}個")


if __name__ == "__main__":
    main()
