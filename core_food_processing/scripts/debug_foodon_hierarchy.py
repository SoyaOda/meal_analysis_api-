#!/usr/bin/env python3
"""
debug_foodon_hierarchy.py

FoodOnの階層構造をデバッグするスクリプト
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

from owlready2 import get_ontology

# FoodOnの主要なクラスID
MULTI_COMPONENT_FOOD = "FOODON_00002501"
FOOD_BY_ORGANISM = "FOODON_00002381"


def main():
    print("="*80)
    print("FoodOn 階層構造デバッグ")
    print("="*80)
    print()

    foodon_path = PROJECT_ROOT / "core_food_processing" / "data" / "foodon.owl"

    print("⏳ オントロジーをロード中...")
    onto = get_ontology(str(foodon_path)).load()
    print("✅ ロード完了")
    print()

    # クラスIDでクラスを検索
    print(f"🔍 {MULTI_COMPONENT_FOOD} を検索中...")
    multi_comp_class = None
    for cls in onto.classes():
        if hasattr(cls, 'name') and cls.name == MULTI_COMPONENT_FOOD:
            multi_comp_class = cls
            break

    if multi_comp_class:
        print(f"✅ 見つかりました: {multi_comp_class}")
        print(f"   Label: {multi_comp_class.label if hasattr(multi_comp_class, 'label') else 'N/A'}")
        print(f"   Parents: {[p.name if hasattr(p, 'name') else str(p) for p in multi_comp_class.is_a]}")

        # 子クラスを数える
        children = list(multi_comp_class.subclasses())
        print(f"   直接の子クラス数: {len(children)}")
        if children:
            print(f"   最初の5つの子クラス:")
            for i, child in enumerate(children[:5], 1):
                child_label = child.label[0] if hasattr(child, 'label') and child.label else child.name
                print(f"     {i}. {child_label}")
    else:
        print(f"❌ {MULTI_COMPONENT_FOOD} が見つかりません")

    print()

    print(f"🔍 {FOOD_BY_ORGANISM} を検索中...")
    by_organism_class = None
    for cls in onto.classes():
        if hasattr(cls, 'name') and cls.name == FOOD_BY_ORGANISM:
            by_organism_class = cls
            break

    if by_organism_class:
        print(f"✅ 見つかりました: {by_organism_class}")
        print(f"   Label: {by_organism_class.label if hasattr(by_organism_class, 'label') else 'N/A'}")
        print(f"   Parents: {[p.name if hasattr(p, 'name') else str(p) for p in by_organism_class.is_a]}")

        # 子クラスを数える
        children = list(by_organism_class.subclasses())
        print(f"   直接の子クラス数: {len(children)}")
        if children:
            print(f"   最初の10つの子クラス:")
            for i, child in enumerate(children[:10], 1):
                child_label = child.label[0] if hasattr(child, 'label') and child.label else child.name
                print(f"     {i}. {child_label}")
    else:
        print(f"❌ {FOOD_BY_ORGANISM} が見つかりません")

    print()

    # その他の有用なクラスを探す
    print("🔍 その他の主要クラスを検索中...")
    food_related = []
    for cls in onto.classes():
        if hasattr(cls, 'name'):
            name = cls.name
            if name.startswith('FOODON_') and hasattr(cls, 'label') and cls.label:
                label = cls.label[0] if isinstance(cls.label, list) else cls.label
                if isinstance(label, str) and ('food' in label.lower() or 'ingredient' in label.lower()):
                    children_count = len(list(cls.subclasses()))
                    if children_count > 10:  # 子クラスが多いもののみ
                        food_related.append((name, label, children_count))

    food_related.sort(key=lambda x: x[2], reverse=True)

    print(f"   子クラスが多い主要クラス（トップ10）:")
    for i, (name, label, count) in enumerate(food_related[:10], 1):
        print(f"     {i}. {name}: {label} ({count} 子クラス)")

    print()


if __name__ == "__main__":
    main()
