#!/usr/bin/env python3
"""
complete_food_database.json と complete_1to1_mappings.json の食材名を比較し、
片方にのみ含まれる食材や重複をまとめるスクリプト

Usage:
    python compare_database_and_mappings.py
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def normalize_food_name(name: str) -> str:
    """食材名を正規化（比較用）

    - 改行を空白に置換（データベース形式: 'Name\\nXXXcals' を 'Name XXXcals' に）
    - 前後の空白を削除
    - 小文字化
    """
    return name.replace('\n', ' ').strip().lower()


def load_database_foods(db_file: Path) -> dict:
    """complete_food_database.jsonから食材情報を読み込む"""
    with open(db_file, 'r', encoding='utf-8') as f:
        db_data = json.load(f)

    db_foods = {}
    for food in db_data['foods']:
        food_name = food['food_name']
        db_foods[food_name] = {
            'sequence': food['sequence'],
            'category': food['catalog_category'],
            'normalized': normalize_food_name(food_name)
        }

    return db_foods


def load_mapping_foods(mapping_file: Path) -> dict:
    """complete_1to1_mappings.jsonから食材情報を読み込む"""
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)

    mapping_foods = defaultdict(list)
    for mapping in mapping_data['mappings']:
        # final_food_nameを使用
        food_name = mapping.get('final_food_name', '')
        if food_name:
            mapping_foods[food_name].append({
                'stemmed_id': mapping.get('stemmed_id', ''),
                'stemmed_name': mapping.get('stemmed_name', ''),
                'final_food_id': mapping.get('final_food_id', ''),
                'normalized': normalize_food_name(food_name)
            })

    return mapping_foods


def compare_foods(db_foods: dict, mapping_foods: dict) -> dict:
    """2つのデータセットを比較

    正規化された食材名で比較を行う
    """
    # 正規化された名前でマッピングを作成
    db_normalized = {info['normalized']: name for name, info in db_foods.items()}
    mapping_normalized = {entries[0]['normalized']: name for name, entries in mapping_foods.items()}

    # 正規化名で比較
    common_normalized = set(db_normalized.keys()) & set(mapping_normalized.keys())
    db_only_normalized = set(db_normalized.keys()) - set(mapping_normalized.keys())
    mapping_only_normalized = set(mapping_normalized.keys()) - set(db_normalized.keys())

    # 元の名前に戻す
    common = {db_normalized[norm] for norm in common_normalized}
    db_only = {db_normalized[norm] for norm in db_only_normalized}
    mapping_only = {mapping_normalized[norm] for norm in mapping_only_normalized}

    return {
        'common': common,
        'db_only': db_only,
        'mapping_only': mapping_only,
        'duplicates_in_mapping': {
            name: entries for name, entries in mapping_foods.items()
            if len(entries) > 1
        }
    }


def generate_report(db_foods: dict, mapping_foods: dict, comparison: dict, output_file: Path):
    """詳細レポートを生成"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_in_database': len(db_foods),
            'total_in_mappings': len(mapping_foods),
            'total_mapping_entries': sum(len(entries) for entries in mapping_foods.values()),
            'common_foods': len(comparison['common']),
            'database_only': len(comparison['db_only']),
            'mapping_only': len(comparison['mapping_only']),
            'duplicates_in_mapping': len(comparison['duplicates_in_mapping'])
        },
        'database_only_foods': [],
        'mapping_only_foods': [],
        'duplicates_in_mapping': []
    }

    # データベースのみの食材
    for food_name in sorted(comparison['db_only']):
        info = db_foods[food_name]
        report['database_only_foods'].append({
            'food_name': food_name,
            'sequence': info['sequence'],
            'category': info['category']
        })

    # マッピングのみの食材
    for food_name in sorted(comparison['mapping_only']):
        entries = mapping_foods[food_name]
        report['mapping_only_foods'].append({
            'food_name': food_name,
            'mapping_count': len(entries),
            'mappings': entries
        })

    # マッピング内の重複
    for food_name, entries in sorted(comparison['duplicates_in_mapping'].items()):
        report['duplicates_in_mapping'].append({
            'food_name': food_name,
            'duplicate_count': len(entries),
            'in_database': food_name in db_foods,
            'mappings': entries
        })

    # レポート保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def print_summary(report: dict):
    """サマリーを出力"""
    print("=" * 80)
    print("食材データベースとマッピングの比較レポート")
    print("=" * 80)
    print(f"\n【サマリー】")
    print(f"データベース総食材数: {report['summary']['total_in_database']:,}")
    print(f"マッピング総食材数: {report['summary']['total_in_mappings']:,}")
    print(f"マッピング総エントリ数: {report['summary']['total_mapping_entries']:,}")
    print(f"\n両方に存在: {report['summary']['common_foods']:,} 食材")
    print(f"データベースのみ: {report['summary']['database_only']:,} 食材")
    print(f"マッピングのみ: {report['summary']['mapping_only']:,} 食材")
    print(f"マッピング内重複: {report['summary']['duplicates_in_mapping']:,} 食材")

    # データベースのみの食材（最初の20件）
    if report['database_only_foods']:
        print(f"\n【データベースのみに存在する食材（最初の20件）】")
        for i, food in enumerate(report['database_only_foods'][:20], 1):
            name = food['food_name']
            truncated_name = name[:60] + "..." if len(name) > 60 else name
            print(f"{i}. {truncated_name}")
            print(f"   Sequence: {food['sequence']}, Category: {food['category']}")

        if len(report['database_only_foods']) > 20:
            print(f"... 他 {len(report['database_only_foods']) - 20} 件")

    # マッピングのみの食材（最初の20件）
    if report['mapping_only_foods']:
        print(f"\n【マッピングのみに存在する食材（最初の20件）】")
        for i, food in enumerate(report['mapping_only_foods'][:20], 1):
            name = food['food_name']
            truncated_name = name[:60] + "..." if len(name) > 60 else name
            print(f"{i}. {truncated_name}")
            print(f"   マッピング数: {food['mapping_count']}")

        if len(report['mapping_only_foods']) > 20:
            print(f"... 他 {len(report['mapping_only_foods']) - 20} 件")

    # マッピング内の重複（最初の10件）
    if report['duplicates_in_mapping']:
        print(f"\n【マッピング内で重複している食材（最初の10件）】")
        for i, dup in enumerate(report['duplicates_in_mapping'][:10], 1):
            name = dup['food_name']
            truncated_name = name[:60] + "..." if len(name) > 60 else name
            in_db = "✓ DB内" if dup['in_database'] else "✗ DB外"
            print(f"{i}. {truncated_name} ({dup['duplicate_count']} 重複, {in_db})")
            for j, mapping in enumerate(dup['mappings'][:3], 1):
                stemmed_name = mapping.get('stemmed_name', '')[:50]
                final_id = mapping.get('final_food_id', 'N/A')
                print(f"   {j}) {stemmed_name} ({final_id})")

        if len(report['duplicates_in_mapping']) > 10:
            print(f"... 他 {len(report['duplicates_in_mapping']) - 10} 件")


def main():
    # ファイルパス
    base_dir = Path('/Users/odasoya/meal_analysis_api_2/web_scraping')
    db_file = base_dir / 'important_data' / 'complete_food_database.json'
    mapping_file = base_dir / 'processed_data' / 'complete_1to1_mappings.json'
    output_file = base_dir / 'important_data' / 'database_mapping_comparison_report.json'

    # データ読み込み
    print("データ読み込み中...")
    db_foods = load_database_foods(db_file)
    mapping_foods = load_mapping_foods(mapping_file)

    # 比較実行
    print("比較分析中...")
    comparison = compare_foods(db_foods, mapping_foods)

    # レポート生成
    print("レポート生成中...")
    report = generate_report(db_foods, mapping_foods, comparison, output_file)

    # サマリー出力
    print_summary(report)

    print(f"\n詳細レポート保存先: {output_file}")
    print("\n完了！")


if __name__ == '__main__':
    main()
