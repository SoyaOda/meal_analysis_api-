# -*- coding: utf-8 -*-
"""
Test module for two-stream weighted searcher (spec3.md)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.index.searcher import IndexSearcher


def test_basic_search():
    """Test basic two-stream search"""
    print("\n=== test_basic_search ===")

    # Initialize searcher
    index_dir = project_root / "data"
    if not index_dir.exists():
        print(f"❌ Index directory not found: {index_dir}")
        print("Please run scripts/build_index_small.py first.")
        return False

    searcher = IndexSearcher(str(index_dir), device="cpu")
    print(f"\n{searcher}\n")

    # Test query
    query_main = "chicken"
    query_desc = "grilled"
    print(f"Query: {query_main} | {query_desc}\n")

    candidates = searcher.search(query_main, query_desc, top_k=5)

    print(f"✅ Found {len(candidates)} candidates\n")
    for i, cand in enumerate(candidates, 1):
        print(f"{i}. Score: {cand['score']:.4f} (main={cand['score_main']:.4f}, full={cand['score_full']:.4f})")
        print(f"   {cand['description']}")
        print(f"   Main: {cand['main_name']}, Descriptors: {cand['descriptors'][:60]}...")
        print()

    # Validation
    assert len(candidates) == 5, f"Expected 5 candidates, got {len(candidates)}"
    assert all('score' in c for c in candidates), "All candidates must have 'score'"
    assert all('description' in c for c in candidates), "All candidates must have 'description'"

    print("✅ Basic search test passed!\n")
    return True


def test_weighted_combination():
    """Test that weights affect ranking"""
    print("\n=== test_weighted_combination ===")

    index_dir = project_root / "data"
    searcher = IndexSearcher(str(index_dir), device="cpu")

    query_main = "milk"
    query_desc = "whole"

    candidates = searcher.search(query_main, query_desc, top_k=3)

    print(f"Query: {query_main} | {query_desc}\n")
    print("Top 3 candidates with weighted scores:\n")
    for i, cand in enumerate(candidates, 1):
        combined = cand['score']
        main = cand['score_main']
        full = cand['score_full']
        # Verify: combined ≈ 0.7*main + 0.3*full
        expected = 0.7 * main + 0.3 * full
        print(f"{i}. {cand['description']}")
        print(f"   Combined: {combined:.4f}, Expected: {expected:.4f} (0.7*{main:.4f} + 0.3*{full:.4f})")
        print()

        # Validation: combined score should approximately match weighted sum
        # (may have small floating point differences)
        assert abs(combined - expected) < 0.01, f"Weight calculation error: {combined} vs {expected}"

    print("✅ Weighted combination test passed!\n")
    return True


def test_main_only_query():
    """Test query with no descriptors"""
    print("\n=== test_main_only_query ===")

    index_dir = project_root / "data"
    searcher = IndexSearcher(str(index_dir), device="cpu")

    query_main = "rice"
    query_desc = ""  # No descriptors

    candidates = searcher.search(query_main, query_desc, top_k=5)

    print(f"Query: {query_main} (no descriptors)\n")
    print("Top 5 candidates:\n")
    for i, cand in enumerate(candidates, 1):
        print(f"{i}. Score: {cand['score']:.4f}")
        print(f"   {cand['description']}")
        print()

    assert len(candidates) == 5, f"Expected 5 candidates, got {len(candidates)}"
    print("✅ Main-only query test passed!\n")
    return True


def test_get_item_by_index():
    """Test metadata retrieval by index"""
    print("\n=== test_get_item_by_index ===")

    index_dir = project_root / "data"
    searcher = IndexSearcher(str(index_dir), device="cpu")

    # Get item at index 0
    item = searcher.get_item_by_index(0)
    assert item is not None, "Item at index 0 should exist"
    print(f"Item 0: {item['description']}")

    # Get item at invalid index
    item_invalid = searcher.get_item_by_index(999999)
    assert item_invalid is None, "Invalid index should return None"

    print("✅ Get item by index test passed!\n")
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Two-Stream Searcher (spec3.md) Test Suite")
    print("=" * 60)

    try:
        success = True
        success &= test_basic_search()
        success &= test_weighted_combination()
        success &= test_main_only_query()
        success &= test_get_item_by_index()

        if success:
            print("\n" + "=" * 60)
            print("✅ All tests passed successfully!")
            print("=" * 60)
        return success
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
