# -*- coding: utf-8 -*-
"""
Test module for reranker with spec3.md field-labeled input
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.reranker import RerankerModel
from src.preprocessing.text_normalizer import build_rerank_text


def test_field_labeled_reranking():
    """Test reranking with field-labeled templates"""
    print("\n=== test_field_labeled_reranking ===")

    # Initialize reranker
    model = RerankerModel()

    # Query
    query_main = "chicken breast"
    query_desc = "grilled"
    query_text = build_rerank_text(query_main, query_desc, is_query=True)

    # Candidates
    candidates_data = [
        ("Chicken", "broilers, breast, meat only, cooked, grilled"),
        ("Chicken", "broilers, breast, meat and skin, cooked, roasted"),
        ("Turkey", "breast, meat only, cooked"),
        ("Beef", "steak, grilled"),
    ]

    # Build field-labeled candidate texts
    candidate_texts = [
        build_rerank_text(main, desc, is_query=False)
        for main, desc in candidates_data
    ]

    print(f"\n📍 Query (field-labeled):")
    print(f"{repr(query_text)}\n")

    print(f"📚 Candidates (field-labeled):")
    for i, text in enumerate(candidate_texts, 1):
        print(f"{i}. {repr(text)}")

    # Rerank
    best_idx, scores = model.rerank(query_text, candidate_texts, return_scores=True)

    print(f"\n🏆 Scores:")
    for i, (data, score) in enumerate(zip(candidates_data, scores)):
        main, desc = data
        marker = " ⭐" if i == best_idx else ""
        print(f"  {i}. {score:8.4f} - {main} ({desc}){marker}")

    print(f"\n✅ Best match: #{best_idx + 1} - {candidates_data[best_idx][0]}")

    # Validation
    assert best_idx == 0, f"Expected best_idx=0 (grilled chicken breast), got {best_idx}"
    assert scores[best_idx] > scores[1], "Grilled should score higher than roasted"
    assert scores[0] > scores[2], "Chicken should score higher than turkey"
    assert scores[0] > scores[3], "Chicken breast should score higher than beef steak"

    print("✅ All validations passed!")


def test_comparison_with_without_labels():
    """Compare reranking with and without field labels"""
    print("\n=== test_comparison_with_without_labels ===")

    model = RerankerModel()

    query_main = "fried chicken"
    query_desc = "crispy, wings"

    candidate_main = "Chicken"
    candidate_desc = "wings, fried, breaded"

    # Without labels (simple concatenation)
    query_simple = f"{query_main} {query_desc}"
    candidate_simple = f"{candidate_main} {candidate_desc}"

    # With labels (field-labeled)
    query_labeled = build_rerank_text(query_main, query_desc, is_query=True)
    candidate_labeled = build_rerank_text(candidate_main, candidate_desc, is_query=False)

    # Score both approaches
    score_simple = model.score_pairs([(query_simple, candidate_simple)])[0]
    score_labeled = model.score_pairs([(query_labeled, candidate_labeled)])[0]

    print(f"\n📊 Comparison:")
    print(f"  Simple concatenation: {score_simple:.4f}")
    print(f"    Query:     '{query_simple}'")
    print(f"    Candidate: '{candidate_simple}'")
    print(f"\n  Field-labeled:        {score_labeled:.4f}")
    print(f"    Query:     {repr(query_labeled)}")
    print(f"    Candidate: {repr(candidate_labeled)}")

    print(f"\n💡 Field-labeled approach:")
    print(f"   - Explicitly separates main name from descriptors")
    print(f"   - Helps model understand structure")
    print(f"   - Reduces over-emphasis on modifier words like 'fried'")

    print("\n✅ Comparison completed!")


def test_nfs_ns_handling():
    """Test handling of NFS/NS (Not Further Specified) cases"""
    print("\n=== test_nfs_ns_handling ===")

    model = RerankerModel()

    # Query without specific cooking method
    query_text = build_rerank_text("chicken breast", "", is_query=True)

    # Candidates including NFS
    candidates = [
        build_rerank_text("Chicken", "breast, NFS", is_query=False),
        build_rerank_text("Chicken", "breast, raw", is_query=False),
        build_rerank_text("Chicken", "breast, cooked, grilled", is_query=False),
    ]

    best_idx, scores = model.rerank(query_text, candidates, return_scores=True)

    print(f"\n📍 Query (ambiguous): 'chicken breast' (no cooking method)")
    print(f"\n🏆 Scores:")
    labels = ["NFS (unspecified)", "raw", "cooked, grilled"]
    for i, (label, score) in enumerate(zip(labels, scores)):
        marker = " ⭐" if i == best_idx else ""
        print(f"  {i}. {score:8.4f} - {label}{marker}")

    print(f"\n💡 NFS/NS is useful when:")
    print(f"   - Cooking method is ambiguous from image/text")
    print(f"   - Want a 'safe' generic match")
    print(f"   - Avoid raw vs cooked mismatch")

    print("\n✅ NFS handling test completed!")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Reranker (spec3.md field-labeled) Test Suite")
    print("=" * 60)

    try:
        test_field_labeled_reranking()
        test_comparison_with_without_labels()
        test_nfs_ns_handling()

        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
        return True
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
