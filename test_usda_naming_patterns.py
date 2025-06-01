#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.getcwd())
from app.services.usda_service import USDAService

async def analyze_usda_naming_patterns():
    usda_service = USDAService()
    
    # Test different naming patterns to understand USDA conventions
    test_patterns = [
        # パスタの命名パターン
        ("Pasta patterns", [
            "Pasta, penne, cooked",
            "Penne pasta, cooked", 
            "Pasta penne cooked",
            "Penne, cooked",
            "Pasta, cooked",
            "Penne"
        ]),
        
        # 肉の命名パターン
        ("Meat patterns", [
            "Beef, ground, cooked",
            "Ground beef, cooked",
            "Beef ground cooked", 
            "Ground beef",
            "Beef, ground",
            "Beef"
        ]),
        
        # 野菜の命名パターン
        ("Vegetable patterns", [
            "Lettuce, romaine, raw",
            "Romaine lettuce, raw",
            "Lettuce romaine raw",
            "Romaine lettuce",
            "Lettuce, romaine", 
            "Lettuce"
        ])
    ]
    
    for category, queries in test_patterns:
        print(f'=== {category} ===')
        for query in queries:
            print(f'\nTesting: "{query}"')
            try:
                results = await usda_service.search_foods_rich(
                    query=query,
                    page_size=5,
                    data_types=['Foundation', 'SR Legacy', 'FNDDS', 'Branded']
                )
                
                if results:
                    print(f'  Found {len(results)} results:')
                    for i, result in enumerate(results[:3]):  # Top 3 only
                        print(f'    {i+1}. {result.description} (Type: {result.data_type}, Score: {result.score})')
                else:
                    print('  No results found')
                    
            except Exception as e:
                print(f'  ERROR: {e}')
        print()

if __name__ == '__main__':
    asyncio.run(analyze_usda_naming_patterns()) 