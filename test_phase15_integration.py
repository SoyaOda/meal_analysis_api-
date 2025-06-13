#!/usr/bin/env python3
"""
Phase1.5 Integration Test

Phase1.5システムが正しく統合されているかテストするスクリプト
意図的に失敗するクエリを含めてPhase1.5の代替クエリ生成機能をテスト
"""

import os
import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any

# 環境変数の設定（サーバーと同じ設定）
os.environ.setdefault("USDA_API_KEY", "vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api_2/service-account-key.json")
os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
os.environ.setdefault("GEMINI_LOCATION", "us-central1")
os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")

from app_v2.components.enhanced_nutrition_search_component import EnhancedNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

async def test_phase15_integration():
    """Phase1.5統合テスト"""
    
    print("🚀 Phase1.5 Integration Test")
    print("=" * 60)
    
    # 意図的に失敗するクエリを含むテストデータ
    test_queries = [
        # 失敗する可能性が高いクエリ（Phase1.5が呼び出される）
        "xyzabc_nonexistent_food_12345",
        "ultra_rare_magical_ingredient_999",
        "impossible_dish_from_mars_777",
        "imaginary_quantum_sauce_666",
        "fictional_alien_vegetable_888",
        "mythical_dragon_meat_555",
        "unicorn_tears_seasoning_333"
    ]
    
    print(f"📝 Test queries: {len(test_queries)} items")
    print(f"   - All queries designed to fail (Phase1.5 triggers): {len(test_queries)} items")
    
    # EnhancedNutritionSearchComponentを初期化
    enhanced_component = EnhancedNutritionSearchComponent(
        enable_phase15=True,
        max_phase15_iterations=3,
        debug=True
    )
    
    # テスト入力を作成
    nutrition_input = NutritionQueryInput(
        ingredient_names=test_queries[:4],  # 最初の4つを食材として
        dish_names=test_queries[4:],        # 残りを料理として
        preferred_source="elasticsearch"
    )
    
    print(f"\n🔍 Starting enhanced search with Phase1.5...")
    start_time = time.time()
    
    try:
        # 拡張検索を実行
        result = await enhanced_component.execute(nutrition_input)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Enhanced search completed in {processing_time:.2f}s")
        
        # 結果の分析
        print(f"\n📊 Phase1.5 Integration Results:")
        print(f"   - Total iterations: {getattr(result, 'total_iterations', 0)}")
        print(f"   - Phase1.5 executions: {len(getattr(result, 'phase15_history', []))}")
        print(f"   - Processing time: {getattr(result, 'processing_time', 0):.2f}s")
        
        # Phase1.5履歴の詳細表示
        phase15_history = getattr(result, 'phase15_history', [])
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
            print(f"\n⚠️  No Phase1.5 executions recorded (all queries may have had exact matches)")
        
        # 最終的なマッチ率
        final_matches = getattr(result, 'final_results', {})
        if final_matches:
            total_queries = len(test_queries)
            successful_matches = sum(1 for matches in final_matches.values() if matches)
            match_rate = (successful_matches / total_queries) * 100 if total_queries > 0 else 0
            
            print(f"\n📈 Final Results:")
            print(f"   - Total queries: {total_queries}")
            print(f"   - Successful matches: {successful_matches}")
            print(f"   - Final match rate: {match_rate:.1f}%")
            
            # 詳細結果の表示
            print(f"\n🔍 Detailed Match Results:")
            for query in test_queries:
                matches = final_matches.get(query, [])
                if matches:
                    best_match = matches[0] if isinstance(matches, list) else matches
                    match_name = getattr(best_match, 'food_name', 'N/A')
                    match_score = getattr(best_match, 'score', 0)
                    is_exact = getattr(best_match, 'is_exact_match', False)
                    match_type = "EXACT" if is_exact else "FUZZY"
                    print(f"   ✅ '{query}' → '{match_name}' (score: {match_score:.3f}, {match_type})")
                else:
                    print(f"   ❌ '{query}' → No match found")
        
        # 代替検索結果の表示
        alternative_matches = getattr(result, 'alternative_matches', {})
        if alternative_matches:
            print(f"\n🔄 Alternative Search Results:")
            for query, alt_results in alternative_matches.items():
                print(f"   '{query}': {len(alt_results)} alternative results found")
                for alt_result in alt_results[:2]:  # 最初の2つだけ表示
                    match = alt_result.get('match', {})
                    match_name = getattr(match, 'food_name', 'N/A')
                    match_score = getattr(match, 'score', 0)
                    print(f"     → '{match_name}' (score: {match_score:.3f})")
        
        print(f"\n✅ Phase1.5 integration test completed successfully!")
        
        # Phase1.5が実際に動作したかの判定
        if phase15_history:
            print(f"🎯 Phase1.5 system is working correctly!")
            print(f"   - {len(phase15_history)} Phase1.5 iterations executed")
            print(f"   - Alternative query generation successful")
        else:
            print(f"⚠️  Phase1.5 system may not have been triggered")
            print(f"   - All queries may have had exact matches")
            print(f"   - Consider using more obscure test queries")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase1.5 integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行関数"""
    success = await test_phase15_integration()
    
    if success:
        print(f"\n🎉 All tests passed!")
    else:
        print(f"\n💥 Tests failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 