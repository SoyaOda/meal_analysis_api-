#!/usr/bin/env python3
"""
compress_ingredients_spec4.py

spec4.md R5, R7に基づくIngredient圧縮

主要な処理:
1. チーズを10-12種の主要品種に圧縮
2. 魚介をFDA Acceptable Market Nameに正規化
3. 視覚で区別できない食材を削除
4. 目標サイズ（600-800）への調整

Usage:
    python core_food_processing/scripts/compress_ingredients_spec4.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent


# spec4.md R7: 主要チーズ（10-12種）
CORE_CHEESES = {
    'cheddar': 'cheddar cheese',
    'mozzarella': 'mozzarella cheese',
    'parmesan': 'parmesan cheese',
    'swiss': 'swiss cheese',
    'feta': 'feta cheese',
    'ricotta': 'ricotta cheese',
    'cream cheese': 'cream cheese',
    'cottage cheese': 'cottage cheese',
    'colby': 'colby cheese',
    'pepper jack': 'pepper jack cheese',
    'muenster': 'muenster cheese',
    'blue cheese': 'blue cheese',
}


# spec4.md R5: FDA Seafood List - Acceptable Market Names
FDA_SEAFOOD_NAMES = {
    # Finfish
    'pollock': ['alaska pollock', 'atlantic pollock'],
    'salmon': ['chinook salmon', 'coho salmon', 'sockeye salmon', 'pink salmon', 'chum salmon', 'atlantic salmon', 'king salmon', 'salmon trout'],
    'tuna': ['albacore', 'yellowfin tuna', 'skipjack tuna', 'bigeye tuna'],
    'cod': ['atlantic cod', 'pacific cod'],
    'haddock': ['haddock'],
    'halibut': ['pacific halibut', 'atlantic halibut'],
    'tilapia': ['tilapia'],
    'catfish': ['channel catfish'],
    'trout': ['rainbow trout', 'lake trout'],
    'swordfish': ['swordfish'],
    'mahi mahi': ['dolphinfish', 'dorado'],

    # Shellfish
    'shrimp': ['white shrimp', 'pink shrimp', 'brown shrimp', 'tiger shrimp', 'rock shrimp'],
    'crab': ['blue crab', 'dungeness crab', 'king crab', 'snow crab', 'rock crab', 'spider crab'],
    'lobster': ['american lobster', 'spiny lobster', 'rock lobster tail', 'northern lobster'],
    'scallop': ['sea scallop', 'bay scallop'],
    'clam': ['hard clam', 'soft clam', 'surf clam', 'manila clam', 'razor clam', 'pacific razor clam'],
    'oyster': ['eastern oyster', 'pacific oyster', 'olympia oyster'],
    'mussel': ['blue mussel', 'green mussel'],
}


# 削除すべき食材パターン（視覚で区別不可・家庭用食事に出ない）
INVALID_INGREDIENT_PATTERNS = [
    r'\bdog food\b',
    r'\binfant food\b',
    r'\bformula\b',
    r'\banhydrous\b',
    r'\blipolyzed\b',
    r'\bdeodorized\b',
    r'\bhydrogenated\b',
    r'\brenovated\b',
    r'\bfor manufacturing\b',
]


def normalize_cheese_name(label: str) -> str | None:
    """
    チーズ名を主要12種に正規化

    Args:
        label: 元のラベル

    Returns:
        正規化後のチーズ名、または None（削除対象）
    """
    label_lower = label.lower()

    # チーズ判定
    if 'cheese' not in label_lower:
        return None

    # 主要チーズにマッチング
    for core_name, canonical_name in CORE_CHEESES.items():
        if core_name in label_lower:
            return canonical_name

    # 主要チーズに含まれないチーズは削除
    return None


def normalize_seafood_name(label: str) -> str | None:
    """
    魚介名をFDA Acceptable Market Nameに正規化

    Args:
        label: 元のラベル

    Returns:
        正規化後の魚介名、または None（そのまま保持 or 削除）
    """
    label_lower = label.lower()

    # FDA Seafood Listにマッチング
    for market_name, variants in FDA_SEAFOOD_NAMES.items():
        for variant in variants:
            if variant in label_lower:
                return market_name

        # market_name自体も確認
        if market_name in label_lower:
            return market_name

    # 魚介関連キーワードがあるが、FDA Listにない場合は削除候補
    seafood_keywords = ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'clam', 'oyster', 'mussel', 'scallop']
    if any(kw in label_lower for kw in seafood_keywords):
        # FDA Listに含まれない魚介は削除
        return None

    # 魚介でない場合はそのまま
    return label


def is_invalid_ingredient(label: str) -> bool:
    """
    削除すべき食材かどうかを判定

    Args:
        label: ラベル

    Returns:
        削除すべき場合True
    """
    label_lower = label.lower()

    for pattern in INVALID_INGREDIENT_PATTERNS:
        if re.search(pattern, label_lower):
            return True

    return False


def main():
    """メイン処理"""
    print("="*80)
    print("spec4.md準拠 Ingredient圧縮スクリプト")
    print("="*80)
    print()

    # 入力ファイル
    ingredients_filtered = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_spec4_filtered.json"

    # データを読み込み
    print("📖 spec4フィルタ済みデータを読み込み中...")
    with open(ingredients_filtered, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  現在の食材数: {len(ingredients):,} 項目")
    print()

    # spec4.md R5, R7 を適用
    print("🔧 spec4.md R5, R7 を適用中...")
    print()

    ingredients_valid = []
    cheese_compressed = []
    seafood_normalized = []
    ingredients_invalid = []

    cheese_groups = defaultdict(lambda: {'off_count': 0, 'items': []})
    seafood_groups = defaultdict(lambda: {'off_count': 0, 'items': []})

    for ingredient in ingredients:
        label = ingredient['label']

        # 不適切な食材
        if is_invalid_ingredient(label):
            ingredients_invalid.append((label, "不適切（dog food等）"))
            continue

        # チーズの正規化
        normalized_cheese = normalize_cheese_name(label)
        if normalized_cheese:
            cheese_groups[normalized_cheese]['off_count'] += ingredient['off_count']
            cheese_groups[normalized_cheese]['items'].extend(ingredient.get('original_labels', [label]))
            cheese_compressed.append(label)
            continue

        # 魚介の正規化
        normalized_seafood = normalize_seafood_name(label)
        if normalized_seafood and normalized_seafood != label:
            # 正規化された
            seafood_groups[normalized_seafood]['off_count'] += ingredient['off_count']
            seafood_groups[normalized_seafood]['items'].extend(ingredient.get('original_labels', [label]))
            seafood_normalized.append(label)
            continue
        elif normalized_seafood is None and any(kw in label.lower() for kw in ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'clam', 'oyster', 'mussel', 'scallop']):
            # FDA Listにない魚介は削除
            ingredients_invalid.append((label, "FDA Listにない魚介"))
            continue

        # その他の食材はそのまま保持
        ingredients_valid.append(ingredient)

    # チーズと魚介のグループを追加
    for cheese_name, data in cheese_groups.items():
        ingredients_valid.append({
            'label': cheese_name,
            'off_count': data['off_count'],
            'original_labels': list(set(data['items'])),
            'score': 0.0
        })

    for seafood_name, data in seafood_groups.items():
        ingredients_valid.append({
            'label': seafood_name,
            'off_count': data['off_count'],
            'original_labels': list(set(data['items'])),
            'score': 0.0
        })

    print(f"  食材: {len(ingredients)} → {len(ingredients_valid)} 項目")
    print(f"    チーズ圧縮: {len(cheese_compressed)} → {len(cheese_groups)} 種")
    print(f"    魚介正規化: {len(seafood_normalized)} → {len(seafood_groups)} 種")
    print(f"    削除: {len(ingredients_invalid)} 項目")
    print()

    # 出力
    output_file = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_spec4_compressed.json"

    print("💾 圧縮データを保存中...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ingredients_valid, f, indent=2, ensure_ascii=False)
    print(f"  {output_file}")
    print()

    # サマリー
    print("="*80)
    print("圧縮結果サマリー")
    print("="*80)
    print(f"食材: {len(ingredients)} → {len(ingredients_valid)} 項目")
    print()

    # チーズの内訳
    print("チーズ（12種に圧縮）:")
    for cheese_name in sorted(cheese_groups.keys()):
        original_count = len(cheese_groups[cheese_name]['items'])
        off_count = cheese_groups[cheese_name]['off_count']
        print(f"  {cheese_name:30s}: {original_count:3d}種統合, OFF {off_count:,} ヒット")
    print()

    # 魚介の内訳
    print("魚介（FDA Acceptable Market Name）:")
    for seafood_name in sorted(seafood_groups.keys()):
        original_count = len(seafood_groups[seafood_name]['items'])
        off_count = seafood_groups[seafood_name]['off_count']
        print(f"  {seafood_name:30s}: {original_count:3d}種統合, OFF {off_count:,} ヒット")
    print()

    # 削除例
    if ingredients_invalid:
        print("削除された食材の例（最初の20項目）:")
        for i, (label, reason) in enumerate(ingredients_invalid[:20], 1):
            print(f"  {i:3d}. {label:50s} ({reason})")
        print()

    # 目標との比較
    target_min = 600
    target_max = 800

    if target_min <= len(ingredients_valid) <= target_max:
        status = "✅ 目標範囲内"
    elif len(ingredients_valid) < target_min:
        status = f"⚠️ 目標より少ない（あと{target_min - len(ingredients_valid)}項目必要）"
    else:
        status = f"⚠️ 目標より多い（{len(ingredients_valid) - target_max}項目削減可能）"

    print(f"目標: {target_min}-{target_max} 項目 → {status}")
    print()

    print("✅ 次のステップ:")
    print("  1. 最終スコアリングと上位選択（Ingredient 600-800）")
    print("  2. spec4.md形式で最終成果物を生成")
    print()


if __name__ == "__main__":
    main()
