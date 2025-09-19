#!/usr/bin/env python3
"""
Advanced Nutrition Search Performance Test

Tests the new AdvancedNutritionSearchComponent with various query counts
to verify speed and detailed results across all performance tiers.
"""

import asyncio
import time
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add app_v2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app_v2'))

from app_v2.components.advanced_nutrition_search_component import AdvancedNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

def print_header(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"🧪 {title}")
    print(f"{'='*80}")

def print_performance_summary(results: Dict[str, Any], query_count: int):
    """Print performance summary"""
    search_summary = results.search_summary
    strategy = search_summary.get("performance_strategy", "unknown")
    processing_time = search_summary.get("total_processing_time_ms", 0)
    search_time = search_summary.get("search_time_ms", 0)

    print(f"\n📊 Performance Summary:")
    print(f"   🎯 Strategy: {strategy}")
    print(f"   ⏱️ Total Time: {processing_time}ms")
    print(f"   🔍 Search Time: {search_time}ms")
    print(f"   📈 Queries: {query_count}")
    print(f"   ⚡ Avg per Query: {processing_time/query_count:.1f}ms")
    print(f"   ✅ Success Rate: {search_summary.get('match_rate_percent', 0):.1f}%")

def print_detailed_results(results: Dict[str, Any], max_results: int = 3):
    """Print detailed search results"""
    print(f"\n🔍 Detailed Results (showing top {max_results}):")

    matches = results.matches
    for i, (term, result_list) in enumerate(matches.items()):
        if i >= max_results:
            break

        print(f"\n   🍽️ Query: '{term}'")

        if isinstance(result_list, list):
            for j, match in enumerate(result_list[:2]):  # Show top 2 matches
                print(f"      {j+1}. {match.name}")
                print(f"         Score: {match.score:.2f}")
                print(f"         Method: {match.search_metadata.get('search_method', 'unknown')}")
                if match.search_metadata.get("alternative_names"):
                    alt_names = match.search_metadata["alternative_names"][:2]
                    print(f"         Alt Names: {alt_names}")
        else:
            print(f"      1. {result_list.name}")
            print(f"         Score: {result_list.score:.2f}")
            print(f"         Method: {result_list.search_metadata.get('search_method', 'unknown')}")

