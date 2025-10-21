#!/usr/bin/env python3
"""
score_and_select.py

OFF頻度データでスコアリングして上位を選択するスクリプト

目標:
- Base (料理): ~600項目
- Ingredient (食材): ~1000項目

スコアリング式（簡易版、OFFのみ）:
- score = log1p(off_count)

Usage:
    python core_food_processing/scripts/score_and_select.py
"""

import json
import math
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent.parent


def main():
    """メイン処理"""
    print("="*80)
    print("スコアリングと上位選択スクリプト")
    print("="*80)
    print()

    # 入力ファイル
    dishes_json = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_with_off_freq.json"
    ingredients_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_with_off_freq.json"

    # データを読み込み
    print("📖 データを読み込み中...")
    with open(dishes_json, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    with open(ingredients_json, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  料理候補: {len(dishes):,} 項目")
    print(f"  食材候補: {len(ingredients):,} 項目")
    print()

    # スコアリング
    print("📊 スコアリング中...")

    for dish in dishes:
        off_count = dish.get('off_count', 0)
        # 簡易スコア: log1p(OFF頻度)
        dish['score'] = math.log1p(off_count)

    for ingredient in ingredients:
        off_count = ingredient.get('off_count', 0)
        # 簡易スコア: log1p(OFF頻度)
        ingredient['score'] = math.log1p(off_count)

    print("  完了")
    print()

    # ソート
    print("🔀 スコアでソート中...")
    dishes_sorted = sorted(dishes, key=lambda x: x['score'], reverse=True)
    ingredients_sorted = sorted(ingredients, key=lambda x: x['score'], reverse=True)
    print("  完了")
    print()

    # 上位選択
    TARGET_DISHES = 600
    TARGET_INGREDIENTS = 1000

    print(f"📌 上位選択中...")
    print(f"  目標: 料理 {TARGET_DISHES} 項目、食材 {TARGET_INGREDIENTS} 項目")
    print()

    # 料理の上位を選択
    dishes_top = dishes_sorted[:TARGET_DISHES]
    print(f"  料理: 上位 {len(dishes_top)} 項目を選択")
    print(f"    最小スコア: {dishes_top[-1]['score']:.2f}")
    print(f"    最小OFF頻度: {dishes_top[-1]['off_count']:,}")

    # 食材の上位を選択
    ingredients_top = ingredients_sorted[:TARGET_INGREDIENTS]
    print(f"  食材: 上位 {len(ingredients_top)} 項目を選択")
    print(f"    最小スコア: {ingredients_top[-1]['score']:.2f}")
    print(f"    最小OFF頻度: {ingredients_top[-1]['off_count']:,}")
    print()

    # 結果を保存
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    dishes_core = output_dir / "dishes_core.json"
    ingredients_core = output_dir / "ingredients_core.json"

    print("💾 CORE候補を保存中...")
    with open(dishes_core, 'w', encoding='utf-8') as f:
        json.dump(dishes_top, f, indent=2, ensure_ascii=False)
    print(f"  料理CORE: {dishes_core}")

    with open(ingredients_core, 'w', encoding='utf-8') as f:
        json.dump(ingredients_top, f, indent=2, ensure_ascii=False)
    print(f"  食材CORE: {ingredients_core}")
    print()

    # 統計情報
    print("="*80)
    print("CORE候補統計")
    print("="*80)
    print(f"料理CORE: {len(dishes_top):,} 項目")
    print(f"  スコア範囲: {dishes_top[-1]['score']:.2f} 〜 {dishes_top[0]['score']:.2f}")
    print(f"  OFF頻度範囲: {dishes_top[-1]['off_count']:,} 〜 {dishes_top[0]['off_count']:,} ヒット")
    print()

    print(f"食材CORE: {len(ingredients_top):,} 項目")
    print(f"  スコア範囲: {ingredients_top[-1]['score']:.2f} 〜 {ingredients_top[0]['score']:.2f}")
    print(f"  OFF頻度範囲: {ingredients_top[-1]['off_count']:,} 〜 {ingredients_top[0]['off_count']:,} ヒット")
    print()

    # トップ20を表示
    print("料理COREトップ20:")
    print("-"*80)
    for i, dish in enumerate(dishes_top[:20], 1):
        print(f"{i:3d}. {dish['label']:50s} (スコア: {dish['score']:6.2f}, {dish['off_count']:,} ヒット)")
    print()

    print("食材COREトップ20:")
    print("-"*80)
    for i, ing in enumerate(ingredients_top[:20], 1):
        print(f"{i:3d}. {ing['label']:50s} (スコア: {ing['score']:6.2f}, {ing['off_count']:,} ヒット)")
    print()

    # 下位10も表示（閾値確認用）
    print("料理CORE下位10:")
    print("-"*80)
    for i, dish in enumerate(dishes_top[-10:], len(dishes_top)-9):
        print(f"{i:3d}. {dish['label']:50s} (スコア: {dish['score']:6.2f}, {dish['off_count']:,} ヒット)")
    print()

    print("食材CORE下位10:")
    print("-"*80)
    for i, ing in enumerate(ingredients_top[-10:], len(ingredients_top)-9):
        print(f"{i:3d}. {ing['label']:50s} (スコア: {ing['score']:6.2f}, {ing['off_count']:,} ヒット)")
    print()

    print("✅ 次のステップ:")
    print("  complete_prompt.txt形式でCORE食品リストを生成")
    print()


if __name__ == "__main__":
    main()
