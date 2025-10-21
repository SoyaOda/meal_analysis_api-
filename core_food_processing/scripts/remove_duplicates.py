#!/usr/bin/env python3
"""
remove_duplicates.py

料理と食材の重複を削除するスクリプト

問題: FoodOnの階層構造により、一部の料理が食材リストにも含まれている
解決: 料理候補を優先し、重複を食材リストから削除

Usage:
    python core_food_processing/scripts/remove_duplicates.py
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def main():
    """メイン処理"""
    print("="*80)
    print("料理/食材 重複削除スクリプト")
    print("="*80)
    print()

    # 入力ファイル
    dishes_json = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_raw.json"
    ingredients_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_raw.json"

    # データを読み込み
    print("📖 データを読み込み中...")
    with open(dishes_json, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    with open(ingredients_json, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  料理候補: {len(dishes):,} 項目")
    print(f"  食材候補: {len(ingredients):,} 項目（修正前）")
    print()

    # ラベルのセットを作成
    dish_labels = {d['label'].lower() for d in dishes}

    # 重複を検出
    original_count = len(ingredients)
    overlapping_items = []

    # 重複していない食材のみを保持
    ingredients_cleaned = []
    for ingredient in ingredients:
        label_lower = ingredient['label'].lower()
        if label_lower in dish_labels:
            overlapping_items.append(ingredient['label'])
        else:
            ingredients_cleaned.append(ingredient)

    removed_count = original_count - len(ingredients_cleaned)

    print(f"🔍 重複検出結果:")
    print(f"  重複項目数: {removed_count:,} 項目 ({removed_count*100//original_count}%)")
    print()

    if removed_count > 0:
        print("削除された項目（最初の30個）:")
        print("-"*80)
        for i, label in enumerate(sorted(overlapping_items)[:30], 1):
            print(f"  {i:3d}. {label}")
        print()

    # 結果を保存
    output_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_cleaned.json"

    print("💾 クリーンアップされた食材リストを保存中...")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(ingredients_cleaned, f, indent=2, ensure_ascii=False)

    print(f"  保存先: {output_json}")
    print(f"  食材候補: {len(ingredients_cleaned):,} 項目（修正後）")
    print()

    # 元のファイルも更新（バックアップを作成）
    backup_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_raw_backup.json"
    print(f"📦 バックアップを作成: {backup_json}")
    ingredients_json.rename(backup_json)

    print(f"🔄 元のファイルを更新: {ingredients_json}")
    with open(ingredients_json, 'w', encoding='utf-8') as f:
        json.dump(ingredients_cleaned, f, indent=2, ensure_ascii=False)

    print()
    print("="*80)
    print("完了")
    print("="*80)
    print(f"料理候補: {len(dishes):,} 項目")
    print(f"食材候補: {len(ingredients_cleaned):,} 項目（{removed_count:,} 項目削除）")
    print(f"合計: {len(dishes) + len(ingredients_cleaned):,} 項目")
    print()


if __name__ == "__main__":
    main()
