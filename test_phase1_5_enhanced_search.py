#!/usr/bin/env python3
"""
Phase1.5 Enhanced Search Test

Phase1.5（代替クエリ生成）を統合した拡張検索機能のテストスクリプト
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

# 既存のapp.pyと同じ環境変数設定を使用
os.environ.setdefault("USDA_API_KEY", "vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api_2/service-account-key.json")
os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
os.environ.setdefault("GEMINI_LOCATION", "us-central1")
os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")

from app_v2.components.enhanced_nutrition_search_component import EnhancedNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

async def test_phase15_enhanced_search():
    """Phase1.5統合拡張検索のテスト"""
    
    print("🧪 Testing Phase1.5 Enhanced Search System")
    print("=" * 60)
    
    # テストケース：exact matchが期待できないクエリを含む
    test_cases = [
        {
            "name": "Niche Ingredients Test",
            "dish_names": ["Quinoa salad"],
            "ingredient_names": ["broccolini", "microgreens", "purple carrots"],
            "image_path": "test_images/food1.jpg"  # 実際の画像パスに置き換え
        },
        {
            "name": "Mixed Match Test", 
            "dish_names": ["Grilled chicken", "Exotic vegetable medley"],
            "ingredient_names": ["chicken breast", "baby kale", "sprouted alfalfa"],
            "image_path": "test_images/food2.jpg"
        },
        {
            "name": "Common Foods Test",
            "dish_names": ["Rice bowl"],
            "ingredient_names": ["white rice", "chicken", "broccoli"],
            "image_path": "test_images/food3.jpg"
        }
    ]
    
    # 拡張検索コンポーネントを初期化
    enhanced_component = EnhancedNutritionSearchComponent(
        enable_phase15=True,
        max_phase15_iterations=3,  # 最大3回まで試行
        debug=True
    )
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # 検索入力を作成
            search_input = NutritionQueryInput(
                dish_names=test_case["dish_names"],
                ingredient_names=test_case["ingredient_names"],
                preferred_source="elasticsearch"
            )
            
            # 画像パスを追加（Phase1.5で使用）
            search_input.image_path = test_case["image_path"]
            
            print(f"📝 Input:")
            print(f"   Dishes: {test_case['dish_names']}")
            print(f"   Ingredients: {test_case['ingredient_names']}")
            print(f"   Image: {test_case['image_path']}")
            
            # 拡張検索実行
            start_time = datetime.now()
            result = await enhanced_component.process(search_input)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # 結果分析
            print(f"\n📊 Results Summary:")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Original queries: {result.processing_summary['original_queries_count']}")
            print(f"   Phase1.5 iterations: {result.processing_summary['total_phase15_iterations']}")
            print(f"   Max iterations reached: {'✅' if result.processing_summary['max_iterations_reached'] else '❌'}")
            print(f"   Convergence achieved: {'✅' if result.processing_summary['convergence_achieved'] else '❌'}")
            print(f"   Final exact matches: {result.processing_summary['final_exact_matches_count']}")
            print(f"   Exact match rate: {result.processing_summary['exact_match_rate']:.1%}")
            print(f"   All exact matches: {'✅' if result.all_exact_matches else '❌'}")
            
            # Phase1.5の詳細（全イテレーション）
            if result.phase15_metadata and result.phase15_metadata.get('iteration_history'):
                print(f"\n🔄 Phase1.5 Iteration History:")
                for iteration_data in result.phase15_metadata['iteration_history']:
                    iteration_num = iteration_data.get('iteration', 'Unknown')
                    print(f"\n   Iteration {iteration_num}:")
                    
                    # 失敗したクエリ
                    no_match_items = iteration_data.get('no_match_items', [])
                    if no_match_items:
                        print(f"      Failed queries: {[item['original_query'] for item in no_match_items]}")
                    
                    # 代替クエリ
                    alt_queries = iteration_data.get('alternative_queries', [])
                    if alt_queries:
                        print(f"      Alternative queries generated: {len(alt_queries)}")
                        for alt_query in alt_queries[:3]:  # 最初の3つだけ表示
                            print(f"         '{alt_query['original_query']}' → '{alt_query['alternative_query']}' ({alt_query['strategy']})")
                        if len(alt_queries) > 3:
                            print(f"         ... and {len(alt_queries) - 3} more")
                    
                    # 生成された代替クエリ数
                    total_generated = iteration_data.get('total_alternatives_generated', 0)
                    if total_generated:
                        print(f"      Total alternatives generated: {total_generated}")
            
            # 最終結果の詳細
            if result.final_consolidated_results:
                print(f"\n🎯 Final Consolidated Results:")
                for query, final_result in result.final_consolidated_results.items():
                    match = final_result["match"]
                    source = final_result["source"]
                    print(f"   '{query}' → '{match.search_name}' (score: {match.score:.2f})")
                    print(f"      Source: {source}")
                    if source == "alternative_search":
                        print(f"      Alternative query: '{final_result['alternative_query']}'")
                        print(f"      Strategy: {final_result['strategy']}")
                    print(f"      Exact match: {'✅' if final_result['is_exact_match'] else '❌'}")
                    print()
            
            # テスト結果を保存
            test_result = {
                "test_case": test_case["name"],
                "input": {
                    "dishes": test_case["dish_names"],
                    "ingredients": test_case["ingredient_names"]
                },
                "processing_time": processing_time,
                "summary": result.processing_summary,
                "all_exact_matches": result.all_exact_matches,
                "phase15_iterations": result.processing_summary['total_phase15_iterations'],
                "convergence_achieved": result.processing_summary['convergence_achieved'],
                "final_matches_count": len(result.final_consolidated_results)
            }
            
            results.append(test_result)
            
        except Exception as e:
            print(f"❌ Error in test case {i}: {e}")
            results.append({
                "test_case": test_case["name"],
                "error": str(e),
                "processing_time": 0.0
            })
    
    # 全体サマリー
    print(f"\n📈 Overall Test Summary")
    print("=" * 60)
    
    successful_tests = [r for r in results if "error" not in r]
    total_tests = len(results)
    
    print(f"Tests completed: {len(successful_tests)}/{total_tests}")
    
    if successful_tests:
        avg_processing_time = sum(r["processing_time"] for r in successful_tests) / len(successful_tests)
        all_exact_matches_count = sum(1 for r in successful_tests if r.get("all_exact_matches", False))
        
        print(f"Average processing time: {avg_processing_time:.2f}s")
        print(f"Tests achieving 100% exact match: {all_exact_matches_count}/{len(successful_tests)}")
        print(f"Phase1.5 success rate: {all_exact_matches_count/len(successful_tests):.1%}")
        
        # 詳細統計
        total_original_queries = sum(r["summary"]["original_queries_count"] for r in successful_tests)
        total_iterations = sum(r["summary"]["total_phase15_iterations"] for r in successful_tests)
        convergence_achieved_count = sum(1 for r in successful_tests if r["summary"]["convergence_achieved"])
        total_final_matches = sum(r["summary"]["final_exact_matches_count"] for r in successful_tests)
        
        print(f"\nDetailed Statistics:")
        print(f"  Total original queries: {total_original_queries}")
        print(f"  Total Phase1.5 iterations: {total_iterations}")
        print(f"  Average iterations per test: {total_iterations/len(successful_tests):.1f}")
        print(f"  Tests achieving convergence: {convergence_achieved_count}/{len(successful_tests)}")
        print(f"  Total final exact matches: {total_final_matches}")
        
        if total_original_queries > 0:
            overall_exact_match_rate = total_final_matches / total_original_queries
            print(f"  Overall exact match rate: {overall_exact_match_rate:.1%}")
            print(f"  Convergence success rate: {convergence_achieved_count/len(successful_tests):.1%}")
    
    # 結果をJSONファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"phase15_test_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": len(successful_tests),
                "average_processing_time": avg_processing_time if successful_tests else 0,
                "phase15_success_rate": all_exact_matches_count/len(successful_tests) if successful_tests else 0
            },
            "detailed_results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n🎉 Phase1.5 Enhanced Search Test Completed!")

async def test_phase15_component_only():
    """Phase1.5コンポーネント単体のテスト"""
    
    print("\n🔧 Testing Phase1.5 Component Only")
    print("-" * 40)
    
    from app_v2.components.phase1_5_component import Phase1_5Component
    from app_v2.models.phase1_5_models import Phase1_5Input, NoMatchItem
    
    # Phase1.5コンポーネントを初期化
    phase15_component = Phase1_5Component()
    
    # テストデータ
    no_match_items = [
        NoMatchItem(
            original_query="broccolini",
            item_type="ingredient",
            confidence=0.9,
            search_results_count=3,
            best_match_score=15.2,
            best_match_name="Broccoli, raw"
        ),
        NoMatchItem(
            original_query="microgreens",
            item_type="ingredient", 
            confidence=0.8,
            search_results_count=1,
            best_match_score=8.5,
            best_match_name="Mixed greens"
        )
    ]
    
    phase1_result = {
        "dishes": [
            {
                "dish_name": "Quinoa salad",
                "confidence": 0.9,
                "ingredients": [
                    {"ingredient_name": "broccolini", "confidence": 0.9},
                    {"ingredient_name": "microgreens", "confidence": 0.8}
                ]
            }
        ]
    }
    
    search_context = {
        "databases_searched": ["elasticsearch"],
        "search_stats": {
            "total_queries": 3,
            "successful_matches": 1,
            "failed_searches": 2
        }
    }
    
    # 画像データを読み込み
    with open("test_images/food1.jpg", "rb") as f:
        image_bytes = f.read()
    
    # Phase1.5入力を作成
    phase15_input = Phase1_5Input(
        image_bytes=image_bytes,
        image_mime_type="image/jpeg",
        phase1_result=phase1_result,
        failed_queries=["broccolini", "microgreens"],
        failure_history=[],
        iteration=1
    )
    
    try:
        # Phase1.5実行
        result = await phase15_component.process(phase15_input)
        
        print(f"✅ Phase1.5 component test successful!")
        print(f"   Alternatives generated: {len(result.alternative_queries)}")
        print(f"   Iteration: {result.iteration}")
        print(f"   Total alternatives: {result.total_alternatives_generated}")
        
        for alt_query in result.alternative_queries:
            print(f"   '{alt_query.original_query}' → '{alt_query.alternative_query}' ({alt_query.strategy})")
        
    except Exception as e:
        print(f"❌ Phase1.5 component test failed: {e}")

if __name__ == "__main__":
    # メイン拡張検索テスト
    asyncio.run(test_phase15_enhanced_search())
    
    # Phase1.5コンポーネント単体テスト
    asyncio.run(test_phase15_component_only()) 