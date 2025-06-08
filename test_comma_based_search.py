#!/usr/bin/env python3
"""
カンマベース段階的検索戦略テスト

search_nameのカンマ区切り構造を活用した改善効果を検証
"""

import asyncio
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery

async def test_comma_based_search_strategy():
    """カンマベース段階的検索戦略をテスト"""
    
    print("🎯 カンマベース段階的検索戦略テスト")
    print("="*70)
    
    # テストクエリ
    test_queries = [
        "potato",
        "tomato", 
        "corn",
        "lettuce",
        "onion"
    ]
    
    for query_term in test_queries:
        print(f"\n🔍 Testing: '{query_term}'")
        print("-"*50)
        
        query = SearchQuery(elasticsearch_query_terms=query_term)
        results = await food_search_service.search_foods(query, size=5)
        
        print("Top 5 results:")
        for i, r in enumerate(results, 1):
            # search_nameをカンマで分割して表示
            name_parts = r.food_name.split(',', 1)
            name_part = name_parts[0].strip() if name_parts else r.food_name
            desc_part = name_parts[1].strip() if len(name_parts) > 1 else ""
            
            print(f"{i:2}. Name: '{name_part}' | Desc: '{desc_part}' | Score: {r.score:.2f}")
            print(f"    Type: {r.data_type} | {r.nutrition.get('calories', 0):3.0f}kcal")
            
            # 期待される結果かチェック
            if query_term.lower() in name_part.lower():
                if "raw" in desc_part.lower() or "flesh" in desc_part.lower():
                    print(f"    ✅ EXCELLENT: Raw ingredient match!")
                elif any(word in desc_part.lower() for word in ["cooked", "boiled", "baked"]):
                    print(f"    ✅ GOOD: Basic preparation match")
                else:
                    print(f"    ⚠️  OK: Name match but check description")
            else:
                print(f"    ❌ POOR: Name doesn't match query")
        
        # 最上位結果の詳細分析
        if results:
            top_result = results[0]
            name_parts = top_result.food_name.split(',', 1)
            name_part = name_parts[0].strip() if name_parts else top_result.food_name
            
            print(f"\n📊 Top result analysis:")
            print(f"   Query: '{query_term}' vs Name: '{name_part}'")
            print(f"   Exact match: {query_term.lower() == name_part.lower()}")
            print(f"   Contains query: {query_term.lower() in name_part.lower()}")
            print(f"   Data type: {top_result.data_type}")
            
            # eatthismuchとの比較
            if query_term == "potato":
                expected_names = ["potato", "potatoes", "red potatoes", "russet potatoes", "white potatoes"]
                is_expected = any(exp.lower() in name_part.lower() for exp in expected_names)
                print(f"   Matches eatthismuch expectation: {is_expected}")

async def test_specific_potato_cases():
    """potato検索の具体的なケースをテスト"""
    
    print(f"\n🥔 Potato検索詳細テスト")
    print("="*70)
    
    query = SearchQuery(elasticsearch_query_terms="potato")
    results = await food_search_service.search_foods(query, size=10)
    
    print("Expected vs Actual results:")
    print("-"*50)
    
    # eatthismuchの期待結果
    expected_results = [
        "Potato, Flesh and skin, raw",
        "Potatoes, Fast foods, hashed brown", 
        "Sweet potato, Raw, unprepared",
        "Red potatoes, Flesh and skin, raw",
        "Russet potatoes, Flesh and skin, raw"
    ]
    
    print("Expected (eatthismuch):")
    for i, expected in enumerate(expected_results, 1):
        print(f"{i:2}. {expected}")
    
    print(f"\nActual (our algorithm):")
    for i, r in enumerate(results, 1):
        name_parts = r.food_name.split(',', 1)
        name_part = name_parts[0].strip()
        desc_part = name_parts[1].strip() if len(name_parts) > 1 else ""
        
        # 期待結果との一致チェック
        match_found = False
        for expected in expected_results:
            if expected.lower() in r.food_name.lower():
                match_found = True
                break
        
        status = "✅" if match_found else "❌"
        print(f"{i:2}. {status} {name_part} | {desc_part} | Score: {r.score:.2f}")
        print(f"    {r.data_type} | {r.nutrition.get('calories', 0):3.0f}kcal")

if __name__ == "__main__":
    asyncio.run(test_comma_based_search_strategy())
    asyncio.run(test_specific_potato_cases()) 