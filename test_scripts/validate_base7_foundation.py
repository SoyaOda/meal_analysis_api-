#!/usr/bin/env python
"""
base_7.jsonのすべてのUSDA名がfoundation_food_names.txtに存在するか検証
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# パス設定
project_root = Path(__file__).parent.parent
foundation_file = project_root / "usda_database" / "names_list" / "foundation_food_names.txt"
base7_file = Path(__file__).parent / "mappings" / "base_7.json"

def load_foundation_database():
    """foundation_food_names.txtから食品名を抽出"""
    print(f"📚 foundation_food_names.txtを読み込み中...")
    
    if not foundation_file.exists():
        print(f"❌ ファイルが見つかりません: {foundation_file}")
        return None
    
    food_names = set()
    
    with open(foundation_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                # 行頭の番号とドットを除去（例: "123. Food name" -> "Food name"）
                match = re.match(r'^\d+\.\s+(.+)$', line)
                if match:
                    food_name = match.group(1)
                    food_names.add(food_name)
                else:
                    # 番号がない場合はそのまま使用
                    food_names.add(line)
    
    print(f"✅ {len(food_names):,} 個の食品名を読み込みました")
    return food_names

def validate_base7_file(file_path, foundation_names):
    """base_7.json内の名前を検証"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # マッピング構造を確認
    if isinstance(data, dict):
        if 'mappings' in data:
            mappings = data['mappings']
        else:
            mappings = data
    else:
        print(f"⚠️  予期しない構造")
        return None
    
    # 検証結果
    results = {
        'total': 0,
        'found': 0,
        'not_found': [],
        'names_checked': []
    }
    
    # 各マッピングの名前をチェック
    for key, mapping in mappings.items():
        # デフォルトのUSDA名を確認
        if 'default_usda' in mapping and mapping['default_usda']:
            name = mapping['default_usda'].get('name')
            if name:
                results['total'] += 1
                results['names_checked'].append(name)
                if name in foundation_names:
                    results['found'] += 1
                else:
                    results['not_found'].append({
                        'key': key,
                        'name': name,
                        'field': 'default_usda'
                    })
        
        # all_usda_mappings内の名前も確認
        if 'all_usda_mappings' in mapping:
            for item in mapping['all_usda_mappings']:
                if 'name' in item:
                    name = item['name']
                    results['total'] += 1
                    results['names_checked'].append(name)
                    if name in foundation_names:
                        results['found'] += 1
                    else:
                        results['not_found'].append({
                            'key': key,
                            'name': name,
                            'field': 'all_usda_mappings'
                        })
    
    return results

def main():
    print("="*80)
    print("base_7.jsonのfoundation_food_names.txt検証")
    print("="*80)
    print()
    
    # foundation_food_names.txtを読み込み
    foundation_names = load_foundation_database()
    
    if not foundation_names:
        print("❌ foundation_food_names.txtの読み込みに失敗しました")
        return
    
    print()
    
    # base_7.jsonを検証
    if not base7_file.exists():
        print(f"❌ {base7_file} が見つかりません")
        return
    
    print(f"📋 検証中: {base7_file.name}")
    print("-"*40)
    
    results = validate_base7_file(base7_file, foundation_names)
    
    if results:
        # ファイルごとの結果表示
        percentage = (results['found'] / results['total'] * 100) if results['total'] > 0 else 0
        print(f"  検証項目数: {results['total']}")
        print(f"  ✅ 存在: {results['found']} ({percentage:.1f}%)")
        
        if results['not_found']:
            print(f"  ❌ 存在しない: {len(results['not_found'])} 件")
            print()
            
            # すべての存在しない項目を表示
            for item in results['not_found'][:20]:
                print(f"     - {item['key']}: \"{item['name']}\" ({item['field']})")
            
            if len(results['not_found']) > 20:
                print(f"     ... 他 {len(results['not_found']) - 20} 件")
            
            # ユニークな名前を集計
            unique_names = {}
            for item in results['not_found']:
                if item['name'] not in unique_names:
                    unique_names[item['name']] = []
                unique_names[item['name']].append(f"{item['key']}:{item['field']}")
            
            print(f"\n  ユニークな存在しない名前: {len(unique_names)} 件")
    
    # 総合結果
    print("\n" + "="*80)
    if results and len(results['not_found']) == 0:
        print("✅ すべての名前がfoundation_food_names.txtに存在します！")
    else:
        print(f"❌ {len(results['not_found'])} 件の名前がfoundation_food_names.txtに存在しません。")
    print("="*80)
    
    # エラー詳細をファイルに保存
    if results and results['not_found']:
        error_file = base7_file.parent / "base_7_validation_errors.json"
        
        # ユニークな名前を集計
        unique_names = {}
        for item in results['not_found']:
            if item['name'] not in unique_names:
                unique_names[item['name']] = []
            unique_names[item['name']].append(f"{item['key']}:{item['field']}")
        
        error_data = {
            'summary': {
                'total': results['total'],
                'found': results['found'],
                'not_found': len(results['not_found']),
                'unique_not_found': len(unique_names)
            },
            'not_found_items': results['not_found'],
            'unique_names': {name: locs for name, locs in unique_names.items()}
        }
        
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 エラー詳細を保存: {error_file}")

if __name__ == "__main__":
    main()
