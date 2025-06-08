#!/usr/bin/env python3
"""
Potato関連データ調査スクリプト

データベース内のpotato関連エントリを詳細調査
"""

import asyncio
from app_v2.elasticsearch.client import es_client
from app_v2.elasticsearch.config import es_config

async def debug_potato_data():
    """データベース内のpotato関連データを詳細調査"""
    
    print("🔍 Potato関連データ詳細調査")
    print("="*70)
    
    # 1. 全てのpotato関連エントリを検索
    print("1. 全てのpotato関連エントリ:")
    print("-"*50)
    
    query = {
        "query": {
            "bool": {
                "should": [
                    {"wildcard": {"food_name": "*potato*"}},
                    {"wildcard": {"food_name": "*Potato*"}},
                    {"match": {"food_name": "potato"}}
                ]
            }
        },
        "size": 50,
        "sort": [
            {"food_name.keyword": {"order": "asc"}}
        ]
    }
    
    response = await es_client.search(
        index_name=es_config.food_nutrition_index,
        query=query,
        size=50
    )
    
    if response and 'hits' in response:
        print(f"Found {len(response['hits']['hits'])} potato-related entries:")
        
        for i, hit in enumerate(response['hits']['hits'], 1):
            source = hit['_source']
            food_name = source.get('food_name', '')
            data_type = source.get('data_type', '')
            calories = source.get('nutrition', {}).get('calories', 0)
            
            # カンマで分割して表示
            name_parts = food_name.split(',', 1)
            name_part = name_parts[0].strip() if name_parts else food_name
            desc_part = name_parts[1].strip() if len(name_parts) > 1 else ""
            
            print(f"{i:2}. Name: '{name_part}' | Desc: '{desc_part}' | Type: {data_type} | {calories:.0f}kcal")
            
            # 期待される結果かチェック
            if "flesh and skin" in food_name.lower() and "raw" in food_name.lower():
                print(f"    ✅ FOUND EXPECTED: {food_name}")
    
    # 2. 特定の期待される名前を直接検索
    print(f"\n2. 期待される特定エントリの直接検索:")
    print("-"*50)
    
    expected_names = [
        "Potato, Flesh and skin, raw",
        "Potatoes, Flesh and skin, raw", 
        "Red potatoes, Flesh and skin, raw",
        "Russet potatoes, Flesh and skin, raw",
        "White potatoes, Flesh and skin, raw"
    ]
    
    for expected_name in expected_names:
        exact_query = {
            "query": {
                "match_phrase": {
                    "food_name": expected_name
                }
            }
        }
        
        response = await es_client.search(
            index_name=es_config.food_nutrition_index,
            query=exact_query,
            size=1
        )
        
        if response and response['hits']['hits']:
            hit = response['hits']['hits'][0]
            source = hit['_source']
            print(f"✅ FOUND: {expected_name}")
            print(f"   Type: {source.get('data_type')} | Calories: {source.get('nutrition', {}).get('calories', 0):.0f}kcal")
        else:
            print(f"❌ NOT FOUND: {expected_name}")
    
    # 3. ingredient タイプのpotato関連エントリのみ
    print(f"\n3. Ingredient タイプのpotato関連エントリ:")
    print("-"*50)
    
    ingredient_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"data_type": "ingredient"}},
                    {"wildcard": {"food_name": "*potato*"}}
                ]
            }
        },
        "size": 20,
        "sort": [
            {"food_name.keyword": {"order": "asc"}}
        ]
    }
    
    response = await es_client.search(
        index_name=es_config.food_nutrition_index,
        query=ingredient_query,
        size=20
    )
    
    if response and 'hits' in response:
        print(f"Found {len(response['hits']['hits'])} ingredient-type potato entries:")
        
        for i, hit in enumerate(response['hits']['hits'], 1):
            source = hit['_source']
            food_name = source.get('food_name', '')
            calories = source.get('nutrition', {}).get('calories', 0)
            
            # カンマで分割して表示
            name_parts = food_name.split(',', 1)
            name_part = name_parts[0].strip() if name_parts else food_name
            desc_part = name_parts[1].strip() if len(name_parts) > 1 else ""
            
            print(f"{i:2}. Name: '{name_part}' | Desc: '{desc_part}' | {calories:.0f}kcal")
            
            # 生ポテトかチェック
            if "raw" in desc_part.lower() or "flesh" in desc_part.lower():
                print(f"    🎯 RAW POTATO CANDIDATE!")

if __name__ == "__main__":
    asyncio.run(debug_potato_data()) 