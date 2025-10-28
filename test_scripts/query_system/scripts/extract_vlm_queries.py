#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLMテスト結果から全クエリを抽出

vlm_test_results_*.jsonから全食材クエリを抽出してtest_queries.jsonを生成します。
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_queries_from_vlm_results(vlm_result_file: str):
    """
    VLMテスト結果ファイルから全クエリを抽出

    Args:
        vlm_result_file: VLMテスト結果JSONファイルのパス
    """
    print("=" * 80)
    print("Extract Queries from VLM Test Results")
    print("=" * 80)
    print(f"\nLoading VLM results from: {vlm_result_file}")

    with open(vlm_result_file, 'r', encoding='utf-8') as f:
        vlm_data = json.load(f)

    metadata = vlm_data.get("test_metadata", {})
    results = vlm_data.get("results", [])

    print(f"✅ Loaded {len(results)} image results")
    print(f"   Model: {metadata.get('model_id', 'Unknown')}")
    print(f"   Prompt Type: {metadata.get('prompt_type', 'Unknown')}")
    print(f"   Total Images: {metadata.get('total_images', 0)}")

    # Extract all food items from all images
    all_queries = []

    for result in results:
        if not result.get("success", False):
            continue

        image_file = result.get("image_file", "unknown.jpg")
        vlm_response = result.get("vlm_response", {})
        dishes = vlm_response.get("dishes", [])

        for dish_idx, dish in enumerate(dishes):
            # Extract main_food
            main_food = dish.get("main_food")
            if main_food:
                query = {
                    "search_name": main_food.get("search_name", ""),
                    "description": main_food.get("description", ""),
                    "weight_g": main_food.get("weight_g", 0),
                    "confidence": main_food.get("confidence", 0.0),
                    "image_file": image_file,
                    "dish_index": dish_idx,
                    "food_type": "main_food"
                }
                all_queries.append(query)

            # Extract extras
            extras = dish.get("extras", [])
            for extra_idx, extra in enumerate(extras):
                query = {
                    "search_name": extra.get("search_name", ""),
                    "description": extra.get("description", ""),
                    "weight_g": extra.get("weight_g", 0),
                    "confidence": extra.get("confidence", 0.0),
                    "image_file": image_file,
                    "dish_index": dish_idx,
                    "extra_index": extra_idx,
                    "food_type": "extra"
                }
                all_queries.append(query)

    print(f"\n✅ Extracted {len(all_queries)} food items from {len(results)} images")

    # Statistics
    print("\n" + "=" * 80)
    print("Statistics")
    print("=" * 80)

    main_food_count = sum(1 for q in all_queries if q["food_type"] == "main_food")
    extra_count = sum(1 for q in all_queries if q["food_type"] == "extra")

    print(f"\nFood Types:")
    print(f"  Main Foods: {main_food_count}")
    print(f"  Extras: {extra_count}")
    print(f"  Total: {len(all_queries)}")

    # Count by image
    image_counts = {}
    for q in all_queries:
        img = q["image_file"]
        image_counts[img] = image_counts.get(img, 0) + 1

    print(f"\nQueries per image:")
    print(f"  Min: {min(image_counts.values())}")
    print(f"  Max: {max(image_counts.values())}")
    print(f"  Average: {sum(image_counts.values()) / len(image_counts):.1f}")

    # Save to file
    output_file = project_root / "tests" / "data" / "test_queries.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n💾 Saving {len(all_queries)} queries to: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_queries, f, indent=2, ensure_ascii=False)

    print("✅ Successfully generated test_queries.json")

    # Sample queries
    print("\n" + "=" * 80)
    print("Sample Queries (first 10)")
    print("=" * 80)

    for i, query in enumerate(all_queries[:10], 1):
        print(f"\n{i}. {query['search_name']} | {query['description']}")
        print(f"   Weight: {query['weight_g']}g, Confidence: {query['confidence']}")
        print(f"   Image: {query['image_file']}, Type: {query['food_type']}")

    # File size
    file_size_kb = output_file.stat().st_size / 1024
    print(f"\n📊 Output file size: {file_size_kb:.2f} KB")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Default VLM result file
    vlm_result_file = "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json"

    # Allow custom file via command line
    if len(sys.argv) > 1:
        vlm_result_file = sys.argv[1]

    try:
        extract_queries_from_vlm_results(vlm_result_file)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
