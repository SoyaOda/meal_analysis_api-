#!/usr/bin/env python3
"""
飲料関連のカテゴリを整理し、重複を削除するスクリプト
"""
import os

def main():
    # ファイルパスの設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    selected_food_file = os.path.join(base_dir, "display_name_generation", "selected_food_list.txt")

    # 削除対象の飲料（他カテゴリから【Beverages — non-alcoholic】へ移動または削除）
    items_to_remove = {
        # 【Milks, Yogurts & Smoothies】から移動する飲料
        "* Chocolate milk, NFS",
        "* Hot chocolate / cocoa, NFS",
        "* Fruit smoothie, NFS",

        # 【Fruits & Fruit‑based】のジュース（すでに【Beverages — non-alcoholic】にある）
        "* Fruit juice, NFS",
        "* Orange juice, 100%, NFS",
        "* Apple juice, 100%",
        "* Grape juice, 100%",

        # 重複している類似アイテム
        "* Water beverage, fruit flavored",  # Water, non-carbonated, flavored と重複
        "* Fruit smoothie juice drink, with dairy",  # Fruit smoothie, bottled で十分

        # 【Milks, Yogurts & Smoothies】から削除（【Dairy】にある）
        "* Milk, NFS",
    }

    # 【Beverages — non-alcoholic】に追加する飲料
    items_to_add_to_beverages = [
        "* Chocolate milk, NFS",
        "* Hot chocolate / cocoa, NFS",
    ]

    # ファイルを読み込む
    with open(selected_food_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    beverages_section_index = -1
    beverages_end_index = -1

    # まず【Beverages — non-alcoholic】セクションの位置を特定
    for i, line in enumerate(lines):
        if '【Beverages — non-alcoholic】' in line or '【Beverages - non-alcoholic】' in line:
            beverages_section_index = i
            # セクションの終わりを探す
            for j in range(i + 1, len(lines)):
                if lines[j].startswith('【'):
                    beverages_end_index = j
                    break

    # 削除とカテゴリ整理を実行
    skip_line = False
    removed_items = []

    for i, line in enumerate(lines):
        original_line = line.rstrip('\n')

        # 削除対象のアイテムをスキップ
        if original_line in items_to_remove:
            removed_items.append(original_line)
            continue

        # 【Beverages — non-alcoholic】セクションの最後に飲料を追加
        if i == beverages_end_index - 1 and beverages_section_index != -1:
            # 既存のアイテムを追加
            result_lines.append(original_line)
            # 新しい飲料を追加
            for item in items_to_add_to_beverages:
                result_lines.append(item)
        else:
            result_lines.append(original_line)

    # ファイルを書き戻す
    with open(selected_food_file, 'w', encoding='utf-8') as f:
        for line in result_lines:
            f.write(line + '\n')

    print("飲料カテゴリの整理が完了しました")
    print(f"削除/移動したアイテム数: {len(removed_items)}")
    print("\n削除/移動したアイテム:")
    for item in removed_items:
        print(f"  {item}")

    print("\n【Beverages — non-alcoholic】に追加したアイテム:")
    for item in items_to_add_to_beverages:
        print(f"  {item}")

    # 食品数をカウント
    food_count = sum(1 for line in result_lines if line.startswith('* '))
    print(f"\n最終的な食品総数: {food_count}件")

if __name__ == "__main__":
    main()