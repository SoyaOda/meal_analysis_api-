#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
失敗ケースの詳細分析：
1. データベースに正解があるか
2. Stage 1で正解候補が取得できているか
3. 栄養素的に許容できる代替案があるか
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline

# 失敗した6ケース
failure_cases = [
    {
        "id": 1,
        "query_main": "beef steak",
        "query_descriptors": "grilled, sliced",
        "expected": "Beef, steak, grilled",
        "matched": "Beef, steak, NFS",
        "issue": "Cooking method mismatch"
    },
    {
        "id": 2,
        "query_main": "macaroni and cheese",
        "query_descriptors": "cooked",
        "expected": "Macaroni or noodles with cheese, cooked",
        "matched": "Macaroni or noodles, creamed, with cheese",
        "issue": "Cooking method mismatch"
    },
    {
        "id": 3,
        "query_main": "chicken breast",
        "query_descriptors": "cooked, boneless, skinless",
        "expected": "Chicken breast, cooked",
        "matched": "Chicken breast, NS as to cooking method, skin not eaten",
        "issue": "Cooking method mismatch (but nutritionally acceptable?)"
    },
    {
        "id": 4,
        "query_main": "beef sirloin",
        "query_descriptors": "cooked, roasted",
        "expected": "Beef, sirloin, roasted",
        "matched": "Beef, roast",
        "issue": "Cooking method mismatch"
    },
    {
        "id": 5,
        "query_main": "potatoes",
        "query_descriptors": "roasted",
        "expected": "Potatoes, roasted",
        "matched": "Potato, roasted, NFS",
        "issue": "Singular/plural mismatch (but nutritionally acceptable?)"
    },
    {
        "id": 6,
        "query_main": "asparagus",
        "query_descriptors": "roasted",
        "expected": "Asparagus, roasted",
        "matched": "Asparagus, NS as to form, cooked",
        "issue": "Cooking method mismatch"
    }
]

# Initialize pipeline
index_dir = project_root / "data"
pipeline = FoodSearchPipeline(
    index_dir=str(index_dir),
    device="cpu"
)

print("=" * 80)
print("失敗ケースの詳細分析")
print("=" * 80)

for case in failure_cases:
    print(f"\n\n{'=' * 80}")
    print(f"[Case {case['id']}] {case['query_main']} | {case['query_descriptors']}")
    print(f"期待: {case['expected']}")
    print(f"実際: {case['matched']}")
    print(f"問題: {case['issue']}")
    print("=" * 80)

    # Stage 1候補を含む詳細結果を取得
    result = pipeline.search(
        query_main=case['query_main'],
        query_descriptors=case['query_descriptors'],
        return_top_k=10,
        return_candidates=True
    )

    print(f"\n📋 Stage 1 Candidates (Top 40):")
    print("-" * 80)

    # 期待する文字列のキーワードを含む候補を探す
    keywords = case['expected'].lower().split()

    found_expected = False
    grilled_items = []
    roasted_items = []
    cooked_items = []

    for i, cand in enumerate(result['stage1_candidates'], 1):
        desc = cand['description'].lower()

        # 期待する候補かチェック
        is_expected = all(kw in desc for kw in ['beef', 'steak']) if 'beef steak' in case['query_main'].lower() else False

        # 調理法をチェック
        has_grilled = 'grilled' in desc or 'broiled' in desc
        has_roasted = 'roasted' in desc or 'roasted' in desc
        has_cooked = 'cooked' in desc

        if has_grilled:
            grilled_items.append((i, cand['description'], cand['score']))
        if has_roasted:
            roasted_items.append((i, cand['description'], cand['score']))
        if has_cooked and not has_grilled and not has_roasted:
            cooked_items.append((i, cand['description'], cand['score']))

        # 上位10件のみ表示
        if i <= 10:
            marker = "✓" if is_expected else " "
            print(f"{marker} {i:2d}. {cand['score']:.4f} - {cand['description']}")

    # 調理法別の候補を表示
    print(f"\n🔥 Grilled/Broiled候補: {len(grilled_items)}件")
    for idx, desc, score in grilled_items[:3]:
        print(f"   {idx:2d}. {score:.4f} - {desc}")

    print(f"\n🔥 Roasted候補: {len(roasted_items)}件")
    for idx, desc, score in roasted_items[:3]:
        print(f"   {idx:2d}. {score:.4f} - {desc}")

    print(f"\n🍳 Cooked（一般）候補: {len(cooked_items)}件")
    for idx, desc, score in cooked_items[:3]:
        print(f"   {idx:2d}. {score:.4f} - {desc}")

    print(f"\n\n🎯 Stage 2 Results (Reranked Top 10):")
    print("-" * 80)
    for i, item in enumerate(result['top_k'], 1):
        marker = "★" if i == 1 else " "
        print(f"{marker} {i:2d}. Rerank: {item['rerank_score']:.4f}, Stage1: {item['stage1_score']:.4f}")
        print(f"       {item['description']}")

    # 栄養素的許容性の評価
    print(f"\n\n💡 栄養素的許容性の評価:")
    print("-" * 80)

    best_match = result['best_match']['description'].lower()

    if case['id'] == 3:  # chicken breast, cooked
        if 'ns as to cooking method' in best_match:
            print("✅ 栄養的に許容可能:")
            print("   'NS as to cooking method'は調理法が不明な場合の標準値")
            print("   'cooked'のみ指定の場合、これが最適な選択肢である可能性が高い")

    elif case['id'] == 5:  # potatoes vs potato
        if 'potato' in best_match and 'roasted' in best_match:
            print("✅ 栄養的に許容可能:")
            print("   単複形の違いのみで、栄養素は同じ")
            print("   'Potato, roasted, NFS'は正解と言える")

print("\n\n" + "=" * 80)
print("分析完了")
print("=" * 80)
