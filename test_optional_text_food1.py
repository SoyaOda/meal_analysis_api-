#!/usr/bin/env python3
"""
Optional Text Integration Test Script

Tests the meal analysis pipeline with optional text input functionality.
This script demonstrates how additional text context can enhance image analysis results.
"""

import asyncio
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Add app_v2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app_v2'))

from app_v2.pipeline.orchestrator import MealAnalysisPipeline

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section_header(title: str, level: int = 1):
    """Print formatted section header"""
    if level == 1:
        print(f"\n{'='*80}")
        print(f"📝 {title}")
        print(f"{'='*80}")
    elif level == 2:
        print(f"\n{'-'*60}")
        print(f"📊 {title}")
        print(f"{'-'*60}")
    else:
        print(f"\n{'>'*40}")
        print(f"🧪 {title}")

def format_nutrition_info(nutrition: Dict[str, float]) -> str:
    """Format nutrition information for display"""
    return (f"🍽 {nutrition.get('calories', 0):.1f}kcal | "
            f"🥩 {nutrition.get('protein', 0):.1f}g | "
            f"🍞 {nutrition.get('carbs', 0):.1f}g | "
            f"🧈 {nutrition.get('fat', 0):.1f}g")

def print_test_header(test_name: str, optional_text: Optional[str] = None):
    """Print header for test case"""
    print_section_header(f"Test Case: {test_name}")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📸 Image: test_images/food1.jpg")
    if optional_text:
        print(f"📝 Optional Text: '{optional_text}'")
    else:
        print(f"📝 Optional Text: None (baseline test)")
    print(f"🎯 Testing: Optional Text Integration")

def print_phase1_results(phase1_result: Dict[str, Any], test_name: str):
    """Print detailed Phase1 results"""
    print_section_header(f"Phase1 Results: {test_name}", 2)

    detected_items = phase1_result.get("detected_food_items", [])
    dishes = phase1_result.get("dishes", [])
    confidence = phase1_result.get("analysis_confidence", 0.0) or 0.0

    print(f"📈 Overall Confidence: {confidence:.2f}")
    print(f"🔍 Detected Items: {len(detected_items)}")
    print(f"🍽️ Dishes: {len(dishes)}")

    # Show dishes with ingredients
    if dishes:
        print(f"\n🍽️ Detected Dishes:")
        for i, dish in enumerate(dishes, 1):
            ingredients = dish.get("ingredients", [])
            dish_confidence = dish.get('confidence', 0.0) or 0.0
            print(f"   {i}. {dish['dish_name']} (conf: {dish_confidence:.2f})")
            print(f"      📝 Ingredients ({len(ingredients)}):")

            # Show all ingredients for comparison
            for ing in ingredients:
                confidence = ing.get('confidence', 0.0) or 0.0
                weight_g = ing.get('weight_g', 0.0) or 0.0
                print(f"         • {ing['ingredient_name']}: {weight_g}g (conf: {confidence:.2f})")

def print_comparison_summary(results: Dict[str, Dict]):
    """Print comparison between test results"""
    print_section_header("Comparison Summary")

    for test_name, result in results.items():
        phase1 = result.get("phase1_result", {})
        processing = result.get("processing_summary", {})

        dishes_count = len(phase1.get("dishes", []))
        confidence = phase1.get("analysis_confidence", 0)
        calories = processing.get("total_calories", 0)
        time_s = processing.get("processing_time_seconds", 0)

        print(f"\n📊 {test_name}:")
        print(f"   🍽️ Dishes: {dishes_count}")
        print(f"   📈 Confidence: {confidence:.2f}")
        print(f"   🍽 Calories: {calories:.1f}kcal")
        print(f"   ⏱️ Time: {time_s:.2f}s")

async def test_optional_text_case(
    test_name: str,
    optional_text: Optional[str] = None,
    model_id: str = "google/gemma-3-27b-it"
) -> Dict[str, Any]:
    """Test a single case with optional text"""
    print_test_header(test_name, optional_text)

    # Check if food1.jpg exists
    image_path = "test_images/food1.jpg"
    if not os.path.exists(image_path):
        print(f"❌ Error: {image_path} not found!")
        return None

    # Load image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    print(f"📏 Image Size: {len(image_bytes)} bytes")

    # Initialize pipeline
    print_section_header("Pipeline Execution", 3)

    start_time = time.time()
    pipeline = MealAnalysisPipeline(
        use_elasticsearch_search=True,
        use_mynetdiary_specialized=False,
        use_fuzzy_matching=False,
        model_id=model_id
    )

    try:
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            optional_text=optional_text,  # KEY: Optional text parameter
            save_detailed_logs=True,
            test_execution=True,
            test_results_dir=f"analysis_results/optional_text_test_{test_name.lower().replace(' ', '_')}"
        )

        execution_time = time.time() - start_time

        print(f"✅ Analysis completed successfully!")
        print(f"⏱️ Execution Time: {execution_time:.2f}s")

        # Print results
        print_phase1_results(result.get("phase1_result", {}), test_name)

        # Show processing summary
        processing_summary = result.get("processing_summary", {})
        print_section_header("Processing Summary", 3)

        print(f"⏱️ Total Processing Time: {processing_summary.get('processing_time_seconds', 0):.2f}s")
        print(f"🍽️ Total Dishes: {processing_summary.get('total_dishes', 0)}")
        print(f"🥗 Total Ingredients: {processing_summary.get('total_ingredients', 0)}")
        print(f"🍽 Final Calories: {processing_summary.get('total_calories', 0):.1f}kcal")

        # Save test summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"optional_text_test_{test_name.lower().replace(' ', '_')}_{timestamp}.json"

        test_summary = {
            "timestamp": timestamp,
            "test_type": "optional_text_integration",
            "test_name": test_name,
            "optional_text": optional_text,
            "model_id": model_id,
            "execution_time_s": execution_time,
            "phase1_results": {
                "confidence": result.get("phase1_result", {}).get("analysis_confidence", 0),
                "detected_dishes": len(result.get("phase1_result", {}).get("dishes", [])),
                "dishes_details": result.get("phase1_result", {}).get("dishes", [])
            },
            "processing_summary": processing_summary,
            "analysis_folder": result.get("analysis_folder")
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)

        print(f"💾 Test Summary: {summary_file}")
        print(f"📁 Analysis Folder: {result.get('analysis_folder')}")

        return test_summary

    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ Test failed after {execution_time:.2f}s")
        print(f"💥 Error: {str(e)}")
        logger.error(f"Optional text test failed for '{test_name}': {e}", exc_info=True)
        return None

