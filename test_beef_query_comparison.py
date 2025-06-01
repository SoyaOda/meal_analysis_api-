#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.getcwd())
from app.services.usda_service import USDAService

async def compare_beef_query_formats():
    usda_service = USDAService()
    
    # Test different query formats
    test_queries = [
        ("USDA Standard Format", "Beef, ground, cooked"),
        ("Natural Language Format", "Ground beef, cooked"),
        ("Alternative Order", "Ground beef, pan-fried"),
        ("USDA Alternative", "Beef, ground, pan-fried"),
        ("Simple USDA", "Beef, ground"),
        ("Simple Natural", "Ground beef"),
        ("Generic", "Beef")
    ]
    
    print("=== Beef Query Format Comparison ===\n")
    
    for format_name, query in test_queries:
        print(f"🔍 Testing: {format_name}")
        print(f"Query: \"{query}\"")
        print("-" * 50)
        
        try:
            results = await usda_service.search_foods_rich(
                query=query,
                page_size=5,
                data_types=['Foundation', 'SR Legacy', 'FNDDS', 'Branded']
            )
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results):
                    print(f"  {i+1}. FDC ID: {result.fdc_id}")
                    print(f"     Description: {result.description}")
                    print(f"     Type: {result.data_type}, Score: {result.score}")
                    print()
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("\n" + "="*70 + "\n")

    # Test hierarchical search progression
    print("=== Hierarchical Search Progression Test ===\n")
    
    hierarchy_test = [
        "Beef, ground, cooked",  # Tier 1: Full specificity
        "Beef, ground",          # Tier 2: Remove rightmost modifier
        "Beef"                   # Tier 3: Core category only
    ]
    
    for i, query in enumerate(hierarchy_test, 1):
        print(f"Tier {i}: \"{query}\"")
        try:
            results = await usda_service.search_foods_rich(
                query=query,
                page_size=3,
                data_types=['Foundation', 'SR Legacy', 'FNDDS']
            )
            
            print(f"  Results: {len(results)}")
            for j, result in enumerate(results[:2]):  # Top 2 only
                print(f"    {j+1}. {result.description} (Score: {result.score})")
            print()
            
        except Exception as e:
            print(f"  ERROR: {e}\n")

if __name__ == '__main__':
    asyncio.run(compare_beef_query_formats()) 