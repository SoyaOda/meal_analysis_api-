# -*- coding: utf-8 -*-
"""
Evaluation test using real test queries
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def load_test_queries(file_path: str):
    """Load test queries from JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_match_quality(query, top_results):
    """
    Evaluate if the matched food is suitable for nutrition calculation

    Returns: (is_good, reason)
    """
    query_name = query['search_name'].lower()
    query_desc = query['description'].lower()

    best_match = top_results[0]
    match_desc = best_match['description'].lower()
    match_main = best_match['main_name'].lower()

    # Check if main food name matches
    main_match = any(word in match_main for word in query_name.split())

    # Check if cooking method matches
    cooking_methods = ['raw', 'cooked', 'grilled', 'roasted', 'baked', 'fried', 'steamed', 'boiled']
    query_methods = [m for m in cooking_methods if m in query_desc]
    match_methods = [m for m in cooking_methods if m in match_desc]

    # Evaluation criteria
    if not main_match:
        return False, "Main food name doesn't match"

    # If query specifies cooking method, check if it's preserved
    if query_methods:
        if not any(qm in match_desc for qm in query_methods):
            # Check if alternative cooking method is close enough
            if 'raw' in query_methods and not match_methods:
                return True, "OK - raw matches unspecified"
            elif 'cooked' in query_methods and match_methods:
                return True, f"OK - cooked matches {match_methods[0]}"
            else:
                return False, f"Cooking method mismatch: query={query_methods}, match={match_methods}"

    return True, "Good match"


def main():
    """Run evaluation test"""
    print("\n" + "=" * 80)
    print("EVALUATION TEST: Real Query Data (20 items)")
    print("=" * 80)

    # Load test queries
    test_data_path = project_root / "tests" / "data" / "test_queries.json"
    queries = load_test_queries(str(test_data_path))

    print(f"\n📋 Loaded {len(queries)} test queries\n")

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=20
    )

    print(f"{pipeline}\n")
    print("=" * 80)

    # Run evaluation
    results = []
    good_matches = 0

    for i, query in enumerate(queries, 1):
        query_main = query['search_name']
        query_desc = query['description']

        print(f"\n[{i}/20] Query: {query_main} | {query_desc}")
        print(f"        Weight: {query['weight_g']}g, Confidence: {query['confidence']}")

        # Search
        result = pipeline.search(
            query_main=query_main,
            query_descriptors=query_desc,
            return_top_k=5
        )

        # Evaluate
        is_good, reason = evaluate_match_quality(query, result['top_k'])

        # Display results
        print(f"\n        Best Match (score: {result['best_match']['rerank_score']:.4f}):")
        print(f"        → {result['best_match']['description']}")
        print(f"        Source: {result['best_match']['source']}, FDC ID: {result['best_match']['fdc_id']}")

        # Evaluation result
        status = "✅" if is_good else "⚠️"
        print(f"\n        {status} Evaluation: {reason}")

        if is_good:
            good_matches += 1

        # Show alternatives
        if len(result['top_k']) > 1:
            print(f"\n        Alternatives:")
            for rank, item in enumerate(result['top_k'][1:4], 2):
                print(f"        {rank}. {item['rerank_score']:.4f} - {item['description']}")

        # Store result
        results.append({
            'query': query,
            'best_match': result['best_match'],
            'is_good': is_good,
            'reason': reason
        })

        print("-" * 80)

    # Summary
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)

    accuracy = (good_matches / len(queries)) * 100
    print(f"\nGood Matches: {good_matches}/{len(queries)} ({accuracy:.1f}%)")

    # Show problematic cases
    problematic = [r for r in results if not r['is_good']]
    if problematic:
        print(f"\n⚠️  Problematic Cases ({len(problematic)}):")
        for i, r in enumerate(problematic, 1):
            q = r['query']
            print(f"\n{i}. Query: {q['search_name']} | {q['description']}")
            print(f"   Matched: {r['best_match']['description']}")
            print(f"   Issue: {r['reason']}")
    else:
        print("\n✅ All matches are suitable for nutrition calculation!")

    print("\n" + "=" * 80)
    print(f"✅ Evaluation completed!")
    print("=" * 80)

    return accuracy >= 75.0  # 75% accuracy threshold


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
