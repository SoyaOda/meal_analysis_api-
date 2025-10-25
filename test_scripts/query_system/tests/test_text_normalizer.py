# -*- coding: utf-8 -*-
"""
Test module for text normalization
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing.text_normalizer import (
    normalize_text,
    parse_usda_name,
    build_query_text,
    build_usda_text
)


def load_test_data():
    """Load prepared test data"""
    data_dir = Path(__file__).parent / "data"

    with open(data_dir / "test_queries.json", 'r', encoding='utf-8') as f:
        queries = json.load(f)

    with open(data_dir / "test_usda_items.json", 'r', encoding='utf-8') as f:
        usda_items = json.load(f)

    return queries, usda_items


def test_normalize_text():
    """Test normalize_text function"""
    print("\n=== test_normalize_text ===")

    # Test case 1: Basic normalization
    result = normalize_text("Chicken, Broiled")
    expected = "chicken broiled"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 1 passed: '{result}'")

    # Test case 2: Remove special characters
    result = normalize_text("French-Fries (Deep-Fried)")
    expected = "french fries deep fried"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 2 passed: '{result}'")

    # Test case 3: Handle multiple spaces
    result = normalize_text("Rice   with    vegetables")
    expected = "rice with vegetables"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 3 passed: '{result}'")

    # Test case 4: Empty string
    result = normalize_text("")
    expected = ""
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 4 passed: empty string")

    print("All normalize_text tests passed!")


def test_parse_usda_name():
    """Test parse_usda_name function"""
    print("\n=== test_parse_usda_name ===")

    # Test case 1: Standard USDA format
    result = parse_usda_name("11001. Chicken, broilers, breast, cooked")
    expected = ("Chicken", "broilers, breast, cooked")
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"Test 1 passed: {result}")

    # Test case 2: Without number prefix
    result = parse_usda_name("Chicken breast")
    expected = ("Chicken breast", "")
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"Test 2 passed: {result}")

    # Test case 3: No description
    result = parse_usda_name("12345. Rice")
    expected = ("Rice", "")
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"Test 3 passed: {result}")

    # Test case 4: Complex description
    result = parse_usda_name("20001. Beef, ground, 90% lean meat / 10% fat, raw")
    expected = ("Beef", "ground, 90% lean meat / 10% fat, raw")
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"Test 4 passed: {result}")

    print("All parse_usda_name tests passed!")


def test_build_query_text():
    """Test build_query_text function"""
    print("\n=== test_build_query_text ===")

    # Test case 1: Combine search_name and description
    result = build_query_text("chicken breast", "grilled")
    expected = "chicken breast grilled"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 1 passed: '{result}'")

    # Test case 2: No description
    result = build_query_text("rice", "")
    expected = "rice"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 2 passed: '{result}'")

    # Test case 3: With surrounding spaces (strip() keeps internal spaces)
    result = build_query_text("  salmon  ", "  baked  ")
    expected = "salmon     baked"  # Internal spaces from both strings are preserved
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 3 passed: '{result}'")

    print("All build_query_text tests passed!")


def test_build_usda_text():
    """Test build_usda_text function"""
    print("\n=== test_build_usda_text ===")

    # Test case 1: Standard USDA item (using test data structure)
    item = {"default_usda": {"name": "11001. Chicken, broiled, skinless"}}
    result = build_usda_text(item)
    expected = "Chicken broiled, skinless"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 1 passed: '{result}'")

    # Test case 2: No description
    item = {"default_usda": {"name": "12345. Rice"}}
    result = build_usda_text(item)
    expected = "Rice"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 2 passed: '{result}'")

    # Test case 3: Missing default_usda key
    item = {"other_key": "some value"}
    result = build_usda_text(item)
    expected = ""
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 3 passed: empty string for missing key")

    # Test case 4: Missing name key
    item = {"default_usda": {"other_field": "value"}}
    result = build_usda_text(item)
    expected = ""
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"Test 4 passed: empty string for missing name")

    print("All build_usda_text tests passed!")


def test_with_real_data():
    """Test with actual VLM and USDA data"""
    print("\n=== test_with_real_data ===")

    queries, usda_items = load_test_data()

    # Test query normalization (from VLM)
    print("\nTesting VLM query normalization:")
    for i, query in enumerate(queries[:3], 1):
        query_text = build_query_text(query['search_name'], query['description'])
        normalized = normalize_text(query_text)
        print(f"{i}. Original: '{query['search_name']} - {query['description']}'")
        print(f"   Normalized: '{normalized}'")

    # Test USDA name parsing
    print("\nTesting USDA name parsing:")
    for i, item in enumerate(usda_items[:3], 1):
        # Convert to the structure expected by build_usda_text
        usda_item = {"default_usda": {"name": item['usda_name']}}
        usda_text = build_usda_text(usda_item)
        normalized = normalize_text(usda_text)
        print(f"{i}. USDA Name: '{item['usda_name']}'")
        print(f"   Built Text: '{usda_text}'")
        print(f"   Normalized: '{normalized}'")

    print("\nReal data test completed!")


def test_integration():
    """Integration test: Full processing flow"""
    print("\n=== test_integration ===")

    queries, usda_items = load_test_data()

    # Simulate matching process
    query = queries[4]  # "beef steak - grilled, sliced"
    query_text = build_query_text(query['search_name'], query['description'])
    query_normalized = normalize_text(query_text)

    print(f"Query: {query['search_name']} - {query['description']}")
    print(f"Query normalized: '{query_normalized}'")

    # Process USDA items
    print("\nProcessing USDA items containing 'beef':")
    for item in usda_items:
        if 'beef' in item['display_name'].lower():
            usda_item = {"default_usda": {"name": item['usda_name']}}
            usda_text = build_usda_text(usda_item)
            usda_normalized = normalize_text(usda_text)
            print(f"  - {item['display_name']}: '{usda_normalized}'")

    print("\nIntegration test completed!")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Text Normalizer Test Suite")
    print("=" * 60)

    try:
        test_normalize_text()
        test_parse_usda_name()
        test_build_query_text()
        test_build_usda_text()
        test_with_real_data()
        test_integration()

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