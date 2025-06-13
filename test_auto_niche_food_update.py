#!/usr/bin/env python3
"""
Test Auto Niche Food Update functionality

自動ニッチ食材更新機能のテスト
"""

import asyncio
import json
from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput
from app_v2.utils.niche_food_manager import NicheFoodManager

async def test_auto_niche_food_update():
    """自動ニッチ食材更新機能のテスト"""
    print("🧪 Testing auto niche food update functionality...")
    
    # 1. 既存のニッチ食材マッピングをバックアップ
    manager = NicheFoodManager()
    original_mappings = manager.load_mappings()
    print(f"   📊 Original mappings: {len(original_mappings['ingredients']['no_exact_match_items'])} ingredients, {len(original_mappings['dishes']['no_exact_match_items'])} dishes")
    
    # 2. Elasticsearchコンポーネントを初期化（自動更新有効）
    es_component = ElasticsearchNutritionSearchComponent(
        elasticsearch_url="http://localhost:9200",
        enable_advanced_features=True,
        enable_auto_niche_update=True,  # 自動更新を有効化
        debug=True
    )
    
    # 3. テスト用のクエリ（意図的にexact matchがないものを含める）
    test_queries = [
        # 既存クエリ（exact matchがある想定）
        "chicken",
        "tomato",
        
        # ニッチなクエリ（exact matchがない可能性）
        "rainbow quinoa",        # ニッチな食材
        "purple sweet potato",   # ニッチな食材
        "jackfruit tacos",       # ニッチな料理
        "microgreen salad",      # ニッチな料理
        "spirulina smoothie",    # ニッチな料理
    ]
    
    # 4. 検索を実行（自動更新を触発）
    print(f"\n🔍 Running search with {len(test_queries)} queries...")
    
    # NutritionQueryInputを作成
    input_data = NutritionQueryInput(
        dish_names=["jackfruit tacos", "microgreen salad", "spirulina smoothie"],
        ingredient_names=["rainbow quinoa", "purple sweet potato", "chicken", "tomato"],
        meal_context="test auto update",
        preferred_source="elasticsearch"
    )
    
    # 検索実行
    search_result = await es_component._lemmatized_enhanced_search(input_data, test_queries)
    
    # 5. 検索結果の分析
    print(f"\n📊 Search results:")
    print(f"   - Total searches: {search_result.search_summary['total_searches']}")
    print(f"   - Successful matches: {search_result.search_summary['successful_matches']}")
    print(f"   - Match rate: {search_result.search_summary['match_rate_percent']}%")
    
    # exact matchの状況を分析
    exact_match_queries = []
    no_exact_match_queries = []
    
    for query, matches in search_result.matches.items():
        if not matches:
            no_exact_match_queries.append(query)
            continue
            
        has_exact_match = any(match.is_exact_match for match in matches)
        if has_exact_match:
            exact_match_queries.append(query)
        else:
            no_exact_match_queries.append(query)
    
    print(f"\n🎯 Exact match analysis:")
    print(f"   ✅ Queries with exact match: {len(exact_match_queries)}")
    for query in exact_match_queries:
        print(f"     - {query}")
    
    print(f"   ❌ Queries without exact match: {len(no_exact_match_queries)}")
    for query in no_exact_match_queries:
        print(f"     - {query}")
    
    # 6. 更新後のニッチ食材マッピングを確認
    updated_mappings = manager.load_mappings()
    print(f"\n📈 Updated mappings: {len(updated_mappings['ingredients']['no_exact_match_items'])} ingredients, {len(updated_mappings['dishes']['no_exact_match_items'])} dishes")
    
    # 新しく追加された項目を特定
    original_ingredients = set(item["original"] for item in original_mappings["ingredients"]["no_exact_match_items"])
    updated_ingredients = set(item["original"] for item in updated_mappings["ingredients"]["no_exact_match_items"])
    new_ingredients = updated_ingredients - original_ingredients
    
    original_dishes = set(original_mappings["dishes"]["no_exact_match_items"])
    updated_dishes = set(updated_mappings["dishes"]["no_exact_match_items"])
    new_dishes = updated_dishes - original_dishes
    
    if new_ingredients or new_dishes:
        print(f"\n🆕 Newly added items:")
        if new_ingredients:
            print(f"   🥗 New ingredients: {len(new_ingredients)}")
            for ingredient in new_ingredients:
                print(f"     + {ingredient}")
        
        if new_dishes:
            print(f"   🍽️  New dishes: {len(new_dishes)}")
            for dish in new_dishes:
                print(f"     + {dish}")
    else:
        print(f"\n📌 No new items were added (all queries had exact matches)")
    
    print(f"\n🎉 Auto niche food update test completed!")
    
    return {
        "original_mappings": original_mappings,
        "updated_mappings": updated_mappings,
        "search_result": search_result,
        "exact_match_queries": exact_match_queries,
        "no_exact_match_queries": no_exact_match_queries,
        "new_ingredients": list(new_ingredients),
        "new_dishes": list(new_dishes)
    }

if __name__ == "__main__":
    asyncio.run(test_auto_niche_food_update()) 