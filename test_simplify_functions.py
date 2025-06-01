#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd())
from app.services.usda_service import USDAService
from app.api.v1.schemas.meal import USDACandidateQuery

def test_simplify_and_generalize():
    usda_service = USDAService()
    
    # Test cases for simplification
    test_cases = [
        "Pasta, penne, cooked",
        "Beef, ground, cooked", 
        "Lettuce, romaine, raw",
        "Chicken, breast, grilled",
        "Potatoes, mashed, home-prepared"
    ]
    
    print("=== Testing _simplify_query_term ===")
    for query in test_cases:
        simplified = usda_service._simplify_query_term(query)
        print(f"'{query}' → '{simplified}'")
    
    print("\n=== Testing _generalize_query_term ===")  
    for query in test_cases:
        # Create mock candidate for generalize function
        candidate = USDACandidateQuery(
            query_term=query,
            granularity_level="ingredient",
            original_term=query.split(',')[0].strip(),
            reason_for_query="test"
        )
        generalized = usda_service._generalize_query_term(candidate)
        print(f"'{query}' → '{generalized}'")
    
    print("\n=== Full Hierarchy Example ===")
    example = "Pasta, penne, cooked"
    candidate = USDACandidateQuery(
        query_term=example,
        granularity_level="ingredient", 
        original_term="Penne pasta",
        reason_for_query="test"
    )
    
    tier1 = example
    tier2 = usda_service._simplify_query_term(tier1)
    tier3 = usda_service._generalize_query_term(candidate)
    
    print(f"Tier 1: '{tier1}'")
    print(f"Tier 2: '{tier2}'") 
    print(f"Tier 3: '{tier3}'")

if __name__ == '__main__':
    test_simplify_and_generalize() 