#!/usr/bin/env python3
"""
Phase1.5 Integration Test with Real Images

test_advanced_elasticsearch_search.pyをベースにしたPhase1.5統合テスト
テスト用プロンプトを使用して意図的にデータベースにない食品名を生成し、
Phase1.5の代替クエリ生成機能をテストする
"""

import os
import requests
import json
import time
import glob
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# 環境変数の設定（サーバーと同じ設定）
os.environ.setdefault("USDA_API_KEY", "vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api_2/service-account-key.json")
os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
os.environ.setdefault("GEMINI_LOCATION", "us-central1")
os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")

# Enhanced Nutrition Search Component
from app_v2.components.enhanced_nutrition_search_component import EnhancedNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput
from app_v2.pipeline.orchestrator import MealAnalysisPipeline

# API設定
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス（food1とfood2のみ）
test_images_dir = "test_images"
image_files = [
    os.path.join(test_images_dir, "food1.jpg"),
    os.path.join(test_images_dir, "food2.jpg")
]

async def test_single_image_phase1_5_integration(image_path: str, main_results_dir: str) -> Optional[Dict[str, Any]]:
    """単一画像でPhase1.5統合テストを実行"""
    
    print(f"\n{'='*60}")
    print(f"🖼️  Testing Phase1.5 integration with image: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    try:
        # Phase1.5テスト用パイプラインを初期化
        print("🔧 Initializing test pipeline with Phase1.5 test prompts...")
        test_pipeline = MealAnalysisPipeline(
            use_elasticsearch_search=True,
            use_test_prompts=True  # テスト用プロンプトを使用
        )
        
        # 画像を読み込み
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        print("📊 Step 1: Running Phase1 with test prompts (creative naming)...")
        start_time = time.time()
        
        # Phase1.5テスト用の完全分析を実行
        result = await test_pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            save_results=True,
            test_execution=True,
            test_results_dir=main_results_dir
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Complete analysis completed in {processing_time:.2f}s")
        
        analysis_id = result.get("analysis_id")
        print(f"Analysis ID: {analysis_id}")
        
        # Phase1結果から検索クエリを抽出
        phase1_result = result.get("phase1_result", {})
        dishes = phase1_result.get("dishes", [])
        
        all_queries = []
        dish_names = []
        ingredient_names = []
        
        for dish in dishes:
            dish_name = dish.get("dish_name")
            if dish_name:
                dish_names.append(dish_name)
                all_queries.append(dish_name)
            
            ingredients = dish.get("ingredients", [])
            for ingredient in ingredients:
                ingredient_name = ingredient.get("ingredient_name")
                if ingredient_name:
                    ingredient_names.append(ingredient_name)
                    all_queries.append(ingredient_name)
        
        # 重複を除去
        all_queries = list(set(all_queries))
        dish_names = list(set(dish_names))
        ingredient_names = list(set(ingredient_names))
        
        print(f"\n📊 Extracted Creative Queries from Phase1 (Test Prompts):")
        print(f"- Total dishes: {len(dish_names)}")
        print(f"- Total ingredients: {len(ingredient_names)}")
        print(f"- Total unique queries: {len(all_queries)}")
        
        # 生成されたクリエイティブなクエリを表示
        print(f"\n🎨 Creative Food Names Generated:")
        for i, query in enumerate(all_queries[:10], 1):  # 最初の10個を表示
            print(f"   {i}. '{query}'")
        if len(all_queries) > 10:
            print(f"   ... and {len(all_queries) - 10} more")
        
        if len(all_queries) == 0:
            print("❌ No search queries extracted from Phase1 results!")
            return None
        
        # EnhancedNutritionSearchComponentでPhase1.5統合テストを実行
        print(f"\n🔍 Step 2: Testing Enhanced Search with Phase1.5 integration...")
        enhanced_component = EnhancedNutritionSearchComponent(
            enable_phase15=True,
            max_phase15_iterations=3,
            debug=True
        )
        
        # ログレベルを設定してデバッグ情報を表示
        import logging
        logging.basicConfig(level=logging.INFO)
        enhanced_component.logger.setLevel(logging.DEBUG)
        
        # Phase1.5で使用する画像データを設定
        enhanced_component.set_image_data(image_bytes, "image/jpeg")
        
        # 検索入力データを作成
        nutrition_query_input = NutritionQueryInput(
            ingredient_names=ingredient_names,
            dish_names=dish_names,
            preferred_source="elasticsearch"
        )
        
        print(f"📝 Enhanced Search Input:")
        print(f"- Ingredient names: {len(ingredient_names)} items")
        print(f"- Dish names: {len(dish_names)} items")
        print(f"- Total search terms: {len(nutrition_query_input.get_all_search_terms())}")
        
        # Enhanced Search with Phase1.5を実行
        print(f"\n🚀 Starting Enhanced Search with Phase1.5...")
        search_start_time = time.time()
        
        enhanced_result = await enhanced_component.process(nutrition_query_input)
        
        search_end_time = time.time()
        search_time = search_end_time - search_start_time
        
        print(f"✅ Enhanced Search with Phase1.5 completed in {search_time:.3f}s")
        
        # Phase1.5統合結果の分析
        print(f"\n📈 Phase1.5 Integration Results:")
        print(f"   - Total iterations: {getattr(enhanced_result, 'total_iterations', 0)}")
        print(f"   - Phase1.5 executions: {len(getattr(enhanced_result, 'phase15_history', []))}")
        print(f"   - Processing time: {getattr(enhanced_result, 'processing_time', 0):.2f}s")
        
        # Phase1.5履歴の詳細表示
        phase15_history = getattr(enhanced_result, 'phase15_history', [])
        if phase15_history:
            print(f"\n🔄 Phase1.5 Execution History:")
            for i, history_item in enumerate(phase15_history, 1):
                print(f"   Iteration {i}:")
                print(f"     - No match items: {len(history_item.get('no_match_items', []))}")
                print(f"     - Alternative queries generated: {len(history_item.get('alternative_queries', []))}")
                print(f"     - Total alternatives: {history_item.get('total_alternatives_generated', 0)}")
                
                # 代替クエリの例を表示
                alt_queries = history_item.get('alternative_queries', [])
                if alt_queries:
                    print(f"     - Example alternatives:")
                    for alt in alt_queries[:3]:  # 最初の3つだけ表示
                        original = alt.get('original_query', 'N/A')
                        alternatives = alt.get('alternatives', [])
                        if alternatives:
                            print(f"       '{original}' → {alternatives[:2]}")
        else:
            print(f"\n⚠️  No Phase1.5 executions recorded")
            print(f"   - This may indicate all creative queries had exact matches")
            print(f"   - Or Phase1.5 system may not have been triggered")
        
        # 最終的なマッチ率
        final_matches = getattr(enhanced_result, 'final_results', {})
        if final_matches:
            total_queries = len(all_queries)
            successful_matches = sum(1 for matches in final_matches.values() if matches)
            match_rate = (successful_matches / total_queries) * 100 if total_queries > 0 else 0
            
            print(f"\n📊 Final Results:")
            print(f"   - Total creative queries: {total_queries}")
            print(f"   - Successful matches: {successful_matches}")
            print(f"   - Final match rate: {match_rate:.1f}%")
            
            # 詳細結果の表示（最初の5つ）
            print(f"\n🔍 Sample Match Results:")
            for i, query in enumerate(list(all_queries)[:5], 1):
                matches = final_matches.get(query, [])
                if matches:
                    best_match = matches[0] if isinstance(matches, list) else matches
                    match_name = getattr(best_match, 'food_name', 'N/A')
                    match_score = getattr(best_match, 'score', 0)
                    is_exact = getattr(best_match, 'is_exact_match', False)
                    match_type = "EXACT" if is_exact else "FUZZY"
                    print(f"   {i}. '{query}' → '{match_name}' (score: {match_score:.3f}, {match_type})")
                else:
                    print(f"   {i}. '{query}' → No match found")
        
        # 代替検索結果の表示
        alternative_matches = getattr(enhanced_result, 'alternative_matches', {})
        if alternative_matches:
            print(f"\n🔄 Alternative Search Results (Phase1.5 Generated):")
            alt_count = 0
            for query, alt_results in alternative_matches.items():
                if alt_count >= 5:  # 最初の5つだけ表示
                    break
                print(f"   '{query}': {len(alt_results)} alternative results found")
                for alt_result in alt_results[:2]:  # 最初の2つだけ表示
                    match = alt_result.get('match', {})
                    match_name = getattr(match, 'food_name', 'N/A')
                    match_score = getattr(match, 'score', 0)
                    print(f"     → '{match_name}' (score: {match_score:.3f})")
                alt_count += 1
        
        # 結果を保存
        await save_phase1_5_test_results(
            analysis_id, enhanced_result, all_queries, dish_names, ingredient_names, 
            image_filename=os.path.basename(image_path), main_results_dir=main_results_dir
        )
        
        # この画像の結果をサマリー用に返す
        summary_result = {
            "image_name": os.path.basename(image_path),
            "analysis_id": analysis_id,
            "total_creative_queries": len(all_queries),
            "phase15_iterations": getattr(enhanced_result, 'total_iterations', 0),
            "phase15_executions": len(getattr(enhanced_result, 'phase15_history', [])),
            "final_match_rate": (sum(1 for matches in final_matches.values() if matches) / len(all_queries) * 100) if final_matches and all_queries else 0,
            "processing_time": getattr(enhanced_result, 'processing_time', 0),
            "dish_names": dish_names,
            "ingredient_names": ingredient_names,
            "all_queries": all_queries,
            "phase15_triggered": len(getattr(enhanced_result, 'phase15_history', [])) > 0
        }
        
        print(f"\n✅ Phase1.5 integration test for {os.path.basename(image_path)} completed!")
        
        # Phase1.5が実際に動作したかの判定
        if phase15_history:
            print(f"🎯 Phase1.5 system is working correctly for this image!")
            print(f"   - {len(phase15_history)} Phase1.5 iterations executed")
            print(f"   - Alternative query generation successful")
        else:
            print(f"⚠️  Phase1.5 system was not triggered for this image")
            print(f"   - Creative queries may have had exact matches")
            print(f"   - Consider more creative naming in test prompts")
        
        return summary_result
        
    except Exception as e:
        print(f"❌ Phase1.5 integration test failed for {os.path.basename(image_path)}: {e}")
        import traceback
        traceback.print_exc()
        return None

async def save_phase1_5_test_results(
    analysis_id: str, 
    enhanced_result, 
    all_queries: List[str], 
    dish_names: List[str], 
    ingredient_names: List[str], 
    image_filename: str, 
    main_results_dir: str
):
    """Phase1.5テスト結果を保存"""
    
    # 画像別のディレクトリを作成
    image_name = os.path.splitext(image_filename)[0]
    image_results_dir = os.path.join(main_results_dir, image_name)
    os.makedirs(image_results_dir, exist_ok=True)
    
    # NutritionMatchオブジェクトを辞書に変換する関数
    def convert_nutrition_match_to_dict(match):
        if hasattr(match, '__dict__'):
            return {
                "food_name": getattr(match, 'food_name', 'N/A'),
                "score": getattr(match, 'score', 0),
                "is_exact_match": getattr(match, 'is_exact_match', False),
                "search_name": getattr(match, 'search_name', 'N/A'),
                "fdc_id": getattr(match, 'fdc_id', None),
                "data_type": getattr(match, 'data_type', 'N/A')
            }
        return match
    
    # final_resultsを変換
    final_results_dict = {}
    final_results = getattr(enhanced_result, 'final_results', {})
    for query, matches in final_results.items():
        if isinstance(matches, list):
            final_results_dict[query] = [convert_nutrition_match_to_dict(match) for match in matches]
        else:
            final_results_dict[query] = convert_nutrition_match_to_dict(matches)
    
    # alternative_matchesを変換
    alternative_matches_dict = {}
    alternative_matches = getattr(enhanced_result, 'alternative_matches', {})
    for query, alt_results in alternative_matches.items():
        alternative_matches_dict[query] = []
        for alt_result in alt_results:
            if isinstance(alt_result, dict) and 'match' in alt_result:
                converted_alt_result = dict(alt_result)
                converted_alt_result['match'] = convert_nutrition_match_to_dict(alt_result['match'])
                alternative_matches_dict[query].append(converted_alt_result)
            else:
                alternative_matches_dict[query].append(alt_result)
    
    # 詳細結果を作成
    detailed_result = {
        "analysis_id": analysis_id,
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "image_filename": image_filename,
        "test_type": "phase1_5_integration_test",
        "input_queries": {
            "all_queries": all_queries,
            "dish_names": dish_names,
            "ingredient_names": ingredient_names
        },
        "phase15_integration": {
            "total_iterations": getattr(enhanced_result, 'total_iterations', 0),
            "phase15_executions": len(getattr(enhanced_result, 'phase15_history', [])),
            "phase15_history": getattr(enhanced_result, 'phase15_history', []),
            "processing_time": getattr(enhanced_result, 'processing_time', 0)
        },
        "final_results": final_results_dict,
        "alternative_matches": alternative_matches_dict,
        "warnings": getattr(enhanced_result, 'warnings', []),
        "errors": getattr(enhanced_result, 'errors', [])
    }
    
    # JSON形式で保存
    json_path = os.path.join(image_results_dir, f"phase1_5_integration_results.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_result, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 Phase1.5 test results saved: {json_path}")

async def test_phase1_5_integration():
    """Phase1.5統合テスト（複数画像）"""
    
    print("🚀 Phase1.5 Integration Test with Real Images")
    print("=" * 80)
    print("🎨 Using creative naming prompts to trigger Phase1.5 alternative query generation")
    print(f"📁 Testing {len(image_files)} images: {[os.path.basename(f) for f in image_files]}")
    
    # メイン結果ディレクトリを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_results_dir = f"analysis_results/phase1_5_integration_test_{timestamp}"
    os.makedirs(main_results_dir, exist_ok=True)
    
    print(f"📁 Created main results directory: {main_results_dir}")
    
    all_results = []
    total_phase15_executions = 0
    total_phase15_iterations = 0
    total_processing_time = 0
    
    # 各画像でテストを実行
    for image_path in image_files:
        result = await test_single_image_phase1_5_integration(image_path, main_results_dir)
        if result:
            all_results.append(result)
            total_phase15_executions += result.get('phase15_executions', 0)
            total_phase15_iterations += result.get('phase15_iterations', 0)
            total_processing_time += result.get('processing_time', 0)
    
    # 総合サマリーを作成
    print(f"\n{'='*80}")
    print(f"🎯 OVERALL PHASE1.5 INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    print(f"📊 Images tested: {len(all_results)}/{len(image_files)}")
    print(f"📈 Overall Statistics:")
    print(f"   - Total Phase1.5 executions: {total_phase15_executions}")
    print(f"   - Total Phase1.5 iterations: {total_phase15_iterations}")
    print(f"   - Average Phase1.5 executions per image: {total_phase15_executions / len(all_results) if all_results else 0:.1f}")
    print(f"   - Total processing time: {total_processing_time:.2f}s")
    print(f"   - Average processing time per image: {total_processing_time / len(all_results) if all_results else 0:.2f}s")
    
    # Phase1.5が動作した画像の統計
    phase15_triggered_images = [r for r in all_results if r.get('phase15_triggered', False)]
    print(f"   - Images that triggered Phase1.5: {len(phase15_triggered_images)}/{len(all_results)}")
    print(f"   - Phase1.5 trigger rate: {len(phase15_triggered_images) / len(all_results) * 100 if all_results else 0:.1f}%")
    
    # 画像別の結果詳細
    print(f"\n📋 Per-Image Results Breakdown:")
    for i, result in enumerate(all_results, 1):
        phase15_status = "✅ TRIGGERED" if result.get('phase15_triggered', False) else "⚠️  NOT TRIGGERED"
        print(f"   {i}. {result['image_name']}:")
        print(f"      - Creative queries: {result['total_creative_queries']}")
        print(f"      - Phase1.5 executions: {result['phase15_executions']}")
        print(f"      - Phase1.5 iterations: {result['phase15_iterations']}")
        print(f"      - Final match rate: {result['final_match_rate']:.1f}%")
        print(f"      - Processing time: {result['processing_time']:.2f}s")
        print(f"      - Phase1.5 status: {phase15_status}")
    
    # 総合結果を保存
    comprehensive_results = {
        "test_summary": {
            "test_type": "phase1_5_integration_test",
            "timestamp": timestamp,
            "images_tested": len(all_results),
            "total_images": len(image_files),
            "total_phase15_executions": total_phase15_executions,
            "total_phase15_iterations": total_phase15_iterations,
            "phase15_trigger_rate": len(phase15_triggered_images) / len(all_results) * 100 if all_results else 0,
            "total_processing_time": total_processing_time,
            "average_processing_time": total_processing_time / len(all_results) if all_results else 0
        },
        "per_image_results": all_results
    }
    
    # JSON形式で保存
    comprehensive_json_path = os.path.join(main_results_dir, "comprehensive_phase1_5_integration_results.json")
    with open(comprehensive_json_path, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 Comprehensive Phase1.5 integration results saved to:")
    print(f"   📁 {main_results_dir}/")
    print(f"   📄 comprehensive_phase1_5_integration_results.json")
    
    # 成功判定
    if total_phase15_executions > 0:
        print(f"\n✅ Phase1.5 integration test completed successfully!")
        print(f"🎯 Phase1.5 system is working correctly!")
        print(f"   - {total_phase15_executions} Phase1.5 executions across {len(all_results)} images")
        print(f"   - {len(phase15_triggered_images)} images successfully triggered Phase1.5")
        return True
    else:
        print(f"\n⚠️  Phase1.5 integration test completed with warnings")
        print(f"   - No Phase1.5 executions were triggered")
        print(f"   - Creative prompts may need adjustment")
        print(f"   - Or all creative queries had exact matches")
        return False

async def main():
    """メイン実行関数"""
    success = await test_phase1_5_integration()
    
    if success:
        print(f"\n🎉 Phase1.5 integration test passed!")
    else:
        print(f"\n💥 Phase1.5 integration test needs attention!")

if __name__ == "__main__":
    asyncio.run(main()) 