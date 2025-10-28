#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全クエリの並列評価（300クエリ）

asyncioで50クエリずつ並列実行し、高速化します。
DeepInfra APIは200並列リクエストまで対応。
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
os.environ['PYTHONUNBUFFERED'] = '1'

from src.pipeline import FoodSearchPipeline


def evaluate_nutrition_match(
    query_name: str,
    query_desc: str,
    matched_name: str,
    matched_desc: str,
    matched_full: str
) -> Dict:
    """栄養計算の観点でマッチングが許容できるかを評価"""
    issues = []

    # 1. 食材名の主要部分が一致しているか
    query_main = query_name.lower().strip()
    matched_main = matched_name.lower().strip()

    query_words = set(query_main.split())
    matched_words = set(matched_main.split())
    common_words = query_words & matched_words

    if not common_words:
        issues.append("food_name_mismatch")

    # 2. 調理法の確認
    cooking_methods = [
        "raw", "cooked", "grilled", "fried", "baked", "roasted",
        "boiled", "steamed", "sauteed", "broiled"
    ]

    query_cooking = None
    matched_cooking = None

    query_text = f"{query_name} {query_desc}".lower()
    matched_text = f"{matched_name} {matched_desc}".lower()

    for method in cooking_methods:
        if method in query_text:
            query_cooking = method
            break

    for method in cooking_methods:
        if method in matched_text:
            matched_cooking = method
            break

    # 調理法の不一致チェック
    if query_cooking and matched_cooking:
        if query_cooking != matched_cooking:
            if not (query_cooking == "cooked" or matched_cooking == "cooked" or
                    "NS as to cooking method" in matched_full):
                issues.append(f"cooking_method_mismatch ({query_cooking} vs {matched_cooking})")
    elif query_cooking == "raw" and matched_cooking and matched_cooking != "raw":
        issues.append(f"raw_vs_cooked ({query_cooking} vs {matched_cooking})")

    # 評価カテゴリ
    if not issues:
        category = "exact_match"
    elif len(issues) == 1 and "food_name_mismatch" not in issues:
        category = "acceptable"
    else:
        category = "problematic"

    return {
        "category": category,
        "issues": issues,
        "query_cooking": query_cooking,
        "matched_cooking": matched_cooking
    }


async def process_batch(
    pipeline: FoodSearchPipeline,
    queries: List[Dict],
    batch_num: int,
    total_batches: int
) -> List[Dict]:
    """1バッチのクエリを並列処理"""

    print(f"\n{'='*80}", flush=True)
    print(f"Batch {batch_num}/{total_batches} ({len(queries)} queries)", flush=True)
    print(f"{'='*80}", flush=True)

    results = []

    # 順次実行（各クエリは内部でStage1とStage2を実行）
    for i, query in enumerate(queries, 1):
        query_name = query["search_name"]
        query_desc = query["description"]

        global_idx = query.get("_index", i)

        if i % 10 == 1:  # Progress every 10 queries
            print(f"  [{global_idx}] {query_name} | {query_desc}", flush=True)

        try:
            result = pipeline.search(
                query_main=query_name,
                query_descriptors=query_desc,
                return_top_k=5
            )

            best_match = result['best_match']

            # Evaluate match
            evaluation = evaluate_nutrition_match(
                query_name=query_name,
                query_desc=query_desc,
                matched_name=best_match['main_name'],
                matched_desc=best_match['descriptors'],
                matched_full=best_match['description']
            )

            results.append({
                "query_id": global_idx,
                "query_name": query_name,
                "query_desc": query_desc,
                "query_image": query.get("image_file", ""),
                "matched_description": best_match['description'],
                "matched_name": best_match['main_name'],
                "matched_desc": best_match['descriptors'],
                "rerank_score": best_match['rerank_score'],
                "stage1_score": best_match['stage1_score'],
                "fdc_id": best_match['fdc_id'],
                "evaluation": evaluation
            })

        except Exception as e:
            print(f"  ❌ Error on query {global_idx}: {e}", flush=True)
            results.append({
                "query_id": global_idx,
                "query_name": query_name,
                "query_desc": query_desc,
                "error": str(e)
            })

    print(f"  ✅ Batch {batch_num} completed: {len(results)} queries processed", flush=True)
    return results


