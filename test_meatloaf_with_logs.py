#!/usr/bin/env python3

import asyncio
import sys
import os
import logging

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service
from app.api.v1.schemas.meal import USDACandidateQuery

# Set up logging to see what's happening in tiered search
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_meatloaf_with_logs():
    """Test meatloaf search with detailed logs"""
    
    usda_service = get_usda_service()
    
    print("=== Testing Meatloaf Search with Logs ===")
    
    # Test meatloaf query with preferred_data_types
    candidate = USDACandidateQuery(
        query_term="Meatloaf, prepared",
        granularity_level="dish",
        preferred_data_types=["SR Legacy", "Branded"],
        original_term="Meatloaf",
        reason_for_query="Test dish-level search with SR Legacy priority"
    )
    
    try:
        print(f"\nTesting with candidate:")
        print(f"  Query: {candidate.query_term}")
        print(f"  Granularity: {candidate.granularity_level}")
        print(f"  Preferred types: {candidate.preferred_data_types}")
        
        results = await usda_service.execute_tiered_usda_search(
            phase1_candidate=candidate,
            brand_context=None,
            max_results_cap=10
        )
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total results: {len(results)} items found")
        
        # Count by tier
        tier_counts = {}
        for result in results:
            tier = getattr(result, 'search_tier', 'Unknown')
            if tier not in tier_counts:
                tier_counts[tier] = 0
            tier_counts[tier] += 1
        
        print(f"Results by tier: {tier_counts}")
        
        # Show detailed results
        for i, result in enumerate(results):
            data_type = result.data_type or "Unknown"
            score = result.score or 0
            tier = getattr(result, 'search_tier', 'N/A')
            query_used = getattr(result, 'search_query_used', 'N/A')
            
            # Check if combo meal
            is_combo = any(combo in result.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
            combo_indicator = " [COMBO]" if is_combo else " [STANDALONE]"
            
            print(f"\n{i+1:2d}. FDC {result.fdc_id}: {result.description}{combo_indicator}")
            print(f"     Type: {data_type}, Score: {score:.1f}, Tier: {tier}")
            print(f"     Query used: '{query_used}'")
        
        # Check if we have good SR Legacy results
        sr_results = [r for r in results if r.data_type == "SR Legacy"]
        if sr_results:
            print(f"\n✅ Found {len(sr_results)} SR Legacy results")
            for sr in sr_results:
                print(f"   SR Legacy: FDC {sr.fdc_id} - {sr.description} (Tier {getattr(sr, 'search_tier', 'N/A')})")
        else:
            print("\n❌ No SR Legacy results found")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(test_meatloaf_with_logs()) 