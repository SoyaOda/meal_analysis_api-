#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全クエリの検索精度評価

300個のVLMクエリで検索を実行し、マッチング結果を評価します。
栄養計算の観点で許容できるかを判断します。
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def evaluate_nutrition_match(
    query_name: str,
    query_desc: str,
    matched_name: str,
    matched_desc: str,
    matched_full: str
) -> Dict:
    """
    栄養計算の観点でマッチングが許容できるかを評価

    Args:
        query_name: クエリの食材名
        query_desc: クエリの説明
        matched_name: マッチした食材名
        matched_desc: マッチした説明
        matched_full: マッチした完全な説明

    Returns:
        評価結果の辞書
    """
    issues = []

    # 1. 食材名の主要部分が一致しているか
    query_main = query_name.lower().strip()
    matched_main = matched_name.lower().strip()

    # Simple word-level matching
    query_words = set(query_main.split())
    matched_words = set(matched_main.split())

    common_words = query_words & matched_words

    if not common_words:
        issues.append("food_name_mismatch")

    # 2. 調理法の確認（主要な調理法のみチェック）
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
            # "cooked" と具体的な調理法は許容
            if not (query_cooking == "cooked" or matched_cooking == "cooked" or
                    "NS as to cooking method" in matched_full):
                issues.append(f"cooking_method_mismatch ({query_cooking} vs {matched_cooking})")
    elif query_cooking == "raw" and matched_cooking and matched_cooking != "raw":
        issues.append(f"raw_vs_cooked ({query_cooking} vs {matched_cooking})")

    # 評価スコア
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


def run_full_evaluation():
    """全300クエリで評価を実行"""

    print("=" * 80)
    print("Full Query Evaluation (300 queries)")
    print("=" * 80)

    # Load test queries
    queries_file = project_root / "tests" / "data" / "test_queries.json"
    print(f"\nLoading queries from: {queries_file}")

    with open(queries_file, 'r', encoding='utf-8') as f:
        queries = json.load(f)

    print(f"✅ Loaded {len(queries)} queries")

    # Initialize pipeline
    index_dir = project_root / "data"
    print(f"\nInitializing pipeline...")

    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=40  # Cost-effective setting
    )

    print(f"✅ {pipeline}\n")

    # Reset stats
    pipeline.reset_usage_stats()

    # Evaluate each query
    results = []

    print("=" * 80)
    print("Running evaluation...")
    print("=" * 80)

    for i, query in enumerate(queries, 1):
        query_name = query["search_name"]
        query_desc = query["description"]

        # Progress indicator
        if i % 50 == 0 or i == 1:
            print(f"\n[{i}/{len(queries)}] Processing: {query_name} | {query_desc}")

        # Search
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
                "query_id": i,
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
            print(f"\n⚠️ Error on query {i}: {e}")
            results.append({
                "query_id": i,
                "query_name": query_name,
                "query_desc": query_desc,
                "error": str(e)
            })

    print(f"\n✅ Completed {len(results)} queries")

    # Get API usage stats
    stats = pipeline.get_usage_stats()

    # Analyze results
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)

    exact_matches = [r for r in results if r.get("evaluation", {}).get("category") == "exact_match"]
    acceptable = [r for r in results if r.get("evaluation", {}).get("category") == "acceptable"]
    problematic = [r for r in results if r.get("evaluation", {}).get("category") == "problematic"]
    errors = [r for r in results if "error" in r]

    print(f"\nMatch Quality:")
    print(f"  ✅ Exact Match: {len(exact_matches)} ({len(exact_matches)/len(results)*100:.1f}%)")
    print(f"  ⚠️  Acceptable: {len(acceptable)} ({len(acceptable)/len(results)*100:.1f}%)")
    print(f"  ❌ Problematic: {len(problematic)} ({len(problematic)/len(results)*100:.1f}%)")
    print(f"  🔥 Errors: {len(errors)} ({len(errors)/len(results)*100:.1f}%)")

    # Issue breakdown
    print(f"\n" + "-" * 80)
    print("Issue Breakdown:")
    print("-" * 80)

    issue_counts = {}
    for r in results:
        if "evaluation" in r:
            for issue in r["evaluation"].get("issues", []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue}: {count}")

    # API costs
    print("\n" + "=" * 80)
    print("API USAGE & COSTS")
    print("=" * 80)

    print(f"\n📊 Embedding API (Qwen3-Embedding-8B)")
    print(f"   Tokens: {stats['embedding']['total_tokens']:,}")
    print(f"   API Calls: {stats['embedding']['api_calls']}")
    print(f"   Cost: ${stats['embedding']['cost_usd']:.6f}")

    print(f"\n📊 Reranker API (Qwen3-Reranker-8B)")
    print(f"   Tokens: {stats['reranker']['total_tokens']:,}")
    print(f"   API Calls: {stats['reranker']['api_calls']}")
    print(f"   Cost: ${stats['reranker']['cost_usd']:.6f}")

    print(f"\n💰 Total Cost: ${stats['total_cost_usd']:.6f}")

    avg_cost = stats['total_cost_usd'] / len(queries)
    print(f"\n📌 Average Cost per Query: ${avg_cost:.6f}")
    print(f"   Estimated cost for 1,000 queries: ${avg_cost * 1000:.2f}")
    print(f"   Estimated cost for 10,000 queries: ${avg_cost * 10000:.2f}")

    # Show problematic cases
    if problematic:
        print("\n" + "=" * 80)
        print(f"PROBLEMATIC CASES (showing first 20 of {len(problematic)})")
        print("=" * 80)

        for i, r in enumerate(problematic[:20], 1):
            print(f"\n{i}. Query: {r['query_name']} | {r['query_desc']}")
            print(f"   Matched: {r['matched_description']}")
            print(f"   Score: {r['rerank_score']:.4f}")
            print(f"   Issues: {', '.join(r['evaluation']['issues'])}")

    # Save results
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "evaluation_results_full.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_queries": len(results),
                "exact_matches": len(exact_matches),
                "acceptable": len(acceptable),
                "problematic": len(problematic),
                "errors": len(errors),
                "exact_match_rate": len(exact_matches) / len(results),
                "acceptable_rate": (len(exact_matches) + len(acceptable)) / len(results),
                "api_usage": stats
            },
            "issue_counts": issue_counts,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved to: {output_file}")

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"📊 Output file size: {file_size_mb:.2f} MB")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        run_full_evaluation()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
