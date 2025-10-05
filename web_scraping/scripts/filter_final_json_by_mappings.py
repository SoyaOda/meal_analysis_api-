#!/usr/bin/env python3
"""
all_foods_final_1152.jsonをcomplete_1to1_mappings.jsonに基づいてフィルタリング
"""

import json
from pathlib import Path


def main():
    print("🔄 Final JSONフィルタリング実行")
    print("=" * 80)

    # Mappingsを読み込み
    with open('processed_data/complete_1to1_mappings.json', 'r', encoding='utf-8') as f:
        mappings_data = json.load(f)

    # Final JSONを読み込み
    with open('processed_data/all_foods_final_1152.json', 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    # Mappingに含まれるfinal_food_nameのセットを作成
    mapped_names = set()
    for mapping in mappings_data['mappings']:
        # Normalize (カンマ削除、小文字化)
        name = mapping['final_food_name'].replace(',', '').lower()
        mapped_names.add(name)

    print(f"📊 Mappingに含まれる食材名: {len(mapped_names)}個")
    print(f"📊 Final JSONの元の食材数: {len(final_data['foods'])}個")

    # フィルタリング
    filtered_foods = []
    removed_foods = []

    for food in final_data['foods']:
        food_name = food['food_name'].replace(',', '').lower()

        if food_name in mapped_names:
            filtered_foods.append(food)
        else:
            removed_foods.append(food['food_name'])

    print(f"✅ フィルタリング後: {len(filtered_foods)}個")
    print(f"❌ 削除: {len(removed_foods)}個")
    print()

    # 削除された食材を表示
    if removed_foods:
        print(f"📋 削除された食材一覧 ({len(removed_foods)}個):")
        for i, name in enumerate(removed_foods, 1):
            print(f"   {i}. {name}")
        print()

    # 保存
    output_data = {
        'metadata': {
            'version': final_data['metadata']['version'],
            'source': 'all_foods_final_1152.json (filtered)',
            'total_foods': len(filtered_foods),
            'removed_foods': len(removed_foods),
            'filter_criteria': 'complete_1to1_mappings.json'
        },
        'foods': filtered_foods
    }

    output_file = Path('processed_data/all_foods_final_1126_filtered.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 保存完了: {output_file}")
    print(f"   総食材数: {len(filtered_foods)}個")

    # 削除リストも保存
    removed_file = Path('processed_data/removed_foods_26.json')
    with open(removed_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_removed': len(removed_foods),
            'removed_food_names': removed_foods
        }, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 削除リスト保存: {removed_file}")


if __name__ == "__main__":
    main()
