#!/usr/bin/env python3
"""
extract_foodon_hierarchical.py

FoodOnオントロジーから階層構造に基づいて料理と食材を分離するスクリプト

仕様（spec1.md）に基づく実装:
- FOODON_00002501 (Multi-component food product) → 料理候補
- FOODON_00002381 (Food product by organism) → 食材候補

Usage:
    python core_food_processing/scripts/extract_foodon_hierarchical.py
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent

# owlready2のインポート
try:
    from owlready2 import get_ontology, Thing
except ImportError:
    print("❌ エラー: owlready2がインストールされていません")
    print("次のコマンドでインストールしてください:")
    print("  pip install owlready2")
    sys.exit(1)


# FoodOnの主要なクラスID
MULTI_COMPONENT_FOOD = "FOODON_00002501"  # Multi-component food product (料理)
FOOD_BY_ORGANISM = "FOODON_00002381"      # Food product by organism (食材)


def extract_label(entity) -> str:
    """
    エンティティからラベルを抽出（英語優先）

    Args:
        entity: オントロジーエンティティ

    Returns:
        ラベル文字列（英語優先、クリーンアップ済み）
    """
    try:
        # labelプロパティから取得
        if hasattr(entity, 'label') and entity.label:
            labels = entity.label if isinstance(entity.label, list) else [entity.label]
            for label in labels:
                if isinstance(label, str):
                    # クリーンアップ: コード番号とソース情報を削除
                    cleaned = clean_label(label)
                    if cleaned:
                        return cleaned
    except (ValueError, AttributeError, TypeError):
        pass

    try:
        # prefLabelプロパティから取得
        if hasattr(entity, 'prefLabel') and entity.prefLabel:
            labels = entity.prefLabel if isinstance(entity.prefLabel, list) else [entity.prefLabel]
            for label in labels:
                if isinstance(label, str):
                    cleaned = clean_label(label)
                    if cleaned:
                        return cleaned
    except (ValueError, AttributeError, TypeError):
        pass

    try:
        # 名前から取得（最後の手段）
        if hasattr(entity, 'name'):
            name = entity.name
            # 数字のみのIDは無視
            if not re.match(r'^\d+$', name) and not name.startswith('FOODON_'):
                return name.replace('_', ' ')
    except (ValueError, AttributeError, TypeError):
        pass

    return ""


def clean_label(label: str) -> str:
    """
    ラベルをクリーンアップ（コード番号とソース情報を削除）

    Args:
        label: 元のラベル

    Returns:
        クリーンアップされたラベル
    """
    # 例: "03310 - porridge water based (ready to eat) (efsa foodex2)"
    #  → "porridge water based (ready to eat)"

    # 先頭の数字コードとハイフンを削除
    label = re.sub(r'^\d+\s*-\s*', '', label)

    # ソース情報（括弧内）を削除
    # (efsa foodex2), (gs1 gpc), (eurocode2), (efg) など
    label = re.sub(r'\s*\((efsa foodex2|gs1 gpc|eurocode\d+|efg)\)\s*$', '', label, flags=re.IGNORECASE)

    # 余分な空白を削除
    label = ' '.join(label.split())

    return label.strip()


def extract_synonyms(entity) -> List[str]:
    """
    エンティティから同義語を抽出

    Args:
        entity: オントロジーエンティティ

    Returns:
        同義語のリスト（クリーンアップ済み）
    """
    synonyms = []

    # hasExactSynonym プロパティ
    if hasattr(entity, 'hasExactSynonym'):
        syns = entity.hasExactSynonym if isinstance(entity.hasExactSynonym, list) else [entity.hasExactSynonym]
        for syn in syns:
            if isinstance(syn, str) and syn.strip():
                cleaned = clean_label(syn.strip())
                if cleaned:
                    synonyms.append(cleaned)

    # hasRelatedSynonym プロパティ
    if hasattr(entity, 'hasRelatedSynonym'):
        syns = entity.hasRelatedSynonym if isinstance(entity.hasRelatedSynonym, list) else [entity.hasRelatedSynonym]
        for syn in syns:
            if isinstance(syn, str) and syn.strip():
                cleaned = clean_label(syn.strip())
                if cleaned:
                    synonyms.append(cleaned)

    return list(set(synonyms))  # 重複削除


def is_ancestor(cls, target_name: str, max_depth: int = 10) -> bool:
    """
    クラスが指定された祖先クラスを持つかチェック（再帰的）

    Args:
        cls: チェック対象のクラス
        target_name: 祖先として探すクラス名（例: "FOODON_00002501"）
        max_depth: 最大探索深度

    Returns:
        祖先として持つ場合True
    """
    if max_depth <= 0:
        return False

    if not hasattr(cls, 'is_a'):
        return False

    # 直接の親をチェック
    for parent in cls.is_a:
        if hasattr(parent, 'name') and parent.name == target_name:
            return True

    # 再帰的に祖先をチェック
    for parent in cls.is_a:
        if hasattr(parent, 'is_a'):
            if is_ancestor(parent, target_name, max_depth - 1):
                return True

    return False


def should_exclude(label: str) -> bool:
    """
    ノイズとして除外すべきラベルかどうかを判定

    Args:
        label: ラベル文字列

    Returns:
        除外すべき場合True
    """
    label_lower = label.lower()

    # 除外キーワード（仕様より）
    exclude_keywords = [
        'packaging', 'package', 'container',
        'process', 'processing',
        'material', 'equipment',
        'unspecified', 'nfs alone', 'ns alone',
        'variety pack', 'variety packs',
    ]

    for keyword in exclude_keywords:
        if keyword in label_lower:
            return True

    # 数字のみは除外
    if re.match(r'^\d+$', label):
        return True

    # 短すぎる（2文字以下）は除外
    if len(label) <= 2:
        return True

    return False


def main():
    """メイン処理"""
    print("="*80)
    print("FoodOn 階層ベース料理/食材分離スクリプト")
    print("="*80)
    print()

    # FoodOnオントロジーのパス
    foodon_path = PROJECT_ROOT / "core_food_processing" / "data" / "foodon.owl"

    if not foodon_path.exists():
        print(f"❌ エラー: {foodon_path} が存在しません")
        sys.exit(1)

    print(f"FoodOnオントロジーを読み込み中: {foodon_path}")
    print(f"ファイルサイズ: {foodon_path.stat().st_size / (1024*1024):.1f} MB")
    print()

    # オントロジーを読み込み
    print("⏳ オントロジーをパース中...")
    try:
        onto = get_ontology(str(foodon_path)).load()
        print("✅ オントロジーの読み込み完了")
    except Exception as e:
        print(f"❌ エラー: オントロジーの読み込みに失敗: {e}")
        sys.exit(1)

    print()

    # 全クラスを取得
    print("🔍 FoodOnクラスを分析中...")
    all_classes = list(onto.classes())
    print(f"  総クラス数: {len(all_classes):,}")
    print()

    # 料理と食材を分離
    print("📂 料理と食材を分離中...")
    dishes: List[Tuple[str, str, List[str]]] = []  # (URI, label, synonyms)
    ingredients: List[Tuple[str, str, List[str]]] = []

    skipped_count = 0
    multi_component_count = 0
    by_organism_count = 0

    for cls in all_classes:
        # ラベルを取得
        label = extract_label(cls)

        # ラベルが空の場合はスキップ
        if not label:
            skipped_count += 1
            continue

        # ノイズとして除外
        if should_exclude(label):
            skipped_count += 1
            continue

        # URIを取得
        uri = str(cls.iri) if hasattr(cls, 'iri') else cls.name

        # 同義語を取得
        synonyms = extract_synonyms(cls)

        # 祖先チェックで分類
        is_multi_component = is_ancestor(cls, MULTI_COMPONENT_FOOD)
        is_by_organism = is_ancestor(cls, FOOD_BY_ORGANISM)

        if is_multi_component:
            dishes.append((uri, label, synonyms))
            multi_component_count += 1
        elif is_by_organism:
            ingredients.append((uri, label, synonyms))
            by_organism_count += 1
        else:
            # どちらでもない場合はスキップ
            skipped_count += 1

    print(f"  料理候補（Multi-component food product）: {multi_component_count:,} 項目")
    print(f"  食材候補（Food product by organism）: {by_organism_count:,} 項目")
    print(f"  スキップ: {skipped_count:,} 項目")
    print()

    # 料理と食材をアルファベット順にソート
    dishes.sort(key=lambda x: x[1].lower())
    ingredients.sort(key=lambda x: x[1].lower())

    # 出力ディレクトリ
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    output_dir.mkdir(exist_ok=True, parents=True)

    # JSONファイルに保存（後続処理で使用）
    dishes_json = output_dir / "dishes_raw.json"
    ingredients_json = output_dir / "ingredients_raw.json"

    print(f"💾 結果を保存中...")

    # 料理を保存
    dishes_data = [
        {
            "uri": uri,
            "label": label,
            "synonyms": synonyms
        }
        for uri, label, synonyms in dishes
    ]

    with open(dishes_json, 'w', encoding='utf-8') as f:
        json.dump(dishes_data, f, indent=2, ensure_ascii=False)

    print(f"  料理候補: {dishes_json}")

    # 食材を保存
    ingredients_data = [
        {
            "uri": uri,
            "label": label,
            "synonyms": synonyms
        }
        for uri, label, synonyms in ingredients
    ]

    with open(ingredients_json, 'w', encoding='utf-8') as f:
        json.dump(ingredients_data, f, indent=2, ensure_ascii=False)

    print(f"  食材候補: {ingredients_json}")
    print()

    # テキストファイルにも保存（確認用）
    dishes_txt = output_dir / "dishes_raw.txt"
    with open(dishes_txt, 'w', encoding='utf-8') as f:
        f.write("## 料理候補（Multi-component food product）\n\n")
        f.write(f"総数: {len(dishes):,}\n\n")
        for uri, label, synonyms in dishes:
            f.write(f"* {label}\n")
            if synonyms:
                syn_text = ", ".join(synonyms[:3])
                if len(synonyms) > 3:
                    syn_text += f" (+{len(synonyms)-3} more)"
                f.write(f"  <!-- Synonyms: {syn_text} -->\n")
            f.write(f"  <!-- URI: {uri} -->\n")

    ingredients_txt = output_dir / "ingredients_raw.txt"
    with open(ingredients_txt, 'w', encoding='utf-8') as f:
        f.write("## 食材候補（Food product by organism）\n\n")
        f.write(f"総数: {len(ingredients):,}\n\n")
        for uri, label, synonyms in ingredients:
            f.write(f"* {label}\n")
            if synonyms:
                syn_text = ", ".join(synonyms[:3])
                if len(synonyms) > 3:
                    syn_text += f" (+{len(synonyms)-3} more)"
                f.write(f"  <!-- Synonyms: {syn_text} -->\n")
            f.write(f"  <!-- URI: {uri} -->\n")

    print("✅ 保存完了!")
    print()

    # サマリーを表示
    print("="*80)
    print("抽出結果サマリー")
    print("="*80)
    print(f"料理候補: {len(dishes):,} 項目")
    print(f"食材候補: {len(ingredients):,} 項目")
    print(f"合計: {len(dishes) + len(ingredients):,} 項目")
    print()
    print("出力ファイル:")
    print(f"  {dishes_json}")
    print(f"  {ingredients_json}")
    print(f"  {dishes_txt}")
    print(f"  {ingredients_txt}")
    print("="*80)
    print()

    # サンプルを表示
    print("料理候補サンプル（最初の10項目）:")
    print("-"*80)
    for i, (uri, label, synonyms) in enumerate(dishes[:10], 1):
        syn_text = f" (synonyms: {', '.join(synonyms[:2])})" if synonyms else ""
        print(f"{i:3d}. {label}{syn_text}")
    print("-"*80)
    print()

    print("食材候補サンプル（最初の10項目）:")
    print("-"*80)
    for i, (uri, label, synonyms) in enumerate(ingredients[:10], 1):
        syn_text = f" (synonyms: {', '.join(synonyms[:2])})" if synonyms else ""
        print(f"{i:3d}. {label}{syn_text}")
    print("-"*80)
    print()

    print("✅ 次のステップ:")
    print("  1. Open Food Facts APIから頻度データを取得")
    print("  2. スコアリングと上位選択")
    print("  3. CORE食品リストの生成")
    print()


if __name__ == "__main__":
    main()
