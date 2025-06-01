#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service

async def test_direct_meatloaf_api():
    """Test direct API search for meatloaf with different data types"""
    
    usda_service = get_usda_service()
    
    print("=== Direct USDA API Meatloaf Test ===")
    
    # Test different query variations and data types
    test_queries = [
        ("Meatloaf", ["SR Legacy"]),
        ("Meatloaf, prepared", ["SR Legacy"]),
        ("Meatloaf", ["Foundation"]),
        ("Meatloaf", ["Branded"]),
        ("Meatloaf", ["SR Legacy", "Foundation", "Branded"]),
    ]
    
    try:
        for query, data_types in test_queries:
            print(f"\n--- Query: '{query}' with data_types: {data_types} ---")
            
            results = await usda_service.search_foods_rich(
                query=query,
                data_types=data_types,
                page_size=10,
                require_all_words=False,
                search_context="dish"
            )
            
            print(f"Found {len(results)} results")
            
            # Group by data type
            by_type = {}
            for result in results:
                data_type = result.data_type or "Unknown"
                if data_type not in by_type:
                    by_type[data_type] = []
                by_type[data_type].append(result)
            
            for data_type, items in by_type.items():
                print(f"\n  {data_type} ({len(items)} items):")
                for i, item in enumerate(items[:3]):  # Show top 3 per type
                    score = item.score or 0
                    # Check if it's a standalone item or combo meal
                    desc_lower = item.description.lower()
                    is_combo = any(combo in desc_lower for combo in [
                        "with", "&", "and", "meal", "dinner", "plate", "combo"
                    ])
                    combo_indicator = " [COMBO]" if is_combo else " [STANDALONE]"
                    
                    print(f"    {i+1}. FDC {item.fdc_id}: {item.description}{combo_indicator}")
                    print(f"       Score: {score:.1f}")
    
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(test_direct_meatloaf_api()) 