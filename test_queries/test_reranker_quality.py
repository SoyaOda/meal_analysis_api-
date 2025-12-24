#!/usr/bin/env python3
"""
Reranker品質テストスクリプト
Usage:
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py

    # Quick test (8 queries)
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py --quick

    # Specific category
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py --category similar_vegetables
"""
import asyncio
import json
import sys
import time
import argparse
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.freeform_usda_meal_analysis_api.services.hybrid_search import HybridSearchEngine
from apps.freeform_usda_meal_analysis_api.services.usda_search import SimplifiedUSDASearcher
from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
from apps.freeform_usda_meal_analysis_api.config.settings import get_settings


def load_test_queries(category: str = None, quick: bool = False) -> list:
    """テストクエリをロード"""
    queries_file = Path(__file__).parent / "challenging_food_queries.json"
    with open(queries_file, "r") as f:
        data = json.load(f)

    if quick:
        return [{"query": q, "difficulty": "quick"} for q in data["quick_test_set"]["queries"]]

    if category:
        if category in data["categories"]:
            return data["categories"][category]["queries"]
        else:
            print(f"Available categories: {list(data['categories'].keys())}")
            sys.exit(1)

    # All queries
    all_queries = []
    for cat_name, cat_data in data["categories"].items():
        for q in cat_data["queries"]:
            q["category"] = cat_name
            all_queries.append(q)
    return all_queries


async def test_query(searcher, hybrid_engine, embedding_service, reranker_service,
                     query: str, topk: int, reranker_model: str) -> dict:
    """単一クエリをテスト"""
    embeddings = await embedding_service.generate_embeddings([query])
    candidates = hybrid_engine.get_hybrid_candidates_sync(
        query=query,
        query_embedding=embeddings[0],
        faiss_index=searcher.index_full,
        items=searcher.items,
        stage1_top_k=topk,
    )

    documents = [c["description"] for c in candidates]
    start_time = time.time()
    best_idx, scores = await reranker_service.rerank(
        query=query,
        documents=documents,
        model=reranker_model,
    )
    reranker_time = time.time() - start_time

    # Top 3 results
    scored = [(scores[i], candidates[i]["description"]) for i in range(len(candidates))]
    scored.sort(key=lambda x: x[0], reverse=True)

    return {
        "query": query,
        "top3": scored[:3],
        "reranker_time": reranker_time,
    }


def check_result(result: dict, query_spec: dict) -> tuple:
    """結果をチェックして合否判定"""
    top_match = result["top3"][0][1].lower()

    issues = []

    # should_not_match チェック
    if "should_not_match" in query_spec:
        for bad_term in query_spec["should_not_match"]:
            if bad_term.lower() in top_match:
                issues.append(f"Contains '{bad_term}' (should not)")

    # expected_match_contains チェック
    if "expected_match_contains" in query_spec:
        expected = query_spec["expected_match_contains"].lower()
        if expected not in top_match:
            # alternative_matches チェック
            if "alternative_matches" in query_spec:
                found_alt = False
                for alt in query_spec["alternative_matches"]:
                    if alt.lower() in top_match:
                        found_alt = True
                        break
                if not found_alt:
                    issues.append(f"Missing '{expected}' or alternatives")
            else:
                issues.append(f"Missing '{expected}'")

    # must_contain チェック
    if "must_contain" in query_spec:
        for term in query_spec["must_contain"]:
            if term.lower() not in top_match:
                issues.append(f"Missing required '{term}'")

    passed = len(issues) == 0
    return passed, issues


async def main():
    parser = argparse.ArgumentParser(description="Reranker Quality Test")
    parser.add_argument("--quick", action="store_true", help="Quick test with 8 queries")
    parser.add_argument("--category", type=str, help="Test specific category")
    parser.add_argument("--topk", type=int, default=50, help="Stage1 TopK (default: 50)")
    parser.add_argument("--model", type=str, default="Qwen/Qwen3-Reranker-4B",
                        choices=["Qwen/Qwen3-Reranker-0.6B", "Qwen/Qwen3-Reranker-4B", "Qwen/Qwen3-Reranker-8B"],
                        help="Reranker model")
    args = parser.parse_args()

    # Load queries
    queries = load_test_queries(category=args.category, quick=args.quick)
    print(f"Testing {len(queries)} queries with TopK={args.topk}, Model={args.model.split('/')[-1]}")
    print("=" * 80)

    # Initialize
    settings = get_settings()
    searcher = SimplifiedUSDASearcher(
        index_dir=settings.USDA_INDEX_DIR,
        stage1_top_k=100,
        device="cpu"
    )
    hybrid_engine = HybridSearchEngine(index_dir=settings.USDA_INDEX_DIR)
    embedding_service = DeepInfraService(model_id="Qwen/Qwen3-Embedding-8B")
    reranker_service = DeepInfraService(model_id=args.model)

    # Run tests
    passed_count = 0
    failed_count = 0
    total_time = 0
    failed_queries = []

    for q_spec in queries:
        query = q_spec["query"]
        result = await test_query(
            searcher, hybrid_engine, embedding_service, reranker_service,
            query, args.topk, args.model
        )
        total_time += result["reranker_time"]

        passed, issues = check_result(result, q_spec)

        if passed:
            passed_count += 1
            status = "✅"
        else:
            failed_count += 1
            status = "❌"
            failed_queries.append({
                "query": query,
                "issues": issues,
                "got": result["top3"][0][1]
            })

        top_match = result["top3"][0][1][:60]
        score = result["top3"][0][0]
        print(f"{status} {query[:40]:<40} -> {top_match:<60} ({score:.4f})")

    # Summary
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed_count}/{passed_count + failed_count} passed ({passed_count/(passed_count+failed_count)*100:.1f}%)")
    print(f"Total Reranker Time: {total_time:.2f}s ({total_time/len(queries)*1000:.0f}ms/query)")

    if failed_queries:
        print("\n❌ FAILED QUERIES:")
        for fq in failed_queries:
            print(f"  Query: {fq['query']}")
            print(f"    Got: {fq['got']}")
            print(f"    Issues: {', '.join(fq['issues'])}")


if __name__ == "__main__":
    asyncio.run(main())
