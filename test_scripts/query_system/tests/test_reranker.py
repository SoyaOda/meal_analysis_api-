# -*- coding: utf-8 -*-
"""
Test module for reranker model
"""

import sys
import json
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.reranker import RerankerModel
from src.preprocessing.text_normalizer import normalize_text, build_query_text, parse_usda_name


def load_test_data():
    """Load prepared test data"""
    data_dir = Path(__file__).parent / "data"

    with open(data_dir / "test_queries.json", 'r', encoding='utf-8') as f:
        queries = json.load(f)

    with open(data_dir / "test_usda_items.json", 'r', encoding='utf-8') as f:
        usda_items = json.load(f)

    return queries, usda_items


def test_model_initialization():
    """Test reranker model initialization"""
    print("\n=== test_model_initialization ===")

    # Test with default parameters
    model = RerankerModel()
    assert model is not None, "Model should be initialized"
    assert model.model_name == "BAAI/bge-reranker-base", "Default model name should match"
    assert model.device == "cpu", "Default device should be cpu"
    print("Test passed: Model initialized successfully")

    print("All model initialization tests passed!")
    return model


def test_rerank_candidates(model):
    """Test reranking candidates"""
    print("\n=== test_rerank_candidates ===")

    query = "grilled chicken breast"
    candidates = [
        "chicken breast grilled skinless",
        "chocolate cake with frosting",
        "grilled fish fillet",
        "chicken curry with rice",
        "roasted chicken"
    ]

    # Test case 1: Get best index without scores
    best_idx = model.rerank(query, candidates, return_scores=False)
    assert isinstance(best_idx, (int, np.integer)), "Best index should be integer"
    assert 0 <= best_idx < len(candidates), f"Best index {best_idx} should be in range [0, {len(candidates)})"
    print(f"Test 1 passed: Best match index = {best_idx} ('{candidates[best_idx]}')")

    # Test case 2: Get best index with scores
    print(f"\nDebug: query='{query}'")
    print(f"Debug: candidates={candidates}")
    best_idx, scores = model.rerank(query, candidates, return_scores=True)
    print(f"Debug: scores={scores}")
    print(f"Debug: scores dtype={scores.dtype}")
    assert isinstance(best_idx, (int, np.integer)), "Best index should be integer"
    assert isinstance(scores, np.ndarray), "Scores should be numpy array"
    assert len(scores) == len(candidates), f"Should have {len(candidates)} scores, got {len(scores)}"
    print(f"Test 2 passed: Best index = {best_idx}, got {len(scores)} scores")

    # Test case 3: Check scores are reasonable
    print("\nScores for all candidates:")
    for i, (cand, score) in enumerate(zip(candidates, scores)):
        print(f"  {i}. {score:8.4f} - '{cand}'")

    # Best candidate should have highest score
    assert scores[best_idx] == np.max(scores), "Best candidate should have highest score"
    print(f"\nTest 3 passed: Best candidate has highest score ({scores[best_idx]:.4f})")

    # Most relevant candidate (chicken breast) should be ranked higher than chocolate cake
    chicken_idx = 0
    cake_idx = 1
    assert scores[chicken_idx] > scores[cake_idx], "Chicken should score higher than cake for chicken query"
    print(f"Test 4 passed: Relevant candidate scored higher (chicken: {scores[chicken_idx]:.4f} > cake: {scores[cake_idx]:.4f})")

    print("All rerank tests passed!")


def test_score_pairs(model):
    """Test scoring text pairs"""
    print("\n=== test_score_pairs ===")

    pairs = [
        ("chicken breast", "grilled chicken"),
        ("chicken breast", "chocolate cake"),
        ("beef steak", "beef tenderloin"),
        ("rice", "pasta")
    ]

    scores = model.score_pairs(pairs)

    assert isinstance(scores, np.ndarray), "Scores should be numpy array"
    assert len(scores) == len(pairs), f"Should have {len(pairs)} scores, got {len(scores)}"
    print(f"Test 1 passed: Scored {len(pairs)} pairs")

    print("\nPair scores:")
    for i, (pair, score) in enumerate(zip(pairs, scores)):
        print(f"  {i}. {score:8.4f} - ('{pair[0]}', '{pair[1]}')")

    # Similar pairs should score higher than dissimilar pairs
    assert scores[0] > scores[1], "Similar pair (chicken-chicken) should score higher than dissimilar pair (chicken-cake)"
    print(f"\nTest 2 passed: Similar pairs scored higher")

    print("All score_pairs tests passed!")


def test_with_real_data(model):
    """Test with actual VLM and USDA data"""
    print("\n=== test_with_real_data ===")

    queries, usda_items = load_test_data()

    # Use "beef steak" query
    query_data = [q for q in queries if "beef" in q['search_name'].lower()][0]
    query_text = build_query_text(query_data['search_name'], query_data['description'])
    query_normalized = normalize_text(query_text)

    print(f"Query: '{query_data['search_name']} - {query_data['description']}'")
    print(f"Normalized: '{query_normalized}'")

    # Get beef-related USDA candidates
    beef_usda = [item for item in usda_items if 'beef' in item['display_name'].lower()][:10]

    candidates = []
    for item in beef_usda:
        search_name, description = parse_usda_name(item['usda_name'])
        text = f"{search_name} {description}".strip()
        normalized = normalize_text(text)
        candidates.append(normalized)

    print(f"\nFound {len(candidates)} beef-related USDA items")

    # Rerank candidates
    best_idx, scores = model.rerank(query_normalized, candidates, return_scores=True)

    print(f"\nTop 5 ranked candidates:")
    # Sort by score descending
    sorted_indices = np.argsort(scores)[::-1]
    for i, idx in enumerate(sorted_indices[:5], 1):
        print(f"  {i}. {scores[idx]:8.4f} - {beef_usda[idx]['display_name']}")
        print(f"               '{candidates[idx]}'")

    print(f"\nBest match: {beef_usda[best_idx]['display_name']}")
    print(f"Score: {scores[best_idx]:.4f}")

    print("\nAll real data tests passed!")


def test_empty_candidates_handling(model):
    """Test error handling for empty candidates"""
    print("\n=== test_empty_candidates_handling ===")

    query = "chicken breast"
    candidates = []

    try:
        model.rerank(query, candidates)
        assert False, "Should raise ValueError for empty candidates"
    except ValueError as e:
        print(f"Test passed: Correctly raised ValueError: {e}")

    print("All error handling tests passed!")


def test_consistency(model):
    """Test that same inputs produce same outputs"""
    print("\n=== test_consistency ===")

    query = "grilled chicken"
    candidates = [
        "chicken breast grilled",
        "chocolate cake",
        "grilled fish"
    ]

    # Rerank twice
    best_idx1, scores1 = model.rerank(query, candidates, return_scores=True)
    best_idx2, scores2 = model.rerank(query, candidates, return_scores=True)

    # Check consistency
    assert best_idx1 == best_idx2, "Same inputs should produce same best index"
    assert np.allclose(scores1, scores2), "Same inputs should produce same scores"
    print(f"Test passed: Results are consistent (best_idx={best_idx1}, max score diff={np.max(np.abs(scores1-scores2))})")

    print("All consistency tests passed!")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Reranker Model Test Suite")
    print("=" * 60)

    try:
        # Initialize model once for all tests
        model = test_model_initialization()

        # Run other tests
        test_rerank_candidates(model)
        test_score_pairs(model)
        test_consistency(model)
        test_empty_candidates_handling(model)
        test_with_real_data(model)

        print("\n" + "=" * 60)
        print("All tests passed successfully!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        return False
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)