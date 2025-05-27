#!/usr/bin/env python3
"""
USDA APIの動作確認スクリプト
"""

import asyncio
import os

# 環境変数の設定
os.environ['USDA_API_KEY'] = 'vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg'
os.environ['USDA_API_BASE_URL'] = 'https://api.nal.usda.gov/fdc/v1'
os.environ['USDA_API_TIMEOUT'] = '10.0'
os.environ['USDA_KEY_NUTRIENT_NUMBERS_STR'] = '208,203,204,205,291,269,307'

from app.services.usda_service import USDAService

async def test_usda():
    service = USDAService()
    
    try:
        # 鶏肉を検索
        print("=== USDA検索テスト: Chicken ===")
        results = await service.search_foods(
            query="Chicken breast",
            data_types=["Foundation", "SR Legacy"],
            page_size=3
        )
        
        print(f"検索結果: {len(results)}件")
        for i, item in enumerate(results):
            print(f"\n{i+1}. {item.description}")
            print(f"   FDC ID: {item.fdc_id}")
            print(f"   データタイプ: {item.data_type}")
            print(f"   栄養素:")
            for nutrient in item.food_nutrients:
                print(f"     - {nutrient.name}: {nutrient.amount} {nutrient.unit_name}")
                
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        await service.close_client()

if __name__ == "__main__":
    asyncio.run(test_usda()) 