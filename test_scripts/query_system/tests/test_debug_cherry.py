# -*- coding: utf-8 -*-
"""
Debug: cherry tomatoes case
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

# Search for cherry tomatoes
result = pipeline.search(
    query_main="cherry tomatoes",
    query_descriptors="raw",
    return_top_k=10,
    return_candidates=True
)

print("\n" + "=" * 80)
print("DEBUG: cherry tomatoes | raw")
print("=" * 80)

print(f"\nStage 1 Candidates (Top 10 of {len(result['stage1_candidates'])}):")
for i, cand in enumerate(result['stage1_candidates'][:10], 1):
    print(f"{i}. Score: {cand['score']:.4f} - {cand['description']}")

print(f"\n\nStage 2 Results (After Reranking):")
for i, item in enumerate(result['top_k'], 1):
    print(f"{i}. Rerank: {item['rerank_score']:.4f}, Stage1: {item['stage1_score']:.4f}")
    print(f"   {item['description']}")
