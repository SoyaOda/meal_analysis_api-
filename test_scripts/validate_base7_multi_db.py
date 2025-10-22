#!/usr/bin/env python
"""
base_7.jsonのUSDA名を各databaseフィールドに応じて適切なデータベースで検証
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# パス設定
project_root = Path(__file__).parent.parent
usda_names_dir = project_root / "usda_database" / "names_list"
base7_file = Path(__file__).parent / "mappings" / "base_7.json"

def load_usda_databases():
    """すべてのUSDAデータベースファイルを読み込み"""
    db_files = {
        'survey_fndds': 'survey_food_names.txt',
        'sr_legacy': 'sr_legacy_food_names.txt',
        'foundation': 'foundation_food_names.txt',
        'branded': 'branded_food_names.txt'
    }
    
    all_databases = {}
    
    for db_name, file_name in db_files.items():
        db_path = usda_names_dir / file_name
        food_names = set()
        
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # 行頭の番号とドットを除去
                        match = re.match(r'^\d+\.\s+(.+)$', line)
                        if match:
                            food_name = match.group(1)
                            food_names.add(food_name)
                        else:
                            food_names.add(line)
            
            print(f"✅ {db_name}: {len(food_names):,} 項目を読み込み")
        else:
            print(f"⚠️  {db_name}: ファイルが見つかりません")
        
        all_databases[db_name] = food_names
    
    return all_databases

def validate_base7_file(file_path, databases):
    """base_7.json内の名前をdatabaseに応じて検証"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        mappings = json.load(f)
    
    # 検証結果
    results = {
        'total': 0,
        'found': 0,
        'not_found': [],
        'database_stats': defaultdict(lambda: {'total': 0, 'found': 0}),
        'names_checked': []
    }
    
    # 各マッピングの名前をチェック
    for key, mapping in mappings.items():
        # デフォルトのUSDA名を確認
        if 'default_usda' in mapping and mapping['default_usda']:
            name = mapping['default_usda'].get('name')
            database = mapping['default_usda'].get('database', 'unknown')
            
            if name:
                results['total'] += 1
                results['database_stats'][database]['total'] += 1
                results['names_checked'].append(name)
                
                # 指定されたデータベースで検証
                if database in databases and name in databases[database]:
                    results['found'] += 1
                    results['database_stats'][database]['found'] += 1
                else:
                    results['not_found'].append({
                        'key': key,
                        'name': name,
                        'database': database,
                        'field': 'default_usda'
                    })
        
        # all_usda_mappings内の名前も確認
        if 'all_usda_mappings' in mapping:
            for item in mapping['all_usda_mappings']:
                if 'name' in item:
                    name = item['name']
                    database = item.get('database', 'unknown')
                    
                    results['total'] += 1
                    results['database_stats'][database]['total'] += 1
                    results['names_checked'].append(name)
                    
                    if database in databases and name in databases[database]:
                        results['found'] += 1
                        results['database_stats'][database]['found'] += 1
                    else:
                        results['not_found'].append({
                            'key': key,
                            'name': name,
                            'database': database,
                            'field': 'all_usda_mappings'
                        })
    
    return results

def main():
    print("="*80)
    print("base_7.jsonのマルチデータベース検証")
    print("="*80)
    print()
    
    # すべてのUSDAデータベースを読み込み
    print("📚 USDAデータベースを読み込み中...")
    databases = load_usda_databases()
    
    total_items = sum(len(names) for names in databases.values())
    print(f"\n✅ 総USDA項目数: {total_items:,}")
    print()
    
    # base_7.jsonを検証
    if not base7_file.exists():
        print(f"❌ {base7_file} が見つかりません")
        return
    
    print(f"📋 検証中: {base7_file.name}")
    print("-"*40)
    
    results = validate_base7_file(base7_file, databases)
    
    if results:
        # ファイルごとの結果表示
        percentage = (results['found'] / results['total'] * 100) if results['total'] > 0 else 0
        print(f"  検証項目数: {results['total']}")
        print(f"  ✅ 存在: {results['found']} ({percentage:.1f}%)")
        
        # データベース別統計
        print(f"\n  データベース別統計:")
        for db_name, stats in sorted(results['database_stats'].items()):
            db_percentage = (stats['found'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"    {db_name}: {stats['found']}/{stats['total']} ({db_percentage:.1f}%)")
        
        if results['not_found']:
            print(f"\n  ❌ 存在しない: {len(results['not_found'])} 件")
            print()
            
            # すべての存在しない項目を表示
            for item in results['not_found'][:20]:
                print(f"     - {item['key']}: \"{item['name']}\" ({item['database']}, {item['field']})")
            
            if len(results['not_found']) > 20:
                print(f"     ... 他 {len(results['not_found']) - 20} 件")
            
            # ユニークな名前を集計
            unique_names = {}
            for item in results['not_found']:
                if item['name'] not in unique_names:
                    unique_names[item['name']] = []
                unique_names[item['name']].append(f"{item['key']}:{item['database']}:{item['field']}")
            
            print(f"\n  ユニークな存在しない名前: {len(unique_names)} 件")
    
    # 総合結果
    print("\n" + "="*80)
    if results and len(results['not_found']) == 0:
        print("✅ すべての名前が対応するUSDAデータベースに存在します！")
    else:
        print(f"❌ {len(results['not_found'])} 件の名前が対応するデータベースに存在しません。")
    print("="*80)
    
    # エラー詳細をファイルに保存
    if results and results['not_found']:
        error_file = base7_file.parent / "base_7_multi_db_validation_errors.json"
        
        # ユニークな名前を集計
        unique_names = {}
        for item in results['not_found']:
            if item['name'] not in unique_names:
                unique_names[item['name']] = []
            unique_names[item['name']].append(f"{item['key']}:{item['database']}:{item['field']}")
        
        error_data = {
            'summary': {
                'total': results['total'],
                'found': results['found'],
                'not_found': len(results['not_found']),
                'unique_not_found': len(unique_names),
                'database_stats': dict(results['database_stats'])
            },
            'not_found_items': results['not_found'],
            'unique_names': {name: locs for name, locs in unique_names.items()}
        }
        
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 エラー詳細を保存: {error_file}")

if __name__ == "__main__":
    main()
