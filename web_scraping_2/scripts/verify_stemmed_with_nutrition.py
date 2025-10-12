#!/usr/bin/env python3
"""
db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.jsonの品質検証

検証項目:
1. 全ての食材で有効な"unit_to_grams"が存在する
2. "default_unit"が"unit_to_grams"に含まれる
3. "unit_to_grams"のunitが数字から始まらない
4. 同一のunitが複数存在しない
"""

import json
import re
from pathlib import Path
from collections import Counter


def verify_stemmed_with_nutrition(filepath: Path):
    """Stemmed with nutritionファイルを検証"""

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 80)
    print("Stemmed With Nutrition 品質検証")
    print("=" * 80)
    print(f"\n総アイテム数: {len(data):,}件\n")

    # 検証結果
    issues = {
        'no_unit_to_grams': [],
        'empty_unit_to_grams': [],
        'default_unit_not_in_mapping': [],
        'units_starting_with_number': [],
        'duplicate_units': []
    }

    # 各アイテムを検証
    for item in data:
        original_name = item.get('original_name', 'Unknown')
        default_unit = item.get('default_unit')
        unit_to_grams = item.get('unit_to_grams')

        # 1. unit_to_gramsの存在チェック
        if unit_to_grams is None:
            issues['no_unit_to_grams'].append({
                'original_name': original_name,
                'reason': 'unit_to_grams is None'
            })
            continue

        # 2. unit_to_gramsが空でないかチェック
        if not unit_to_grams or len(unit_to_grams) == 0:
            issues['empty_unit_to_grams'].append({
                'original_name': original_name,
                'reason': 'unit_to_grams is empty'
            })
            continue

        # 3. default_unitがunit_to_gramsに含まれるかチェック
        if default_unit and default_unit not in unit_to_grams:
            issues['default_unit_not_in_mapping'].append({
                'original_name': original_name,
                'default_unit': default_unit,
                'available_units': list(unit_to_grams.keys())
            })

        # 4. unitが数字から始まらないかチェック
        number_pattern = re.compile(r'^\d+\.?\d*\s+')
        for unit_name in unit_to_grams.keys():
            if number_pattern.match(unit_name):
                issues['units_starting_with_number'].append({
                    'original_name': original_name,
                    'unit': unit_name,
                    'gram_value': unit_to_grams[unit_name]
                })

        # 5. 同一unitが複数存在しないかチェック（大文字小文字も区別）
        unit_counter = Counter(unit_to_grams.keys())
        duplicates = [unit for unit, count in unit_counter.items() if count > 1]
        if duplicates:
            issues['duplicate_units'].append({
                'original_name': original_name,
                'duplicate_units': duplicates
            })

    # 結果表示
    print("【検証結果】\n")

    # 1. unit_to_gramsの存在
    if issues['no_unit_to_grams']:
        print(f"❌ unit_to_gramsが存在しない: {len(issues['no_unit_to_grams'])}件")
        for item in issues['no_unit_to_grams'][:5]:
            print(f"   - {item['original_name']}")
        if len(issues['no_unit_to_grams']) > 5:
            print(f"   ... 他 {len(issues['no_unit_to_grams']) - 5} 件")
    else:
        print(f"✅ unit_to_gramsが存在しない: 0件")

    # 2. unit_to_gramsが空
    if issues['empty_unit_to_grams']:
        print(f"\n❌ unit_to_gramsが空: {len(issues['empty_unit_to_grams'])}件")
        for item in issues['empty_unit_to_grams'][:5]:
            print(f"   - {item['original_name']}")
        if len(issues['empty_unit_to_grams']) > 5:
            print(f"   ... 他 {len(issues['empty_unit_to_grams']) - 5} 件")
    else:
        print(f"✅ unit_to_gramsが空: 0件")

    # 3. default_unitがunit_to_gramsに含まれない
    if issues['default_unit_not_in_mapping']:
        print(f"\n❌ default_unitがunit_to_gramsに含まれない: {len(issues['default_unit_not_in_mapping'])}件")
        for item in issues['default_unit_not_in_mapping'][:5]:
            print(f"   - {item['original_name']}")
            print(f"     default_unit: {item['default_unit']}")
            print(f"     available_units: {', '.join(item['available_units'][:5])}")
        if len(issues['default_unit_not_in_mapping']) > 5:
            print(f"   ... 他 {len(issues['default_unit_not_in_mapping']) - 5} 件")
    else:
        print(f"✅ default_unitがunit_to_gramsに含まれない: 0件")

    # 4. unitが数字から始まる
    if issues['units_starting_with_number']:
        print(f"\n❌ 数字から始まるunit: {len(issues['units_starting_with_number'])}件")
        for item in issues['units_starting_with_number'][:10]:
            print(f"   - {item['original_name']}: \"{item['unit']}\" = {item['gram_value']}g")
        if len(issues['units_starting_with_number']) > 10:
            print(f"   ... 他 {len(issues['units_starting_with_number']) - 10} 件")
    else:
        print(f"✅ 数字から始まるunit: 0件")

    # 5. 同一unitの重複
    if issues['duplicate_units']:
        print(f"\n❌ 同一unitが複数存在: {len(issues['duplicate_units'])}件")
        for item in issues['duplicate_units'][:5]:
            print(f"   - {item['original_name']}: {item['duplicate_units']}")
        if len(issues['duplicate_units']) > 5:
            print(f"   ... 他 {len(issues['duplicate_units']) - 5} 件")
    else:
        print(f"✅ 同一unitが複数存在: 0件")

    # 総合評価
    print("\n" + "=" * 80)
    total_issues = sum(len(v) for v in issues.values())
    if total_issues == 0:
        print("🎉 すべての検証項目をクリア！データは完全に正常です。")
    else:
        print(f"⚠️  合計 {total_issues} 件の問題が見つかりました。")
    print("=" * 80)

    # 詳細レポートをJSONで保存
    report_file = filepath.parent / 'stemmed_with_nutrition_verification_report.json'
    report = {
        'total_items': len(data),
        'total_issues': total_issues,
        'issues_summary': {
            'no_unit_to_grams': len(issues['no_unit_to_grams']),
            'empty_unit_to_grams': len(issues['empty_unit_to_grams']),
            'default_unit_not_in_mapping': len(issues['default_unit_not_in_mapping']),
            'units_starting_with_number': len(issues['units_starting_with_number']),
            'duplicate_units': len(issues['duplicate_units'])
        },
        'issues_detail': issues
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n詳細レポート: {report_file}")

    return total_issues == 0


def main():
    """メイン処理"""
    stemmed_file = Path('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json')

    if not stemmed_file.exists():
        print(f"❌ ファイルが見つかりません: {stemmed_file}")
        return

    success = verify_stemmed_with_nutrition(stemmed_file)

    if success:
        print("\n✅ 検証完了：すべてのチェックに合格しました！")
    else:
        print("\n⚠️  検証完了：いくつかの問題が見つかりました。詳細レポートを確認してください。")


if __name__ == '__main__':
    main()
