#!/usr/bin/env python3
"""
extract_foodon_core.py

FoodOnオントロジーからCORE食品リストを抽出し、
complete_prompt.txt形式で出力するスクリプト

Usage:
    python core_food_processing/scripts/extract_foodon_core.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent

# owlready2のインポート
try:
    from owlready2 import get_ontology
except ImportError:
    print("❌ エラー: owlready2がインストールされていません")
    print("次のコマンドでインストールしてください:")
    print("  pip install owlready2")
    sys.exit(1)


def extract_label(entity) -> str:
    """
    エンティティからラベルを抽出

    Args:
        entity: オントロジーエンティティ

    Returns:
        ラベル文字列（英語優先）
    """
    try:
        # labelプロパティから取得
        if hasattr(entity, 'label') and entity.label:
            # 英語ラベルを優先
            for label in entity.label:
                if isinstance(label, str):
                    return label.strip()
            # リストの最初の要素を返す
            if isinstance(entity.label, list) and len(entity.label) > 0:
                return str(entity.label[0]).strip()
    except (ValueError, AttributeError, TypeError):
        pass  # データ型エラーをスキップ

    try:
        # prefLabelプロパティから取得（OBO形式）
        if hasattr(entity, 'prefLabel') and entity.prefLabel:
            for label in entity.prefLabel:
                if isinstance(label, str):
                    return label.strip()
    except (ValueError, AttributeError, TypeError):
        pass

    try:
        # 名前から取得（最後の手段）
        if hasattr(entity, 'name'):
            # FOODON_xxxxxxx のような形式から読みやすい名前に変換
            name = entity.name
            # 数字のみのIDは無視
            if not re.match(r'^\d+$', name):
                # アンダースコアをスペースに変換して見やすくする
                return name.replace('_', ' ')
    except (ValueError, AttributeError, TypeError):
        pass

    return ""


def extract_synonyms(entity) -> List[str]:
    """
    エンティティから同義語を抽出

    Args:
        entity: オントロジーエンティティ

    Returns:
        同義語のリスト
    """
    synonyms = []

    # hasExactSynonym プロパティ
    if hasattr(entity, 'hasExactSynonym'):
        for syn in entity.hasExactSynonym:
            if isinstance(syn, str) and syn.strip():
                synonyms.append(syn.strip())

    # hasRelatedSynonym プロパティ
    if hasattr(entity, 'hasRelatedSynonym'):
        for syn in entity.hasRelatedSynonym:
            if isinstance(syn, str) and syn.strip():
                synonyms.append(syn.strip())

    return list(set(synonyms))  # 重複削除


def is_food_product(entity) -> bool:
    """
    エンティティがfood productカテゴリかどうかを判定

    Args:
        entity: オントロジーエンティティ

    Returns:
        food productならTrue
    """
    # クラスでない場合はFalse
    if not hasattr(entity, 'is_a'):
        return False

    # food productの親クラスをたどる
    # FoodOnでは "food product" (FOODON_00002403) が主要なカテゴリ
    for parent in entity.is_a:
        if hasattr(parent, 'name'):
            parent_name = parent.name.lower()
            # food product関連のクラス名をチェック
            if 'food' in parent_name and 'product' in parent_name:
                return True
            # 再帰的にチェック（最大3階層まで）
            if hasattr(parent, 'is_a'):
                for grandparent in parent.is_a:
                    if hasattr(grandparent, 'name'):
                        gp_name = grandparent.name.lower()
                        if 'food' in gp_name and 'product' in gp_name:
                            return True

    return False


def categorize_food(label: str) -> str:
    """
    食品ラベルからカテゴリを推定

    Args:
        label: 食品ラベル

    Returns:
        カテゴリ名
    """
    label_lower = label.lower()

    # カテゴリマッピング（キーワードベース）
    categories = {
        "Fruits": ["fruit", "apple", "banana", "berry", "citrus", "melon", "grape", "cherry", "peach", "pear"],
        "Vegetables": ["vegetable", "lettuce", "spinach", "carrot", "tomato", "cucumber", "pepper", "onion", "broccoli", "cabbage"],
        "Meats & Poultry": ["meat", "beef", "pork", "chicken", "turkey", "lamb", "veal", "poultry"],
        "Seafood": ["fish", "salmon", "tuna", "shrimp", "crab", "lobster", "shellfish", "seafood"],
        "Dairy": ["milk", "cheese", "yogurt", "butter", "cream", "dairy"],
        "Grains & Cereals": ["grain", "rice", "wheat", "oat", "barley", "cereal", "bread", "pasta", "noodle"],
        "Legumes & Beans": ["bean", "lentil", "pea", "chickpea", "legume", "soy"],
        "Nuts & Seeds": ["nut", "almond", "walnut", "peanut", "seed", "cashew", "pistachio"],
        "Beverages": ["beverage", "drink", "juice", "coffee", "tea", "soda", "water"],
        "Desserts & Sweets": ["dessert", "cake", "cookie", "candy", "chocolate", "ice cream", "sweet"],
        "Oils & Fats": ["oil", "fat", "margarine"],
        "Condiments & Sauces": ["sauce", "ketchup", "mustard", "mayo", "dressing", "condiment"],
        "Prepared Foods": ["pizza", "burger", "sandwich", "soup", "stew", "salad"],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in label_lower:
                return category

    return "Other Foods"


def main():
    """メイン処理"""
    print("="*80)
    print("FoodOn CORE食品リスト抽出スクリプト")
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

    # オントロジーを読み込み（時間がかかる場合があります）
    print("⏳ オントロジーをパース中...")
    try:
        onto = get_ontology(str(foodon_path)).load()
        print("✅ オントロジーの読み込み完了")
    except Exception as e:
        print(f"❌ エラー: オントロジーの読み込みに失敗: {e}")
        sys.exit(1)

    print()

    # 全クラスを取得
    print("🔍 food productクラスを抽出中...")
    all_classes = list(onto.classes())
    print(f"  総クラス数: {len(all_classes):,}")

    # food product関連のクラスを抽出
    food_items: Dict[str, Tuple[str, List[str]]] = {}  # URI -> (label, synonyms)

    for cls in all_classes:
        # ラベルを取得
        label = extract_label(cls)

        # ラベルが空の場合はスキップ
        if not label:
            continue

        # food productかどうかを簡易判定（ラベルに"food"が含まれる）
        # より厳密な判定は is_food_product() を使用可能
        label_lower = label.lower()
        if 'food' in label_lower or 'product' in label_lower or \
           any(keyword in label_lower for keyword in [
               'fruit', 'vegetable', 'meat', 'fish', 'grain', 'dairy',
               'beverage', 'bread', 'cheese', 'sauce', 'oil'
           ]):
            # 同義語を取得
            synonyms = extract_synonyms(cls)

            # URIを取得
            uri = str(cls.iri) if hasattr(cls, 'iri') else cls.name

            food_items[uri] = (label, synonyms)

    print(f"  抽出された食品項目数: {len(food_items):,}")
    print()

    # カテゴリごとに分類
    print("📂 カテゴリごとに分類中...")
    categorized_foods: Dict[str, List[Tuple[str, str, List[str]]]] = defaultdict(list)

    for uri, (label, synonyms) in food_items.items():
        category = categorize_food(label)
        categorized_foods[category].append((uri, label, synonyms))

    # カテゴリごとにソート
    for category in categorized_foods:
        categorized_foods[category].sort(key=lambda x: x[1])  # ラベルでソート

    print(f"  カテゴリ数: {len(categorized_foods)}")
    for category, items in sorted(categorized_foods.items()):
        print(f"    {category}: {len(items):,} 項目")
    print()

    # 出力ファイルに保存
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    output_dir.mkdir(exist_ok=True, parents=True)

    output_file = output_dir / "foodon_core_list.txt"

    print(f"💾 CORE食品リストを保存中: {output_file}")
    print()

    with open(output_file, 'w', encoding='utf-8') as f:
        # ヘッダー
        f.write("## EXACT_FOOD_LIST (CORE) - FoodOn Ontology\n\n")
        f.write("Generated from FoodOn ontology (CC-BY-4.0)\n")
        f.write(f"Total items: {len(food_items):,}\n")
        f.write(f"Categories: {len(categorized_foods)}\n\n")
        f.write("---\n\n")

        # カテゴリごとに出力
        for category, items in sorted(categorized_foods.items()):
            f.write(f"## {category}\n\n")

            for uri, label, synonyms in items:
                # メインラベル
                f.write(f"* {label}\n")

                # 同義語（コメントとして追加）
                if synonyms:
                    # 最初の3つの同義語のみを表示
                    syn_text = ", ".join(synonyms[:3])
                    if len(synonyms) > 3:
                        syn_text += f" (+{len(synonyms)-3} more)"
                    f.write(f"  <!-- Synonyms: {syn_text} -->\n")
                    # URI（コメントとして追加）
                    f.write(f"  <!-- URI: {uri} -->\n")

            f.write("\n")

    print("✅ 保存完了!")
    print()

    # サマリーを表示
    print("="*80)
    print("抽出結果サマリー")
    print("="*80)
    print(f"総食品項目数: {len(food_items):,}")
    print(f"カテゴリ数: {len(categorized_foods)}")
    print()
    print("カテゴリ別内訳:")
    for category, items in sorted(categorized_foods.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {category:30s}: {len(items):,} 項目")
    print()
    print(f"出力先: {output_file}")
    print("="*80)
    print()

    # サンプルを表示
    print("サンプル（最初の20項目）:")
    print("-"*80)
    count = 0
    for category, items in sorted(categorized_foods.items()):
        for uri, label, synonyms in items[:5]:
            count += 1
            syn_text = f" (synonyms: {', '.join(synonyms[:2])})" if synonyms else ""
            print(f"{count:3d}. [{category}] {label}{syn_text}")
            if count >= 20:
                break
        if count >= 20:
            break
    print("-"*80)
    print()


if __name__ == "__main__":
    main()
