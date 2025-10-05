#!/usr/bin/env python3
"""
complete_1to1_mappings.jsonの1,126食材をUnified Processorで再処理
"""

import json
from pathlib import Path
from unified_food_processor import UnifiedFoodProcessor


def main():
    print("🔄 1,126食材をUnified Processorで再処理")
    print("=" * 80)

    processor = UnifiedFoodProcessor()

    # Mappingsを読み込み
    with open('processed_data/complete_1to1_mappings.json', 'r', encoding='utf-8') as f:
        mappings_data = json.load(f)

    # Scraping生データを読み込み
    scraping_file = processor.data_dir / 'comprehensive_food_collection_all_20251001_124446.json'
    with open(scraping_file, 'r', encoding='utf-8') as f:
        scraping_data = json.load(f)

    # Manual処理済みデータを読み込み
    with open('processed_data/manual_foods_converted_to_processed_format.json', 'r', encoding='utf-8') as f:
        manual_data = json.load(f)

    # Manual food IDsセット
    manual_food_ids = set(f['food_id'] for f in manual_data['foods'])

    # Mappingに含まれるfinal_food_nameのセットを作成
    mapped_names = {}
    for mapping in mappings_data['mappings']:
        name_normalized = mapping['final_food_name'].replace(',', '').lower()
        mapped_names[name_normalized] = mapping

    print(f"📊 処理対象: {len(mapped_names)}個")
    print()

    # Scraping結果をfood_nameでインデックス化
    scraping_by_name = {}
    for item in scraping_data['collection_results']:
        if item.get('data_collection_success') and item.get('comprehensive_data'):
            food_name = item['comprehensive_data'].get('food_name', '').replace('\n', ', ')
            if food_name:
                name_normalized = food_name.replace(',', '').lower()
                scraping_by_name[name_normalized] = item['comprehensive_data']

    # Filtered版を読み込んで元のfood_idマッピングを作成
    with open('processed_data/all_foods_final_1126_filtered.json', 'r', encoding='utf-8') as f:
        filtered_data = json.load(f)

    # food_nameでfood_idをマッピング
    name_to_food_id = {}
    for food in filtered_data['foods']:
        name_normalized = food['food_name'].replace(',', '').lower()
        name_to_food_id[name_normalized] = food['food_id']

    # 処理実行
    results = []
    scraping_count = 0
    manual_count = 0
    failed_count = 0

    # Filtered版の順序でfood_idを保持
    for food in filtered_data['foods']:
        food_name_normalized = food['food_name'].replace(',', '').lower()
        original_food_id = food['food_id']

        # Manual食材かチェック
        if original_food_id in manual_food_ids:
            # Manual食材を追加
            manual_food = next((f for f in manual_data['foods'] if f['food_id'] == original_food_id), None)
            if manual_food:
                manual_food['data_source'] = 'manual'
                results.append(manual_food)
                manual_count += 1
        else:
            # Scraping食材を処理
            scraping_raw = scraping_by_name.get(food_name_normalized)
            if not scraping_raw:
                print(f"⚠️  見つからない: {food['food_name']}")
                failed_count += 1
                continue

            # Unified Processorで処理（元のfood_idを使用）
            processed = processor.process_scraped_food(scraping_raw, original_food_id)

            if processed:
                processed['data_source'] = 'scraping'
                results.append(processed)
                scraping_count += 1
            else:
                print(f"❌ 処理失敗: {food['food_name']}")
                failed_count += 1

    print(f"📊 処理結果:")
    print(f"   Scraping: {scraping_count}個")
    print(f"   Manual: {manual_count}個")
    print(f"   失敗: {failed_count}個")
    print(f"   合計: {len(results)}個")
    print()

    # 保存
    output_data = {
        'metadata': {
            'version': '2.0_unified',
            'processed_at': results[0]['metadata']['processed_at'] if results else '',
            'total_foods': len(results),
            'processor': 'unified_food_processor',
            'data_source_breakdown': {
                'scraping': scraping_count,
                'manual': manual_count
            }
        },
        'foods': results
    }

    output_file = processor.output_dir / 'all_foods_final_1126_unified.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 保存完了: {output_file}")


if __name__ == "__main__":
    main()
