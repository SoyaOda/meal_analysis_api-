#!/usr/bin/env python3
"""
Test Full Pipeline with Google Gemma-3-27B-IT Model

Tests the complete meal analysis pipeline using the Gemma-3-27B model instead of Qwen.
This script tests the model change to evaluate differences in image analysis performance.
"""

import asyncio
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any
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
        print(f"🔬 {title}")
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

def print_model_comparison_header():
    """Print header for model comparison"""
    print_section_header("Google Gemma-3-27B-IT vs Qwen2.5VL-32B Comparison Test")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 Model Change: Qwen/Qwen2.5-VL-32B-Instruct → google/gemma-3-27b-it")
    print(f"🎯 Testing: Image Analysis Performance Comparison")

def print_phase1_results(phase1_result: Dict[str, Any], model_name: str):
    """Print detailed Phase1 results with model info"""
    print_section_header(f"Phase1: {model_name} Image Analysis Results", 2)

    detected_items = phase1_result.get("detected_food_items", [])
    dishes = phase1_result.get("dishes", [])
    confidence = phase1_result.get("analysis_confidence", 0.0) or 0.0

    print(f"🤖 Model: {model_name}")
    print(f"📈 Overall Confidence: {confidence:.2f}")
    print(f"🔍 Detected Items: {len(detected_items)}")
    print(f"🍽️ Dishes: {len(dishes)}")

    # Show traditional dishes
    if dishes:
        print(f"\n🍽️ Detected Dishes:")
        for i, dish in enumerate(dishes[:3], 1):  # Show top 3
            ingredients = dish.get("ingredients", [])
            dish_confidence = dish.get('confidence', 0.0) or 0.0
            print(f"   {i}. {dish['dish_name']} (conf: {dish_confidence:.2f})")
            print(f"      📝 Ingredients: {len(ingredients)}")

            # Show ingredients
            for ing in ingredients[:3]:  # Show top 3 ingredients
                confidence = ing.get('confidence', 0.0) or 0.0
                weight_g = ing.get('weight_g', 0.0) or 0.0
                print(f"         • {ing['ingredient_name']}: {weight_g}g (conf: {confidence:.2f})")

def print_nutrition_search_results(search_result: Dict[str, Any]):
    """Print nutrition search performance"""
    print_section_header("Advanced Nutrition Search Results", 2)

    matches_count = search_result.get("matches_count", 0)
    match_rate = search_result.get("match_rate", 0)
    search_summary = search_result.get("search_summary", {})

    print(f"🎯 Search Method: {search_result.get('search_method', 'unknown')}")
    print(f"📊 Total Matches: {matches_count}")
    print(f"✅ Match Rate: {match_rate:.1%}")

    # Show search performance
    if search_summary:
        strategy = search_summary.get("performance_strategy", "unknown")
        total_time = search_summary.get("total_processing_time_ms", 0)
        queries = search_summary.get("total_searches", 0)

        print(f"   🎯 Strategy Used: {strategy}")
        print(f"   ⏱️ Total Time: {total_time}ms")
        print(f"   📝 Queries: {queries}")
        if queries > 0:
            avg_time = total_time / queries
            print(f"   ⚡ Avg per Query: {avg_time:.1f}ms")

def print_final_results(nutrition_result: Dict[str, Any]):
    """Print final nutrition calculation results"""
    print_section_header("Final Nutrition Results", 2)

    dishes = nutrition_result.get("dishes", [])
    total_nutrition = nutrition_result.get("total_nutrition", {})
    calc_summary = nutrition_result.get("calculation_summary", {})

    print(f"🍽️ Total Dishes: {len(dishes)}")
    print(f"📊 {format_nutrition_info(total_nutrition)}")

    if calc_summary:
        print(f"\n📋 Calculation Summary:")
        print(f"   🥗 Total Ingredients: {calc_summary.get('total_ingredients', 0)}")
        print(f"   🎯 Match Rate: {calc_summary.get('ingredient_match_rate', 0):.1%}")

