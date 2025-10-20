#!/usr/bin/env python3
"""
selected_food_list.txtから特殊パターンや限定的な食品を削除するスクリプト
"""
import os

def main():
    # ファイルパスの設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    items_to_delete_file = os.path.join(script_dir, "items_to_delete.txt")
    selected_food_file = os.path.join(base_dir, "display_name_generation", "selected_food_list.txt")

    # 削除対象アイテムを読み込み（空行とコメント行を除外）
    items_to_delete = set()
    with open(items_to_delete_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                items_to_delete.add(line)

    print(f"削除対象アイテム数: {len(items_to_delete)}")

    # selected_food_list.txtを読み込んで削除処理
    remaining_lines = []
    deleted_items = []

    with open(selected_food_file, 'r', encoding='utf-8') as f:
        for line in f:
            original_line = line.rstrip('\n')

            # 食品名の抽出（"* "で始まる行から食品名を取得）
            if line.startswith("* "):
                food_name = line[2:].strip()
                if food_name in items_to_delete:
                    deleted_items.append(food_name)
                    continue

            remaining_lines.append(original_line)

    # ファイルを書き戻す
    with open(selected_food_file, 'w', encoding='utf-8') as f:
        for line in remaining_lines:
            f.write(line + '\n')

    print(f"削除されたアイテム数: {len(deleted_items)}")
    print(f"残りの行数: {len(remaining_lines)}")

    # 削除されたアイテムをログとして出力
    deleted_log_file = os.path.join(script_dir, "deleted_items_log.txt")
    with open(deleted_log_file, 'w', encoding='utf-8') as f:
        f.write(f"削除されたアイテム数: {len(deleted_items)}\n")
        f.write("=" * 50 + "\n")
        for item in sorted(deleted_items):
            f.write(f"{item}\n")

    print(f"削除ログを {deleted_log_file} に保存しました")

    # 削除対象で見つからなかったアイテムも確認
    not_found = items_to_delete - set(deleted_items)
    if not_found:
        print(f"\n警告: {len(not_found)}個の削除対象アイテムが見つかりませんでした:")
        for item in sorted(not_found):
            print(f"  - {item}")

if __name__ == "__main__":
    main()