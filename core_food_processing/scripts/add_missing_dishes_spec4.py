#!/usr/bin/env python3
"""
add_missing_dishes_spec4.py

spec4.mdで指摘されている不足料理を追加

主要な処理:
1. spec4.md R6に基づく不足料理の追加
2. 誤って削除された料理の復元（sushi等）
3. 目標サイズ（Base 350-400）への調整

Usage:
    python core_food_processing/scripts/add_missing_dishes_spec4.py
"""

import json
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent.parent


# spec4.md R6: 不足しているBase料理リスト
MISSING_DISHES = [
    # Pizza (3 thicknesses)
    {'label': 'pizza, cheese, thin crust', 'category': 'Pizza/Pasta/Mac', 'off_count': 0},
    {'label': 'pizza, cheese, medium crust', 'category': 'Pizza/Pasta/Mac', 'off_count': 0},
    {'label': 'pizza, cheese, thick crust', 'category': 'Pizza/Pasta/Mac', 'off_count': 0},

    # Pasta
    {'label': 'spaghetti bolognese', 'category': 'Pizza/Pasta/Mac', 'off_count': 0},
    {'label': 'spaghetti marinara', 'category': 'Pizza/Pasta/Mac', 'off_count': 0},
    {'label': 'fettuccine alfredo', 'category': 'Pizza/Pasta/Mac', 'off_count': 0},
    {'label': 'mac and cheese', 'category': 'Pizza/Pasta/Mac', 'off_count': 0},

    # Asian Noodles & Rice
    {'label': 'ramen', 'category': 'Asian Noodles & Rice', 'off_count': 0},
    {'label': 'pho', 'category': 'Asian Noodles & Rice', 'off_count': 0},
    {'label': 'pad thai', 'category': 'Asian Noodles & Rice', 'off_count': 0},
    {'label': 'lo mein', 'category': 'Asian Noodles & Rice', 'off_count': 0},
    {'label': 'fried rice', 'category': 'Asian Noodles & Rice', 'off_count': 0},
    {'label': 'teriyaki bowl', 'category': 'Asian Noodles & Rice', 'off_count': 0},
    {'label': 'sushi', 'category': 'Asian Noodles & Rice', 'off_count': 0},

    # Mex/Tex-Mex
    {'label': 'tacos, corn tortilla', 'category': 'Mex/Tex-Mex', 'off_count': 0},
    {'label': 'tacos, flour tortilla', 'category': 'Mex/Tex-Mex', 'off_count': 0},

    # Sandwiches/Burgers/Wraps
    {'label': 'hamburger', 'category': 'Sandwiches/Burgers/Wraps', 'off_count': 0},
    {'label': 'club sandwich', 'category': 'Sandwiches/Burgers/Wraps', 'off_count': 0},
    {'label': 'turkey sandwich', 'category': 'Sandwiches/Burgers/Wraps', 'off_count': 0},
    {'label': 'chicken wrap', 'category': 'Sandwiches/Burgers/Wraps', 'off_count': 0},

    # Sides
    {'label': 'french fries', 'category': 'Sides', 'off_count': 0},
    {'label': 'mashed potatoes', 'category': 'Sides', 'off_count': 0},
    {'label': 'rice pilaf', 'category': 'Sides', 'off_count': 0},
    {'label': 'rice and peas', 'category': 'Sides', 'off_count': 0},
]


def main():
    """メイン処理"""
    print("="*80)
    print("spec4.md不足料理追加スクリプト")
    print("="*80)
    print()

    # 入力ファイル
    dishes_filtered = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_spec4_filtered.json"

    # データを読み込み
    print("📖 spec4フィルタ済みデータを読み込み中...")
    with open(dishes_filtered, 'r', encoding='utf-8') as f:
        dishes = json.load(f)

    print(f"  現在の料理数: {len(dishes):,} 項目")
    print()

    # 不足料理を追加
    print("➕ 不足している料理を追加中...")

    # 既存のラベルセット
    existing_labels = {d['label'].lower() for d in dishes}

    added_count = 0
    for missing_dish in MISSING_DISHES:
        label_lower = missing_dish['label'].lower()

        # 既に存在する場合はスキップ
        if label_lower in existing_labels:
            continue

        # 追加
        dishes.append({
            'label': missing_dish['label'],
            'off_count': missing_dish['off_count'],
            'original_labels': [missing_dish['label']],
            'score': 0.0,
            'category': missing_dish.get('category', 'Other')
        })
        added_count += 1
        print(f"  + {missing_dish['label']}")

    print()
    print(f"  追加: {added_count} 項目")
    print(f"  合計: {len(dishes):,} 項目")
    print()

    # 出力
    output_file = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_spec4_augmented.json"

    print("💾 拡張データを保存中...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dishes, f, indent=2, ensure_ascii=False)
    print(f"  {output_file}")
    print()

    # サマリー
    print("="*80)
    print("拡張結果サマリー")
    print("="*80)
    print(f"料理: {len(dishes) - added_count} → {len(dishes)} 項目（+{added_count}）")
    print()

    # 目標との比較
    target_min = 350
    target_max = 400

    if target_min <= len(dishes) <= target_max:
        status = "✅ 目標範囲内"
    elif len(dishes) < target_min:
        status = f"⚠️ 目標より少ない（あと{target_min - len(dishes)}項目必要）"
    else:
        status = f"⚠️ 目標より多い（{len(dishes) - target_max}項目削減可能）"

    print(f"目標: {target_min}-{target_max} 項目 → {status}")
    print()

    print("✅ 次のステップ:")
    print("  1. 魚介名の正規化（FDA Seafood List）")
    print("  2. チーズの圧縮（10-12種）")
    print("  3. 最終スコアリングと上位選択（Ingredient 600-800）")
    print()


if __name__ == "__main__":
    main()
