#!/usr/bin/env python3
"""
Stemmed DB全食材に対してFinal JSONから類似栄養素の候補を全て取得
simple_100g_calculator.pyのロジックを使用
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def calculate_100g_nutrition_simple(food_data: Dict) -> Optional[Dict]:
    """essential_nutritionから100g栄養素を計算（all_foods_final_1152.json用）"""

    essential = food_data.get("essential_nutrition", {})
    if not essential:
        return None

    # serving_sizeからgramsを取得
    serving_size = essential.get("serving_size", {})

    if serving_size:
        grams = serving_size.get("grams", 0)
    else:
        # serving_sizeがない場合はservings[0]から取得
        servings = food_data.get("serving_options", {}).get("servings", [])
        if servings:
            grams = servings[0].get("grams_per_unit", 0)
        else:
            return None

    if grams == 0:
        return None

    # カロリー
    calories_dict = essential.get("calories", {})
    calories = float(calories_dict.get("value", 0))

    # マクロ栄養素
    macros = essential.get("macros", {})
    protein = float(macros.get("protein", {}).get("value", 0))
    fat = float(macros.get("total_fat", {}).get("value", 0))
    carbs = float(macros.get("total_carbs", {}).get("value", 0))

    # 100g換算
    factor = 100 / grams

    return {
        "calories": calories * factor,
        "protein": protein * factor,
        "fat": fat * factor,
        "carbs": carbs * factor,
        "source_serving": serving_size.get("unit", "") if serving_size else "",
        "source_grams": grams
    }


def calculate_nutrition_similarity(stemmed: Dict, final: Dict) -> Dict:
    """栄養素の類似度を計算（差分パーセンテージ）"""

    def calc_diff_pct(stemmed_val: float, final_val: float) -> float:
        """差分パーセンテージを計算"""
        if stemmed_val == 0 and final_val == 0:
            return 0.0
        if stemmed_val == 0:
            return 100.0
        return abs(stemmed_val - final_val) / stemmed_val * 100

    cal_diff = calc_diff_pct(stemmed['calories'], final['calories'])
    protein_diff = calc_diff_pct(stemmed['protein'], final['protein'])
    fat_diff = calc_diff_pct(stemmed['fat'], final['fat'])
    carbs_diff = calc_diff_pct(stemmed['carbs'], final['carbs'])

    # 平均差分
    avg_diff = (cal_diff + protein_diff + fat_diff + carbs_diff) / 4

    return {
        'calories_diff_pct': cal_diff,
        'protein_diff_pct': protein_diff,
        'fat_diff_pct': fat_diff,
        'carbs_diff_pct': carbs_diff,
        'average_diff_pct': avg_diff,
        'is_exact_match': (cal_diff <= 2.0 and protein_diff <= 2.0 and
                          fat_diff <= 2.0 and carbs_diff <= 2.0)
    }


def main():
    print("🔍 Stemmed DB → Final JSON 全候補マッチングシステム")
    print("=" * 80)
    print("対象: Stemmed DB全1,142食材")
    print("候補: Final JSON 1,152食材から類似栄養素を全て抽出")
    print("計算方式: essential_nutrition (serving_size.grams基準)")
    print("マッチング基準: カロリー・タンパク質・脂質・炭水化物 全て2.0%以内")
    print("=" * 80)

    # ファイル読み込み
    stemmed_file = Path('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json')
    # all_foods_final_1152.jsonを使用（全1,152食材で100g計算可能）
    final_file = Path('processed_data/all_foods_final_1152.json')

    print(f"\n📂 ファイル読み込み中...")
    with open(stemmed_file, 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    with open(final_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    # Final JSONのフォーマット確認
    if isinstance(final_data, dict) and 'foods' in final_data:
        final_foods = final_data['foods']
    elif isinstance(final_data, list):
        final_foods = final_data
    else:
        print("❌ エラー: Final JSONのフォーマットが不正です")
        return

    print(f"✅ Stemmed DB: {len(stemmed_data)}個")
    print(f"✅ Final JSON: {len(final_foods)}個")

    # Final食材の100g栄養素を事前計算
    print(f"\n🔄 Final食材の100g栄養素を計算中...")

    final_nutrition_list = []
    failed_count = 0

    for final_food in final_foods:
        nutrition_100g = calculate_100g_nutrition_simple(final_food)

        if nutrition_100g:
            final_nutrition_list.append({
                'food': final_food,
                'nutrition_100g': nutrition_100g
            })
        else:
            failed_count += 1

    print(f"✅ {len(final_nutrition_list)}個の食材で100g栄養素を計算完了")
    if failed_count > 0:
        print(f"❌ 計算失敗: {failed_count}個")

    # 各Stemmed食材に対して全候補を抽出
    print(f"\n🔍 類似栄養素候補を抽出中...")

    results = []

    for i, stemmed_food in enumerate(stemmed_data):
        if (i + 1) % 100 == 0:
            print(f"   進行状況: {i + 1}/{len(stemmed_data)}")

        stemmed_nutrition = stemmed_food['nutrition']
        candidates = []

        # 全てのFinal食材と比較
        for final_item in final_nutrition_list:
            similarity = calculate_nutrition_similarity(
                stemmed_nutrition,
                final_item['nutrition_100g']
            )

            candidates.append({
                'final_food_name': final_item['food']['food_name'],
                'final_nutrition_100g': final_item['nutrition_100g'],
                'similarity': similarity
            })

        # 類似度でソート（差分が小さい順）
        candidates.sort(key=lambda x: x['similarity']['average_diff_pct'])

        results.append({
            'stemmed_id': stemmed_food['id'],
            'stemmed_name': stemmed_food['original_name'],
            'stemmed_nutrition': stemmed_nutrition,
            'total_candidates': len(candidates),
            'exact_matches': sum(1 for c in candidates if c['similarity']['is_exact_match']),
            'all_candidates': candidates  # 全候補を含む（類似度順）
        })

    print(f"\n✅ 候補抽出完了!")

    # 統計表示
    total_exact_matches = sum(r['exact_matches'] for r in results)
    stemmed_with_exact_match = sum(1 for r in results if r['exact_matches'] > 0)
    stemmed_without_exact_match = len(results) - stemmed_with_exact_match

    print(f"\n📊 マッチング統計:")
    print(f"   Stemmed食材総数: {len(stemmed_data)}個")
    print(f"   Final候補総数: {len(final_nutrition_list)}個")
    print(f"\n   ✅ 厳密マッチあり: {stemmed_with_exact_match}個 ({stemmed_with_exact_match/len(stemmed_data)*100:.1f}%)")
    print(f"   ❌ 厳密マッチなし: {stemmed_without_exact_match}個 ({stemmed_without_exact_match/len(stemmed_data)*100:.1f}%)")
    print(f"   📈 総厳密マッチ数: {total_exact_matches}個")

    # サンプル表示（厳密マッチあり、0カロリー以外）
    exact_match_samples = [r for r in results
                           if r['exact_matches'] > 0
                           and r['stemmed_nutrition']['calories'] > 0][:5]

    if exact_match_samples:
        print(f"\n✅ 厳密マッチサンプル（0カロリー以外、最初の5個）:")
        for i, item in enumerate(exact_match_samples, 1):
            print(f"\n{i}. {item['stemmed_name']}")
            print(f"   Stemmed 100g: カロリー {item['stemmed_nutrition']['calories']:.1f}, "
                  f"タンパク質 {item['stemmed_nutrition']['protein']:.1f}g, "
                  f"脂質 {item['stemmed_nutrition']['fat']:.1f}g, "
                  f"炭水化物 {item['stemmed_nutrition']['carbs']:.1f}g")
            print(f"   厳密マッチ数: {item['exact_matches']}個")

            # 最も類似度が高い候補（厳密マッチ）を表示
            exact_candidate = next((c for c in item['all_candidates'] if c['similarity']['is_exact_match']), None)
            if exact_candidate:
                print(f"   → 候補: {exact_candidate['final_food_name']}")
                print(f"      Final 100g: カロリー {exact_candidate['final_nutrition_100g']['calories']:.1f}, "
                      f"タンパク質 {exact_candidate['final_nutrition_100g']['protein']:.1f}g, "
                      f"脂質 {exact_candidate['final_nutrition_100g']['fat']:.1f}g, "
                      f"炭水化物 {exact_candidate['final_nutrition_100g']['carbs']:.1f}g")
                print(f"      平均差分: {exact_candidate['similarity']['average_diff_pct']:.3f}%")

    # サンプル表示（厳密マッチなし、最も近い候補）
    no_exact_match_samples = [r for r in results
                              if r['exact_matches'] == 0
                              and r['stemmed_nutrition']['calories'] > 0][:5]

    if no_exact_match_samples:
        print(f"\n❌ 厳密マッチなしサンプル（最も近い候補、最初の5個）:")
        for i, item in enumerate(no_exact_match_samples, 1):
            print(f"\n{i}. {item['stemmed_name']}")
            print(f"   Stemmed 100g: カロリー {item['stemmed_nutrition']['calories']:.1f}, "
                  f"タンパク質 {item['stemmed_nutrition']['protein']:.1f}g, "
                  f"脂質 {item['stemmed_nutrition']['fat']:.1f}g, "
                  f"炭水化物 {item['stemmed_nutrition']['carbs']:.1f}g")

            # 最も類似度が高い候補（最初の候補）を表示
            if item['all_candidates']:
                closest = item['all_candidates'][0]
                print(f"   → 最も近い候補: {closest['final_food_name']}")
                print(f"      Final 100g: カロリー {closest['final_nutrition_100g']['calories']:.1f}, "
                      f"タンパク質 {closest['final_nutrition_100g']['protein']:.1f}g, "
                      f"脂質 {closest['final_nutrition_100g']['fat']:.1f}g, "
                      f"炭水化物 {closest['final_nutrition_100g']['carbs']:.1f}g")
                print(f"      平均差分: {closest['similarity']['average_diff_pct']:.1f}%")

    # 結果保存
    output_file = 'processed_data/stemmed_to_final_all_candidates_2pct.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_stemmed': len(stemmed_data),
                'total_final_foods': len(final_foods),
                'final_calculated_count': len(final_nutrition_list),
                'stemmed_with_exact_match': stemmed_with_exact_match,
                'stemmed_without_exact_match': stemmed_without_exact_match,
                'exact_match_rate': stemmed_with_exact_match / len(stemmed_data) * 100,
                'total_exact_matches': total_exact_matches
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n" + "=" * 80)
    print(f"💾 結果保存: {output_file}")
    print(f"\n📈 厳密マッチ成功率: {stemmed_with_exact_match}/{len(stemmed_data)} ({stemmed_with_exact_match/len(stemmed_data)*100:.1f}%)")
    print(f"   新規追加が必要: {stemmed_without_exact_match}個")
    print(f"\n💡 各Stemmed食材に対して全Final候補が類似度順に保存されています")


if __name__ == "__main__":
    main()
