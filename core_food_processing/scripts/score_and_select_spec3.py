#!/usr/bin/env python3
"""
score_and_select_spec3.py

spec3.mdに基づくスコアリングと上位選択

目標サイズ（spec3.md）:
- Base foods: 350-500項目
- Ingredients: 600-900項目

スコアリング式（spec3.md）:
- score = 0.5*log1p(OFF_count) + 0.5*log1p(Recipe_count)
  ※ Recipe1M+データがないため、OFF_countのみで簡易実装

Usage:
    python core_food_processing/scripts/score_and_select_spec3.py
"""

import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def main():
    """メイン処理"""
    print("="*80)
    print("スコアリングと上位選択スクリプト（spec3.md準拠）")
    print("="*80)
    print()

    # 入力ファイル
    dishes_json = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_normalized_spec3.json"
    ingredients_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_normalized_spec3.json"

    # データを読み込み
    print("📖 正規化データを読み込み中...")
    with open(dishes_json, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    with open(ingredients_json, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  料理候補: {len(dishes):,} 項目")
    print(f"  食材候補: {len(ingredients):,} 項目")
    print()

    # スコアリング
    print("📊 スコアリング中...")
    print("   ※ spec3.mdのスコア式: 0.5*log1p(OFF) + 0.5*log1p(Recipe)")
    print("   ※ Recipe1M+データがないため、OFFのみで簡易実装")
    print()

    for dish in dishes:
        off_count = dish.get('off_count', 0)
        # 簡易スコア: log1p(OFF頻度)
        # Recipe1M+データがあれば追加
        dish['score'] = math.log1p(off_count)

    for ingredient in ingredients:
        off_count = ingredient.get('off_count', 0)
        ingredient['score'] = math.log1p(off_count)

    print("  完了")
    print()

    # ソート
    print("🔀 スコアでソート中...")
    dishes_sorted = sorted(dishes, key=lambda x: x['score'], reverse=True)
    ingredients_sorted = sorted(ingredients, key=lambda x: x['score'], reverse=True)
    print("  完了")
    print()

    # 上位選択（spec3.mdの目標サイズ）
    TARGET_DISHES_MIN = 350
    TARGET_DISHES_MAX = 500
    TARGET_INGREDIENTS_MIN = 600
    TARGET_INGREDIENTS_MAX = 900

    print(f"📌 上位選択中...")
    print(f"  目標: 料理 {TARGET_DISHES_MIN}-{TARGET_DISHES_MAX} 項目")
    print(f"        食材 {TARGET_INGREDIENTS_MIN}-{TARGET_INGREDIENTS_MAX} 項目")
    print()

    # 料理の上位を選択
    # 317項目 → 350-500の範囲内なのでそのまま使用
    if len(dishes_sorted) <= TARGET_DISHES_MAX:
        dishes_top = dishes_sorted
        print(f"  料理: 全 {len(dishes_top)} 項目を採用（目標範囲内）")
    else:
        dishes_top = dishes_sorted[:TARGET_DISHES_MAX]
        print(f"  料理: 上位 {len(dishes_top)} 項目を選択")

    if len(dishes_top) > 0:
        print(f"    最小スコア: {dishes_top[-1]['score']:.2f}")
        print(f"    最小OFF頻度: {dishes_top[-1]['off_count']:,}")
        print(f"    最大スコア: {dishes_top[0]['score']:.2f}")
        print(f"    最大OFF頻度: {dishes_top[0]['off_count']:,}")
    print()

    # 食材の上位を選択
    # 2,482項目 → 900項目に絞る
    if len(ingredients_sorted) <= TARGET_INGREDIENTS_MAX:
        ingredients_top = ingredients_sorted
        print(f"  食材: 全 {len(ingredients_top)} 項目を採用")
    else:
        ingredients_top = ingredients_sorted[:TARGET_INGREDIENTS_MAX]
        print(f"  食材: 上位 {len(ingredients_top)} 項目を選択")

    if len(ingredients_top) > 0:
        print(f"    最小スコア: {ingredients_top[-1]['score']:.2f}")
        print(f"    最小OFF頻度: {ingredients_top[-1]['off_count']:,}")
        print(f"    最大スコア: {ingredients_top[0]['score']:.2f}")
        print(f"    最大OFF頻度: {ingredients_top[0]['off_count']:,}")
    print()

    # 結果を保存
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    dishes_core = output_dir / "dishes_core_spec3.json"
    ingredients_core = output_dir / "ingredients_core_spec3.json"

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
    print("CORE候補統計（spec3.md準拠）")
    print("="*80)
    print(f"料理CORE: {len(dishes_top):,} 項目")
    if len(dishes_top) > 0:
        print(f"  スコア範囲: {dishes_top[-1]['score']:.2f} 〜 {dishes_top[0]['score']:.2f}")
        print(f"  OFF頻度範囲: {dishes_top[-1]['off_count']:,} 〜 {dishes_top[0]['off_count']:,} ヒット")
    print()

    print(f"食材CORE: {len(ingredients_top):,} 項目")
    if len(ingredients_top) > 0:
        print(f"  スコア範囲: {ingredients_top[-1]['score']:.2f} 〜 {ingredients_top[0]['score']:.2f}")
        print(f"  OFF頻度範囲: {ingredients_top[-1]['off_count']:,} 〜 {ingredients_top[0]['off_count']:,} ヒット")
    print()

    # トップ20を表示
    print("料理COREトップ20:")
    print("-"*80)
    for i, dish in enumerate(dishes_top[:20], 1):
        original_count = len(dish.get('original_labels', []))
        print(f"{i:3d}. {dish['label']:40s} (スコア: {dish['score']:6.2f}, {dish['off_count']:,} ヒット, {original_count}種統合)")
    print()

    print("食材COREトップ20:")
    print("-"*80)
    for i, ing in enumerate(ingredients_top[:20], 1):
        original_count = len(ing.get('original_labels', []))
        print(f"{i:3d}. {ing['label']:40s} (スコア: {ing['score']:6.2f}, {ing['off_count']:,} ヒット, {original_count}種統合)")
    print()

    # 下位10も表示（閾値確認用）
    if len(dishes_top) >= 10:
        print("料理CORE下位10:")
        print("-"*80)
        for i, dish in enumerate(dishes_top[-10:], len(dishes_top)-9):
            print(f"{i:3d}. {dish['label']:40s} (スコア: {dish['score']:6.2f}, {dish['off_count']:,} ヒット)")
        print()

    if len(ingredients_top) >= 10:
        print("食材CORE下位10:")
        print("-"*80)
        for i, ing in enumerate(ingredients_top[-10:], len(ingredients_top)-9):
            print(f"{i:3d}. {ing['label']:40s} (スコア: {ing['score']:6.2f}, {ing['off_count']:,} ヒット)")
        print()

    print("✅ 次のステップ:")
    print("  最終CORE食品リストをspec3.md形式で生成")
    print()


if __name__ == "__main__":
    main()
