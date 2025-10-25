# -*- coding: utf-8 -*-
"""
Test module for text_normalizer (spec3.md two-stream approach)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing.text_normalizer import (
    build_main_only_text,
    build_full_text,
    build_rerank_text,
    parse_usda_name,
    normalize_text
)


def test_build_main_only_text():
    """Test main_only text generation"""
    print("\n=== test_build_main_only_text ===")

    # Test case 1: Simple name
    result = build_main_only_text("Chicken")
    assert result == "Chicken", f"Expected 'Chicken', got '{result}'"
    print("✅ Test 1 passed: Simple name")

    # Test case 2: Name with spaces
    result = build_main_only_text("Beef steak")
    assert result == "Beef steak", f"Expected 'Beef steak', got '{result}'"
    print("✅ Test 2 passed: Name with spaces")

    # Test case 3: Name with leading/trailing spaces
    result = build_main_only_text("  Rice  ")
    assert result == "Rice", f"Expected 'Rice', got '{result}'"
    print("✅ Test 3 passed: Trim spaces")

    print("All build_main_only_text tests passed!\n")


def test_build_full_text():
    """Test full text generation with separator"""
    print("\n=== test_build_full_text ===")

    # Test case 1: With descriptors
    result = build_full_text("Chicken", "broilers, breast, cooked, roasted")
    expected = "Chicken ; broilers breast cooked roasted"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✅ Test 1 passed: With descriptors")

    # Test case 2: Without descriptors
    result = build_full_text("Beef", "")
    assert result == "Beef", f"Expected 'Beef', got '{result}'"
    print("✅ Test 2 passed: Without descriptors")

    # Test case 3: Complex descriptors
    result = build_full_text("Pork", "ground, 85% lean, cooked, pan-fried")
    expected = "Pork ; ground 85% lean cooked pan-fried"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✅ Test 3 passed: Complex descriptors")

    # Test case 4: Descriptors with multiple spaces
    result = build_full_text("Fish", "raw,  fresh,  whole")
    expected = "Fish ; raw fresh whole"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✅ Test 4 passed: Normalize spaces in descriptors")

    print("All build_full_text tests passed!\n")


def test_build_rerank_text():
    """Test rerank text generation with field labels"""
    print("\n=== test_build_rerank_text ===")

    # Test case 1: Query with description
    result = build_rerank_text("chicken breast", "grilled", is_query=True)
    expected = "name: chicken breast\ndescription: grilled"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✅ Test 1 passed: Query with description")

    # Test case 2: Query without description
    result = build_rerank_text("rice", "", is_query=True)
    expected = "name: rice\ndescription: N/A"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✅ Test 2 passed: Query without description")

    # Test case 3: Candidate with description
    result = build_rerank_text("Chicken", "broilers, cooked, roasted", is_query=False)
    expected = "name: Chicken\ndescription: broilers, cooked, roasted"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✅ Test 3 passed: Candidate with description")

    # Test case 4: None values
    result = build_rerank_text("", "", is_query=True)
    expected = "name: N/A\ndescription: N/A"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print("✅ Test 4 passed: Handle empty values")

    print("All build_rerank_text tests passed!\n")


def test_integration_two_stream():
    """Test integration of two-stream approach"""
    print("\n=== test_integration_two_stream ===")

    # USDA name example
    usda_name = "57. Chicken, broilers or fryers, breast, meat only, cooked, grilled"

    # Step 1: Parse
    main_name, descriptors = parse_usda_name(usda_name)
    print(f"Parsed USDA name:")
    print(f"  main_name: '{main_name}'")
    print(f"  descriptors: '{descriptors}'")
    assert main_name == "Chicken", f"Expected 'Chicken', got '{main_name}'"
    assert "broilers" in descriptors, f"Expected 'broilers' in descriptors"

    # Step 2: Build main_only text
    main_text = build_main_only_text(main_name)
    main_normalized = normalize_text(main_text)
    print(f"\nMain-only:")
    print(f"  Raw: '{main_text}'")
    print(f"  Normalized: '{main_normalized}'")
    assert main_normalized == "chicken", f"Expected 'chicken', got '{main_normalized}'"

    # Step 3: Build full text
    full_text = build_full_text(main_name, descriptors)
    full_normalized = normalize_text(full_text)
    print(f"\nFull text:")
    print(f"  Raw: '{full_text}'")
    print(f"  Normalized: '{full_normalized}'")
    assert "chicken" in full_normalized, "chicken should be in full_normalized"
    assert "broilers" in full_normalized, "broilers should be in full_normalized"
    assert ";" not in full_normalized, "Separator should be removed by normalization"

    # Step 4: Build rerank text
    rerank_text = build_rerank_text(main_name, descriptors, is_query=False)
    print(f"\nRerank text:")
    print(f"  {repr(rerank_text)}")
    assert "name: Chicken" in rerank_text, "Should contain 'name: Chicken'"
    assert "description:" in rerank_text, "Should contain 'description:'"

    print("\n✅ All integration tests passed!")


def test_comparison_example():
    """Test comparison: main vs full embeddings"""
    print("\n=== test_comparison_example ===")

    # Example 1: "Chicken, grilled"
    main1, desc1 = "Chicken", "grilled"
    main_text1 = build_main_only_text(main1)
    full_text1 = build_full_text(main1, desc1)

    print(f"\nExample 1: Chicken, grilled")
    print(f"  main_only: '{normalize_text(main_text1)}'")
    print(f"  full:      '{normalize_text(full_text1)}'")

    # Example 2: "Fried chicken"
    main2, desc2 = "Chicken", "fried"
    main_text2 = build_main_only_text(main2)
    full_text2 = build_full_text(main2, desc2)

    print(f"\nExample 2: Chicken, fried")
    print(f"  main_only: '{normalize_text(main_text2)}'")
    print(f"  full:      '{normalize_text(full_text2)}'")

    # Example 3: "Fried rice" (different main!)
    main3, desc3 = "Rice", "fried"
    main_text3 = build_main_only_text(main3)
    full_text3 = build_full_text(main3, desc3)

    print(f"\nExample 3: Rice, fried")
    print(f"  main_only: '{normalize_text(main_text3)}'")
    print(f"  full:      '{normalize_text(full_text3)}'")

    print("\n💡 Key insight:")
    print("  - main_only embeddings: 'chicken' vs 'rice' (clearly different)")
    print("  - full embeddings: both contain 'fried', but main name distinguishes them")
    print("  - Weighted combination (0.7*main + 0.3*full) prevents 'fried' from dominating")

    print("\n✅ Comparison example completed!")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Text Normalizer (spec3.md) Test Suite")
    print("=" * 60)

    try:
        test_build_main_only_text()
        test_build_full_text()
        test_build_rerank_text()
        test_integration_two_stream()
        test_comparison_example()

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
