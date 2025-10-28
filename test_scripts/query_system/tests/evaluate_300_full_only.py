#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全300クエリの評価（Full検索のみ、weight_full=1.0）

Main検索を使わず、Full検索のみで評価し、結果が改善されるか確認
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def process_single_query(args):
    """単一クエリを処理（スレッドセーフ）"""
    pipeline, query, total = args

    query_idx = query["_index"]
    query_name = query["search_name"]
    query_desc = query["description"]

    try:
        result = pipeline.search(
            query_main=query_name,
            query_descriptors=query_desc,
            return_top_k=5,
            return_candidates=True  # Stage 1候補も保存
        )

        best_match = result['best_match']
        stage1_candidates = result.get('stage1_candidates', [])

        # Evaluate match
        evaluation = evaluate_nutrition_match(
            query_name=query_name,
            query_desc=query_desc,
            matched_name=best_match['main_name'],
            matched_desc=best_match['descriptors'],
            matched_full=best_match['description']
        )

        return {
            "query_id": query_idx,
            "query_name": query_name,
            "query_desc": query_desc,
            "query_image": query.get("image_file", ""),
            "matched_description": best_match['description'],
            "matched_name": best_match['main_name'],
            "matched_desc": best_match['descriptors'],
            "rerank_score": best_match['rerank_score'],
            "stage1_score": best_match['stage1_score'],
            "fdc_id": best_match['fdc_id'],
            "evaluation": evaluation,
            "top_k_results": result['top_k'],
            "stage1_candidates": stage1_candidates,
            "error": None
        }

    except Exception as e:
        return {
            "query_id": query_idx,
            "query_name": query_name,
            "query_desc": query_desc,
            "error": str(e)
        }


