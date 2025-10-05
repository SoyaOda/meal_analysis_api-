#!/usr/bin/env python3
"""
complete_scraping_data_1188_foods.jsonの詳細検証
"""

import json
from pathlib import Path


def main():
    print("🔍 complete_scraping_data_1188_foods.json 詳細検証")
    print("=" * 80)

    # データ読み込み
    data_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']
    total = len(results)

    print(f"総食材数: {total}個")
    print()

    # 検証1: catalog_category
    print("=" * 80)
    print("【検証1】catalog_category")
    print("=" * 80)

    has_catalog_category = 0
    empty_catalog_category = 0
    catalog_categories = set()
    no_category_samples = []

    for i, item in enumerate(results, 1):
        catalog_cat = item.get('catalog_category')

        if catalog_cat:
            has_catalog_category += 1
            if catalog_cat.strip():
                catalog_categories.add(catalog_cat)
            else:
                empty_catalog_category += 1
        else:
            if len(no_category_samples) < 5:
                no_category_samples.append({
                    'sequence': i,
                    'food_name': item.get('food_name', 'N/A')
                })

    print(f"catalog_category存在: {has_catalog_category}/{total} ({has_catalog_category/total*100:.1f}%)")
    print(f"空文字: {empty_catalog_category}個")
    print(f"ユニークなカテゴリ数: {len(catalog_categories)}個")
    print()
    print(f"カテゴリ一覧:")
    for cat in sorted(catalog_categories):
        count = sum(1 for item in results if item.get('catalog_category') == cat)
        print(f"   {cat}: {count}個")

    if no_category_samples:
        print()
        print(f"❌ catalog_category不在サンプル:")
        for sample in no_category_samples:
            print(f"   {sample['sequence']}. {sample['food_name']}")

    # 検証2: food_name の一致
    print()
    print("=" * 80)
    print("【検証2】food_name の3箇所一致確認")
    print("=" * 80)

    all_match = 0
    mismatch_samples = []

    for i, item in enumerate(results, 1):
        food_name = item.get('food_name')
        catalog_food_name = item.get('catalog_food_name')
        comp_data = item.get('comprehensive_data', {})
        comp_food_name = comp_data.get('food_name')

        # 3つ全て存在するか
        if not food_name:
            if len(mismatch_samples) < 5:
                mismatch_samples.append({
                    'sequence': i,
                    'issue': 'food_name不在',
                    'food_name': None,
                    'catalog_food_name': catalog_food_name,
                    'comp_food_name': comp_food_name
                })
            continue

        if not catalog_food_name:
            if len(mismatch_samples) < 5:
                mismatch_samples.append({
                    'sequence': i,
                    'issue': 'catalog_food_name不在',
                    'food_name': food_name,
                    'catalog_food_name': None,
                    'comp_food_name': comp_food_name
                })
            continue

        if not comp_food_name:
            if len(mismatch_samples) < 5:
                mismatch_samples.append({
                    'sequence': i,
                    'issue': 'comprehensive_data.food_name不在',
                    'food_name': food_name,
                    'catalog_food_name': catalog_food_name,
                    'comp_food_name': None
                })
            continue

        # 3つが一致するか
        if food_name == catalog_food_name == comp_food_name:
            all_match += 1
        else:
            if len(mismatch_samples) < 5:
                mismatch_samples.append({
                    'sequence': i,
                    'issue': '内容不一致',
                    'food_name': food_name,
                    'catalog_food_name': catalog_food_name,
                    'comp_food_name': comp_food_name
                })

    print(f"3箇所全て存在: {all_match + len([s for s in mismatch_samples if 'food_name' in str(s)])}/{total}")
    print(f"3箇所全て一致: {all_match}/{total} ({all_match/total*100:.1f}%)")

    if mismatch_samples:
        print()
        print(f"❌ 不一致サンプル（最初の5個）:")
        for sample in mismatch_samples:
            print(f"   {sample['sequence']}. {sample['issue']}")
            print(f"      food_name: {sample['food_name']}")
            print(f"      catalog_food_name: {sample['catalog_food_name']}")
            print(f"      comp_food_name: {sample['comp_food_name']}")
            print()

    # 総合判定
    print()
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    if has_catalog_category == total and all_match == total:
        print("✅ 全ての検証項目をパス！")
        print(f"   catalog_category: {total}/{total} (100.0%)")
        print(f"   food_name 3箇所一致: {total}/{total} (100.0%)")
    else:
        print("⚠️  一部の食材で問題があります:")
        if has_catalog_category < total:
            print(f"   catalog_category不在: {total - has_catalog_category}個")
        if all_match < total:
            print(f"   food_name不一致: {total - all_match}個")


if __name__ == "__main__":
    main()
