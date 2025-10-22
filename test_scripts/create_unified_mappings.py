#!/usr/bin/env python
"""
base_1〜base_7.jsonを統合して一つのmappings.jsonを作成
"""

import json
from pathlib import Path
from collections import OrderedDict

mappings_dir = Path(__file__).parent / "mappings"

def merge_base_files():
    """base_1〜base_7を統合"""
    
    print("="*80)
    print("base_1〜base_7.jsonの統合")
    print("="*80)
    print()
    
    unified_mappings = OrderedDict()
    total_items = 0
    file_stats = []
    
    # base_1からbase_7まで読み込んで統合
    for i in range(1, 8):
        file_path = mappings_dir / f"base_{i}.json"
        
        if not file_path.exists():
            print(f"⚠️  {file_path.name} が見つかりません - スキップ")
            continue
        
        print(f"📚 読み込み中: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # mappings構造を確認
        if isinstance(data, dict):
            if 'mappings' in data:
                mappings = data['mappings']
            else:
                mappings = data
        else:
            print(f"  ⚠️  予期しない構造 - スキップ")
            continue
        
        # 統合（重複チェック付き）
        duplicates = []
        for key, value in mappings.items():
            if key in unified_mappings:
                duplicates.append(key)
                print(f"  ⚠️  重複キー: {key}")
            else:
                unified_mappings[key] = value
        
        item_count = len(mappings)
        total_items += item_count
        
        file_stats.append({
            'file': file_path.name,
            'items': item_count,
            'duplicates': len(duplicates)
        })
        
        print(f"  ✅ {item_count} 項目を追加")
        if duplicates:
            print(f"  ⚠️  {len(duplicates)} 件の重複")
    
    print()
    print("="*80)
    print("📊 統合結果")
    print("="*80)
    print()
    
    for stat in file_stats:
        dup_info = f" ({stat['duplicates']} 重複)" if stat['duplicates'] > 0 else ""
        print(f"  {stat['file']:15} : {stat['items']:4} 項目{dup_info}")
    
    print()
    print(f"  総項目数: {total_items}")
    print(f"  ユニーク項目数: {len(unified_mappings)}")
    
    if total_items != len(unified_mappings):
        print(f"  ⚠️  重複により {total_items - len(unified_mappings)} 項目が除外されました")
    
    return unified_mappings

def save_unified_mappings(mappings):
    """統合マッピングをファイルに保存"""
    
    output_file = mappings_dir / "mappings.json"
    
    # メタデータを追加
    output_data = {
        "_metadata": {
            "description": "Unified food name mappings from base_1 to base_7",
            "source_files": [f"base_{i}.json" for i in range(1, 8)],
            "total_foods": len(mappings),
            "databases_used": ["survey_fndds", "foundation"],
            "version": "1.0"
        },
        "mappings": mappings
    }
    
    # バックアップを作成（既存ファイルがある場合）
    if output_file.exists():
        backup_path = output_file.with_suffix('.json.backup')
        with open(output_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 既存ファイルのバックアップ作成: {backup_path.name}")
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 統合ファイルを保存: {output_file}")
    print(f"   ファイルサイズ: {output_file.stat().st_size:,} bytes")
    
    return output_file

def main():
    # base_1〜base_7を統合
    unified_mappings = merge_base_files()
    
    # ファイルに保存
    output_file = save_unified_mappings(unified_mappings)
    
    print()
    print("="*80)
    print("✅ 統合完了")
    print("="*80)
    print()
    print(f"出力ファイル: {output_file}")
    print(f"総マッピング数: {len(unified_mappings)}")

if __name__ == "__main__":
    main()
