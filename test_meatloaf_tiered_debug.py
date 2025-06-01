#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service
from app.api.v1.schemas.meal import USDACandidateQuery

async def debug_meatloaf_tiered():
    """Debug what exactly tiered search provides for Meatloaf"""
    
    usda_service = get_usda_service()
    
    print("=== Debugging Meatloaf Tiered Search ===")
    
    # Phase1で生成されたクエリを再現
    candidate = USDACandidateQuery(
        query_term="Meatloaf, prepared, cooked",
        granularity_level="dish",
        preferred_data_types=["SR Legacy", "Branded"],
        original_term="Meatloaf",
        reason_for_query="Prepared dish query targeting SR Legacy database first, with Branded as backup"
    )
    
    try:
        print(f"Testing candidate: {candidate.query_term}")
        print(f"Granularity: {candidate.granularity_level}")
        print(f"Preferred types: {candidate.preferred_data_types}")
        
        # Execute tiered search - 実際にPhase2が受け取る結果
        tiered_results = await usda_service.execute_tiered_usda_search(
            phase1_candidate=candidate,
            brand_context=None,
            max_results_cap=15
        )
        
        print(f"\n=== TIERED SEARCH RESULTS ===")
        print(f"Total results: {len(tiered_results)}")
        
        # Results by tier and data type
        tier_analysis = {}
        datatype_analysis = {}
        sr_legacy_results = []
        
        for result in tiered_results:
            tier = getattr(result, 'search_tier', 'Unknown')
            data_type = result.data_type or 'Unknown'
            
            if tier not in tier_analysis:
                tier_analysis[tier] = 0
            tier_analysis[tier] += 1
            
            if data_type not in datatype_analysis:
                datatype_analysis[data_type] = 0
            datatype_analysis[data_type] += 1
            
            if data_type == "SR Legacy":
                sr_legacy_results.append(result)
        
        print(f"Results by tier: {tier_analysis}")
        print(f"Results by data type: {datatype_analysis}")
        
        # Show all results
        for i, result in enumerate(tiered_results):
            tier = getattr(result, 'search_tier', 'N/A')
            query_used = getattr(result, 'search_query_used', 'N/A')
            
            # Check if combo meal
            is_combo = any(combo in result.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
            combo_indicator = " [COMBO]" if is_combo else " [STANDALONE]"
            
            print(f"\n{i+1:2d}. FDC {result.fdc_id}: {result.description}{combo_indicator}")
            print(f"     Type: {result.data_type}, Score: {result.score}, Tier: {tier}")
            print(f"     Query used: '{query_used}'")
        
        # SR Legacy analysis
        if sr_legacy_results:
            print(f"\n=== SR LEGACY RESULTS FOUND ===")
            for sr in sr_legacy_results:
                tier = getattr(sr, 'search_tier', 'N/A')
                query_used = getattr(sr, 'search_query_used', 'N/A')
                is_combo = any(combo in sr.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
                combo_indicator = " [COMBO]" if is_combo else " [STANDALONE]"
                
                print(f"✅ FDC {sr.fdc_id}: {sr.description}{combo_indicator}")
                print(f"   Tier: {tier}, Query: '{query_used}', Score: {sr.score}")
                
                # This should be suitable for dish-level calculation
                if not is_combo and "vegetarian" not in sr.description.lower():
                    print(f"   🎯 THIS SHOULD BE SUITABLE FOR DISH-LEVEL STRATEGY!")
                elif "vegetarian" in sr.description.lower():
                    print(f"   ⚠️  Vegetarian - may not be ideal for standard meatloaf")
        else:
            print(f"\n❌ NO SR LEGACY RESULTS - This explains why Phase2 chose ingredient_level")
            
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(debug_meatloaf_tiered()) 