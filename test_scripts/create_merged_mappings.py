#!/usr/bin/env python
"""
重複項目を適切に統合した最終版mappings.jsonを作成
"""

import json
from pathlib import Path
from collections import OrderedDict

mappings_dir = Path(__file__).parent / "mappings"

def load_and_merge_duplicates():
    """重複項目を統合しながら全baseファイルを読み込み"""
    
    unified_mappings = OrderedDict()
    merge_stats = {
        'total_items': 0,
        'duplicates_merged': 0,
        'foundation_items_added': 0,
        'survey_items': 0
    }
    
    # まずbase_1〜base_6を読み込み（Survey FNDDS）
    survey_mappings = {}
    for i in range(1, 7):
        file_path = mappings_dir / f"base_{i}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'mappings' in data:
                    mappings = data['mappings']
                else:
                    mappings = data
                
                for key, value in mappings.items():
                    if key not in survey_mappings:
                        survey_mappings[key] = value
                        merge_stats['survey_items'] += 1
    
    # base_7を読み込み（Foundation Food）
    foundation_mappings = {}
    file_path = mappings_dir / "base_7.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            foundation_mappings = data
    
    # Survey FNDDSをベースに統合
    for key, survey_item in survey_mappings.items():
        if key in foundation_mappings:
            # 重複項目を統合
            merged = merge_items(survey_item, foundation_mappings[key])
            unified_mappings[key] = merged
            merge_stats['duplicates_merged'] += 1
        else:
            # Survey FNDDSのみ
            unified_mappings[key] = survey_item
    
    # Foundation Foodのみの項目を追加
    for key, foundation_item in foundation_mappings.items():
        if key not in unified_mappings:
            unified_mappings[key] = foundation_item
            merge_stats['foundation_items_added'] += 1
    
    merge_stats['total_items'] = len(unified_mappings)
    
    return unified_mappings, merge_stats

def merge_items(survey_item, foundation_item):
    """Survey FNDDSとFoundation Foodの項目を統合"""
    
    merged = survey_item.copy()
    
    # Foundation Foodの情報を補完
    # 1. Foundation代替を追加
    if foundation_item.get('default_usda'):
        merged['foundation_alternative'] = {
            'name': foundation_item['default_usda'].get('name'),
            'database': 'foundation',
            'reason': 'Foundation Food database alternative for more specific nutrition data'
        }
    
    # 2. all_usda_mappingsを統合（重複除去）
    if 'all_usda_mappings' not in merged:
        merged['all_usda_mappings'] = []
    
    # 既存のUSDA名をセットで管理
    existing_names = {m['name'] for m in merged['all_usda_mappings']}
    
    # Foundation Foodのマッピングを追加
    for mapping in foundation_item.get('all_usda_mappings', []):
        if mapping['name'] not in existing_names:
            # databaseフィールドを確実にfoundationに
            mapping_copy = mapping.copy()
            mapping_copy['database'] = 'foundation'
            merged['all_usda_mappings'].append(mapping_copy)
            existing_names.add(mapping['name'])
    
    # 3. データベース情報を追加
    if 'databases' not in merged:
        merged['databases'] = []
    
    if 'survey_fndds' not in merged['databases']:
        merged['databases'].append('survey_fndds')
    if 'foundation' not in merged['databases']:
        merged['databases'].append('foundation')
    
    # 4. 統合情報を記録
    merged['is_merged'] = True
    merged['merge_info'] = {
        'survey_default': survey_item.get('default_usda', {}).get('name'),
        'foundation_default': foundation_item.get('default_usda', {}).get('name'),
        'survey_mappings_count': len([m for m in merged['all_usda_mappings'] if m.get('database') != 'foundation']),
        'foundation_mappings_count': len([m for m in merged['all_usda_mappings'] if m.get('database') == 'foundation'])
    }
    
    return merged

def save_merged_mappings(mappings, stats):
    """統合マッピングを保存"""
    
    output_file = mappings_dir / "mappings.json"
    
    # メタデータを追加
    output_data = {
        "_metadata": {
            "description": "Unified food name mappings with duplicate resolution",
            "source_files": [f"base_{i}.json" for i in range(1, 8)],
            "total_foods": stats['total_items'],
            "duplicates_merged": stats['duplicates_merged'],
            "survey_items": stats['survey_items'],
            "foundation_only_items": stats['foundation_items_added'],
            "databases_used": ["survey_fndds", "foundation"],
            "version": "2.0",
            "merge_strategy": "Survey FNDDS prioritized with Foundation Food supplementation"
        },
        "mappings": mappings
    }
    
    # バックアップを作成
    if output_file.exists():
        backup_path = output_file.with_suffix('.json.backup_v2')
        with open(output_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        print(f"💾 既存ファイルのバックアップ作成: {backup_path.name}")
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 統合ファイルを保存: {output_file}")
    print(f"   ファイルサイズ: {output_file.stat().st_size:,} bytes")
    
    return output_file

def main():
    print("="*80)
    print("重複を統合した最終版mappings.json作成")
    print("="*80)
    print()
    
    # 重複を統合しながら読み込み
    print("📚 ファイルを読み込み、重複を統合中...")
    unified_mappings, stats = load_and_merge_duplicates()
    
    # 統計を表示
    print()
    print("📊 統合結果:")
    print(f"  総項目数: {stats['total_items']}")
    print(f"  Survey FNDDS項目: {stats['survey_items']}")
    print(f"  Foundation Food専用項目: {stats['foundation_items_added']}")
    print(f"  統合された重複項目: {stats['duplicates_merged']}")
    
    # ファイルに保存
    output_file = save_merged_mappings(unified_mappings, stats)
    
    print()
    print("="*80)
    print("✅ 統合完了")
    print("="*80)
    print()
    print(f"最終項目数: {stats['total_items']}")
    print("特徴:")
    print("  - 重複項目は両データベースの情報を統合")
    print("  - foundation_alternativeフィールドでFoundation版を保持")
    print("  - all_usda_mappingsに両データベースの項目を含む")
    print("  - is_mergedフラグで統合項目を識別")

if __name__ == "__main__":
    main()
