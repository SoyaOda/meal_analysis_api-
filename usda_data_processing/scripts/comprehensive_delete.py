#!/usr/bin/env python3
"""
selected_food_list.txtから特殊ケース・レアな食事・不要な組み合わせを包括的に削除
"""
import os

def main():
    # ファイルパスの設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    # 削除対象ファイルのリスト
    delete_files = [
        os.path.join(script_dir, "items_to_delete.txt"),
        os.path.join(script_dir, "additional_items_to_delete.txt")
    ]

    selected_food_file = os.path.join(base_dir, "display_name_generation", "selected_food_list.txt")

    # 全ての削除対象アイテムを収集（空行とコメント行を除外）
    items_to_delete = set()
    for delete_file in delete_files:
        if os.path.exists(delete_file):
            with open(delete_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('【'):
                        items_to_delete.add(line)

    print(f"削除対象アイテム総数: {len(items_to_delete)}")

    # selected_food_list.txtを読み込む
    with open(selected_food_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 削除処理
    remaining_lines = []
    deleted_items = []
    category_count = {}
    current_category = "未分類"

    for line in lines:
        original_line = line.rstrip('\n')

        # カテゴリ行の検出
        if line.startswith("【"):
            current_category = line.strip()
            remaining_lines.append(original_line)
            continue

        # 空行はそのまま残す
        if not line.strip():
            remaining_lines.append(original_line)
            continue

        # 食品名の抽出（"* "で始まる行から食品名を取得）
        if line.startswith("* "):
            food_name = line[2:].strip()
            if food_name in items_to_delete:
                deleted_items.append(food_name)
                if current_category not in category_count:
                    category_count[current_category] = 0
                category_count[current_category] += 1
                continue

        remaining_lines.append(original_line)

    # ファイルを書き戻す
    with open(selected_food_file, 'w', encoding='utf-8') as f:
        for line in remaining_lines:
            f.write(line + '\n')

    print(f"削除されたアイテム数: {len(deleted_items)}")
    print(f"残りの行数: {len(remaining_lines)}")

    # カテゴリごとの削除数を表示
    print("\n=== カテゴリごとの削除数 ===")
    for category, count in sorted(category_count.items()):
        print(f"{category}: {count}件")

    # 削除されたアイテムをログとして出力
    deleted_log_file = os.path.join(script_dir, "comprehensive_deleted_items_log.txt")
    with open(deleted_log_file, 'w', encoding='utf-8') as f:
        f.write(f"削除されたアイテム総数: {len(deleted_items)}\n")
        f.write("=" * 50 + "\n")
        f.write("\n=== カテゴリごとの削除数 ===\n")
        for category, count in sorted(category_count.items()):
            f.write(f"{category}: {count}件\n")
        f.write("\n" + "=" * 50 + "\n")
        f.write("\n=== 削除されたアイテム一覧 ===\n")
        for item in sorted(deleted_items):
            f.write(f"{item}\n")

    print(f"\n削除ログを {deleted_log_file} に保存しました")

    # 削除対象で見つからなかったアイテムも確認
    not_found = items_to_delete - set(deleted_items)
    if not_found:
        print(f"\n警告: {len(not_found)}個の削除対象アイテムが見つかりませんでした")
        not_found_log = os.path.join(script_dir, "not_found_items.txt")
        with open(not_found_log, 'w', encoding='utf-8') as f:
            for item in sorted(not_found):
                f.write(f"{item}\n")
        print(f"見つからなかったアイテムを {not_found_log} に保存しました")

    # 残った食品数をカウント
    food_count = sum(1 for line in remaining_lines if line.startswith("* "))
    print(f"\n最終的な食品数: {food_count}件")

if __name__ == "__main__":
    main()