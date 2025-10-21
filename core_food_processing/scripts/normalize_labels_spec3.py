#!/usr/bin/env python3
"""
normalize_labels_spec3.py

spec3.mdに基づいてラベルを正規化するスクリプト

主要な処理:
1. ファセット語（加工・包装・品質属性）を除去
2. 視覚アンカーのないラベルを除外
3. 同義語を代表語に縮約
4. 視覚で区別できる正規名に変換

Usage:
    python core_food_processing/scripts/normalize_labels_spec3.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent


# spec3.mdに基づく除外ストップワード
FACET_STOPWORDS = [
    # 加工状態
    r'\bpowder(ed)?\b', r'\bmix\b', r'\bbase\b', r'\bseasoning\b',
    r'\bconcentrate(d)?\b', r'\binstant\b', r'\bdehydrated\b',
    r'\bfreeze-dried\b', r'\bpasteurized\b', r'\bfreeze-concentrated\b',
    r'\bspray-dried\b', r'\bsoft curd\b',

    # 包装・保存
    r'\bcanned\b', r'\bfrozen\b', r'\bpacket\b', r'\bshelf stable\b',
    r'\bprepacked\b', r'\bready-to-bake\b', r'\bbottled\b',
    r'\bindividually wrapped\b', r'\bin paper carton\b',

    # 品質・栄養属性
    r'\bartificial(ly)?\s+(flavor(ed)?|color(ed)?)\b',
    r'\blow\s+(sodium|fat|calorie|alcohol)\b',
    r'\breduced\s+(fat|sodium|calorie)\b',
    r'\bfat\s+free\b', r'\blight\b', r'\bdiet\b',
    r'\bvitamin\s+d\s+added\b', r'\bfortified\b',
    r'\bsalt-free\b', r'\bunsalted\b', r'\bsalted\b',
    r'\bsweet\b', r'\bsweetened\b', r'\bunsweetened\b',

    # 加工度・調理状態（過度に詳細）
    r'\braw\b', r'\bcooked\b', r'\bchilled\b', r'\boven-cooked\b',
    r'\bpit barbeque cooked\b', r'\bfried\b',
    r'\bhomogenized\b', r'\bfermented\b',
    r'\bpeeled\b', r'\bdeveined\b', r'\bbreaded\b',
    r'\bgrated\b', r'\bshredded\b', r'\bsliced\b',

    # メーカー・製法特性
    r'\bfor manufacturing\b', r'\brenovated\b', r'\blipolyzed\b',
    r'\bdeodorized\b', r'\bhydrogenated\b', r'\banhydrous\b',
    r'\bfrom concentrate\b', r'\bmade from concentrate\b',

    # その他
    r'\bNFS\b', r'\bNS\b',  # これらは後で特別処理
    r'\bunspecified\b', r'\bgeneral\b',
]

# 視覚アンカー（料理）- これらを含むものは残す
VISUAL_ANCHOR_DISHES = [
    'soup', 'stew', 'curry', 'pizza', 'pasta', 'noodle', 'ramen',
    'rice', 'taco', 'burrito', 'quesadilla', 'enchilada', 'nachos',
    'salad', 'burger', 'sandwich', 'fries', 'dumpling', 'roll',
    'waffle', 'pancake', 'omelet', 'kebab', 'skewer', 'sushi',
    'lasagna', 'gnocchi', 'ravioli', 'cake', 'cookie', 'brownie',
    'pie', 'tart', 'ice cream', 'pudding', 'yogurt',
    'popcorn', 'chips', 'crackers', 'pretzels',
]

# 視覚アンカー（食材） - 基本的な食材名
VISUAL_ANCHOR_INGREDIENTS = [
    'beef', 'pork', 'chicken', 'turkey', 'lamb', 'duck',
    'fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster',
    'milk', 'cheese', 'butter', 'cream', 'egg', 'yogurt',
    'lettuce', 'tomato', 'onion', 'garlic', 'pepper', 'carrot',
    'potato', 'rice', 'bread', 'pasta', 'oil',
]


def remove_facets(label: str) -> str:
    """
    ファセット語（加工・包装・品質属性）を除去

    Args:
        label: 元のラベル

    Returns:
        ファセット語を除去したラベル
    """
    cleaned = label

    # 括弧内の内容を全て削除
    cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)

    # ストップワードを削除
    for pattern in FACET_STOPWORDS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # カンマで区切られた修飾語を削除
    # 例: "chicken, grilled, seasoned" → "chicken"
    parts = cleaned.split(',')
    if len(parts) > 1:
        cleaned = parts[0]  # 最初の部分のみ保持

    # 連続する空白を1つに
    cleaned = ' '.join(cleaned.split())

    return cleaned.strip()


def has_visual_anchor(label: str, is_dish: bool = True) -> bool:
    """
    視覚アンカーを持つかどうかを判定

    Args:
        label: ラベル
        is_dish: 料理かどうか

    Returns:
        視覚アンカーがある場合True
    """
    label_lower = label.lower()

    anchors = VISUAL_ANCHOR_DISHES if is_dish else VISUAL_ANCHOR_INGREDIENTS

    for anchor in anchors:
        if anchor in label_lower:
            return True

    return False


def should_exclude_beverage(label: str) -> bool:
    """
    除外すべき飲料かどうかを判定

    spec3.mdによると、飲料は極少数に限定
    """
    label_lower = label.lower()

    # 許可する飲料（視覚で区別しやすい）
    allowed_beverages = [
        'beer', 'wine', 'sake', 'soda', 'cola',
        'coffee', 'tea', 'juice', 'smoothie', 'shake',
        'water', 'milk', 'kefir',
    ]

    # 許可リストに含まれるかチェック
    for allowed in allowed_beverages:
        if allowed in label_lower:
            return False

    # beverage, drink, liquor などの一般的な飲料ラベルは除外
    if any(word in label_lower for word in ['beverage', 'drink', 'liquor', 'wine food product']):
        return True

    return False


def normalize_to_base_form(label: str, all_labels: Set[str]) -> str:
    """
    同義語を代表語に縮約

    例: "ice cream (artificially flavored)" → "ice cream"
         "shrimp (raw)" → "shrimp"
    """
    # ファセット除去
    base = remove_facets(label)

    # 既に存在する場合はそのまま返す
    if base in all_labels:
        return base

    return base


def main():
    """メイン処理"""
    print("="*80)
    print("ラベル正規化スクリプト（spec3.md準拠）")
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

    # 正規化と統合
    print("🔧 ラベルを正規化中...")

    # 料理の正規化
    dishes_normalized = defaultdict(lambda: {'off_count': 0, 'items': []})
    dishes_excluded = []

    for dish in dishes:
        original_label = dish['label']
        normalized_label = remove_facets(original_label)

        # 視覚アンカーチェック
        if not has_visual_anchor(normalized_label, is_dish=True):
            dishes_excluded.append((original_label, "視覚アンカーなし"))
            continue

        # 飲料の除外チェック
        if should_exclude_beverage(normalized_label):
            dishes_excluded.append((original_label, "除外すべき飲料"))
            continue

        # 空白または短すぎる
        if not normalized_label or len(normalized_label) <= 2:
            dishes_excluded.append((original_label, "空白または短すぎる"))
            continue

        # 正規化後のラベルでグループ化（OFF頻度を合算）
        dishes_normalized[normalized_label]['off_count'] += dish['off_count']
        dishes_normalized[normalized_label]['items'].append(original_label)

    print(f"  料理: {len(dishes_normalized):,} 項目に正規化（{len(dishes_excluded):,} 項目除外）")

    # 食材の正規化
    ingredients_normalized = defaultdict(lambda: {'off_count': 0, 'items': []})
    ingredients_excluded = []

    for ingredient in ingredients:
        original_label = ingredient['label']
        normalized_label = remove_facets(original_label)

        # 視覚アンカーチェック（食材は緩め）
        if not has_visual_anchor(normalized_label, is_dish=False):
            # 基本的な食材名でなければ除外
            if len(normalized_label.split()) > 3:  # 3単語以上は複雑すぎる
                ingredients_excluded.append((original_label, "複雑すぎる"))
                continue

        # 空白または短すぎる
        if not normalized_label or len(normalized_label) <= 2:
            ingredients_excluded.append((original_label, "空白または短すぎる"))
            continue

        # 正規化後のラベルでグループ化
        ingredients_normalized[normalized_label]['off_count'] += ingredient['off_count']
        ingredients_normalized[normalized_label]['items'].append(original_label)

    print(f"  食材: {len(ingredients_normalized):,} 項目に正規化（{len(ingredients_excluded):,} 項目除外）")
    print()

    # 正規化後のデータを作成
    dishes_final = []
    for label, data in dishes_normalized.items():
        dishes_final.append({
            'label': label,
            'off_count': data['off_count'],
            'original_labels': data['items'],
            'score': 0.0  # 後でスコアリング
        })

    ingredients_final = []
    for label, data in ingredients_normalized.items():
        ingredients_final.append({
            'label': label,
            'off_count': data['off_count'],
            'original_labels': data['items'],
            'score': 0.0
        })

    # 出力
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    dishes_normalized_json = output_dir / "dishes_normalized_spec3.json"
    ingredients_normalized_json = output_dir / "ingredients_normalized_spec3.json"

    print("💾 正規化データを保存中...")
    with open(dishes_normalized_json, 'w', encoding='utf-8') as f:
        json.dump(dishes_final, f, indent=2, ensure_ascii=False)
    print(f"  料理: {dishes_normalized_json}")

    with open(ingredients_normalized_json, 'w', encoding='utf-8') as f:
        json.dump(ingredients_final, f, indent=2, ensure_ascii=False)
    print(f"  食材: {ingredients_normalized_json}")
    print()

    # 統計情報
    print("="*80)
    print("正規化結果サマリー")
    print("="*80)
    print(f"料理: {len(dishes):,} → {len(dishes_final):,} 項目（{len(dishes_excluded):,} 除外）")
    print(f"食材: {len(ingredients):,} → {len(ingredients_final):,} 項目（{len(ingredients_excluded):,} 除外）")
    print()

    # 除外理由の内訳
    if dishes_excluded:
        print("料理除外理由（最初の20項目）:")
        for i, (label, reason) in enumerate(dishes_excluded[:20], 1):
            print(f"  {i:3d}. {label:50s} ({reason})")
        print()

    # 縮約例
    print("縮約例（複数→1つに統合された料理、最初の10項目）:")
    count = 0
    for label, data in sorted(dishes_normalized.items(), key=lambda x: len(x[1]['items']), reverse=True):
        if len(data['items']) > 1:
            count += 1
            print(f"{count:3d}. {label}")
            for original in data['items'][:3]:
                print(f"       ← {original}")
            if len(data['items']) > 3:
                print(f"       ... (+{len(data['items'])-3} more)")
            if count >= 10:
                break
    print()

    print("✅ 次のステップ:")
    print("  1. CV準拠（Food-101/UEC/Vireo）の料理名をマッピング")
    print("  2. スコアリングと上位選択（350-500 / 600-900）")
    print()


if __name__ == "__main__":
    main()