async def test_gemma3_model():
    """Test the complete pipeline with Gemma-3-27B model"""
    print_model_comparison_header()

    # Check if food1.jpg exists
    image_path = "test_images/food1.jpg"
    if not os.path.exists(image_path):
        print(f"❌ Error: {image_path} not found!")
        return None

    print(f"📸 Image: {image_path}")

    # Load image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    print(f"📏 Image Size: {len(image_bytes)} bytes")

    # Initialize pipeline
    print_section_header("Pipeline Initialization", 2)

    pipeline_start = time.time()
    pipeline = MealAnalysisPipeline(
        use_elasticsearch_search=True,
        use_mynetdiary_specialized=False,
        use_fuzzy_matching=False  # This will trigger AdvancedNutritionSearchComponent
    )

    pipeline_info = pipeline.get_pipeline_info()
    print(f"🆔 Pipeline ID: {pipeline_info['pipeline_id']}")
    print(f"🤖 Expected Model: google/gemma-3-27b-it")

    # Execute complete analysis
    print_section_header("Executing Analysis with Gemma-3-27B", 2)

    execution_start = time.time()

    try:
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            optional_text=None,
            save_detailed_logs=True,
            test_execution=True,
            test_results_dir="analysis_results/gemma3_test"
        )

        execution_time = time.time() - execution_start
        total_pipeline_time = time.time() - pipeline_start

        print(f"✅ Analysis completed successfully!")
        print(f"⏱️ Execution Time: {execution_time:.2f}s")
        print(f"⏱️ Total Pipeline Time: {total_pipeline_time:.2f}s")

        # Print detailed results for each phase
        print_phase1_results(result.get("phase1_result", {}), "google/gemma-3-27b-it")
        print_nutrition_search_results(result.get("nutrition_search_result", {}))
        print_final_results(result.get("final_nutrition_result", {}))

        # Show processing summary
        processing_summary = result.get("processing_summary", {})
        print_section_header("Processing Summary", 2)

        total_time = processing_summary.get("processing_time_seconds", 0)
        print(f"⏱️ Total Processing Time: {total_time:.2f}s")
        print(f"🍽️ Total Dishes: {processing_summary.get('total_dishes', 0)}")
        print(f"🥗 Total Ingredients: {processing_summary.get('total_ingredients', 0)}")
        print(f"🎯 Search Match Rate: {processing_summary.get('nutrition_search_match_rate', 'N/A')}")
        print(f"🍽 Final Calories: {processing_summary.get('total_calories', 0):.1f}kcal")

        # Save test summary for comparison
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"gemma3_test_food1_{timestamp}.json"

        # Show analysis folder
        analysis_folder = result.get("analysis_folder")
        if analysis_folder:
            print_section_header("Analysis Files Saved", 3)
            print(f"📁 Analysis Folder: {analysis_folder}")

        test_summary = {
            "timestamp": timestamp,
            "test_type": "gemma3_model_comparison",
            "model": "google/gemma-3-27b-it",
            "image_file": image_path,
            "image_size_bytes": len(image_bytes),
            "execution_time_s": execution_time,
            "total_pipeline_time_s": total_pipeline_time,
            "pipeline_info": pipeline_info,
            "phase1_results": {
                "model_used": "google/gemma-3-27b-it",
                "confidence": result.get("phase1_result", {}).get("analysis_confidence", 0),
                "detected_dishes": len(result.get("phase1_result", {}).get("dishes", [])),
                "detected_items": len(result.get("phase1_result", {}).get("detected_food_items", []))
            },
            "nutrition_search_performance": {
                "strategy": result.get("nutrition_search_result", {}).get("search_summary", {}).get("performance_strategy"),
                "total_processing_time_ms": result.get("nutrition_search_result", {}).get("search_summary", {}).get("total_processing_time_ms"),
                "queries_processed": result.get("nutrition_search_result", {}).get("search_summary", {}).get("total_searches"),
                "success_rate": result.get("nutrition_search_result", {}).get("match_rate", 0)
            },
            "final_results": {
                "total_calories": result.get("processing_summary", {}).get("total_calories"),
                "total_dishes": result.get("processing_summary", {}).get("total_dishes"),
                "total_ingredients": result.get("processing_summary", {}).get("total_ingredients")
            },
            "analysis_folder": analysis_folder
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)

        print_section_header("Gemma-3-27B Test Completed!", 1)
        print(f"💾 Test Summary: {summary_file}")
        print(f"📁 Full Analysis: {analysis_folder}")
        print(f"⚡ Total Time: {total_pipeline_time:.2f}s")

        # Performance highlights
        phase1_results = test_summary["phase1_results"]
        search_perf = test_summary["nutrition_search_performance"]

        print(f"\n🎯 Model Performance:")
        print(f"   🤖 Model: {phase1_results['model_used']}")
        print(f"   📈 Confidence: {phase1_results['confidence']:.2f}")
        print(f"   🍽️ Dishes Detected: {phase1_results['detected_dishes']}")

        if search_perf.get("strategy"):
            print(f"   ⚡ Search: {search_perf.get('queries_processed', 0)} queries in {search_perf.get('total_processing_time_ms', 0)}ms")

        return test_summary

    except Exception as e:
        execution_time = time.time() - execution_start
        print(f"❌ Pipeline execution failed after {execution_time:.2f}s")
        print(f"💥 Error: {str(e)}")

        # Log the full exception for debugging
        logger.error(f"Gemma-3-27B test failed: {e}", exc_info=True)

        return None

async def main():
    """Main test execution"""
    print("🚀 Starting Gemma-3-27B Model Test")
    print("🔄 Model Change: Qwen → Gemma-3-27B-IT")

    # Run the test
    result = await test_gemma3_model()

    if result:
        print(f"\n✨ Gemma-3-27B test completed successfully!")

        # Performance comparison summary
        phase1_perf = result["phase1_results"]
        final_perf = result["final_results"]

        print(f"\n📊 Quick Comparison Summary:")
        print(f"   🤖 Model: google/gemma-3-27b-it")
        print(f"   ⏱️ Time: {result['total_pipeline_time_s']:.2f}s")
        print(f"   📈 Confidence: {phase1_perf['confidence']:.2f}")
        print(f"   🍽️ Results: {final_perf.get('total_calories', 0):.1f}kcal")
        print(f"   🎯 Dishes: {final_perf.get('total_dishes', 0)}")
    else:
        print(f"\n💥 Gemma-3-27B test failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())