#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service
from app.api.v1.schemas.meal import USDACandidateQuery

async def test_simplified_meatloaf():
    """Test the simplified tiered search for Meatloaf"""
    
    usda_service = get_usda_service()
    
    print("=== Testing Simplified Tiered Search for Meatloaf ===")
    
    # Test query simplification logic directly
    query1 = "Meatloaf, prepared, cooked"
    simplified = usda_service._simplify_query_term(query1)
    print(f"Tier 1→2: '{query1}' → '{simplified}'")
    
    generalized = usda_service._generalize_query_term(
        USDACandidateQuery(
            query_term=query1,
            granularity_level="dish",
            preferred_data_types=["SR Legacy", "Branded"],
            original_term="Meatloaf",
            reason_for_query="Test"
        )
    )
    print(f"Tier 2→3: '{simplified}' → '{generalized}'")
    
    # Phase1で生成されたクエリを再現
    candidate = USDACandidateQuery(
        query_term="Meatloaf, prepared, cooked",
        granularity_level="dish",
        preferred_data_types=["SR Legacy", "Branded"],
        original_term="Meatloaf",
        reason_for_query="Prepared dish query targeting SR Legacy database first, with Branded as backup"
    )
    
    try:
        print(f"\n=== EXECUTING TIERED SEARCH ===")
        print(f"Original query: {candidate.query_term}")
        
        # Execute tiered search with new logic
        tiered_results = await usda_service.execute_tiered_usda_search(
            phase1_candidate=candidate,
            brand_context=None,
            max_results_cap=15
        )
        
        print(f"\nTotal results: {len(tiered_results)}")
        
        # Analyze results by tier
        tier_analysis = {}
        meatloaf_specific_results = []
        
        for result in tiered_results:
            tier = getattr(result, 'search_tier', 'Unknown')
            query_used = getattr(result, 'search_query_used', 'N/A')
            
            if tier not in tier_analysis:
                tier_analysis[tier] = []
            tier_analysis[tier].append(result)
            
            # Look for actual meatloaf results
            if 'meatloaf' in result.description.lower():
                meatloaf_specific_results.append(result)
        
        print(f"Results by tier: {dict((k, len(v)) for k, v in tier_analysis.items())}")
        
        # Show results by tier
        for tier in sorted(tier_analysis.keys()):
            tier_results = tier_analysis[tier]
            query_used = getattr(tier_results[0], 'search_query_used', 'N/A') if tier_results else 'N/A'
            print(f"\n--- TIER {tier} (Query: '{query_used}') ---")
            
            for i, result in enumerate(tier_results[:3]):  # Show top 3 per tier
                is_combo = any(combo in result.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
                combo_indicator = " [COMBO]" if is_combo else " [STANDALONE]"
                
                print(f"  {i+1}. FDC {result.fdc_id}: {result.description}{combo_indicator}")
                print(f"     Type: {result.data_type}, Score: {result.score}")
        
        # Show meatloaf-specific results
        if meatloaf_specific_results:
            print(f"\n=== MEATLOAF-SPECIFIC RESULTS ===")
            for result in meatloaf_specific_results:
                tier = getattr(result, 'search_tier', 'N/A')
                query_used = getattr(result, 'search_query_used', 'N/A')
                is_combo = any(combo in result.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
                combo_indicator = " [COMBO]" if is_combo else " [STANDALONE]"
                
                print(f"✅ FDC {result.fdc_id}: {result.description}{combo_indicator}")
                print(f"   Tier: {tier}, Query: '{query_used}', Type: {result.data_type}, Score: {result.score}")
                
                if result.data_type == "SR Legacy" and not is_combo:
                    print(f"   🎯 PERFECT for dish-level strategy!")
        else:
            print(f"\n❌ No meatloaf-specific results found")
            
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(test_simplified_meatloaf()) 