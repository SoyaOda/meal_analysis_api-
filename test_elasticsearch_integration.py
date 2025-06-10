#!/usr/bin/env python3
"""
Elasticsearch Integration Test

新しいElasticsearchNutritionSearchComponentをテストする
"""

import asyncio
import json
from typing import List

from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

async def test_elasticsearch_component():
    """ElasticsearchNutritionSearchComponentのテスト"""
    
    print("=== Elasticsearch Integration Test ===")
    
    # テスト用クエリデータ
    test_queries = {
        "ingredient_names": ["Chicken", "Potato", "Lettuce", "Tomato"],
        "dish_names": ["Roasted Potatoes", "Mixed Green Salad"]
    }
    
    print(f"🔍 Testing with {len(test_queries['ingredient_names'])} ingredients and {len(test_queries['dish_names'])} dishes")
    
    try:
        # コンポーネントの初期化
        print("\n1. Initializing ElasticsearchNutritionSearchComponent...")
        component = ElasticsearchNutritionSearchComponent()
        
        # 入力データの作成
        input_data = NutritionQueryInput(
            ingredient_names=test_queries["ingredient_names"],
            dish_names=test_queries["dish_names"],
            preferred_source="elasticsearch"
        )
        
        print(f"   Total search terms: {len(input_data.get_all_search_terms())}")
        print(f"   Search terms: {input_data.get_all_search_terms()}")
        
        # 検索実行
        print("\n2. Executing search...")
        result = await component.execute(input_data)
        
        # 結果の表示
        print(f"\n✅ Search completed!")
        print(f"   Search method: {result.search_summary.get('search_method', 'unknown')}")
        print(f"   Total searches: {result.search_summary.get('total_searches', 0)}")
        print(f"   Successful matches: {result.search_summary.get('successful_matches', 0)}")
        print(f"   Match rate: {result.search_summary.get('match_rate_percent', 0):.1f}%")
        print(f"   Search time: {result.search_summary.get('search_time_ms', 0)}ms")
        
        # 詳細マッチ結果
        print(f"\n📊 Match Details:")
        for search_term, match in result.matches.items():
            print(f"   '{search_term}' -> '{match.search_name}' (score: {match.score:.3f})")
            if match.nutrition:
                calories = match.nutrition.get('calories', 0)
                protein = match.nutrition.get('protein', 0)
                print(f"      Nutrition: {calories:.1f} kcal, {protein:.1f}g protein")
        
        # 警告・エラーの表示
        if result.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        if result.errors:
            print(f"\n❌ Errors:")
            for error in result.errors:
                print(f"   - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_component_comparison():
    """ElasticsearchコンポーネントとLocalコンポーネントの比較テスト"""
    
    print("\n=== Component Comparison Test ===")
    
    # 同じクエリで両方のコンポーネントをテスト
    test_queries = {
        "ingredient_names": ["Chicken", "Potato"],
        "dish_names": ["Roasted Potatoes"]
    }
    
    input_data = NutritionQueryInput(
        ingredient_names=test_queries["ingredient_names"],
        dish_names=test_queries["dish_names"]
    )
    
    try:
        # Elasticsearchコンポーネント
        print("\n1. Testing ElasticsearchNutritionSearchComponent...")
        es_component = ElasticsearchNutritionSearchComponent()
        es_result = await es_component.execute(input_data)
        
        # Localコンポーネント（比較用）
        print("\n2. Testing LocalNutritionSearchComponent...")
        from app_v2.components.local_nutrition_search_component import LocalNutritionSearchComponent
        local_component = LocalNutritionSearchComponent()
        local_result = await local_component.execute(input_data)
        
        # 比較結果
        print(f"\n📈 Comparison Results:")
        print(f"   Elasticsearch: {es_result.search_summary.get('successful_matches', 0)} matches in {es_result.search_summary.get('search_time_ms', 0)}ms")
        print(f"   Local DB:      {local_result.search_summary.get('successful_matches', 0)} matches in {local_result.search_summary.get('search_time_ms', 0)}ms")
        
        # 検索方法の比較
        es_method = es_result.search_summary.get('search_method', 'unknown')
        local_method = local_result.search_summary.get('search_method', 'unknown')
        print(f"   ES Method:     {es_method}")
        print(f"   Local Method:  {local_method}")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Elasticsearch Integration Tests")
    
    # 基本テスト
    success1 = asyncio.run(test_elasticsearch_component())
    
    # 比較テスト
    success2 = asyncio.run(test_component_comparison())
    
    if success1 and success2:
        print("\n✅ All Elasticsearch integration tests passed!")
    else:
        print("\n❌ Some tests failed!") 