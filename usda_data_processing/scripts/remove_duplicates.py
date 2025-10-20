#!/usr/bin/env python3
"""
selected_food_list.txtから重複項目を削除
"""

from pathlib import Path


def remove_duplicates(file_path: Path) -> None:
    """
    重複項目を削除

    Args:
        file_path: ファイルパス
    """
    # 削除する項目のリスト（完全一致）
    items_to_remove = [
        # 1) 完全重複（名称が完全一致）
        "* Ravioli, cheese-filled, with tomato sauce",  # Pizza & Italian basesセクション内（line 10付近）
        "* Cheese, American",  # Cheeses & Cheese/Sauce Anchorsセクション内
        "* Alfredo sauce",  # Cheeses & Cheese/Sauce Anchorsセクション内
        "* Stew, NFS",  # Mixed Dishes — Asian / Latin / Italian etc.セクション内

        # 2) 出自だけの違い
        "* Bread, white, made from home recipe or purchased at a bakery",
        "* Bread, whole wheat, made from home recipe or purchased at bakery",
        "* Bread, wheat or cracked wheat, made from home recipe or purchased at bakery",
        "* Cookie, chocolate chip, made from home recipe or purchased at a bakery",
        "* Cornbread, made from home recipe",

        # 3) ベース×軽微バリエーションの重複
        "* Pizza, extra cheese, thin crust",
        "* Pizza, extra cheese, thick crust",
        "* Lasagna with meat, home recipe",
        "* Lasagna, meatless, with vegetables",
        "* Pork bacon, smoked or cured, cooked",
        "* Soup, ramen noodles, water added",
        "* Hot dog, NFS",
        "* Cream puff, eclair, custard or cream filled, iced",
        "* Seafood paella, Puerto Rican style",

        # 4) 用途限定
        "* Cheese sauce, for use with vegetables",
        "* Cream sauce, for use with vegetables",
        "* Gravy, for use with vegetables",
        "* Soy based sauce, for use with vegetables",
        "* Tomato sauce, for use with vegetables",
    ]

    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 削除対象を追跡
    removed_items = []
    kept_lines = []
    skip_next_empty = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 削除対象かチェック
        if stripped in items_to_remove:
            removed_items.append(stripped)
            skip_next_empty = True
            continue

        # 削除直後の空行をスキップ（フォーマット維持のため）
        if skip_next_empty and stripped == "":
            skip_next_empty = False
            # 次の行が項目ならこの空行は保持
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("*"):
                kept_lines.append(line)
            continue

        skip_next_empty = False
        kept_lines.append(line)

    # ファイルに書き込む
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(kept_lines)

    print(f"✅ {len(removed_items)}件の重複項目を削除しました")
    print("\n削除した項目:")
    for item in removed_items:
        print(f"  - {item}")


def main():
    """メイン実行"""
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    file_path = base_dir / "usda_data_processing" / "display_name_generation" / "selected_food_list.txt"

    print("=" * 80)
    print("重複項目削除スクリプト")
    print("=" * 80)
    print()

    remove_duplicates(file_path)

    print()
    print("=" * 80)
    print("✨ 処理完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
