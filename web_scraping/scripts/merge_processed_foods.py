#!/usr/bin/env python3
"""
メインのprocessed foodsとmanual processed foodsを統合するスクリプト
"""

import os
import json
from pathlib import Path
from datetime import datetime


def merge_processed_foods(main_file: str, manual_file: str, output_dir: str) -> str:
    """2つのprocessed foodsファイルを統合"""

    # データ読み込み
    with open(main_file, 'r', encoding='utf-8') as f:
        main_data = json.load(f)

    with open(manual_file, 'r', encoding='utf-8') as f:
        manual_data = json.load(f)

    # 統合
    merged_foods = main_data['foods'] + manual_data['foods']

    # food_idを再採番
    for i, food in enumerate(merged_foods, 1):
        food['food_id'] = f"food_{i:04d}"

    # カテゴリ別統計を計算
    category_stats = {}
    for food in merged_foods:
        cat = food['category']
        if cat not in category_stats:
            category_stats[cat] = {
                'count': 0,
                'avg_nutrition': 0,
                'avg_serving': 0
            }
        category_stats[cat]['count'] += 1
        category_stats[cat]['avg_nutrition'] += food['nutrition_facts']['total_nutrients']
        category_stats[cat]['avg_serving'] += food['serving_options']['total_servings']

    # 平均値計算
    for cat in category_stats:
        count = category_stats[cat]['count']
        category_stats[cat]['avg_nutrition'] /= count
        category_stats[cat]['avg_serving'] /= count

    # 統合データ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    merged_data = {
        'metadata': {
            'version': '1.0',
            'processed_at': datetime.now().isoformat(),
            'total_foods': len(merged_foods),
            'sources': [
                {
                    'type': 'web_scraping',
                    'file': os.path.basename(main_file),
                    'count': len(main_data['foods'])
                },
                {
                    'type': 'manual_entry',
                    'file': os.path.basename(manual_file),
                    'count': len(manual_data['foods'])
                }
            ],
            'processing_notes': 'Merged web-scraped and manually entered foods'
        },
        'foods': merged_foods
    }

    # 保存
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"all_foods_processed_{timestamp}.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    # サマリーファイルも作成
    summary_data = {
        'total_processed_foods': len(merged_foods),
        'category_breakdown': category_stats,
        'processing_timestamp': datetime.now().isoformat(),
        'sources': merged_data['metadata']['sources']
    }

    summary_file = os.path.join(output_dir, f"all_foods_summary_{timestamp}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    return output_file, summary_file, category_stats


def main():
    base_dir = Path('.')
    processed_dir = base_dir / 'processed_data'

    # 最新のファイルを使用
    main_file = processed_dir / 'processed_foods_20251003_103644.json'
    manual_file = processed_dir / 'manual_foods_processed_20251003_111122.json'

    print("🔄 Processed Foodsの統合")
    print("=" * 60)
    print(f"📁 メインファイル: {main_file.name}")
    print(f"📁 手作業ファイル: {manual_file.name}")

    # 統合実行
    output_file, summary_file, category_stats = merge_processed_foods(
        str(main_file),
        str(manual_file),
        str(processed_dir)
    )

    print(f"\n✅ 統合完了!")
    print(f"   📄 統合データ: {os.path.basename(output_file)}")
    print(f"   📄 サマリー: {os.path.basename(summary_file)}")

    # 統計表示
    with open(output_file, 'r', encoding='utf-8') as f:
        merged_data = json.load(f)

    print("\n" + "=" * 60)
    print("📊 統合結果")
    print("=" * 60)

    for source in merged_data['metadata']['sources']:
        print(f"\n📁 {source['type']}:")
        print(f"   ファイル: {source['file']}")
        print(f"   食材数: {source['count']}個")

    print(f"\n合計食材数: {merged_data['metadata']['total_foods']}個")

    print(f"\n📂 カテゴリ別内訳:")
    sorted_cats = sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    for cat, stats in sorted_cats:
        print(f"   {cat}: {stats['count']}個")
        print(f"      平均栄養素: {stats['avg_nutrition']:.1f}個")
        print(f"      平均サービング: {stats['avg_serving']:.1f}個")


if __name__ == "__main__":
    main()
