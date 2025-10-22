#!/usr/bin/env python
"""
base_1〜base_5.jsonの無効なUSDA名を修正対応表に従って更新
"""

import json
from pathlib import Path

# パス設定
mappings_dir = Path(__file__).parent / "mappings"
corrections_file = mappings_dir / "base_files_corrections_final.json"

def load_corrections():
    """修正対応表を読み込み"""
    with open(corrections_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['corrections']

def apply_corrections_to_file(file_path, corrections):
    """ファイルに修正を適用"""
    print(f"\n📝 処理中: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # mappings構造を確認
    if 'mappings' in data:
        mappings = data['mappings']
    else:
        mappings = data
    
    corrections_applied = 0
    
    # 各マッピングをチェックして修正
    for key, mapping in mappings.items():
        # default_usdaをチェック
        if 'default_usda' in mapping and mapping['default_usda']:
            name = mapping['default_usda'].get('name')
            if name and name in corrections:
                old_name = name
                new_name = corrections[name]['corrected']
                mapping['default_usda']['name'] = new_name
                print(f"  ✅ {key}: \"{old_name}\" → \"{new_name}\"")
                corrections_applied += 1
        
        # all_usda_mappingsをチェック
        if 'all_usda_mappings' in mapping:
            for item in mapping['all_usda_mappings']:
                if 'name' in item:
                    name = item['name']
                    if name in corrections:
                        old_name = name
                        new_name = corrections[name]['corrected']
                        item['name'] = new_name
                        print(f"  ✅ {key} (all_mappings): \"{old_name}\" → \"{new_name}\"")
                        corrections_applied += 1
    
    # 修正があった場合のみファイルを保存
    if corrections_applied > 0:
        # バックアップを作成
        backup_path = file_path.with_suffix('.json.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 バックアップ作成: {backup_path.name}")
        
        # 修正版を保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 修正を保存: {corrections_applied} 件")
    else:
        print(f"  ℹ️  修正なし")
    
    return corrections_applied

def main():
    print("="*80)
    print("base_1〜base_5.jsonの無効項目修正スクリプト")
    print("="*80)
    print()
    
    # 修正対応表を読み込み
    print("📚 修正対応表を読み込み中...")
    corrections = load_corrections()
    print(f"✅ {len(corrections)} 件の修正項目を読み込みました")
    
    # base_1からbase_5まで処理
    total_corrections = 0
    
    for i in range(1, 6):
        file_path = mappings_dir / f"base_{i}.json"
        
        if not file_path.exists():
            print(f"\n⚠️  {file_path.name} が見つかりません")
            continue
        
        corrections_applied = apply_corrections_to_file(file_path, corrections)
        total_corrections += corrections_applied
    
    # 結果サマリー
    print("\n" + "="*80)
    print("📊 修正完了")
    print("="*80)
    print(f"総修正件数: {total_corrections} 件")
    print()
    print("次のステップ:")
    print("  1. validate_base_mappings.pyを再実行して検証")
    print("  2. すべて有効になったことを確認")
    print("="*80)

if __name__ == "__main__":
    main()
