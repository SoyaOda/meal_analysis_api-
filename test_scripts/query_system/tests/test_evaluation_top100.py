# -*- coding: utf-8 -*-
"""
Evaluation test using real test queries with stage1_top_k=100
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
    print("EVALUATION TEST: Real Query Data (20 items) - stage1_top_k=100")
    print("=" * 80)

    # Load test queries
    test_data_path = project_root / "tests" / "data" / "test_queries.json"
    queries = load_test_queries(str(test_data_path))

    print(f"\n📋 Loaded {len(queries)} test queries\n")

    # Initialize pipeline with stage1_top_k=100
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=100  # CHANGED: Increased from 20 to 100
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

        top_match = result['top_k'][0]

        print(f"\n        Best Match (score: {top_match['rerank_score']:.4f}):")
        print(f"        → {top_match['description']}")
        print(f"        Source: {top_match['source']}, FDC ID: {top_match['fdc_id']}")

        # Evaluate match quality
        is_good, reason = evaluate_match_quality(query, result['top_k'])

        if is_good:
            print(f"\n        ✅ Evaluation: {reason}")
            good_matches += 1
        else:
            print(f"\n        ⚠️ Evaluation: {reason}")

        # Show alternatives
        print(f"\n        Alternatives:")
        for j, item in enumerate(result['top_k'][1:5], 2):
            print(f"        {j}. {item['rerank_score']:.4f} - {item['description']}")

        print("-" * 80)

        results.append({
            'query': f"{query_main} | {query_desc}",
            'matched': top_match['description'],
            'is_good': is_good,
            'reason': reason
        })

    # Summary
    accuracy = (good_matches / len(queries)) * 100
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"\nGood Matches: {good_matches}/{len(queries)} ({accuracy:.1f}%)")

    # Show problematic cases
    problematic = [r for r in results if not r['is_good']]
    if problematic:
        print(f"\n⚠️  Problematic Cases ({len(problematic)}):")
        for i, r in enumerate(problematic, 1):
            print(f"\n{i}. Query: {r['query']}")
            print(f"   Matched: {r['matched']}")
            print(f"   Issue: {r['reason']}")

    print("\n" + "=" * 80)
    print("✅ Evaluation completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
