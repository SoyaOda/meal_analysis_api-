#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service
from app.api.v1.schemas.meal import USDACandidateQuery

async def test_tier_formatting():
    """Test the tier formatting for Phase2 prompt"""
    
    usda_service = get_usda_service()
    
    print("=== Testing Tier Formatting for Phase2 ===")
    
    # Phase1で生成されたクエリを再現
    candidate = USDACandidateQuery(
        query_term="Meatloaf, prepared, cooked",
        granularity_level="dish",
        preferred_data_types=["SR Legacy", "Branded"],
        original_term="Meatloaf",
        reason_for_query="Prepared dish query targeting SR Legacy database first, with Branded as backup"
    )
    
    try:
        print(f"Executing tiered search for: {candidate.query_term}")
        
        # Execute tiered search
        tiered_results = await usda_service.execute_tiered_usda_search(
            phase1_candidate=candidate,
            brand_context=None,
            max_results_cap=15
        )
        
        print(f"\nTotal results: {len(tiered_results)}")
        
        # Test tier organization
        tier_organized = usda_service.organize_results_by_tier(tiered_results)
        print(f"\nTier organization:")
        for tier, results in tier_organized.items():
            print(f"  Tier {tier}: {len(results)} results")
        
        # Test formatted output for Phase2 prompt
        print(f"\n" + "="*60)
        print("FORMATTED OUTPUT FOR PHASE2 PROMPT:")
        print("="*60)
        
        formatted_output = usda_service.format_tier_results_for_prompt(tiered_results)
        print(formatted_output)
        
        print(f"\n" + "="*60)
        print("MEATLOAF-SPECIFIC ANALYSIS:")
        print("="*60)
        
        # Analyze meatloaf-specific results by tier
        meatloaf_by_tier = {}
        for result in tiered_results:
            if 'meatloaf' in result.description.lower():
                tier = getattr(result, 'search_tier', 0)
                if tier not in meatloaf_by_tier:
                    meatloaf_by_tier[tier] = []
                meatloaf_by_tier[tier].append(result)
        
        for tier in sorted(meatloaf_by_tier.keys()):
            results = meatloaf_by_tier[tier]
            query_used = getattr(results[0], 'search_query_used', 'N/A')
            print(f"\n🥩 TIER {tier} MEATLOAF OPTIONS (Query: '{query_used}'):")
            
            for result in results:
                is_combo = any(combo in result.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
                strategy_suitability = "🎯 DISH-LEVEL SUITABLE" if result.data_type == "SR Legacy" and not is_combo else "⚠️  COMBO/BRANDED"
                
                print(f"  • FDC {result.fdc_id}: {result.description}")
                print(f"    Type: {result.data_type}, Score: {result.score:.1f} - {strategy_suitability}")
            
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(test_tier_formatting()) 