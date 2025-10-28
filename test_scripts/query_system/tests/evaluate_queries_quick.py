#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
クイック評価テスト（最初の10クエリのみ）

動作確認用に少数のクエリで評価を実行します。
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Disable buffering
import os
os.environ['PYTHONUNBUFFERED'] = '1'

from src.pipeline import FoodSearchPipeline

print("=" * 80, flush=True)
print("Quick Evaluation Test (10 queries)", flush=True)
print("=" * 80, flush=True)

# Load test queries
queries_file = project_root / "tests" / "data" / "test_queries.json"
print(f"\nLoading queries from: {queries_file}", flush=True)

with open(queries_file, 'r', encoding='utf-8') as f:
    all_queries = json.load(f)

# Take first 10
queries = all_queries[:10]
print(f"✅ Testing with {len(queries)} queries (out of {len(all_queries)} total)", flush=True)

# Initialize pipeline
index_dir = project_root / "data"
print(f"\nInitializing pipeline...", flush=True)

pipeline = FoodSearchPipeline(
    index_dir=str(index_dir),
    device="cpu",
    stage1_top_k=40
)

print(f"✅ {pipeline}\n", flush=True)

# Reset stats
pipeline.reset_usage_stats()

# Evaluate each query
results = []

print("=" * 80, flush=True)
print("Running evaluation...", flush=True)
print("=" * 80, flush=True)

for i, query in enumerate(queries, 1):
    query_name = query["search_name"]
    query_desc = query["description"]

    print(f"\n[{i}/{len(queries)}] {query_name} | {query_desc}", flush=True)

    # Search
    try:
        result = pipeline.search(
            query_main=query_name,
            query_descriptors=query_desc,
            return_top_k=5
        )

        best_match = result['best_match']

        print(f"  → Matched: {best_match['description']}", flush=True)
        print(f"  → Score: {best_match['rerank_score']:.4f}", flush=True)

        results.append({
            "query_id": i,
            "query_name": query_name,
            "query_desc": query_desc,
            "matched_description": best_match['description'],
            "rerank_score": best_match['rerank_score'],
            "fdc_id": best_match['fdc_id']
        })

    except Exception as e:
        print(f"  ❌ Error: {e}", flush=True)
        results.append({
            "query_id": i,
            "query_name": query_name,
            "query_desc": query_desc,
            "error": str(e)
        })

print(f"\n✅ Completed {len(results)} queries", flush=True)

# Get API usage stats
stats = pipeline.get_usage_stats()

print("\n" + "=" * 80, flush=True)
print("API USAGE & COSTS", flush=True)
print("=" * 80, flush=True)

print(f"\n📊 Reranker API", flush=True)
print(f"   Tokens: {stats['reranker']['total_tokens']:,}", flush=True)
print(f"   Cost: ${stats['reranker']['cost_usd']:.6f}", flush=True)

print(f"\n💰 Total Cost: ${stats['total_cost_usd']:.6f}", flush=True)

avg_cost = stats['total_cost_usd'] / len(queries)
print(f"\n📌 Average Cost per Query: ${avg_cost:.6f}", flush=True)
print(f"   Extrapolated to 300 queries: ${avg_cost * 300:.4f}", flush=True)

print("\n" + "=" * 80, flush=True)
print("✅ Quick test completed successfully!", flush=True)
print("=" * 80, flush=True)
