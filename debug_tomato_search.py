#!/usr/bin/env python3
"""
Tomato検索デバッグスクリプト

Fresh Tomato Pastaが生トマトより上位に来る原因を分析
"""

import asyncio
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery

async def debug_tomato_search():
    """tomato検索の詳細分析"""
    print("🔍 Tomato Search Debug Analysis")
    print("=" * 50)
    
    query = SearchQuery(elasticsearch_query_terms="tomato")
    results = await food_search_service.search_foods(query, size=5)
    
    print("Top 5 results with detailed analysis:")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"{i}. 📊 RESULT ANALYSIS")
        print(f"   Food Name: '{result.food_name}'")
        print(f"   Description: '{result.description}'")
        print(f"   Data Type: {result.data_type}")
        print(f"   Score: {result.score:.2f}")
        
        # 分析項目
        food_name_lower = result.food_name.lower()
        description_lower = (result.description or "").lower()
        
        print(f"   🔍 Analysis:")
        print(f"   - Contains 'tomato' in food_name: {'tomato' in food_name_lower}")
        print(f"   - Contains 'fresh' in food_name: {'fresh' in food_name_lower}")
        print(f"   - Contains 'fresh' in description: {'fresh' in description_lower}")
        print(f"   - Contains 'raw' in description: {'raw' in description_lower}")
        print(f"   - Contains 'flesh' in description: {'flesh' in description_lower}")
        print(f"   - Contains 'skin' in description: {'skin' in description_lower}")
        
        # スコア構成要素の推定
        print(f"   📈 Estimated Score Components:")
        
        # 基本マッチスコア（推定）
        base_score = 1000.0 if 'tomato' in food_name_lower else 0.0
        print(f"   - Base food_name match (~1000.0): {'✅' if 'tomato' in food_name_lower else '❌'}")
        
        # Fresh/Rawブーストの推定
        fresh_boost = 0.0
        if 'tomato' in food_name_lower:
            if 'fresh' in (food_name_lower + " " + description_lower):
                fresh_boost += 200.0
                print(f"   - 'Fresh' keyword boost (+200.0): ✅")
            elif 'raw' in description_lower:
                fresh_boost += 200.0
                print(f"   - 'Raw' keyword boost (+200.0): ✅")
            else:
                print(f"   - Raw/Fresh keyword boost: ❌")
        
        estimated_total = base_score + fresh_boost
        print(f"   - Estimated total: ~{estimated_total:.1f} (Actual: {result.score:.2f})")
        
        print()

if __name__ == "__main__":
    asyncio.run(debug_tomato_search()) 