async def test_performance_tier(component: AdvancedNutritionSearchComponent,
                               test_terms: List[str],
                               tier_name: str) -> Dict[str, Any]:
    """Test specific performance tier"""
    print_header(f"{tier_name} Test ({len(test_terms)} queries)")

    # Create input
    nutrition_input = NutritionQueryInput(
        ingredient_names=test_terms[:len(test_terms)//2],  # Half as ingredients
        dish_names=test_terms[len(test_terms)//2:]         # Half as dishes
    )

    print(f"📝 Test Terms: {test_terms}")

    # Execute search
    start_time = time.time()
    try:
        result = await component.process(nutrition_input)
        end_time = time.time()

        execution_time = int((end_time - start_time) * 1000)

        print(f"⏱️ Execution Time: {execution_time}ms")
        print_performance_summary(result, len(test_terms))
        print_detailed_results(result)

        return {
            "tier_name": tier_name,
            "query_count": len(test_terms),
            "execution_time_ms": execution_time,
            "strategy": result.search_summary.get("performance_strategy", "unknown"),
            "success_rate": result.search_summary.get("match_rate_percent", 0),
            "results": result
        }

    except Exception as e:
        print(f"❌ Error in {tier_name}: {e}")
        return {
            "tier_name": tier_name,
            "query_count": len(test_terms),
            "error": str(e)
        }

async def run_comprehensive_performance_test():
    """Run comprehensive performance tests across all tiers"""
    print_header("Advanced Nutrition Search Performance Test Suite")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing all performance tiers with realistic food queries")

    # Initialize component
    component = AdvancedNutritionSearchComponent()

    # Define test cases for different performance tiers
    test_cases = [
        # Tier 1: Small (≤5 queries) - Parallel API
        {
            "name": "Small Query Set (Parallel API)",
            "terms": ["chickpeas", "tomato", "chicken breast", "brown rice"]
        },

        # Tier 2: Medium (6-15 queries) - Batched API
        {
            "name": "Medium Query Set (Batched API)",
            "terms": [
                "chickpeas", "garbanzo beans", "tomato", "tomatoes",
                "chicken breast", "brown rice", "white rice", "black beans",
                "kidney beans", "sweet potato"
            ]
        },

        # Tier 3: Large (16+ queries) - Direct Elasticsearch
        {
            "name": "Large Query Set (Elasticsearch Batch)",
            "terms": [
                "chickpeas", "garbanzo beans", "tomato", "tomatoes", "cherry tomatoes",
                "chicken breast", "chicken thigh", "ground chicken", "grilled chicken",
                "brown rice", "white rice", "jasmine rice", "basmati rice",
                "black beans", "kidney beans", "pinto beans", "navy beans",
                "sweet potato", "russet potato", "red potato", "fingerling potato",
                "spinach", "kale", "arugula", "lettuce"
            ]
        }
    ]

    # Run tests
    all_results = []

    for test_case in test_cases:
        result = await test_performance_tier(
            component,
            test_case["terms"],
            test_case["name"]
        )
        all_results.append(result)

        # Small delay between tests
        await asyncio.sleep(1)

    # Print overall summary
    print_header("Overall Performance Summary")

    for result in all_results:
        if "error" not in result:
            tier = result["tier_name"]
            count = result["query_count"]
            time_ms = result["execution_time_ms"]
            strategy = result["strategy"]
            success = result["success_rate"]
            avg_per_query = time_ms / count if count > 0 else 0

            print(f"\n🎯 {tier}:")
            print(f"   📊 Queries: {count}")
            print(f"   ⚡ Strategy: {strategy}")
            print(f"   ⏱️ Total Time: {time_ms}ms")
            print(f"   📈 Avg/Query: {avg_per_query:.1f}ms")
            print(f"   ✅ Success: {success:.1f}%")
        else:
            print(f"\n❌ {result['tier_name']}: {result['error']}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"advanced_nutrition_search_performance_{timestamp}.json"

    # Convert results for JSON serialization
    json_results = []
    for result in all_results:
        json_result = {k: v for k, v in result.items() if k != "results"}
        if "results" in result:
            # Add summary info only to keep file manageable
            json_result["result_summary"] = {
                "total_matches": len(result["results"].matches),
                "search_summary": result["results"].search_summary,
                "error_count": len(result["results"].errors) if result["results"].errors else 0
            }
        json_results.append(json_result)

    test_summary = {
        "timestamp": timestamp,
        "test_type": "advanced_nutrition_search_performance",
        "component": "AdvancedNutritionSearchComponent",
        "performance_tiers_tested": len(test_cases),
        "results": json_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_summary, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Detailed results saved: {output_file}")
    print(f"\n🎉 Performance test completed!")

    return test_summary

async def test_debug_logging():
    """Test debug logging capabilities"""
    print_header("Debug Logging Test")

    component = AdvancedNutritionSearchComponent()

    # Test with a few queries to see debug output
    test_terms = ["chickpeas", "garbanzo beans", "tomato"]

    nutrition_input = NutritionQueryInput(
        ingredient_names=["chickpeas"],
        dish_names=["garbanzo beans", "tomato"]
    )

    print("🔍 Testing debug logging with sample queries...")

    result = await component.process(nutrition_input)

    print(f"\n🧪 Debug Info Available:")
    print(f"   - Processing details logged for each phase")
    print(f"   - Search strategy selection reasoning")
    print(f"   - Individual query timing and results")
    print(f"   - Error handling and fallback strategies")

    return True

if __name__ == "__main__":
    print("🚀 Starting Advanced Nutrition Search Performance Tests")

    async def main():
        # Run comprehensive performance test
        await run_comprehensive_performance_test()

        # Test debug logging
        await test_debug_logging()

        print(f"\n✨ All tests completed successfully!")

    # Run the tests
    asyncio.run(main())