#!/usr/bin/env python3
"""
serving_optionsの"Select Serving"存在確認
"""

import json
from pathlib import Path


def main():
    print("🔍 'Select Serving' 存在確認")
    print("=" * 80)

    # データ読み込み
    data_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']
    total = len(results)

    has_select_serving = 0
    no_select_serving = []

    for i, item in enumerate(results, 1):
        food_name = item.get('food_name', 'N/A')
        comp_data = item.get('comprehensive_data', {})
        serving_options = comp_data.get('serving_options', {})
        raw_serving_data = serving_options.get('raw_serving_data', [])

        # "Select Serving"を探す
        found = False
        for serving_item in raw_serving_data:
            if isinstance(serving_item, str) and serving_item.strip() == "Select Serving":
                found = True
                break

        if found:
            has_select_serving += 1
        else:
            if len(no_select_serving) < 10:
                no_select_serving.append({
                    'sequence': i,
                    'food_name': food_name,
                    'raw_serving_data_length': len(raw_serving_data)
                })

    # 結果表示
    print(f"総食材数: {total}個")
    print()
    print(f"✅ 'Select Serving'存在: {has_select_serving}/{total} ({has_select_serving/total*100:.1f}%)")
    print(f"❌ 'Select Serving'不在: {len(results) - has_select_serving}/{total} ({(len(results) - has_select_serving)/total*100:.1f}%)")
    print()

    if no_select_serving:
        print("=" * 80)
        print("【'Select Serving'不在サンプル（最初の10個）】")
        print("=" * 80)
        for item in no_select_serving:
            print(f"{item['sequence']:4d}. {item['food_name']}")
            print(f"       raw_serving_data要素数: {item['raw_serving_data_length']}")
            print()

    # 総合判定
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    if has_select_serving == total:
        print("🎉 全1,188食材で'Select Serving'が存在します！")
    else:
        missing_count = total - has_select_serving
        print(f"⚠️  {missing_count}個の食材で'Select Serving'が不在です")


if __name__ == "__main__":
    main()
