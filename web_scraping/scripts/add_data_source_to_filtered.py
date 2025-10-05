#!/usr/bin/env python3
"""
all_foods_final_1126_filtered.jsonに各食材のdata_source (scraping/manual) を追加
"""

import json
from pathlib import Path


def main():
    print("🔄 Data Source情報追加実行")
    print("=" * 80)

    # Manual foodsのリストを取得
    with open('processed_data/manual_foods_converted_to_processed_format.json', 'r', encoding='utf-8') as f:
        manual_data = json.load(f)

    manual_food_ids = set(f['food_id'] for f in manual_data['foods'])
    print(f"📊 Manual foods: {len(manual_food_ids)}個")

    # Filtered JSONを読み込み
    with open('processed_data/all_foods_final_1126_filtered.json', 'r', encoding='utf-8') as f:
        filtered_data = json.load(f)

    print(f"📊 Filtered foods: {len(filtered_data['foods'])}個")
    print()

    # data_sourceを追加
    scraping_count = 0
    manual_count = 0

    for food in filtered_data['foods']:
        food_id = food['food_id']

        if food_id in manual_food_ids:
            food['data_source'] = 'manual'
            manual_count += 1
        else:
            food['data_source'] = 'scraping'
            scraping_count += 1

    print(f"✅ Data Source追加完了:")
    print(f"   Scraping由来: {scraping_count}個")
    print(f"   Manual由来: {manual_count}個")
    print()

    # メタデータ更新
    filtered_data['metadata']['data_source_breakdown'] = {
        'scraping': scraping_count,
        'manual': manual_count
    }

    # 上書き保存
    output_file = Path('processed_data/all_foods_final_1126_filtered.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 保存完了: {output_file}")

    # サンプル表示
    print(f"\n📝 サンプル（最初の5個）:")
    for i, food in enumerate(filtered_data['foods'][:5], 1):
        print(f"   {i}. {food['food_id']}: {food['food_name']} → data_source: {food['data_source']}")


if __name__ == "__main__":
    main()
