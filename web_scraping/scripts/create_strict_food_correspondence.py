#!/usr/bin/env python3
"""
厳密な栄養情報マッチングで食材対応を作成
- 名前の部分一致 + カロリー・マクロ栄養素全て1%以内
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


def normalize_name(name: str) -> str:
    """名前を正規化"""
    normalized = name.lower().strip()
    normalized = re.sub(r'\s+\d+cals?$', '', normalized)
    normalized = normalized.replace('\n', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def extract_keywords(name: str) -> set:
    """重要なキーワードを抽出"""
    words = normalize_name(name).split()
    # ストップワード除外
    stop_words = {'with', 'without', 'or', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'by'}
    return {w for w in words if w not in stop_words and len(w) > 2}


def calculate_100g_nutrition(serving_options: List[Dict]) -> Optional[Dict]:
    """Serving情報から100gあたりの栄養素を計算"""
    if not serving_options:
        return None

    # gramsが最も大きいservingを使用（より正確）
    best_serving = max(serving_options, key=lambda s: s.get('grams_per_unit', 0))

    grams = best_serving.get('grams_per_unit', 0)
    if grams == 0:
        return None

    calories = best_serving.get('calories_per_unit', 0)

    # 100g換算
    cal_per_100g = (calories / grams) * 100

    # マクロ栄養素を計算（nutrition_factsから）
    return {
        'calories': cal_per_100g,
        'grams_per_unit': grams,
        'calories_per_unit': calories
    }


def extract_macros_from_nutrition_facts(nutrition_facts: Dict) -> Dict:
    """nutrition_factsからマクロ栄養素を抽出"""
    macros = {
        'protein': 0.0,
        'fat': 0.0,
        'carbs': 0.0
    }

    if 'nutrients' not in nutrition_facts:
        return macros

    for nutrient in nutrition_facts['nutrients']:
        key = nutrient.get('key', '').lower()
        value = nutrient.get('value', 0)

        if 'protein' in key:
            macros['protein'] = float(value)
        elif 'total_fat' in key or key == 'fat':
            macros['fat'] = float(value)
        elif 'total_carb' in key or key == 'carbs':
            macros['carbs'] = float(value)

    return macros


def convert_macros_to_100g(macros: Dict, grams_per_serving: float) -> Dict:
    """マクロ栄養素を100gあたりに換算"""
    if grams_per_serving == 0:
        return macros

    factor = 100 / grams_per_serving

    return {
        'protein': macros['protein'] * factor,
        'fat': macros['fat'] * factor,
        'carbs': macros['carbs'] * factor
    }


def check_nutrition_match(stemmed_nutrition: Dict, final_nutrition_100g: Dict, final_macros_100g: Dict) -> Dict:
    """栄養情報の一致をチェック（全て1%以内）"""

    # カロリー差
    cal_diff = abs(stemmed_nutrition['calories'] - final_nutrition_100g['calories'])
    cal_diff_pct = (cal_diff / stemmed_nutrition['calories'] * 100) if stemmed_nutrition['calories'] > 0 else 100

    # タンパク質差
    protein_diff = abs(stemmed_nutrition['protein'] - final_macros_100g['protein'])
    protein_diff_pct = (protein_diff / stemmed_nutrition['protein'] * 100) if stemmed_nutrition['protein'] > 0 else 0

    # 脂質差
    fat_diff = abs(stemmed_nutrition['fat'] - final_macros_100g['fat'])
    fat_diff_pct = (fat_diff / stemmed_nutrition['fat'] * 100) if stemmed_nutrition['fat'] > 0 else 0

    # 炭水化物差
    carbs_diff = abs(stemmed_nutrition['carbs'] - final_macros_100g['carbs'])
    carbs_diff_pct = (carbs_diff / stemmed_nutrition['carbs'] * 100) if stemmed_nutrition['carbs'] > 0 else 0

    # 全て1%以内かチェック
    all_within_1pct = (cal_diff_pct <= 1.0 and
                       protein_diff_pct <= 1.0 and
                       fat_diff_pct <= 1.0 and
                       carbs_diff_pct <= 1.0)

    return {
        'match': all_within_1pct,
        'calories_diff_pct': cal_diff_pct,
        'protein_diff_pct': protein_diff_pct,
        'fat_diff_pct': fat_diff_pct,
        'carbs_diff_pct': carbs_diff_pct,
        'details': {
            'stemmed': stemmed_nutrition,
            'final_100g': {
                **final_nutrition_100g,
                **final_macros_100g
            }
        }
    }


def find_best_match(stemmed_food: Dict, final_foods: List[Dict]) -> Optional[Dict]:
    """最適な対応食材を見つける"""

    stemmed_keywords = extract_keywords(stemmed_food['original_name'])
    stemmed_nutrition = stemmed_food['nutrition']

    candidates = []

    for final_food in final_foods:
        final_keywords = extract_keywords(final_food['food_name'])

        # キーワード一致度
        if not stemmed_keywords or not final_keywords:
            keyword_match = 0
        else:
            common_keywords = stemmed_keywords & final_keywords
            keyword_match = len(common_keywords) / len(stemmed_keywords)

        # 最低50%のキーワード一致が必要
        if keyword_match < 0.5:
            continue

        # 100g栄養情報を計算
        nutrition_100g = calculate_100g_nutrition(final_food['serving_options']['servings'])
        if not nutrition_100g:
            continue

        # マクロ栄養素を抽出
        macros = extract_macros_from_nutrition_facts(final_food['nutrition_facts'])
        macros_100g = convert_macros_to_100g(macros, nutrition_100g['grams_per_unit'])

        # 栄養情報マッチチェック
        match_result = check_nutrition_match(stemmed_nutrition, nutrition_100g, macros_100g)

        if match_result['match']:
            candidates.append({
                'final_food': final_food,
                'keyword_match': keyword_match,
                'nutrition_match': match_result,
                'common_keywords': list(stemmed_keywords & final_keywords)
            })

    # キーワード一致度が高い順にソート
    candidates.sort(key=lambda x: x['keyword_match'], reverse=True)

    return candidates[0] if candidates else None


def main():
    print("🔍 厳密な栄養情報ベース食材対応システム")
    print("=" * 80)
    print("マッチング基準: 名前部分一致 + カロリー・マクロ栄養素全て1%以内")
    print("=" * 80)

    # ファイル読み込み
    stemmed_file = Path('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json')
    final_file = Path('processed_data/all_foods_final_1152.json')

    with open(stemmed_file, 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    with open(final_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    final_foods = final_data['foods']

    print(f"\n📋 Stemmed Database: {len(stemmed_data)}個")
    print(f"📋 Final JSON: {len(final_foods)}個")

    # 対応チェック
    print(f"\n🔍 厳密マッチング実行中...")

    matched = []
    unmatched = []

    for i, stemmed_food in enumerate(stemmed_data):
        if (i + 1) % 100 == 0:
            print(f"   進行状況: {i + 1}/{len(stemmed_data)}")

        best_match = find_best_match(stemmed_food, final_foods)

        if best_match:
            matched.append({
                'stemmed_food': stemmed_food,
                'final_food': best_match['final_food'],
                'keyword_match': best_match['keyword_match'],
                'nutrition_match': best_match['nutrition_match'],
                'common_keywords': best_match['common_keywords']
            })
        else:
            unmatched.append(stemmed_food)

    print(f"\n✅ 完了!")
    print(f"\n📊 マッチング結果:")
    print(f"   ✅ マッチ成功: {len(matched)}個 ({len(matched)/len(stemmed_data)*100:.1f}%)")
    print(f"   ❌ 未マッチ: {len(unmatched)}個 ({len(unmatched)/len(stemmed_data)*100:.1f}%)")

    # 未マッチ食材を表示
    if unmatched:
        print(f"\n❌ 未マッチ食材（新規追加が必要）:")
        for i, food in enumerate(unmatched, 1):
            print(f"\n{i}. {food['original_name']}")
            print(f"   100g栄養: カロリー {food['nutrition']['calories']:.1f}, "
                  f"タンパク質 {food['nutrition']['protein']:.1f}g, "
                  f"脂質 {food['nutrition']['fat']:.1f}g, "
                  f"炭水化物 {food['nutrition']['carbs']:.1f}g")

    # マッチサンプル表示
    print(f"\n✅ マッチ成功サンプル（最初の5個）:")
    for i, match in enumerate(matched[:5], 1):
        print(f"\n{i}. Stemmed: {match['stemmed_food']['original_name']}")
        print(f"   Final: {match['final_food']['food_name']}")
        print(f"   キーワード一致: {match['keyword_match']*100:.1f}%")
        print(f"   共通キーワード: {', '.join(match['common_keywords'])}")
        print(f"   栄養差: カロリー {match['nutrition_match']['calories_diff_pct']:.2f}%, "
              f"タンパク質 {match['nutrition_match']['protein_diff_pct']:.2f}%, "
              f"脂質 {match['nutrition_match']['fat_diff_pct']:.2f}%, "
              f"炭水化物 {match['nutrition_match']['carbs_diff_pct']:.2f}%")

    # 対応テーブル保存
    correspondence = {
        'summary': {
            'total_stemmed': len(stemmed_data),
            'total_final': len(final_foods),
            'matched': len(matched),
            'unmatched': len(unmatched),
            'match_rate': len(matched) / len(stemmed_data) * 100
        },
        'matched_pairs': [
            {
                'stemmed_id': m['stemmed_food']['id'],
                'stemmed_name': m['stemmed_food']['original_name'],
                'final_id': m['final_food']['food_id'],
                'final_name': m['final_food']['food_name'],
                'keyword_match': m['keyword_match'],
                'nutrition_diff': {
                    'calories_pct': m['nutrition_match']['calories_diff_pct'],
                    'protein_pct': m['nutrition_match']['protein_diff_pct'],
                    'fat_pct': m['nutrition_match']['fat_diff_pct'],
                    'carbs_pct': m['nutrition_match']['carbs_diff_pct']
                }
            }
            for m in matched
        ],
        'unmatched_foods': [
            {
                'stemmed_id': f['id'],
                'original_name': f['original_name'],
                'nutrition_100g': f['nutrition']
            }
            for f in unmatched
        ]
    }

    output_file = 'processed_data/strict_food_correspondence.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(correspondence, f, ensure_ascii=False, indent=2)

    print(f"\n" + "=" * 80)
    print(f"💾 対応テーブル保存: {output_file}")
    print(f"\n📈 目標達成度: {len(matched)}/{len(stemmed_data)} ({len(matched)/len(stemmed_data)*100:.1f}%)")

    if unmatched:
        print(f"\n⚠️  新規追加が必要な食材: {len(unmatched)}個")
        print(f"   → 未マッチ食材リストを確認してください")


if __name__ == "__main__":
    main()