def run_evaluation_full_only():
    """全300クエリを50並列で評価（Full検索のみ、weight_full=1.0）"""

    print("=" * 80, flush=True)
    print("Full Evaluation with Full-Search-Only (300 queries, 50 parallel workers)", flush=True)
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

    # Initialize pipeline with Full-only weights
    index_dir = project_root / "data"
    print(f"\nInitializing pipeline with Full-search-only...", flush=True)

    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        weight_main=0.0,  # Main検索を使わない
        weight_full=1.0,  # Full検索のみ
        stage1_top_k=40
    )

    print(f"✅ {pipeline}", flush=True)
    print(f"⚙️  Weights: main=0.0, full=1.0 (Full-search-only)", flush=True)
    print(f"📝 Retry configuration: max_retries=10, retry_delay=1.0s\n", flush=True)

    # Reset stats
    pipeline.reset_usage_stats()

    # Prepare arguments for parallel execution
    args_list = [(pipeline, query, len(all_queries)) for query in all_queries]

    # Process with ThreadPoolExecutor (50 workers)
    print(f"Starting parallel execution with 50 workers...", flush=True)
    print("=" * 80, flush=True)

    start_time = time.time()
    all_results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=50) as executor:
        # Submit all tasks
        future_to_query = {
            executor.submit(process_single_query, args): args[1]["_index"]
            for args in args_list
        }

        # Process completed tasks
        for future in as_completed(future_to_query):
            query_idx = future_to_query[future]
            try:
                result = future.result()
                all_results.append(result)
                completed += 1

                # Progress update every 30 queries
                if completed % 30 == 0 or completed == len(all_queries):
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(all_queries) - completed) / rate if rate > 0 else 0
                    print(f"Progress: {completed}/{len(all_queries)} ({completed/len(all_queries)*100:.1f}%) - {rate:.1f} q/s - ETA: {eta:.0f}s", flush=True)

            except Exception as e:
                print(f"❌ Unexpected error processing query {query_idx}: {e}", flush=True)
                completed += 1

    elapsed = time.time() - start_time

    print(f"\n✅ All queries completed in {elapsed:.1f} seconds", flush=True)
    print(f"   Average: {elapsed/len(all_results):.2f} seconds/query", flush=True)
    print(f"   Throughput: {len(all_results)/elapsed:.2f} queries/second", flush=True)

    # Sort results by query_id
    all_results.sort(key=lambda x: x["query_id"])

    # Get API usage stats
    stats = pipeline.get_usage_stats()

    # Analyze results
    print("\n" + "=" * 80, flush=True)
    print("EVALUATION RESULTS (Full-Search-Only)", flush=True)
    print("=" * 80, flush=True)

    exact_matches = [r for r in all_results if r.get("evaluation", {}).get("category") == "exact_match"]
    acceptable = [r for r in all_results if r.get("evaluation", {}).get("category") == "acceptable"]
    problematic = [r for r in all_results if r.get("evaluation", {}).get("category") == "problematic"]
    errors = [r for r in all_results if r.get("error") is not None]

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
        if "evaluation" in r and r["evaluation"]:
            for issue in r["evaluation"].get("issues", []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue}: {count}", flush=True)

    # API costs and retry info
    print("\n" + "=" * 80, flush=True)
    print("API USAGE & COSTS", flush=True)
    print("=" * 80, flush=True)

    print(f"\n📊 Embedding API", flush=True)
    print(f"   Tokens: {stats['embedding']['total_tokens']:,}", flush=True)
    print(f"   Cost: ${stats['embedding']['cost_usd']:.6f}", flush=True)

    print(f"\n📊 Reranker API", flush=True)
    print(f"   Tokens: {stats['reranker']['total_tokens']:,}", flush=True)
    print(f"   API Calls: {stats['reranker']['api_calls']}", flush=True)
    print(f"   Cost: ${stats['reranker']['cost_usd']:.4f}", flush=True)

    # Retry information
    if stats['reranker'].get('total_retries', 0) > 0 or stats['reranker'].get('failed_requests', 0) > 0:
        print(f"\n🔄 Retry Information:", flush=True)
        print(f"   Total Retries: {stats['reranker'].get('total_retries', 0)}", flush=True)
        print(f"   Failed Requests: {stats['reranker'].get('failed_requests', 0)}", flush=True)

    print(f"\n💰 Total Cost: ${stats['total_cost_usd']:.4f}", flush=True)

    avg_cost = stats['total_cost_usd'] / len(all_results)
    print(f"\n📌 Average Cost per Query: ${avg_cost:.6f}", flush=True)

    # Check prosciutto case
    print("\n" + "=" * 80, flush=True)
    print("PROSCIUTTO ケースの確認", flush=True)
    print("=" * 80, flush=True)

    prosciutto_cases = [r for r in all_results if 'prosciutto' in r['query_name'].lower() and 'pizza' not in r['query_name'].lower()]

    for case in prosciutto_cases:
        print(f"\nQuery {case['query_id']}: {case['query_name']} | {case['query_desc']}")
        print(f"  Matched: {case['matched_description']}")
        print(f"  FDC ID: {case['fdc_id']}")
        print(f"  Rerank Score: {case['rerank_score']:.4f}")
        print(f"  Stage1 Score: {case['stage1_score']:.4f}")

        # Check if Ham, prosciutto in Stage 1
        candidates = case.get('stage1_candidates', [])
        correct_fdc = 2705879
        found = any(c['fdc_id'] == correct_fdc for c in candidates)

        if found:
            rank = next(i+1 for i, c in enumerate(candidates) if c['fdc_id'] == correct_fdc)
            score = next(c['score'] for c in candidates if c['fdc_id'] == correct_fdc)
            print(f"  ✅ Stage 1で「Ham, prosciutto」が{rank}位 (score: {score:.6f})")
        else:
            print(f"  ❌ Stage 1で「Ham, prosciutto」が40位圏外")

    # Save results
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    # フル版
    output_file_full = output_dir / "evaluation_results_300_full_only_full.json"

    print(f"\n💾 Saving full results (with Stage 1 candidates)...", flush=True)

    with open(output_file_full, 'w', encoding='utf-8') as f:
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
                "throughput_queries_per_sec": len(all_results) / elapsed,
                "parallel_workers": 50,
                "weight_main": 0.0,
                "weight_full": 1.0,
                "api_usage": stats
            },
            "issue_counts": issue_counts,
            "results": all_results
        }, f, indent=2, ensure_ascii=False)

    file_size_full_mb = output_file_full.stat().st_size / (1024 * 1024)
    print(f"✅ Full results saved to: {output_file_full}", flush=True)
    print(f"   File size: {file_size_full_mb:.2f} MB", flush=True)

    # サマリー版
    output_file_summary = output_dir / "evaluation_results_300_full_only.json"

    print(f"\n💾 Saving summary results (without Stage 1 candidates)...", flush=True)

    results_summary = []
    for r in all_results:
        r_copy = r.copy()
        r_copy.pop('stage1_candidates', None)
        results_summary.append(r_copy)

    with open(output_file_summary, 'w', encoding='utf-8') as f:
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
                "throughput_queries_per_sec": len(all_results) / elapsed,
                "parallel_workers": 50,
                "weight_main": 0.0,
                "weight_full": 1.0,
                "api_usage": stats
            },
            "issue_counts": issue_counts,
            "results": results_summary
        }, f, indent=2, ensure_ascii=False)

    file_size_summary_mb = output_file_summary.stat().st_size / (1024 * 1024)
    print(f"✅ Summary results saved to: {output_file_summary}", flush=True)
    print(f"   File size: {file_size_summary_mb:.2f} MB", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("✅ Evaluation completed successfully!", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    try:
        run_evaluation_full_only()
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
