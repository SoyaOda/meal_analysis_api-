#!/usr/bin/env python
"""
base_7.jsonの全てのdatabaseフィールドを"foundation"に変更
"""

import json
from pathlib import Path

base7_file = Path(__file__).parent / "mappings" / "base_7.json"

def fix_database_fields():
    """全てのdatabaseフィールドをfoundationに変更"""
    
    print("📚 base_7.jsonを読み込み中...")
    with open(base7_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changes_count = 0
    
    # 各マッピングを処理
    for key, mapping in data.items():
        # default_usdaのdatabaseを修正
        if 'default_usda' in mapping and mapping['default_usda']:
            if 'database' in mapping['default_usda']:
                old_db = mapping['default_usda']['database']
                if old_db != 'foundation':
                    mapping['default_usda']['database'] = 'foundation'
                    changes_count += 1
                    print(f"  ✅ {key} (default_usda): {old_db} → foundation")
        
        # all_usda_mappingsのdatabaseを修正
        if 'all_usda_mappings' in mapping:
            for item in mapping['all_usda_mappings']:
                if 'database' in item:
                    old_db = item['database']
                    if old_db != 'foundation':
                        item['database'] = 'foundation'
                        changes_count += 1
    
    print(f"\n📊 総変更数: {changes_count} 件")
    
    # バックアップを作成
    backup_path = base7_file.with_suffix('.json.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 バックアップ作成: {backup_path}")
    
    # 修正版を保存
    with open(base7_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 修正版を保存: {base7_file}")
    
    return changes_count

def main():
    print("="*80)
    print("base_7.jsonのdatabaseフィールドをfoundationに統一")
    print("="*80)
    print()
    
    if not base7_file.exists():
        print(f"❌ {base7_file} が見つかりません")
        return
    
    changes = fix_database_fields()
    
    print("\n" + "="*80)
    if changes > 0:
        print(f"✅ {changes} 件のdatabaseフィールドをfoundationに変更しました")
    else:
        print("✅ すべてのdatabaseフィールドは既にfoundationです")
    print("="*80)

if __name__ == "__main__":
    main()
