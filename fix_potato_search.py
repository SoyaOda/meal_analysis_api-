#!/usr/bin/env python3
"""
Potato検索問題修正案

Function Score再有効化とキーワードブースト戦略を実装
"""

import asyncio
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery, NutritionTarget
from app_v2.elasticsearch.config import es_config

async def test_potato_search_improvements():
    """potato検索改善案をテスト"""
    
    print("🛠 Potato検索改善案テスト")
    print("="*70)
    
    # 現在の設定を保存
    original_enable_nutritional = es_config.enable_nutritional_similarity
    original_nutritional_weight = es_config.nutritional_similarity_weight
    original_enable_popularity = es_config.enable_popularity_boost
    original_popularity_weight = es_config.popularity_boost_weight
    
    try:
        # 改善案1: Function Score再有効化
        print("1. 改善案: Function Score再有効化")
        print("-"*50)
        
        # 設定を一時的に変更
        es_config.enable_nutritional_similarity = True
        es_config.nutritional_similarity_weight = 2.5
        es_config.enable_popularity_boost = True
        es_config.popularity_boost_weight = 0.5
        
        # 生ポテトの典型的な栄養プロファイル
        raw_potato_nutrition = NutritionTarget(
            calories=280.0,
            protein_g=7.0,
            fat_total_g=0.3,
            carbohydrate_by_difference_g=64.0
        )
        
        query_with_nutrition = SearchQuery(
            elasticsearch_query_terms='potato',
            target_nutrition_vector=raw_potato_nutrition
        )
        
        improved_results = await food_search_service.search_foods(
            query_with_nutrition, 
            size=8,
            enable_nutritional_similarity=True
        )
        
        print("Function Score有効化後の結果:")
        for i, r in enumerate(improved_results, 1):
            cal_diff = abs(r.nutrition.get('calories', 0) - 280.0)
            fat_diff = abs(r.nutrition.get('fat_total_g', 0) - 0.3)
            is_raw = 'raw' in r.food_name.lower() or ('flesh' in r.food_name.lower() and 'skin' in r.food_name.lower())
            status = "✅" if is_raw else "⚠️"
            
            print(f"{i}. {status} {r.food_name[:40]:40} | Score: {r.score:.3f}")
            print(f"   {r.nutrition.get('calories', 0):3.0f}kcal (diff: {cal_diff:3.0f}), Type: {r.data_type}, Fav: {r.num_favorites}")
        
        # 改善案2: データタイプ優先度テスト
        print("\n2. 改善案: Ingredient優先検索")
        print("-"*50)
        
        ingredient_priority_results = await food_search_service.search_foods(
            query_with_nutrition,
            size=8,
            enable_nutritional_similarity=True,
            data_type_filter=["ingredient", "dish"]  # ingredientを優先、brandedを除外
        )
        
        print("Ingredient優先検索結果:")
        for i, r in enumerate(ingredient_priority_results, 1):
            is_raw = 'raw' in r.food_name.lower() or ('flesh' in r.food_name.lower() and 'skin' in r.food_name.lower())
            status = "✅" if is_raw else "⚠️"
            
            print(f"{i}. {status} {r.food_name[:40]:40} | {r.data_type}")
            print(f"   {r.nutrition.get('calories', 0):3.0f}kcal, {r.nutrition.get('carbohydrate_by_difference_g', 0):2.0f}g carbs, {r.nutrition.get('fat_total_g', 0):3.1f}g fat")
        
        # 改善案3: 具体的なクエリ改善
        print("\n3. 改善案: クエリ改善テスト")
        print("-"*50)
        
        improved_queries = [
            "potato raw flesh skin",
            "potato raw",
            "fresh potato",
            "raw potato"
        ]
        
        for query_text in improved_queries:
            print(f"\nクエリ: '{query_text}'")
            improved_query = SearchQuery(
                elasticsearch_query_terms=query_text,
                target_nutrition_vector=raw_potato_nutrition
            )
            
            results = await food_search_service.search_foods(
                improved_query,
                size=3,
                enable_nutritional_similarity=True,
                data_type_filter=["ingredient", "dish"]
            )
            
            for i, r in enumerate(results, 1):
                is_raw = 'raw' in r.food_name.lower()
                status = "✅" if is_raw else "⚠️"
                print(f"  {i}. {status} {r.food_name[:35]:35} | {r.nutrition.get('calories', 0):3.0f}kcal")
        
        # 最適化された設定での最終テスト
        print("\n4. 最適化設定での最終テスト")
        print("-"*50)
        
        final_query = SearchQuery(
            elasticsearch_query_terms='potato raw flesh skin',
            target_nutrition_vector=raw_potato_nutrition
        )
        
        final_results = await food_search_service.search_foods(
            final_query,
            size=5,
            enable_nutritional_similarity=True,
            data_type_filter=["ingredient"]  # ingredientのみに限定
        )
        
        print("最適化設定での結果（eatthismuchとの比較）:")
        expected_results = [
            {"name": "Potato - Flesh and skin, raw", "calories": 284},
            {"name": "Red potatoes - Flesh and skin, raw", "calories": 119}, 
            {"name": "Russet potatoes - Flesh and skin, raw", "calories": 292},
        ]
        
        for i, r in enumerate(final_results, 1):
            cal_match = any(abs(r.nutrition.get('calories', 0) - exp['calories']) < 50 for exp in expected_results)
            name_match = any(key in r.food_name.lower() for key in ['flesh', 'skin', 'raw'])
            
            if cal_match and name_match:
                status = "🎯 PERFECT MATCH"
            elif name_match:
                status = "✅ GOOD MATCH"
            else:
                status = "⚠️ PARTIAL MATCH"
            
            print(f"{i}. {status}")
            print(f"   {r.food_name}")
            print(f"   {r.nutrition.get('calories', 0):3.0f}kcal, {r.nutrition.get('carbohydrate_by_difference_g', 0):2.0f}g carbs, {r.nutrition.get('fat_total_g', 0):3.1f}g fat, {r.nutrition.get('protein_g', 0):2.0f}g protein")
        
    finally:
        # 設定を元に戻す
        es_config.enable_nutritional_similarity = original_enable_nutritional
        es_config.nutritional_similarity_weight = original_nutritional_weight
        es_config.enable_popularity_boost = original_enable_popularity
        es_config.popularity_boost_weight = original_popularity_weight
    
    # 推奨設定
    print("\n5. 推奨される設定変更")
    print("-"*50)
    print("✅ 推奨設定:")
    print("  - enable_nutritional_similarity: True")
    print("  - nutritional_similarity_weight: 2.5")
    print("  - enable_popularity_boost: True")  
    print("  - popularity_boost_weight: 0.5")
    print("  - クエリ改善: 'potato raw flesh skin'")
    print("  - データタイプフィルタ: ['ingredient', 'dish']")
    
    print("\n📋 実装すべき改善:")
    print("1. Function Scoreを再有効化")
    print("2. 栄養プロファイル類似性を活用") 
    print("3. 'raw', 'flesh', 'skin'キーワードの検索クエリ改善")
    print("4. データタイプ 'ingredient' の優先度向上")

if __name__ == "__main__":
    asyncio.run(test_potato_search_improvements()) 