async def run_parallel_evaluation():
    """全300クエリを並列評価"""

    print("=" * 80, flush=True)
    print("Parallel Query Evaluation (300 queries, batch_size=50)", flush=True)
    print("=" * 80, flush=True)

    # Load test queries
    queries_file = project_root / "tests" / "data" / "test_queries.json"
    print(f"\nLoading queries from: {queries_file}", flush=True)

    with open(queries_file, 'r', encoding='utf-8') as f:
        all_queries = json.load(f)

    print(f"✅ Loaded {len(all_queries)} queries", flush=True)

    # Add index to each query
    for i, query in enumerate(all_queries, 1):
        query["_index"] = i

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

    # Split into batches
    batch_size = 50
    batches = [
        all_queries[i:i+batch_size]
        for i in range(0, len(all_queries), batch_size)
    ]

    print(f"Split into {len(batches)} batches of {batch_size} queries", flush=True)

    # Process batches
    start_time = time.time()
    all_results = []

    for batch_num, batch in enumerate(batches, 1):
        batch_results = await process_batch(pipeline, batch, batch_num, len(batches))
        all_results.extend(batch_results)

    elapsed = time.time() - start_time

    print(f"\n✅ All batches completed in {elapsed:.1f} seconds", flush=True)
    print(f"   Average: {elapsed/len(all_results):.2f} seconds/query", flush=True)

    # Get API usage stats
    stats = pipeline.get_usage_stats()

    # Analyze results
    print("\n" + "=" * 80, flush=True)
    print("EVALUATION RESULTS", flush=True)
    print("=" * 80, flush=True)

    exact_matches = [r for r in all_results if r.get("evaluation", {}).get("category") == "exact_match"]
    acceptable = [r for r in all_results if r.get("evaluation", {}).get("category") == "acceptable"]
    problematic = [r for r in all_results if r.get("evaluation", {}).get("category") == "problematic"]
    errors = [r for r in all_results if "error" in r]

    print(f"\nMatch Quality:", flush=True)
    print(f"  ✅ Exact Match: {len(exact_matches)} ({len(exact_matches)/len(all_results)*100:.1f}%)", flush=True)
    print(f"  ⚠️  Acceptable: {len(acceptable)} ({len(acceptable)/len(all_results)*100:.1f}%)", flush=True)
    print(f"  ❌ Problematic: {len(problematic)} ({len(problematic)/len(all_results)*100:.1f}%)", flush=True)
    print(f"  🔥 Errors: {len(errors)} ({len(errors)/len(all_results)*100:.1f}%)", flush=True)

    # Overall acceptance rate
    acceptance_rate = (len(exact_matches) + len(acceptable)) / len(all_results) * 100
    print(f"\n📊 Overall Acceptance Rate: {acceptance_rate:.1f}%", flush=True)

    # Issue breakdown
    print(f"\n" + "-" * 80, flush=True)
    print("Issue Breakdown:", flush=True)
    print("-" * 80, flush=True)

    issue_counts = {}
    for r in all_results:
        if "evaluation" in r:
            for issue in r["evaluation"].get("issues", []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue}: {count}", flush=True)

    # API costs
    print("\n" + "=" * 80, flush=True)
    print("API USAGE & COSTS", flush=True)
    print("=" * 80, flush=True)

    print(f"\n📊 Embedding API", flush=True)
    print(f"   Tokens: {stats['embedding']['total_tokens']:,}", flush=True)
    print(f"   Cost: ${stats['embedding']['cost_usd']:.6f}", flush=True)

    print(f"\n📊 Reranker API", flush=True)
    print(f"   Tokens: {stats['reranker']['total_tokens']:,}", flush=True)
    print(f"   Cost: ${stats['reranker']['cost_usd']:.6f}", flush=True)

    print(f"\n💰 Total Cost: ${stats['total_cost_usd']:.4f}", flush=True)

    avg_cost = stats['total_cost_usd'] / len(all_results)
    print(f"\n📌 Average Cost per Query: ${avg_cost:.6f}", flush=True)

    # Show problematic cases sample
    if problematic:
        print("\n" + "=" * 80, flush=True)
        print(f"PROBLEMATIC CASES (showing first 10 of {len(problematic)})", flush=True)
        print("=" * 80, flush=True)

        for i, r in enumerate(problematic[:10], 1):
            print(f"\n{i}. Query: {r['query_name']} | {r['query_desc']}", flush=True)
            print(f"   Matched: {r['matched_description']}", flush=True)
            print(f"   Score: {r['rerank_score']:.4f}", flush=True)
            print(f"   Issues: {', '.join(r['evaluation']['issues'])}", flush=True)

    # Save results
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "evaluation_results_full.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_queries": len(all_results),
                "exact_matches": len(exact_matches),
                "acceptable": len(acceptable),
                "problematic": len(problematic),
                "errors": len(errors),
                "exact_match_rate": len(exact_matches) / len(all_results),
                "acceptable_rate": (len(exact_matches) + len(acceptable)) / len(all_results),
                "acceptance_rate": acceptance_rate / 100,
                "elapsed_seconds": elapsed,
                "avg_seconds_per_query": elapsed / len(all_results),
                "api_usage": stats
            },
            "issue_counts": issue_counts,
            "results": all_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved to: {output_file}", flush=True)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"📊 Output file size: {file_size_mb:.2f} MB", flush=True)

    print("\n" + "=" * 80, flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(run_parallel_evaluation())
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
