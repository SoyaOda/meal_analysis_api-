#!/usr/bin/env python3
"""
selected_food_list.txtから（）で囲まれた日本語の注釈を削除
"""

import re
from pathlib import Path


def remove_japanese_annotations(file_path: Path) -> None:
    """
    ファイルから（）で囲まれた日本語部分を削除

    Args:
        file_path: 処理するファイルのパス
    """
    # ファイルを読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # （）で囲まれた部分を削除（全角括弧）
    # パターン: （任意の文字）
    content_cleaned = re.sub(r'（[^）]*）', '', content)

    # 結果を保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_cleaned)

    print(f"✅ 日本語注釈を削除しました: {file_path}")


def main():
    """メイン実行"""
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    file_path = base_dir / "usda_data_processing" / "display_name_generation" / "selected_food_list.txt"

    print("=" * 80)
    print("日本語注釈削除スクリプト")
    print("=" * 80)
    print()

    # 処理前のサンプルを表示
    print("📂 処理対象ファイル:")
    print(f"   {file_path}")
    print()

    # 削除実行
    remove_japanese_annotations(file_path)

    print()
    print("=" * 80)
    print("✨ 処理完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
