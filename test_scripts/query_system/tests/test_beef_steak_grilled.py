#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
beef steak | grilledケースの詳細確認
データベースに存在する"grilled"候補がStage 1で取得されているか
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline

# Initialize pipeline
index_dir = project_root / "data"
pipeline = FoodSearchPipeline(
    index_dir=str(index_dir),
    device="cpu"
)

print("=" * 80)
print("beef steak | grilled の詳細分析")
print("=" * 80)

# Stage 1候補を全て取得（top_k=100で十分カバー）
result = pipeline.search(
    query_main="beef steak",
    query_descriptors="grilled, sliced",
    return_top_k=10,
    return_candidates=True
)

print(f"\n📋 Stage 1 Candidates: {len(result['stage1_candidates'])}件")
print("-" * 80)

# grilled候補を探す
grilled_candidates = []
for i, cand in enumerate(result['stage1_candidates'], 1):
    desc = cand['description'].lower()
    if 'grilled' in desc or 'broiled' in desc:
        grilled_candidates.append({
            'rank': i,
            'score': cand['score'],
            'description': cand['description'],
            'source': cand['source'],
            'fdc_id': cand['fdc_id']
        })

print(f"\n🔥 Grilled/Broiled候補: {len(grilled_candidates)}件")
print("-" * 80)

if len(grilled_candidates) > 0:
    print("\n✅ Stage 1でgrilled候補が取得されています！")
    for item in grilled_candidates:
        print(f"\n   Rank: {item['rank']}")
        print(f"   Score: {item['score']:.4f}")
        print(f"   Description: {item['description']}")
        print(f"   Source: {item['source']}")
        print(f"   FDC ID: {item['fdc_id']}")
else:
    print("\n❌ Stage 1でgrilled候補が取得されていません")
    print("   → Retrieverの問題")

# 目標のgrilled候補を確認
target = "Beef, short loin, t-bone steak, bone-in, separable lean only, trimmed to 1/8\" fat, choice, cooked, grilled"
print(f"\n\n🎯 目標候補の確認:")
print(f"   {target}")

found = False
for i, cand in enumerate(result['stage1_candidates'], 1):
    if target.lower() in cand['description'].lower() or cand['fdc_id'] == 746763:
        print(f"\n   ✅ 見つかりました！")
        print(f"   Rank: {i}")
        print(f"   Score: {cand['score']:.4f}")
        found = True
        break

if not found:
    print(f"\n   ❌ 見つかりませんでした（Stage 1の範囲外）")

print("\n\n🎯 Stage 2 Results (Reranked Top 10):")
print("-" * 80)
for i, item in enumerate(result['top_k'], 1):
    marker = "★" if i == 1 else " "
    is_grilled = 'grilled' in item['description'].lower() or 'broiled' in item['description'].lower()
    tag = " [GRILLED]" if is_grilled else ""
    print(f"{marker} {i:2d}. Rerank: {item['rerank_score']:.4f}, Stage1: {item['stage1_score']:.4f}{tag}")
    print(f"       {item['description']}")

print("\n" + "=" * 80)
