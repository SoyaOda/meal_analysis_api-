#!/usr/bin/env python3
"""
段階的検索戦略テスト v2.0

food_name主要、description補助の2段階検索戦略をテスト
"""

import asyncio
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery

async def test_two_stage_search_strategy():
    """段階的検索戦略をテスト"""
    
    print("🎯 段階的検索戦略テスト v2.0")
    print("="*70)
    
    # テストクエリ
    test_cases = [
        {
            "query": "potato",
            "expected_priority": ["raw", "flesh", "skin", "fresh"],
            "expected_names": ["Potato", "Potatoes", "Red potatoes", "Russet potatoes", "White potatoes"]
        },
        {
            "query": "tomato",
            "expected_priority": ["raw", "fresh"],
            "expected_names": ["Tomato", "Tomatoes"]
        },
        {
            "query": "corn",
            "expected_priority": ["raw", "fresh"],
            "expected_names": ["Corn", "Sweet corn"]
        },
        {
            "query": "onion",
            "expected_priority": ["raw", "fresh"],
            "expected_names": ["Onion", "Onions"]
        }
    ]
    
    for test_case in test_cases:
        query_term = test_case["query"]
        expected_priority = test_case["expected_priority"]
        expected_names = test_case["expected_names"]
        
        print(f"\n🔍 Testing: '{query_term}'")
        print("-"*50)
        
        query = SearchQuery(elasticsearch_query_terms=query_term)
        results = await food_search_service.search_foods(query, size=8)
        
        print("Top 8 results:")
        raw_ingredient_found = False
        
        for i, r in enumerate(results, 1):
            # 現在のデータ構造に対応（search_nameがカンマ区切り）
            if ',' in r.food_name:
                name_parts = r.food_name.split(',', 1)
                name_part = name_parts[0].strip()
                desc_part = name_parts[1].strip()
            else:
                name_part = r.food_name
                desc_part = ""
            
            print(f"{i:2}. Name: '{name_part}' | Desc: '{desc_part}' | Score: {r.score:.2f}")
            print(f"    Type: {r.data_type} | {r.nutrition.get('calories', 0):3.0f}kcal")
            
            # 分析結果
            name_match = query_term.lower() in name_part.lower()
            raw_keywords = any(keyword in desc_part.lower() for keyword in expected_priority)
            expected_name = any(exp.lower() in name_part.lower() for exp in expected_names)
            
            if name_match and raw_keywords and expected_name:
                print(f"    ✅ PERFECT: Expected name + raw ingredient!")
                raw_ingredient_found = True
            elif name_match and expected_name:
                if raw_keywords:
                    print(f"    ✅ EXCELLENT: Expected name + raw/fresh!")
                    raw_ingredient_found = True
                else:
                    print(f"    ✅ GOOD: Expected name match")
            elif name_match:
                print(f"    ⚠️  OK: Name match but check if expected")
            else:
                print(f"    ❌ POOR: Name doesn't match query")
        
        # 総評
        print(f"\n📊 Summary for '{query_term}':")
        if results:
            top_result = results[0]
            if ',' in top_result.food_name:
                name_parts = top_result.food_name.split(',', 1)
                top_name = name_parts[0].strip()
                top_desc = name_parts[1].strip()
            else:
                top_name = top_result.food_name
                top_desc = ""
            
            print(f"   Top result: '{top_name}' + '{top_desc}'")
            print(f"   Score: {top_result.score:.2f}")
            print(f"   Type: {top_result.data_type}")
            print(f"   Raw ingredient in top 8: {'Yes' if raw_ingredient_found else 'No'}")
            
            # eatthismuchとの比較
            if query_term == "potato":
                is_ideal = any(exp.lower() in top_name.lower() for exp in expected_names) and \
                          any(keyword in top_desc.lower() for keyword in ["raw", "flesh"])
                print(f"   Matches eatthismuch ideal: {'Yes' if is_ideal else 'No'}")

async def compare_with_eatthismuch_expectations():
    """eatthismuchの期待結果と比較"""
    
    print(f"\n🥔 EatThisMuch期待結果との詳細比較")
    print("="*70)
    
    # eatthismuchの期待結果（potato検索）
    eatthismuch_expected = [
        "Potato - Flesh and skin, raw (284kcal)",
        "Potatoes - Fast foods, hashed brown (392kcal)",
        "Sweet potato - Raw, unprepared (112kcal)",
        "Red potatoes - Flesh and skin, raw (119kcal)",
        "Russet potatoes - Flesh and skin, raw (292kcal)"
    ]
    
    print("EatThisMuch期待結果:")
    for i, expected in enumerate(eatthismuch_expected, 1):
        print(f"{i:2}. {expected}")
    
    print(f"\nOur Algorithm Results:")
    query = SearchQuery(elasticsearch_query_terms="potato")
    results = await food_search_service.search_foods(query, size=10)
    
    matches_found = 0
    for i, r in enumerate(results, 1):
        # 現在のデータ構造に対応
        if ',' in r.food_name:
            name_parts = r.food_name.split(',', 1)
            name_part = name_parts[0].strip()
            desc_part = name_parts[1].strip()
        else:
            name_part = r.food_name
            desc_part = ""
        
        # 期待結果との一致チェック
        is_raw_potato = False
        for expected in eatthismuch_expected:
            if name_part.lower() in expected.lower() and "raw" in desc_part.lower():
                is_raw_potato = True
                matches_found += 1
                break
        
        status = "✅" if is_raw_potato else "❌"
        print(f"{i:2}. {status} {name_part} | {desc_part} | Score: {r.score:.2f}")
        print(f"    {r.data_type} | {r.nutrition.get('calories', 0):3.0f}kcal")
    
    print(f"\n📊 Match Summary:")
    print(f"   Expected matches found in top 10: {matches_found}/5")
    print(f"   Match rate: {(matches_found/5)*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_two_stage_search_strategy())
    asyncio.run(compare_with_eatthismuch_expectations()) 