# -*- coding: utf-8 -*-
"""
Test data preparation script

Prepares test dataset from actual VLM analysis results and USDA database.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Data file paths
VLM_TEST_RESULTS = project_root.parent / "output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json"
USDA_MAPPINGS = project_root.parent / "mappings/mappings_final/usda_food_mappings_unified.json"


def load_vlm_test_data() -> List[Dict]:
    """
    Load query data from VLM test results

    Returns:
        List of query data [{"search_name": str, "description": str, ...}, ...]
    """
    print(f"Loading VLM test data from: {VLM_TEST_RESULTS}")

    with open(VLM_TEST_RESULTS, 'r', encoding='utf-8') as f:
        data = json.load(f)

    query_items = []

    for result in data.get('results', []):
        if not result.get('success'):
            continue

        vlm_response = result.get('vlm_response', {})
        dishes = vlm_response.get('dishes', [])

        for dish in dishes:
            # Add main_food
            if dish.get('main_food'):
                main_food = dish['main_food']
                query_items.append({
                    'search_name': main_food.get('search_name', ''),
                    'description': main_food.get('description', ''),
                    'weight_g': main_food.get('weight_g', 0),
                    'confidence': main_food.get('confidence', 0.0),
                    'image_file': result.get('image_file', '')
                })

            # Add extras
            for extra in dish.get('extras', []):
                query_items.append({
                    'search_name': extra.get('search_name', ''),
                    'description': extra.get('description', ''),
                    'weight_g': extra.get('weight_g', 0),
                    'confidence': extra.get('confidence', 0.0),
                    'image_file': result.get('image_file', '')
                })

    print(f"Loaded {len(query_items)} query items from VLM results")
    return query_items


def load_usda_database() -> List[Dict]:
    """
    Load USDA mapping database

    Returns:
        List of USDA food data [{"id": str, "usda_name": str, ...}, ...]
    """
    print(f"Loading USDA database from: {USDA_MAPPINGS}")

    with open(USDA_MAPPINGS, 'r', encoding='utf-8') as f:
        data = json.load(f)

    usda_items = []

    for food_id, food_data in data.items():
        default_usda = food_data.get('default_usda', {})
        usda_name = default_usda.get('name', '')

        if not usda_name:
            continue

        usda_items.append({
            'id': food_id,
            'usda_name': usda_name,
            'display_name': food_data.get('display_name', ''),
            'category': food_data.get('category', ''),
            'role': food_data.get('role', ''),
            'aliases': food_data.get('aliases', [])
        })

    print(f"Loaded {len(usda_items)} USDA items from database")
    return usda_items


def extract_sample_data(
    query_items: List[Dict],
    usda_items: List[Dict],
    num_queries: int = 10,
    num_usda: int = 50
) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract sample data for testing

    Args:
        query_items: All query data
        usda_items: All USDA food data
        num_queries: Number of queries to extract
        num_usda: Number of USDA items to extract

    Returns:
        (sample queries, sample USDA data)
    """
    # Select from different search_names for diversity
    unique_queries = {}
    for item in query_items:
        name = item['search_name']
        if name not in unique_queries:
            unique_queries[name] = item

    sample_queries = list(unique_queries.values())[:num_queries]
    sample_usda = usda_items[:num_usda]

    print(f"Extracted {len(sample_queries)} sample queries and {len(sample_usda)} sample USDA items")
    return sample_queries, sample_usda


def save_test_data(
    query_items: List[Dict],
    usda_items: List[Dict],
    output_dir: Path
):
    """
    Save test data as JSON files

    Args:
        query_items: Query data
        usda_items: USDA food data
        output_dir: Output directory
    """
    output_dir.mkdir(exist_ok=True)

    # Save query data
    query_file = output_dir / "test_queries.json"
    with open(query_file, 'w', encoding='utf-8') as f:
        json.dump(query_items, f, indent=2, ensure_ascii=False)
    print(f"Saved query data to: {query_file}")

    # Save USDA data
    usda_file = output_dir / "test_usda_items.json"
    with open(usda_file, 'w', encoding='utf-8') as f:
        json.dump(usda_items, f, indent=2, ensure_ascii=False)
    print(f"Saved USDA data to: {usda_file}")


def display_sample_data(query_items: List[Dict], usda_items: List[Dict]):
    """
    Display sample data content
    """
    print("\n" + "=" * 60)
    print("Sample Query Data (first 5):")
    print("=" * 60)
    for i, item in enumerate(query_items[:5], 1):
        print(f"{i}. {item['search_name']} - {item['description']}")
        print(f"   Weight: {item['weight_g']}g, Confidence: {item['confidence']}")

    print("\n" + "=" * 60)
    print("Sample USDA Data (first 5):")
    print("=" * 60)
    for i, item in enumerate(usda_items[:5], 1):
        print(f"{i}. [{item['id']}] {item['display_name']}")
        print(f"   USDA Name: {item['usda_name']}")
        print(f"   Category: {item['category']}, Role: {item['role']}")


def main():
    """
    Main processing
    """
    print("=" * 60)
    print("Test Data Preparation Script")
    print("=" * 60)
    print()

    # Load data
    query_items = load_vlm_test_data()
    usda_items = load_usda_database()

    # Extract sample data
    sample_queries, sample_usda = extract_sample_data(
        query_items,
        usda_items,
        num_queries=20,  # 20 queries for testing
        num_usda=100     # 100 USDA items for testing
    )

    # Display data
    display_sample_data(sample_queries, sample_usda)

    # Save data
    output_dir = project_root / "tests" / "data"
    save_test_data(sample_queries, sample_usda, output_dir)

    print("\n" + "=" * 60)
    print("Test data preparation completed successfully!")
    print("=" * 60)

    return sample_queries, sample_usda


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)