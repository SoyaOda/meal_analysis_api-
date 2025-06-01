#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.usda_service import get_usda_service
from app.api.v1.schemas.meal import USDACandidateQuery

async def debug_meatloaf_tiers():
    """Debug each tier of meatloaf search to see what's happening"""
    
    usda_service = get_usda_service()
    
    print("=== Debugging Meatloaf Tiered Search ===")
    
    # Test the exact same query as the system uses
    candidate = USDACandidateQuery(
        query_term="Meatloaf, prepared",
        granularity_level="dish",
        preferred_data_types=["SR Legacy", "Branded"],
        original_term="Meatloaf",
        reason_for_query="Test dish-level search with SR Legacy priority"
    )
    
    try:
        print(f"\nOriginal query: '{candidate.query_term}'")
        print(f"Preferred data types: {candidate.preferred_data_types}")
        
        # Test Tier 1 manually
        print("\n--- TIER 1 TEST ---")
        tier1_results = await usda_service.search_foods_rich(
            query=candidate.query_term,
            data_types=candidate.preferred_data_types,
            page_size=15,
            require_all_words=True,
            search_context="dish"
        )
        
        print(f"Tier 1 results: {len(tier1_results)}")
        for i, r in enumerate(tier1_results):
            combo = any(combo in r.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
            print(f"  {i+1}. FDC {r.fdc_id}: {r.description} ({r.data_type}, Score: {r.score}, {'COMBO' if combo else 'STANDALONE'})")
        
        # Test Tier 2 query generation
        print("\n--- TIER 2 TEST ---")
        tier2_query = usda_service._simplify_query_term(candidate.query_term)
        print(f"Tier 2 query: '{tier2_query}'")
        
        tier2_results = await usda_service.search_foods_rich(
            query=tier2_query,
            data_types=["SR Legacy", "Branded", "Foundation"],
            page_size=15,
            require_all_words=False,
            search_context="ingredient"
        )
        
        print(f"Tier 2 results: {len(tier2_results)}")
        for i, r in enumerate(tier2_results[:5]):
            combo = any(combo in r.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
            print(f"  {i+1}. FDC {r.fdc_id}: {r.description} ({r.data_type}, Score: {r.score}, {'COMBO' if combo else 'STANDALONE'})")
        
        # Test Tier 3 query generation
        print("\n--- TIER 3 TEST ---")
        tier3_query = usda_service._generalize_query_term(candidate)
        print(f"Tier 3 query: '{tier3_query}'")
        
        tier3_results = await usda_service.search_foods_rich(
            query=tier3_query,
            data_types=["Foundation", "SR Legacy", "Branded"],
            page_size=15,
            require_all_words=False,
            search_context="ingredient"
        )
        
        print(f"Tier 3 results: {len(tier3_results)}")
        for i, r in enumerate(tier3_results[:5]):
            combo = any(combo in r.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
            print(f"  {i+1}. FDC {r.fdc_id}: {r.description} ({r.data_type}, Score: {r.score}, {'COMBO' if combo else 'STANDALONE'})")
        
        # Test what happens with just "Meatloaf" 
        print("\n--- SIMPLIFIED QUERY TEST ---")
        simple_results = await usda_service.search_foods_rich(
            query="Meatloaf",
            data_types=["SR Legacy", "Branded"],
            page_size=10,
            require_all_words=False,
            search_context="dish"
        )
        
        print(f"Simple 'Meatloaf' results: {len(simple_results)}")
        for i, r in enumerate(simple_results):
            combo = any(combo in r.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"])
            print(f"  {i+1}. FDC {r.fdc_id}: {r.description} ({r.data_type}, Score: {r.score}, {'COMBO' if combo else 'STANDALONE'})")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    finally:
        await usda_service.close_client()

if __name__ == "__main__":
    asyncio.run(debug_meatloaf_tiers()) 