#!/usr/bin/env python
"""
Foundation Food (base_7) を優先した統合マッピングを作成
"""

import json
from pathlib import Path
from collections import OrderedDict

mappings_dir = Path(__file__).parent / "mappings"

def load_and_merge_with_foundation_priority():
    """Foundation Foodを優先して重複項目を統合"""
    
    unified_mappings = OrderedDict()
    merge_stats = {
        'total_items': 0,
        'duplicates_replaced': 0,
        'survey_only_items': 0,
        'foundation_items': 0
    }
    
    # まずbase_7を読み込み（Foundation Food - 優先）
    foundation_mappings = {}
    file_path = mappings_dir / "base_7.json"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            foundation_mappings = json.load(f)
            merge_stats['foundation_items'] = len(foundation_mappings)
    
    # Foundation Foodを先に追加
    for key, value in foundation_mappings.items():
        unified_mappings[key] = value
    
    # base_1〜base_6を読み込み（Survey FNDDS）
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
                    if key in foundation_mappings:
                        # 重複項目 - Foundation優先だが、Survey情報を補完として追加
                        merged = merge_with_foundation_priority(foundation_mappings[key], value)
                        unified_mappings[key] = merged
                        merge_stats['duplicates_replaced'] += 1
                    elif key not in unified_mappings:
                        # Survey FNDDSのみの項目
                        unified_mappings[key] = value
                        merge_stats['survey_only_items'] += 1
    
    merge_stats['total_items'] = len(unified_mappings)
    
    return unified_mappings, merge_stats

def merge_with_foundation_priority(foundation_item, survey_item):
    """Foundation Foodを優先し、Survey FNDDSを補完として統合"""
    
    # Foundation Foodをベースとする
    merged = foundation_item.copy()
    
    # Survey FNDDSの情報を補完として追加
    merged['survey_alternative'] = {
        'name': survey_item.get('default_usda', {}).get('name'),
        'database': 'survey_fndds',
        'reason': 'Survey FNDDS alternative for broader compatibility'
    }
    
    # all_usda_mappingsを統合（Foundation優先）
    if 'all_usda_mappings' not in merged:
        merged['all_usda_mappings'] = []
    
    # Foundation Foodのマッピングを最初に配置
    foundation_mappings = merged['all_usda_mappings'].copy()
    
    # Survey FNDDSのマッピングを追加（重複除去）
    existing_names = {m['name'] for m in foundation_mappings}
    
    for mapping in survey_item.get('all_usda_mappings', []):
        if mapping['name'] not in existing_names:
            # Survey FNDDSの項目を追加
            mapping_copy = mapping.copy()
            if 'database' not in mapping_copy or mapping_copy['database'] != 'survey_fndds':
                mapping_copy['database'] = 'survey_fndds'
            foundation_mappings.append(mapping_copy)
            existing_names.add(mapping['name'])
    
    merged['all_usda_mappings'] = foundation_mappings
    
    # データベース情報を追加
    merged['databases'] = ['foundation', 'survey_fndds']
    
    # 統合情報を記録
    merged['is_merged'] = True
    merged['merge_info'] = {
        'primary_database': 'foundation',
        'foundation_default': foundation_item.get('default_usda', {}).get('name'),
        'survey_default': survey_item.get('default_usda', {}).get('name'),
        'foundation_mappings_count': len([m for m in merged['all_usda_mappings'] if m.get('database') == 'foundation']),
        'survey_mappings_count': len([m for m in merged['all_usda_mappings'] if m.get('database') == 'survey_fndds'])
    }
    
    return merged

def save_foundation_priority_mappings(mappings, stats):
    """Foundation優先の統合マッピングを保存"""
    
    output_file = mappings_dir / "mappings.json"
    
    # メタデータを追加
    output_data = {
        "_metadata": {
            "description": "Unified food name mappings with Foundation Food priority",
            "source_files": [f"base_{i}.json" for i in range(1, 8)],
            "total_foods": stats['total_items'],
            "foundation_items": stats['foundation_items'],
            "survey_only_items": stats['survey_only_items'],
            "duplicates_with_foundation_priority": stats['duplicates_replaced'],
            "databases_used": ["foundation", "survey_fndds"],
            "priority": "Foundation Food database prioritized for accuracy",
            "version": "3.0",
            "merge_strategy": "Foundation Food prioritized with Survey FNDDS as fallback"
        },
        "mappings": mappings
    }
    
    # バックアップを作成
    if output_file.exists():
        backup_path = output_file.with_suffix('.json.backup_v3')
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
    print("Foundation Food優先の統合マッピング作成")
    print("="*80)
    print()
    
    # Foundation Foodを優先して統合
    print("📚 Foundation Foodを優先して統合中...")
    unified_mappings, stats = load_and_merge_with_foundation_priority()
    
    # 統計を表示
    print()
    print("📊 統合結果:")
    print(f"  総項目数: {stats['total_items']}")
    print(f"  Foundation Food項目: {stats['foundation_items']}")
    print(f"  Survey FNDDS専用項目: {stats['survey_only_items']}")
    print(f"  Foundation優先で置換された重複: {stats['duplicates_replaced']}")
    
    # ファイルに保存
    output_file = save_foundation_priority_mappings(unified_mappings, stats)
    
    print()
    print("="*80)
    print("✅ Foundation Food優先での統合完了")
    print("="*80)
    print()
    print(f"最終項目数: {stats['total_items']}")
    print()
    print("特徴:")
    print("  🎯 Foundation Foodを優先（より正確な栄養データ）")
    print("  📊 重複項目はFoundation版をdefault_usdaに設定")
    print("  🔄 Survey FNDDS版はsurvey_alternativeとして保持")
    print("  📝 all_usda_mappingsにFoundationを先頭に配置")

if __name__ == "__main__":
    main()
