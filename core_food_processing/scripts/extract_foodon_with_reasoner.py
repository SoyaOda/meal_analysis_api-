#!/usr/bin/env python3
"""
extract_foodon_with_reasoner.py

Reasonerを有効化してFoodOnから料理と食材を分離するスクリプト（spec2.md準拠）

仕様:
- Base food (料理): FOODON:00002501 (multi-component food product) の子孫
- Ingredient (食材): FOODON:00002381 (food product by organism) の子孫
- Reasonerを有効化してインポートと推論を解決

Usage:
    python core_food_processing/scripts/extract_foodon_with_reasoner.py
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent

try:
    from owlready2 import get_ontology, sync_reasoner_pellet
except ImportError:
    print("❌ エラー: owlready2がインストールされていません")
    sys.exit(1)


# FoodOnの主要なクラスID
MULTI_COMPONENT_FOOD = "FOODON_00002501"  # Multi-component food product (料理)

# 食材候補クラス（複数のアプローチ）
FOOD_BY_ORGANISM = "FOODON_00002381"      # Food product by organism (食材 - メイン)
FOOD_MATERIAL = "FOODON_00001872"         # Food material (to be processed)
ANIMAL_FOOD_PRODUCT = "FOODON_00004242"   # Animal food product
PLANT_FOOD_PRODUCT = "FOODON_03316003"    # Plant food product（検索で追加）

# 食材候補として使用するクラスのリスト
INGREDIENT_CLASSES = [
    FOOD_BY_ORGANISM,
    FOOD_MATERIAL,
    ANIMAL_FOOD_PRODUCT,
    # PLANT_FOOD_PRODUCTは後で検索
]


def clean_label(label: str) -> str:
    """ラベルをクリーンアップ"""
    # 先頭の数字コードとハイフンを削除
    label = re.sub(r'^\d+\s*-\s*', '', label)
    # ソース情報を削除
    label = re.sub(r'\s*\((efsa foodex2|gs1 gpc|eurocode\d+|efg)\)\s*$', '', label, flags=re.IGNORECASE)
    # 余分な空白を削除
    label = ' '.join(label.split())
    return label.strip()


def extract_label(entity) -> str:
    """エンティティからラベルを抽出"""
    try:
        if hasattr(entity, 'label') and entity.label:
            labels = entity.label if isinstance(entity.label, list) else [entity.label]
            for label in labels:
                label_str = str(label)
                # locstr形式の処理
                if label_str.startswith("locstr("):
                    # locstr('text', 'lang') から text を抽出
                    match = re.match(r"locstr\(['\"](.+?)['\"],\s*['\"](.+?)['\"]\)", label_str)
                    if match:
                        label_str = match.group(1)

                cleaned = clean_label(label_str)
                if cleaned and not cleaned.startswith('obsolete'):
                    return cleaned
    except (ValueError, AttributeError, TypeError):
        pass

    try:
        if hasattr(entity, 'prefLabel') and entity.prefLabel:
            labels = entity.prefLabel if isinstance(entity.prefLabel, list) else [entity.prefLabel]
            for label in labels:
                label_str = str(label)
                cleaned = clean_label(label_str)
                if cleaned and not cleaned.startswith('obsolete'):
                    return cleaned
    except (ValueError, AttributeError, TypeError):
        pass

    return ""


def extract_synonyms(entity) -> List[str]:
    """同義語を抽出"""
    synonyms = []

    if hasattr(entity, 'hasExactSynonym'):
        syns = entity.hasExactSynonym if isinstance(entity.hasExactSynonym, list) else [entity.hasExactSynonym]
        for syn in syns:
            if syn:
                syn_str = str(syn)
                cleaned = clean_label(syn_str)
                if cleaned:
                    synonyms.append(cleaned)

    if hasattr(entity, 'hasRelatedSynonym'):
        syns = entity.hasRelatedSynonym if isinstance(entity.hasRelatedSynonym, list) else [entity.hasRelatedSynonym]
        for syn in syns:
            if syn:
                syn_str = str(syn)
                cleaned = clean_label(syn_str)
                if cleaned:
                    synonyms.append(cleaned)

    return list(set(synonyms))


def should_exclude(label: str) -> bool:
    """除外すべきラベルかどうかを判定"""
    label_lower = label.lower()

    exclude_keywords = [
        'packaging', 'package', 'container',
        'process', 'processing',
        'material', 'equipment',
        'unspecified', 'nfs alone', 'ns alone',
        'variety pack', 'variety packs',
        'obsolete',
    ]

    for keyword in exclude_keywords:
        if keyword in label_lower:
            return True

    if re.match(r'^\d+$', label):
        return True

    if len(label) <= 2:
        return True

    return False


def get_all_descendants(cls, visited: Set = None) -> Set:
    """クラスの全子孫を取得（再帰的）"""
    if visited is None:
        visited = set()

    if cls in visited:
        return set()

    visited.add(cls)
    descendants = {cls}

    try:
        for subclass in cls.subclasses():
            descendants.update(get_all_descendants(subclass, visited))
    except:
        pass

    return descendants


def main():
    """メイン処理"""
    print("="*80)
    print("FoodOn Reasoner有効化版 - 料理/食材分離スクリプト（spec2.md準拠）")
    print("="*80)
    print()

    # 最新版を使用
    foodon_path = PROJECT_ROOT / "core_food_processing" / "data" / "foodon_latest.owl"

    if not foodon_path.exists():
        # フォールバック
        foodon_path = PROJECT_ROOT / "core_food_processing" / "data" / "foodon.owl"

    if not foodon_path.exists():
        print(f"❌ エラー: FoodOnファイルが存在しません")
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
        print(f"❌ エラー: {e}")
        sys.exit(1)

    print()

    # Reasonerを実行（推論を有効化）
    print("🧠 Reasoner（推論エンジン）を実行中...")
    print("   ※これには数分かかる場合があります...")
    try:
        with onto:
            sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
        print("✅ Reasonerの実行完了")
    except Exception as e:
        print(f"⚠️  警告: Reasonerの実行に失敗しました（スキップして続行）: {e}")
        print("   推論なしで処理を続けます...")

    print()

    # 目的のクラスを検索
    print(f"🔍 目的のクラスを検索中...")
    multi_comp_class = None
    ingredient_classes = {}  # class_id -> class_object

    all_classes_dict = {}
    for cls in onto.classes():
        if hasattr(cls, 'name'):
            all_classes_dict[cls.name] = cls

    # 料理クラスを検索
    if MULTI_COMPONENT_FOOD in all_classes_dict:
        multi_comp_class = all_classes_dict[MULTI_COMPONENT_FOOD]
        print(f"✅ {MULTI_COMPONENT_FOOD} が見つかりました")
        multi_label = extract_label(multi_comp_class)
        print(f"   Label: {multi_label}")
    else:
        print(f"❌ エラー: {MULTI_COMPONENT_FOOD} が見つかりません")
        sys.exit(1)

    # 食材クラスを検索
    print()
    print("🔍 食材候補クラスを検索中...")
    for class_id in INGREDIENT_CLASSES:
        if class_id in all_classes_dict:
            ingredient_classes[class_id] = all_classes_dict[class_id]
            label = extract_label(all_classes_dict[class_id])
            print(f"✅ {class_id}: {label if label else '(no label)'}")
        else:
            print(f"⚠️  {class_id} が見つかりません（スキップ）")

    if not ingredient_classes:
        print(f"❌ エラー: 食材候補クラスが1つも見つかりません")
        sys.exit(1)

    print()

    # 子孫クラスを取得
    print("📂 子孫クラスを取得中...")

    print(f"   {MULTI_COMPONENT_FOOD} の子孫を取得中...")
    multi_descendants = get_all_descendants(multi_comp_class)
    print(f"   ✅ {len(multi_descendants):,} クラス")

    # 食材候補の子孫を取得（複数クラスを統合）
    all_ingredient_descendants = set()
    for class_id, cls in ingredient_classes.items():
        print(f"   {class_id} の子孫を取得中...")
        descendants = get_all_descendants(cls)
        print(f"   ✅ {len(descendants):,} クラス")
        all_ingredient_descendants.update(descendants)

    # 重複削除
    print(f"   食材候補の合計（重複削除後）: {len(all_ingredient_descendants):,} クラス")
    print()

    # 料理と食材を分離
    print("📂 料理と食材を分離中...")
    dishes: List[Tuple[str, str, List[str]]] = []
    ingredients: List[Tuple[str, str, List[str]]] = []

    skipped_count = 0

    # 料理候補を処理
    for cls in multi_descendants:
        label = extract_label(cls)
        if not label or should_exclude(label):
            skipped_count += 1
            continue

        uri = str(cls.iri) if hasattr(cls, 'iri') else str(cls)
        synonyms = extract_synonyms(cls)
        dishes.append((uri, label, synonyms))

    # 食材候補を処理
    for cls in all_ingredient_descendants:
        label = extract_label(cls)
        if not label or should_exclude(label):
            skipped_count += 1
            continue

        uri = str(cls.iri) if hasattr(cls, 'iri') else str(cls)
        synonyms = extract_synonyms(cls)
        ingredients.append((uri, label, synonyms))

    print(f"  料理候補: {len(dishes):,} 項目")
    print(f"  食材候補: {len(ingredients):,} 項目")
    print(f"  スキップ: {skipped_count:,} 項目")
    print()

    # ソート
    dishes.sort(key=lambda x: x[1].lower())
    ingredients.sort(key=lambda x: x[1].lower())

    # 出力
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    output_dir.mkdir(exist_ok=True, parents=True)

    dishes_json = output_dir / "dishes_raw.json"
    ingredients_json = output_dir / "ingredients_raw.json"

    print(f"💾 結果を保存中...")

    # 料理を保存
    dishes_data = [
        {"uri": uri, "label": label, "synonyms": synonyms}
        for uri, label, synonyms in dishes
    ]
    with open(dishes_json, 'w', encoding='utf-8') as f:
        json.dump(dishes_data, f, indent=2, ensure_ascii=False)
    print(f"  料理候補: {dishes_json}")

    # 食材を保存
    ingredients_data = [
        {"uri": uri, "label": label, "synonyms": synonyms}
        for uri, label, synonyms in ingredients
    ]
    with open(ingredients_json, 'w', encoding='utf-8') as f:
        json.dump(ingredients_data, f, indent=2, ensure_ascii=False)
    print(f"  食材候補: {ingredients_json}")
    print()

    # サマリー
    print("="*80)
    print("抽出結果サマリー")
    print("="*80)
    print(f"料理候補（Base food）: {len(dishes):,} 項目")
    print(f"食材候補（Ingredient）: {len(ingredients):,} 項目")
    print(f"合計: {len(dishes) + len(ingredients):,} 項目")
    print()

    # サンプル
    print("料理候補サンプル（最初の15項目）:")
    print("-"*80)
    for i, (uri, label, synonyms) in enumerate(dishes[:15], 1):
        syn_text = f" (synonyms: {', '.join(synonyms[:2])})" if synonyms else ""
        print(f"{i:3d}. {label}{syn_text}")
    print("-"*80)
    print()

    print("食材候補サンプル（最初の15項目）:")
    print("-"*80)
    for i, (uri, label, synonyms) in enumerate(ingredients[:15], 1):
        syn_text = f" (synonyms: {', '.join(synonyms[:2])})" if synonyms else ""
        print(f"{i:3d}. {label}{syn_text}")
    print("-"*80)
    print()

    print("✅ 次のステップ:")
    print("  1. Open Food Facts APIから頻度データを取得")
    print("  2. スコアリング（0.5*log1p(OFF) + 0.4*log1p(Recipe1M) + 0.1*WWEIA）")
    print("  3. 上位選択（Base ~600、Ingredient ~1000）")
    print("  4. CORE食品リストの生成")
    print()


if __name__ == "__main__":
    main()
