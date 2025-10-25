# -*- coding: utf-8 -*-
"""
Test full index search with realistic queries
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def test_realistic_queries():
    """Test with realistic food queries"""
    print("\n" + "=" * 60)
    print("Full Index Search Test (5,772 items)")
    print("=" * 60)

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=20
    )

    print(f"\n{pipeline}\n")

    # Realistic test queries
    test_queries = [
        {"main": "chicken breast", "descriptors": "grilled, boneless"},
        {"main": "rice", "descriptors": "white, cooked"},
        {"main": "salmon", "descriptors": "baked"},
        {"main": "broccoli", "descriptors": "steamed"},
        {"main": "bread", "descriptors": "whole wheat"},
        {"main": "egg", "descriptors": "scrambled"},
        {"main": "apple", "descriptors": "fresh"},
        {"main": "steak", "descriptors": "grilled"},
    ]

    print("Testing realistic queries:\n")

    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Query: {query['main']} | {query['descriptors']}")

        result = pipeline.search(
            query_main=query['main'],
            query_descriptors=query['descriptors'],
            return_top_k=3
        )

        best = result['best_match']
        print(f"   Best Match (score: {best['rerank_score']:.4f}):")
        print(f"   → {best['description']}")
        print(f"   Source: {best['source']}, FDC ID: {best['fdc_id']}")

        print(f"\n   Top 3:")
        for rank, item in enumerate(result['top_k'], 1):
            print(f"   {rank}. {item['rerank_score']:.4f} - {item['description']}")

        print()

    print("=" * 60)
    print("✅ Full index search test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_realistic_queries()
