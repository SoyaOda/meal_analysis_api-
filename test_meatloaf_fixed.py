#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service
from app.api.v1.schemas.meal import USDACandidateQuery

async def test_meatloaf_search():
    """Test meatloaf search with updated system (no FNDDS, SR Legacy first)"""
    
    usda_service = get_usda_service()
    
    print("=== Testing Meatloaf Search (Fixed System) ===")
    
    # Test meatloaf query with preferred_data_types
    candidate = USDACandidateQuery(
        query_term="Meatloaf, prepared",
        granularity_level="dish",
        preferred_data_types=["SR Legacy", "Branded"],
        original_term="Meatloaf",
        reason_for_query="Test dish-level search with SR Legacy priority"
    )
    
    try:
        results = await usda_service.execute_tiered_usda_search(
            phase1_candidate=candidate,
            brand_context=None,
            max_results_cap=10
        )
        
        print(f"\nMeatloaf search results: {len(results)} items found")
        print("\nTop results:")
        
        sr_legacy_count = 0
        branded_count = 0
        
        for i, result in enumerate(results):
            data_type = result.data_type or "Unknown"
            score = result.score or 0
            tier = getattr(result, 'search_tier', 'N/A')
            
            if data_type == "SR Legacy":
                sr_legacy_count += 1
            elif data_type == "Branded":
                branded_count += 1
            
            print(f"{i+1:2d}. FDC {result.fdc_id}: {result.description}")
            print(f"     Type: {data_type}, Score: {score:.1f}, Tier: {tier}")
            
            if i >= 4:  # Show top 5
                break
        
        print(f"\nDatabase type distribution:")
        print(f"  SR Legacy: {sr_legacy_count}")
        print(f"  Branded: {branded_count}")
        print(f"  Others: {len(results) - sr_legacy_count - branded_count}")
        
        # Check if we have good SR Legacy results
        sr_results = [r for r in results if r.data_type == "SR Legacy"]
        if sr_results:
            print(f"\n✅ Found {len(sr_results)} SR Legacy results")
            best_sr = sr_results[0]
            print(f"   Best SR Legacy: FDC {best_sr.fdc_id} - {best_sr.description}")
        else:
            print("\n❌ No SR Legacy results found")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(test_meatloaf_search()) 