#!/usr/bin/env python3
"""
comprehensive_food_collection_all_20251001_124446.jsonの構造検証
"""

import json
from pathlib import Path


def main():
    print("🔍 生データ構造検証")
    print("=" * 80)

    # 生データ読み込み
    data_file = Path('data/comprehensive_food_collection_all_20251001_124446.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    summary = data.get('collection_summary', {})
    results = data.get('collection_results', [])

    print(f"📊 全体統計:")
    print(f"   総食材数: {summary.get('total_foods', 0)}個")
    print(f"   成功: {summary.get('successful', 0)}個")
    print(f"   失敗: {summary.get('failed', 0)}個")
    print(f"   成功率: {summary.get('success_rate', 0):.1f}%")
    print()

    # 検証項目
    total_items = len(results)

    # 1. food_name存在確認
    has_food_name = 0
    has_catalog_food_name = 0
    names_match = 0

    # 2. ステータス確認
    navigation_success = 0
    data_collection_success = 0
    both_success = 0

    # 3. comprehensive_data存在確認
    has_comprehensive_data = 0
    comprehensive_has_food_name = 0

    # 問題サンプル
    name_mismatch_samples = []
    status_failed_samples = []
    no_comprehensive_data_samples = []

    for i, item in enumerate(results, 1):
        # food_name確認
        food_name = item.get('food_name')
        catalog_food_name = item.get('catalog_food_name')

        if food_name:
            has_food_name += 1
        if catalog_food_name:
            has_catalog_food_name += 1

        if food_name and catalog_food_name:
            if food_name == catalog_food_name:
                names_match += 1
            else:
                if len(name_mismatch_samples) < 5:
                    name_mismatch_samples.append({
                        'sequence': i,
                        'food_name': food_name,
                        'catalog_food_name': catalog_food_name
                    })

        # ステータス確認
        nav_success = item.get('navigation_success', False)
        data_success = item.get('data_collection_success', False)

        if nav_success:
            navigation_success += 1
        if data_success:
            data_collection_success += 1
        if nav_success and data_success:
            both_success += 1
        else:
            if len(status_failed_samples) < 5:
                status_failed_samples.append({
                    'sequence': i,
                    'food_name': food_name,
                    'navigation_success': nav_success,
                    'data_collection_success': data_success
                })

        # comprehensive_data確認
        comp_data = item.get('comprehensive_data')
        if comp_data:
            has_comprehensive_data += 1
            if comp_data.get('food_name'):
                comprehensive_has_food_name += 1
        else:
            if len(no_comprehensive_data_samples) < 5:
                no_comprehensive_data_samples.append({
                    'sequence': i,
                    'food_name': food_name
                })

    # 結果表示
    print("=" * 80)
    print("【検証1】food_name と catalog_food_name")
    print("=" * 80)
    print(f"food_name存在: {has_food_name}/{total_items} ({has_food_name/total_items*100:.1f}%)")
    print(f"catalog_food_name存在: {has_catalog_food_name}/{total_items} ({has_catalog_food_name/total_items*100:.1f}%)")
    print(f"両者が一致: {names_match}/{total_items} ({names_match/total_items*100:.1f}%)")

    if name_mismatch_samples:
        print()
        print(f"⚠️  不一致サンプル（最初の5個）:")
        for sample in name_mismatch_samples:
            print(f"   {sample['sequence']}.")
            print(f"      food_name: {sample['food_name']}")
            print(f"      catalog_food_name: {sample['catalog_food_name']}")

    print()
    print("=" * 80)
    print("【検証2】navigation_success と data_collection_success")
    print("=" * 80)
    print(f"navigation_success=true: {navigation_success}/{total_items} ({navigation_success/total_items*100:.1f}%)")
    print(f"data_collection_success=true: {data_collection_success}/{total_items} ({data_collection_success/total_items*100:.1f}%)")
    print(f"両方true: {both_success}/{total_items} ({both_success/total_items*100:.1f}%)")

    if status_failed_samples:
        print()
        print(f"❌ ステータス失敗サンプル（最初の5個）:")
        for sample in status_failed_samples:
            print(f"   {sample['sequence']}. {sample['food_name']}")
            print(f"      navigation_success: {sample['navigation_success']}")
            print(f"      data_collection_success: {sample['data_collection_success']}")

    print()
    print("=" * 80)
    print("【検証3】comprehensive_data")
    print("=" * 80)
    print(f"comprehensive_data存在: {has_comprehensive_data}/{total_items} ({has_comprehensive_data/total_items*100:.1f}%)")
    print(f"comprehensive_data内にfood_name存在: {comprehensive_has_food_name}/{total_items} ({comprehensive_has_food_name/total_items*100:.1f}%)")

    if no_comprehensive_data_samples:
        print()
        print(f"⚠️  comprehensive_data不在サンプル（最初の5個）:")
        for sample in no_comprehensive_data_samples:
            print(f"   {sample['sequence']}. {sample['food_name']}")

    print()
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    # 理想的な状態の食材数
    ideal_foods = 0
    for item in results:
        food_name = item.get('food_name')
        catalog_food_name = item.get('catalog_food_name')
        nav_success = item.get('navigation_success', False)
        data_success = item.get('data_collection_success', False)
        comp_data = item.get('comprehensive_data')

        if (food_name and catalog_food_name and
            food_name == catalog_food_name and
            nav_success and data_success and
            comp_data and comp_data.get('food_name')):
            ideal_foods += 1

    print(f"✅ 全条件を満たす食材: {ideal_foods}/{total_items} ({ideal_foods/total_items*100:.1f}%)")
    print()

    if ideal_foods == total_items:
        print("🎉 全ての食材が理想的な状態です！")
    else:
        print(f"⚠️  {total_items - ideal_foods}個の食材に問題があります")
        print()
        print("推奨アクション:")
        print("  1. 両方true食材のみを使用する")
        print("  2. comprehensive_dataが存在する食材のみを使用する")
        print("  3. food_nameとcatalog_food_nameが一致する食材のみを使用する")


if __name__ == "__main__":
    main()
