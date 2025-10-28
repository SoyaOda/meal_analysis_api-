#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
beef steak | grilledケースの詳細確認（stage1_top_k=100）
FDC ID: 746763 が何位に現れるか確認
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline

# Initialize pipeline with stage1_top_k=100
index_dir = project_root / "data"
pipeline = FoodSearchPipeline(
    index_dir=str(index_dir),
    device="cpu",
    stage1_top_k=100  # Increased from 40 to 100
)

print("=" * 80)
print("beef steak | grilled の詳細分析（stage1_top_k=100）")
print("=" * 80)

# Stage 1候補を全て取得（top_k=100）
result = pipeline.search(
    query_main="beef steak",
    query_descriptors="grilled, sliced",
    return_top_k=10,
    return_candidates=True
)

print(f"\n📋 Stage 1 Candidates: {len(result['stage1_candidates'])}件")
print("-" * 80)

# 目標のFDC ID: 746763を探す
target_fdc_id = 746763
target_description = "Beef, short loin, t-bone steak, bone-in, separable lean only, trimmed to 1/8\" fat, choice, cooked, grilled"

print(f"\n🎯 目標候補の確認:")
print(f"   FDC ID: {target_fdc_id}")
print(f"   Description: {target_description}")
print("-" * 80)

found = False
for i, cand in enumerate(result['stage1_candidates'], 1):
    if cand['fdc_id'] == target_fdc_id:
        print(f"\n   ✅ 見つかりました！")
        print(f"   📍 Rank: {i}/100")
        print(f"   📊 Stage1 Score: {cand['score']:.4f}")
        print(f"   📝 Description: {cand['description']}")
        print(f"   🏷️  Source: {cand['source']}")
        found = True
        break

if not found:
    print(f"\n   ❌ 見つかりませんでした（top-100の範囲外）")
    print(f"   → さらにstage1_top_kを増やす必要があります")

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

print(f"\n\n🔥 Grilled/Broiled候補: {len(grilled_candidates)}件")
print("-" * 80)

if len(grilled_candidates) > 0:
    print("\n✅ Stage 1でgrilled候補が取得されています！")
    for item in grilled_candidates[:5]:  # Show top 5
        print(f"\n   Rank: {item['rank']}/100")
        print(f"   Score: {item['score']:.4f}")
        print(f"   Description: {item['description']}")
        print(f"   Source: {item['source']}")
        print(f"   FDC ID: {item['fdc_id']}")
else:
    print("\n❌ Stage 1でgrilled候補が取得されていません")

print("\n\n🎯 Stage 2 Results (Reranked Top 10):")
print("-" * 80)
for i, item in enumerate(result['top_k'], 1):
    marker = "★" if i == 1 else " "
    is_grilled = 'grilled' in item['description'].lower() or 'broiled' in item['description'].lower()
    tag = " [GRILLED]" if is_grilled else ""
    is_target = item.get('fdc_id') == target_fdc_id
    target_tag = " [TARGET]" if is_target else ""
    print(f"{marker} {i:2d}. Rerank: {item['rerank_score']:.4f}, Stage1: {item['stage1_score']:.4f}{tag}{target_tag}")
    print(f"       {item['description']}")

print("\n" + "=" * 80)
