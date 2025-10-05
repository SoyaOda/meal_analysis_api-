#!/usr/bin/env python3
"""
Filtered版をベースに、serving_sizeがNoneの食材のみUnified Processorで修正
"""

import json
from pathlib import Path
from unified_food_processor import UnifiedFoodProcessor


def main():
    print("🔄 Serving Size修正（元の情報を保持）")
    print("=" * 80)

    processor = UnifiedFoodProcessor()

    # Filtered版を読み込み
    with open('processed_data/all_foods_final_1126_filtered.json', 'r', encoding='utf-8') as f:
        filtered_data = json.load(f)

    # Scraping生データを読み込み
    scraping_file = processor.data_dir / 'comprehensive_food_collection_all_20251001_124446.json'
    with open(scraping_file, 'r', encoding='utf-8') as f:
        scraping_data = json.load(f)

    # Scraping結果をfood_nameでインデックス化
    scraping_by_name = {}
    for item in scraping_data['collection_results']:
        if item.get('data_collection_success') and item.get('comprehensive_data'):
            food_name = item['comprehensive_data'].get('food_name', '').replace('\n', ', ')
            if food_name:
                name_normalized = food_name.replace(',', '').lower()
                scraping_by_name[name_normalized] = item['comprehensive_data']

    # 処理
    fixed_count = 0
    already_ok_count = 0
    manual_count = 0

    for food in filtered_data['foods']:
        # data_sourceを追加（まだない場合）
        if 'data_source' not in food:
            # Manual食材かチェック（food_id >= 1100）
            food_id_num = int(food['food_id'].replace('food_', ''))
            if food_id_num >= 1100:
                food['data_source'] = 'manual'
                manual_count += 1
            else:
                food['data_source'] = 'scraping'

        # Serving sizeチェック
        serving_size = food.get('essential_nutrition', {}).get('serving_size')

        if serving_size and serving_size.get('grams', 0) > 0:
            # 既に正常
            already_ok_count += 1
            continue

        # Manual食材はスキップ
        if food.get('data_source') == 'manual':
            manual_count += 1
            continue

        # Scraping食材でserving_sizeがNone → 修正
        food_name_normalized = food['food_name'].replace(',', '').lower()
        scraping_raw = scraping_by_name.get(food_name_normalized)

        if not scraping_raw:
            print(f"⚠️  見つからない: {food['food_name']}")
            continue

        # Unified Processorで処理
        processed = processor.process_scraped_food(scraping_raw, food['food_id'])

        if processed:
            # serving_sizeのみ更新
            food['essential_nutrition']['serving_size'] = processed['essential_nutrition']['serving_size']

            # metadata更新
            if 'metadata' not in food:
                food['metadata'] = {}
            food['metadata']['serving_size_fixed'] = True
            food['metadata']['serving_size_info'] = processed['metadata'].get('serving_size_info')

            fixed_count += 1
        else:
            print(f"❌ 処理失敗: {food['food_name']}")

    print(f"📊 処理結果:")
    print(f"   既に正常: {already_ok_count}個")
    print(f"   修正: {fixed_count}個")
    print(f"   Manual: {manual_count}個")
    print(f"   合計: {len(filtered_data['foods'])}個")
    print()

    # 保存
    output_file = Path('processed_data/all_foods_final_1126_complete.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 保存完了: {output_file}")

    # 最終確認
    scraping_foods = [f for f in filtered_data['foods'] if f.get('data_source') == 'scraping']
    issues = 0
    for food in scraping_foods:
        ss = food.get('essential_nutrition', {}).get('serving_size')
        if not ss or ss.get('grams', 0) <= 0:
            issues += 1

    print()
    print(f"✅ Scraping由来: {len(scraping_foods)}個")
    print(f"   構造問題: {issues}個")

    if issues == 0:
        print()
        print("🎉 全ての食材で構造が正常です！元の情報も保持されています。")


if __name__ == "__main__":
    main()
