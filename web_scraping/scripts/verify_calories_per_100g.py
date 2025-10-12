#!/usr/bin/env python3
"""
nutrition_per_100g_oldのcaloriesと、update_infoから計算したcalories_per_100gを比較検証

比較方法:
1. update_info['serving_conversions']のgramユニットから計算
2. nutrition_per_100g_old['calories']と比較
3. 差分を分析

Usage:
    python verify_calories_per_100g.py
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


def calculate_calories_per_100g(update_info: dict) -> Optional[float]:
    """update_infoから100gあたりのカロリーを計算

    Method 1を使用: serving_infoから計算（より信頼性が高い）
    """
    # Method 1: serving_info (優先)
    serving_info = update_info.get('serving_info', {})
    grams_per_unit = serving_info.get('grams_per_unit')
    calories_per_unit = serving_info.get('calories_per_unit')

    if grams_per_unit and calories_per_unit and grams_per_unit > 0:
        return (calories_per_unit / grams_per_unit) * 100

    # Fallback: Method 2 (serving_conversionsのgramユニット)
    # 注意: このデータは信頼性が低い可能性がある
    conversions = update_info.get('serving_conversions', {}).get('conversions', [])
    for conversion in conversions:
        if conversion.get('unit') == 'gram':
            calories = conversion.get('calories')
            grams = conversion.get('grams')
            if calories is not None and grams == 1.0:
                return calories * 100

    return None


def compare_calories(data: List[dict]) -> Dict:
    """全食材のカロリーを比較"""

    stats = {
        'total_items': len(data),
        'calculated_successfully': 0,
        'calculation_failed': 0,
        'perfect_match': 0,
        'small_diff': 0,      # 差分 < 0.1
        'medium_diff': 0,     # 0.1 <= 差分 < 1.0
        'large_diff': 0,      # 1.0 <= 差分 < 5.0
        'very_large_diff': 0, # 差分 >= 5.0
        'discrepancies': [],
        'failed_calculations': []
    }

    for item in data:
        item_id = item['id']
        name = item.get('original_name', 'N/A')

        # nutrition_per_100g_oldから元のカロリー
        old_calories = item.get('nutrition_per_100g_old', {}).get('calories')

        # update_infoから新しいカロリーを計算
        update_info = item.get('update_info', {})
        new_calories = calculate_calories_per_100g(update_info)

        if new_calories is None:
            stats['calculation_failed'] += 1
            stats['failed_calculations'].append({
                'id': item_id,
                'name': name,
                'old_calories': old_calories
            })
            continue

        stats['calculated_successfully'] += 1

        # 差分を計算
        diff = abs(new_calories - old_calories)
        diff_percent = (diff / old_calories * 100) if old_calories > 0 else 0

        # 差分レベルで分類
        if diff < 0.01:
            stats['perfect_match'] += 1
        elif diff < 0.1:
            stats['small_diff'] += 1
        elif diff < 1.0:
            stats['medium_diff'] += 1
            stats['discrepancies'].append({
                'id': item_id,
                'name': name,
                'old_calories': old_calories,
                'new_calories': new_calories,
                'diff': diff,
                'diff_percent': diff_percent,
                'level': 'medium'
            })
        elif diff < 5.0:
            stats['large_diff'] += 1
            stats['discrepancies'].append({
                'id': item_id,
                'name': name,
                'old_calories': old_calories,
                'new_calories': new_calories,
                'diff': diff,
                'diff_percent': diff_percent,
                'level': 'large'
            })
        else:
            stats['very_large_diff'] += 1
            stats['discrepancies'].append({
                'id': item_id,
                'name': name,
                'old_calories': old_calories,
                'new_calories': new_calories,
                'diff': diff,
                'diff_percent': diff_percent,
                'level': 'very_large'
            })

    # 差分の大きい順にソート
    stats['discrepancies'].sort(key=lambda x: x['diff'], reverse=True)

    return stats


def save_report(stats: Dict, filepath: Path):
    """レポートを保存"""
    report = {
        'total_items': stats['total_items'],
        'calculated_successfully': stats['calculated_successfully'],
        'calculation_failed': stats['calculation_failed'],
        'comparison': {
            'perfect_match': stats['perfect_match'],
            'small_diff': stats['small_diff'],
            'medium_diff': stats['medium_diff'],
            'large_diff': stats['large_diff'],
            'very_large_diff': stats['very_large_diff']
        },
        'failed_calculations': stats['failed_calculations'],
        'discrepancies': stats['discrepancies'][:50]  # 最大50件
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def print_summary(stats: Dict):
    """サマリーを出力"""
    print("=" * 80)
    print("calories_per_100g 検証レポート")
    print("=" * 80)

    print(f"\n【統計】")
    print(f"総食材数: {stats['total_items']:,}")
    print(f"計算成功: {stats['calculated_successfully']:,} ({stats['calculated_successfully']/stats['total_items']*100:.2f}%)")
    print(f"計算失敗: {stats['calculation_failed']:,}")

    print(f"\n【差分レベル別】")
    print(f"完全一致 (< 0.01): {stats['perfect_match']:,} ({stats['perfect_match']/stats['calculated_successfully']*100:.2f}%)")
    print(f"微小差分 (< 0.1): {stats['small_diff']:,} ({stats['small_diff']/stats['calculated_successfully']*100:.2f}%)")
    print(f"中程度差分 (< 1.0): {stats['medium_diff']:,} ({stats['medium_diff']/stats['calculated_successfully']*100:.2f}%)")
    print(f"大差分 (< 5.0): {stats['large_diff']:,} ({stats['large_diff']/stats['calculated_successfully']*100:.2f}%)")
    print(f"非常に大きな差分 (>= 5.0): {stats['very_large_diff']:,} ({stats['very_large_diff']/stats['calculated_successfully']*100:.2f}%)")

    acceptable = stats['perfect_match'] + stats['small_diff']
    print(f"\n許容範囲内 (< 0.1): {acceptable:,} ({acceptable/stats['calculated_successfully']*100:.2f}%)")

    if stats['discrepancies']:
        print(f"\n【差分が大きい食材（上位10件）】")
        for i, item in enumerate(stats['discrepancies'][:10], 1):
            print(f"{i}. {item['name']}")
            print(f"   Old: {item['old_calories']:.2f} kcal/100g")
            print(f"   New: {item['new_calories']:.2f} kcal/100g")
            print(f"   Diff: {item['diff']:.2f} kcal ({item['diff_percent']:.2f}%)")
            print(f"   Level: {item['level']}")

    if stats['failed_calculations']:
        print(f"\n【計算失敗した食材】 ({len(stats['failed_calculations'])}件)")
        for i, item in enumerate(stats['failed_calculations'][:5], 1):
            print(f"{i}. {item['name']}")
            print(f"   ID: {item['id']}")
            print(f"   Old calories: {item['old_calories']}")

    print(f"\n【結論】")
    if stats['calculation_failed'] == 0:
        if acceptable == stats['calculated_successfully']:
            print("✅ 全ての食材で計算成功、かつ差分が許容範囲内（< 0.1 kcal）です！")
        elif acceptable / stats['calculated_successfully'] > 0.95:
            print(f"✅ 95%以上の食材で差分が許容範囲内です")
            print(f"⚠️ {stats['medium_diff'] + stats['large_diff'] + stats['very_large_diff']:,}件で中〜大きな差分があります")
        else:
            print(f"⚠️ {acceptable/stats['calculated_successfully']*100:.1f}%の食材のみが許容範囲内です")
            print(f"⚠️ 差分の大きい食材を確認してください")
    else:
        print(f"⚠️ {stats['calculation_failed']:,}件で計算失敗しています")


def main():
    # ファイルパス
    base_dir = Path('/Users/odasoya/meal_analysis_api_2')
    stemmed_db_file = base_dir / 'db' / 'updated_mynetdiary_converted_tool_calls_list_stemmed.json'
    report_file = base_dir / 'db' / 'calories_per_100g_verification_report.json'

    print("【1. データ読み込み中】")
    with open(stemmed_db_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Stemmed DB: {len(data)} アイテム")

    print("\n【2. カロリー比較中】")
    stats = compare_calories(data)
    print(f"✓ 比較完了")

    print("\n【3. レポート保存中】")
    save_report(stats, report_file)
    print(f"✓ レポート保存: {report_file}")

    print("\n")
    print_summary(stats)

    print(f"\n完了！")


if __name__ == '__main__':
    main()
