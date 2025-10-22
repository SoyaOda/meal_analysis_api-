#!/usr/bin/env python
"""
selected_food_list.txtの食品名がoriginal_name_single_ingredients.txtと
original_name.txtから正確に抽出されているか検証

出力:
1. verified_matching_foods.txt - 完全一致した食品名
2. non_matching_foods.txt - 一致しなかった食品名
"""

import re
from pathlib import Path
from typing import Set, List, Tuple


def load_original_names(file_path: Path) -> Set[str]:
    """
    original_name*.txtから食品名を読み込み

    Args:
        file_path: ファイルパス

    Returns:
        食品名のセット（番号プレフィックスを除去）
    """
    food_names = set()

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('>') or line.startswith('**') or line.startswith('---'):
                continue

            # 番号プレフィックスを除去（例: "1. Food name" -> "Food name"）
            match = re.match(r'^\d+\.\s+(.+)$', line)
            if match:
                food_name = match.group(1)
                food_names.add(food_name)

    return food_names


def load_selected_foods(file_path: Path) -> List[Tuple[str, str]]:
    """
    selected_food_list.txtから食品名を読み込み

    Args:
        file_path: ファイルパス

    Returns:
        (カテゴリ, 食品名)のタプルのリスト
    """
    selected_foods = []
    current_category = "不明"

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # カテゴリヘッダー検出（例: 【Pizza & Italian bases】）
            category_match = re.match(r'^【(.+)】$', line)
            if category_match:
                current_category = category_match.group(1)
                continue

            # 食品名検出（例: * Pizza, cheese, from restaurant...）
            food_match = re.match(r'^\*\s+(.+)$', line)
            if food_match:
                food_name = food_match.group(1)
                
                # 行末の注釈を除去（例: "←ブランド強識別", "# コメント"など）
                # ←や#以降を削除し、前後の空白をトリム
                food_name = re.sub(r'\s*[←#].*$', '', food_name).strip()
                
                selected_foods.append((current_category, food_name))

    return selected_foods


def verify_foods(
    selected_foods: List[Tuple[str, str]],
    original_names: Set[str]
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    選択された食品名が元データに存在するか検証

    Args:
        selected_foods: (カテゴリ, 食品名)のリスト
        original_names: 元データの食品名セット

    Returns:
        (一致リスト, 不一致リスト)
    """
    matching = []
    non_matching = []

    for category, food_name in selected_foods:
        if food_name in original_names:
            matching.append((category, food_name))
        else:
            non_matching.append((category, food_name))

    return matching, non_matching


def save_results(
    matching: List[Tuple[str, str]],
    non_matching: List[Tuple[str, str]],
    output_dir: Path
):
    """
    検証結果をファイルに保存

    Args:
        matching: 一致した(カテゴリ, 食品名)のリスト
        non_matching: 不一致の(カテゴリ, 食品名)のリスト
        output_dir: 出力ディレクトリ
    """
    # 一致した食品名を保存
    matching_output = output_dir / "verified_matching_foods.txt"
    with open(matching_output, 'w', encoding='utf-8') as f:
        f.write(f"# 検証結果: 一致した食品名\n")
        f.write(f"# 総数: {len(matching)}件\n\n")

        current_category = None
        for category, food_name in matching:
            if category != current_category:
                f.write(f"\n【{category}】\n")
                current_category = category
            f.write(f"* {food_name}\n")

    # 不一致の食品名を保存
    non_matching_output = output_dir / "non_matching_foods.txt"
    with open(non_matching_output, 'w', encoding='utf-8') as f:
        f.write(f"# 検証結果: 不一致の食品名\n")
        f.write(f"# 総数: {len(non_matching)}件\n\n")

        if non_matching:
            current_category = None
            for category, food_name in non_matching:
                if category != current_category:
                    f.write(f"\n【{category}】\n")
                    current_category = category
                f.write(f"* {food_name}\n")
        else:
            f.write("全ての食品名が一致しました！\n")

    return matching_output, non_matching_output


def main():
    """メイン実行"""
    # パス設定
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    data_dir = base_dir / "usda_data_processing" / "display_name_generation"

    single_ingredients_path = data_dir / "original_name_single_ingredients.txt"
    composite_dishes_path = data_dir / "original_name.txt"
    selected_foods_path = data_dir / "selected_food_list.txt"

    print("=" * 80)
    print("食品名検証スクリプト")
    print("=" * 80)
    print()

    # Step 1: 元データの食品名を読み込み
    print("📂 Step 1: 元データの食品名を読み込み中...")
    original_names = set()

    single_names = load_original_names(single_ingredients_path)
    print(f"   - 単一食材: {len(single_names)}件")
    original_names.update(single_names)

    composite_names = load_original_names(composite_dishes_path)
    print(f"   - 複合料理: {len(composite_names)}件")
    original_names.update(composite_names)

    print(f"✅ 総元データ食品数: {len(original_names)}件\n")

    # Step 2: 選択された食品名を読み込み
    print("📂 Step 2: 選択された食品名を読み込み中...")
    selected_foods = load_selected_foods(selected_foods_path)
    print(f"✅ 選択済み食品数: {len(selected_foods)}件\n")

    # Step 3: 検証
    print("🔍 Step 3: 食品名の照合中...")
    matching, non_matching = verify_foods(selected_foods, original_names)

    print(f"   - ✅ 一致: {len(matching)}件")
    print(f"   - ❌ 不一致: {len(non_matching)}件")

    if non_matching:
        print(f"\n⚠️  {len(non_matching)}件の食品名が元データに存在しません")
        print("\n不一致の例（最初の10件）:")
        for i, (category, food_name) in enumerate(non_matching[:10], 1):
            print(f"   {i}. [{category}] {food_name}")
        if len(non_matching) > 10:
            print(f"   ... 他 {len(non_matching) - 10}件")
    else:
        print("\n✨ 全ての食品名が元データに存在します！")

    print()

    # Step 4: 結果をファイルに保存
    print("💾 Step 4: 結果をファイルに保存中...")
    matching_file, non_matching_file = save_results(matching, non_matching, data_dir)

    print(f"✅ 一致リスト: {matching_file}")
    print(f"   - ファイルサイズ: {matching_file.stat().st_size / 1024:.1f} KB")

    print(f"✅ 不一致リスト: {non_matching_file}")
    print(f"   - ファイルサイズ: {non_matching_file.stat().st_size / 1024:.1f} KB")

    print()
    print("=" * 80)
    print("✨ 検証完了")
    print("=" * 80)

    # 統計サマリー
    print(f"\n📊 統計サマリー:")
    print(f"   - 元データ総数: {len(original_names)}件")
    print(f"   - 選択済み総数: {len(selected_foods)}件")
    print(f"   - 一致率: {len(matching) / len(selected_foods) * 100:.2f}%")

    return 0 if len(non_matching) == 0 else 1


if __name__ == "__main__":
    exit(main())
