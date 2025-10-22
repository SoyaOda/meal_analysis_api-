#!/usr/bin/env python
"""
重複項目を分析して適切に統合する
"""

import json
from pathlib import Path
from collections import defaultdict

mappings_dir = Path(__file__).parent / "mappings"

def load_all_bases():
    """全baseファイルを読み込み"""
    all_data = {}
    
    for i in range(1, 8):
        file_path = mappings_dir / f"base_{i}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'mappings' in data:
                    all_data[f"base_{i}"] = data['mappings']
                else:
                    all_data[f"base_{i}"] = data
    
    return all_data

def find_duplicates(all_data):
    """重複項目を特定"""
    item_locations = defaultdict(list)
    
    for base_name, mappings in all_data.items():
        for key in mappings.keys():
            item_locations[key].append(base_name)
    
    duplicates = {k: v for k, v in item_locations.items() if len(v) > 1}
    return duplicates

def analyze_duplicate(key, all_data, locations):
    """重複項目の詳細分析"""
    print(f"\n{'='*80}")
    print(f"🔍 重複項目: {key}")
    print(f"   出現場所: {', '.join(locations)}")
    print("-"*80)
    
    comparison = {}
    
    for location in locations:
        base_num = location.replace("base_", "")
        item = all_data[location][key]
        
        print(f"\n📁 {location}:")
        
        # デフォルトUSDA
        if 'default_usda' in item and item['default_usda']:
            default = item['default_usda']
            print(f"  default_usda:")
            print(f"    name: {default.get('name', 'N/A')}")
            print(f"    database: {default.get('database', 'N/A')}")
            
            comparison[location] = {
                'default_name': default.get('name'),
                'default_db': default.get('database'),
                'all_mappings_count': len(item.get('all_usda_mappings', []))
            }
        
        # all_usda_mappingsの数
        if 'all_usda_mappings' in item:
            print(f"  all_usda_mappings: {len(item['all_usda_mappings'])} 項目")
            # 最初の2つを表示
            for idx, mapping in enumerate(item['all_usda_mappings'][:2]):
                print(f"    - {mapping.get('name', 'N/A')} ({mapping.get('database', 'N/A')})")
            if len(item['all_usda_mappings']) > 2:
                print(f"    ... 他 {len(item['all_usda_mappings']) - 2} 項目")
    
    return comparison

def merge_duplicate_items(key, all_data, locations):
    """重複項目を適切に統合"""
    merged = {}
    
    # 基本構造を最初の項目から取得
    base_item = all_data[locations[0]][key].copy()
    
    # Survey FNDDSを優先（base_1-6）、Foundation Foodは補完
    survey_item = None
    foundation_item = None
    
    for location in locations:
        if location in ['base_1', 'base_2', 'base_3', 'base_4', 'base_5', 'base_6']:
            survey_item = all_data[location][key]
        elif location == 'base_7':
            foundation_item = all_data[location][key]
    
    # Survey FNDDSをベースとして使用
    if survey_item:
        merged = survey_item.copy()
        
        # Foundation Foodの情報を補完
        if foundation_item:
            # all_usda_mappingsを統合（重複除去）
            if 'all_usda_mappings' not in merged:
                merged['all_usda_mappings'] = []
            
            existing_names = {m['name'] for m in merged.get('all_usda_mappings', [])}
            
            for mapping in foundation_item.get('all_usda_mappings', []):
                if mapping['name'] not in existing_names:
                    # Foundationデータベースの項目を追加
                    merged['all_usda_mappings'].append(mapping)
            
            # Foundation専用フィールドを追加
            if 'foundation_alternative' not in merged:
                merged['foundation_alternative'] = {
                    'name': foundation_item.get('default_usda', {}).get('name'),
                    'database': 'foundation',
                    'reason': 'Foundation Food database alternative'
                }
    else:
        # Foundation Foodのみの場合はそのまま使用
        merged = foundation_item.copy() if foundation_item else base_item
    
    return merged

def main():
    print("="*80)
    print("重複項目の分析と統合")
    print("="*80)
    
    # 全baseファイルを読み込み
    all_data = load_all_bases()
    
    # 重複を検出
    duplicates = find_duplicates(all_data)
    
    print(f"\n📊 重複項目数: {len(duplicates)}")
    print(f"   項目: {', '.join(list(duplicates.keys())[:10])}")
    if len(duplicates) > 10:
        print(f"   ... 他 {len(duplicates) - 10} 項目")
    
    # 詳細分析（最初の5つ）
    for key in list(duplicates.keys())[:5]:
        analyze_duplicate(key, all_data, duplicates[key])
    
    print("\n" + "="*80)
    print("📝 統合戦略")
    print("="*80)
    print("""
    1. Survey FNDDS (base_1-6) を優先
    2. Foundation Food (base_7) の情報を補完として追加
    3. all_usda_mappingsは両方のデータベースから統合（重複除去）
    4. foundation_alternativeフィールドでFoundation版を保持
    """)
    
    # 統合処理の実行
    merge_count = 0
    for key, locations in duplicates.items():
        merged = merge_duplicate_items(key, all_data, locations)
        # 最初の出現場所に統合版を保存
        all_data[locations[0]][key] = merged
        merge_count += 1
    
    print(f"\n✅ {merge_count} 件の重複項目を統合しました")
    
    return all_data, duplicates

if __name__ == "__main__":
    all_data, duplicates = main()
    
    # 統合情報をファイルに保存
    with open(mappings_dir / "duplicate_analysis.json", 'w', encoding='utf-8') as f:
        json.dump({
            'duplicates': duplicates,
            'merge_count': len(duplicates)
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 分析結果を保存: duplicate_analysis.json")
