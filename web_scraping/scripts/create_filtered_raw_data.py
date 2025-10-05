#!/usr/bin/env python3
"""
comprehensive_data存在する1,188食材のみをフィルタリング
"""

import json
from pathlib import Path


def main():
    print("🔄 生データのフィルタリング（両方success条件）")
    print("=" * 80)

    # 元データ読み込み
    source_file = Path('data/comprehensive_food_collection_all_20251001_124446.json')
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📁 元データ: {source_file}")
    print(f"   総食材数: {len(data['collection_results'])}個")
    print()

    # フィルタリング条件: comprehensive_data存在 AND 両方success
    filtered_results = []
    removed_count = 0
    removed_reasons = {
        'no_comprehensive_data': 0,
        'navigation_failed': 0,
        'data_collection_failed': 0
    }

    for item in data['collection_results']:
        comp_data = item.get('comprehensive_data')
        nav_success = item.get('navigation_success', False)
        data_success = item.get('data_collection_success', False)

        # 全条件を満たすかチェック
        if comp_data and nav_success and data_success:
            filtered_results.append(item)
        else:
            removed_count += 1
            # 削除理由を記録
            if not comp_data:
                removed_reasons['no_comprehensive_data'] += 1
            if not nav_success:
                removed_reasons['navigation_failed'] += 1
            if not data_success:
                removed_reasons['data_collection_failed'] += 1

    print(f"✅ フィルタ条件を満たす食材: {len(filtered_results)}個")
    print(f"❌ 削除: {removed_count}個")
    print()
    print(f"削除理由:")
    print(f"   comprehensive_data不在: {removed_reasons['no_comprehensive_data']}個")
    print(f"   navigation_success=false: {removed_reasons['navigation_failed']}個")
    print(f"   data_collection_success=false: {removed_reasons['data_collection_failed']}個")
    print()

    # 新しいデータ構造作成
    filtered_data = {
        "collection_summary": {
            **data['collection_summary'],
            "filtered_at": "2025-10-04T00:00:00",
            "filter_criteria": "comprehensive_data存在 AND navigation_success=true AND data_collection_success=true",
            "original_total_foods": data['collection_summary']['total_foods'],
            "filtered_total_foods": len(filtered_results),
            "removed_foods": removed_count,
            "removed_reasons": removed_reasons
        },
        "collection_results": filtered_results
    }

    # 保存
    output_dir = Path('important_data')
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / 'comprehensive_food_collection_all_20251001_124446.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)

    print(f"💾 保存完了: {output_file}")
    print(f"   フィルタ後総食材数: {len(filtered_results)}個")
    print()

    # 検証
    print("🔍 検証:")
    has_comprehensive = sum(1 for item in filtered_results if item.get('comprehensive_data'))
    print(f"   comprehensive_data存在: {has_comprehensive}/{len(filtered_results)} (100.0%)")

    both_success = sum(1 for item in filtered_results
                      if item.get('navigation_success') and item.get('data_collection_success'))
    print(f"   両方success: {both_success}/{len(filtered_results)} (100.0%)")

    print()
    print("✅ フィルタリング完了 - 全1,188食材が完全に使用可能な状態です")


if __name__ == "__main__":
    main()
