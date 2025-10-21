#!/usr/bin/env python3
"""
apply_spec4_rules.py

spec4.md準拠のルールを適用してBase/Ingredientを再分類

主要な処理:
1. より厳格なファセット語除去（R2）
2. Base/Ingredientの分類修正（R1: Baseは盛りつけ単位の料理のみ）
3. sauce/dressing/paste類をIngredientへ移動
4. dough/shell/carrier類を除外
5. 不適切な項目の削除

Usage:
    python core_food_processing/scripts/apply_spec4_rules.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent


# spec4.md R2: より厳格なファセット語禁止パターン
STRICT_FACET_PATTERNS = [
    r'\bfood product\b',
    r'\bproduct\b',
    r'\bsubstitute\b',
    r'\bimitation\b',
    r'\bmix\b',
    r'\bbase\b',
    r'\bseasoning\b',
    r'\binstant\b',
    r'\bpowder(ed)?\b',
    r'\bconcentrate(d)?\b',
    r'\bcanned\b',
    r'\bfrozen\b',
    r'\blow\b',
    r'\breduced\b',
    r'\bdiet\b',
    r'\bartificial(ly)?\b',
    r'\bpacket\b',
    r'\bprepack(ed)?\b',
    r'\bstix\b',
    r'\bwith .*(vitamin|flavor|colour|color)\b',
    r'\bdehydrated\b',
    r'\bfreeze-dried\b',
    r'\bderived product\b',
]


# spec4.md R1: BaseからIngredientへ移動すべきパターン
MOVE_TO_INGREDIENT_PATTERNS = [
    r'\bsauce\b',
    r'\bdressing\b',
    r'\bpaste\b',
    r'\bvinegar\b',
    r'\bdough\b',
    r'\bshell\b',
    r'\btortilla\b',
    r'\bbun\b',
    r'\broll\b',
    r'\bbread\b',
    r'\bcream\b',
    r'\bspread\b',
]


# Baseとして不適切（削除）
INVALID_BASE_PATTERNS = [
    r'\bdough\b',
    r'\bshell\b',
    r'\beer\b',
    r'\bwine\b',
    r'\bvinegar\b',
    r'\bbeverage\b',
    r'\bdrink\b',
    r'\bor\b.*\bfood product\b',  # "pancake or waffle food product"
]


# 料理として認識する強力なキーワード（これがあればBase候補）
STRONG_DISH_KEYWORDS = [
    # メイン料理
    'soup', 'stew', 'curry', 'pizza', 'pasta', 'spaghetti', 'lasagna',
    'ramen', 'noodle', 'pho', 'pad thai', 'lo mein', 'fried rice',
    'taco', 'burrito', 'quesadilla', 'enchilada', 'nachos',
    'burger', 'sandwich', 'wrap',
    'salad', 'omelet', 'pancake', 'waffle', 'french toast',
    'pot pie', 'casserole', 'gumbo', 'chowder',
    # デザート（Baseとして認識）
    'pie', 'cake', 'pudding', 'cookie', 'brownie', 'ice cream',
    'tart', 'parfait', 'sundae', 'yogurt',
    # その他の料理
    'popcorn', 'chips', 'dumpling', 'gnocchi', 'ravioli',
]


def apply_strict_facet_removal(label: str) -> str:
    """
    spec4.md R2に基づく厳格なファセット語除去

    Args:
        label: 元のラベル

    Returns:
        ファセット語を除去したラベル
    """
    cleaned = label

    # 括弧内を削除
    cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)

    # 厳格な禁止パターンを削除
    for pattern in STRICT_FACET_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # カンマ以降を削除
    if ',' in cleaned:
        cleaned = cleaned.split(',')[0]

    # 連続する空白を1つに
    cleaned = ' '.join(cleaned.split())

    return cleaned.strip()


def should_move_to_ingredient(label: str) -> bool:
    """
    BaseからIngredientへ移動すべきかを判定（spec4.md R1）

    Args:
        label: ラベル

    Returns:
        Ingredientへ移動すべき場合True
    """
    label_lower = label.lower()

    # sauce, dressing, paste等はIngredient
    for pattern in MOVE_TO_INGREDIENT_PATTERNS:
        if re.search(pattern, label_lower):
            # ただし、料理名に含まれる場合は除外
            # 例: "chicken in tomato sauce" は料理だが、"tomato sauce" 単体は食材
            has_strong_dish = any(kw in label_lower for kw in STRONG_DISH_KEYWORDS)
            if not has_strong_dish:
                return True

    return False


def is_invalid_base(label: str) -> bool:
    """
    Baseとして不適切な項目を判定

    Args:
        label: ラベル

    Returns:
        不適切な場合True
    """
    label_lower = label.lower()

    for pattern in INVALID_BASE_PATTERNS:
        if re.search(pattern, label_lower):
            return True

    return False


def is_valid_dish(label: str) -> bool:
    """
    有効な料理かどうかを判定（spec4.md R1）

    Args:
        label: ラベル

    Returns:
        有効な料理の場合True
    """
    label_lower = label.lower()

    # 強力な料理キーワードを含む
    for keyword in STRONG_DISH_KEYWORDS:
        if keyword in label_lower:
            return True

    # 上記に該当しない場合は料理ではない可能性が高い
    return False


def main():
    """メイン処理"""
    print("="*80)
    print("spec4.md準拠ルール適用スクリプト")
    print("="*80)
    print()

    # 入力ファイル（spec3の出力）
    dishes_spec3 = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_core_spec3.json"
    ingredients_spec3 = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_core_spec3.json"

    # データを読み込み
    print("📖 spec3の結果を読み込み中...")
    with open(dishes_spec3, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    with open(ingredients_spec3, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  料理（spec3）: {len(dishes):,} 項目")
    print(f"  食材（spec3）: {len(ingredients):,} 項目")
    print()

    # spec4.md R1, R2 を適用
    print("🔧 spec4.md ルールを適用中...")
    print()

    dishes_valid = []
    dishes_moved_to_ingredient = []
    dishes_invalid = []

    for dish in dishes:
        label = dish['label']

        # より厳格なファセット語除去
        cleaned_label = apply_strict_facet_removal(label)

        # 空白または短すぎる
        if not cleaned_label or len(cleaned_label) <= 2:
            dishes_invalid.append((label, "空白または短すぎる"))
            continue

        # Baseとして不適切
        if is_invalid_base(cleaned_label):
            dishes_invalid.append((label, "不適切（dough/shell/beverage等）"))
            continue

        # Ingredientへ移動すべき
        if should_move_to_ingredient(cleaned_label):
            dishes_moved_to_ingredient.append({
                'label': cleaned_label,
                'off_count': dish['off_count'],
                'original_labels': dish.get('original_labels', []),
                'score': dish.get('score', 0.0),
                'moved_from': 'dishes'
            })
            continue

        # 有効な料理でない
        if not is_valid_dish(cleaned_label):
            dishes_invalid.append((label, "料理キーワードなし"))
            continue

        # 有効なBase
        dish['label'] = cleaned_label
        dishes_valid.append(dish)

    print(f"  料理: {len(dishes)} → {len(dishes_valid)} 項目")
    print(f"    → Ingredientへ移動: {len(dishes_moved_to_ingredient)} 項目")
    print(f"    → 削除: {len(dishes_invalid)} 項目")
    print()

    # 食材も厳格なファセット語除去を適用
    ingredients_valid = []
    ingredients_invalid = []

    # Baseから移動してきた項目を追加
    for item in dishes_moved_to_ingredient:
        ingredients_valid.append(item)

    for ingredient in ingredients:
        label = ingredient['label']

        # より厳格なファセット語除去
        cleaned_label = apply_strict_facet_removal(label)

        # 空白または短すぎる
        if not cleaned_label or len(cleaned_label) <= 2:
            ingredients_invalid.append((label, "空白または短すぎる"))
            continue

        # 有効な食材
        ingredient['label'] = cleaned_label
        ingredients_valid.append(ingredient)

    print(f"  食材: {len(ingredients)} + {len(dishes_moved_to_ingredient)} → {len(ingredients_valid)} 項目")
    print(f"    → 削除: {len(ingredients_invalid)} 項目")
    print()

    # 正規化後のラベルでグループ化（重複を統合）
    print("🔀 ラベル重複を統合中...")

    dishes_grouped = defaultdict(lambda: {'off_count': 0, 'items': []})
    for dish in dishes_valid:
        label = dish['label']
        dishes_grouped[label]['off_count'] += dish['off_count']
        dishes_grouped[label]['items'].extend(dish.get('original_labels', [label]))

    ingredients_grouped = defaultdict(lambda: {'off_count': 0, 'items': []})
    for ingredient in ingredients_valid:
        label = ingredient['label']
        ingredients_grouped[label]['off_count'] += ingredient['off_count']
        ingredients_grouped[label]['items'].extend(ingredient.get('original_labels', [label]))

    # 最終リスト作成
    dishes_final = []
    for label, data in dishes_grouped.items():
        dishes_final.append({
            'label': label,
            'off_count': data['off_count'],
            'original_labels': list(set(data['items'])),
            'score': 0.0  # 後でスコアリング
        })

    ingredients_final = []
    for label, data in ingredients_grouped.items():
        ingredients_final.append({
            'label': label,
            'off_count': data['off_count'],
            'original_labels': list(set(data['items'])),
            'score': 0.0
        })

    print(f"  料理: {len(dishes_final):,} 項目（重複統合後）")
    print(f"  食材: {len(ingredients_final):,} 項目（重複統合後）")
    print()

    # 出力
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    dishes_output = output_dir / "dishes_spec4_filtered.json"
    ingredients_output = output_dir / "ingredients_spec4_filtered.json"

    print("💾 spec4準拠データを保存中...")
    with open(dishes_output, 'w', encoding='utf-8') as f:
        json.dump(dishes_final, f, indent=2, ensure_ascii=False)
    print(f"  料理: {dishes_output}")

    with open(ingredients_output, 'w', encoding='utf-8') as f:
        json.dump(ingredients_final, f, indent=2, ensure_ascii=False)
    print(f"  食材: {ingredients_output}")
    print()

    # 統計情報
    print("="*80)
    print("spec4.md適用結果サマリー")
    print("="*80)
    print(f"料理: {len(dishes)} → {len(dishes_final)} 項目")
    print(f"  Ingredientへ移動: {len(dishes_moved_to_ingredient)} 項目")
    print(f"  削除: {len(dishes_invalid)} 項目")
    print()

    print(f"食材: {len(ingredients)} → {len(ingredients_final)} 項目")
    print(f"  削除: {len(ingredients_invalid)} 項目")
    print()

    # 削除された料理の例
    if dishes_invalid:
        print("削除された料理の例（最初の20項目）:")
        for i, (label, reason) in enumerate(dishes_invalid[:20], 1):
            print(f"  {i:3d}. {label:50s} ({reason})")
        print()

    # Ingredientへ移動した項目の例
    if dishes_moved_to_ingredient:
        print("Baseから Ingredientへ移動した項目（最初の20項目）:")
        for i, item in enumerate(dishes_moved_to_ingredient[:20], 1):
            print(f"  {i:3d}. {item['label']:50s} (OFF: {item['off_count']:,})")
        print()

    print("✅ 次のステップ:")
    print("  1. 魚介名の正規化（FDA Seafood List）")
    print("  2. 不足している料理の追加（ramen, pho等）")
    print("  3. チーズの圧縮（10-12種）")
    print("  4. 最終スコアリングと上位選択（Base 350-400, Ingredient 600-800）")
    print()


if __name__ == "__main__":
    main()
