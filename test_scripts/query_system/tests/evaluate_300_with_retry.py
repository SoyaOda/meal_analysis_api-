#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全300クエリの評価（リトライ機能付き、50並列）

リトライ機能を使用して、タイムアウトを最小限に抑えます。
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
            "top_k_results": result['top_k'],  # Top 5のReranker結果も保存
            "stage1_candidates": stage1_candidates,  # Stage 1の全候補を保存
            "error": None
        }

    except Exception as e:
        return {
            "query_id": query_idx,
            "query_name": query_name,
            "query_desc": query_desc,
            "error": str(e)
        }


def run_evaluation_with_retry():
    """全300クエリを50並列で評価（リトライ機能付き）"""

    print("=" * 80, flush=True)
    print("Full Evaluation with Retry (300 queries, 50 parallel workers)", flush=True)
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

    # Initialize pipeline with retry enabled
    index_dir = project_root / "data"
    print(f"\nInitializing pipeline with retry support...", flush=True)

    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=40
    )

    print(f"✅ {pipeline}", flush=True)
    print(f"📝 Retry configuration: max_retries=10, retry_delay=1.0s\n", flush=True)

    # Reset stats
    pipeline.reset_usage_stats()

    # Prepare arguments for parallel execution
    args_list = [(pipeline, query, len(all_queries)) for query in all_queries]

    # Process with ThreadPoolExecutor (50 workers to reduce timeout)
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
    print("EVALUATION RESULTS", flush=True)
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

        retry_history = stats['reranker'].get('retry_history', [])
        if retry_history:
            successful_retries = [h for h in retry_history if h['success']]
            failed_retries = [h for h in retry_history if not h['success']]
            print(f"   Successful after retry: {len(successful_retries)}", flush=True)
            print(f"   Failed after all retries: {len(failed_retries)}", flush=True)

    print(f"\n💰 Total Cost: ${stats['total_cost_usd']:.4f}", flush=True)

    avg_cost = stats['total_cost_usd'] / len(all_results)
    print(f"\n📌 Average Cost per Query: ${avg_cost:.6f}", flush=True)

    # Problematic cases analysis
    if problematic:
        print("\n" + "=" * 80, flush=True)
        print(f"PROBLEMATIC CASES ANALYSIS", flush=True)
        print("=" * 80, flush=True)

        # Categorize by score
        timeout_like = [r for r in problematic if r.get('rerank_score', 1.0) < 0.03]
        high_score = [r for r in problematic if r.get('rerank_score', 0.0) > 0.9]
        medium_score = [r for r in problematic if 0.03 <= r.get('rerank_score', 0.0) <= 0.9]

        print(f"\n1. Timeout-like (score < 0.03): {len(timeout_like)}", flush=True)
        print(f"2. High score (> 0.9, likely singular/plural): {len(high_score)}", flush=True)
        print(f"3. Medium score (real mismatches): {len(medium_score)}", flush=True)

        print(f"\n✅ Effective Success Rate (excluding timeout-like): {(len(exact_matches) + len(acceptable) + len(high_score))/(len(all_results) - len(timeout_like))*100:.1f}%", flush=True)

        # Show first 10 problematic cases
        print("\n" + "=" * 80, flush=True)
        print(f"First 10 Problematic Cases:", flush=True)
        print("=" * 80, flush=True)
        for i, r in enumerate(problematic[:10], 1):
            score = r.get('rerank_score', 0.0)
            print(f"\n{i}. {r['query_name']} | {r['query_desc']}", flush=True)
            print(f"   → {r.get('matched_description', 'N/A')}", flush=True)
            print(f"   Score: {score:.4f}, Issues: {', '.join(r.get('evaluation', {}).get('issues', []))}", flush=True)

    # Show errors if any
    if errors:
        print("\n" + "=" * 80, flush=True)
        print(f"ERRORS ({len(errors)} total)", flush=True)
        print("=" * 80, flush=True)
        for i, r in enumerate(errors[:5], 1):
            print(f"{i}. Query {r['query_id']}: {r['query_name']} | {r['query_desc']}", flush=True)
            print(f"   Error: {r['error']}", flush=True)

    # Save results
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    # フル版（Stage 1候補含む）を保存
    output_file_full = output_dir / "evaluation_results_300_with_retry_full.json"

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
                "api_usage": stats
            },
            "issue_counts": issue_counts,
            "results": all_results  # Stage 1候補含む
        }, f, indent=2, ensure_ascii=False)

    file_size_full_mb = output_file_full.stat().st_size / (1024 * 1024)
    print(f"✅ Full results saved to: {output_file_full}", flush=True)
    print(f"   File size: {file_size_full_mb:.2f} MB", flush=True)

    # サマリー版（Stage 1候補なし）も保存
    output_file_summary = output_dir / "evaluation_results_300_with_retry.json"

    print(f"\n💾 Saving summary results (without Stage 1 candidates)...", flush=True)

    # Stage 1候補を除外したコピーを作成
    results_summary = []
    for r in all_results:
        r_copy = r.copy()
        r_copy.pop('stage1_candidates', None)  # Stage 1候補を削除
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
        run_evaluation_with_retry()
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
