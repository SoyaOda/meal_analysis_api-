#!/usr/bin/env python3
"""
USDA検索の問題をデバッグするためのスクリプト
"""

import asyncio
import json
import os
from app.services.usda_service import USDAService
from app.core.config import get_settings

async def test_usda_searches():
    """改善されたUSDA検索をテストする"""
    
    # 環境変数の設定を確認
    settings = get_settings()
    print(f"🔧 USDA API Key configured: {'Yes' if settings.USDA_API_KEY else 'No'}")
    
    usda_service = USDAService()
    
    # テストクエリリスト
    test_queries = [
        ("La Madeleine Caesar Salad", "branded_product"),
        ("Caesar salad", "dish"),
        ("Penne pasta, cooked", "ingredient"),
        ("Chicken breast, cooked", "ingredient"),
        ("Feta cheese", "ingredient"),
        ("Tomato, raw", "ingredient")
    ]
    
    for query, query_type in test_queries:
        print(f"\n🔍 Testing query: '{query}' (type: {query_type})")
        
        try:
            if query_type == "branded_product" and "La Madeleine" in query:
                # ブランド検索をテスト
                remaining_query = query.replace("La Madeleine ", "")
                results = await usda_service.search_foods_rich(
                    query=remaining_query,
                    data_types=["Branded", "FNDDS"],
                    page_size=10,
                    require_all_words=True,
                    brand_owner_filter="La Madeleine"
                )
                print(f"   📊 Brand search results: {len(results)}")
            else:
                # 通常検索をテスト
                if query_type == "dish":
                    data_types = ["FNDDS", "Branded", "Foundation"]
                    require_all_words = True
                elif query_type == "ingredient":
                    data_types = ["Foundation", "FNDDS"]
                    require_all_words = False
                else:
                    data_types = None
                    require_all_words = False
                
                results = await usda_service.search_foods_rich(
                    query=query,
                    data_types=data_types,
                    page_size=10,
                    require_all_words=require_all_words
                )
                print(f"   📊 Search results: {len(results)}")
            
            # 結果の詳細を表示
            for i, result in enumerate(results[:3]):  # 上位3件のみ表示
                print(f"      {i+1}. FDC ID: {result.fdc_id}")
                print(f"         Description: {result.description}")
                print(f"         Type: {result.data_type}")
                print(f"         Brand: {result.brand_owner or 'N/A'}")
                print(f"         Score: {result.score:.2f}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_usda_searches()) 