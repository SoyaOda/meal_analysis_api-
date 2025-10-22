#!/usr/bin/env python
"""
mappings.jsonからoysters_note（メタ項目）を削除
"""

import json
from pathlib import Path
from datetime import datetime

mappings_file = Path(__file__).parent / "mappings" / "mappings.json"

def remove_meta_item():
    """oysters_noteを削除"""

    # mappings.jsonを読み込み
    with open(mappings_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # バックアップ作成
    backup_file = mappings_file.with_suffix('.json.backup_before_meta_removal')
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"📁 バックアップ作成: {backup_file}")

    # メタ項目を確認
    if 'oysters_note' in data['mappings']:
        meta_item = data['mappings']['oysters_note']
        print(f"\n🔍 削除対象のメタ項目を確認:")
        print(f"   キー: oysters_note")
        print(f"   display_name: {meta_item.get('display_name', 'N/A')}")
        print(f"   category: {meta_item.get('category', 'N/A')}")

        # 削除
        del data['mappings']['oysters_note']
        print(f"\n✅ oysters_noteを削除しました")

        # メタデータを更新
        old_total = data['_metadata']['total_foods']
        data['_metadata']['total_foods'] = len(data['mappings'])
        print(f"\n📊 総食品数を更新: {old_total} → {data['_metadata']['total_foods']}")

        # 更新日時を追加
        data['_metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data['_metadata']['note'] = "Meta item 'oysters_note' removed"

        # 保存
        with open(mappings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ mappings.jsonを更新しました")

        return True
    else:
        print("⚠️ oysters_noteが見つかりません")
        return False

def regenerate_display_names():
    """display_names_list.txtを再生成"""

    output_file = Path(__file__).parent / "mappings" / "display_names_list.txt"

    # mappings.jsonを読み込み
    with open(mappings_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mappings = data.get('mappings', {})

    # display_nameを収集
    display_names = []
    for key, value in mappings.items():
        if 'display_name' in value:
            display_names.append(value['display_name'])
        else:
            display_names.append(key)

    # ソート
    display_names.sort()

    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Display Names List from mappings.json\n")
        f.write(f"# Total: {len(display_names)} items\n")
        f.write("# " + "="*50 + "\n\n")

        for i, name in enumerate(display_names, 1):
            f.write(f"{i}. {name}\n")

    print(f"\n📝 display_names_list.txtを再生成しました")
    print(f"   総項目数: {len(display_names)}")

    return len(display_names)

def main():
    print("="*80)
    print("メタ項目削除スクリプト")
    print("="*80)
    print()

    # oysters_noteを削除
    if remove_meta_item():
        # display_names_list.txtを再生成
        count = regenerate_display_names()

        print()
        print("="*80)
        print("✅ 完了")
        print(f"   • oysters_noteを削除")
        print(f"   • 総食品数: 487項目")
        print(f"   • display_names_list.txt再生成完了")
        print("="*80)
    else:
        print("\n処理を中止しました")

if __name__ == "__main__":
    main()