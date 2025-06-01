#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service

async def test_meatloaf_direct():
    """Test direct USDA search for meatloaf queries"""
    
    usda_service = get_usda_service()
    
    try:
        # Phase1で生成されたクエリをテスト
        print('=== Testing Phase1 Query: "Meatloaf, prepared, cooked" ===')
        results1 = await usda_service.search_foods_rich(
            query='Meatloaf, prepared, cooked',
            data_types=['SR Legacy', 'Branded'],
            page_size=10,
            require_all_words=True,
            search_context='dish'
        )
        print(f'Results: {len(results1)}')
        for i, r in enumerate(results1):
            print(f'  {i+1}. FDC {r.fdc_id}: {r.description} ({r.data_type}, Score: {r.score})')
        
        print('\n=== Testing Simplified Query: "Meatloaf" ===')
        results2 = await usda_service.search_foods_rich(
            query='Meatloaf',
            data_types=['SR Legacy', 'Branded'],
            page_size=10,
            require_all_words=False,
            search_context='dish'
        )
        print(f'Results: {len(results2)}')
        for i, r in enumerate(results2):
            print(f'  {i+1}. FDC {r.fdc_id}: {r.description} ({r.data_type}, Score: {r.score})')
        
        # SR Legacyのみで検索
        print('\n=== Testing SR Legacy Only: "Meatloaf" ===')
        results3 = await usda_service.search_foods_rich(
            query='Meatloaf',
            data_types=['SR Legacy'],
            page_size=10,
            require_all_words=False,
            search_context='dish'
        )
        print(f'Results: {len(results3)}')
        for i, r in enumerate(results3):
            print(f'  {i+1}. FDC {r.fdc_id}: {r.description} ({r.data_type}, Score: {r.score})')
            
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(test_meatloaf_direct()) 