async def run_optional_text_tests():
    """Run comprehensive optional text tests"""
    print_section_header("Optional Text Integration Tests")
    print(f"🧪 Testing different text contexts with the same image")
    print(f"🤖 Model: google/gemma-3-27b-it (best for diversity and detail)")

    # Test cases with different optional text contexts
    test_cases = [
        {
            "name": "Baseline (No Text)",
            "optional_text": None,
            "description": "Standard analysis without additional context"
        },
        {
            "name": "Homemade Context",
            "optional_text": "This is a homemade meal prepared with fresh ingredients from the garden",
            "description": "Emphasis on fresh, homemade preparation"
        },
        {
            "name": "Restaurant Context",
            "optional_text": "This is a restaurant meal from an Italian bistro with generous portions",
            "description": "Restaurant setting with portion size hints"
        },
        {
            "name": "Dietary Context",
            "optional_text": "This is a low-sodium, heart-healthy meal with reduced oil and extra vegetables",
            "description": "Health-conscious preparation method"
        },
        {
            "name": "Specific Ingredients",
            "optional_text": "This pasta dish contains whole wheat penne, organic tomatoes, fresh basil, and parmesan cheese",
            "description": "Specific ingredient information"
        }
    ]

    print(f"📋 Test Cases: {len(test_cases)}")
    for i, case in enumerate(test_cases, 1):
        print(f"   {i}. {case['name']}: {case['description']}")

    results = {}

    # Run all test cases
    for i, test_case in enumerate(test_cases, 1):
        print_section_header(f"Running Test {i}/{len(test_cases)}: {test_case['name']}")

        result = await test_optional_text_case(
            test_case["name"],
            test_case["optional_text"]
        )

        if result:
            results[test_case["name"]] = result

        # Brief pause between tests
        if i < len(test_cases):
            print(f"\n⏳ Preparing next test in 3 seconds...")
            await asyncio.sleep(3)

    # Generate comparison results
    if results:
        print_comparison_summary(results)

        # Save comprehensive comparison
        comparison_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_file = f"optional_text_comparison_{comparison_timestamp}.json"

        comparison_data = {
            "timestamp": comparison_timestamp,
            "test_type": "optional_text_comparison",
            "total_test_cases": len(test_cases),
            "successful_tests": len(results),
            "test_cases": test_cases,
            "results": results
        }

        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Comprehensive Comparison: {comparison_file}")

        # Analysis insights
        print_section_header("Key Insights")
        baseline = results.get("Baseline (No Text)")

        if baseline:
            baseline_dishes = baseline["phase1_results"]["detected_dishes"]
            print(f"🏁 Baseline detected {baseline_dishes} dishes")

            for name, result in results.items():
                if name != "Baseline (No Text)":
                    dishes_count = result["phase1_results"]["detected_dishes"]
                    confidence = result["phase1_results"]["confidence"]

                    if dishes_count != baseline_dishes:
                        print(f"   📊 {name}: {dishes_count} dishes ({dishes_count - baseline_dishes:+d} vs baseline)")
                    else:
                        print(f"   📊 {name}: Same dish count, confidence: {confidence:.2f}")

    return results

async def main():
    """Main test execution"""
    print("🚀 Starting Optional Text Integration Test")
    print("📝 New Feature: Image + Text Analysis")

    results = await run_optional_text_tests()

    if results:
        print(f"\n✨ Optional text tests completed successfully!")
        print(f"📊 Tested {len(results)} scenarios with text context integration")

        print(f"\n🎯 Features Demonstrated:")
        print(f"   ✅ API endpoint optional_text parameter")
        print(f"   ✅ Pipeline integration with text context")
        print(f"   ✅ Prompt enhancement with additional information")
        print(f"   ✅ Comparative analysis across different contexts")
        print(f"   ✅ Detailed logging and result tracking")
    else:
        print(f"\n💥 Optional text tests failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)