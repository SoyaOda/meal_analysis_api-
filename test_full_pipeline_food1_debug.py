#!/usr/bin/env python3
"""
Full Pipeline Test with food1.jpg - Comprehensive Debug Version

Tests the complete meal analysis pipeline with the new AdvancedNutritionSearchComponent
integrated, including detailed debug output for each phase timing and results.
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

def print_phase_timing(phase_name: str, timing_ms: int, details: str = ""):
    """Print phase timing information"""
    print(f"⏱️ {phase_name}: {timing_ms}ms {details}")

def print_phase1_results(phase1_result: Dict[str, Any]):
    """Print detailed Phase1 results"""
    print_section_header("Phase1: Image Analysis Results", 2)

    detected_items = phase1_result.get("detected_food_items", [])
    dishes = phase1_result.get("dishes", [])
    confidence = phase1_result.get("analysis_confidence", 0.0) or 0.0

    print(f"📈 Overall Confidence: {confidence:.2f}")
    print(f"🔍 Detected Items: {len(detected_items)}")
    print(f"🍽️ Dishes: {len(dishes)}")

    # Show detected food items (structured data)
    if detected_items:
        print(f"\n🎯 Structured Food Items:")
        for i, item in enumerate(detected_items[:5], 1):  # Show top 5
            attributes = item.get("attributes", [])
            attr_text = f" ({len(attributes)} attributes)" if attributes else ""
            brand = f" [Brand: {item['brand']}]" if item.get("brand") else ""
            confidence = item.get('confidence', 0.0) or 0.0
            print(f"   {i}. {item['item_name']} (conf: {confidence:.2f}){attr_text}{brand}")

            # Show top attributes
            for attr in attributes[:2]:
                attr_confidence = attr.get('confidence', 0.0) or 0.0
                print(f"      • {attr['type']}: {attr['value']} (conf: {attr_confidence:.2f})")

    # Show traditional dishes
    if dishes:
        print(f"\n🍽️ Traditional Dishes:")
        for i, dish in enumerate(dishes[:3], 1):  # Show top 3
            ingredients = dish.get("ingredients", [])
            dish_confidence = dish.get('confidence', 0.0) or 0.0
            print(f"   {i}. {dish['dish_name']} (conf: {dish_confidence:.2f})")
            print(f"      📝 Ingredients: {len(ingredients)}")

            # Show ingredients
            for ing in ingredients[:3]:  # Show top 3 ingredients
                confidence = ing.get('confidence', 0.0) or 0.0  # Handle None values
                weight_g = ing.get('weight_g', 0.0) or 0.0
                print(f"         • {ing['ingredient_name']}: {weight_g}g (conf: {confidence:.2f})")

def print_nutrition_search_results(search_result: Dict[str, Any]):
    """Print detailed nutrition search results"""
    print_section_header("Nutrition Search Results", 2)

    matches_count = search_result.get("matches_count", 0)
    match_rate = search_result.get("match_rate", 0)
    search_summary = search_result.get("search_summary", {})

    print(f"🎯 Search Method: {search_result.get('search_method', 'unknown')}")
    print(f"📊 Total Matches: {matches_count}")
    print(f"✅ Match Rate: {match_rate:.1%}")

    # Show search timing and performance
    if search_summary:
        print(f"\n⚡ Performance Details:")
        strategy = search_summary.get("performance_strategy", "unknown")
        total_time = search_summary.get("total_processing_time_ms", 0)
        search_time = search_summary.get("search_time_ms", 0)

        print(f"   🎯 Strategy Used: {strategy}")
        print(f"   ⏱️ Total Time: {total_time}ms")
        print(f"   🔍 Search Time: {search_time}ms")
        print(f"   📈 Alternative Name Support: {search_summary.get('alternative_name_support', False)}")

        # Query details
        total_searches = search_summary.get("total_searches", 0)
        successful_matches = search_summary.get("successful_matches", 0)
        avg_time = total_time / total_searches if total_searches > 0 else 0

        print(f"   📝 Queries Processed: {total_searches}")
        print(f"   ✅ Successful: {successful_matches}")
        print(f"   ⚡ Avg per Query: {avg_time:.1f}ms")

def print_nutrition_calculation_results(nutrition_result: Dict[str, Any]):
    """Print detailed nutrition calculation results"""
    print_section_header("Nutrition Calculation Results", 2)

    dishes = nutrition_result.get("dishes", [])
    total_nutrition = nutrition_result.get("total_nutrition", {})
    calc_summary = nutrition_result.get("calculation_summary", {})

    print(f"🍽️ Total Dishes: {len(dishes)}")
    print(f"📊 {format_nutrition_info(total_nutrition)}")

    # Show calculation summary
    if calc_summary:
        print(f"\n📋 Calculation Summary:")
        print(f"   🥗 Total Ingredients: {calc_summary.get('total_ingredients', 0)}")
        print(f"   ✅ Matched Ingredients: {calc_summary.get('matched_ingredients', 0)}")
        print(f"   ❓ Estimated Ingredients: {calc_summary.get('estimated_ingredients', 0)}")
        print(f"   🎯 Match Rate: {calc_summary.get('ingredient_match_rate', 0):.1%}")

    # Show top dishes with details
    print(f"\n🍽️ Dish Breakdown:")
    for i, dish in enumerate(dishes[:3], 1):  # Show top 3 dishes
        dish_nutrition = dish.get("total_nutrition", {})
        ingredients = dish.get("ingredients", [])

        print(f"   {i}. {dish['dish_name']} (conf: {dish['confidence']:.2f})")
        print(f"      📊 {format_nutrition_info(dish_nutrition)}")
        print(f"      🥗 Ingredients: {len(ingredients)}")

        # Show top ingredients with nutrition
        for ing in ingredients[:2]:  # Show top 2 ingredients per dish
            ing_nutrition = ing.get("calculated_nutrition", {})
            source_db = ing.get("source_db", "unknown")
            print(f"         • {ing['ingredient_name']}: {ing['weight_g']}g")
            print(f"           {format_nutrition_info(ing_nutrition)} [{source_db}]")

def print_processing_summary(processing_summary: Dict[str, Any]):
    """Print processing summary with timing details"""
    print_section_header("Processing Summary", 2)

    total_time = processing_summary.get("processing_time_seconds", 0)
    pipeline_status = processing_summary.get("pipeline_status", "unknown")
    search_method = processing_summary.get("search_method", "unknown")

    print(f"⏱️ Total Processing Time: {total_time:.2f}s")
    print(f"🎯 Pipeline Status: {pipeline_status}")
    print(f"🔍 Search Method: {search_method}")

    # Component breakdown
    print(f"\n📊 Component Results:")
    print(f"   🍽️ Total Dishes: {processing_summary.get('total_dishes', 0)}")
    print(f"   🥗 Total Ingredients: {processing_summary.get('total_ingredients', 0)}")
    print(f"   🎯 Search Match Rate: {processing_summary.get('nutrition_search_match_rate', 'N/A')}")
    print(f"   🍽 Final Calories: {processing_summary.get('total_calories', 0):.1f}kcal")

def print_metadata_info(metadata: Dict[str, Any]):
    """Print metadata and component information"""
    print_section_header("System Metadata", 3)

    pipeline_version = metadata.get("pipeline_version", "unknown")
    timestamp = metadata.get("timestamp", "unknown")
    components = metadata.get("components_used", [])
    search_method = metadata.get("nutrition_search_method", "unknown")

    print(f"📦 Pipeline Version: {pipeline_version}")
    print(f"🕐 Analysis Timestamp: {timestamp}")
    print(f"🔍 Nutrition Search Method: {search_method}")
    print(f"🧩 Components Used: {', '.join(components)}")

async def test_full_pipeline_with_food1():
    """Test the complete pipeline with food1.jpg"""
    print_section_header("Full Pipeline Test with food1.jpg")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing complete Qwen2.5VL-72B → Advanced Query System → Nutrition Calculation")

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

    # Initialize pipeline with debug settings
    print_section_header("Pipeline Initialization", 2)

    pipeline_start = time.time()
    pipeline = MealAnalysisPipeline(
        use_elasticsearch_search=True,
        use_mynetdiary_specialized=False,
        use_fuzzy_matching=False  # This will trigger AdvancedNutritionSearchComponent
    )

    pipeline_info = pipeline.get_pipeline_info()
    print(f"🆔 Pipeline ID: {pipeline_info['pipeline_id']}")
    print(f"📦 Pipeline Version: {pipeline_info['version']}")
    print(f"🔍 Nutrition Search Method: {pipeline_info['nutrition_search_method']}")

    # Show components
    components = pipeline_info.get('components', [])
    print(f"🧩 Components ({len(components)}):")
    for comp in components:
        print(f"   • {comp['component_name']} ({comp['component_type']})")

    # Execute complete analysis with detailed logging
    print_section_header("Executing Complete Analysis", 2)

    execution_start = time.time()

    try:
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            optional_text=None,
            save_detailed_logs=True,
            test_execution=True,
            test_results_dir="analysis_results/full_pipeline_test"
        )

        execution_time = time.time() - execution_start
        total_pipeline_time = time.time() - pipeline_start

        print(f"✅ Analysis completed successfully!")
        print_phase_timing("Execution Time", int(execution_time * 1000), "")
        print_phase_timing("Total Pipeline Time", int(total_pipeline_time * 1000), "(including initialization)")

        # Print detailed results for each phase
        print_phase1_results(result.get("phase1_result", {}))
        print_nutrition_search_results(result.get("nutrition_search_result", {}))
        print_nutrition_calculation_results(result.get("final_nutrition_result", {}))
        print_processing_summary(result.get("processing_summary", {}))
        print_metadata_info(result.get("metadata", {}))

        # Show saved analysis files
        analysis_folder = result.get("analysis_folder")
        saved_files = result.get("saved_files", {})

        if analysis_folder:
            print_section_header("Analysis Files Saved", 3)
            print(f"📁 Analysis Folder: {analysis_folder}")
            print(f"💾 Files Saved: {len(saved_files)}")

            for phase, files in saved_files.items():
                print(f"   📋 {phase}: {len(files)} files")
                for file_path in files[:2]:  # Show first 2 files per phase
                    file_name = os.path.basename(file_path)
                    print(f"      • {file_name}")

        # Save test summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"full_pipeline_test_food1_{timestamp}.json"

        test_summary = {
            "timestamp": timestamp,
            "test_type": "full_pipeline_with_advanced_nutrition_search",
            "image_file": image_path,
            "image_size_bytes": len(image_bytes),
            "execution_time_ms": int(execution_time * 1000),
            "total_pipeline_time_ms": int(total_pipeline_time * 1000),
            "pipeline_info": pipeline_info,
            "components_used": result.get("metadata", {}).get("components_used", []),
            "nutrition_search_performance": {
                "strategy": result.get("nutrition_search_result", {}).get("search_summary", {}).get("performance_strategy"),
                "total_processing_time_ms": result.get("nutrition_search_result", {}).get("search_summary", {}).get("total_processing_time_ms"),
                "search_time_ms": result.get("nutrition_search_result", {}).get("search_summary", {}).get("search_time_ms"),
                "queries_processed": result.get("nutrition_search_result", {}).get("search_summary", {}).get("total_searches"),
                "successful_matches": result.get("nutrition_search_result", {}).get("search_summary", {}).get("successful_matches")
            },
            "final_results": {
                "total_calories": result.get("processing_summary", {}).get("total_calories"),
                "total_dishes": result.get("processing_summary", {}).get("total_dishes"),
                "total_ingredients": result.get("processing_summary", {}).get("total_ingredients"),
                "match_rate": result.get("processing_summary", {}).get("nutrition_search_match_rate")
            },
            "analysis_folder": analysis_folder
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)

        print_section_header("Test Completed Successfully!", 1)
        print(f"💾 Test Summary: {summary_file}")
        print(f"📁 Full Analysis: {analysis_folder}")
        print(f"⚡ Total Time: {total_pipeline_time:.2f}s")

        # Performance highlights
        search_perf = test_summary["nutrition_search_performance"]
        if search_perf.get("strategy"):
            print(f"🎯 Search Strategy: {search_perf['strategy']}")
            print(f"⏱️ Search Performance: {search_perf.get('search_time_ms', 0)}ms for {search_perf.get('queries_processed', 0)} queries")

        return test_summary

    except Exception as e:
        execution_time = time.time() - execution_start
        print(f"❌ Pipeline execution failed after {execution_time:.2f}s")
        print(f"💥 Error: {str(e)}")

        # Log the full exception for debugging
        logger.error(f"Full pipeline test failed: {e}", exc_info=True)

        return None

async def main():
    """Main test execution"""
    print("🚀 Starting Full Pipeline Test with Advanced Nutrition Search")

    # Run the comprehensive test
    result = await test_full_pipeline_with_food1()

    if result:
        print(f"\n✨ Full pipeline test completed successfully!")
        print(f"📊 Performance Summary:")
        print(f"   ⏱️ Total Time: {result['total_pipeline_time_ms']}ms")

        nutrition_perf = result["nutrition_search_performance"]
        if nutrition_perf.get("strategy"):
            print(f"   🎯 Search Strategy: {nutrition_perf['strategy']}")
            queries = nutrition_perf.get("queries_processed", 0)
            search_time = nutrition_perf.get("search_time_ms", 0)
            if queries > 0:
                avg_per_query = search_time / queries
                print(f"   ⚡ Search Avg: {avg_per_query:.1f}ms per query ({queries} total)")

        final_results = result["final_results"]
        print(f"   🍽️ Final Results: {final_results.get('total_calories', 0):.1f}kcal")
        print(f"   📊 Success Rate: {final_results.get('match_rate', 'N/A')}")
    else:
        print(f"\n💥 Full pipeline test failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())