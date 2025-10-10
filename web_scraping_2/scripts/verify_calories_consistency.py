#!/usr/bin/env python3
"""
全食材のdefault_caloriesとtitle_caloriesの一致を検証するスクリプト
"""

import json
import re
from pathlib import Path

def main():
    json_file = Path(__file__).parent.parent / "output" / "all_foods_default_unit_calories.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mismatches = []
    valid_count = 0
    excluded_count = 0

    for food in data['foods']:
        # 除外食材はスキップ
        if food['default_calories'] is None:
            excluded_count += 1
            continue

        # title_caloriesから数値を抽出（コンマ対応）
        title_calories = food['title_calories']
        title_match = re.search(r'([\d,]+)cals', title_calories)

        if not title_match:
            mismatches.append({
                'food_name': food['food_name'],
                'category': food['category'],
                'file': food['file'],
                'default_calories': food['default_calories'],
                'title_calories': title_calories,
                'issue': 'title_calories format error'
            })
            continue

        # title_caloriesの数値をfloatに変換
        title_cal_value = float(title_match.group(1).replace(',', ''))
        default_cal_value = food['default_calories']

        # 値を比較
        if title_cal_value != default_cal_value:
            mismatches.append({
                'food_name': food['food_name'],
                'category': food['category'],
                'file': food['file'],
                'default_calories': default_cal_value,
                'title_calories': title_calories,
                'title_cal_value': title_cal_value,
                'difference': title_cal_value - default_cal_value,
                'issue': 'calories mismatch'
            })
        else:
            valid_count += 1

    # 結果を表示
    print("=" * 80)
    print("カロリー一致性検証結果")
    print("=" * 80)
    print(f"\n総食材数: {len(data['foods'])}")
    print(f"有効食材数: {valid_count}")
    print(f"除外食材数: {excluded_count}")
    print(f"不一致食材数: {len(mismatches)}")
    print(f"一致率: {valid_count / (len(data['foods']) - excluded_count) * 100:.2f}%")

    if mismatches:
        print(f"\n{'=' * 80}")
        print(f"不一致の詳細 ({len(mismatches)}件):")
        print(f"{'=' * 80}\n")

        for i, mismatch in enumerate(mismatches, 1):
            print(f"{i}. {mismatch['food_name']}")
            print(f"   カテゴリ: {mismatch['category']}")
            print(f"   ファイル: {mismatch['file']}")
            print(f"   default_calories: {mismatch['default_calories']}")
            print(f"   title_calories: {mismatch['title_calories']}")
            if 'title_cal_value' in mismatch:
                print(f"   title数値: {mismatch['title_cal_value']}")
                print(f"   差分: {mismatch['difference']:+.1f}")
            print(f"   問題: {mismatch['issue']}")
            print()

        # レポートファイルに保存
        report_file = Path(__file__).parent.parent / "output" / "CALORIES_CONSISTENCY_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# カロリー一致性検証レポート\n\n")
            f.write(f"## 概要\n\n")
            f.write(f"- 総食材数: {len(data['foods'])}\n")
            f.write(f"- 有効食材数: {valid_count}\n")
            f.write(f"- 除外食材数: {excluded_count}\n")
            f.write(f"- 不一致食材数: {len(mismatches)}\n")
            f.write(f"- 一致率: {valid_count / (len(data['foods']) - excluded_count) * 100:.2f}%\n\n")

            f.write(f"## 不一致の詳細 ({len(mismatches)}件)\n\n")

            for i, mismatch in enumerate(mismatches, 1):
                f.write(f"### {i}. {mismatch['food_name']}\n\n")
                f.write(f"- **カテゴリ**: {mismatch['category']}\n")
                f.write(f"- **ファイル**: {mismatch['file']}\n")
                f.write(f"- **default_calories**: {mismatch['default_calories']}\n")
                f.write(f"- **title_calories**: {mismatch['title_calories']}\n")
                if 'title_cal_value' in mismatch:
                    f.write(f"- **title数値**: {mismatch['title_cal_value']}\n")
                    f.write(f"- **差分**: {mismatch['difference']:+.1f}\n")
                f.write(f"- **問題**: {mismatch['issue']}\n\n")

        print(f"\nレポートを保存しました: {report_file}")
    else:
        print("\n✅ 全ての食材でカロリーが一致しています！")

if __name__ == "__main__":
    main()
