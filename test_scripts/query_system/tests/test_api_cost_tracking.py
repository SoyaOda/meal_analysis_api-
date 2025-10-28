#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Cost Tracking Test

修正したsrc/内のスクリプトでAPI使用統計が正しく記録されるかテストします。
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def main():
    """メインテスト"""
    print("=" * 80)
    print("API Cost Tracking Test")
    print("=" * 80)

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=100
    )

    print(f"\n{pipeline}\n")

    # Test queries
    test_queries = [
        {"main": "beef steak", "desc": "grilled, sliced"},
        {"main": "chicken breast", "desc": "cooked, boneless, skinless"},
        {"main": "mixed greens", "desc": "raw"},
    ]

    # Reset stats before testing
    pipeline.reset_usage_stats()

    # Run searches
    print("\n🔍 Running test queries...")
    print("-" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] {query['main']} | {query['desc']}")

        result = pipeline.search(
            query_main=query['main'],
            query_descriptors=query['desc'],
            return_top_k=5
        )

        best_match = result['top_k'][0]
        print(f"  ✓ Best Match: {best_match['description']}")
        print(f"    Score: {best_match['rerank_score']:.4f}")

    # Display API usage statistics
    pipeline.print_usage_stats()

    # Get stats for programmatic use
    stats = pipeline.get_usage_stats()

    # Calculate per-query average
    num_queries = len(test_queries)
    avg_cost = stats['total_cost_usd'] / num_queries

    print("\n" + "=" * 80)
    print("PER-QUERY AVERAGE")
    print("=" * 80)
    print(f"Average Cost per Query: ${avg_cost:.6f}")
    print(f"Estimated cost for 1,000 queries: ${avg_cost * 1000:.2f}")
    print(f"Estimated cost for 10,000 queries: ${avg_cost * 10000:.2f}")
    print("=" * 80)

    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
